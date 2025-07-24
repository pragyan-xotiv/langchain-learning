# LangGraph Workflow Assembly

## 🎯 Overview

This guide assembles all components into a complete LangGraph workflow that orchestrates the Interactive Quiz Generator. The workflow connects nodes through conditional edges to create a seamless conversational experience.

## 📋 Reference Documents

- **Design Specification**: `../flow.md`
- **Previous Step**: `05-edge-logic.md` 
- **Next Step**: `07-gradio-interface.md`

## 🏗️ Workflow Implementation

Create the complete workflow system in `src/workflow.py`:

```python
"""LangGraph workflow assembly for the Interactive Quiz Generator"""

from typing import Dict, Any, Optional, Callable
import asyncio
import logging
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI

from .state import QuizState, create_initial_state
from .nodes import (
    query_analyzer, topic_validator, quiz_generator,
    answer_validator, score_generator
)
from .edges import route_conversation, route_after_score_generation
from .utils import Config

# Configure logging
logger = logging.getLogger(__name__)

class QuizWorkflow:
    """
    Main workflow orchestrator for the Interactive Quiz Generator.
    
    This class assembles all nodes and edges into a complete LangGraph workflow
    that manages the entire quiz conversation flow.
    """
    
    def __init__(self):
        """Initialize the quiz workflow"""
        self.llm = self._create_llm_client()
        self.workflow_graph = None
        self.compiled_graph = None
        self._build_workflow()
    
    def _create_llm_client(self) -> ChatOpenAI:
        """Create and configure the LLM client"""
        return ChatOpenAI(
            api_key=Config.OPENAI_API_KEY,
            model=Config.OPENAI_MODEL,
            temperature=Config.OPENAI_TEMPERATURE,
            max_tokens=Config.OPENAI_MAX_TOKENS
        )
    
    def _build_workflow(self) -> None:
        """Build the complete LangGraph workflow"""
        logger.info("Building LangGraph workflow...")
        
        try:
            # Create state graph
            workflow = StateGraph(QuizState)
            
            # Add all nodes
            self._add_nodes(workflow)
            
            # Set entry point
            workflow.set_entry_point("query_analyzer")
            
            # Add edges
            self._add_edges(workflow)
            
            # Compile the workflow
            self.workflow_graph = workflow
            self.compiled_graph = workflow.compile()
            
            logger.info("LangGraph workflow built successfully")
            
        except Exception as e:
            logger.error(f"Failed to build workflow: {str(e)}")
            raise WorkflowBuildError(f"Workflow construction failed: {str(e)}")
    
    def _add_nodes(self, workflow: StateGraph) -> None:
        """Add all processing nodes to the workflow"""
        
        # Core processing nodes
        workflow.add_node("query_analyzer", self._wrap_node(query_analyzer))
        workflow.add_node("topic_validator", self._wrap_node(topic_validator))
        workflow.add_node("quiz_generator", self._wrap_node(quiz_generator))
        workflow.add_node("answer_validator", self._wrap_node(answer_validator))
        workflow.add_node("score_generator", self._wrap_node(score_generator))
        
        # Helper nodes
        workflow.add_node("clarification_handler", self._wrap_node(self._clarification_handler))
        workflow.add_node("quiz_completion_handler", self._wrap_node(self._quiz_completion_handler))
        workflow.add_node("session_manager", self._wrap_node(self._session_manager))
        
        logger.debug("Added all nodes to workflow")
    
    def _add_edges(self, workflow: StateGraph) -> None:
        """Add all edges and routing logic to the workflow"""
        
        # Main conditional edge from query analyzer
        workflow.add_conditional_edges(
            "query_analyzer",
            self._route_from_query_analyzer,
            {
                "topic_validator": "topic_validator",
                "answer_validator": "answer_validator", 
                "quiz_generator": "quiz_generator",
                "score_generator": "score_generator",
                "clarification_handler": "clarification_handler",
                "session_manager": "session_manager",
                "end": END
            }
        )
        
        # Topic validator edges
        workflow.add_conditional_edges(
            "topic_validator",
            self._route_from_topic_validator,
            {
                "quiz_generator": "quiz_generator",
                "clarification_handler": "clarification_handler",
                "session_manager": "session_manager",
                "end": END
            }
        )
        
        # Quiz generator always returns to query analyzer
        workflow.add_edge("quiz_generator", "query_analyzer")
        
        # Answer validator always goes to score generator
        workflow.add_edge("answer_validator", "score_generator")
        
        # Score generator conditional routing
        workflow.add_conditional_edges(
            "score_generator",
            self._route_from_score_generator,
            {
                "quiz_generator": "quiz_generator",
                "quiz_completion_handler": "quiz_completion_handler",
                "query_analyzer": "query_analyzer"
            }
        )
        
        # Helper node edges
        workflow.add_edge("clarification_handler", "query_analyzer")
        workflow.add_edge("quiz_completion_handler", "query_analyzer")
        workflow.add_edge("session_manager", "query_analyzer")
        
        logger.debug("Added all edges to workflow")
    
    def _wrap_node(self, node_func: Callable) -> Callable:
        """Wrap node function with LLM client injection and error handling"""
        
        def wrapped_node(state: QuizState) -> QuizState:
            try:
                # Inject LLM client for nodes that need it
                if node_func.__name__ in ['query_analyzer', 'topic_validator', 'quiz_generator', 'answer_validator']:
                    return node_func(state, self.llm)
                else:
                    return node_func(state)
            except Exception as e:
                logger.error(f"Node {node_func.__name__} failed: {str(e)}")
                state.last_error = f"System error in {node_func.__name__}: {str(e)}"
                state.retry_count += 1
                return state
        
        return wrapped_node
    
    # === ROUTING FUNCTIONS ===
    
    def _route_from_query_analyzer(self, state: QuizState) -> str:
        """Route from query analyzer based on intent and phase"""
        return route_conversation(state)
    
    def _route_from_topic_validator(self, state: QuizState) -> str:
        """Route from topic validator based on validation results"""
        if state.topic_validated:
            return "quiz_generator"
        elif state.retry_count >= 3:
            return "end"
        else:
            return "clarification_handler"
    
    def _route_from_score_generator(self, state: QuizState) -> str:
        """Route from score generator based on quiz status"""
        if state.quiz_completed:
            return "quiz_completion_handler"
        else:
            return "quiz_generator"
    
    # === HELPER NODES ===
    
    def _clarification_handler(self, state: QuizState) -> QuizState:
        """Handle clarification requests and provide helpful responses"""
        logger.info("Processing clarification request")
        
        try:
            # Determine clarification type based on current phase and error
            clarification_type = self._determine_clarification_type(state)
            
            # Generate appropriate clarification message
            clarification_message = self._generate_clarification_message(state, clarification_type)
            
            # Update conversation history
            state.add_conversation_entry(
                user_input=state.user_input,
                system_response=clarification_message
            )
            
            # Reset for fresh input
            state.user_input = ""
            state.last_error = None
            
            return state
            
        except Exception as e:
            logger.error(f"Clarification handler error: {str(e)}")
            state.last_error = "I'm having trouble helping you. Please try again."
            return state
    
    def _quiz_completion_handler(self, state: QuizState) -> QuizState:
        """Handle quiz completion and generate summary"""
        logger.info("Processing quiz completion")
        
        try:
            # Generate completion summary
            summary = self._generate_completion_summary(state)
            
            # Update conversation history
            state.add_conversation_entry(
                user_input="Quiz completed",
                system_response=summary
            )
            
            # Update phase
            state.current_phase = "quiz_complete"
            
            return state
            
        except Exception as e:
            logger.error(f"Quiz completion handler error: {str(e)}")
            state.last_error = "Error generating quiz summary"
            return state
    
    def _session_manager(self, state: QuizState) -> QuizState:
        """Handle session management tasks"""
        logger.info("Processing session management")
        
        try:
            # Handle session reset for new quiz
            if state.user_intent == "new_quiz":
                state.reset_for_new_quiz()
                state.add_conversation_entry(
                    user_input=state.user_input,
                    system_response="Starting a new quiz! What topic would you like to explore?"
                )
            
            # Handle session termination
            elif state.user_intent == "exit":
                state.add_conversation_entry(
                    user_input=state.user_input,
                    system_response="Thanks for using the Quiz Generator! Goodbye!"
                )
            
            return state
            
        except Exception as e:
            logger.error(f"Session manager error: {str(e)}")
            state.last_error = "Error managing session"
            return state
    
    # === HELPER METHODS ===
    
    def _determine_clarification_type(self, state: QuizState) -> str:
        """Determine what type of clarification is needed"""
        if state.current_phase == "topic_selection":
            return "topic_needed"
        elif state.current_phase == "quiz_active" and not state.current_question:
            return "question_generation_failed" 
        elif state.current_phase == "quiz_active" and state.current_question:
            return "answer_format_help"
        elif state.last_error:
            return "error_recovery"
        else:
            return "general_help"
    
    def _generate_clarification_message(self, state: QuizState, clarification_type: str) -> str:
        """Generate appropriate clarification message"""
        
        messages = {
            "topic_needed": "I'd love to create a quiz for you! What topic would you like to be quizzed on? For example: 'Python programming', 'World War II history', or 'basic chemistry'.",
            
            "question_generation_failed": "I had trouble creating a question for that topic. Could you try a different topic or be more specific about what you'd like to learn?",
            
            "answer_format_help": f"I'm waiting for your answer to: '{state.current_question}'\n\nYou can answer in your own words, or if it's multiple choice, just say the letter (A, B, C, or D).",
            
            "error_recovery": f"I encountered an issue: {state.last_error}\n\nLet's try again! You can:\n- Continue with the current quiz\n- Start a new quiz with 'new quiz'\n- Exit with 'exit'",
            
            "general_help": "I'm here to help! You can:\n- Start a quiz by telling me a topic\n- Answer the current question if we're in a quiz\n- Say 'new quiz' to start over\n- Say 'exit' to end our conversation"
        }
        
        return messages.get(clarification_type, messages["general_help"])
    
    def _generate_completion_summary(self, state: QuizState) -> str:
        """Generate quiz completion summary"""
        performance = state.get_performance_summary()
        accuracy = performance['accuracy']
        
        # Determine performance level
        if accuracy >= 90:
            performance_level = "Excellent"
            emoji = "🎉"
        elif accuracy >= 80:
            performance_level = "Great"
            emoji = "👏"
        elif accuracy >= 70:
            performance_level = "Good"
            emoji = "👍"
        elif accuracy >= 60:
            performance_level = "Fair"
            emoji = "📈"
        else:
            performance_level = "Keep practicing"
            emoji = "💪"
        
        summary = f"""{emoji} **Quiz Complete!**

**{performance_level} work on {state.topic}!**

📊 **Final Results:**
- Questions answered: {state.total_questions_answered}
- Correct answers: {state.correct_answers_count}
- Accuracy: {accuracy:.1f}%
- Total score: {state.total_score} points

Would you like to:
- Try a **new quiz** on a different topic?
- **Exit** and come back later?

Just let me know what you'd prefer!"""
        
        return summary
    
    # === WORKFLOW EXECUTION ===
    
    async def process_input(self, user_input: str, current_state: Optional[QuizState] = None) -> QuizState:
        """
        Process user input through the complete workflow.
        
        Args:
            user_input: User's input text
            current_state: Current quiz state (creates new if None)
            
        Returns:
            Updated quiz state after processing
        """
        logger.info(f"Processing user input: '{user_input}'")
        
        try:
            # Create or update state
            if current_state is None:
                state = create_initial_state()
            else:
                state = current_state
            
            # Set user input
            state.user_input = user_input.strip()
            
            # Execute workflow
            result = await self.compiled_graph.ainvoke(state)
            
            logger.info(f"Workflow completed, final phase: {result.current_phase}")
            return result
            
        except Exception as e:
            logger.error(f"Workflow execution error: {str(e)}")
            
            # Create error state
            if current_state:
                current_state.last_error = f"System error: {str(e)}"
                return current_state
            else:
                error_state = create_initial_state()
                error_state.last_error = f"System error: {str(e)}"
                return error_state
    
    def process_input_sync(self, user_input: str, current_state: Optional[QuizState] = None) -> QuizState:
        """Synchronous wrapper for process_input"""
        return asyncio.run(self.process_input(user_input, current_state))
    
    def get_response_for_state(self, state: QuizState) -> str:
        """Generate appropriate response text based on current state"""
        
        # Handle errors first
        if state.last_error:
            return f"Sorry, I encountered an issue: {state.last_error}\n\nHow would you like to proceed?"
        
        # Handle phase-specific responses
        if state.current_phase == "topic_selection":
            return "What topic would you like to be quizzed on?"
        
        elif state.current_phase == "topic_validation":
            if state.topic_validated:
                return f"Great! Starting your {state.topic} quiz."
            else:
                return "I had trouble with that topic. Could you try a different one?"
        
        elif state.current_phase == "quiz_active":
            if state.current_question:
                if state.question_type == "multiple_choice" and state.question_options:
                    options = "\n".join([
                        f"{chr(65+i)}) {opt}" 
                        for i, opt in enumerate(state.question_options)
                    ])
                    return f"**Question {state.current_question_index + 1}:** {state.current_question}\n\n{options}"
                else:
                    return f"**Question {state.current_question_index + 1}:** {state.current_question}"
            else:
                return "Let me generate a question for you..."
        
        elif state.current_phase == "question_answered":
            feedback = state.answer_feedback or "Answer processed."
            progress = f"Score: {state.total_score} points ({state.correct_answers_count}/{state.total_questions_answered} correct)"
            
            if not state.quiz_completed:
                return f"{feedback}\n\n{progress}\n\nReady for the next question?"
            else:
                return self._generate_completion_summary(state)
        
        elif state.current_phase == "quiz_complete":
            return "Would you like to start a new quiz or end here?"
        
        else:
            return "I'm not sure how to help with that. What would you like to do?"
    
    # === WORKFLOW INTROSPECTION ===
    
    def get_workflow_info(self) -> Dict[str, Any]:
        """Get information about the workflow structure"""
        if not self.compiled_graph:
            return {"error": "Workflow not compiled"}
        
        try:
            graph_dict = self.compiled_graph.get_graph().to_json()
            return {
                "nodes": list(graph_dict.get("nodes", {}).keys()),
                "edges": len(graph_dict.get("edges", [])),
                "entry_point": "query_analyzer",
                "compiled": True
            }
        except Exception as e:
            return {"error": f"Failed to get workflow info: {str(e)}"}
    
    def visualize_workflow(self) -> str:
        """Generate a text representation of the workflow"""
        try:
            return self.compiled_graph.get_graph().draw_ascii()
        except Exception as e:
            return f"Visualization failed: {str(e)}"

# === EXCEPTIONS ===

class WorkflowError(Exception):
    """Base exception for workflow errors"""
    pass

class WorkflowBuildError(WorkflowError):
    """Error in workflow construction"""
    pass

class WorkflowExecutionError(WorkflowError):
    """Error in workflow execution"""
    pass

# === FACTORY FUNCTIONS ===

def create_quiz_workflow() -> QuizWorkflow:
    """Create and return a configured quiz workflow"""
    try:
        workflow = QuizWorkflow()
        logger.info("Quiz workflow created successfully")
        return workflow
    except Exception as e:
        logger.error(f"Failed to create quiz workflow: {str(e)}")
        raise WorkflowBuildError(f"Workflow creation failed: {str(e)}")

# === TESTING UTILITIES ===

async def test_workflow_execution():
    """Test complete workflow execution"""
    workflow = create_quiz_workflow()
    
    # Test conversation flow
    test_inputs = [
        "I want a quiz about Python programming",
        "Lists are collections of items",
        "continue",
        "exit"
    ]
    
    state = None
    for user_input in test_inputs:
        logger.info(f"Testing input: '{user_input}'")
        state = await workflow.process_input(user_input, state)
        response = workflow.get_response_for_state(state)
        logger.info(f"Response: {response[:100]}...")
    
    return state

def test_workflow_sync():
    """Synchronous test of workflow"""
    return asyncio.run(test_workflow_execution())

if __name__ == "__main__":
    # Test workflow
    print("Testing Quiz Workflow...")
    
    try:
        final_state = test_workflow_sync()
        print(f"Test completed. Final phase: {final_state.current_phase}")
        
        # Print workflow info
        workflow = create_quiz_workflow()
        info = workflow.get_workflow_info()
        print(f"Workflow info: {info}")
        
    except Exception as e:
        print(f"Test failed: {str(e)}")
```

## 🧪 Workflow Testing Implementation  

Create comprehensive tests in `tests/test_workflow.py`:

```python
"""Tests for workflow assembly and execution"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from src.workflow import (
    QuizWorkflow, create_quiz_workflow, WorkflowBuildError,
    test_workflow_execution
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

class TestWorkflowExecution:
    """Test workflow execution"""
    
    @patch('src.workflow.ChatOpenAI')
    @patch('src.nodes.safe_llm_call')
    def test_process_input_new_state(self, mock_llm_call, mock_openai):
        """Test processing input with new state"""
        mock_openai.return_value = Mock()
        mock_llm_call.return_value = asyncio.Future()
        mock_llm_call.return_value.set_result('{"intent": "start_quiz", "confidence": 0.9}')
        
        workflow = QuizWorkflow()
        
        # Test with new state
        result = asyncio.run(workflow.process_input("I want a quiz about Python"))
        
        assert isinstance(result, QuizState)
        assert result.user_input == "I want a quiz about Python"
    
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
    
    @patch('src.workflow.ChatOpenAI') 
    def test_session_manager_new_quiz(self, mock_openai):
        """Test session manager for new quiz"""
        mock_openai.return_value = Mock()
        
        workflow = QuizWorkflow()
        state = QuizState()
        state.user_intent = "new_quiz"
        state.topic = "Old Topic"
        state.total_score = 50
        
        result = workflow._session_manager(state)
        
        # State should be reset for new quiz
        assert result.topic is None
        assert result.total_score == 0
    
    @patch('src.workflow.ChatOpenAI')
    def test_session_manager_exit(self, mock_openai):
        """Test session manager for exit"""
        mock_openai.return_value = Mock()
        
        workflow = QuizWorkflow()
        state = QuizState()
        state.user_intent = "exit"
        
        result = workflow._session_manager(state)
        
        assert len(result.conversation_history) > 0
        last_message = result.conversation_history[-1]["system"]
        assert "goodbye" in last_message.lower()

class TestRoutingFunctions:
    """Test workflow routing functions"""
    
    @patch('src.workflow.ChatOpenAI')
    def test_route_from_query_analyzer(self, mock_openai):
        """Test routing from query analyzer"""
        mock_openai.return_value = Mock()
        
        workflow = QuizWorkflow()
        state = QuizState()
        state.user_intent = "start_quiz"
        state.current_phase = "topic_selection"
        
        result = workflow._route_from_query_analyzer(state)
        
        assert result == "topic_validator"
    
    @patch('src.workflow.ChatOpenAI')
    def test_route_from_topic_validator(self, mock_openai):
        """Test routing from topic validator"""
        mock_openai.return_value = Mock()
        
        workflow = QuizWorkflow()
        state = QuizState()
        
        # Test successful validation
        state.topic_validated = True
        result = workflow._route_from_topic_validator(state)
        assert result == "quiz_generator"
        
        # Test failed validation with retries
        state.topic_validated = False
        state.retry_count = 1
        result = workflow._route_from_topic_validator(state)
        assert result == "clarification_handler"
        
        # Test max retries
        state.retry_count = 3
        result = workflow._route_from_topic_validator(state)
        assert result == "end"
    
    @patch('src.workflow.ChatOpenAI')
    def test_route_from_score_generator(self, mock_openai):
        """Test routing from score generator"""
        mock_openai.return_value = Mock()
        
        workflow = QuizWorkflow()
        state = QuizState()
        
        # Test quiz completed
        state.quiz_completed = True
        result = workflow._route_from_score_generator(state)
        assert result == "quiz_completion_handler"
        
        # Test quiz continues
        state.quiz_completed = False
        result = workflow._route_from_score_generator(state)
        assert result == "quiz_generator"

class TestWorkflowIntegration:
    """Test complete workflow integration"""
    
    @patch('src.workflow.ChatOpenAI')
    @patch('src.nodes.safe_llm_call')
    async def test_complete_quiz_flow(self, mock_llm_call, mock_openai):
        """Test complete quiz workflow"""
        mock_openai.return_value = Mock()
        
        # Mock LLM responses for different stages
        mock_responses = [
            '{"intent": "start_quiz", "confidence": 0.9}',  # Intent classification
            '{"topic": "Python Programming", "confidence": 0.9}',  # Topic extraction
            '{"is_valid": true, "category": "programming"}',  # Topic validation
            '{"question": "What is a list?", "type": "open_ended", "correct_answer": "A collection"}',  # Question generation
            '{"is_correct": true, "feedback": "Correct!"}',  # Answer validation
        ]
        
        call_count = 0
        async def mock_llm_response(*args, **kwargs):
            nonlocal call_count
            if call_count < len(mock_responses):
                result = mock_responses[call_count]
                call_count += 1
                return result
            return '{"intent": "continue", "confidence": 0.8}'
        
        mock_llm_call.side_effect = mock_llm_response
        
        workflow = QuizWorkflow()
        
        # Start quiz
        state = await workflow.process_input("I want a quiz about Python programming")
        assert state.user_input == "I want a quiz about Python programming"
        
        # This test would need more sophisticated mocking to fully test the flow
        # For now, we verify the basic structure works
    
    @patch('src.workflow.ChatOpenAI')
    def test_workflow_error_handling(self, mock_openai):
        """Test workflow error handling"""
        mock_openai.return_value = Mock()
        
        workflow = QuizWorkflow()
        
        # Test with workflow execution error
        with patch.object(workflow.compiled_graph, 'ainvoke', side_effect=Exception("Test error")):
            result = workflow.process_input_sync("test input")
            
            assert result.last_error is not None
            assert "Test error" in result.last_error

if __name__ == "__main__":
    pytest.main([__file__])
```

## 📋 Implementation Checklist

### Core Implementation
- [ ] **QuizWorkflow Class**: Complete workflow orchestrator
- [ ] **Node Integration**: All nodes properly wrapped and integrated
- [ ] **Edge Configuration**: All routing logic properly configured
- [ ] **Helper Nodes**: Clarification, completion, and session management nodes
- [ ] **Error Handling**: Comprehensive error handling throughout workflow

### Advanced Features
- [ ] **Async Support**: Proper async/await throughout workflow execution
- [ ] **State Management**: Proper state passing and updates
- [ ] **Response Generation**: Context-aware response generation
- [ ] **Workflow Introspection**: Methods to inspect and visualize workflow

### Testing
- [ ] **Unit Tests**: All workflow components tested independently
- [ ] **Integration Tests**: Complete workflow execution tested
- [ ] **Error Scenarios**: Error handling and recovery tested
- [ ] **Performance Tests**: Workflow execution performance validated

## ✅ Completion Criteria

Workflow assembly is complete when:

1. **Complete LangGraph workflow implemented** with all nodes and edges
2. **All routing logic working** correctly between nodes
3. **Helper nodes implemented** for clarification and session management
4. **Async execution working** reliably with proper error handling
5. **Response generation working** for all application states
6. **Complete test suite passing** with >90% coverage

**Next Step**: Proceed to **[07-gradio-interface.md](./07-gradio-interface.md)** to implement the web interface. 