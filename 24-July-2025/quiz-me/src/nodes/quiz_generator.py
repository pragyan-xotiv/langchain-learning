"""Quiz Generator Node for the Interactive Quiz Generator

This module implements the quiz generator node that generates diverse, engaging 
quiz questions based on the validated topic.
"""

from typing import Dict, Any, Optional
import asyncio
import logging
from datetime import datetime
from langchain_openai import ChatOpenAI

from ..state import QuizState
from ..prompts import format_question_generation_prompt, extract_json_from_response
from .query_analyzer import create_llm_client, safe_llm_call, LLMCallError

logger = logging.getLogger(__name__)

class QuizGeneratorError(Exception):
    """Exception raised during quiz generation"""
    pass

def determine_question_type(state: QuizState) -> str:
    """Determine appropriate question type based on quiz progression"""
    total_questions = state.total_questions_answered
    
    # Question type distribution strategy
    if total_questions == 0:
        return "multiple_choice"  # Start with easier format
    elif total_questions % 3 == 0:
        return "open_ended"  # Every third question
    elif total_questions % 4 == 0:
        return "true_false"  # Every fourth question
    else:
        return "multiple_choice"  # Default format

def quiz_generator(state: QuizState, llm: Optional[ChatOpenAI] = None) -> QuizState:
    """
    Generates diverse, engaging quiz questions based on the validated topic.
    
    Args:
        state: Current quiz state with validated topic
        llm: Language model client (optional, will create if not provided)
        
    Returns:
        Updated state with generated question
    """
    logger.info(f"Quiz Generator creating question {state.current_question_index + 1} for topic '{state.topic}'")
    
    if llm is None:
        llm = create_llm_client()
    
    try:
        # Validate prerequisites
        if not state.topic_validated or not state.topic:
            state.last_error = "Cannot generate questions without validated topic"
            return state
        
        # Determine question type based on progression
        question_type = determine_question_type(state)
        
        # Format question generation prompt
        prompt = format_question_generation_prompt(state, question_type)
        
        # Generate question
        response = asyncio.run(safe_llm_call(llm, prompt))
        result = extract_json_from_response(response)
        
        if "error" in result:
            logger.error(f"Question generation failed: {result['error']}")
            state.last_error = "Failed to generate question. Please try again."
            return state
        
        # Extract question data
        question = result.get("question", "")
        q_type = result.get("type", question_type)
        correct_answer = result.get("correct_answer", "")
        options = result.get("options", None)
        explanation = result.get("explanation", "")
        
        if not question or not correct_answer:
            logger.error("Generated question missing required fields")
            state.last_error = "Generated question was incomplete. Please try again."
            return state
        
        # Update state with new question
        state.current_question = question
        state.question_type = q_type
        state.correct_answer = correct_answer
        state.question_options = options
        
        # Store question metadata
        state.quiz_metadata[f"question_{state.current_question_index}_metadata"] = {
            "explanation": explanation,
            "difficulty_justification": result.get("difficulty_justification", ""),
            "learning_objective": result.get("learning_objective", ""),
            "generated_at": datetime.now().isoformat()
        }
        
        logger.info(f"Generated {q_type} question: '{question[:50]}...'")
        
        # Clear any previous errors
        state.last_error = None
        
        return state
        
    except Exception as e:
        logger.error(f"Quiz generator error: {str(e)}")
        state.last_error = f"Question generation failed: {str(e)}"
        return state

def validate_quiz_generator_prerequisites(state: QuizState) -> list[str]:
    """Validate that state meets quiz generator prerequisites"""
    errors = []
    
    if not hasattr(state, 'topic') or not state.topic:
        errors.append("Quiz generator requires 'topic' field")
    
    if not hasattr(state, 'topic_validated') or not state.topic_validated:
        errors.append("Quiz generator requires 'topic_validated' to be True")
    
    return errors 