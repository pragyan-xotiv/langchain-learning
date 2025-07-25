"""LLM prompt templates and management system for the Interactive Quiz Generator

This package provides the complete prompt template system for the Interactive Quiz Generator.
All LLM interactions use carefully crafted prompts designed for reliability, consistency,
and optimal performance.

Prompt Templates:
- intent_classification: Analyzes user input to determine intent and context  
- topic_extraction: Extracts and validates quiz topics from user input
- topic_validation: Validates topic appropriateness and feasibility
- question_generation: Generates diverse quiz questions for validated topics
- answer_validation: Evaluates user responses and provides feedback
- clarification: Handles unclear inputs and requests clarification
- summary_generation: Creates performance summaries and final reports

Core Classes:
- PromptType: Enumeration of all prompt types in the system
- PromptTemplate: Container for prompt template and metadata
- PromptManager: Template management and formatting utilities
"""

from .intent_classification import format_intent_classification_prompt
from .topic_extraction import format_topic_extraction_prompt
from .topic_validation import format_topic_validation_prompt
from .question_generation import format_question_generation_prompt
from .answer_validation import format_answer_validation_prompt
from .clarification import format_clarification_prompt
from .summary_generation import format_summary_generation_prompt

# Import shared types and utilities
from .prompt_types import PromptType, PromptTemplate
from .prompt_manager import PromptManager

__all__ = [
    # Prompt formatting functions
    "format_intent_classification_prompt",
    "format_topic_extraction_prompt",
    "format_topic_validation_prompt",
    "format_question_generation_prompt",
    "format_answer_validation_prompt",
    "format_clarification_prompt",
    "format_summary_generation_prompt",
    
    # Core classes and types
    "PromptType",
    "PromptTemplate", 
    "PromptManager"
] 