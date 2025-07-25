"""Core QuizState class for the Interactive Quiz Generator"""

from typing import List, Dict, Optional, Literal, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict
import uuid

class QuizState(BaseModel):
    """
    Centralized state management for the quiz application.
    
    This class maintains all application data and provides type safety
    throughout the workflow. State is passed between nodes and updated
    as the quiz progresses.
    """
    
    # === User Input & Intent ===
    user_input: str = Field(default="", description="Latest user input text")
    user_intent: Optional[Literal[
        "start_quiz", "answer_question", "new_quiz", 
        "exit", "continue", "clarification"
    ]] = Field(default=None, description="Classified user intention")
    
    # === Current Phase Tracking ===
    current_phase: Literal[
        "topic_selection", "topic_validation", "quiz_active", 
        "question_answered", "quiz_complete"
    ] = Field(default="topic_selection", description="Current application phase")
    
    # === Quiz Configuration ===
    topic: Optional[str] = Field(default=None, description="Quiz topic")
    topic_validated: bool = Field(default=False, description="Topic validation status")
    quiz_type: Literal["finite", "infinite"] = Field(default="finite", description="Quiz duration type")
    max_questions: Optional[int] = Field(default=10, description="Maximum questions for finite quizzes")
    
    # === Question Management ===
    current_question_index: int = Field(default=0, description="Current question number (0-based)")
    current_question: Optional[str] = Field(default=None, description="Current question text")
    question_type: Optional[Literal[
        "multiple_choice", "open_ended", "true_false", "fill_in_blank"
    ]] = Field(default=None, description="Current question format")
    question_options: Optional[List[str]] = Field(default=None, description="Multiple choice options")
    correct_answer: Optional[str] = Field(default=None, description="Correct answer for current question")
    
    # === User Responses & History ===
    user_answers: List[Dict[str, Any]] = Field(default_factory=list, description="Complete answer history")
    current_answer: Optional[str] = Field(default=None, description="User's current answer")
    answer_is_correct: Optional[bool] = Field(default=None, description="Current answer correctness")
    answer_feedback: Optional[str] = Field(default=None, description="Feedback on current answer")
    
    # === Scoring System ===
    total_score: int = Field(default=0, description="Cumulative score")
    total_questions_answered: int = Field(default=0, description="Total questions completed")
    correct_answers_count: int = Field(default=0, description="Number of correct answers")
    quiz_completion_percentage: float = Field(default=0.0, description="Quiz progress percentage")
    
    # === Session Management ===
    quiz_active: bool = Field(default=False, description="Quiz session status")
    quiz_completed: bool = Field(default=False, description="Quiz completion status")
    session_id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique session identifier")
    
    # === Error Handling ===
    last_error: Optional[str] = Field(default=None, description="Last error message")
    retry_count: int = Field(default=0, description="Number of retry attempts")
    
    # === Context & Metadata ===
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list, description="Conversation log")
    quiz_metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional quiz information")
    
    # === Timestamps ===
    created_at: datetime = Field(default_factory=datetime.now, description="State creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update timestamp")
    
    model_config = ConfigDict(
        # Generate schema for OpenAPI docs  
        json_schema_extra = {
            "example": {
                "user_input": "I want a quiz about Python programming",
                "user_intent": "start_quiz",
                "current_phase": "topic_validation",
                "topic": "Python Programming",
                "topic_validated": True,
                "quiz_active": True,
                "max_questions": 10
            }
        }
    )
    
    # === Validators ===
    
    @field_validator('quiz_completion_percentage')
    @classmethod
    def validate_percentage(cls, v: float) -> float:
        """Ensure percentage is between 0 and 100"""
        if v < 0 or v > 100:
            raise ValueError('Completion percentage must be between 0 and 100')
        return v
    
    @field_validator('current_question_index')
    @classmethod  
    def validate_question_index(cls, v: int) -> int:
        """Ensure question index is non-negative"""
        if v < 0:
            raise ValueError('Question index cannot be negative')
        return v
    
    @field_validator('total_score')
    @classmethod
    def validate_score(cls, v: int) -> int:
        """Ensure score is non-negative"""
        if v < 0:
            raise ValueError('Total score cannot be negative')
        return v
    
    @field_validator('correct_answers_count')
    @classmethod
    def validate_correct_count(cls, v: int, info: Any) -> int:
        """Ensure correct answers don't exceed total answers"""
        if hasattr(info, 'data') and info.data:
            total_answered = info.data.get('total_questions_answered', 0)
            if v > total_answered:
                raise ValueError('Correct answers cannot exceed total answered')
        return v
    
    # === State Management Methods ===
    
    def update_timestamp(self) -> None:
        """Update the last modified timestamp"""
        self.updated_at = datetime.now()
    
    def add_conversation_entry(self, user_input: str, system_response: str = "") -> None:
        """Add entry to conversation history"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "user": user_input,
            "system": system_response,
            "phase": self.current_phase,
            "question_index": self.current_question_index
        }
        self.conversation_history.append(entry)
        self.update_timestamp()
    
    def add_answer_record(self, question: str, user_answer: str, 
                         correct_answer: str, is_correct: bool, 
                         feedback: str = "", explanation: str = "") -> None:
        """Add complete answer record to history"""
        answer_record = {
            "question_index": self.current_question_index,
            "question": question,
            "user_answer": user_answer,
            "correct_answer": correct_answer,
            "is_correct": is_correct,
            "feedback": feedback,
            "explanation": explanation,
            "question_type": self.question_type,
            "timestamp": datetime.now().isoformat()
        }
        self.user_answers.append(answer_record)
        self.update_timestamp()
    
    def reset_for_new_quiz(self) -> None:
        """Reset state for starting a new quiz"""
        # Preserve session info
        session_id = self.session_id
        conversation_history = self.conversation_history.copy()
        
        # Reset quiz-specific fields
        self.topic = None
        self.topic_validated = False
        self.current_question_index = 0
        self.current_question = None
        self.question_type = None
        self.question_options = None
        self.correct_answer = None
        self.user_answers = []
        self.current_answer = None
        self.answer_is_correct = None
        self.answer_feedback = None
        self.total_score = 0
        self.total_questions_answered = 0
        self.correct_answers_count = 0
        self.quiz_completion_percentage = 0.0
        self.quiz_active = False
        self.quiz_completed = False
        self.current_phase = "topic_selection"
        self.last_error = None
        self.retry_count = 0
        self.quiz_metadata = {}
        
        # Restore preserved fields
        self.session_id = session_id
        self.conversation_history = conversation_history
        self.update_timestamp()
    
    def increment_question(self) -> None:
        """Move to next question"""
        self.current_question_index += 1
        self.current_question = None
        self.question_type = None
        self.question_options = None
        self.correct_answer = None
        self.current_answer = None
        self.answer_is_correct = None
        self.answer_feedback = None
        self.update_timestamp()
    
    def calculate_accuracy(self) -> float:
        """Calculate current accuracy percentage"""
        if self.total_questions_answered == 0:
            return 0.0
        return (self.correct_answers_count / self.total_questions_answered) * 100
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Generate performance summary statistics"""
        accuracy = self.calculate_accuracy()
        
        # Analyze question type performance
        type_performance = {}
        for answer in self.user_answers:
            q_type = answer.get('question_type', 'unknown')
            if q_type not in type_performance:
                type_performance[q_type] = {"correct": 0, "total": 0}
            
            type_performance[q_type]["total"] += 1
            if answer.get('is_correct', False):
                type_performance[q_type]["correct"] += 1
        
        return {
            "total_questions": self.total_questions_answered,
            "correct_answers": self.correct_answers_count,
            "accuracy": accuracy,
            "total_score": self.total_score,
            "completion_percentage": self.quiz_completion_percentage,
            "question_type_performance": type_performance,
            "session_duration": (self.updated_at - self.created_at).total_seconds(),
            "topic": self.topic
        }

 