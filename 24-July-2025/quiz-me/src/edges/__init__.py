"""Edge logic and routing for the Interactive Quiz Generator workflow

This package contains conditional routing logic that determines which node to execute next
based on the current state. These edges enable dynamic conversation flow and proper error handling.

Routing Functions:
- conversation_router: Primary routing function for the main conversation flow
- query_analyzer_router: Routes flow after query analysis based on intent and phase
- topic_validator_router: Routes flow after topic validation based on results
- quiz_generator_router: Routes flow after question generation
- answer_validator_router: Routes flow after answer validation
- score_generator_router: Routes flow after score generation based on completion status
"""

from .conversation_router import route_conversation
from .query_analyzer_router import route_from_query_analyzer
from .topic_validator_router import route_from_topic_validator
from .quiz_generator_router import route_from_quiz_generator
from .answer_validator_router import route_from_answer_validator
from .score_generator_router import route_from_score_generator

__all__ = [
    "route_conversation",
    "route_from_query_analyzer",
    "route_from_topic_validator", 
    "route_from_quiz_generator",
    "route_from_answer_validator",
    "route_from_score_generator"
] 