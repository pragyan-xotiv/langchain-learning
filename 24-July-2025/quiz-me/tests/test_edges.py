"""Tests for edge logic and routing functionality"""

import pytest
from unittest.mock import Mock, patch

from src.edges import (
    route_conversation, route_from_topic_selection, route_from_topic_validation,
    route_from_quiz_active, route_from_question_answered, route_from_quiz_complete,
    should_end_session, should_start_new_quiz, should_continue_quiz,
    classify_error_type, validate_routing_decision, 
    test_routing_scenarios as routing_scenarios_util,  # Rename to avoid pytest warning
    simulate_conversation_flow, RoutingMetrics, main_route_conversation,
    route_after_query_analysis, route_after_topic_validation,
    route_after_question_generation, route_after_answer_validation,
    route_after_scoring
)
from src.state import QuizState, create_test_state

class TestMainRouting:
    """Test main routing function"""
    
    def test_route_conversation_exit_intent(self):
        """Test routing with exit intent from any phase"""
        state = create_test_state()
        state.current_phase = "quiz_active"
        state.user_intent = "exit"
        
        result = route_conversation(state)
        assert result == "end"
    
    def test_route_conversation_new_quiz_intent(self):
        """Test routing with new quiz intent from any phase"""
        state = create_test_state()
        state.current_phase = "quiz_active"
        state.user_intent = "new_quiz"
        
        result = route_conversation(state)
        assert result == "topic_validator"
    
    def test_route_conversation_unknown_phase(self):
        """Test routing with unknown phase"""
        state = QuizState()
        state.current_phase = "unknown_phase"
        
        result = route_conversation(state)
        assert result == "query_analyzer"
    
    def test_main_route_conversation_with_decorators(self):
        """Test main routing function with decorators"""
        state = create_test_state()
        state.current_phase = "topic_selection"
        state.user_intent = "start_quiz"
        state.user_input = "Python programming"  # Add user input for validation
        
        result = main_route_conversation(state)
        assert result == "topic_validator"

class TestPhaseSpecificRouting:
    """Test phase-specific routing functions"""
    
    def test_route_from_topic_selection(self):
        """Test routing from topic selection phase"""
        state = create_test_state()
        state.current_phase = "topic_selection"
        
        # Test start quiz intent
        state.user_intent = "start_quiz"
        result = route_from_topic_selection(state)
        assert result == "topic_validator"
        
        # Test clarification intent
        state.user_intent = "clarification"
        result = route_from_topic_selection(state)
        assert result == "clarification_handler"
        
        # Test unknown intent
        state.user_intent = "unknown"
        result = route_from_topic_selection(state)
        assert result == "clarification_handler"
    
    def test_route_from_topic_validation(self):
        """Test routing from topic validation phase"""
        state = create_test_state()
        state.current_phase = "topic_validation"
        
        # Test successful validation
        state.topic_validated = True
        result = route_from_topic_validation(state)
        assert result == "quiz_generator"
        
        # Test failed validation
        state.topic_validated = False
        state.retry_count = 1
        result = route_from_topic_validation(state)
        assert result == "clarification_handler"
        
        # Test max retries
        state.retry_count = 3
        result = route_from_topic_validation(state)
        assert result == "end"
    
    def test_route_from_quiz_active(self):
        """Test routing from quiz active phase"""
        state = create_test_state()
        state.current_phase = "quiz_active"
        
        # Test answer intent
        state.user_intent = "answer_question"
        result = route_from_quiz_active(state)
        assert result == "answer_validator"
        
        # Test clarification intent
        state.user_intent = "clarification"
        result = route_from_quiz_active(state)
        assert result == "clarification_handler"
        
        # Test ambiguous intent with current question
        state.user_intent = "unclear"
        state.current_question = "What is 2+2?"
        state.user_input = "4"
        result = route_from_quiz_active(state)
        assert result == "answer_validator"
        assert state.user_intent == "answer_question"  # Should be overridden
    
    def test_route_from_question_answered(self):
        """Test routing from question answered phase"""
        state = create_test_state()
        state.current_phase = "question_answered"
        
        # Test continue intent
        state.user_intent = "continue"
        result = route_from_question_answered(state)
        assert result == "score_generator"
        
        # Test default routing
        state.user_intent = "unknown"
        result = route_from_question_answered(state)
        assert result == "score_generator"
    
    def test_route_from_quiz_complete(self):
        """Test routing from quiz complete phase"""
        state = create_test_state()
        state.current_phase = "quiz_complete"
        
        # Test new quiz intent
        state.user_intent = "new_quiz"
        result = route_from_quiz_complete(state)
        assert result == "topic_validator"
        
        # Test other intents
        state.user_intent = "unknown"
        result = route_from_quiz_complete(state)
        assert result == "end"

class TestRoutingConditions:
    """Test routing condition functions"""
    
    def test_should_end_session(self):
        """Test session ending conditions"""
        state = QuizState()
        
        # Test exit intent
        state.user_intent = "exit"
        assert should_end_session(state) is True
        
        # Test too many retries
        state.user_intent = "continue"
        state.retry_count = 5
        assert should_end_session(state) is True
        
        # Test quiz complete without new quiz intent
        state.retry_count = 0
        state.current_phase = "quiz_complete"
        state.user_intent = "goodbye"
        assert should_end_session(state) is True
        
        # Test normal continuation
        state.current_phase = "quiz_active"
        state.user_intent = "continue"
        assert should_end_session(state) is False
    
    def test_should_start_new_quiz(self):
        """Test new quiz starting conditions"""
        state = QuizState()
        
        state.user_intent = "new_quiz"
        assert should_start_new_quiz(state) is True
        
        state.user_intent = "start_quiz"
        assert should_start_new_quiz(state) is True
        
        state.user_intent = "continue"
        assert should_start_new_quiz(state) is False
    
    def test_should_continue_quiz(self):
        """Test quiz continuation conditions"""
        state = create_test_state()
        state.quiz_active = True
        state.quiz_completed = False
        state.user_intent = "continue"
        
        assert should_continue_quiz(state) is True
        
        # Test with quiz completed
        state.quiz_completed = True
        assert should_continue_quiz(state) is False
        
        # Test with quiz not active
        state.quiz_completed = False
        state.quiz_active = False
        assert should_continue_quiz(state) is False

class TestErrorHandling:
    """Test error handling and classification"""
    
    def test_classify_error_type(self):
        """Test error type classification"""
        assert classify_error_type("User input unclear") == "user_input_error"
        assert classify_error_type("LLM API timeout") == "llm_error"
        assert classify_error_type("Validation failed") == "validation_error"
        assert classify_error_type("Unknown error") == "unknown"
        assert classify_error_type(None) == "unknown"

class TestRoutingValidation:
    """Test routing validation"""
    
    def test_validate_routing_decision(self):
        """Test routing decision validation"""
        state = create_test_state()
        state.current_phase = "topic_selection"
        state.user_input = "Python programming"  # Add user input for validation
        
        # Valid transition
        assert validate_routing_decision(state, "topic_validator") is True
        
        # Invalid transition
        assert validate_routing_decision(state, "answer_validator") is False
        
        # Query analyzer is always valid
        assert validate_routing_decision(state, "query_analyzer") is True
    
    def test_routing_prerequisites(self):
        """Test routing prerequisites validation"""
        state = QuizState()
        
        # Topic validator requires user input
        assert validate_routing_decision(state, "topic_validator") is False
        
        state.user_input = "Python programming"
        assert validate_routing_decision(state, "topic_validator") is True

class TestQueryAnalyzerRouting:
    """Test query analyzer routing"""
    
    def test_route_after_query_analysis_clear_intents(self):
        """Test routing with clear intents"""
        state = create_test_state()
        
        # Test exit intent
        state.user_intent = "exit"
        result = route_after_query_analysis(state)
        assert result == "end"
        
        # Test start quiz intent (not in active quiz)
        state.user_intent = "start_quiz"
        state.quiz_active = False  # Not in active quiz
        result = route_after_query_analysis(state)
        assert result == "topic_validator"
        
        # Test answer question intent
        state.user_intent = "answer_question"
        state.current_question = "What is 2+2?"
        state.user_input = "4"
        result = route_after_query_analysis(state)
        assert result == "answer_validator"
    
    def test_resolve_ambiguous_intent(self):
        """Test ambiguous intent resolution"""
        from src.edges.query_analyzer_router import resolve_ambiguous_intent
        
        state = create_test_state()
        state.current_phase = "quiz_active"
        state.current_question = "What is 2+2?"
        state.user_input = "4"
        
        result = resolve_ambiguous_intent(state)
        assert result == "answer_validator"
        assert state.user_intent == "answer_question"

class TestTopicValidatorRouting:
    """Test topic validator routing"""
    
    def test_route_after_topic_validation_success(self):
        """Test successful topic validation routing"""
        state = create_test_state()
        state.topic = "Python Programming"
        state.topic_validated = True
        
        result = route_after_topic_validation(state)
        assert result == "quiz_generator"
    
    def test_route_after_topic_validation_failure(self):
        """Test failed topic validation routing"""
        state = create_test_state()
        state.topic = "Inappropriate Topic"
        state.topic_validated = False
        state.last_error = "Topic not suitable"
        
        result = route_after_topic_validation(state)
        assert result == "clarification_handler"
    
    def test_suggest_alternative_topics(self):
        """Test alternative topic suggestions"""
        from src.edges.topic_validator_router import suggest_alternative_topics
        
        state = create_test_state()
        state.user_input = "I want to learn about python programming"
        
        suggestions = suggest_alternative_topics(state)
        assert len(suggestions) > 0
        assert any("Python" in suggestion for suggestion in suggestions)

class TestQuizGeneratorRouting:
    """Test quiz generator routing"""
    
    def test_route_after_question_generation_success(self):
        """Test successful question generation routing"""
        state = create_test_state()
        state.current_question = "What is 2+2?"
        state.correct_answer = "4"
        
        result = route_after_question_generation(state)
        assert result == "query_analyzer"
        assert state.current_phase == "quiz_active"
    
    def test_route_after_question_generation_failure(self):
        """Test failed question generation routing"""
        state = create_test_state()
        state.current_question = None
        state.last_error = "Could not generate question"
        
        result = route_after_question_generation(state)
        # Should handle generation failure
        assert result in ["quiz_generator", "topic_validator", "clarification_handler", "quiz_completion_handler"]
    
    def test_handle_topic_exhausted(self):
        """Test topic exhausted handling"""
        from src.edges.quiz_generator_router import handle_topic_exhausted
        
        state = create_test_state()
        state.total_questions_answered = 5  # Sufficient questions
        
        result = handle_topic_exhausted(state)
        assert result == "quiz_completion_handler"
        assert state.quiz_completed is True

class TestAnswerValidatorRouting:
    """Test answer validator routing"""
    
    def test_route_after_answer_validation_success(self):
        """Test successful answer validation routing"""
        state = create_test_state()
        state.answer_is_correct = True
        
        result = route_after_answer_validation(state)
        assert result == "score_generator"
        assert state.current_phase == "question_answered"
    
    def test_route_after_answer_validation_failure(self):
        """Test failed answer validation routing"""
        state = create_test_state()
        state.answer_is_correct = None
        state.last_error = "Validation failed"
        
        result = route_after_answer_validation(state)
        # Should handle validation error
        assert result in ["answer_validator", "clarification_handler", "score_generator"]
    
    def test_fallback_validation(self):
        """Test fallback validation methods"""
        from src.edges.answer_validator_router import perform_simple_validation
        
        state = create_test_state()
        state.current_answer = "a"
        state.correct_answer = "0"
        state.question_type = "multiple_choice"
        
        result = perform_simple_validation(state)
        assert result is True  # Should match a -> 0

class TestScoreGeneratorRouting:
    """Test score generator routing"""
    
    def test_route_after_scoring_completion(self):
        """Test routing when quiz is completed"""
        state = create_test_state()
        state.quiz_completed = True
        state.total_questions_answered = 10
        state.correct_answers_count = 8
        
        result = route_after_scoring(state)
        assert result == "quiz_completion_handler"
        assert state.current_phase == "quiz_complete"
    
    def test_route_after_scoring_continuation(self):
        """Test routing when quiz continues"""
        state = create_test_state()
        state.quiz_completed = False
        state.total_questions_answered = 3
        state.max_questions = 10
        
        result = route_after_scoring(state)
        assert result == "quiz_generator"
    
    def test_performance_based_routing(self):
        """Test performance-based routing decisions"""
        from src.edges.score_generator_router import handle_performance_based_routing
        
        # Test struggling user
        state = create_test_state()
        state.total_questions_answered = 5
        state.correct_answers_count = 1  # 20% accuracy
        
        result = handle_performance_based_routing(state)
        assert result == "struggling_user_handler"
        
        # Test excelling user
        state.correct_answers_count = 5  # 100% accuracy
        result = handle_performance_based_routing(state)
        assert result == "excelling_user_handler"

class TestRoutingMetrics:
    """Test routing metrics tracking"""
    
    def test_routing_metrics_recording(self):
        """Test metrics recording functionality"""
        metrics = RoutingMetrics()
        
        metrics.record_routing("topic_selection", "topic_validator", "start_quiz")
        metrics.record_routing("topic_selection", "topic_validator", "start_quiz")
        metrics.record_error_route("llm_error")
        
        stats = metrics.get_routing_stats()
        
        assert stats["total_routes"] == 2
        assert ("topic_selection->topic_validator", 2) in stats["most_common_routes"]
        assert stats["error_routes"]["llm_error"] == 1

class TestRoutingScenarios:
    """Test complete routing scenarios"""
    
    def test_routing_scenarios(self):
        """Test predefined routing scenarios"""
        scenarios = routing_scenarios_util()  # Use the renamed import
        
        assert "topic_selection_start" in scenarios
        assert "quiz_active_answer" in scenarios
        assert "quiz_complete_new" in scenarios
        assert "any_phase_exit" in scenarios
        
        # Verify expected results
        assert scenarios["topic_selection_start"] == "topic_validator"
        assert scenarios["quiz_active_answer"] == "answer_validator"
        assert scenarios["any_phase_exit"] == "end"
    
    def test_conversation_flow_simulation(self):
        """Test conversation flow simulation"""
        state = create_test_state()
        state.current_phase = "topic_selection"  # Start from topic selection
        state.user_intent = "start_quiz"
        state.user_input = "Python programming"  # Add user input
        state.quiz_active = False  # Not in active quiz yet
        
        flow = simulate_conversation_flow(state, max_steps=5)
        
        assert len(flow) > 0
        assert flow[0] == "topic_validator"  # First step should be topic validation
    
    def test_complete_quiz_flow(self):
        """Test complete quiz flow simulation"""
        state = QuizState()
        state.current_phase = "topic_selection"
        state.user_intent = "start_quiz"
        state.user_input = "Python programming"
        
        # Simulate successful topic validation
        flow_step1 = route_conversation(state)
        assert flow_step1 == "topic_validator"
        
        # Simulate successful quiz generation
        state.current_phase = "topic_validation"
        state.topic_validated = True
        state.topic = "Python Programming"
        flow_step2 = route_conversation(state)
        assert flow_step2 == "quiz_generator"
        
        # Simulate answer submission
        state.current_phase = "quiz_active"
        state.user_intent = "answer_question"
        state.current_question = "What is a list?"
        flow_step3 = route_conversation(state)
        assert flow_step3 == "answer_validator"

class TestComplexScenarios:
    """Test complex routing scenarios"""
    
    def test_mid_quiz_topic_change(self):
        """Test handling topic change during quiz"""
        from src.edges.conversation_router import handle_mid_quiz_topic_change
        
        state = create_test_state()
        state.quiz_active = True
        state.total_questions_answered = 3
        state.topic = "Math"
        state.total_score = 15
        
        result = handle_mid_quiz_topic_change(state)
        assert result == "topic_validator"
        assert "previous_session" in state.quiz_metadata
    
    def test_ambiguous_answer_intent(self):
        """Test handling ambiguous answer intent"""
        from src.edges.conversation_router import handle_ambiguous_answer_intent
        
        state = create_test_state()
        state.current_phase = "quiz_active"
        state.current_question = "What is 2+2?"
        state.user_input = "four"
        
        result = handle_ambiguous_answer_intent(state)
        assert result == "answer_validator"
        assert state.user_intent == "answer_question"
    
    def test_infinite_quiz_termination(self):
        """Test infinite quiz termination logic"""
        from src.edges.conversation_router import handle_infinite_quiz_termination
        
        state = create_test_state()
        state.quiz_type = "infinite"
        state.total_questions_answered = 50  # Hit limit
        
        result = handle_infinite_quiz_termination(state)
        assert result == "quiz_completion_handler"
        assert state.quiz_completed is True

class TestErrorRecovery:
    """Test error recovery routing"""
    
    def test_error_recovery_routing(self):
        """Test error recovery based on error type"""
        from src.edges.conversation_router import route_error_recovery
        
        state = create_test_state()
        
        # Test user input error
        state.last_error = "User input unclear"
        result = route_error_recovery(state)
        assert result == "clarification_handler"
        
        # Test LLM error with retries available
        state.last_error = "LLM API timeout"
        state.retry_count = 1
        result = route_error_recovery(state)
        assert result in ["query_analyzer", "topic_validator", "quiz_generator", "answer_validator"]
        
        # Test LLM error with max retries
        state.retry_count = 3
        result = route_error_recovery(state)
        assert result == "end"

class TestRoutingDecorators:
    """Test routing decorators"""
    
    def test_log_routing_decision(self):
        """Test routing decision logging"""
        from src.edges.conversation_router import log_routing_decision, routing_metrics
        
        @log_routing_decision
        def test_route(state):
            return "test_node"
        
        state = create_test_state()
        state.current_phase = "test_phase"
        state.user_intent = "test_intent"
        
        result = test_route(state)
        assert result == "test_node"
        
        # Check that metrics were recorded
        stats = routing_metrics.get_routing_stats()
        assert stats["total_routes"] > 0
    
    def test_validate_routing_result(self):
        """Test routing result validation"""
        from src.edges.conversation_router import validate_routing_result
        
        @validate_routing_result
        def invalid_route(state):
            return "invalid_node"
        
        state = create_test_state()
        state.current_phase = "topic_selection"
        
        result = invalid_route(state)
        assert result == "query_analyzer"  # Should fallback to safe routing

if __name__ == "__main__":
    pytest.main([__file__]) 