"""State factory functions for the Interactive Quiz Generator

This module provides factory functions for creating QuizState objects in various
configurations, particularly useful for testing and initialization.

To be implemented in Phase 1 following 02-state-management.md
"""

from typing import Optional, List, Dict, Any
import uuid
from datetime import datetime
from .quiz_state import QuizState
from .state_types import QuizPhase, UserIntent, QuestionType, DifficultyLevel

def create_initial_state(session_id: Optional[str] = None) -> QuizState:
    """
    Create a new QuizState for the beginning of a quiz session.
    
    Args:
        session_id: Optional session identifier (generates one if not provided)
        
    Returns:
        Fresh QuizState ready for topic selection
        
    Full implementation will include proper field initialization and validation.
    """
    if session_id is None:
        session_id = str(uuid.uuid4())
    
    return QuizState(
        session_id=session_id,
        timestamp=datetime.now(),
        current_phase=QuizPhase.TOPIC_SELECTION,
        user_input="",
        conversation_history=[],
        is_quiz_active=False,
        is_quiz_complete=False
    )

def create_test_state(
    phase: QuizPhase = QuizPhase.QUIZ_ACTIVE,
    topic: str = "Python Programming",
    question_index: int = 0,
    total_questions: int = 5,
    **kwargs: Any
) -> QuizState:
    """
    Create a QuizState configured for testing scenarios.
    
    Args:
        phase: Quiz phase to set
        topic: Quiz topic
        question_index: Current question index
        total_questions: Total number of questions
        **kwargs: Additional state properties to override
        
    Returns:
        QuizState configured for testing
        
    Placeholder - see 02-state-management.md for complete implementation
    """
    base_state = create_initial_state()
    
    # Update with test configuration
    base_state.current_phase = phase
    base_state.validated_topic = topic
    base_state.question_index = question_index
    base_state.total_questions = total_questions
    base_state.is_quiz_active = (phase == QuizPhase.QUIZ_ACTIVE)
    
    # Apply any additional overrides
    for key, value in kwargs.items():
        if hasattr(base_state, key):
            setattr(base_state, key, value)
    
    return base_state

def create_quiz_active_state(
    topic: str,
    questions_completed: int = 0,
    total_questions: int = 10,
    current_score: float = 0.0
) -> QuizState:
    """
    Create a QuizState for an active quiz scenario.
    
    Args:
        topic: Quiz topic
        questions_completed: Number of questions already completed
        total_questions: Total questions in quiz
        current_score: Current accumulated score
        
    Returns:
        QuizState configured for active quiz
        
    Placeholder - full implementation coming
    """
    state = create_initial_state()
    state.current_phase = QuizPhase.QUIZ_ACTIVE
    state.validated_topic = topic
    state.question_index = questions_completed
    state.total_questions = total_questions
    state.total_score = current_score
    state.questions_attempted = questions_completed
    state.is_quiz_active = True
    
    return state

def create_completed_state(
    topic: str,
    total_questions: int = 10,
    final_score: float = 8.5,
    questions_correct: int = 8
) -> QuizState:
    """
    Create a QuizState for a completed quiz scenario.
    
    Args:
        topic: Quiz topic
        total_questions: Total questions in quiz
        final_score: Final quiz score
        questions_correct: Number of correct answers
        
    Returns:
        QuizState configured for completed quiz
        
    Placeholder - full implementation coming
    """
    state = create_initial_state()
    state.current_phase = QuizPhase.QUIZ_COMPLETE
    state.validated_topic = topic
    state.question_index = total_questions
    state.total_questions = total_questions
    state.total_score = final_score
    state.max_possible_score = float(total_questions)
    state.percentage_score = (final_score / total_questions) * 100
    state.questions_correct = questions_correct
    state.questions_attempted = total_questions
    state.is_quiz_active = False
    state.is_quiz_complete = True
    
    return state 