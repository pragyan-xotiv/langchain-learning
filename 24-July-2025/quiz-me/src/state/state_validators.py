"""State transition validation utilities

This module provides validation functions for ensuring state consistency
and proper transitions between states.
"""

from typing import List
from .quiz_state import QuizState

def validate_state_consistency(state: QuizState) -> List[str]:
    """
    Validate state consistency across all fields.
    
    Args:
        state: QuizState object to validate
        
    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []
    
    # Quiz activation validation
    if state.quiz_active and not state.topic_validated:
        errors.append("Quiz cannot be active without validated topic")
    
    # Question indexing validation
    if state.current_question_index > len(state.user_answers) + 1:
        errors.append("Question index inconsistent with answer history")
    
    # Scoring validation
    if state.correct_answers_count > state.total_questions_answered:
        errors.append("Correct answers cannot exceed total answered")
    
    if state.total_questions_answered != len(state.user_answers):
        errors.append("Answer history length doesn't match total questions answered")
    
    # Phase validation
    phase_requirements = {
        "topic_selection": [],
        "topic_validation": ["user_input"],
        "quiz_active": ["topic", "topic_validated"],
        "question_answered": ["current_answer", "answer_is_correct"],
        "quiz_complete": ["quiz_completed"]
    }
    
    required_fields = phase_requirements.get(state.current_phase, [])
    for field in required_fields:
        if not getattr(state, field):
            errors.append(f"Phase '{state.current_phase}' requires field '{field}'")
    
    # Completion validation
    if state.quiz_type == "finite" and state.max_questions:
        if state.total_questions_answered > state.max_questions:
            errors.append("Questions answered exceeds maximum for finite quiz")
    
    return errors


def validate_state_transition(old_state: QuizState, new_state: QuizState) -> List[str]:
    """
    Validate state transition between two states.
    
    Args:
        old_state: Previous state
        new_state: New state after transition
        
    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []
    
    # Session ID should remain constant
    if old_state.session_id != new_state.session_id:
        errors.append("Session ID should not change during transitions")
    
    # Question index should only increase or reset
    if (new_state.current_question_index != 0 and 
        new_state.current_question_index < old_state.current_question_index):
        errors.append("Question index should not decrease (except on reset)")
    
    # Score should not decrease
    if new_state.total_score < old_state.total_score:
        errors.append("Total score should not decrease")
    
    # Answer count should not decrease
    if new_state.total_questions_answered < old_state.total_questions_answered:
        errors.append("Total questions answered should not decrease")
    
    return errors

__all__ = [
    "validate_state_consistency",
    "validate_state_transition"
] 