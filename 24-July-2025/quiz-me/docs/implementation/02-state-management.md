# State Management Implementation

## 🎯 Overview  

This guide implements the `QuizState` class using Pydantic models, providing centralized state management for the Interactive Quiz Generator. The state object maintains all application data and ensures type safety throughout the workflow.

## 📋 Reference Documents

- **Design Specification**: `../state.md`
- **Previous Step**: `01-project-setup.md`
- **Next Step**: `03-prompt-templates.md`

## 🏗️ QuizState Implementation

### Core State Class

Create the complete state class in `src/state.py`:

```python
"""State management for the Interactive Quiz Generator"""

from typing import List, Dict, Optional, Literal, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
import json
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
    conversation_history: List[Dict[str, str]] = Field(default_factory=list, description="Conversation log")
    quiz_metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional quiz information")
    
    # === Timestamps ===
    created_at: datetime = Field(default_factory=datetime.now, description="State creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update timestamp")
    
    class Config:
        """Pydantic configuration"""
        # Allow field updates
        allow_mutation = True
        # Generate schema for OpenAPI docs
        schema_extra = {
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
    
    # === Validators ===
    
    @validator('quiz_completion_percentage')
    def validate_percentage(cls, v):
        """Ensure percentage is between 0 and 100"""
        if v < 0 or v > 100:
            raise ValueError('Completion percentage must be between 0 and 100')
        return v
    
    @validator('current_question_index')
    def validate_question_index(cls, v):
        """Ensure question index is non-negative"""
        if v < 0:
            raise ValueError('Question index cannot be negative')
        return v
    
    @validator('total_score')
    def validate_score(cls, v):
        """Ensure score is non-negative"""
        if v < 0:
            raise ValueError('Total score cannot be negative')
        return v
    
    @validator('correct_answers_count')
    def validate_correct_count(cls, v, values):
        """Ensure correct answers don't exceed total answers"""
        total_answered = values.get('total_questions_answered', 0)
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


# === State Validation Functions ===

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


# === State Serialization ===

def serialize_state(state: QuizState) -> str:
    """
    Serialize state to JSON string for persistence.
    
    Args:
        state: QuizState object to serialize
        
    Returns:
        JSON string representation
    """
    state_dict = state.dict()
    
    # Convert datetime objects to ISO strings
    for key, value in state_dict.items():
        if isinstance(value, datetime):
            state_dict[key] = value.isoformat()
    
    # Add serialization metadata
    state_dict['_serialized_at'] = datetime.now().isoformat()
    state_dict['_version'] = "1.0"
    
    return json.dumps(state_dict, indent=2, default=str)


def deserialize_state(state_json: str) -> QuizState:
    """
    Deserialize state from JSON string.
    
    Args:
        state_json: JSON string representation
        
    Returns:
        QuizState object
        
    Raises:
        ValueError: If deserialization fails
    """
    try:
        state_dict = json.loads(state_json)
        
        # Remove serialization metadata
        state_dict.pop('_serialized_at', None)
        state_dict.pop('_version', None)
        
        # Convert ISO strings back to datetime objects
        for key in ['created_at', 'updated_at']:
            if key in state_dict and isinstance(state_dict[key], str):
                state_dict[key] = datetime.fromisoformat(state_dict[key])
        
        return QuizState(**state_dict)
        
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        raise ValueError(f"Failed to deserialize state: {str(e)}")


# === State Factory Functions ===

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


def create_test_state(phase: str = "quiz_active", **kwargs) -> QuizState:
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
```

## 🧪 State Testing Implementation

Create comprehensive tests in `tests/test_state.py`:

```python
"""Tests for state management functionality"""

import pytest
from datetime import datetime, timedelta
from src.state import (
    QuizState, validate_state_consistency, validate_state_transition,
    serialize_state, deserialize_state, create_initial_state, create_test_state
)

class TestQuizState:
    """Test QuizState class functionality"""
    
    def test_initial_state_creation(self):
        """Test creating initial state"""
        state = QuizState()
        
        assert state.current_phase == "topic_selection"
        assert state.user_input == ""
        assert state.user_intent is None
        assert state.quiz_active is False
        assert state.total_score == 0
        assert state.session_id is not None
        assert len(state.conversation_history) == 0
        assert len(state.user_answers) == 0
    
    def test_conversation_history_management(self):
        """Test conversation history functionality"""
        state = QuizState()
        
        # Add conversation entry
        state.add_conversation_entry("Hello", "Hi there!")
        
        assert len(state.conversation_history) == 1
        entry = state.conversation_history[0]
        assert entry["user"] == "Hello"
        assert entry["system"] == "Hi there!"
        assert entry["phase"] == "topic_selection"
        assert "timestamp" in entry
    
    def test_answer_record_management(self):
        """Test answer recording functionality"""
        state = QuizState()
        
        # Add answer record
        state.add_answer_record(
            question="What is 2+2?",
            user_answer="4",
            correct_answer="4",
            is_correct=True,
            feedback="Correct!",
            explanation="Basic arithmetic"
        )
        
        assert len(state.user_answers) == 1
        record = state.user_answers[0]
        assert record["question"] == "What is 2+2?"
        assert record["user_answer"] == "4"
        assert record["is_correct"] is True
        assert record["feedback"] == "Correct!"
    
    def test_quiz_reset(self):
        """Test quiz reset functionality"""
        state = QuizState()
        
        # Set some quiz data
        state.topic = "Python"
        state.topic_validated = True
        state.quiz_active = True
        state.total_score = 50
        state.current_question_index = 5
        state.add_conversation_entry("test", "response")
        
        original_session_id = state.session_id
        
        # Reset quiz
        state.reset_for_new_quiz()
        
        # Check reset fields
        assert state.topic is None
        assert state.topic_validated is False
        assert state.quiz_active is False
        assert state.total_score == 0
        assert state.current_question_index == 0
        assert state.current_phase == "topic_selection"
        
        # Check preserved fields
        assert state.session_id == original_session_id
        assert len(state.conversation_history) == 1  # Preserved
    
    def test_question_increment(self):
        """Test question increment functionality"""
        state = create_test_state()
        state.current_question_index = 5
        state.current_question = "Test question"
        state.current_answer = "Test answer"
        
        state.increment_question()
        
        assert state.current_question_index == 6
        assert state.current_question is None
        assert state.current_answer is None
    
    def test_accuracy_calculation(self):
        """Test accuracy calculation"""
        state = QuizState()
        
        # No questions answered
        assert state.calculate_accuracy() == 0.0
        
        # Set some data
        state.total_questions_answered = 10
        state.correct_answers_count = 7
        
        assert state.calculate_accuracy() == 70.0
    
    def test_performance_summary(self):
        """Test performance summary generation"""
        state = create_test_state()
        state.total_questions_answered = 5
        state.correct_answers_count = 4
        state.total_score = 40
        
        # Add some answer records
        state.user_answers = [
            {"question_type": "multiple_choice", "is_correct": True},
            {"question_type": "multiple_choice", "is_correct": False},
            {"question_type": "open_ended", "is_correct": True}
        ]
        
        summary = state.get_performance_summary()
        
        assert summary["total_questions"] == 5
        assert summary["correct_answers"] == 4
        assert summary["accuracy"] == 80.0
        assert summary["total_score"] == 40
        assert "question_type_performance" in summary


class TestStateValidation:
    """Test state validation functions"""
    
    def test_consistent_state_validation(self):
        """Test validation of consistent state"""
        state = create_test_state()
        errors = validate_state_consistency(state)
        
        assert len(errors) == 0  # Should be valid
    
    def test_inconsistent_state_validation(self):
        """Test validation of inconsistent state"""
        state = QuizState()
        
        # Create inconsistent state
        state.quiz_active = True  # Quiz active but topic not validated
        state.correct_answers_count = 5
        state.total_questions_answered = 3  # Less than correct answers
        
        errors = validate_state_consistency(state)
        
        assert len(errors) > 0
        assert any("Quiz cannot be active without validated topic" in error for error in errors)
        assert any("Correct answers cannot exceed total answered" in error for error in errors)
    
    def test_state_transition_validation(self):
        """Test state transition validation"""
        old_state = create_test_state()
        old_state.total_score = 30
        old_state.current_question_index = 3
        
        new_state = create_test_state()
        new_state.total_score = 40  # Score increased - valid
        new_state.current_question_index = 4  # Index increased - valid
        new_state.session_id = old_state.session_id  # Same session
        
        errors = validate_state_transition(old_state, new_state)
        assert len(errors) == 0
        
        # Test invalid transition
        invalid_state = create_test_state()
        invalid_state.total_score = 20  # Score decreased - invalid
        invalid_state.session_id = "different_id"  # Changed session - invalid
        
        errors = validate_state_transition(old_state, invalid_state)
        assert len(errors) > 0


class TestStateSerialization:
    """Test state serialization functionality"""
    
    def test_state_serialization(self):
        """Test state serialization to JSON"""
        state = create_test_state()
        state.topic = "Test Topic"
        state.total_score = 50
        
        json_str = serialize_state(state)
        
        assert isinstance(json_str, str)
        assert "Test Topic" in json_str
        assert "50" in json_str
        assert "_serialized_at" in json_str
    
    def test_state_deserialization(self):
        """Test state deserialization from JSON"""
        original_state = create_test_state()
        original_state.topic = "Python Programming"
        original_state.total_score = 75
        original_state.quiz_active = True
        
        # Serialize and deserialize
        json_str = serialize_state(original_state)
        restored_state = deserialize_state(json_str)
        
        # Check key fields are preserved
        assert restored_state.topic == "Python Programming"
        assert restored_state.total_score == 75
        assert restored_state.quiz_active is True
        assert restored_state.session_id == original_state.session_id
    
    def test_invalid_deserialization(self):
        """Test handling of invalid JSON"""
        with pytest.raises(ValueError):
            deserialize_state("invalid json")
        
        with pytest.raises(ValueError):
            deserialize_state('{"invalid": "state_data"}')


class TestStateFactories:
    """Test state factory functions"""
    
    def test_initial_state_creation(self):
        """Test initial state factory"""
        state = create_initial_state()
        
        assert state.current_phase == "topic_selection"
        assert state.quiz_active is False
        assert state.session_id is not None
    
    def test_initial_state_with_session_id(self):
        """Test initial state with custom session ID"""
        custom_id = "test_session_123"
        state = create_initial_state(session_id=custom_id)
        
        assert state.session_id == custom_id
    
    def test_test_state_creation(self):
        """Test test state factory"""
        state = create_test_state(phase="quiz_active", topic="Custom Topic")
        
        assert state.current_phase == "quiz_active"
        assert state.topic == "Custom Topic"
        assert state.topic_validated is True
        assert state.quiz_active is True


if __name__ == "__main__":
    pytest.main([__file__])
```

## 🔧 Integration with Other Components

### State Usage in Nodes

Example of how nodes will interact with state:

```python
# Example node implementation (preview)
def query_analyzer_node(state: QuizState) -> QuizState:
    """Example of node using state"""
    
    # Validate state before processing
    errors = validate_state_consistency(state)
    if errors:
        state.last_error = f"State validation failed: {errors[0]}"
        return state
    
    # Process user input
    state.user_intent = classify_intent(state.user_input, state.current_phase)
    
    # Update conversation history
    state.add_conversation_entry(
        user_input=state.user_input,
        system_response=f"Classified intent as: {state.user_intent}"
    )
    
    # Update timestamp
    state.update_timestamp()
    
    return state
```

### State Middleware (Optional)

For advanced state management, create middleware:

```python
# src/state_middleware.py
from functools import wraps
from typing import Callable
from .state import QuizState, validate_state_consistency

def validate_state_middleware(func: Callable) -> Callable:
    """Middleware to validate state before and after node execution"""
    
    @wraps(func)
    def wrapper(state: QuizState) -> QuizState:
        # Pre-execution validation
        pre_errors = validate_state_consistency(state)
        if pre_errors:
            state.last_error = f"Pre-execution validation failed: {pre_errors[0]}"
            return state
        
        # Execute node
        result_state = func(state)
        
        # Post-execution validation
        post_errors = validate_state_consistency(result_state)
        if post_errors:
            result_state.last_error = f"Post-execution validation failed: {post_errors[0]}"
        
        return result_state
    
    return wrapper
```

## 📋 Implementation Checklist

### Core Implementation
- [ ] **QuizState Class**: Complete Pydantic model with all fields
- [ ] **Validators**: Field validation and consistency checks
- [ ] **State Methods**: Conversation, answer, and quiz management methods
- [ ] **Serialization**: JSON serialization and deserialization
- [ ] **Factory Functions**: State creation utilities

### Testing
- [ ] **Unit Tests**: All state methods and validators tested
- [ ] **Integration Tests**: State interaction with other components
- [ ] **Edge Cases**: Invalid data and error conditions tested
- [ ] **Performance Tests**: Serialization and large state objects

### Validation
- [ ] **Type Checking**: mypy passes without errors
- [ ] **Test Coverage**: >90% test coverage for state module
- [ ] **Documentation**: All methods have comprehensive docstrings

## 🚨 Common Issues and Solutions

### Memory Management
**Issue**: Large conversation history consuming memory
**Solution**: Implement history trimming in `add_conversation_entry`:

```python
def add_conversation_entry(self, user_input: str, system_response: str = "") -> None:
    """Add entry with automatic history trimming"""
    # ... existing code ...
    
    # Trim history to last 50 entries
    if len(self.conversation_history) > 50:
        self.conversation_history = self.conversation_history[-50:]
```

### State Consistency
**Issue**: State becomes inconsistent during complex operations
**Solution**: Use validation middleware and atomic updates

### Performance
**Issue**: State serialization is slow
**Solution**: Use ujson for faster JSON operations (add to requirements.txt)

## ✅ Completion Criteria

State management is complete when:

1. **QuizState class implemented** with all specified fields and methods
2. **Validation functions working** for consistency and transitions  
3. **Serialization working** for state persistence
4. **Comprehensive tests passing** with >90% coverage
5. **Type checking passes** without errors
6. **Integration ready** for use in nodes and workflow

**Next Step**: Proceed to **[03-prompt-templates.md](./03-prompt-templates.md)** to implement LLM prompt management. 