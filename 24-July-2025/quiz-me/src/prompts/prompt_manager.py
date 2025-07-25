"""Template management system for LLM prompts"""

from typing import Dict, List, Optional, Any, Union
import json
from .prompt_types import PromptType, PromptTemplate
from .templates import (
    INTENT_CLASSIFICATION_PROMPT, TOPIC_EXTRACTION_PROMPT,
    TOPIC_VALIDATION_PROMPT, QUESTION_GENERATION_PROMPT,
    ANSWER_VALIDATION_PROMPT, CLARIFICATION_PROMPT,
    QUIZ_SUMMARY_PROMPT
)

class PromptManager:
    """Manages all prompt templates and formatting"""
    
    def __init__(self):
        self.templates: Dict[PromptType, PromptTemplate] = {}
        self._load_templates()
    
    def _load_templates(self):
        """Load all prompt templates"""
        # Intent Classification
        self.templates[PromptType.INTENT_CLASSIFICATION] = PromptTemplate(
            name="intent_classification",
            template=INTENT_CLASSIFICATION_PROMPT,
            required_vars=["current_phase", "quiz_active", "topic", "conversation_history", "user_input"],
            description="Classify user intent based on input and context",
            expected_output="json"
        )
        
        # Topic Extraction
        self.templates[PromptType.TOPIC_EXTRACTION] = PromptTemplate(
            name="topic_extraction", 
            template=TOPIC_EXTRACTION_PROMPT,
            required_vars=["user_input"],
            description="Extract quiz topic from user input",
            expected_output="json"
        )
        
        # Topic Validation
        self.templates[PromptType.TOPIC_VALIDATION] = PromptTemplate(
            name="topic_validation",
            template=TOPIC_VALIDATION_PROMPT,
            required_vars=["topic"],
            description="Validate topic appropriateness and feasibility",
            expected_output="json"
        )
        
        # Question Generation
        self.templates[PromptType.QUESTION_GENERATION] = PromptTemplate(
            name="question_generation",
            template=QUESTION_GENERATION_PROMPT,
            required_vars=["topic", "question_number", "difficulty_level", "previous_questions", "question_type"],
            description="Generate quiz questions for specified topic",
            expected_output="json"
        )
        
        # Answer Validation
        self.templates[PromptType.ANSWER_VALIDATION] = PromptTemplate(
            name="answer_validation",
            template=ANSWER_VALIDATION_PROMPT,
            required_vars=["question", "correct_answer", "user_answer"],
            optional_vars=["question_type", "options"],
            description="Validate and score user answers",
            expected_output="json"
        )
        
        # Clarification
        self.templates[PromptType.CLARIFICATION] = PromptTemplate(
            name="clarification",
            template=CLARIFICATION_PROMPT,
            required_vars=["current_phase", "user_input", "issue_type"],
            optional_vars=["current_question"],
            description="Generate helpful clarification responses",
            expected_output="text"
        )
        
        # Summary Generation
        self.templates[PromptType.SUMMARY_GENERATION] = PromptTemplate(
            name="summary_generation",
            template=QUIZ_SUMMARY_PROMPT,
            required_vars=["topic", "total_questions", "correct_answers", "final_score", "accuracy"],
            optional_vars=["question_type_breakdown", "strong_areas", "weak_areas"],
            description="Generate quiz completion summaries",
            expected_output="text"
        )
    
    def get_template(self, prompt_type: PromptType) -> PromptTemplate:
        """Get prompt template by type"""
        return self.templates[prompt_type]
    
    def format_prompt(self, prompt_type: PromptType, **kwargs) -> str:
        """Format prompt template with provided variables"""
        template = self.templates[prompt_type]
        
        # Validate required variables
        missing_vars = [var for var in template.required_vars if var not in kwargs]
        if missing_vars:
            raise ValueError(f"Missing required variables for {prompt_type.value}: {missing_vars}")
        
        # Set defaults for optional variables
        for var in template.optional_vars:
            if var not in kwargs:
                kwargs[var] = self._get_default_value(var)
        
        try:
            return template.template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Template formatting failed for {prompt_type.value}: {str(e)}")
    
    def _get_default_value(self, var_name: str) -> str:
        """Get default value for optional variables"""
        defaults = {
            "question_type": "open_ended",
            "options": "None",
            "current_question": "No current question",
            "question_type_breakdown": "Not available",
            "strong_areas": "General knowledge",
            "weak_areas": "None identified"
        }
        return defaults.get(var_name, "Not specified")

# Initialize global prompt manager
prompt_manager = PromptManager() 