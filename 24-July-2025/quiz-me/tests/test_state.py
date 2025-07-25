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
            deserialize_state('{"current_question_index": "not_a_number"}')


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