"""Consolidated prompt formatting functions for the Interactive Quiz Generator

This module contains all functions that format prompts with dynamic data from QuizState.
Each function takes state or specific parameters and returns a formatted prompt string.
"""

from typing import Dict, List, Optional, Any
from .prompt_manager import prompt_manager, PromptType
from ..state import QuizState

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

def format_summary_generation_prompt(state: QuizState) -> str:
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

__all__ = [
    # Helper functions
    "format_conversation_history", 
    "format_previous_questions", 
    "format_question_type_breakdown",
    
    # State-based formatting functions
    "format_intent_classification_prompt", 
    "format_topic_extraction_prompt",
    "format_topic_validation_prompt", 
    "format_question_generation_prompt",
    "format_answer_validation_prompt", 
    "format_clarification_prompt",
    "format_summary_generation_prompt"
] 