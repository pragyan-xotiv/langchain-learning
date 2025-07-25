"""LangGraph workflow assembly for the Interactive Quiz Generator

This module assembles all components into a complete LangGraph workflow that 
orchestrates the Interactive Quiz Generator conversation flow.
"""

from typing import Dict, Any, Optional, Callable
import asyncio
import logging
from langgraph.graph import StateGraph, END, START
from langchain_openai import ChatOpenAI

from .state import QuizState, create_initial_state
from .nodes import (
    query_analyzer, topic_validator, quiz_generator,
    answer_validator, score_generator
)
from .edges import (
    route_conversation, route_after_query_analysis,
    route_after_topic_validation, route_after_question_generation,
    route_after_answer_validation, route_after_scoring
)
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
        try:
            self.llm = self._create_llm_client()
            self.workflow_graph = None
            self.compiled_graph = None
            self._build_workflow()
        except Exception as e:
            logger.error(f"Failed to initialize workflow: {str(e)}")
            raise WorkflowBuildError(f"Workflow initialization failed: {str(e)}")
    
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
            workflow.add_edge(START, "query_analyzer")
            
            # Add edges
            self._add_edges(workflow)
            
            # Store references
            self.workflow_graph = workflow
            self.compiled_graph = workflow.compile()
            
            logger.info("LangGraph workflow built successfully")
            
        except Exception as e:
            logger.error(f"Failed to build workflow: {str(e)}")
            raise WorkflowBuildError(f"Workflow construction failed: {str(e)}")
    
    def _add_nodes(self, workflow: StateGraph) -> None:
        """Add all processing nodes to the workflow"""
        
        # Core processing nodes - wrapped with LLM injection
        workflow.add_node("query_analyzer", self._wrap_node(query_analyzer))
        workflow.add_node("topic_validator", self._wrap_node(topic_validator))
        workflow.add_node("quiz_generator", self._wrap_node(quiz_generator))
        workflow.add_node("answer_validator", self._wrap_node(answer_validator))
        workflow.add_node("score_generator", self._wrap_node(score_generator))
        
        # Helper nodes - no LLM needed
        workflow.add_node("clarification_handler", self._clarification_handler)
        workflow.add_node("quiz_completion_handler", self._quiz_completion_handler)
        workflow.add_node("session_manager", self._session_manager)
        
        logger.debug("Added all nodes to workflow")
    
    def _add_edges(self, workflow: StateGraph) -> None:
        """Add all edges and routing logic to the workflow"""
        
        # Main conditional edge from query analyzer
        workflow.add_conditional_edges(
            "query_analyzer",
            route_after_query_analysis,
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
        
        # Topic validator conditional edges
        workflow.add_conditional_edges(
            "topic_validator",
            route_after_topic_validation,
            {
                "quiz_generator": "quiz_generator",
                "clarification_handler": "clarification_handler",
                "session_manager": "session_manager",
                "end": END
            }
        )
        
        # Quiz generator conditional edges
        workflow.add_conditional_edges(
            "quiz_generator",
            route_after_question_generation,
            {
                "query_analyzer": "query_analyzer",
                "quiz_generator": "quiz_generator", 
                "quiz_completion_handler": "quiz_completion_handler",
                "end": END
            }
        )
        
        # Answer validator conditional edges
        workflow.add_conditional_edges(
            "answer_validator",
            route_after_answer_validation,
            {
                "score_generator": "score_generator",
                "clarification_handler": "clarification_handler"
            }
        )
        
        # Score generator conditional edges
        workflow.add_conditional_edges(
            "score_generator", 
            route_after_scoring,
            {
                "quiz_generator": "quiz_generator",
                "quiz_completion_handler": "quiz_completion_handler",
                "query_analyzer": "query_analyzer"
            }
        )
        
        # Helper node edges - all return to query analyzer
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
        # Check for errors first since they take priority
        if state.last_error:
            return "error_recovery"
        elif state.current_phase == "topic_selection":
            return "topic_needed"
        elif state.current_phase == "quiz_active" and not state.current_question:
            return "question_generation_failed" 
        elif state.current_phase == "quiz_active" and state.current_question:
            return "answer_format_help"
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
            graph = self.compiled_graph.get_graph()
            # Get nodes directly from the graph
            nodes = list(self.workflow_graph.nodes.keys()) if self.workflow_graph else []
            
            return {
                "nodes": nodes,
                "edges": len(getattr(graph, 'edges', [])),
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