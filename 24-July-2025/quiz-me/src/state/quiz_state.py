"""Main QuizState class for the Interactive Quiz Generator

This module provides the centralized QuizState class that maintains all application data
throughout the user session and ensures type safety across the workflow.

To be implemented in Phase 1 following 02-state-management.md
"""

from typing import List, Dict, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field
from .state_types import (
    QuizPhase, UserIntent, QuestionType, DifficultyLevel,
    ValidationResult, QuizQuestion, UserAnswer, ScoringResult
)

class QuizState(BaseModel):
    """
    Centralized state management for the quiz application.
    
    This class maintains all application data and provides type safety
    throughout the workflow. State is passed between nodes and updated
    as the quiz progresses.
    
    Implementation will include comprehensive field validation, state transition
    validation, and serialization support.
    
    To be implemented in Phase 1 following 02-state-management.md
    """
    
    # Session Management
    session_id: str = Field(default="", description="Unique session identifier")
    timestamp: datetime = Field(default_factory=datetime.now, description="State creation/update timestamp")
    
    # User Input and Context
    user_input: str = Field(default="", description="Latest user input text")
    previous_inputs: List[str] = Field(default_factory=list, description="History of user inputs")
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list, description="Full conversation context")
    
    # Application Phase and Intent
    current_phase: QuizPhase = Field(default=QuizPhase.TOPIC_SELECTION, description="Current application phase")
    user_intent: Optional[UserIntent] = Field(default=None, description="Detected user intent")
    intent_confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence in intent detection")
    
    # Topic Management
    requested_topic: str = Field(default="", description="User-requested quiz topic")
    extracted_topic: str = Field(default="", description="Extracted and normalized topic")
    validated_topic: str = Field(default="", description="Final validated quiz topic")
    topic_validation_result: Optional[ValidationResult] = Field(default=None, description="Topic validation outcome")
    alternative_topics: List[str] = Field(default_factory=list, description="Alternative topic suggestions")
    
    # Question Management
    current_question: Optional[QuizQuestion] = Field(default=None, description="Currently active question")
    questions_queue: List[QuizQuestion] = Field(default_factory=list, description="Upcoming questions queue")
    questions_completed: List[QuizQuestion] = Field(default_factory=list, description="Completed questions history")
    question_index: int = Field(default=0, ge=0, description="Current question number (0-based)")
    total_questions: int = Field(default=10, ge=1, description="Total planned questions for quiz")
    
    # Answer and Scoring
    current_answer: Optional[UserAnswer] = Field(default=None, description="User's current answer")
    answers_history: List[UserAnswer] = Field(default_factory=list, description="All user answers history")
    current_scoring: Optional[ScoringResult] = Field(default=None, description="Current question scoring result")
    scoring_history: List[ScoringResult] = Field(default_factory=list, description="All scoring results")
    
    # Progress and Performance
    total_score: float = Field(default=0.0, ge=0.0, description="Cumulative quiz score")
    max_possible_score: float = Field(default=0.0, ge=0.0, description="Maximum possible score")
    percentage_score: float = Field(default=0.0, ge=0.0, le=100.0, description="Score as percentage")
    questions_correct: int = Field(default=0, ge=0, description="Number of correct answers")
    questions_attempted: int = Field(default=0, ge=0, description="Number of questions attempted")
    
    # Error Handling and Recovery
    last_error: Optional[str] = Field(default=None, description="Last error message if any")
    error_count: int = Field(default=0, ge=0, description="Number of errors encountered")
    needs_clarification: bool = Field(default=False, description="Whether user input needs clarification")
    clarification_context: str = Field(default="", description="Context for clarification request")
    
    # Quiz Configuration
    difficulty_preference: Optional[DifficultyLevel] = Field(default=None, description="User's difficulty preference")
    question_types_enabled: List[QuestionType] = Field(
        default_factory=lambda: [QuestionType.MULTIPLE_CHOICE, QuestionType.OPEN_ENDED, QuestionType.TRUE_FALSE],
        description="Enabled question types for this quiz"
    )
    
    # System State
    is_quiz_active: bool = Field(default=False, description="Whether quiz is currently active")
    is_quiz_complete: bool = Field(default=False, description="Whether quiz has been completed")
    system_messages: List[str] = Field(default_factory=list, description="System messages and notifications")
    
    class Config:
        """Pydantic configuration"""
        allow_mutation = True
        use_enum_values = True
        validate_assignment = True
        arbitrary_types_allowed = True
    
    def __str__(self) -> str:
        """String representation for debugging"""
        return f"QuizState(phase={self.current_phase}, topic='{self.validated_topic}', q={self.question_index}/{self.total_questions})"
    
    def __repr__(self) -> str:
        """Detailed representation for debugging"""
        return f"QuizState(session_id='{self.session_id}', phase={self.current_phase}, topic='{self.validated_topic}', question_index={self.question_index}, score={self.total_score})" 