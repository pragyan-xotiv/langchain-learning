"""Tests for node functionality"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from src.nodes import (
    query_analyzer, topic_validator, quiz_generator, 
    answer_validator, score_generator,
    validate_multiple_choice_answer, validate_true_false_answer,
    determine_question_type, get_difficulty_multiplier, get_question_type_bonus,
    calculate_performance_trend, validate_node_prerequisites,
    NODE_FUNCTIONS, NODE_VALIDATORS, execute_node
)
from src.state import QuizState, create_test_state

class TestNodePrerequisites:
    """Test node prerequisite validation"""
    
    def test_query_analyzer_prerequisites(self):
        """Test query analyzer prerequisites"""
        state = QuizState()
        errors = validate_node_prerequisites(state, "query_analyzer")
        assert "user_input" in str(errors)
        
        state.user_input = "test input"
        errors = validate_node_prerequisites(state, "query_analyzer")
        assert len(errors) == 0
    
    def test_topic_validator_prerequisites(self):
        """Test topic validator prerequisites"""
        state = QuizState()
        errors = validate_node_prerequisites(state, "topic_validator")
        assert "user_input" in str(errors)
    
    def test_quiz_generator_prerequisites(self):
        """Test quiz generator prerequisites"""
        state = QuizState()
        errors = validate_node_prerequisites(state, "quiz_generator")
        assert len(errors) > 0
        
        state.topic = "Test Topic"
        state.topic_validated = True
        errors = validate_node_prerequisites(state, "quiz_generator")
        assert len(errors) == 0

    def test_answer_validator_prerequisites(self):
        """Test answer validator prerequisites"""
        state = QuizState()
        errors = validate_node_prerequisites(state, "answer_validator")
        assert len(errors) > 0
        
        state.current_answer = "test answer"
        state.current_question = "test question"
        state.correct_answer = "correct answer"
        errors = validate_node_prerequisites(state, "answer_validator")
        assert len(errors) == 0

    def test_score_generator_prerequisites(self):
        """Test score generator prerequisites"""
        # QuizState initializes with default values, so prerequisites pass
        state = QuizState()
        errors = validate_node_prerequisites(state, "score_generator")
        assert len(errors) == 0  # Default values exist
        
        # Test with missing attributes (simulate edge case)
        delattr(state, 'answer_is_correct')
        errors = validate_node_prerequisites(state, "score_generator")
        assert len(errors) > 0

class TestQueryAnalyzer:
    """Test Query Analyzer node"""
    
    @patch('src.nodes.query_analyzer.safe_llm_call', new_callable=AsyncMock)
    def test_query_analyzer_success(self, mock_llm_call):
        """Test successful query analysis"""
        # Mock LLM response using AsyncMock
        mock_llm_call.return_value = '{"intent": "start_quiz", "confidence": 0.9, "reasoning": "User wants to start"}'
        
        state = QuizState()
        state.user_input = "I want a quiz about Python"
        
        llm = AsyncMock()
        result = query_analyzer(state, llm)
        
        assert result.user_intent == "start_quiz"
        assert len(result.conversation_history) > 0
        assert result.last_error is None
    
    @patch('src.nodes.query_analyzer.safe_llm_call')
    def test_query_analyzer_llm_error(self, mock_llm_call):
        """Test query analyzer with LLM error"""
        mock_llm_call.side_effect = Exception("LLM error")
        
        state = QuizState()
        state.user_input = "test input"
        
        llm = AsyncMock()
        result = query_analyzer(state, llm)
        
        assert result.user_intent == "clarification"
        assert result.last_error is not None
    
    def test_query_analyzer_empty_input(self):
        """Test query analyzer with empty input"""
        state = QuizState()
        state.user_input = ""
        
        llm = AsyncMock()
        result = query_analyzer(state, llm)
        
        assert result.last_error is not None
        assert "Empty user input" in result.last_error

class TestTopicValidator:
    """Test Topic Validator node"""
    
    @patch('src.nodes.query_analyzer.safe_llm_call', new_callable=AsyncMock)
    def test_topic_validator_success(self, mock_llm_call):
        """Test successful topic validation"""
        # Mock responses for extraction and validation
        mock_llm_call.side_effect = [
            '{"topic": "Python Programming", "confidence": 0.9}',
            '{"is_valid": true, "category": "programming", "difficulty_level": "intermediate"}'
        ]
        
        state = QuizState()
        state.user_input = "I want to learn Python programming"
        
        llm = AsyncMock()
        result = topic_validator(state, llm)
        
        assert result.topic == "Python Programming"
        assert result.topic_validated is True
        assert result.current_phase == "quiz_active"
        assert result.quiz_active is True
    
    @patch('src.nodes.query_analyzer.safe_llm_call', new_callable=AsyncMock)
    def test_topic_validator_invalid_topic(self, mock_llm_call):
        """Test topic validation with invalid topic"""
        mock_llm_call.side_effect = [
            '{"topic": "Inappropriate Topic", "confidence": 0.8}',
            '{"is_valid": false, "reason": "Topic not suitable", "suggestions": ["Alternative Topic"]}'
        ]
        
        state = QuizState()
        state.user_input = "Inappropriate topic request"
        
        llm = AsyncMock()
        result = topic_validator(state, llm)
        
        assert result.topic_validated is False
        assert result.current_phase == "topic_selection"
        assert result.last_error is not None

class TestQuizGenerator:
    """Test Quiz Generator node"""
    
    @patch('src.nodes.query_analyzer.safe_llm_call', new_callable=AsyncMock)
    def test_quiz_generator_success(self, mock_llm_call):
        """Test successful question generation"""
        mock_llm_call.return_value = '''{
            "question": "What is a Python list?",
            "type": "open_ended",
            "correct_answer": "A mutable sequence of items",
            "explanation": "Lists are fundamental data structures"
        }'''
        
        state = create_test_state()
        
        llm = AsyncMock()
        result = quiz_generator(state, llm)
        
        assert result.current_question == "What is a Python list?"
        assert result.question_type == "open_ended"
        assert result.correct_answer == "A mutable sequence of items"
        assert result.last_error is None
    
    def test_quiz_generator_missing_topic(self):
        """Test quiz generator with missing topic"""
        state = QuizState()
        
        llm = AsyncMock()
        result = quiz_generator(state, llm)
        
        assert result.last_error is not None
        assert "without validated topic" in result.last_error
    
    def test_determine_question_type(self):
        """Test question type determination logic"""
        state = QuizState()
        
        # First question should be multiple choice
        state.total_questions_answered = 0
        assert determine_question_type(state) == "multiple_choice"
        
        # Every third question should be open ended
        state.total_questions_answered = 3
        assert determine_question_type(state) == "open_ended"
        
        # Every fourth question should be true/false
        state.total_questions_answered = 4
        assert determine_question_type(state) == "true_false"

class TestAnswerValidator:
    """Test Answer Validator node"""
    
    def test_validate_multiple_choice_exact_match(self):
        """Test multiple choice validation with exact match"""
        state = create_test_state()
        state.current_answer = "A"
        state.correct_answer = "A"
        state.question_type = "multiple_choice"
        
        result = validate_multiple_choice_answer(state)
        
        assert result["is_correct"] is True
        assert result["score_percentage"] == 100
    
    def test_validate_multiple_choice_letter_mapping(self):
        """Test multiple choice validation with letter mapping"""
        state = create_test_state()
        state.current_answer = "a"
        state.correct_answer = "0"  # First option
        state.question_type = "multiple_choice"
        
        result = validate_multiple_choice_answer(state)
        
        assert result["is_correct"] is True
    
    def test_validate_true_false_answer(self):
        """Test true/false answer validation"""
        state = create_test_state()
        state.current_answer = "yes"
        state.correct_answer = "true"
        state.question_type = "true_false"
        
        result = validate_true_false_answer(state)
        
        assert result["is_correct"] is True
        assert result["score_percentage"] == 100
    
    @patch('src.nodes.query_analyzer.safe_llm_call', new_callable=AsyncMock)
    def test_answer_validator_open_ended(self, mock_llm_call):
        """Test answer validator with open-ended question"""
        mock_llm_call.return_value = '''{
            "is_correct": true,
            "partial_credit": false,
            "score_percentage": 85,
            "feedback": "Good answer with minor gaps"
        }'''
        
        state = create_test_state()
        state.current_answer = "A list is a collection of items"
        state.question_type = "open_ended"
        
        llm = AsyncMock()
        result = answer_validator(state, llm)
        
        assert result.answer_is_correct is True
        assert result.current_phase == "question_answered"
        assert len(result.user_answers) > 0

class TestScoreGenerator:
    """Test Score Generator node"""
    
    def test_score_generator_correct_answer(self):
        """Test score generation for correct answer"""
        state = create_test_state()
        state.answer_is_correct = True
        state.question_type = "open_ended"
        state.quiz_metadata["difficulty_level"] = "hard"
        state.max_questions = 5
        
        initial_score = state.total_score
        
        llm = AsyncMock()
        result = score_generator(state, llm)
        
        assert result.total_score > initial_score
        assert result.total_questions_answered == 1
        assert result.correct_answers_count == 1
    
    def test_score_generator_incorrect_answer(self):
        """Test score generation for incorrect answer"""
        state = create_test_state()
        state.answer_is_correct = False
        state.max_questions = 5
        
        initial_score = state.total_score
        
        llm = AsyncMock()
        result = score_generator(state, llm)
        
        assert result.total_score == initial_score  # No points added
        assert result.total_questions_answered == 1
        assert result.correct_answers_count == 0
    
    def test_score_generator_quiz_completion(self):
        """Test quiz completion detection"""
        state = create_test_state()
        state.answer_is_correct = True
        state.max_questions = 1
        state.total_questions_answered = 0  # Will become 1 after processing
        
        llm = AsyncMock()
        result = score_generator(state, llm)
        
        assert result.quiz_completed is True
        assert result.quiz_active is False
        assert result.current_phase == "quiz_complete"
    
    def test_get_difficulty_multiplier(self):
        """Test difficulty multiplier calculation"""
        state = QuizState()
        
        state.quiz_metadata["difficulty_level"] = "easy"
        assert get_difficulty_multiplier(state) == 0.8
        
        state.quiz_metadata["difficulty_level"] = "hard"
        assert get_difficulty_multiplier(state) == 1.5
        
        state.quiz_metadata["difficulty_level"] = "unknown"
        assert get_difficulty_multiplier(state) == 1.0
    
    def test_get_question_type_bonus(self):
        """Test question type bonus calculation"""
        assert get_question_type_bonus("multiple_choice") == 0
        assert get_question_type_bonus("open_ended") == 5
        assert get_question_type_bonus("fill_in_blank") == 3
    
    def test_calculate_performance_trend(self):
        """Test performance trend calculation"""
        # Insufficient data
        answers = [{"is_correct": True}]
        trend = calculate_performance_trend(answers)
        assert trend == "insufficient_data"
        
        # Strong performance
        answers = [{"is_correct": True} for _ in range(5)]
        trend = calculate_performance_trend(answers)
        assert trend == "strong"
        
        # Poor performance
        answers = [{"is_correct": False} for _ in range(5)]
        trend = calculate_performance_trend(answers)
        assert trend == "struggling"

class TestNodeExecution:
    """Test node execution utilities"""
    
    def test_execute_node_success(self):
        """Test successful node execution"""
        state = create_test_state()
        state.answer_is_correct = True
        
        result = execute_node(state, "score_generator")
        
        assert result.total_questions_answered == 1
        assert result.last_error is None
    
    def test_execute_node_prerequisites_fail(self):
        """Test node execution with failed prerequisites"""
        state = QuizState()  # Empty state
        
        result = execute_node(state, "quiz_generator")
        
        assert result.last_error is not None
        assert "prerequisites failed" in result.last_error
    
    def test_execute_node_unknown_node(self):
        """Test node execution with unknown node"""
        state = QuizState()
        
        with pytest.raises(ValueError):
            execute_node(state, "unknown_node")

class TestNodeConfiguration:
    """Test node configuration and mappings"""
    
    def test_node_functions_complete(self):
        """Test that all nodes are registered in NODE_FUNCTIONS"""
        expected_nodes = ["query_analyzer", "topic_validator", "quiz_generator", 
                         "answer_validator", "score_generator"]
        
        for node in expected_nodes:
            assert node in NODE_FUNCTIONS
            assert callable(NODE_FUNCTIONS[node])
    
    def test_node_validators_complete(self):
        """Test that all nodes have validators in NODE_VALIDATORS"""
        for node in NODE_FUNCTIONS.keys():
            assert node in NODE_VALIDATORS
            assert callable(NODE_VALIDATORS[node])
    
    def test_validate_unknown_node(self):
        """Test validation of unknown node"""
        state = QuizState()
        errors = validate_node_prerequisites(state, "unknown_node")
        assert "Unknown node" in str(errors)

if __name__ == "__main__":
    pytest.main([__file__]) 