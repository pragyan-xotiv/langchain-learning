"""LLM prompt templates and management system"""

from typing import Dict, List, Optional, Any
import json
import re
from .prompt_types import PromptType, PromptTemplate
from .prompt_manager import PromptManager, prompt_manager
from .formatters import (
    # Helper functions
    format_conversation_history, 
    format_previous_questions, 
    format_question_type_breakdown,
    
    # State-based formatting functions
    format_intent_classification_prompt, 
    format_topic_extraction_prompt,
    format_topic_validation_prompt, 
    format_question_generation_prompt,
    format_answer_validation_prompt, 
    format_clarification_prompt,
    format_summary_generation_prompt
)
from ..state import QuizState

# === PROMPT VALIDATION ===

def validate_prompt_response(response: str, expected_format: str = "json") -> bool:
    """Validate LLM response format"""
    if expected_format == "json":
        try:
            json.loads(response)
            return True
        except (json.JSONDecodeError, TypeError):
            return False
    
    # For text responses, just check it's not empty
    return bool(response.strip())

def extract_json_from_response(response: str) -> Dict[str, Any]:
    """Extract JSON from LLM response, handling common formatting issues"""
    response = response.strip()
    
    # Try direct parsing first
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        pass
    
    # Try to find JSON within the response
    json_match = re.search(r'\{.*\}', response, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
    
    # Return error structure
    return {
        "error": "Failed to parse JSON response",
        "raw_response": response
    }

# === TESTING UTILITIES ===

def create_test_prompts() -> Dict[str, str]:
    """Create test prompts for validation"""
    from ..state import create_test_state
    
    test_state = create_test_state()
    test_state.user_input = "I want a quiz about Python programming"
    test_state.current_question = "What is a list in Python?"
    test_state.current_answer = "A collection of items"
    test_state.correct_answer = "An ordered collection of items"
    
    return {
        "intent_classification": format_intent_classification_prompt(test_state),
        "topic_extraction": format_topic_extraction_prompt("I want to learn about machine learning"),
        "topic_validation": format_topic_validation_prompt("Machine Learning"),
        "question_generation": format_question_generation_prompt(test_state),
        "answer_validation": format_answer_validation_prompt(test_state),
        "clarification": format_clarification_prompt(test_state, "unclear_intent"),
        "summary": format_summary_generation_prompt(test_state)
    }

__all__ = [
    # Core classes
    "PromptType", "PromptTemplate", "PromptManager", "prompt_manager",
    
    # Formatting functions
    "format_intent_classification_prompt", "format_topic_extraction_prompt",
    "format_topic_validation_prompt", "format_question_generation_prompt",
    "format_answer_validation_prompt", "format_clarification_prompt",
    "format_summary_generation_prompt",
    
    # Helper functions
    "format_conversation_history", "format_previous_questions", 
    "format_question_type_breakdown",
    
    # Validation functions
    "validate_prompt_response", "extract_json_from_response",
    
    # Testing utilities
    "create_test_prompts"
] 