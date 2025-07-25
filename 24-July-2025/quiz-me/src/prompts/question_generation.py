"""Question Generation Prompt for the Interactive Quiz Generator

This module contains the prompt template for generating diverse quiz questions
based on validated topics. This is used by the Quiz Generator node.

To be implemented in Phase 1 following 03-prompt-templates.md
"""

from typing import Any
import logging

logger = logging.getLogger(__name__)

def format_question_generation_prompt(state) -> str:
    """
    Format question generation prompt from current state.
    
    This prompt generates quiz questions including:
    - Multiple choice questions with realistic distractors
    - Open-ended questions requiring detailed responses
    - True/false questions with clear explanations
    - Mixed difficulty levels appropriate for the topic
    
    Args:
        state: Current QuizState object containing validated topic and parameters
        
    Returns:
        Formatted prompt string for LLM question generation
        
    Full implementation will include:
    - Question type templates and generation patterns
    - Difficulty level management and progression
    - Quality criteria and validation guidelines
    - Structured output format for questions and answers
    
    Placeholder - see 03-prompt-templates.md for complete implementation
    """
    logger.info("Formatting question generation prompt - placeholder implementation")
    
    # TODO: Implement complete question generation prompt template
    # TODO: Add question type templates (MC, open-ended, T/F)
    # TODO: Add difficulty level management and progression
    # TODO: Add quality criteria and validation guidelines
    # TODO: Add structured output format for questions and answers
    
    return f"""Placeholder question generation prompt for topic: {getattr(state, 'validated_topic', 'No topic')}
    
This will be replaced with a comprehensive question generation prompt that includes:
- Multiple question type templates
- Difficulty level management
- Quality assurance criteria
- Structured JSON output requirements
    
Implementation coming in Phase 1.""" 