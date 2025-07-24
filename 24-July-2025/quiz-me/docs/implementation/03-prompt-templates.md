# Prompt Templates Implementation

## 🎯 Overview

This guide implements the complete LLM prompt template system for the Interactive Quiz Generator. The prompts are designed for reliability, consistency, and optimal performance with language models.

## 📋 Reference Documents

- **Design Specification**: `../prompts.md`
- **Previous Step**: `02-state-management.md`
- **Next Step**: `04-node-implementations.md`

## 🏗️ Prompt System Architecture

Create the prompt management system in `src/prompts.py`:

```python
"""LLM prompt templates and management system"""

from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import json
from .state import QuizState

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

# === PROMPT TEMPLATES ===

INTENT_CLASSIFICATION_PROMPT = """
You are an intent classifier for an interactive quiz application. Analyze the user's input and determine their intent based on the current context.

CURRENT CONTEXT:
- Current Phase: {current_phase}
- Quiz Active: {quiz_active}
- Current Topic: {topic}
- Recent Conversation: {conversation_history}

USER INPUT: "{user_input}"

POSSIBLE INTENTS:
1. start_quiz - User wants to begin a new quiz on a topic
2. answer_question - User is responding to a quiz question
3. new_quiz - User wants to start over with a different topic
4. exit - User wants to end the session
5. continue - User wants to proceed to the next question
6. clarification - User needs help or has questions

CLASSIFICATION RULES:
- If quiz is active and user provides a direct answer, classify as "answer_question"
- Keywords like "new quiz", "different topic", "start over" indicate "new_quiz"
- Keywords like "exit", "quit", "bye", "done" indicate "exit"
- Keywords like "next", "continue", "more" indicate "continue"
- If input seems unclear or off-topic, classify as "clarification"

Respond with JSON:
{{
    "intent": "one_of_the_intents_above",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation of your classification"
}}
"""

TOPIC_EXTRACTION_PROMPT = """
Extract the quiz topic from the user's input. Clean and standardize the topic name.

USER INPUT: "{user_input}"

EXTRACTION GUIDELINES:
- Identify the main subject the user wants to be quizzed on
- Make the topic specific but not overly narrow
- Clean up grammar and formatting
- Handle multiple topics by selecting the primary one
- If no clear topic, return null

EXAMPLES:
Input: "I want to learn about World War 2" → Topic: "World War II"
Input: "Quiz me on Python programming please" → Topic: "Python Programming"
Input: "Something about space and planets" → Topic: "Astronomy and Planets"
Input: "I don't know, anything" → Topic: null

Respond with JSON:
{{
    "topic": "extracted_topic_or_null",
    "confidence": 0.0-1.0,
    "alternative_topics": ["list", "if", "multiple", "detected"],
    "specificity_level": "very_broad|broad|specific|very_specific"
}}
"""

TOPIC_VALIDATION_PROMPT = """
Validate whether this topic is suitable for quiz generation.

TOPIC TO VALIDATE: "{topic}"

VALIDATION CRITERIA:
1. APPROPRIATENESS: Educational, safe, non-controversial content
2. SPECIFICITY: Not too broad ("everything") or too narrow ("my pet's name")
3. FEASIBILITY: Sufficient factual content exists for question generation
4. SAFETY: No harmful, offensive, or inappropriate material

CATEGORY GUIDELINES:
- Academic subjects: Usually valid (Science, History, Literature, etc.)
- Professional skills: Usually valid (Programming, Business, etc.)
- Hobbies/Interests: Valid if educational (Photography, Cooking, etc.)
- Personal/Private: Usually invalid (Personal relationships, private data)
- Controversial: Use caution (Politics, Religion - focus on facts only)

Respond with JSON:
{{
    "is_valid": true/false,
    "confidence": 0.0-1.0,
    "category": "academic|professional|hobby|general_knowledge|other",
    "difficulty_level": "beginner|intermediate|advanced",
    "estimated_questions": 5-50,
    "reason": "explanation_if_invalid",
    "suggestions": ["alternative", "topics", "if", "invalid"]
}}
"""

QUESTION_GENERATION_PROMPT = """
Generate a quiz question for the given topic and context.

QUIZ CONTEXT:
- Topic: {topic}
- Question Number: {question_number}
- Difficulty Level: {difficulty_level}
- Previous Questions: {previous_questions}
- Question Type: {question_type}

QUESTION REQUIREMENTS:
1. Create an educational, factual question about the topic
2. Match the specified difficulty level
3. Avoid repeating previous questions or very similar concepts
4. Make the question clear and unambiguous
5. Ensure there is a definitive correct answer

QUESTION TYPE SPECIFICATIONS:

MULTIPLE_CHOICE:
- Provide exactly 4 options (A, B, C, D)
- Only one correct answer
- Make distractors plausible but clearly incorrect
- Avoid "all of the above" or "none of the above"

OPEN_ENDED:
- Ask for explanation, description, or analysis
- Allow for multiple correct phrasings
- Focus on understanding, not memorization

TRUE_FALSE:
- Create a clear statement that is definitively true or false
- Avoid ambiguous or opinion-based statements

FILL_IN_BLANK:
- Create sentence with one key term missing
- Ensure only one logical answer fits
- Use context clues to guide the answer

Respond with JSON:
{{
    "question": "the_question_text",
    "type": "multiple_choice|open_ended|true_false|fill_in_blank",
    "correct_answer": "the_correct_answer",
    "options": ["A", "B", "C", "D"] or null,
    "explanation": "why_this_is_the_correct_answer",
    "difficulty_justification": "why_this_matches_requested_difficulty",
    "learning_objective": "what_this_question_teaches"
}}
"""

ANSWER_VALIDATION_PROMPT = """
Evaluate the user's answer to a quiz question.

QUESTION: "{question}"
CORRECT ANSWER: "{correct_answer}"
USER ANSWER: "{user_answer}"
QUESTION TYPE: {question_type}

EVALUATION CRITERIA:
1. ACCURACY: Does the answer contain the correct information?
2. COMPLETENESS: Does it address the key points?
3. UNDERSTANDING: Does it demonstrate comprehension of the concept?

SCORING GUIDELINES:
- CORRECT: Answer is accurate and demonstrates understanding
- PARTIALLY_CORRECT: Contains some correct elements but missing key points
- INCORRECT: Answer is wrong or shows misunderstanding

For multiple choice questions, use exact matching.
For open-ended questions, be generous with partial credit for answers that show understanding even if not perfectly worded.

Respond with JSON:
{{
    "is_correct": true/false,
    "partial_credit": true/false,
    "score_percentage": 0-100,
    "feedback": "encouraging_feedback_with_explanation",
    "key_points_covered": ["points", "correctly", "addressed"],
    "missing_points": ["points", "not", "addressed"],
    "suggestion": "how_to_improve_or_expand_answer"
}}
"""

CLARIFICATION_PROMPT = """
Generate a helpful clarification response for unclear user input.

CONTEXT:
- Current Phase: {current_phase}
- Current Question: {current_question}
- User Input: "{user_input}"
- Issue Type: {issue_type}

CLARIFICATION TYPES:

UNCLEAR_INTENT:
- User input doesn't match expected response format
- Provide examples of valid responses

TOPIC_UNCLEAR:
- User topic request is too vague or broad
- Suggest more specific alternatives

ANSWER_FORMAT:
- User answer format doesn't match question type
- Explain expected answer format with examples

GENERAL_CONFUSION:
- User seems lost or confused about the application
- Provide helpful guidance and options

Response should be:
- Friendly and encouraging
- Specific and actionable
- Include examples where helpful
- Offer multiple options when appropriate

Generate a helpful clarification message (plain text, no JSON needed).
"""

QUIZ_SUMMARY_PROMPT = """
Generate an engaging completion summary for the quiz.

QUIZ DATA:
- Topic: {topic}
- Total Questions: {total_questions}
- Correct Answers: {correct_answers}
- Final Score: {final_score}
- Accuracy: {accuracy}%
- Question Types: {question_type_breakdown}
- Strong Areas: {strong_areas}
- Improvement Areas: {weak_areas}

SUMMARY REQUIREMENTS:
1. Congratulatory and encouraging tone
2. Highlight achievements and progress
3. Provide specific feedback on performance
4. Suggest next steps or related topics
5. Include relevant emojis for engagement
6. Keep it concise but comprehensive

STRUCTURE:
- Opening congratulations
- Performance highlights
- Areas of strength
- Areas for improvement
- Suggestions for next steps

Generate an encouraging completion message (plain text).
"""

# === HELPER FUNCTIONS ===

def format_conversation_history(history: List[Dict[str, str]], max_entries: int = 3) -> str:
    """Format conversation history for prompt inclusion"""
    if not history:
        return "No previous conversation"
    
    recent = history[-max_entries:]
    formatted = []
    
    for entry in recent:
        user_text = entry.get('user', '')
        system_text = entry.get('system', '')
        
        if user_text:
            formatted.append(f"User: {user_text}")
        if system_text:
            formatted.append(f"System: {system_text}")
    
    return "\n".join(formatted) if formatted else "No previous conversation"

def format_previous_questions(questions: List[str], max_questions: int = 5) -> str:
    """Format previous questions for context"""
    if not questions:
        return "No previous questions"
    
    recent = questions[-max_questions:]
    return "\n".join([f"{i+1}. {q}" for i, q in enumerate(recent)])

def format_question_type_breakdown(breakdown: Dict[str, Any]) -> str:
    """Format question type performance breakdown"""
    if not breakdown:
        return "No breakdown available"
    
    formatted = []
    for q_type, data in breakdown.items():
        if isinstance(data, dict) and 'correct' in data and 'total' in data:
            accuracy = (data['correct'] / data['total'] * 100) if data['total'] > 0 else 0
            formatted.append(f"{q_type}: {data['correct']}/{data['total']} ({accuracy:.1f}%)")
    
    return ", ".join(formatted) if formatted else "No breakdown available"

# === STATE-BASED PROMPT FORMATTING ===

def format_intent_classification_prompt(state: QuizState) -> str:
    """Format intent classification prompt from state"""
    return prompt_manager.format_prompt(
        PromptType.INTENT_CLASSIFICATION,
        current_phase=state.current_phase,
        quiz_active=state.quiz_active,
        topic=state.topic or "None",
        conversation_history=format_conversation_history(state.conversation_history),
        user_input=state.user_input
    )

def format_topic_extraction_prompt(user_input: str) -> str:
    """Format topic extraction prompt"""
    return prompt_manager.format_prompt(
        PromptType.TOPIC_EXTRACTION,
        user_input=user_input
    )

def format_topic_validation_prompt(topic: str) -> str:
    """Format topic validation prompt"""
    return prompt_manager.format_prompt(
        PromptType.TOPIC_VALIDATION,
        topic=topic
    )

def format_question_generation_prompt(state: QuizState, question_type: str = "open_ended") -> str:
    """Format question generation prompt from state"""
    previous_questions = [answer.get('question', '') for answer in state.user_answers]
    
    return prompt_manager.format_prompt(
        PromptType.QUESTION_GENERATION,
        topic=state.topic,
        question_number=state.current_question_index + 1,
        difficulty_level=state.quiz_metadata.get('difficulty_level', 'medium'),
        previous_questions=format_previous_questions(previous_questions),
        question_type=question_type
    )

def format_answer_validation_prompt(state: QuizState) -> str:
    """Format answer validation prompt from state"""
    return prompt_manager.format_prompt(
        PromptType.ANSWER_VALIDATION,
        question=state.current_question,
        correct_answer=state.correct_answer,
        user_answer=state.current_answer,
        question_type=state.question_type or "open_ended",
        options=str(state.question_options) if state.question_options else "None"
    )

def format_clarification_prompt(state: QuizState, issue_type: str) -> str:
    """Format clarification prompt from state"""
    return prompt_manager.format_prompt(
        PromptType.CLARIFICATION,
        current_phase=state.current_phase,
        current_question=state.current_question or "No current question",
        user_input=state.user_input,
        issue_type=issue_type
    )

def format_summary_prompt(state: QuizState) -> str:
    """Format quiz summary prompt from state"""
    summary = state.get_performance_summary()
    
    return prompt_manager.format_prompt(
        PromptType.SUMMARY_GENERATION,
        topic=state.topic,
        total_questions=state.total_questions_answered,
        correct_answers=state.correct_answers_count,
        final_score=state.total_score,
        accuracy=summary['accuracy'],
        question_type_breakdown=format_question_type_breakdown(summary.get('question_type_performance', {})),
        strong_areas="General knowledge",  # TODO: Implement analysis
        weak_areas="None identified"       # TODO: Implement analysis
    )

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
    import re
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
        "summary": format_summary_prompt(test_state)
    }

if __name__ == "__main__":
    # Test prompt generation
    test_prompts = create_test_prompts()
    for prompt_type, prompt in test_prompts.items():
        print(f"\n=== {prompt_type.upper()} ===")
        print(prompt[:200] + "..." if len(prompt) > 200 else prompt)
```

## 🧪 Prompt Testing Implementation

Create comprehensive tests in `tests/test_prompts.py`:

```python
"""Tests for prompt template functionality"""

import pytest
import json
from src.prompts import (
    PromptManager, PromptType, PromptTemplate,
    format_intent_classification_prompt, format_topic_extraction_prompt,
    format_topic_validation_prompt, format_question_generation_prompt,
    format_answer_validation_prompt, format_clarification_prompt,
    format_summary_prompt, validate_prompt_response, extract_json_from_response,
    create_test_prompts
)
from src.state import QuizState, create_test_state

class TestPromptManager:
    """Test PromptManager functionality"""
    
    def test_prompt_manager_initialization(self):
        """Test prompt manager loads all templates"""
        manager = PromptManager()
        
        # Check all prompt types are loaded
        expected_types = [
            PromptType.INTENT_CLASSIFICATION,
            PromptType.TOPIC_EXTRACTION,
            PromptType.TOPIC_VALIDATION,
            PromptType.QUESTION_GENERATION,
            PromptType.ANSWER_VALIDATION,
            PromptType.CLARIFICATION,
            PromptType.SUMMARY_GENERATION
        ]
        
        for prompt_type in expected_types:
            assert prompt_type in manager.templates
            template = manager.templates[prompt_type]
            assert isinstance(template, PromptTemplate)
            assert template.template  # Template should not be empty
            assert template.required_vars  # Should have required variables
    
    def test_get_template(self):
        """Test getting template by type"""
        manager = PromptManager()
        
        template = manager.get_template(PromptType.INTENT_CLASSIFICATION)
        assert template.name == "intent_classification"
        assert "CURRENT CONTEXT" in template.template
        assert "user_input" in template.required_vars
    
    def test_format_prompt_success(self):
        """Test successful prompt formatting"""
        manager = PromptManager()
        
        formatted = manager.format_prompt(
            PromptType.TOPIC_EXTRACTION,
            user_input="I want to learn about Python"
        )
        
        assert "I want to learn about Python" in formatted
        assert "{user_input}" not in formatted  # Should be replaced
    
    def test_format_prompt_missing_required_vars(self):
        """Test prompt formatting with missing required variables"""
        manager = PromptManager()
        
        with pytest.raises(ValueError) as exc_info:
            manager.format_prompt(PromptType.TOPIC_EXTRACTION)
        
        assert "Missing required variables" in str(exc_info.value)
        assert "user_input" in str(exc_info.value)
    
    def test_format_prompt_with_optional_vars(self):
        """Test prompt formatting with optional variables"""
        manager = PromptManager()
        
        # This should work with defaults for optional vars
        formatted = manager.format_prompt(
            PromptType.ANSWER_VALIDATION,
            question="Test question?",
            correct_answer="Test answer",
            user_answer="User answer"
        )
        
        assert "Test question?" in formatted
        assert "open_ended" in formatted  # Default question_type


class TestPromptFormatting:
    """Test prompt formatting functions"""
    
    def test_intent_classification_formatting(self):
        """Test intent classification prompt formatting"""
        state = create_test_state()
        state.user_input = "I want a new quiz"
        state.current_phase = "quiz_active"
        
        prompt = format_intent_classification_prompt(state)
        
        assert "I want a new quiz" in prompt
        assert "quiz_active" in prompt
        assert "POSSIBLE INTENTS" in prompt
    
    def test_topic_extraction_formatting(self):
        """Test topic extraction prompt formatting"""
        prompt = format_topic_extraction_prompt("I want to learn about machine learning")
        
        assert "I want to learn about machine learning" in prompt
        assert "EXTRACTION GUIDELINES" in prompt
        assert "EXAMPLES:" in prompt
    
    def test_topic_validation_formatting(self):
        """Test topic validation prompt formatting"""
        prompt = format_topic_validation_prompt("Python Programming")
        
        assert "Python Programming" in prompt
        assert "VALIDATION CRITERIA" in prompt
        assert "CATEGORY GUIDELINES" in prompt
    
    def test_question_generation_formatting(self):
        """Test question generation prompt formatting"""
        state = create_test_state()
        state.topic = "Python Programming"
        state.current_question_index = 2
        
        prompt = format_question_generation_prompt(state, "multiple_choice")
        
        assert "Python Programming" in prompt
        assert "Question Number: 3" in prompt  # Index + 1
        assert "multiple_choice" in prompt
        assert "QUESTION REQUIREMENTS" in prompt
    
    def test_answer_validation_formatting(self):
        """Test answer validation prompt formatting"""
        state = create_test_state()
        state.current_question = "What is a list?"
        state.correct_answer = "A collection of items"
        state.current_answer = "An array of elements"
        state.question_type = "open_ended"
        
        prompt = format_answer_validation_prompt(state)
        
        assert "What is a list?" in prompt
        assert "A collection of items" in prompt
        assert "An array of elements" in prompt
        assert "EVALUATION CRITERIA" in prompt
    
    def test_clarification_formatting(self):
        """Test clarification prompt formatting"""
        state = create_test_state()
        state.user_input = "I don't understand"
        state.current_phase = "quiz_active"
        
        prompt = format_clarification_prompt(state, "unclear_intent")
        
        assert "I don't understand" in prompt
        assert "quiz_active" in prompt
        assert "unclear_intent" in prompt
    
    def test_summary_formatting(self):
        """Test summary prompt formatting"""
        state = create_test_state()
        state.topic = "Python Programming"
        state.total_questions_answered = 5
        state.correct_answers_count = 4
        state.total_score = 40
        
        prompt = format_summary_prompt(state)
        
        assert "Python Programming" in prompt
        assert "Total Questions: 5" in prompt
        assert "Correct Answers: 4" in prompt
        assert "Final Score: 40" in prompt


class TestPromptValidation:
    """Test prompt validation utilities"""
    
    def test_validate_json_response(self):
        """Test JSON response validation"""
        valid_json = '{"intent": "start_quiz", "confidence": 0.9}'
        invalid_json = '{"invalid": json}'
        
        assert validate_prompt_response(valid_json, "json") is True
        assert validate_prompt_response(invalid_json, "json") is False
    
    def test_validate_text_response(self):
        """Test text response validation"""
        valid_text = "This is a valid response"
        empty_text = ""
        whitespace_text = "   "
        
        assert validate_prompt_response(valid_text, "text") is True
        assert validate_prompt_response(empty_text, "text") is False
        assert validate_prompt_response(whitespace_text, "text") is False
    
    def test_extract_json_from_response(self):
        """Test JSON extraction from response"""
        # Clean JSON response
        clean_json = '{"intent": "start_quiz", "confidence": 0.9}'
        result = extract_json_from_response(clean_json)
        assert result["intent"] == "start_quiz"
        assert result["confidence"] == 0.9
        
        # JSON embedded in text
        embedded_json = 'Here is the result: {"intent": "exit", "confidence": 0.8} end'
        result = extract_json_from_response(embedded_json)
        assert result["intent"] == "exit"
        
        # Invalid JSON
        invalid_json = 'This is not JSON at all'
        result = extract_json_from_response(invalid_json)
        assert "error" in result
        assert "raw_response" in result


class TestPromptIntegration:
    """Test prompt integration with state"""
    
    def test_create_test_prompts(self):
        """Test test prompt creation"""
        test_prompts = create_test_prompts()
        
        expected_types = [
            "intent_classification", "topic_extraction", "topic_validation",
            "question_generation", "answer_validation", "clarification", "summary"
        ]
        
        for prompt_type in expected_types:
            assert prompt_type in test_prompts
            assert isinstance(test_prompts[prompt_type], str)
            assert len(test_prompts[prompt_type]) > 100  # Should be substantial
    
    def test_prompt_template_consistency(self):
        """Test that all templates have consistent structure"""
        manager = PromptManager()
        
        for prompt_type, template in manager.templates.items():
            # All templates should have basic metadata
            assert template.name
            assert template.template
            assert template.required_vars
            assert template.description
            
            # Templates should contain their required variables as placeholders
            for var in template.required_vars:
                placeholder = "{" + var + "}"
                assert placeholder in template.template, f"Template {template.name} missing placeholder for {var}"
    
    def test_state_integration(self):
        """Test prompt formatting with actual state objects"""
        state = QuizState()
        state.user_input = "I want to quiz on history"
        state.topic = "World History"
        state.topic_validated = True
        state.current_phase = "quiz_active"
        state.quiz_active = True
        
        # Should be able to format multiple prompt types
        intent_prompt = format_intent_classification_prompt(state)
        topic_prompt = format_topic_validation_prompt(state.topic)
        
        assert len(intent_prompt) > 200
        assert len(topic_prompt) > 200
        assert "World History" in topic_prompt


if __name__ == "__main__":
    pytest.main([__file__])
```

## 🔧 Advanced Prompt Features

### Dynamic Prompt Adjustment

```python
# src/adaptive_prompts.py (optional enhancement)
from typing import Dict, List
from .state import QuizState
from .prompts import PromptManager, PromptType

class AdaptivePromptManager(PromptManager):
    """Enhanced prompt manager with adaptive capabilities"""
    
    def __init__(self):
        super().__init__()
        self.performance_history: List[Dict] = []
    
    def adjust_difficulty_prompt(self, base_prompt: str, performance_data: Dict) -> str:
        """Adjust question generation prompt based on performance"""
        accuracy = performance_data.get('accuracy', 50)
        
        if accuracy > 85:
            difficulty_adjustment = "\nIMPORTANT: Generate a more challenging question. The user is performing very well."
        elif accuracy < 50:
            difficulty_adjustment = "\nIMPORTANT: Generate an easier question. The user is struggling with the current difficulty."
        else:
            difficulty_adjustment = ""
        
        return base_prompt + difficulty_adjustment
    
    def personalize_feedback_prompt(self, base_prompt: str, user_patterns: Dict) -> str:
        """Personalize feedback based on user learning patterns"""
        if user_patterns.get('prefers_detailed_explanations', False):
            feedback_style = "\nFEEDBACK STYLE: Provide detailed, comprehensive explanations."
        else:
            feedback_style = "\nFEEDBACK STYLE: Keep feedback concise and focused."
        
        return base_prompt + feedback_style
```

### Prompt Caching

```python
# src/prompt_cache.py (optional enhancement)
from functools import lru_cache
from typing import Tuple
import hashlib

class PromptCache:
    """Cache for formatted prompts to improve performance"""
    
    def __init__(self, max_size: int = 100):
        self.cache: Dict[str, str] = {}
        self.max_size = max_size
        self.access_count: Dict[str, int] = {}
    
    def get_cache_key(self, prompt_type: str, **kwargs) -> str:
        """Generate cache key from prompt type and parameters"""
        # Create deterministic key from parameters
        param_str = str(sorted(kwargs.items()))
        key_material = f"{prompt_type}:{param_str}"
        return hashlib.md5(key_material.encode()).hexdigest()
    
    def get(self, cache_key: str) -> Optional[str]:
        """Get cached prompt"""
        if cache_key in self.cache:
            self.access_count[cache_key] = self.access_count.get(cache_key, 0) + 1
            return self.cache[cache_key]
        return None
    
    def set(self, cache_key: str, prompt: str) -> None:
        """Cache formatted prompt"""
        if len(self.cache) >= self.max_size:
            # Remove least recently used item
            lru_key = min(self.access_count.keys(), key=lambda k: self.access_count[k])
            del self.cache[lru_key]
            del self.access_count[lru_key]
        
        self.cache[cache_key] = prompt
        self.access_count[cache_key] = 1

# Global cache instance
prompt_cache = PromptCache()
```

## 📋 Implementation Checklist

### Core Implementation
- [ ] **PromptTemplate Class**: Dataclass with metadata
- [ ] **PromptManager Class**: Template management and formatting
- [ ] **All Prompt Templates**: 7 core prompt templates implemented
- [ ] **Formatting Functions**: State-based prompt formatting utilities
- [ ] **Validation Functions**: Response validation and JSON extraction

### Testing
- [ ] **Unit Tests**: All prompt functions tested
- [ ] **Integration Tests**: Prompt-state integration tested
- [ ] **Edge Cases**: Invalid inputs and malformed responses handled
- [ ] **Template Validation**: All templates have required placeholders

### Quality Assurance
- [ ] **Type Checking**: mypy passes without errors
- [ ] **Template Consistency**: All templates follow consistent structure
- [ ] **Documentation**: All functions have comprehensive docstrings

## 🚨 Common Issues and Solutions

### Template Formatting Errors
**Issue**: KeyError when formatting templates
**Solution**: Validate all required variables before formatting:

```python
def safe_format_prompt(prompt_type: PromptType, **kwargs) -> str:
    """Safely format prompt with error handling"""
    try:
        return prompt_manager.format_prompt(prompt_type, **kwargs)
    except ValueError as e:
        # Log error and return fallback prompt
        logger.error(f"Prompt formatting failed: {e}")
        return f"Error formatting prompt: {e}"
```

### LLM Response Parsing
**Issue**: LLM returns malformed JSON
**Solution**: Use robust JSON extraction with fallbacks:

```python
def robust_json_extraction(response: str) -> Dict[str, Any]:
    """Extract JSON with multiple fallback strategies"""
    # Try multiple parsing strategies
    strategies = [
        lambda r: json.loads(r),
        lambda r: json.loads(re.search(r'\{.*\}', r, re.DOTALL).group()),
        lambda r: {"error": "Failed to parse", "raw": r}
    ]
    
    for strategy in strategies:
        try:
            return strategy(response)
        except:
            continue
    
    return {"error": "All parsing strategies failed"}
```

## ✅ Completion Criteria

Prompt templates implementation is complete when:

1. **All 7 prompt templates implemented** and tested
2. **PromptManager class functional** with formatting and validation
3. **State integration working** for all prompt types
4. **Comprehensive tests passing** with >90% coverage
5. **JSON response handling robust** with fallback mechanisms
6. **Type checking passes** without errors

**Next Step**: Proceed to **[04-node-implementations.md](./04-node-implementations.md)** to implement the processing nodes. 