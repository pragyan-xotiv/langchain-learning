"""Shared types and enumerations for state management

This module defines the core types, enumerations, and data structures used
throughout the state management system.
"""

from typing import List, Dict, Optional, Any
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field

class QuizPhase(str, Enum):
    """Current phase of the quiz application"""
    TOPIC_SELECTION = "topic_selection"
    TOPIC_VALIDATION = "topic_validation" 
    QUIZ_ACTIVE = "quiz_active"
    QUESTION_ANSWERED = "question_answered"
    QUIZ_COMPLETE = "quiz_complete"
    ERROR_RECOVERY = "error_recovery"

class UserIntent(str, Enum):
    """Detected user intent from query analysis"""
    START_QUIZ = "start_quiz"
    ANSWER_QUESTION = "answer_question"
    CHANGE_TOPIC = "change_topic"
    GET_HELP = "get_help"
    EXIT_QUIZ = "exit_quiz"
    REQUEST_CLARIFICATION = "request_clarification"
    VIEW_PROGRESS = "view_progress"
    UNKNOWN = "unknown"

class QuestionType(str, Enum):
    """Types of quiz questions"""
    MULTIPLE_CHOICE = "multiple_choice"
    OPEN_ENDED = "open_ended"
    TRUE_FALSE = "true_false"
    FILL_IN_BLANK = "fill_in_blank"

class DifficultyLevel(str, Enum):
    """Question difficulty levels"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class ValidationResult(BaseModel):
    """Result of a validation operation"""
    is_valid: bool
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str = ""
    suggestions: List[str] = Field(default_factory=list)

class QuizQuestion(BaseModel):
    """Individual quiz question data structure"""
    id: str
    question_text: str
    question_type: QuestionType
    difficulty: DifficultyLevel
    correct_answer: str
    options: Optional[List[str]] = None  # For multiple choice
    explanation: str = ""
    topic: str = ""
    subtopic: str = ""

class UserAnswer(BaseModel):
    """User's answer to a quiz question"""
    question_id: str
    answer_text: str
    timestamp: datetime = Field(default_factory=datetime.now)
    confidence: Optional[float] = None

class ScoringResult(BaseModel):
    """Result of answer scoring and evaluation"""
    question_id: str
    is_correct: bool
    score: float = Field(ge=0.0, le=1.0)
    max_score: float = 1.0
    feedback: str = ""
    detailed_explanation: str = "" 