"""Tests for prompt template functionality"""

import pytest
import json
from src.prompts import (
    PromptManager, PromptType, PromptTemplate,
    format_intent_classification_prompt, format_topic_extraction_prompt,
    format_topic_validation_prompt, format_question_generation_prompt,
    format_answer_validation_prompt, format_clarification_prompt,
    format_summary_generation_prompt, validate_prompt_response, extract_json_from_response,
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
        
        prompt = format_summary_generation_prompt(state)
        
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