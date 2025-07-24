# Node Implementations

## 🎯 Overview

This guide implements the five core processing nodes that handle the quiz workflow logic. Each node is a specialized function that processes the current state and returns an updated state.

## 📋 Reference Documents

- **Design Specification**: `../nodes.md`
- **Previous Step**: `03-prompt-templates.md`
- **Next Step**: `05-edge-logic.md`

## 🏗️ Node Architecture Implementation

Create the complete node system in `src/nodes.py`:

```python
"""Processing nodes for the Interactive Quiz Generator workflow"""

from typing import Dict, Any, Optional, List
import asyncio
import json
import logging
from datetime import datetime
from langchain_openai import ChatOpenAI
from .state import QuizState
from .prompts import (
    format_intent_classification_prompt,
    format_topic_extraction_prompt,
    format_topic_validation_prompt,
    format_question_generation_prompt,
    format_answer_validation_prompt,
    format_clarification_prompt,
    format_summary_prompt,
    extract_json_from_response
)
from .utils import Config

# Configure logging
logger = logging.getLogger(__name__)

# === NODE IMPLEMENTATIONS ===

class QuizNodeError(Exception):
    """Base exception for node processing errors"""
    pass

class LLMCallError(QuizNodeError):
    """Error in LLM communication"""
    pass

class StateValidationError(QuizNodeError):
    """Error in state validation"""
    pass

def create_llm_client() -> ChatOpenAI:
    """Create and configure LLM client"""
    return ChatOpenAI(
        api_key=Config.OPENAI_API_KEY,
        model=Config.OPENAI_MODEL,
        temperature=Config.OPENAI_TEMPERATURE,
        max_tokens=Config.OPENAI_MAX_TOKENS
    )

async def safe_llm_call(llm: ChatOpenAI, prompt: str, max_retries: int = 3) -> str:
    """Make LLM call with error handling and retries"""
    for attempt in range(max_retries):
        try:
            response = await llm.ainvoke(prompt)
            return response.content
        except Exception as e:
            logger.warning(f"LLM call attempt {attempt + 1} failed: {str(e)}")
            if attempt == max_retries - 1:
                raise LLMCallError(f"LLM call failed after {max_retries} attempts: {str(e)}")
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
    
    raise LLMCallError("Unexpected error in LLM call")

# === NODE 1: QUERY ANALYZER ===

def query_analyzer(state: QuizState, llm: ChatOpenAI) -> QuizState:
    """
    Analyzes user input to determine intent and context.
    
    Args:
        state: Current quiz state with user_input populated
        llm: Language model client
        
    Returns:
        Updated state with user_intent and conversation_history
    """
    logger.info(f"Query Analyzer processing: '{state.user_input}' in phase '{state.current_phase}'")
    
    try:
        # Validate input state
        if not state.user_input.strip():
            state.last_error = "Empty user input provided"
            return state
        
        # Format prompt for intent classification
        prompt = format_intent_classification_prompt(state)
        
        # Call LLM for intent classification
        response = asyncio.run(safe_llm_call(llm, prompt))
        
        # Parse response
        result = extract_json_from_response(response)
        
        if "error" in result:
            logger.error(f"Intent classification failed: {result['error']}")
            state.last_error = f"Intent analysis failed: {result['error']}"
            state.user_intent = "clarification"  # Default fallback
        else:
            # Extract intent information
            state.user_intent = result.get("intent", "clarification")
            confidence = result.get("confidence", 0.0)
            reasoning = result.get("reasoning", "No reasoning provided")
            
            logger.info(f"Intent classified as '{state.user_intent}' with confidence {confidence}")
            
            # Store analysis in metadata
            state.quiz_metadata["last_intent_analysis"] = {
                "intent": state.user_intent,
                "confidence": confidence,
                "reasoning": reasoning,
                "timestamp": datetime.now().isoformat()
            }
        
        # Update conversation history
        state.add_conversation_entry(
            user_input=state.user_input,
            system_response=f"Intent classified as: {state.user_intent}"
        )
        
        # Clear any previous errors on successful processing
        if not state.last_error:
            state.last_error = None
        
        return state
        
    except Exception as e:
        logger.error(f"Query analyzer error: {str(e)}")
        state.last_error = f"Query analysis failed: {str(e)}"
        state.user_intent = "clarification"
        return state

# === NODE 2: TOPIC VALIDATOR ===

def topic_validator(state: QuizState, llm: ChatOpenAI) -> QuizState:
    """
    Validates quiz topics for appropriateness and feasibility.
    
    Args:
        state: Current quiz state with user_input containing topic
        llm: Language model client
        
    Returns:
        Updated state with topic validation results
    """
    logger.info(f"Topic Validator processing input: '{state.user_input}'")
    
    try:
        # Extract topic from user input
        extraction_prompt = format_topic_extraction_prompt(state.user_input)
        extraction_response = asyncio.run(safe_llm_call(llm, extraction_prompt))
        extraction_result = extract_json_from_response(extraction_response)
        
        if "error" in extraction_result or not extraction_result.get("topic"):
            logger.warning("Topic extraction failed")
            state.last_error = "Could not identify a clear quiz topic from your input"
            state.current_phase = "topic_selection"
            return state
        
        # Store extracted topic
        extracted_topic = extraction_result["topic"]
        state.topic = extracted_topic
        
        logger.info(f"Extracted topic: '{extracted_topic}'")
        
        # Validate topic appropriateness
        validation_prompt = format_topic_validation_prompt(extracted_topic)
        validation_response = asyncio.run(safe_llm_call(llm, validation_prompt))
        validation_result = extract_json_from_response(validation_response)
        
        if "error" in validation_result:
            logger.error(f"Topic validation failed: {validation_result['error']}")
            state.last_error = "Failed to validate topic appropriateness"
            state.current_phase = "topic_selection"
            return state
        
        # Process validation results
        is_valid = validation_result.get("is_valid", False)
        state.topic_validated = is_valid
        
        if is_valid:
            # Topic is valid - set up quiz
            logger.info(f"Topic '{extracted_topic}' validated successfully")
            state.current_phase = "quiz_active"
            state.quiz_active = True
            
            # Store topic metadata
            state.quiz_metadata.update({
                "topic_category": validation_result.get("category", "general"),
                "difficulty_level": validation_result.get("difficulty_level", "medium"),
                "estimated_questions": validation_result.get("estimated_questions", 10),
                "validation_confidence": validation_result.get("confidence", 0.0)
            })
            
            # Set quiz parameters
            estimated_questions = validation_result.get("estimated_questions", 10)
            state.max_questions = min(estimated_questions, Config.MAX_QUESTIONS_DEFAULT)
            
        else:
            # Topic is invalid
            logger.warning(f"Topic '{extracted_topic}' validation failed")
            reason = validation_result.get("reason", "Topic not suitable for quiz generation")
            suggestions = validation_result.get("suggestions", [])
            
            state.last_error = reason
            if suggestions:
                state.last_error += f" Try these alternatives: {', '.join(suggestions)}"
            
            state.current_phase = "topic_selection"
            state.topic = None  # Clear invalid topic
        
        return state
        
    except Exception as e:
        logger.error(f"Topic validator error: {str(e)}")
        state.last_error = f"Topic validation failed: {str(e)}"
        state.current_phase = "topic_selection"
        state.topic_validated = False
        return state

# === NODE 3: QUIZ GENERATOR ===

def quiz_generator(state: QuizState, llm: ChatOpenAI) -> QuizState:
    """
    Generates diverse, engaging quiz questions based on the validated topic.
    
    Args:
        state: Current quiz state with validated topic
        llm: Language model client
        
    Returns:
        Updated state with generated question
    """
    logger.info(f"Quiz Generator creating question {state.current_question_index + 1} for topic '{state.topic}'")
    
    try:
        # Validate prerequisites
        if not state.topic_validated or not state.topic:
            state.last_error = "Cannot generate questions without validated topic"
            return state
        
        # Determine question type based on progression
        question_type = determine_question_type(state)
        
        # Format question generation prompt
        prompt = format_question_generation_prompt(state, question_type)
        
        # Generate question
        response = asyncio.run(safe_llm_call(llm, prompt))
        result = extract_json_from_response(response)
        
        if "error" in result:
            logger.error(f"Question generation failed: {result['error']}")
            state.last_error = "Failed to generate question. Please try again."
            return state
        
        # Extract question data
        question = result.get("question", "")
        q_type = result.get("type", question_type)
        correct_answer = result.get("correct_answer", "")
        options = result.get("options", None)
        explanation = result.get("explanation", "")
        
        if not question or not correct_answer:
            logger.error("Generated question missing required fields")
            state.last_error = "Generated question was incomplete. Please try again."
            return state
        
        # Update state with new question
        state.current_question = question
        state.question_type = q_type
        state.correct_answer = correct_answer
        state.question_options = options
        
        # Store question metadata
        state.quiz_metadata[f"question_{state.current_question_index}_metadata"] = {
            "explanation": explanation,
            "difficulty_justification": result.get("difficulty_justification", ""),
            "learning_objective": result.get("learning_objective", ""),
            "generated_at": datetime.now().isoformat()
        }
        
        logger.info(f"Generated {q_type} question: '{question[:50]}...'")
        
        # Clear any previous errors
        state.last_error = None
        
        return state
        
    except Exception as e:
        logger.error(f"Quiz generator error: {str(e)}")
        state.last_error = f"Question generation failed: {str(e)}"
        return state

def determine_question_type(state: QuizState) -> str:
    """Determine appropriate question type based on quiz progression"""
    total_questions = state.total_questions_answered
    
    # Question type distribution strategy
    if total_questions == 0:
        return "multiple_choice"  # Start with easier format
    elif total_questions % 3 == 0:
        return "open_ended"  # Every third question
    elif total_questions % 4 == 0:
        return "true_false"  # Every fourth question
    else:
        return "multiple_choice"  # Default format

# === NODE 4: ANSWER VALIDATOR ===

def answer_validator(state: QuizState, llm: ChatOpenAI) -> QuizState:
    """
    Evaluates user answers for correctness and provides constructive feedback.
    
    Args:
        state: Current quiz state with user answer
        llm: Language model client
        
    Returns:
        Updated state with validation results and feedback
    """
    logger.info(f"Answer Validator processing answer for question {state.current_question_index + 1}")
    
    try:
        # Validate prerequisites
        if not state.current_answer or not state.current_question:
            state.last_error = "Missing answer or question for validation"
            return state
        
        # Use different validation strategies based on question type
        if state.question_type == "multiple_choice":
            result = validate_multiple_choice_answer(state)
        elif state.question_type == "true_false":
            result = validate_true_false_answer(state)
        else:
            # Use LLM for open-ended and complex answers
            prompt = format_answer_validation_prompt(state)
            response = asyncio.run(safe_llm_call(llm, prompt))
            result = extract_json_from_response(response)
        
        if "error" in result:
            logger.error(f"Answer validation failed: {result['error']}")
            state.last_error = "Failed to validate answer. Please try again."
            return state
        
        # Extract validation results
        is_correct = result.get("is_correct", False)
        partial_credit = result.get("partial_credit", False)
        score_percentage = result.get("score_percentage", 0 if not is_correct else 100)
        feedback = result.get("feedback", "No feedback available")
        
        # Update state
        state.answer_is_correct = is_correct
        state.answer_feedback = feedback
        
        # Add detailed answer record
        state.add_answer_record(
            question=state.current_question,
            user_answer=state.current_answer,
            correct_answer=state.correct_answer,
            is_correct=is_correct,
            feedback=feedback,
            explanation=result.get("explanation", "")
        )
        
        # Update phase
        state.current_phase = "question_answered"
        
        logger.info(f"Answer validated: {'Correct' if is_correct else 'Incorrect'} ({score_percentage}%)")
        
        return state
        
    except Exception as e:
        logger.error(f"Answer validator error: {str(e)}")
        state.last_error = f"Answer validation failed: {str(e)}"
        return state

def validate_multiple_choice_answer(state: QuizState) -> Dict[str, Any]:
    """Validate multiple choice answers using exact matching"""
    user_answer = state.current_answer.strip().lower()
    correct_answer = state.correct_answer.strip().lower()
    
    # Handle various input formats
    answer_mappings = {
        'a': '0', '1': '0', 'first': '0',
        'b': '1', '2': '1', 'second': '1',
        'c': '2', '3': '2', 'third': '2',
        'd': '3', '4': '3', 'fourth': '3'
    }
    
    # Try exact match first
    is_correct = (user_answer == correct_answer)
    
    # If not exact match, try letter/number matching
    if not is_correct and state.question_options:
        user_mapped = answer_mappings.get(user_answer, user_answer)
        correct_mapped = answer_mappings.get(correct_answer, correct_answer)
        is_correct = (user_mapped == correct_mapped)
        
        # Try matching against option text
        if not is_correct:
            for i, option in enumerate(state.question_options):
                if user_answer in option.lower():
                    is_correct = (str(i) == correct_answer or chr(65 + i).lower() == correct_answer)
                    break
    
    return {
        "is_correct": is_correct,
        "partial_credit": False,
        "score_percentage": 100 if is_correct else 0,
        "feedback": "Correct!" if is_correct else f"The correct answer is {state.correct_answer}."
    }

def validate_true_false_answer(state: QuizState) -> Dict[str, Any]:
    """Validate true/false answers"""
    user_answer = state.current_answer.strip().lower()
    correct_answer = state.correct_answer.strip().lower()
    
    # Normalize true/false responses
    true_values = {'true', 't', 'yes', 'y', '1', 'correct'}
    false_values = {'false', 'f', 'no', 'n', '0', 'incorrect'}
    
    user_normalized = None
    if user_answer in true_values:
        user_normalized = 'true'
    elif user_answer in false_values:
        user_normalized = 'false'
    
    correct_normalized = None
    if correct_answer in true_values:
        correct_normalized = 'true'
    elif correct_answer in false_values:
        correct_normalized = 'false'
    
    is_correct = (user_normalized == correct_normalized and user_normalized is not None)
    
    return {
        "is_correct": is_correct,
        "partial_credit": False,
        "score_percentage": 100 if is_correct else 0,
        "feedback": "Correct!" if is_correct else f"The correct answer is {correct_answer}."
    }

# === NODE 5: SCORE GENERATOR ===

def score_generator(state: QuizState, llm: ChatOpenAI) -> QuizState:
    """
    Calculates scores, tracks progress, and determines quiz completion status.
    
    Args:
        state: Current quiz state with validated answer
        llm: Language model client
        
    Returns:
        Updated state with scoring and completion information
    """
    logger.info(f"Score Generator processing question {state.current_question_index + 1}")
    
    try:
        # Update question counters
        state.total_questions_answered += 1
        
        # Update score based on correctness
        if state.answer_is_correct:
            state.correct_answers_count += 1
            
            # Calculate points with bonuses
            base_points = 10
            difficulty_multiplier = get_difficulty_multiplier(state)
            question_type_bonus = get_question_type_bonus(state.question_type)
            
            points_earned = int(base_points * difficulty_multiplier + question_type_bonus)
            state.total_score += points_earned
            
            logger.info(f"Points earned: {points_earned} (base: {base_points}, multiplier: {difficulty_multiplier}, bonus: {question_type_bonus})")
        
        # Calculate progress and completion
        if state.quiz_type == "finite" and state.max_questions:
            state.quiz_completion_percentage = (
                state.total_questions_answered / state.max_questions * 100
            )
            
            # Check if quiz is complete
            if state.total_questions_answered >= state.max_questions:
                state.quiz_completed = True
                state.quiz_active = False
                state.current_phase = "quiz_complete"
                logger.info("Quiz completed - maximum questions reached")
        
        # Generate performance insights
        accuracy = state.calculate_accuracy()
        state.quiz_metadata.update({
            "current_accuracy": accuracy,
            "performance_trend": calculate_performance_trend(state.user_answers),
            "last_score_update": datetime.now().isoformat()
        })
        
        # Move to next question if quiz continues
        if not state.quiz_completed:
            state.increment_question()
        
        logger.info(f"Score updated: {state.total_score} points, {accuracy:.1f}% accuracy")
        
        return state
        
    except Exception as e:
        logger.error(f"Score generator error: {str(e)}")
        state.last_error = f"Score calculation failed: {str(e)}"
        return state

def get_difficulty_multiplier(state: QuizState) -> float:
    """Get scoring multiplier based on difficulty level"""
    difficulty = state.quiz_metadata.get('difficulty_level', 'medium')
    multipliers = {
        'beginner': 0.8,
        'easy': 0.8,
        'medium': 1.0,
        'intermediate': 1.0,
        'hard': 1.5,
        'advanced': 1.5
    }
    return multipliers.get(difficulty, 1.0)

def get_question_type_bonus(question_type: Optional[str]) -> int:
    """Get bonus points based on question type difficulty"""
    bonuses = {
        'multiple_choice': 0,
        'true_false': 0,
        'fill_in_blank': 3,
        'open_ended': 5
    }
    return bonuses.get(question_type, 0)

def calculate_performance_trend(answers: List[Dict[str, Any]]) -> str:
    """Calculate performance trend from recent answers"""
    if len(answers) < 3:
        return "insufficient_data"
    
    recent_answers = answers[-5:]  # Last 5 answers
    recent_correct = sum(1 for answer in recent_answers if answer.get('is_correct', False))
    recent_accuracy = recent_correct / len(recent_answers)
    
    if len(answers) >= 10:
        earlier_answers = answers[-10:-5]  # 5 answers before recent
        earlier_correct = sum(1 for answer in earlier_answers if answer.get('is_correct', False))
        earlier_accuracy = earlier_correct / len(earlier_answers)
        
        if recent_accuracy > earlier_accuracy + 0.2:
            return "improving"
        elif recent_accuracy < earlier_accuracy - 0.2:
            return "declining"
        else:
            return "stable"
    
    if recent_accuracy >= 0.8:
        return "strong"
    elif recent_accuracy >= 0.6:
        return "moderate"
    else:
        return "struggling"

# === UTILITY FUNCTIONS ===

def validate_node_prerequisites(state: QuizState, node_name: str) -> List[str]:
    """Validate that state meets node prerequisites"""
    errors = []
    
    prerequisites = {
        "query_analyzer": ["user_input"],
        "topic_validator": ["user_input"],
        "quiz_generator": ["topic", "topic_validated"],
        "answer_validator": ["current_answer", "current_question", "correct_answer"],
        "score_generator": ["answer_is_correct", "total_questions_answered"]
    }
    
    required_fields = prerequisites.get(node_name, [])
    for field in required_fields:
        value = getattr(state, field, None)
        if value is None or (isinstance(value, str) and not value.strip()):
            errors.append(f"Node '{node_name}' requires field '{field}'")
    
    return errors

async def test_node_chain(initial_state: QuizState) -> QuizState:
    """Test complete node chain execution"""
    llm = create_llm_client()
    
    # Simulate node chain
    state = initial_state
    
    # Query Analyzer
    state = query_analyzer(state, llm)
    if state.last_error:
        return state
    
    # Topic Validator (if appropriate intent)
    if state.user_intent == "start_quiz":
        state = topic_validator(state, llm)
        if state.last_error:
            return state
    
    # Quiz Generator (if topic validated)
    if state.topic_validated:
        state = quiz_generator(state, llm)
        if state.last_error:
            return state
    
    return state

# === ERROR RECOVERY ===

def recover_from_node_error(state: QuizState, node_name: str, error: Exception) -> QuizState:
    """Implement error recovery strategies for nodes"""
    logger.error(f"Node '{node_name}' failed with error: {str(error)}")
    
    # Increment retry count
    state.retry_count += 1
    
    # Implement specific recovery strategies
    if node_name == "query_analyzer":
        state.user_intent = "clarification"
        state.last_error = "I didn't understand that. Could you rephrase?"
    
    elif node_name == "topic_validator":
        state.current_phase = "topic_selection"
        state.last_error = "I had trouble with that topic. Please try a different one."
    
    elif node_name == "quiz_generator":
        state.last_error = "I couldn't generate a question. Let me try again."
    
    elif node_name == "answer_validator":
        state.last_error = "I couldn't evaluate your answer. Please try again."
    
    elif node_name == "score_generator":
        state.last_error = "I couldn't update your score. Let me continue with the next question."
    
    # If too many retries, suggest restart
    if state.retry_count >= 3:
        state.last_error += " You might want to start a new quiz."
    
    return state

if __name__ == "__main__":
    # Test node implementations
    from .state import create_test_state
    
    test_state = create_test_state()
    test_state.user_input = "I want a quiz about Python programming"
    
    llm = create_llm_client()
    result = asyncio.run(test_node_chain(test_state))
    
    print(f"Final state phase: {result.current_phase}")
    print(f"Topic: {result.topic}")
    print(f"Errors: {result.last_error}")
```

## 🧪 Node Testing Implementation

Create comprehensive tests in `tests/test_nodes.py`:

```python
"""Tests for node functionality"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from src.nodes import (
    query_analyzer, topic_validator, quiz_generator, 
    answer_validator, score_generator,
    validate_multiple_choice_answer, validate_true_false_answer,
    determine_question_type, get_difficulty_multiplier, get_question_type_bonus,
    calculate_performance_trend, validate_node_prerequisites
)
from src.state import QuizState, create_test_state

class TestNodePrerequisites:
    """Test node prerequisite validation"""
    
    def test_query_analyzer_prerequisites(self):
        """Test query analyzer prerequisites"""
        state = QuizState()
        errors = validate_node_prerequisites(state, "query_analyzer")
        assert "user_input" in str(errors)
        
        state.user_input = "test input"
        errors = validate_node_prerequisites(state, "query_analyzer")
        assert len(errors) == 0
    
    def test_topic_validator_prerequisites(self):
        """Test topic validator prerequisites"""
        state = QuizState()
        errors = validate_node_prerequisites(state, "topic_validator")
        assert "user_input" in str(errors)
    
    def test_quiz_generator_prerequisites(self):
        """Test quiz generator prerequisites"""
        state = QuizState()
        errors = validate_node_prerequisites(state, "quiz_generator")
        assert len(errors) > 0
        
        state.topic = "Test Topic"
        state.topic_validated = True
        errors = validate_node_prerequisites(state, "quiz_generator")
        assert len(errors) == 0

class TestQueryAnalyzer:
    """Test Query Analyzer node"""
    
    @patch('src.nodes.safe_llm_call')
    def test_query_analyzer_success(self, mock_llm_call):
        """Test successful query analysis"""
        # Mock LLM response
        mock_llm_call.return_value = asyncio.Future()
        mock_llm_call.return_value.set_result('{"intent": "start_quiz", "confidence": 0.9, "reasoning": "User wants to start"}')
        
        state = QuizState()
        state.user_input = "I want a quiz about Python"
        
        llm = Mock()
        result = query_analyzer(state, llm)
        
        assert result.user_intent == "start_quiz"
        assert len(result.conversation_history) > 0
        assert result.last_error is None
    
    @patch('src.nodes.safe_llm_call')
    def test_query_analyzer_llm_error(self, mock_llm_call):
        """Test query analyzer with LLM error"""
        mock_llm_call.side_effect = Exception("LLM error")
        
        state = QuizState()
        state.user_input = "test input"
        
        llm = Mock()
        result = query_analyzer(state, llm)
        
        assert result.user_intent == "clarification"
        assert result.last_error is not None
    
    def test_query_analyzer_empty_input(self):
        """Test query analyzer with empty input"""
        state = QuizState()
        state.user_input = ""
        
        llm = Mock()
        result = query_analyzer(state, llm)
        
        assert result.last_error is not None
        assert "Empty user input" in result.last_error

class TestTopicValidator:
    """Test Topic Validator node"""
    
    @patch('src.nodes.safe_llm_call')
    def test_topic_validator_success(self, mock_llm_call):
        """Test successful topic validation"""
        # Mock responses for extraction and validation
        mock_responses = [
            '{"topic": "Python Programming", "confidence": 0.9}',
            '{"is_valid": true, "category": "programming", "difficulty_level": "intermediate"}'
        ]
        mock_llm_call.side_effect = [asyncio.Future() for _ in mock_responses]
        for future, response in zip(mock_llm_call.side_effect, mock_responses):
            future.set_result(response)
        
        state = QuizState()
        state.user_input = "I want to learn Python programming"
        
        llm = Mock()
        result = topic_validator(state, llm)
        
        assert result.topic == "Python Programming"
        assert result.topic_validated is True
        assert result.current_phase == "quiz_active"
        assert result.quiz_active is True
    
    @patch('src.nodes.safe_llm_call')
    def test_topic_validator_invalid_topic(self, mock_llm_call):
        """Test topic validation with invalid topic"""
        mock_responses = [
            '{"topic": "Inappropriate Topic", "confidence": 0.8}',
            '{"is_valid": false, "reason": "Topic not suitable", "suggestions": ["Alternative Topic"]}'
        ]
        mock_llm_call.side_effect = [asyncio.Future() for _ in mock_responses]
        for future, response in zip(mock_llm_call.side_effect, mock_responses):
            future.set_result(response)
        
        state = QuizState()
        state.user_input = "Inappropriate topic request"
        
        llm = Mock()
        result = topic_validator(state, llm)
        
        assert result.topic_validated is False
        assert result.current_phase == "topic_selection"
        assert result.last_error is not None

class TestQuizGenerator:
    """Test Quiz Generator node"""
    
    @patch('src.nodes.safe_llm_call')
    def test_quiz_generator_success(self, mock_llm_call):
        """Test successful question generation"""
        mock_response = '''{
            "question": "What is a Python list?",
            "type": "open_ended",
            "correct_answer": "A mutable sequence of items",
            "explanation": "Lists are fundamental data structures"
        }'''
        mock_llm_call.return_value = asyncio.Future()
        mock_llm_call.return_value.set_result(mock_response)
        
        state = create_test_state()
        
        llm = Mock()
        result = quiz_generator(state, llm)
        
        assert result.current_question == "What is a Python list?"
        assert result.question_type == "open_ended"
        assert result.correct_answer == "A mutable sequence of items"
        assert result.last_error is None
    
    def test_quiz_generator_missing_topic(self):
        """Test quiz generator with missing topic"""
        state = QuizState()
        
        llm = Mock()
        result = quiz_generator(state, llm)
        
        assert result.last_error is not None
        assert "without validated topic" in result.last_error
    
    def test_determine_question_type(self):
        """Test question type determination logic"""
        state = QuizState()
        
        # First question should be multiple choice
        state.total_questions_answered = 0
        assert determine_question_type(state) == "multiple_choice"
        
        # Every third question should be open ended
        state.total_questions_answered = 3
        assert determine_question_type(state) == "open_ended"
        
        # Every fourth question should be true/false
        state.total_questions_answered = 4
        assert determine_question_type(state) == "true_false"

class TestAnswerValidator:
    """Test Answer Validator node"""
    
    def test_validate_multiple_choice_exact_match(self):
        """Test multiple choice validation with exact match"""
        state = create_test_state()
        state.current_answer = "A"
        state.correct_answer = "A"
        state.question_type = "multiple_choice"
        
        result = validate_multiple_choice_answer(state)
        
        assert result["is_correct"] is True
        assert result["score_percentage"] == 100
    
    def test_validate_multiple_choice_letter_mapping(self):
        """Test multiple choice validation with letter mapping"""
        state = create_test_state()
        state.current_answer = "a"
        state.correct_answer = "0"  # First option
        state.question_type = "multiple_choice"
        
        result = validate_multiple_choice_answer(state)
        
        assert result["is_correct"] is True
    
    def test_validate_true_false_answer(self):
        """Test true/false answer validation"""
        state = create_test_state()
        state.current_answer = "yes"
        state.correct_answer = "true"
        state.question_type = "true_false"
        
        result = validate_true_false_answer(state)
        
        assert result["is_correct"] is True
        assert result["score_percentage"] == 100
    
    @patch('src.nodes.safe_llm_call')
    def test_answer_validator_open_ended(self, mock_llm_call):
        """Test answer validator with open-ended question"""
        mock_response = '''{
            "is_correct": true,
            "partial_credit": false,
            "score_percentage": 85,
            "feedback": "Good answer with minor gaps"
        }'''
        mock_llm_call.return_value = asyncio.Future()
        mock_llm_call.return_value.set_result(mock_response)
        
        state = create_test_state()
        state.current_answer = "A list is a collection of items"
        state.question_type = "open_ended"
        
        llm = Mock()
        result = answer_validator(state, llm)
        
        assert result.answer_is_correct is True
        assert result.current_phase == "question_answered"
        assert len(result.user_answers) > 0

class TestScoreGenerator:
    """Test Score Generator node"""
    
    def test_score_generator_correct_answer(self):
        """Test score generation for correct answer"""
        state = create_test_state()
        state.answer_is_correct = True
        state.question_type = "open_ended"
        state.quiz_metadata["difficulty_level"] = "hard"
        state.max_questions = 5
        
        initial_score = state.total_score
        
        llm = Mock()
        result = score_generator(state, llm)
        
        assert result.total_score > initial_score
        assert result.total_questions_answered == 1
        assert result.correct_answers_count == 1
    
    def test_score_generator_incorrect_answer(self):
        """Test score generation for incorrect answer"""
        state = create_test_state()
        state.answer_is_correct = False
        state.max_questions = 5
        
        initial_score = state.total_score
        
        llm = Mock()
        result = score_generator(state, llm)
        
        assert result.total_score == initial_score  # No points added
        assert result.total_questions_answered == 1
        assert result.correct_answers_count == 0
    
    def test_score_generator_quiz_completion(self):
        """Test quiz completion detection"""
        state = create_test_state()
        state.answer_is_correct = True
        state.max_questions = 1
        state.total_questions_answered = 0  # Will become 1 after processing
        
        llm = Mock()
        result = score_generator(state, llm)
        
        assert result.quiz_completed is True
        assert result.quiz_active is False
        assert result.current_phase == "quiz_complete"
    
    def test_get_difficulty_multiplier(self):
        """Test difficulty multiplier calculation"""
        state = QuizState()
        
        state.quiz_metadata["difficulty_level"] = "easy"
        assert get_difficulty_multiplier(state) == 0.8
        
        state.quiz_metadata["difficulty_level"] = "hard"
        assert get_difficulty_multiplier(state) == 1.5
        
        state.quiz_metadata["difficulty_level"] = "unknown"
        assert get_difficulty_multiplier(state) == 1.0
    
    def test_get_question_type_bonus(self):
        """Test question type bonus calculation"""
        assert get_question_type_bonus("multiple_choice") == 0
        assert get_question_type_bonus("open_ended") == 5
        assert get_question_type_bonus("fill_in_blank") == 3
    
    def test_calculate_performance_trend(self):
        """Test performance trend calculation"""
        # Insufficient data
        answers = [{"is_correct": True}]
        trend = calculate_performance_trend(answers)
        assert trend == "insufficient_data"
        
        # Strong performance
        answers = [{"is_correct": True} for _ in range(5)]
        trend = calculate_performance_trend(answers)
        assert trend == "strong"
        
        # Poor performance
        answers = [{"is_correct": False} for _ in range(5)]
        trend = calculate_performance_trend(answers)
        assert trend == "struggling"

if __name__ == "__main__":
    pytest.main([__file__])
```

## 📋 Implementation Checklist

### Core Implementation
- [ ] **All 5 Nodes Implemented**: Query Analyzer, Topic Validator, Quiz Generator, Answer Validator, Score Generator
- [ ] **Error Handling**: Comprehensive error handling with recovery strategies
- [ ] **Async Support**: Proper async/await for LLM calls
- [ ] **State Validation**: Input/output state validation for each node
- [ ] **Logging**: Comprehensive logging throughout node execution

### Testing
- [ ] **Unit Tests**: All node functions tested independently
- [ ] **Integration Tests**: Node chain execution tested
- [ ] **Error Cases**: Error conditions and recovery tested
- [ ] **Edge Cases**: Boundary conditions and invalid inputs tested

### Quality Assurance
- [ ] **Type Checking**: mypy passes without errors
- [ ] **Performance**: Nodes execute within acceptable time limits
- [ ] **Documentation**: All functions have comprehensive docstrings

## ✅ Completion Criteria

Node implementations are complete when:

1. **All 5 nodes implemented** with full functionality
2. **Comprehensive error handling** with recovery mechanisms
3. **Async LLM integration** working reliably
4. **Complete test suite passing** with >90% coverage
5. **State validation** working for all node transitions
6. **Performance acceptable** (<3 seconds per node average)

**Next Step**: Proceed to **[05-edge-logic.md](./05-edge-logic.md)** to implement the routing logic between nodes. 