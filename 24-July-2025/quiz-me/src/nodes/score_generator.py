"""Score Generator Node for the Interactive Quiz Generator

This module implements the score generator node that handles scoring, progress 
tracking, and quiz completion logic.
"""

from typing import Dict, Any, Optional, List
import asyncio
import logging
from datetime import datetime
from langchain_openai import ChatOpenAI

from ..state import QuizState
from ..utils import Config

logger = logging.getLogger(__name__)

class ScoreGeneratorError(Exception):
    """Exception raised during score generation"""
    pass

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

def score_generator(state: QuizState, llm: Optional[ChatOpenAI] = None) -> QuizState:
    """
    Calculates scores, tracks progress, and determines quiz completion status.
    
    Args:
        state: Current quiz state with validated answer
        llm: Language model client (optional, not used in this node)
        
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

def validate_score_generator_prerequisites(state: QuizState) -> list[str]:
    """Validate that state meets score generator prerequisites"""
    errors = []
    
    if not hasattr(state, 'answer_is_correct'):
        errors.append("Score generator requires 'answer_is_correct' field")
    
    if not hasattr(state, 'total_questions_answered'):
        errors.append("Score generator requires 'total_questions_answered' field")
    
    return errors 