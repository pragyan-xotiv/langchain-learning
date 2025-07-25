"""Topic Validator Node for the Interactive Quiz Generator

This module implements the topic validator node that validates topic appropriateness 
and feasibility for quiz generation.
"""

from typing import Dict, Any, Optional
import asyncio
import logging
from datetime import datetime
from langchain_openai import ChatOpenAI

from ..state import QuizState
from ..prompts import (
    format_topic_extraction_prompt, 
    format_topic_validation_prompt, 
    extract_json_from_response
)
from .query_analyzer import create_llm_client, safe_llm_call, LLMCallError

logger = logging.getLogger(__name__)

class TopicValidatorError(Exception):
    """Exception raised during topic validation"""
    pass

def topic_validator(state: QuizState, llm: Optional[ChatOpenAI] = None) -> QuizState:
    """
    Validates quiz topics for appropriateness and feasibility.
    
    Args:
        state: Current quiz state with user_input containing topic
        llm: Language model client (optional, will create if not provided)
        
    Returns:
        Updated state with topic validation results
    """
    logger.info(f"Topic Validator processing input: '{state.user_input}'")
    
    if llm is None:
        llm = create_llm_client()
    
    try:
        # Extract topic from user input
        extraction_prompt = format_topic_extraction_prompt(state.user_input)
        extraction_response = asyncio.run(safe_llm_call(llm, extraction_prompt))
        extraction_result = extract_json_from_response(extraction_response)
        
        if "error" in extraction_result or not extraction_result.get("topic"):
            logger.warning("Topic extraction failed")
            state.last_error = "Could not identify a clear quiz topic from your input"
            state.current_phase = "topic_selection"
            return state
        
        # Store extracted topic
        extracted_topic = extraction_result["topic"]
        state.topic = extracted_topic
        
        logger.info(f"Extracted topic: '{extracted_topic}'")
        
        # Validate topic appropriateness
        validation_prompt = format_topic_validation_prompt(extracted_topic)
        validation_response = asyncio.run(safe_llm_call(llm, validation_prompt))
        validation_result = extract_json_from_response(validation_response)
        
        if "error" in validation_result:
            logger.error(f"Topic validation failed: {validation_result['error']}")
            state.last_error = "Failed to validate topic appropriateness"
            state.current_phase = "topic_selection"
            return state
        
        # Process validation results
        is_valid = validation_result.get("is_valid", False)
        state.topic_validated = is_valid
        
        if is_valid:
            # Topic is valid - set up quiz
            logger.info(f"Topic '{extracted_topic}' validated successfully")
            state.current_phase = "quiz_active"
            state.quiz_active = True
            
            # Store topic metadata
            state.quiz_metadata.update({
                "topic_category": validation_result.get("category", "general"),
                "difficulty_level": validation_result.get("difficulty_level", "medium"),
                "estimated_questions": validation_result.get("estimated_questions", 10),
                "validation_confidence": validation_result.get("confidence", 0.0)
            })
            
            # Set quiz parameters
            estimated_questions = validation_result.get("estimated_questions", 10)
            state.max_questions = min(estimated_questions, Config.MAX_QUESTIONS_DEFAULT)
            
        else:
            # Topic is invalid
            logger.warning(f"Topic '{extracted_topic}' validation failed")
            reason = validation_result.get("reason", "Topic not suitable for quiz generation")
            suggestions = validation_result.get("suggestions", [])
            
            state.last_error = reason
            if suggestions:
                state.last_error += f" Try these alternatives: {', '.join(suggestions)}"
            
            state.current_phase = "topic_selection"
            state.topic = None  # Clear invalid topic
        
        return state
        
    except Exception as e:
        logger.error(f"Topic validator error: {str(e)}")
        state.last_error = f"Topic validation failed: {str(e)}"
        state.current_phase = "topic_selection"
        state.topic_validated = False
        return state

def validate_topic_validator_prerequisites(state: QuizState) -> list[str]:
    """Validate that state meets topic validator prerequisites"""
    errors = []
    
    if not hasattr(state, 'user_input') or not state.user_input:
        errors.append("Topic validator requires 'user_input' field")
    
    return errors 