"""Score Generator Router for the Interactive Quiz Generator

This module implements routing logic after score generation, handling quiz
completion, continuation decisions, and progress management.
"""

from typing import Optional, Dict, Any
import logging

from ..state import QuizState

logger = logging.getLogger(__name__)

def route_after_scoring(state: QuizState) -> str:
    """
    Route after score generation based on quiz status and completion.
    
    Args:
        state: Current quiz state with updated scores
        
    Returns:
        Next node identifier based on quiz status
    """
    logger.info(f"Routing after scoring: completed={state.quiz_completed}, questions={state.total_questions_answered}/{state.max_questions}")
    
    try:
        # Check if quiz is completed
        if state.quiz_completed:
            return handle_quiz_completion(state)
        
        else:
            # Quiz continues - determine next step
            return determine_continuation_flow(state)
            
    except Exception as e:
        logger.error(f"Score generator routing error: {str(e)}")
        return handle_scoring_error(state, str(e))

def handle_quiz_completion(state: QuizState) -> str:
    """
    Handle quiz completion with final results and options.
    
    Args:
        state: Current quiz state with completed quiz
        
    Returns:
        Next node for quiz completion handling
    """
    logger.info("Handling quiz completion")
    
    # Update final state
    state.current_phase = "quiz_complete"
    state.quiz_active = False
    
    # Calculate final statistics
    calculate_final_statistics(state)
    
    # Determine completion type
    completion_type = determine_completion_type(state)
    
    # Store completion metadata
    state.quiz_metadata["completion_type"] = completion_type
    state.quiz_metadata["final_statistics"] = get_final_statistics(state)
    
    logger.info(f"Quiz completed: {completion_type}, Score: {state.total_score}, Accuracy: {state.calculate_accuracy()}%")
    
    # Route to completion handler or present results
    return "quiz_completion_handler"

def determine_continuation_flow(state: QuizState) -> str:
    """
    Determine how quiz should continue after scoring.
    
    Args:
        state: Current quiz state
        
    Returns:
        Next node for quiz continuation
    """
    logger.debug("Determining quiz continuation flow")
    
    # Check various continuation conditions
    if should_check_user_intent(state):
        return check_user_continuation_intent(state)
    
    elif should_auto_continue(state):
        return continue_quiz_automatically(state)
    
    elif should_pause_for_feedback(state):
        return pause_for_feedback(state)
    
    else:
        # Default continuation
        return continue_to_next_question(state)

def handle_scoring_error(state: QuizState, error_message: str) -> str:
    """
    Handle errors during score generation routing.
    
    Args:
        state: Current quiz state
        error_message: Error message
        
    Returns:
        Next node for error recovery
    """
    logger.error(f"Handling scoring error: {error_message}")
    
    # Store error context
    state.quiz_metadata["scoring_error"] = {
        "error": error_message,
        "context": "score_generator_routing"
    }
    
    # Try to continue quiz despite error
    if can_continue_despite_error(state):
        logger.info("Continuing quiz despite scoring error")
        return continue_to_next_question(state)
    else:
        logger.warning("Cannot continue quiz due to scoring error")
        return "error_recovery_handler"

# === COMPLETION HANDLERS ===

def determine_completion_type(state: QuizState) -> str:
    """
    Determine how the quiz was completed.
    
    Args:
        state: Current quiz state
        
    Returns:
        Completion type identifier
    """
    if state.total_questions_answered >= (state.max_questions or 10):
        return "normal_completion"
    
    elif state.quiz_metadata.get("ended_due_to_generation_failure"):
        return "technical_completion"
    
    elif state.quiz_metadata.get("user_requested_end"):
        return "user_ended"
    
    elif state.quiz_metadata.get("max_retries_reached"):
        return "error_completion"
    
    else:
        return "unknown_completion"

def calculate_final_statistics(state: QuizState):
    """Calculate and store final quiz statistics"""
    accuracy = state.calculate_accuracy()
    
    # Performance categories
    if accuracy >= 90:
        performance = "excellent"
    elif accuracy >= 80:
        performance = "good"
    elif accuracy >= 70:
        performance = "fair"
    elif accuracy >= 60:
        performance = "needs_improvement"
    else:
        performance = "poor"
    
    # Store in metadata
    state.quiz_metadata.update({
        "final_accuracy": accuracy,
        "performance_category": performance,
        "total_points": state.total_score,
        "questions_attempted": state.total_questions_answered,
        "correct_answers": state.correct_answers_count,
        "completion_timestamp": state.updated_at.isoformat() if state.updated_at else None
    })

def get_final_statistics(state: QuizState) -> Dict[str, Any]:
    """Get final statistics dictionary"""
    return {
        "accuracy": state.calculate_accuracy(),
        "total_score": state.total_score,
        "questions_answered": state.total_questions_answered,
        "correct_count": state.correct_answers_count,
        "performance": state.quiz_metadata.get("performance_category", "unknown"),
        "topic": state.topic,
        "completion_type": state.quiz_metadata.get("completion_type", "unknown")
    }

# === CONTINUATION HANDLERS ===

def should_check_user_intent(state: QuizState) -> bool:
    """Check if we should ask user about continuation"""
    # For infinite quizzes or when approaching limits
    return (
        state.quiz_type == "infinite" or
        (state.max_questions and state.total_questions_answered >= state.max_questions * 0.8)
    )

def should_auto_continue(state: QuizState) -> bool:
    """Check if quiz should auto-continue"""
    return (
        state.quiz_type == "finite" and
        state.max_questions and
        state.total_questions_answered < state.max_questions and
        not state.quiz_metadata.get("user_pause_requested")
    )

def should_pause_for_feedback(state: QuizState) -> bool:
    """Check if we should pause for user feedback"""
    # Pause every 5 questions for longer quizzes
    return (
        state.total_questions_answered > 0 and
        state.total_questions_answered % 5 == 0 and
        state.total_questions_answered < (state.max_questions or 10)
    )

def check_user_continuation_intent(state: QuizState) -> str:
    """Check user's intent for quiz continuation"""
    logger.info("Checking user continuation intent")
    
    # Set up context for asking user
    state.quiz_metadata["continuation_check"] = {
        "questions_answered": state.total_questions_answered,
        "current_score": state.total_score,
        "accuracy": state.calculate_accuracy()
    }
    
    # Route to a handler that will ask user if they want to continue
    return "continuation_check_handler"

def continue_quiz_automatically(state: QuizState) -> str:
    """Continue quiz automatically to next question"""
    logger.info("Continuing quiz automatically")
    
    # Move to next question
    state.increment_question()
    state.current_phase = "quiz_active"
    
    # Generate next question
    return "quiz_generator"

def pause_for_feedback(state: QuizState) -> str:
    """Pause quiz to provide feedback"""
    logger.info("Pausing quiz for feedback")
    
    # Set up feedback context
    state.quiz_metadata["feedback_pause"] = {
        "milestone": state.total_questions_answered,
        "performance_so_far": state.calculate_accuracy(),
        "encouragement_needed": state.calculate_accuracy() < 60
    }
    
    return "feedback_handler"

def continue_to_next_question(state: QuizState) -> str:
    """Continue to next question in quiz"""
    logger.debug("Continuing to next question")
    
    # Prepare for next question
    state.increment_question()
    state.current_phase = "quiz_active"
    
    return "quiz_generator"

# === ERROR HANDLING ===

def can_continue_despite_error(state: QuizState) -> bool:
    """
    Determine if quiz can continue despite scoring error.
    
    Args:
        state: Current quiz state
        
    Returns:
        True if quiz can continue
    """
    # Continue if we have valid questions answered and no critical errors
    return (
        state.total_questions_answered >= 0 and  # Even 0 is okay
        not state.quiz_metadata.get("critical_error") and
        state.retry_count < 5
    )

# === SPECIAL FLOW HANDLERS ===

def handle_infinite_quiz_continuation(state: QuizState) -> str:
    """Handle continuation logic for infinite quizzes"""
    logger.debug("Handling infinite quiz continuation")
    
    # Check for natural stopping points
    if state.total_questions_answered >= 50:  # Reasonable limit
        logger.info("Infinite quiz reached reasonable limit")
        state.quiz_completed = True
        return handle_quiz_completion(state)
    
    # Check if user wants to continue (should be in user_intent)
    if state.user_intent == "continue":
        return continue_to_next_question(state)
    elif state.user_intent in ["stop", "done", "exit"]:
        state.quiz_completed = True
        return handle_quiz_completion(state)
    else:
        # Ask user if they want to continue
        return check_user_continuation_intent(state)

def handle_performance_based_routing(state: QuizState) -> str:
    """Handle routing based on user performance"""
    accuracy = state.calculate_accuracy()
    
    if accuracy < 30 and state.total_questions_answered >= 3:
        # User struggling significantly
        logger.info("User struggling - offering help or topic change")
        state.quiz_metadata["struggling_user"] = True
        return "struggling_user_handler"
    
    elif accuracy > 95 and state.total_questions_answered >= 5:
        # User excelling - offer harder questions or completion
        logger.info("User excelling - offering advanced options")
        state.quiz_metadata["excelling_user"] = True
        return "excelling_user_handler"
    
    else:
        # Normal continuation
        return continue_to_next_question(state)

def handle_milestone_celebration(state: QuizState) -> str:
    """Handle milestone celebrations in quiz"""
    milestones = [5, 10, 15, 20, 25]
    
    if state.total_questions_answered in milestones:
        logger.info(f"Celebrating milestone: {state.total_questions_answered} questions")
        
        state.quiz_metadata["milestone_reached"] = {
            "questions": state.total_questions_answered,
            "accuracy": state.calculate_accuracy(),
            "score": state.total_score
        }
        
        return "milestone_celebration_handler"
    
    return continue_to_next_question(state)

# === ROUTING DECISION HELPERS ===

def get_continuation_options(state: QuizState) -> Dict[str, str]:
    """
    Get available continuation options based on current state.
    
    Args:
        state: Current quiz state
        
    Returns:
        Dictionary of option descriptions and their routing destinations
    """
    options = {}
    
    # Always available options
    options["continue"] = "Continue with next question"
    options["end"] = "End quiz and see results"
    
    # Conditional options
    if state.total_questions_answered >= 3:
        options["change_topic"] = "Change to different topic"
    
    if state.calculate_accuracy() < 60:
        options["get_help"] = "Get help with current topic"
    
    if state.quiz_type == "finite" and state.total_questions_answered < (state.max_questions or 10):
        options["extend"] = "Add more questions to quiz"
    
    return options

def should_offer_topic_change(state: QuizState) -> bool:
    """Check if topic change should be offered"""
    return (
        state.total_questions_answered >= 3 and
        (state.calculate_accuracy() < 40 or  # Struggling
         state.quiz_metadata.get("user_boredom_indicators"))
    )

def should_offer_difficulty_adjustment(state: QuizState) -> bool:
    """Check if difficulty adjustment should be offered"""
    accuracy = state.calculate_accuracy()
    return (
        state.total_questions_answered >= 3 and
        (accuracy > 90 or accuracy < 40)  # Too easy or too hard
    )

# === ROUTING VALIDATION ===

def validate_score_generator_routing(state: QuizState, next_node: str) -> bool:
    """
    Validate score generator routing decision.
    
    Args:
        state: Current quiz state
        next_node: Proposed next node
        
    Returns:
        True if routing is valid
    """
    # Valid nodes after score generation
    valid_nodes = [
        "quiz_generator",               # Continue with next question
        "quiz_completion_handler",      # Quiz finished
        "continuation_check_handler",   # Ask user about continuation
        "feedback_handler",             # Provide feedback
        "milestone_celebration_handler", # Celebrate milestones
        "struggling_user_handler",      # Help struggling users
        "excelling_user_handler",       # Challenge excelling users
        "error_recovery_handler",       # Handle errors
        "query_analyzer"                # Get user input for continuation
    ]
    
    if next_node not in valid_nodes:
        logger.warning(f"Invalid node '{next_node}' after score generation")
        return False
    
    # Specific validations
    if next_node == "quiz_completion_handler":
        if not state.quiz_completed:
            logger.warning("Cannot route to completion handler if quiz not completed")
            return False
    
    if next_node == "quiz_generator":
        if state.quiz_completed:
            logger.warning("Cannot generate more questions if quiz completed")
            return False
    
    return True

if __name__ == "__main__":
    # Test score generator routing
    from ..state import create_test_state
    
    # Test quiz completion
    state = create_test_state()
    state.quiz_completed = True
    state.total_questions_answered = 10
    state.correct_answers_count = 8
    result = route_after_scoring(state)
    print(f"Quiz completed: {result}")
    
    # Test quiz continuation
    state = create_test_state()
    state.quiz_completed = False
    state.total_questions_answered = 3
    state.max_questions = 10
    result = route_after_scoring(state)
    print(f"Quiz continuing: {result}")
    
    # Test performance-based routing
    state = create_test_state()
    state.total_questions_answered = 5
    state.correct_answers_count = 1  # Poor performance
    result = handle_performance_based_routing(state)
    print(f"Poor performance routing: {result}")
    
    # Test continuation options
    state = create_test_state()
    state.total_questions_answered = 5
    state.correct_answers_count = 3
    options = get_continuation_options(state)
    print(f"Continuation options: {options}") 