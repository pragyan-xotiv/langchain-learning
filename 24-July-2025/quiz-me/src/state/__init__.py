"""State management for the Interactive Quiz Generator

This package provides centralized state management using Pydantic models.
The QuizState class maintains all application data throughout the user session
and ensures type safety across the workflow.

Components:
- quiz_state: Main QuizState class with comprehensive field validation
- state_validators: State transition validation functions
- state_serializers: Serialization/deserialization utilities
- state_factory: Factory functions for testing and initialization
- state_types: Shared types and enumerations used across state management

Core Classes:
- QuizState: Centralized state management for the quiz application
- StateValidator: Validation utilities for state transitions
- StateSerializer: Serialization and persistence utilities
"""

from .quiz_state import QuizState
from .state_validators import StateValidator, validate_state_transition
from .state_serializers import StateSerializer, serialize_state, deserialize_state
from .state_factory import create_initial_state, create_test_state
from .state_types import QuizPhase, UserIntent, QuestionType

__all__ = [
    # Core state class
    "QuizState",
    
    # Validation utilities
    "StateValidator",
    "validate_state_transition",
    
    # Serialization utilities  
    "StateSerializer",
    "serialize_state",
    "deserialize_state",
    
    # Factory functions
    "create_initial_state",
    "create_test_state",
    
    # Types and enums
    "QuizPhase",
    "UserIntent",
    "QuestionType"
] 