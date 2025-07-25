"""Processing nodes for the Interactive Quiz Generator workflow

This package contains the five core processing nodes that handle the quiz workflow logic.
Each node is implemented in a separate module for better organization and maintainability.

Nodes:
- query_analyzer: Analyzes user input and determines intent
- topic_validator: Validates topic appropriateness and feasibility  
- quiz_generator: Generates diverse, engaging quiz questions
- answer_validator: Evaluates user responses with intelligent scoring
- score_generator: Calculates scores and tracks progress

Each node follows a consistent pattern:
- Takes QuizState and optional LLM client as parameters
- Returns updated QuizState with results
- Includes comprehensive error handling
- Has prerequisite validation functions
"""

from .query_analyzer import (
    query_analyzer, 
    validate_query_analyzer_prerequisites,
    QueryAnalyzerError
)
from .topic_validator import (
    topic_validator, 
    validate_topic_validator_prerequisites,
    TopicValidatorError
)
from .quiz_generator import (
    quiz_generator, 
    validate_quiz_generator_prerequisites,
    determine_question_type,
    QuizGeneratorError
)
from .answer_validator import (
    answer_validator, 
    validate_answer_validator_prerequisites,
    validate_multiple_choice_answer,
    validate_true_false_answer,
    AnswerValidatorError
)
from .score_generator import (
    score_generator, 
    validate_score_generator_prerequisites,
    get_difficulty_multiplier,
    get_question_type_bonus,
    calculate_performance_trend,
    ScoreGeneratorError
)
from .query_analyzer import (
    create_llm_client,
    safe_llm_call,
    LLMCallError
)

# Node execution functions
NODE_FUNCTIONS = {
    "query_analyzer": query_analyzer,
    "topic_validator": topic_validator,
    "quiz_generator": quiz_generator,
    "answer_validator": answer_validator,  
    "score_generator": score_generator
}

# Node prerequisite validators
NODE_VALIDATORS = {
    "query_analyzer": validate_query_analyzer_prerequisites,
    "topic_validator": validate_topic_validator_prerequisites,
    "quiz_generator": validate_quiz_generator_prerequisites,
    "answer_validator": validate_answer_validator_prerequisites,
    "score_generator": validate_score_generator_prerequisites
}

# Node exceptions
NODE_EXCEPTIONS = {
    "query_analyzer": QueryAnalyzerError,
    "topic_validator": TopicValidatorError,
    "quiz_generator": QuizGeneratorError,
    "answer_validator": AnswerValidatorError,
    "score_generator": ScoreGeneratorError
}

def validate_node_prerequisites(state, node_name: str) -> list[str]:
    """Validate that state meets prerequisites for specified node"""
    if node_name not in NODE_VALIDATORS:
        return [f"Unknown node: {node_name}"]
    
    validator = NODE_VALIDATORS[node_name]
    return validator(state)

def execute_node(state, node_name: str, llm=None):
    """Execute specified node with state and optional LLM client"""
    if node_name not in NODE_FUNCTIONS:
        raise ValueError(f"Unknown node: {node_name}")
    
    # Validate prerequisites first
    errors = validate_node_prerequisites(state, node_name)
    if errors:
        state.last_error = f"Node prerequisites failed: {'; '.join(errors)}"
        return state
    
    # Execute node
    node_function = NODE_FUNCTIONS[node_name]
    return node_function(state, llm)

__all__ = [
    # Core node functions
    "query_analyzer",
    "topic_validator", 
    "quiz_generator",
    "answer_validator",
    "score_generator",
    
    # Prerequisite validators
    "validate_query_analyzer_prerequisites",
    "validate_topic_validator_prerequisites", 
    "validate_quiz_generator_prerequisites",
    "validate_answer_validator_prerequisites",
    "validate_score_generator_prerequisites",
    
    # Helper functions
    "determine_question_type",
    "validate_multiple_choice_answer",
    "validate_true_false_answer", 
    "get_difficulty_multiplier",
    "get_question_type_bonus",
    "calculate_performance_trend",
    
    # Node exceptions
    "QueryAnalyzerError",
    "TopicValidatorError",
    "QuizGeneratorError", 
    "AnswerValidatorError",
    "ScoreGeneratorError",
    
    # LLM utilities
    "create_llm_client",
    "safe_llm_call", 
    "LLMCallError",
    
    # Utility functions
    "NODE_FUNCTIONS",
    "NODE_VALIDATORS",
    "NODE_EXCEPTIONS",
    "validate_node_prerequisites",
    "execute_node"
] 