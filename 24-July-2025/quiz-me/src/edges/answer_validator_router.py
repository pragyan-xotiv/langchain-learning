"""Answer Validator Router for the Interactive Quiz Generator

This module implements routing logic after answer validation, handling validation
results, correctness-based routing, and feedback management.
"""

from typing import Optional, Dict, Any
import logging

from ..state import QuizState

logger = logging.getLogger(__name__)

def route_after_answer_validation(state: QuizState) -> str:
    """
    Route after answer validation based on validation results.
    
    Args:
        state: Current quiz state with answer validation results
        
    Returns:
        Next node identifier based on validation outcome
    """
    logger.info(f"Routing after answer validation: correct={state.answer_is_correct}, phase='{state.current_phase}'")
    
    try:
        # Check if validation was successful
        if state.answer_is_correct is not None:
            # Validation completed successfully
            return route_based_on_correctness(state)
        
        else:
            # Validation failed or error occurred
            logger.warning("Answer validation failed or returned no result")
            return handle_validation_errors(state)
            
    except Exception as e:
        logger.error(f"Answer validator routing error: {str(e)}")
        return handle_validation_exception(state, str(e))

def route_based_on_correctness(state: QuizState) -> str:
    """
    Route based on whether the answer was correct or incorrect.
    
    Args:
        state: Current quiz state with validation results
        
    Returns:
        Next node based on answer correctness
    """
    logger.debug(f"Routing based on correctness: {state.answer_is_correct}")
    
    # Update phase to indicate question has been answered
    state.current_phase = "question_answered"
    
    # Continue to score generation regardless of correctness
    # The score generator will handle scoring and determine next steps
    return "score_generator"

def handle_validation_errors(state: QuizState) -> str:
    """
    Handle answer validation errors with appropriate recovery.
    
    Args:
        state: Current quiz state with validation error
        
    Returns:
        Next node for error recovery
    """
    logger.info("Handling answer validation errors")
    
    # Check retry count to avoid infinite loops
    if state.retry_count >= 3:
        logger.warning("Maximum validation retries reached")
        return handle_max_validation_retries(state)
    
    # Analyze the validation error
    error_type = analyze_validation_error(state)
    
    if error_type == "empty_answer":
        return handle_empty_answer(state)
    elif error_type == "invalid_format":
        return handle_invalid_format(state)
    elif error_type == "llm_error":
        return handle_llm_validation_error(state)
    elif error_type == "timeout_error":
        return handle_timeout_error(state)
    else:
        # Generic error handling
        return retry_answer_validation(state)

def handle_validation_exception(state: QuizState, error_message: str) -> str:
    """
    Handle technical exceptions during validation.
    
    Args:
        state: Current quiz state
        error_message: Exception message
        
    Returns:
        Next node for exception recovery
    """
    logger.error(f"Handling validation exception: {error_message}")
    
    # Store error context
    state.quiz_metadata["validation_exception"] = {
        "error": error_message,
        "question": state.current_question,
        "answer": state.current_answer
    }
    
    # Classify exception type
    error_lower = error_message.lower()
    
    if "network" in error_lower or "connection" in error_lower:
        return handle_network_validation_error(state)
    elif "json" in error_lower or "parsing" in error_lower:
        return handle_parsing_validation_error(state)
    else:
        return handle_generic_validation_error(state)

# === ERROR TYPE HANDLERS ===

def handle_empty_answer(state: QuizState) -> str:
    """Handle case where user provided empty answer"""
    logger.info("Handling empty answer submission")
    
    # Ask user to provide an answer
    state.quiz_metadata["validation_error_type"] = "empty_answer"
    state.quiz_metadata["retry_request"] = "Please provide an answer to the question."
    
    return "clarification_handler"

def handle_invalid_format(state: QuizState) -> str:
    """Handle case where answer format is invalid"""
    logger.info("Handling invalid answer format")
    
    # Provide format guidance based on question type
    format_guidance = get_format_guidance(state.question_type)
    
    state.quiz_metadata["validation_error_type"] = "invalid_format"
    state.quiz_metadata["format_guidance"] = format_guidance
    state.quiz_metadata["retry_request"] = f"Please provide your answer in the correct format: {format_guidance}"
    
    return "clarification_handler"

def handle_llm_validation_error(state: QuizState) -> str:
    """Handle LLM errors during validation"""
    logger.info("Handling LLM validation error")
    
    if state.retry_count < 3:
        state.retry_count += 1
        logger.info(f"Retrying answer validation (attempt {state.retry_count})")
        return "answer_validator"
    else:
        # Use fallback validation method
        return use_fallback_validation(state)

def handle_timeout_error(state: QuizState) -> str:
    """Handle timeout errors during validation"""
    logger.info("Handling validation timeout error")
    
    if state.retry_count < 2:  # Fewer retries for timeout
        state.retry_count += 1
        return "answer_validator"
    else:
        # Skip validation and move on
        return skip_validation_and_continue(state)

def handle_network_validation_error(state: QuizState) -> str:
    """Handle network errors during validation"""
    logger.info("Handling network validation error")
    
    if state.retry_count < 2:
        state.retry_count += 1
        return "answer_validator"
    else:
        # Use offline validation if possible
        return try_offline_validation(state)

def handle_parsing_validation_error(state: QuizState) -> str:
    """Handle JSON/parsing errors during validation"""
    logger.info("Handling parsing validation error")
    
    # These errors might be due to malformed LLM response
    if state.retry_count < 3:
        state.retry_count += 1
        return "answer_validator"
    else:
        # Use simple validation rules
        return use_simple_validation(state)

def handle_generic_validation_error(state: QuizState) -> str:
    """Handle generic validation errors"""
    logger.info("Handling generic validation error")
    
    state.quiz_metadata["validation_error_type"] = "generic"
    return "error_recovery_handler"

def handle_max_validation_retries(state: QuizState) -> str:
    """Handle case where maximum validation retries reached"""
    logger.warning("Maximum answer validation retries reached")
    
    # Try to continue quiz by accepting answer as-is or skipping
    if should_skip_validation(state):
        return skip_validation_and_continue(state)
    else:
        # Ask user for different answer or clarification
        state.quiz_metadata["max_retries_reached"] = True
        return "clarification_handler"

# === FALLBACK VALIDATION METHODS ===

def use_fallback_validation(state: QuizState) -> str:
    """Use fallback validation when LLM validation fails"""
    logger.info("Using fallback validation method")
    
    # Attempt simple rule-based validation
    validation_result = perform_simple_validation(state)
    
    if validation_result is not None:
        # Simple validation succeeded
        state.answer_is_correct = validation_result
        state.answer_feedback = "Answer validated using simplified method."
        return "score_generator"
    else:
        # Even simple validation failed
        return skip_validation_and_continue(state)

def try_offline_validation(state: QuizState) -> str:
    """Try offline validation methods"""
    logger.info("Attempting offline validation")
    
    # Use simple string matching for certain question types
    if state.question_type in ["multiple_choice", "true_false"]:
        result = perform_offline_validation(state)
        if result is not None:
            state.answer_is_correct = result
            state.answer_feedback = "Answer validated offline."
            return "score_generator"
    
    # Fall back to skipping validation
    return skip_validation_and_continue(state)

def use_simple_validation(state: QuizState) -> str:
    """Use simple validation rules"""
    logger.info("Using simple validation rules")
    
    result = perform_simple_validation(state)
    
    if result is not None:
        state.answer_is_correct = result
        state.answer_feedback = "Answer validated using basic rules."
        return "score_generator"
    else:
        # Mark as partially correct and continue
        state.answer_is_correct = True  # Benefit of the doubt
        state.answer_feedback = "Unable to validate answer fully, marked as correct."
        return "score_generator"

def skip_validation_and_continue(state: QuizState) -> str:
    """Skip validation and continue with quiz"""
    logger.info("Skipping answer validation and continuing")
    
    # Mark answer as correct to avoid penalizing user for technical issues
    state.answer_is_correct = True
    state.answer_feedback = "Technical issue during validation. Answer accepted."
    
    # Note the skip in metadata
    state.quiz_metadata["validation_skipped"] = True
    state.quiz_metadata["skip_reason"] = "Technical validation failure"
    
    return "score_generator"

def retry_answer_validation(state: QuizState) -> str:
    """Retry answer validation with incremented count"""
    state.retry_count += 1
    logger.info(f"Retrying answer validation (attempt {state.retry_count})")
    return "answer_validator"

# === VALIDATION HELPERS ===

def analyze_validation_error(state: QuizState) -> str:
    """
    Analyze validation error to determine type.
    
    Args:
        state: Current quiz state
        
    Returns:
        Error type classification
    """
    error_message = state.last_error or ""
    answer = state.current_answer or ""
    
    # Check for empty answer
    if not answer.strip():
        return "empty_answer"
    
    # Check error message patterns
    error_lower = error_message.lower()
    
    if "format" in error_lower or "invalid" in error_lower:
        return "invalid_format"
    
    if "llm" in error_lower or "api" in error_lower:
        return "llm_error"
    
    if "timeout" in error_lower or "took too long" in error_lower:
        return "timeout_error"
    
    if "network" in error_lower or "connection" in error_lower:
        return "network_error"
    
    return "unknown_error"

def get_format_guidance(question_type: Optional[str]) -> str:
    """
    Get format guidance for different question types.
    
    Args:
        question_type: Type of question
        
    Returns:
        Format guidance string
    """
    guidance = {
        "multiple_choice": "Select A, B, C, or D",
        "true_false": "Answer True or False",
        "fill_in_blank": "Provide the missing word or phrase",
        "open_ended": "Provide a complete answer in your own words"
    }
    
    return guidance.get(question_type, "Provide your answer clearly")

def perform_simple_validation(state: QuizState) -> Optional[bool]:
    """
    Perform simple rule-based validation.
    
    Args:
        state: Current quiz state
        
    Returns:
        True if correct, False if incorrect, None if cannot determine
    """
    if not state.current_answer or not state.correct_answer:
        return None
    
    user_answer = state.current_answer.strip().lower()
    correct_answer = state.correct_answer.strip().lower()
    
    # Exact match
    if user_answer == correct_answer:
        return True
    
    # Handle multiple choice
    if state.question_type == "multiple_choice":
        # Check various formats (A, a, 1, first, etc.)
        return validate_multiple_choice_simple(user_answer, correct_answer)
    
    # Handle true/false
    if state.question_type == "true_false":
        return validate_true_false_simple(user_answer, correct_answer)
    
    # For other types, cannot determine with simple rules
    return None

def perform_offline_validation(state: QuizState) -> Optional[bool]:
    """
    Perform offline validation for certain question types.
    
    Args:
        state: Current quiz state
        
    Returns:
        Validation result or None if cannot validate offline
    """
    # This is a simplified version of the validation logic from answer_validator node
    if state.question_type == "multiple_choice":
        from ..nodes.answer_validator import validate_multiple_choice_answer
        result = validate_multiple_choice_answer(state)
        return result.get("is_correct")
    
    elif state.question_type == "true_false":
        from ..nodes.answer_validator import validate_true_false_answer
        result = validate_true_false_answer(state)
        return result.get("is_correct")
    
    return None

def validate_multiple_choice_simple(user_answer: str, correct_answer: str) -> bool:
    """Simple multiple choice validation"""
    # Normalize answers
    letter_to_number = {'a': '0', 'b': '1', 'c': '2', 'd': '3'}
    number_to_letter = {'0': 'a', '1': 'b', '2': 'c', '3': 'd'}
    
    # Try direct match
    if user_answer == correct_answer:
        return True
    
    # Try letter/number conversion
    if user_answer in letter_to_number and correct_answer in number_to_letter:
        return letter_to_number[user_answer] == correct_answer
    
    if user_answer in number_to_letter and correct_answer in letter_to_number:
        return user_answer == letter_to_number[correct_answer]
    
    return False

def validate_true_false_simple(user_answer: str, correct_answer: str) -> bool:
    """Simple true/false validation"""
    true_values = {'true', 't', 'yes', 'y', '1'}
    false_values = {'false', 'f', 'no', 'n', '0'}
    
    # Normalize both answers
    user_normalized = 'true' if user_answer in true_values else 'false' if user_answer in false_values else None
    correct_normalized = 'true' if correct_answer in true_values else 'false' if correct_answer in false_values else None
    
    if user_normalized and correct_normalized:
        return user_normalized == correct_normalized
    
    return False

def should_skip_validation(state: QuizState) -> bool:
    """
    Determine if validation should be skipped.
    
    Args:
        state: Current quiz state
        
    Returns:
        True if validation should be skipped
    """
    # Skip if we've had too many failures and want to keep quiz flowing
    return (
        state.retry_count >= 3 and
        state.total_questions_answered > 0  # Don't skip on first question
    )

# === ROUTING VALIDATION ===

def validate_answer_validator_routing(state: QuizState, next_node: str) -> bool:
    """
    Validate answer validator routing decision.
    
    Args:
        state: Current quiz state
        next_node: Proposed next node
        
    Returns:
        True if routing is valid
    """
    # Valid nodes after answer validation
    valid_nodes = [
        "score_generator",           # Normal flow after validation
        "answer_validator",          # Retry validation
        "clarification_handler",     # Ask for better answer
        "error_recovery_handler",    # Handle serious errors
        "quiz_completion_handler"    # End quiz due to issues
    ]
    
    if next_node not in valid_nodes:
        logger.warning(f"Invalid node '{next_node}' after answer validation")
        return False
    
    # Specific validations
    if next_node == "score_generator":
        if state.answer_is_correct is None:
            logger.warning("Cannot route to score_generator without validation result")
            return False
    
    return True

if __name__ == "__main__":
    # Test answer validator routing
    from ..state import create_test_state
    
    # Test correct answer
    state = create_test_state()
    state.current_answer = "4"
    state.correct_answer = "4"
    state.answer_is_correct = True
    result = route_after_answer_validation(state)
    print(f"Correct answer: {result}")
    
    # Test incorrect answer
    state = create_test_state()
    state.current_answer = "5"
    state.correct_answer = "4"
    state.answer_is_correct = False
    result = route_after_answer_validation(state)
    print(f"Incorrect answer: {result}")
    
    # Test validation error
    state = create_test_state()
    state.current_answer = "4"
    state.answer_is_correct = None
    state.last_error = "Validation failed"
    result = route_after_answer_validation(state)
    print(f"Validation error: {result}")
    
    # Test simple validation
    state = create_test_state()
    state.current_answer = "a"
    state.correct_answer = "0"
    state.question_type = "multiple_choice"
    result = perform_simple_validation(state)
    print(f"Simple validation result: {result}") 