"""Query Analyzer Router for the Interactive Quiz Generator

This module implements routing logic after query analysis, handling intent-based
routing decisions and ambiguous intent resolution.
"""

from typing import Dict, Optional, List
import logging

from ..state import QuizState

logger = logging.getLogger(__name__)

def route_after_query_analysis(state: QuizState) -> str:
    """
    Route after query analysis based on classified intent and current phase.
    
    Args:
        state: Current quiz state with analyzed user intent
        
    Returns:
        Next node identifier based on intent and context
    """
    logger.info(f"Routing after query analysis: intent='{state.user_intent}', phase='{state.current_phase}'")
    
    try:
        # Handle clear intents first
        if state.user_intent == "exit":
            return "end"
        
        if state.user_intent == "new_quiz":
            return handle_new_quiz_request(state)
        
        if state.user_intent == "start_quiz":
            return handle_start_quiz_request(state)
        
        if state.user_intent == "answer_question":
            return handle_answer_submission(state)
        
        if state.user_intent == "continue":
            return handle_continue_request(state)
        
        if state.user_intent == "clarification":
            return "clarification_handler"
        
        # Handle ambiguous or unclear intents
        return resolve_ambiguous_intent(state)
        
    except Exception as e:
        logger.error(f"Query analyzer routing error: {str(e)}")
        return "clarification_handler"

def handle_intent_routing(state: QuizState) -> str:
    """
    Handle routing based on specific user intents with context awareness.
    
    Args:
        state: Current quiz state
        
    Returns:
        Next node based on intent and current context
    """
    intent = state.user_intent
    phase = state.current_phase
    
    logger.debug(f"Handling intent routing: {intent} in phase {phase}")
    
    # Intent-specific routing logic
    intent_routing = {
        "start_quiz": lambda s: "topic_validator" if not s.quiz_active else handle_active_quiz_new_request(s),
        "answer_question": lambda s: "answer_validator" if s.current_question else "clarification_handler",
        "continue": lambda s: handle_continue_based_on_phase(s),
        "change_topic": lambda s: handle_topic_change_request(s),
        "help": lambda s: "help_handler",
        "status": lambda s: "status_handler"
    }
    
    handler = intent_routing.get(intent)
    if handler:
        return handler(state)
    
    # Default to clarification for unknown intents
    logger.warning(f"Unknown intent '{intent}' - requesting clarification")
    return "clarification_handler"

def resolve_ambiguous_intent(state: QuizState) -> str:
    """
    Resolve ambiguous or unclear user intents based on context.
    
    Args:
        state: Current quiz state
        
    Returns:
        Best guess at next node based on context clues
    """
    logger.debug("Resolving ambiguous intent based on context")
    
    # Analyze context clues
    user_input = state.user_input.lower().strip()
    
    # If we're in quiz_active phase and have a question, likely an answer
    if (state.current_phase == "quiz_active" and 
        state.current_question and 
        user_input):
        
        # Check for command-like words
        command_words = ["help", "exit", "quit", "new", "start", "stop", "change"]
        if any(word in user_input for word in command_words):
            logger.info("Ambiguous input contains command words - re-analyzing")
            return "query_analyzer"  # Re-analyze with more context
        
        # Likely an answer attempt
        logger.info("Ambiguous input in quiz context - treating as answer")
        state.user_intent = "answer_question"
        state.current_answer = state.user_input  # Store as answer
        return "answer_validator"
    
    # If we're not in an active quiz, likely wants to start
    if not state.quiz_active and user_input:
        # Check if input looks like a topic
        if len(user_input.split()) <= 5 and not any(char in user_input for char in "?!"):
            logger.info("Ambiguous input looks like topic - treating as start quiz")
            state.user_intent = "start_quiz"
            return "topic_validator"
    
    # Default to asking for clarification
    return "clarification_handler"

# === INTENT-SPECIFIC HANDLERS ===

def handle_new_quiz_request(state: QuizState) -> str:
    """Handle new quiz request regardless of current state"""
    logger.info("Handling new quiz request")
    
    # Store current quiz data if there was one in progress
    if state.quiz_active and state.total_questions_answered > 0:
        state.quiz_metadata["interrupted_session"] = {
            "topic": state.topic,
            "questions_answered": state.total_questions_answered,
            "score": state.total_score,
            "interrupted_at": state.current_phase
        }
    
    return "topic_validator"

def handle_start_quiz_request(state: QuizState) -> str:
    """Handle start quiz request with context awareness"""
    logger.debug("Handling start quiz request")
    
    # If already in active quiz, clarify intent
    if state.quiz_active and not state.quiz_completed:
        logger.info("Quiz already active - need clarification")
        return "clarification_handler"
    
    return "topic_validator"

def handle_answer_submission(state: QuizState) -> str:
    """Handle answer submission with validation"""
    logger.debug("Handling answer submission")
    
    # Validate we're in the right context for an answer
    if not state.current_question:
        logger.warning("Answer submitted but no current question")
        return "clarification_handler"
    
    if not state.user_input.strip():
        logger.warning("Empty answer submitted")
        return "clarification_handler"
    
    # Store answer and validate
    state.current_answer = state.user_input
    return "answer_validator"

def handle_continue_request(state: QuizState) -> str:
    """Handle continue request based on current phase"""
    logger.debug("Handling continue request")
    
    return handle_continue_based_on_phase(state)

def handle_continue_based_on_phase(state: QuizState) -> str:
    """Route continue request based on current phase"""
    phase = state.current_phase
    
    if phase == "question_answered":
        return "score_generator"
    elif phase == "quiz_active":
        # User wants to continue but we need a new question
        return "quiz_generator"
    elif phase == "quiz_complete":
        # Continue means new quiz
        return "topic_validator"
    elif phase == "topic_selection":
        # Continue with topic selection
        return "topic_validator"
    else:
        # Unclear context - ask for clarification
        return "clarification_handler"

def handle_active_quiz_new_request(state: QuizState) -> str:
    """Handle new quiz request while quiz is active"""
    logger.info("New quiz requested while quiz is active")
    
    # This is ambiguous - user might mean:
    # 1. Start completely new quiz (abandon current)
    # 2. Continue current quiz
    # 3. Change topic of current quiz
    
    return "clarification_handler"

def handle_topic_change_request(state: QuizState) -> str:
    """Handle request to change topic"""
    logger.info("Handling topic change request")
    
    # Store current progress if quiz is active
    if state.quiz_active and state.total_questions_answered > 0:
        state.quiz_metadata["topic_change_session"] = {
            "previous_topic": state.topic,
            "questions_answered": state.total_questions_answered,
            "score": state.total_score
        }
    
    return "topic_validator"

# === CONTEXT ANALYSIS HELPERS ===

def analyze_input_context(user_input: str, state: QuizState) -> Dict[str, any]:
    """
    Analyze user input for context clues to help with routing.
    
    Args:
        user_input: User's input text
        state: Current quiz state
        
    Returns:
        Dictionary with context analysis results
    """
    input_lower = user_input.lower().strip()
    
    context = {
        "likely_answer": False,
        "likely_command": False,
        "likely_topic": False,
        "confidence": 0.0,
        "keywords": []
    }
    
    # Check for command indicators
    command_indicators = ["help", "exit", "quit", "new", "start", "stop", "change", "status"]
    found_commands = [word for word in command_indicators if word in input_lower]
    if found_commands:
        context["likely_command"] = True
        context["keywords"].extend(found_commands)
        context["confidence"] += 0.3
    
    # Check for answer indicators (in quiz context)
    if state.current_question and state.current_phase == "quiz_active":
        # Short responses are often answers
        if 1 <= len(input_lower.split()) <= 10:
            context["likely_answer"] = True
            context["confidence"] += 0.4
        
        # Multiple choice indicators
        if input_lower in ['a', 'b', 'c', 'd'] or input_lower in ['1', '2', '3', '4']:
            context["likely_answer"] = True
            context["confidence"] += 0.5
        
        # True/false indicators
        true_false_words = ["true", "false", "yes", "no", "correct", "incorrect"]
        if any(word in input_lower for word in true_false_words):
            context["likely_answer"] = True
            context["confidence"] += 0.4
    
    # Check for topic indicators
    if not state.quiz_active or state.current_phase == "topic_selection":
        # Topics are usually short noun phrases
        words = input_lower.split()
        if 1 <= len(words) <= 5 and not any(char in input_lower for char in "?!"):
            context["likely_topic"] = True
            context["confidence"] += 0.3
    
    return context

def get_routing_suggestions(state: QuizState) -> List[str]:
    """
    Get routing suggestions based on current state.
    
    Args:
        state: Current quiz state
        
    Returns:
        List of suggested next nodes in order of preference
    """
    suggestions = []
    
    # Base suggestions on current phase
    if state.current_phase == "topic_selection":
        suggestions = ["topic_validator", "clarification_handler"]
    
    elif state.current_phase == "quiz_active":
        if state.current_question:
            suggestions = ["answer_validator", "clarification_handler", "quiz_generator"]
        else:
            suggestions = ["quiz_generator", "clarification_handler"]
    
    elif state.current_phase == "question_answered":
        suggestions = ["score_generator", "clarification_handler"]
    
    elif state.current_phase == "quiz_complete":
        suggestions = ["topic_validator", "end", "clarification_handler"]
    
    else:
        suggestions = ["query_analyzer", "clarification_handler"]
    
    # Always include fallback options
    if "clarification_handler" not in suggestions:
        suggestions.append("clarification_handler")
    
    if "query_analyzer" not in suggestions:
        suggestions.append("query_analyzer")
    
    return suggestions

# === ROUTING VALIDATION ===

def validate_query_routing(state: QuizState, next_node: str) -> bool:
    """
    Validate that routing decision makes sense after query analysis.
    
    Args:
        state: Current quiz state
        next_node: Proposed next node
        
    Returns:
        True if routing is valid, False otherwise
    """
    # Check if node makes sense for current intent
    intent_compatible_nodes = {
        "start_quiz": ["topic_validator", "clarification_handler"],
        "answer_question": ["answer_validator", "clarification_handler"],
        "continue": ["score_generator", "quiz_generator", "topic_validator"],
        "exit": ["end"],
        "new_quiz": ["topic_validator"],
        "clarification": ["clarification_handler"]
    }
    
    compatible_nodes = intent_compatible_nodes.get(state.user_intent, [])
    if compatible_nodes and next_node not in compatible_nodes:
        logger.warning(f"Node '{next_node}' not compatible with intent '{state.user_intent}'")
        return False
    
    # Check phase compatibility
    phase_compatible_nodes = {
        "topic_selection": ["topic_validator", "clarification_handler", "end"],
        "quiz_active": ["answer_validator", "quiz_generator", "clarification_handler", "end"],
        "question_answered": ["score_generator", "clarification_handler", "end"],
        "quiz_complete": ["topic_validator", "end", "clarification_handler"]
    }
    
    compatible_nodes = phase_compatible_nodes.get(state.current_phase, [])
    if compatible_nodes and next_node not in compatible_nodes:
        logger.warning(f"Node '{next_node}' not compatible with phase '{state.current_phase}'")
        return False
    
    return True

if __name__ == "__main__":
    # Test query analyzer routing
    from ..state import create_test_state
    
    # Test different scenarios
    scenarios = [
        ("start_quiz", "topic_selection"),
        ("answer_question", "quiz_active"),
        ("continue", "question_answered"),
        ("exit", "quiz_active")
    ]
    
    for intent, phase in scenarios:
        state = create_test_state()
        state.user_intent = intent
        state.current_phase = phase
        
        result = route_after_query_analysis(state)
        print(f"Intent: {intent}, Phase: {phase} -> {result}") 