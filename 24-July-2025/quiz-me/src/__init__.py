"""Interactive Quiz Generator - Core Package

This package contains the core components of the Interactive Quiz Generator,
organized into modular subpackages for better maintainability and development.

Subpackages:
- nodes: Processing nodes that handle quiz workflow logic
- edges: Conditional routing logic for state transitions
- prompts: LLM prompt templates and management system
- state: Centralized state management with Pydantic models

Other modules:
- workflow: LangGraph workflow assembly and orchestration
- utils: Helper functions and configuration management
"""

# Import core components from organized subpackages
from .nodes import (
    query_analyzer, topic_validator, quiz_generator, 
    answer_validator, score_generator
)

from .edges import (
    route_conversation, main_route_conversation,
    route_after_query_analysis, route_after_topic_validation,
    route_after_question_generation, route_after_answer_validation,
    route_after_scoring, should_end_session, should_start_new_quiz,
    should_continue_quiz, classify_error_type, validate_routing_decision
)

from .prompts import (
    format_intent_classification_prompt, format_topic_extraction_prompt,
    format_topic_validation_prompt, format_question_generation_prompt,
    format_answer_validation_prompt, format_clarification_prompt,
    format_summary_generation_prompt, PromptType, PromptTemplate, PromptManager,
    validate_prompt_response, extract_json_from_response
)

from .state import (
    QuizState, validate_state_consistency, validate_state_transition,
    serialize_state, deserialize_state,
    create_initial_state, create_test_state
)

# Import workflow and utilities
from .workflow import QuizWorkflow, create_quiz_workflow
from .utils import Config, validate_environment_setup

__all__ = [
    # Node functions
    "query_analyzer", "topic_validator", "quiz_generator",
    "answer_validator", "score_generator",
    
    # Edge functions
    "route_conversation", "main_route_conversation",
    "route_after_query_analysis", "route_after_topic_validation", 
    "route_after_question_generation", "route_after_answer_validation",
    "route_after_scoring", "should_end_session", "should_start_new_quiz",
    "should_continue_quiz", "classify_error_type", "validate_routing_decision",
    
    # Prompt functions and classes
    "format_intent_classification_prompt", "format_topic_extraction_prompt",
    "format_topic_validation_prompt", "format_question_generation_prompt", 
    "format_answer_validation_prompt", "format_clarification_prompt",
    "format_summary_generation_prompt", "PromptType", "PromptTemplate", "PromptManager",
    "validate_prompt_response", "extract_json_from_response",
    
    # State management
    "QuizState", "validate_state_consistency", "validate_state_transition",
    "serialize_state", "deserialize_state",
    "create_initial_state", "create_test_state",
    
    # Workflow and utilities
    "QuizWorkflow", "create_quiz_workflow",
    "Config", "validate_environment_setup"
] 