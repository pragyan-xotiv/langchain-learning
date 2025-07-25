# src/state_middleware.py
from functools import wraps
from typing import Callable, Any
from .quiz_state import QuizState
from .state_validators import validate_state_consistency

def validate_state_middleware(func: Callable[[QuizState], QuizState]) -> Callable[[QuizState], QuizState]:
    """Middleware to validate state before and after node execution"""
    
    @wraps(func)
    def wrapper(state: QuizState) -> QuizState:
        # Pre-execution validation
        pre_errors = validate_state_consistency(state)
        if pre_errors:
            state.last_error = f"Pre-execution validation failed: {pre_errors[0]}"
            return state
        
        # Execute node
        result_state = func(state)
        
        # Post-execution validation
        post_errors = validate_state_consistency(result_state)
        if post_errors:
            result_state.last_error = f"Post-execution validation failed: {post_errors[0]}"
        
        return result_state
    
    return wrapper 