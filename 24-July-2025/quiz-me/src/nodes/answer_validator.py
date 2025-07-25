"""Answer Validator Node for the Interactive Quiz Generator

This module implements the answer validator node that evaluates user responses 
with intelligent scoring and constructive feedback.
"""

from typing import Dict, Any, Optional
import asyncio
import logging
from datetime import datetime
from langchain_openai import ChatOpenAI

from ..state import QuizState
from ..prompts import format_answer_validation_prompt, extract_json_from_response
from .query_analyzer import create_llm_client, safe_llm_call, LLMCallError

logger = logging.getLogger(__name__)

class AnswerValidatorError(Exception):
    """Exception raised during answer validation"""
    pass

def validate_multiple_choice_answer(state: QuizState) -> Dict[str, Any]:
    """Validate multiple choice answers using exact matching"""
    user_answer = state.current_answer.strip().lower()
    correct_answer = state.correct_answer.strip().lower()
    
    # Handle various input formats
    letter_to_number = {'a': '0', 'b': '1', 'c': '2', 'd': '3'}
    number_to_letter = {'0': 'a', '1': 'b', '2': 'c', '3': 'd'}
    word_to_number = {'first': '0', 'second': '1', 'third': '2', 'fourth': '3'}
    
    # Try exact match first
    is_correct = (user_answer == correct_answer)
    
    # If not exact match, try different mapping combinations
    if not is_correct:
        # Normalize both answers to numbers for comparison
        user_normalized = user_answer
        correct_normalized = correct_answer
        
        # Convert user answer to number if it's a letter or word
        if user_answer in letter_to_number:
            user_normalized = letter_to_number[user_answer]
        elif user_answer in word_to_number:
            user_normalized = word_to_number[user_answer]
        
        # Convert correct answer to number if it's a letter
        if correct_answer in letter_to_number:
            correct_normalized = letter_to_number[correct_answer]
            
        # Check if normalized versions match
        is_correct = (user_normalized == correct_normalized)
        
        # Also try the reverse - normalize correct answer to letter and compare
        if not is_correct and correct_answer in number_to_letter:
            correct_as_letter = number_to_letter[correct_answer]
            is_correct = (user_answer == correct_as_letter)
        
        # Try matching against option text if available
        if not is_correct and state.question_options:
            for i, option in enumerate(state.question_options):
                if user_answer in option.lower():
                    is_correct = (str(i) == correct_answer or chr(65 + i).lower() == correct_answer)
                    break
    
    return {
        "is_correct": is_correct,
        "partial_credit": False,
        "score_percentage": 100 if is_correct else 0,
        "feedback": "Correct!" if is_correct else f"The correct answer is {state.correct_answer}."
    }

def validate_true_false_answer(state: QuizState) -> Dict[str, Any]:
    """Validate true/false answers"""
    user_answer = state.current_answer.strip().lower()
    correct_answer = state.correct_answer.strip().lower()
    
    # Normalize true/false responses
    true_values = {'true', 't', 'yes', 'y', '1', 'correct'}
    false_values = {'false', 'f', 'no', 'n', '0', 'incorrect'}
    
    user_normalized = None
    if user_answer in true_values:
        user_normalized = 'true'
    elif user_answer in false_values:
        user_normalized = 'false'
    
    correct_normalized = None
    if correct_answer in true_values:
        correct_normalized = 'true'
    elif correct_answer in false_values:
        correct_normalized = 'false'
    
    is_correct = (user_normalized == correct_normalized and user_normalized is not None)
    
    return {
        "is_correct": is_correct,
        "partial_credit": False,
        "score_percentage": 100 if is_correct else 0,
        "feedback": "Correct!" if is_correct else f"The correct answer is {correct_answer}."
    }

def answer_validator(state: QuizState, llm: Optional[ChatOpenAI] = None) -> QuizState:
    """
    Evaluates user answers for correctness and provides constructive feedback.
    
    Args:
        state: Current quiz state with user answer
        llm: Language model client (optional, will create if not provided)
        
    Returns:
        Updated state with validation results and feedback
    """
    logger.info(f"Answer Validator processing answer for question {state.current_question_index + 1}")
    
    if llm is None:
        llm = create_llm_client()
    
    try:
        # Validate prerequisites
        if not state.current_answer or not state.current_question:
            state.last_error = "Missing answer or question for validation"
            return state
        
        # Use different validation strategies based on question type
        if state.question_type == "multiple_choice":
            result = validate_multiple_choice_answer(state)
        elif state.question_type == "true_false":
            result = validate_true_false_answer(state)
        else:
            # Use LLM for open-ended and complex answers
            prompt = format_answer_validation_prompt(state)
            response = asyncio.run(safe_llm_call(llm, prompt))
            result = extract_json_from_response(response)
        
        if "error" in result:
            logger.error(f"Answer validation failed: {result['error']}")
            state.last_error = "Failed to validate answer. Please try again."
            return state
        
        # Extract validation results
        is_correct = result.get("is_correct", False)
        partial_credit = result.get("partial_credit", False)
        score_percentage = result.get("score_percentage", 0 if not is_correct else 100)
        feedback = result.get("feedback", "No feedback available")
        
        # Update state
        state.answer_is_correct = is_correct
        state.answer_feedback = feedback
        
        # Add detailed answer record
        state.add_answer_record(
            question=state.current_question,
            user_answer=state.current_answer,
            correct_answer=state.correct_answer,
            is_correct=is_correct,
            feedback=feedback,
            explanation=result.get("explanation", "")
        )
        
        # Update phase
        state.current_phase = "question_answered"
        
        logger.info(f"Answer validated: {'Correct' if is_correct else 'Incorrect'} ({score_percentage}%)")
        
        return state
        
    except Exception as e:
        logger.error(f"Answer validator error: {str(e)}")
        state.last_error = f"Answer validation failed: {str(e)}"
        return state

def validate_answer_validator_prerequisites(state: QuizState) -> list[str]:
    """Validate that state meets answer validator prerequisites"""
    errors = []
    
    if not hasattr(state, 'current_answer') or not state.current_answer:
        errors.append("Answer validator requires 'current_answer' field")
    
    if not hasattr(state, 'current_question') or not state.current_question:
        errors.append("Answer validator requires 'current_question' field")
    
    if not hasattr(state, 'correct_answer') or not state.correct_answer:
        errors.append("Answer validator requires 'correct_answer' field")
    
    return errors 