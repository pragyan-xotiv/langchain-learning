"""Main conversation router for the Interactive Quiz Generator workflow

This module implements the primary routing logic that determines the next node based on
current state, user intent, and system conditions. It handles complex decision-making
and provides error recovery mechanisms.
"""

from typing import Dict, Optional, Literal, Callable, List, Any
import logging
from datetime import datetime

from ..state import QuizState

# Configure logging
logger = logging.getLogger(__name__)

# === CORE ROUTING FUNCTIONS ===

def route_conversation(state: QuizState) -> str:
    """
    Main routing function that determines the next node based on current state.
    
    This is the primary conditional edge used by LangGraph to route between nodes.
    
    Args:
        state: Current quiz state
        
    Returns:
        String identifier of the next node to execute
    """
    logger.info(f"Routing from phase '{state.current_phase}' with intent '{state.user_intent}'")
    
    try:
        # Handle exit intent from any phase
        if state.user_intent == "exit":
            logger.info("User requested exit - routing to end")
            return "end"
        
        # Handle new quiz request from any phase
        if state.user_intent == "new_quiz":
            logger.info("User requested new quiz - routing to topic validator")
            # Reset state for new quiz will be handled by the node
            return "topic_validator"
        
        # Route based on current phase
        if state.current_phase == "topic_selection":
            return route_from_topic_selection(state)
        
        elif state.current_phase == "topic_validation":
            return route_from_topic_validation(state)
        
        elif state.current_phase == "quiz_active":
            return route_from_quiz_active(state)
        
        elif state.current_phase == "question_answered":
            return route_from_question_answered(state)
        
        elif state.current_phase == "quiz_complete":
            return route_from_quiz_complete(state)
        
        else:
            logger.warning(f"Unknown phase '{state.current_phase}' - routing to query analyzer")
            return "query_analyzer"
    
    except Exception as e:
        logger.error(f"Routing error: {str(e)}")
        # Default fallback routing
        return "query_analyzer"

# === PHASE-SPECIFIC ROUTING FUNCTIONS ===

def route_from_topic_selection(state: QuizState) -> str:
    """Route from topic selection phase"""
    logger.debug(f"Routing from topic_selection with intent: {state.user_intent}")
    
    if state.user_intent == "start_quiz":
        return "topic_validator"
    elif state.user_intent == "clarification":
        return "clarification_handler"
    else:
        # For any unclear input in topic selection, ask for clarification
        return "clarification_handler"

def route_from_topic_validation(state: QuizState) -> str:
    """Route from topic validation phase"""
    logger.debug(f"Routing from topic_validation, validated: {state.topic_validated}")
    
    if state.topic_validated:
        return "quiz_generator"
    else:
        # Topic validation failed
        if state.retry_count >= 3:
            logger.warning("Max retries reached for topic validation")
            return "end"
        else:
            return "clarification_handler"

def route_from_quiz_active(state: QuizState) -> str:
    """Route from quiz active phase"""
    logger.debug(f"Routing from quiz_active with intent: {state.user_intent}")
    
    if state.user_intent == "answer_question":
        return "answer_validator"
    elif state.user_intent == "clarification":
        return "clarification_handler"
    else:
        # If intent is unclear but we have a current question, 
        # assume it's an answer attempt
        if state.current_question and state.user_input.strip():
            logger.info("Unclear intent but treating as answer attempt")
            state.user_intent = "answer_question"  # Override intent
            return "answer_validator"
        else:
            return "clarification_handler"

def route_from_question_answered(state: QuizState) -> str:
    """Route from question answered phase"""
    logger.debug(f"Routing from question_answered with intent: {state.user_intent}")
    
    if state.user_intent == "continue" or state.user_intent == "answer_question":
        return "score_generator"
    elif state.user_intent == "clarification":
        return "clarification_handler"
    else:
        # Default to continuing with score generation
        return "score_generator"

def route_from_quiz_complete(state: QuizState) -> str:
    """Route from quiz complete phase"""
    logger.debug(f"Routing from quiz_complete with intent: {state.user_intent}")
    
    if state.user_intent == "new_quiz" or state.user_intent == "start_quiz":
        return "topic_validator"
    else:
        return "end"

# === SPECIALIZED ROUTING FUNCTIONS ===

def route_after_score_generation(state: QuizState) -> str:
    """Route after score generation based on quiz completion status"""
    logger.debug(f"Routing after score generation, completed: {state.quiz_completed}")
    
    if state.quiz_completed:
        return "quiz_completion_handler"
    else:
        # Quiz continues - generate next question
        return "quiz_generator"

def route_after_clarification(state: QuizState) -> str:
    """Route after providing clarification"""
    logger.debug("Routing after clarification")
    
    # Always return to query analyzer to get fresh user input
    return "query_analyzer"

def route_error_recovery(state: QuizState) -> str:
    """Route for error recovery scenarios"""
    logger.debug(f"Error recovery routing, retry_count: {state.retry_count}")
    
    error_type = classify_error_type(state.last_error)
    
    if error_type == "user_input_error":
        return "clarification_handler"
    elif error_type == "llm_error":
        if state.retry_count < 3:
            # Retry the same operation
            return get_retry_node_for_phase(state.current_phase)
        else:
            return "end"
    elif error_type == "validation_error":
        return "clarification_handler"
    else:
        return "end"

# === CONDITIONAL ROUTING HELPERS ===

def should_end_session(state: QuizState) -> bool:
    """Determine if session should end"""
    conditions = [
        state.user_intent == "exit",
        state.retry_count >= 5,  # Too many errors
        (state.current_phase == "quiz_complete" and 
         state.user_intent not in ["new_quiz", "start_quiz"])
    ]
    
    return any(conditions)

def should_start_new_quiz(state: QuizState) -> bool:
    """Determine if new quiz should start"""
    return state.user_intent in ["new_quiz", "start_quiz"]

def should_continue_quiz(state: QuizState) -> bool:
    """Determine if quiz should continue"""
    return (
        state.quiz_active and 
        not state.quiz_completed and
        state.user_intent in ["continue", "answer_question"]
    )

def get_retry_node_for_phase(phase: str) -> str:
    """Get appropriate node to retry for given phase"""
    retry_mapping = {
        "topic_selection": "query_analyzer",
        "topic_validation": "topic_validator", 
        "quiz_active": "quiz_generator",
        "question_answered": "answer_validator"
    }
    return retry_mapping.get(phase, "query_analyzer")

def classify_error_type(error_message: Optional[str]) -> str:
    """Classify error type for appropriate routing"""
    if not error_message:
        return "unknown"
    
    error_lower = error_message.lower()
    
    if any(keyword in error_lower for keyword in ["input", "understand", "unclear"]):
        return "user_input_error"
    elif any(keyword in error_lower for keyword in ["llm", "api", "network", "timeout"]):
        return "llm_error"
    elif any(keyword in error_lower for keyword in ["validation", "invalid", "format"]):
        return "validation_error"
    else:
        return "unknown"

# === COMPLEX ROUTING SCENARIOS ===

def handle_mid_quiz_topic_change(state: QuizState) -> str:
    """Handle user requesting topic change during active quiz"""
    logger.info("Handling mid-quiz topic change request")
    
    # Store current quiz progress in metadata for potential resume
    if state.total_questions_answered > 0:
        state.quiz_metadata["previous_session"] = {
            "topic": state.topic,
            "questions_answered": state.total_questions_answered,
            "score": state.total_score,
            "abandoned_at": state.current_phase
        }
    
    # Reset quiz state will be handled by topic validator
    return "topic_validator"

def handle_ambiguous_answer_intent(state: QuizState) -> str:
    """Handle cases where it's unclear if input is an answer or command"""
    logger.debug("Handling ambiguous answer intent")
    
    # If we're in quiz_active phase and have a current question,
    # lean towards treating input as an answer
    if (state.current_phase == "quiz_active" and 
        state.current_question and 
        len(state.user_input.strip()) > 0):
        
        # Check if input looks like a command
        command_keywords = ["help", "exit", "quit", "new", "start", "stop"]
        if any(keyword in state.user_input.lower() for keyword in command_keywords):
            return "query_analyzer"  # Re-analyze intent
        else:
            # Treat as answer attempt
            state.user_intent = "answer_question"
            return "answer_validator"
    
    return "clarification_handler"

def handle_infinite_quiz_termination(state: QuizState) -> str:
    """Handle termination logic for infinite quizzes"""
    logger.debug("Handling infinite quiz termination check")
    
    if state.quiz_type == "infinite":
        # Check for natural stopping points
        if state.total_questions_answered >= 50:  # Reasonable upper limit
            logger.info("Infinite quiz hitting reasonable limit")
            state.quiz_completed = True
            return "quiz_completion_handler"
        elif state.user_intent == "continue":
            return "quiz_generator"
        elif state.user_intent in ["exit", "stop", "done"]:
            state.quiz_completed = True
            return "quiz_completion_handler"
        else:
            # Ask user if they want to continue
            return "continuation_check_handler"
    
    return "score_generator"

# === ROUTING VALIDATION ===

def validate_routing_decision(state: QuizState, next_node: str) -> bool:
    """Validate that routing decision is appropriate for current state"""
    logger.debug(f"Validating routing decision: {next_node}")
    
    # Define valid transitions
    valid_transitions = {
        "topic_selection": ["topic_validator", "clarification_handler", "end"],
        "topic_validation": ["quiz_generator", "clarification_handler", "end"],
        "quiz_active": ["answer_validator", "clarification_handler", "quiz_generator", "end"],
        "question_answered": ["score_generator", "clarification_handler", "end"],
        "quiz_complete": ["topic_validator", "end"]
    }
    
    valid_next_nodes = valid_transitions.get(state.current_phase, [])
    
    if next_node not in valid_next_nodes and next_node != "query_analyzer":
        logger.warning(f"Invalid transition from {state.current_phase} to {next_node}")
        return False
    
    # Check node-specific prerequisites
    node_requirements = {
        "topic_validator": lambda s: bool(s.user_input),
        "quiz_generator": lambda s: s.topic_validated and s.topic,
        "answer_validator": lambda s: bool(s.current_answer and s.current_question),
        "score_generator": lambda s: s.answer_is_correct is not None
    }
    
    requirement_check = node_requirements.get(next_node)
    if requirement_check and not requirement_check(state):
        logger.warning(f"Prerequisites not met for node {next_node}")
        return False
    
    return True

# === ROUTING METRICS AND MONITORING ===

class RoutingMetrics:
    """Track routing decisions for monitoring and optimization"""
    
    def __init__(self):
        self.routing_counts: Dict[str, int] = {}
        self.error_routes: Dict[str, int] = {}
        self.phase_transitions: Dict[str, Dict[str, int]] = {}
    
    def record_routing(self, from_phase: str, to_node: str, user_intent: str):
        """Record a routing decision"""
        route_key = f"{from_phase}->{to_node}"
        self.routing_counts[route_key] = self.routing_counts.get(route_key, 0) + 1
        
        if from_phase not in self.phase_transitions:
            self.phase_transitions[from_phase] = {}
        self.phase_transitions[from_phase][to_node] = (
            self.phase_transitions[from_phase].get(to_node, 0) + 1
        )
    
    def record_error_route(self, error_type: str):
        """Record an error-based routing decision"""
        self.error_routes[error_type] = self.error_routes.get(error_type, 0) + 1
    
    def get_routing_stats(self) -> Dict[str, Any]:
        """Get routing statistics"""
        return {
            "total_routes": sum(self.routing_counts.values()),
            "most_common_routes": sorted(
                self.routing_counts.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:10],
            "error_routes": self.error_routes,
            "phase_transitions": self.phase_transitions
        }

# Global metrics instance
routing_metrics = RoutingMetrics()

# === ROUTING DECORATORS ===

def log_routing_decision(func: Callable) -> Callable:
    """Decorator to log routing decisions"""
    def wrapper(state: QuizState) -> str:
        result = func(state)
        logger.info(f"Routing decision: {state.current_phase} -> {result} (intent: {state.user_intent})")
        
        # Record metrics
        routing_metrics.record_routing(state.current_phase, result, state.user_intent or "unknown")
        
        return result
    return wrapper

def validate_routing_result(func: Callable) -> Callable:
    """Decorator to validate routing results"""
    def wrapper(state: QuizState) -> str:
        result = func(state)
        
        if not validate_routing_decision(state, result):
            logger.error(f"Invalid routing decision: {state.current_phase} -> {result}")
            # Fallback to safe routing
            return "query_analyzer"
        
        return result
    return wrapper

# === MAIN ROUTING FUNCTION WITH DECORATORS ===

@log_routing_decision
@validate_routing_result
def main_route_conversation(state: QuizState) -> str:
    """Main routing function with logging and validation"""
    return route_conversation(state)

# === ROUTING TESTING UTILITIES ===

def test_routing_scenarios() -> Dict[str, str]:
    """Test various routing scenarios"""
    from ..state import create_test_state
    
    scenarios = {}
    
    # Test basic topic selection
    state = create_test_state()
    state.current_phase = "topic_selection"
    state.user_intent = "start_quiz"
    scenarios["topic_selection_start"] = route_conversation(state)
    
    # Test quiz active with answer
    state = create_test_state()
    state.current_phase = "quiz_active"
    state.user_intent = "answer_question"
    scenarios["quiz_active_answer"] = route_conversation(state)
    
    # Test quiz completion
    state = create_test_state()
    state.current_phase = "quiz_complete"
    state.user_intent = "new_quiz"
    scenarios["quiz_complete_new"] = route_conversation(state)
    
    # Test exit from any phase
    state = create_test_state()
    state.current_phase = "quiz_active"
    state.user_intent = "exit"
    scenarios["any_phase_exit"] = route_conversation(state)
    
    return scenarios

def simulate_conversation_flow(initial_state: QuizState, max_steps: int = 10) -> List[str]:
    """Simulate conversation flow for testing"""
    steps = []
    state = initial_state
    
    for i in range(max_steps):
        if should_end_session(state):
            steps.append("end")
            break
        
        next_node = route_conversation(state)
        steps.append(next_node)
        
        # Simulate state changes (simplified)
        if next_node == "topic_validator":
            state.current_phase = "topic_validation"
        elif next_node == "quiz_generator":
            state.current_phase = "quiz_active"
        elif next_node == "answer_validator":
            state.current_phase = "question_answered"
        elif next_node == "score_generator":
            if state.quiz_completed:
                state.current_phase = "quiz_complete"
            else:
                state.current_phase = "quiz_active"
    
    return steps

if __name__ == "__main__":
    # Test routing scenarios
    print("Testing routing scenarios:")
    scenarios = test_routing_scenarios()
    for scenario, result in scenarios.items():
        print(f"  {scenario}: {result}")
    
    # Test conversation flow simulation
    from ..state import create_test_state
    test_state = create_test_state()
    test_state.user_intent = "start_quiz"
    
    flow = simulate_conversation_flow(test_state)
    print(f"\nSimulated conversation flow: {' -> '.join(flow)}") 