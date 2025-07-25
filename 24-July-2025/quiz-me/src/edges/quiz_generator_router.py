"""Quiz Generator Router for the Interactive Quiz Generator

This module implements routing logic after quiz generation, handling question
generation results, failure recovery, and quiz flow management.
"""

from typing import Optional, Dict, List
import logging

from ..state import QuizState

logger = logging.getLogger(__name__)

def route_after_question_generation(state: QuizState) -> str:
    """
    Route after question generation based on generation results.
    
    Args:
        state: Current quiz state with question generation results
        
    Returns:
        Next node identifier based on generation outcome
    """
    logger.info(f"Routing after question generation: question='{state.current_question is not None}', phase='{state.current_phase}'")
    
    try:
        # Check if question was generated successfully
        if state.current_question and state.correct_answer:
            logger.info("Question generated successfully")
            return determine_next_question_flow(state)
        
        else:
            # Question generation failed
            logger.warning("Question generation failed")
            return handle_generation_failure(state)
            
    except Exception as e:
        logger.error(f"Quiz generator routing error: {str(e)}")
        return handle_generation_error(state, str(e))

def determine_next_question_flow(state: QuizState) -> str:
    """
    Determine the next step in quiz flow after successful question generation.
    
    Args:
        state: Current quiz state with generated question
        
    Returns:
        Next node in the quiz flow
    """
    logger.debug("Determining next question flow")
    
    # For normal quiz flow, present question to user for answering
    # This typically means going to a node that handles question presentation
    # and waits for user answer, which then routes to answer_validator
    
    # Check if this is the first question or a continuation
    if state.current_question_index == 0:
        logger.info("Presenting first question of quiz")
    else:
        logger.info(f"Presenting question {state.current_question_index + 1}")
    
    # Update state to indicate we're ready for an answer
    state.current_phase = "quiz_active"
    
    # In the actual workflow, this might route to a question presenter node
    # For now, we'll route to query_analyzer to get user's answer
    return "query_analyzer"

def handle_generation_failure(state: QuizState) -> str:
    """
    Handle question generation failure with appropriate recovery.
    
    Args:
        state: Current quiz state with failed generation
        
    Returns:
        Next node for recovery
    """
    logger.info("Handling question generation failure")
    
    # Check retry count to avoid infinite loops
    if state.retry_count >= 3:
        logger.warning("Maximum generation retries reached")
        return handle_max_generation_retries(state)
    
    # Analyze the failure reason
    failure_reason = analyze_generation_failure(state)
    
    if failure_reason == "topic_exhausted":
        return handle_topic_exhausted(state)
    elif failure_reason == "difficulty_mismatch":
        return handle_difficulty_adjustment(state)
    elif failure_reason == "format_issue":
        return handle_format_issue(state)
    elif failure_reason == "llm_error":
        return handle_llm_generation_error(state)
    else:
        # Generic failure handling
        return retry_question_generation(state)

def handle_generation_error(state: QuizState, error_message: str) -> str:
    """
    Handle technical errors during question generation.
    
    Args:
        state: Current quiz state
        error_message: Error message from generation
        
    Returns:
        Next node for error recovery
    """
    logger.error(f"Handling generation error: {error_message}")
    
    # Classify error type
    error_lower = error_message.lower()
    
    if "network" in error_lower or "timeout" in error_lower:
        return handle_network_generation_error(state)
    elif "api" in error_lower or "llm" in error_lower:
        return handle_llm_generation_error(state)
    elif "validation" in error_lower:
        return handle_validation_generation_error(state)
    else:
        return handle_generic_generation_error(state)

# === FAILURE TYPE HANDLERS ===

def handle_topic_exhausted(state: QuizState) -> str:
    """Handle case where topic has been exhausted for questions"""
    logger.info("Handling topic exhausted scenario")
    
    # Check if we have answered enough questions to consider quiz complete
    min_questions = 3  # Minimum questions for a valid quiz
    
    if state.total_questions_answered >= min_questions:
        logger.info("Sufficient questions answered, completing quiz")
        state.quiz_completed = True
        state.current_phase = "quiz_complete"
        return "quiz_completion_handler"
    
    else:
        logger.info("Insufficient questions, requesting topic expansion")
        state.quiz_metadata["topic_exhausted"] = True
        state.quiz_metadata["expansion_needed"] = True
        return "topic_expansion_handler"

def handle_difficulty_adjustment(state: QuizState) -> str:
    """Handle difficulty level adjustment needed"""
    logger.info("Handling difficulty adjustment")
    
    # Adjust difficulty based on user performance
    current_accuracy = state.calculate_accuracy() if state.total_questions_answered > 0 else 0.5
    
    if current_accuracy > 0.8:
        # User performing well, increase difficulty
        adjust_difficulty_up(state)
    elif current_accuracy < 0.4:
        # User struggling, decrease difficulty
        adjust_difficulty_down(state)
    
    # Retry generation with adjusted difficulty
    state.retry_count += 1
    return "quiz_generator"

def handle_format_issue(state: QuizState) -> str:
    """Handle question format issues"""
    logger.info("Handling question format issue")
    
    # Try different question type
    current_type = state.question_type
    alternative_types = get_alternative_question_types(current_type)
    
    if alternative_types:
        # Store original type and try alternative
        state.quiz_metadata["original_question_type"] = current_type
        state.quiz_metadata["format_fallback"] = True
        
        # This would be handled by the quiz generator to try different format
        state.retry_count += 1
        return "quiz_generator"
    
    else:
        # No alternatives available
        return handle_no_format_alternatives(state)

def handle_max_generation_retries(state: QuizState) -> str:
    """Handle case where maximum generation retries reached"""
    logger.warning("Maximum question generation retries reached")
    
    # Check if we can end quiz gracefully
    if state.total_questions_answered > 0:
        logger.info("Ending quiz due to generation issues")
        state.quiz_completed = True
        state.current_phase = "quiz_complete"
        state.quiz_metadata["ended_due_to_generation_failure"] = True
        return "quiz_completion_handler"
    
    else:
        # No questions answered, this is a more serious issue
        logger.error("Cannot generate any questions for this topic")
        state.quiz_metadata["generation_completely_failed"] = True
        return "topic_selection_fallback"

# === ERROR TYPE HANDLERS ===

def handle_network_generation_error(state: QuizState) -> str:
    """Handle network errors during generation"""
    logger.info("Handling network generation error")
    
    if state.retry_count < 2:  # Fewer retries for network issues
        state.retry_count += 1
        return "quiz_generator"
    else:
        return "network_error_handler"

def handle_llm_generation_error(state: QuizState) -> str:
    """Handle LLM errors during generation"""
    logger.info("Handling LLM generation error")
    
    if state.retry_count < 3:
        state.retry_count += 1
        return "quiz_generator"
    else:
        # Switch to fallback generation mode
        state.quiz_metadata["llm_fallback_mode"] = True
        return "fallback_generator"

def handle_validation_generation_error(state: QuizState) -> str:
    """Handle validation errors during generation"""
    logger.info("Handling validation generation error")
    
    # These might be fixable by adjusting generation parameters
    state.quiz_metadata["validation_error_adjustment"] = True
    state.retry_count += 1
    
    if state.retry_count < 3:
        return "quiz_generator"
    else:
        return "clarification_handler"

def handle_generic_generation_error(state: QuizState) -> str:
    """Handle generic generation errors"""
    logger.info("Handling generic generation error")
    
    state.quiz_metadata["generic_error"] = True
    return "error_recovery_handler"

# === QUIZ FLOW HELPERS ===

def retry_question_generation(state: QuizState) -> str:
    """Retry question generation with incremented retry count"""
    state.retry_count += 1
    logger.info(f"Retrying question generation (attempt {state.retry_count})")
    return "quiz_generator"

def adjust_difficulty_up(state: QuizState):
    """Adjust quiz difficulty upward"""
    current_level = state.quiz_metadata.get("difficulty_level", "medium")
    
    difficulty_progression = {
        "beginner": "medium",
        "easy": "medium", 
        "medium": "hard",
        "intermediate": "hard",
        "hard": "advanced",
        "advanced": "expert"
    }
    
    new_level = difficulty_progression.get(current_level, "hard")
    state.quiz_metadata["difficulty_level"] = new_level
    state.quiz_metadata["difficulty_adjusted"] = "increased"
    
    logger.info(f"Difficulty adjusted from {current_level} to {new_level}")

def adjust_difficulty_down(state: QuizState):
    """Adjust quiz difficulty downward"""
    current_level = state.quiz_metadata.get("difficulty_level", "medium")
    
    difficulty_regression = {
        "expert": "advanced",
        "advanced": "hard",
        "hard": "medium",
        "intermediate": "medium",
        "medium": "easy",
        "easy": "beginner",
        "beginner": "beginner"  # Can't go lower
    }
    
    new_level = difficulty_regression.get(current_level, "easy")
    state.quiz_metadata["difficulty_level"] = new_level
    state.quiz_metadata["difficulty_adjusted"] = "decreased"
    
    logger.info(f"Difficulty adjusted from {current_level} to {new_level}")

def get_alternative_question_types(current_type: Optional[str]) -> List[str]:
    """
    Get alternative question types to try.
    
    Args:
        current_type: Current question type that failed
        
    Returns:
        List of alternative question types
    """
    all_types = ["multiple_choice", "true_false", "open_ended", "fill_in_blank"]
    
    if current_type in all_types:
        alternatives = [t for t in all_types if t != current_type]
    else:
        alternatives = all_types
    
    # Prefer easier formats when having trouble
    preferred_order = ["multiple_choice", "true_false", "fill_in_blank", "open_ended"]
    
    # Sort alternatives by preference
    sorted_alternatives = []
    for preferred in preferred_order:
        if preferred in alternatives:
            sorted_alternatives.append(preferred)
    
    return sorted_alternatives

def handle_no_format_alternatives(state: QuizState) -> str:
    """Handle case where no question format alternatives are available"""
    logger.warning("No alternative question formats available")
    
    # This suggests a fundamental issue with the topic or generation
    state.quiz_metadata["no_format_alternatives"] = True
    
    if state.total_questions_answered > 0:
        # End quiz if we have some questions
        state.quiz_completed = True
        return "quiz_completion_handler"
    else:
        # Go back to topic selection
        return "topic_validator"

# === ANALYSIS HELPERS ===

def analyze_generation_failure(state: QuizState) -> str:
    """
    Analyze why question generation failed.
    
    Args:
        state: Current quiz state
        
    Returns:
        Failure type classification
    """
    error_message = state.last_error or ""
    error_lower = error_message.lower()
    
    # Check error message patterns
    if "exhausted" in error_lower or "no more questions" in error_lower:
        return "topic_exhausted"
    
    if "difficulty" in error_lower or "too hard" in error_lower or "too easy" in error_lower:
        return "difficulty_mismatch"
    
    if "format" in error_lower or "type" in error_lower:
        return "format_issue"
    
    if "llm" in error_lower or "api" in error_lower:
        return "llm_error"
    
    # Check quiz state patterns
    if state.current_question_index >= 20:  # Arbitrary high number
        return "topic_exhausted"
    
    # Default classification
    return "generation_error"

def should_continue_quiz_after_failure(state: QuizState) -> bool:
    """
    Determine if quiz should continue after generation failure.
    
    Args:
        state: Current quiz state
        
    Returns:
        True if quiz should continue
    """
    # Continue if we have answered some questions and haven't hit retry limit
    return (
        state.total_questions_answered > 0 and
        state.retry_count < 3 and
        not state.quiz_completed
    )

# === ROUTING VALIDATION ===

def validate_quiz_generator_routing(state: QuizState, next_node: str) -> bool:
    """
    Validate quiz generator routing decision.
    
    Args:
        state: Current quiz state
        next_node: Proposed next node
        
    Returns:
        True if routing is valid
    """
    # Valid nodes after quiz generation
    valid_nodes = [
        "query_analyzer",              # Present question to user
        "quiz_generator",              # Retry generation
        "quiz_completion_handler",     # End quiz due to issues
        "topic_validator",             # Return to topic selection
        "clarification_handler",       # Ask for help/clarification
        "error_recovery_handler",      # Handle errors
        "fallback_generator",          # Use fallback generation
        "network_error_handler",       # Handle network issues
        "topic_expansion_handler"      # Expand topic scope
    ]
    
    if next_node not in valid_nodes:
        logger.warning(f"Invalid node '{next_node}' after quiz generation")
        return False
    
    # Specific validations
    if next_node == "query_analyzer":
        if not (state.current_question and state.correct_answer):
            logger.warning("Cannot present question without valid question and answer")
            return False
    
    return True

if __name__ == "__main__":
    # Test quiz generator routing
    from ..state import create_test_state
    
    # Test successful generation
    state = create_test_state()
    state.current_question = "What is 2 + 2?"
    state.correct_answer = "4"
    result = route_after_question_generation(state)
    print(f"Successful generation: {result}")
    
    # Test failed generation
    state = create_test_state()
    state.current_question = None
    state.last_error = "Could not generate question"
    result = route_after_question_generation(state)
    print(f"Failed generation: {result}")
    
    # Test alternative question types
    alternatives = get_alternative_question_types("multiple_choice")
    print(f"Alternative types: {alternatives}") 