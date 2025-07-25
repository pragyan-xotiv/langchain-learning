"""Shared types and enumerations for prompt management"""

from typing import List, Optional
from dataclasses import dataclass
from enum import Enum

class PromptType(Enum):
    """Types of prompts in the system"""
    INTENT_CLASSIFICATION = "intent_classification"
    TOPIC_EXTRACTION = "topic_extraction"
    TOPIC_VALIDATION = "topic_validation"
    QUESTION_GENERATION = "question_generation"
    ANSWER_VALIDATION = "answer_validation"
    CLARIFICATION = "clarification"
    SUMMARY_GENERATION = "summary_generation"

@dataclass
class PromptTemplate:
    """Container for prompt template and metadata"""
    name: str
    template: str
    required_vars: List[str]
    optional_vars: List[str] = None
    description: str = ""
    expected_output: str = "json"
    
    def __post_init__(self):
        if self.optional_vars is None:
            self.optional_vars = [] 