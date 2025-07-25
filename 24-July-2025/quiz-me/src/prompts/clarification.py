"""Clarification Prompt for the Interactive Quiz Generator

This module contains the prompt template for handling unclear inputs and
requesting clarification from users. This supports various nodes that need
to handle ambiguous user input.

To be implemented in Phase 1 following 03-prompt-templates.md
"""

from typing import Any
import logging

logger = logging.getLogger(__name__)

def format_clarification_prompt(state) -> str:
    """
    Format clarification prompt from current state.
    
    This prompt generates clarification requests for:
    - Ambiguous user inputs that need more context
    - Multiple possible interpretations that need disambiguation
    - Missing information required for proper processing
    - Guidance for users on how to provide better input
    
    Args:
        state: Current QuizState object containing ambiguous input and context
        
    Returns:
        Formatted prompt string for LLM clarification generation
        
    Full implementation will include:
    - Context-aware clarification strategies
    - User-friendly guidance and examples
    - Progressive clarification techniques
    - Fallback handling for persistent ambiguity
    
    Placeholder - see 03-prompt-templates.md for complete implementation
    """
    logger.info("Formatting clarification prompt - placeholder implementation")
    
    # TODO: Implement complete clarification prompt template
    # TODO: Add context-aware clarification strategies
    # TODO: Add user-friendly guidance and examples
    # TODO: Add progressive clarification techniques
    # TODO: Add fallback handling for persistent ambiguity
    
    return f"""Placeholder clarification prompt for input: {getattr(state, 'user_input', 'No input')}
    
This will be replaced with a comprehensive clarification prompt that includes:
- Context-aware clarification strategies
- User-friendly guidance and examples
- Progressive clarification techniques
- Helpful suggestions and alternatives
    
Implementation coming in Phase 1.""" 