"""Edge logic and routing for the Interactive Quiz Generator workflow

This package contains the conditional routing logic that determines how the application
flows between nodes. Edge logic handles complex decision-making based on current state,
user intent, and system conditions.

Modules:
- conversation_router: Main conversation flow routing logic
- query_analyzer_router: Routes after query analysis
- topic_validator_router: Routes after topic validation  
- quiz_generator_router: Routes after question generation
- answer_validator_router: Routes after answer validation
- score_generator_router: Routes after score generation

Each router follows a consistent pattern:
- Takes QuizState as parameter
- Returns string identifier of next node
- Includes comprehensive logging and validation
- Handles error scenarios gracefully
"""

from .conversation_router import (
    route_conversation,
    main_route_conversation,
    route_from_topic_selection,
    route_from_topic_validation,
    route_from_quiz_active,
    route_from_question_answered,
    route_from_quiz_complete,
    route_after_score_generation,
    route_after_clarification,
    route_error_recovery,
    handle_mid_quiz_topic_change,
    handle_ambiguous_answer_intent,
    handle_infinite_quiz_termination
)
from .query_analyzer_router import (
    route_after_query_analysis,
    handle_intent_routing,
    resolve_ambiguous_intent
)
from .topic_validator_router import (
    route_after_topic_validation,
    handle_validation_failure,
    suggest_alternative_topics
)
from .quiz_generator_router import (
    route_after_question_generation,
    handle_generation_failure,
    determine_next_question_flow
)
from .answer_validator_router import (
    route_after_answer_validation,
    handle_validation_errors,
    route_based_on_correctness
)
from .score_generator_router import (
    route_after_scoring,
    handle_quiz_completion,
    determine_continuation_flow
)

# Routing condition functions
from .conversation_router import (
    should_end_session,
    should_start_new_quiz,
    should_continue_quiz,
    get_retry_node_for_phase,
    classify_error_type,
    validate_routing_decision
)

# Routing utilities and metrics
from .conversation_router import (
    RoutingMetrics,
    routing_metrics,
    log_routing_decision,
    validate_routing_result,
    test_routing_scenarios,
    simulate_conversation_flow
)

# Router execution functions
ROUTER_FUNCTIONS = {
    "main": route_conversation,
    "query_analyzer": route_after_query_analysis,
    "topic_validator": route_after_topic_validation,
    "quiz_generator": route_after_question_generation,
    "answer_validator": route_after_answer_validation,
    "score_generator": route_after_scoring
}

def execute_router(state, router_name: str = "main") -> str:
    """Execute specified router with state"""
    if router_name not in ROUTER_FUNCTIONS:
        raise ValueError(f"Unknown router: {router_name}")
    
    router_function = ROUTER_FUNCTIONS[router_name]
    return router_function(state)

__all__ = [
    # Main routing functions
    "route_conversation",
    "main_route_conversation",
    
    # Phase-specific routing
    "route_from_topic_selection",
    "route_from_topic_validation", 
    "route_from_quiz_active",
    "route_from_question_answered",
    "route_from_quiz_complete",
    
    # Specialized routing
    "route_after_score_generation",
    "route_after_clarification",
    "route_error_recovery",
    "handle_mid_quiz_topic_change",
    "handle_ambiguous_answer_intent",
    "handle_infinite_quiz_termination",
    
    # Node-specific routers
    "route_after_query_analysis",
    "route_after_topic_validation",
    "route_after_question_generation", 
    "route_after_answer_validation",
    "route_after_scoring",
    
    # Routing conditions
    "should_end_session",
    "should_start_new_quiz",
    "should_continue_quiz",
    "get_retry_node_for_phase",
    "classify_error_type",
    "validate_routing_decision",
    
    # Routing utilities
    "RoutingMetrics",
    "routing_metrics",
    "log_routing_decision",
    "validate_routing_result",
    "test_routing_scenarios",
    "simulate_conversation_flow",
    
    # Utility functions
    "ROUTER_FUNCTIONS",
    "execute_router"
] 