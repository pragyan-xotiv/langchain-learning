"""Tests for workflow assembly and execution

This module tests the complete LangGraph workflow assembly, including:
- Workflow construction and initialization
- Node integration and execution
- Edge routing and state transitions
- Helper node functionality
- Error handling and recovery
- Response generation
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from src.workflow import (
    QuizWorkflow, create_quiz_workflow, WorkflowBuildError,
    WorkflowExecutionError, test_workflow_execution
)
from src.state import QuizState, create_initial_state

class TestWorkflowConstruction:
    """Test workflow construction and setup"""
    
    @patch('src.workflow.ChatOpenAI')
    def test_workflow_initialization(self, mock_openai):
        """Test workflow initialization"""
        mock_openai.return_value = Mock()
        
        workflow = QuizWorkflow()
        
        assert workflow.llm is not None
        assert workflow.compiled_graph is not None
        assert workflow.workflow_graph is not None
    
    @patch('src.workflow.ChatOpenAI')
    def test_workflow_factory(self, mock_openai):
        """Test workflow factory function"""
        mock_openai.return_value = Mock()
        
        workflow = create_quiz_workflow()
        
        assert isinstance(workflow, QuizWorkflow)
        assert workflow.compiled_graph is not None
    
    @patch('src.workflow.ChatOpenAI')
    def test_workflow_info(self, mock_openai):
        """Test workflow information retrieval"""
        mock_openai.return_value = Mock()
        
        workflow = QuizWorkflow()
        info = workflow.get_workflow_info()
        
        assert "nodes" in info
        assert "edges" in info
        assert info["compiled"] is True
        assert "query_analyzer" in info["nodes"]
    
    @patch('src.workflow.ChatOpenAI')
    @patch('src.workflow.QuizWorkflow._create_llm_client')
    def test_workflow_build_error(self, mock_create_llm, mock_openai):
        """Test workflow build error handling"""
        mock_create_llm.side_effect = Exception("OpenAI connection failed")
        
        with pytest.raises(WorkflowBuildError):
            QuizWorkflow()

class TestWorkflowExecution:
    """Test workflow execution"""
    
    @patch('src.workflow.ChatOpenAI')
    @patch('src.nodes.query_analyzer.safe_llm_call')
    def test_process_input_new_state(self, mock_llm_call, mock_openai):
        """Test processing input with new state"""
        mock_openai.return_value = Mock()
        
        # Mock successful LLM response
        async def mock_llm_response(*args, **kwargs):
            return '{"intent": "start_quiz", "confidence": 0.9}'
        
        mock_llm_call.side_effect = mock_llm_response
        
        workflow = QuizWorkflow()
        
        # Mock the compiled graph to avoid complex execution
        mock_result = create_initial_state()
        mock_result.user_input = "I want a quiz about Python"
        mock_result.user_intent = "start_quiz"
        
        with patch.object(workflow.compiled_graph, 'ainvoke', return_value=asyncio.Future()) as mock_invoke:
            mock_invoke.return_value.set_result(mock_result)
            
            result = asyncio.run(workflow.process_input("I want a quiz about Python"))
            
            assert isinstance(result, QuizState)
            assert result.user_input == "I want a quiz about Python"
            assert result.user_intent == "start_quiz"
    
    @patch('src.workflow.ChatOpenAI')
    def test_process_input_existing_state(self, mock_openai):
        """Test processing input with existing state"""
        mock_openai.return_value = Mock()
        
        workflow = QuizWorkflow()
        existing_state = create_initial_state()
        existing_state.topic = "Python Programming"
        
        # Mock the workflow execution to avoid complex LLM calls
        with patch.object(workflow.compiled_graph, 'ainvoke', return_value=asyncio.Future()) as mock_invoke:
            mock_invoke.return_value.set_result(existing_state)
            
            result = asyncio.run(workflow.process_input("continue", existing_state))
            
            assert result.topic == "Python Programming"
    
    @patch('src.workflow.ChatOpenAI')
    def test_process_input_sync(self, mock_openai):
        """Test synchronous input processing"""
        mock_openai.return_value = Mock()
        
        workflow = QuizWorkflow()
        
        with patch.object(workflow, 'process_input', return_value=asyncio.Future()) as mock_process:
            test_state = create_initial_state()
            mock_process.return_value.set_result(test_state)
            
            result = workflow.process_input_sync("test input")
            
            assert isinstance(result, QuizState)
    
    @patch('src.workflow.ChatOpenAI')
    def test_process_input_error_handling(self, mock_openai):
        """Test error handling during input processing"""
        mock_openai.return_value = Mock()
        
        workflow = QuizWorkflow()
        
        # Mock workflow execution to raise an error
        with patch.object(workflow.compiled_graph, 'ainvoke', side_effect=Exception("Execution failed")):
            result = asyncio.run(workflow.process_input("test input"))
            
            assert result.last_error is not None
            assert "System error" in result.last_error

class TestResponseGeneration:
    """Test response generation for different states"""
    
    @patch('src.workflow.ChatOpenAI')
    def test_response_topic_selection(self, mock_openai):
        """Test response for topic selection phase"""
        mock_openai.return_value = Mock()
        
        workflow = QuizWorkflow()
        state = QuizState()
        state.current_phase = "topic_selection"
        
        response = workflow.get_response_for_state(state)
        
        assert "topic" in response.lower()
        assert "quiz" in response.lower()
    
    @patch('src.workflow.ChatOpenAI')
    def test_response_quiz_active(self, mock_openai):
        """Test response for quiz active phase"""
        mock_openai.return_value = Mock()
        
        workflow = QuizWorkflow()
        state = QuizState()
        state.current_phase = "quiz_active"
        state.current_question = "What is Python?"
        state.current_question_index = 0
        
        response = workflow.get_response_for_state(state)
        
        assert "Question 1" in response
        assert "What is Python?" in response
    
    @patch('src.workflow.ChatOpenAI')
    def test_response_multiple_choice(self, mock_openai):
        """Test response for multiple choice question"""
        mock_openai.return_value = Mock()
        
        workflow = QuizWorkflow()
        state = QuizState()
        state.current_phase = "quiz_active"
        state.current_question = "Which is correct?"
        state.question_type = "multiple_choice"
        state.question_options = ["Option A", "Option B", "Option C", "Option D"]
        state.current_question_index = 0
        
        response = workflow.get_response_for_state(state)
        
        assert "A) Option A" in response
        assert "B) Option B" in response
        assert "C) Option C" in response
        assert "D) Option D" in response
    
    @patch('src.workflow.ChatOpenAI')
    def test_response_with_error(self, mock_openai):
        """Test response when there's an error"""
        mock_openai.return_value = Mock()
        
        workflow = QuizWorkflow()
        state = QuizState()
        state.last_error = "Test error message"
        
        response = workflow.get_response_for_state(state)
        
        assert "Test error message" in response
        assert "issue" in response.lower()
    
    @patch('src.workflow.ChatOpenAI')
    def test_response_question_answered(self, mock_openai):
        """Test response after question is answered"""
        mock_openai.return_value = Mock()
        
        workflow = QuizWorkflow()
        state = QuizState()
        state.current_phase = "question_answered"
        state.answer_feedback = "Correct!"
        state.total_score = 10
        state.correct_answers_count = 1
        state.total_questions_answered = 1
        state.quiz_completed = False
        
        response = workflow.get_response_for_state(state)
        
        assert "Correct!" in response
        assert "Score: 10 points" in response
        assert "Ready for the next question?" in response

class TestHelperNodes:
    """Test helper node functionality"""
    
    @patch('src.workflow.ChatOpenAI')
    def test_clarification_handler(self, mock_openai):
        """Test clarification handler node"""
        mock_openai.return_value = Mock()
        
        workflow = QuizWorkflow()
        state = QuizState()
        state.current_phase = "topic_selection"
        state.user_input = "unclear input"
        
        result = workflow._clarification_handler(state)
        
        assert len(result.conversation_history) > 0
        assert result.user_input == ""  # Should be reset
        assert result.last_error is None
    
    @patch('src.workflow.ChatOpenAI')
    def test_clarification_handler_error_recovery(self, mock_openai):
        """Test clarification handler for error recovery"""
        mock_openai.return_value = Mock()
        
        workflow = QuizWorkflow()
        state = QuizState()
        state.current_phase = "quiz_active"
        state.last_error = "Something went wrong"
        state.user_input = "help"
        
        result = workflow._clarification_handler(state)
        
        assert result.last_error is None
        assert len(result.conversation_history) > 0
        # Check that error recovery message mentions the error
        last_response = result.conversation_history[-1]["system"]
        assert "Something went wrong" in last_response
    
    @patch('src.workflow.ChatOpenAI')
    def test_quiz_completion_handler(self, mock_openai):
        """Test quiz completion handler"""
        mock_openai.return_value = Mock()
        
        workflow = QuizWorkflow()
        state = QuizState()
        state.topic = "Python Programming"
        state.total_questions_answered = 5
        state.correct_answers_count = 4
        state.total_score = 40
        
        result = workflow._quiz_completion_handler(state)
        
        assert result.current_phase == "quiz_complete"
        assert len(result.conversation_history) > 0
        # Check completion summary content
        last_response = result.conversation_history[-1]["system"]
        assert "Quiz Complete!" in last_response
        assert "Python Programming" in last_response
        assert "40 points" in last_response
    
    @patch('src.workflow.ChatOpenAI') 
    def test_session_manager_new_quiz(self, mock_openai):
        """Test session manager for new quiz"""
        mock_openai.return_value = Mock()
        
        workflow = QuizWorkflow()
        state = QuizState()
        state.user_intent = "new_quiz"
        state.user_input = "new quiz"
        state.topic = "Old Topic"
        state.total_score = 50
        
        result = workflow._session_manager(state)
        
        # State should be reset for new quiz
        assert result.topic is None
        assert result.total_score == 0
        assert len(result.conversation_history) > 0
    
    @patch('src.workflow.ChatOpenAI')
    def test_session_manager_exit(self, mock_openai):
        """Test session manager for exit"""
        mock_openai.return_value = Mock()
        
        workflow = QuizWorkflow()
        state = QuizState()
        state.user_intent = "exit"
        state.user_input = "exit"
        
        result = workflow._session_manager(state)
        
        assert len(result.conversation_history) > 0
        last_message = result.conversation_history[-1]["system"]
        assert "goodbye" in last_message.lower()

class TestClarificationTypes:
    """Test different clarification type handling"""
    
    @patch('src.workflow.ChatOpenAI')
    def test_determine_clarification_type_topic_needed(self, mock_openai):
        """Test clarification type determination for topic selection"""
        mock_openai.return_value = Mock()
        
        workflow = QuizWorkflow()
        state = QuizState()
        state.current_phase = "topic_selection"
        
        clarification_type = workflow._determine_clarification_type(state)
        
        assert clarification_type == "topic_needed"
    
    @patch('src.workflow.ChatOpenAI')
    def test_determine_clarification_type_answer_help(self, mock_openai):
        """Test clarification type for answer format help"""
        mock_openai.return_value = Mock()
        
        workflow = QuizWorkflow()
        state = QuizState()
        state.current_phase = "quiz_active"
        state.current_question = "What is Python?"
        
        clarification_type = workflow._determine_clarification_type(state)
        
        assert clarification_type == "answer_format_help"
    
    @patch('src.workflow.ChatOpenAI')
    def test_generate_clarification_message_topic_needed(self, mock_openai):
        """Test clarification message generation for topic needed"""
        mock_openai.return_value = Mock()
        
        workflow = QuizWorkflow()
        state = QuizState()
        
        message = workflow._generate_clarification_message(state, "topic_needed")
        
        assert "topic" in message.lower()
        assert "quiz" in message.lower()
        assert "Python programming" in message  # Example topic

class TestCompletionSummary:
    """Test quiz completion summary generation"""
    
    @patch('src.workflow.ChatOpenAI')
    def test_completion_summary_excellent(self, mock_openai):
        """Test completion summary for excellent performance"""
        mock_openai.return_value = Mock()
        
        workflow = QuizWorkflow()
        state = QuizState()
        state.topic = "Python Programming"
        state.total_questions_answered = 10
        state.correct_answers_count = 9  # 90% accuracy
        state.total_score = 90
        
        summary = workflow._generate_completion_summary(state)
        
        assert "Excellent" in summary
        assert "🎉" in summary
        assert "90%" in summary
        assert "Python Programming" in summary
    
    @patch('src.workflow.ChatOpenAI')
    def test_completion_summary_fair(self, mock_openai):
        """Test completion summary for fair performance"""
        mock_openai.return_value = Mock()
        
        workflow = QuizWorkflow()
        state = QuizState()
        state.topic = "History"
        state.total_questions_answered = 10
        state.correct_answers_count = 6  # 60% accuracy
        state.total_score = 60
        
        summary = workflow._generate_completion_summary(state)
        
        assert "Fair" in summary
        assert "📈" in summary
        assert "60%" in summary

class TestNodeWrapping:
    """Test node function wrapping"""
    
    @patch('src.workflow.ChatOpenAI')
    def test_wrap_node_with_llm_injection(self, mock_openai):
        """Test node wrapping with LLM injection"""
        mock_openai.return_value = Mock()
        
        # Mock node function that expects LLM
        def mock_node(state, llm):
            assert llm is not None
            return state
        
        mock_node.__name__ = "query_analyzer"
        
        workflow = QuizWorkflow()
        wrapped = workflow._wrap_node(mock_node)
        
        state = QuizState()
        result = wrapped(state)
        
        assert result == state
    
    @patch('src.workflow.ChatOpenAI')
    def test_wrap_node_without_llm(self, mock_openai):
        """Test node wrapping without LLM injection"""
        mock_openai.return_value = Mock()
        
        # Mock node function that doesn't need LLM
        def mock_node(state):
            return state
        
        mock_node.__name__ = "other_node"
        
        workflow = QuizWorkflow()
        wrapped = workflow._wrap_node(mock_node)
        
        state = QuizState()
        result = wrapped(state)
        
        assert result == state
    
    @patch('src.workflow.ChatOpenAI')
    def test_wrap_node_error_handling(self, mock_openai):
        """Test node wrapping error handling"""
        mock_openai.return_value = Mock()
        
        # Mock node function that raises an error
        def mock_node(state, llm):
            raise Exception("Node failed")
        
        mock_node.__name__ = "failing_node"
        
        workflow = QuizWorkflow()
        wrapped = workflow._wrap_node(mock_node)
        
        state = QuizState()
        result = wrapped(state)
        
        assert result.last_error is not None
        assert "Node failed" in result.last_error
        assert result.retry_count == 1

class TestWorkflowIntrospection:
    """Test workflow introspection capabilities"""
    
    @patch('src.workflow.ChatOpenAI')
    def test_workflow_visualization(self, mock_openai):
        """Test workflow visualization"""
        mock_openai.return_value = Mock()
        
        workflow = QuizWorkflow()
        
        # Mock the graph visualization
        with patch.object(workflow.compiled_graph.get_graph(), 'draw_ascii', return_value="ASCII GRAPH"):
            visualization = workflow.visualize_workflow()
            
            assert "ASCII GRAPH" in visualization
    
    @patch('src.workflow.ChatOpenAI')
    def test_workflow_visualization_error(self, mock_openai):
        """Test workflow visualization error handling"""
        mock_openai.return_value = Mock()
        
        workflow = QuizWorkflow()
        
        # Mock visualization to raise an error
        with patch.object(workflow.compiled_graph.get_graph(), 'draw_ascii', side_effect=Exception("Viz failed")):
            visualization = workflow.visualize_workflow()
            
            assert "Visualization failed" in visualization
            assert "Viz failed" in visualization

class TestWorkflowIntegration:
    """Test complete workflow integration"""
    
    @patch('src.workflow.ChatOpenAI')
    def test_workflow_factory_error_handling(self, mock_openai):
        """Test workflow factory error handling"""
        mock_openai.side_effect = Exception("Factory failed")
        
        with pytest.raises(WorkflowBuildError):
            create_quiz_workflow()
    
    @patch('src.workflow.ChatOpenAI')
    @patch('src.nodes.query_analyzer.safe_llm_call')
    async def test_workflow_execution_test_utility(self, mock_llm_call, mock_openai):
        """Test the test_workflow_execution utility"""
        mock_openai.return_value = Mock()
        
        # Mock LLM responses
        async def mock_llm_response(*args, **kwargs):
            return '{"intent": "start_quiz", "confidence": 0.9}'
        
        mock_llm_call.side_effect = mock_llm_response
        
        # Mock the workflow execution to avoid complex state transitions
        with patch('src.workflow.QuizWorkflow.process_input') as mock_process:
            mock_state = create_initial_state()
            mock_process.return_value = asyncio.Future()
            mock_process.return_value.set_result(mock_state)
            
            result = await test_workflow_execution()
            
            assert isinstance(result, QuizState)

class TestErrorHandling:
    """Test comprehensive error handling"""
    
    @patch('src.workflow.ChatOpenAI')
    def test_clarification_handler_exception(self, mock_openai):
        """Test clarification handler exception handling"""
        mock_openai.return_value = Mock()
        
        workflow = QuizWorkflow()
        state = QuizState()
        
        # Mock _determine_clarification_type to raise an exception
        with patch.object(workflow, '_determine_clarification_type', side_effect=Exception("Handler failed")):
            result = workflow._clarification_handler(state)
            
            assert result.last_error is not None
            assert "trouble helping" in result.last_error
    
    @patch('src.workflow.ChatOpenAI')
    def test_quiz_completion_handler_exception(self, mock_openai):
        """Test quiz completion handler exception handling"""
        mock_openai.return_value = Mock()
        
        workflow = QuizWorkflow()
        state = QuizState()
        
        # Mock _generate_completion_summary to raise an exception
        with patch.object(workflow, '_generate_completion_summary', side_effect=Exception("Summary failed")):
            result = workflow._quiz_completion_handler(state)
            
            assert result.last_error is not None
            assert "Error generating quiz summary" in result.last_error
    
    @patch('src.workflow.ChatOpenAI')
    def test_session_manager_exception(self, mock_openai):
        """Test session manager exception handling"""
        mock_openai.return_value = Mock()
        
        workflow = QuizWorkflow()
        state = QuizState()
        state.user_intent = "new_quiz"
        
        # Mock reset_for_new_quiz to raise an exception
        with patch.object(state, 'reset_for_new_quiz', side_effect=Exception("Reset failed")):
            result = workflow._session_manager(state)
            
            assert result.last_error is not None
            assert "Error managing session" in result.last_error

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 