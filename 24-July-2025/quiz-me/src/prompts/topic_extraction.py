"""Topic Extraction Prompt for the Interactive Quiz Generator

This module contains the prompt template for extracting and validating quiz topics
from user input. This supports the Topic Validator node.

To be implemented in Phase 1 following 03-prompt-templates.md
"""

from typing import Any
import logging

logger = logging.getLogger(__name__)

def format_topic_extraction_prompt(state) -> str:
    """
    Format topic extraction prompt from current state.
    
    This prompt extracts quiz topics from user input including:
    - Primary topic identification and extraction
    - Topic scope and boundary definition
    - Subject area and difficulty level assessment
    - Related subtopics and focus areas
    
    Args:
        state: Current QuizState object containing user input and context
        
    Returns:
        Formatted prompt string for LLM topic extraction
        
    Full implementation will include:
    - Topic extraction patterns and techniques
    - Scope definition and boundary setting
    - Subject area classification
    - JSON output schema for structured topic data
    
    Placeholder - see 03-prompt-templates.md for complete implementation
    """
    logger.info("Formatting topic extraction prompt - placeholder implementation")
    
    # TODO: Implement complete topic extraction prompt template
    # TODO: Add topic identification and extraction patterns
    # TODO: Add scope definition and boundary setting logic
    # TODO: Add subject area classification system
    # TODO: Add JSON output schema for structured data
    
    return f"""Placeholder topic extraction prompt for input: {getattr(state, 'user_input', 'No input')}
    
This will be replaced with a comprehensive topic extraction prompt that includes:
- Topic identification and extraction techniques
- Scope and boundary definition methods
- Subject area classification
- Structured JSON output requirements
    
Implementation coming in Phase 1.""" 