"""Intent Classification Prompt for the Interactive Quiz Generator

This module contains the prompt template for analyzing user input to determine
intent and context. This is used by the Query Analyzer node.

To be implemented in Phase 1 following 03-prompt-templates.md
"""

from typing import Any
import logging

logger = logging.getLogger(__name__)

def format_intent_classification_prompt(state) -> str:
    """
    Format intent classification prompt from current state.
    
    This prompt analyzes user input to determine:
    - Primary user intent (start_quiz, answer_question, change_topic, exit, etc.)
    - Extracted entities and context information
    - Confidence level for the intent classification
    - Any ambiguities that need clarification
    
    Args:
        state: Current QuizState object containing user input and context
        
    Returns:
        Formatted prompt string for LLM intent classification
        
    Full implementation will include:
    - Comprehensive intent classification categories
    - Context-aware prompt formatting based on current phase
    - Examples and few-shot learning patterns
    - JSON output schema for structured responses
    
    Placeholder - see 03-prompt-templates.md for complete implementation
    """
    logger.info("Formatting intent classification prompt - placeholder implementation")
    
    # TODO: Implement complete intent classification prompt template
    # TODO: Add comprehensive intent categories and examples
    # TODO: Add context-aware formatting based on current phase
    # TODO: Add JSON output schema specification
    # TODO: Add few-shot learning examples for better accuracy
    
    return f"""Placeholder intent classification prompt for input: {getattr(state, 'user_input', 'No input')}
    
This will be replaced with a comprehensive intent classification prompt that includes:
- Clear intent categories and definitions
- Context from current quiz phase
- Examples for few-shot learning
- Structured JSON output requirements
    
Implementation coming in Phase 1.""" 