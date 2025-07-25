"""Factory functions for creating QuizState instances

This module provides factory functions for creating QuizState instances
for different scenarios like testing, initialization, and specific use cases.
"""

from typing import Optional, Any
from .quiz_state import QuizState

def create_initial_state(session_id: Optional[str] = None) -> QuizState:
    """
    Create initial state for new quiz session.
    
    Args:
        session_id: Optional session identifier
        
    Returns:
        Fresh QuizState object
    """
    state = QuizState()
    if session_id:
        state.session_id = session_id
    return state


def create_test_state(phase: str = "quiz_active", **kwargs: Any) -> QuizState:
    """
    Create state for testing purposes.
    
    Args:
        phase: Current phase to set
        **kwargs: Additional field values
        
    Returns:
        QuizState configured for testing
    """
    defaults = {
        "topic": "Test Topic",
        "topic_validated": True,
        "quiz_active": True,
        "current_question": "Test question?",
        "question_type": "open_ended",
        "correct_answer": "Test answer"
    }
    
    # Merge defaults with provided kwargs
    test_data = {**defaults, **kwargs, "current_phase": phase}
    return QuizState(**test_data)

__all__ = [
    "create_initial_state",
    "create_test_state"
] 