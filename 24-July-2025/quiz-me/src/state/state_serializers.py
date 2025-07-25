"""JSON serialization utilities for state persistence

This module provides functions for serializing and deserializing QuizState
objects to and from JSON format for persistence and transport.
"""

import json
from datetime import datetime
from .quiz_state import QuizState

def serialize_state(state: QuizState) -> str:
    """
    Serialize state to JSON string for persistence.
    
    Args:
        state: QuizState object to serialize
        
    Returns:
        JSON string representation
    """
    state_dict = state.model_dump()
    
    # Convert datetime objects to ISO strings
    for key, value in state_dict.items():
        if isinstance(value, datetime):
            state_dict[key] = value.isoformat()
    
    # Add serialization metadata
    state_dict['_serialized_at'] = datetime.now().isoformat()
    state_dict['_version'] = "1.0"
    
    return json.dumps(state_dict, indent=2, default=str)


def deserialize_state(state_json: str) -> QuizState:
    """
    Deserialize state from JSON string.
    
    Args:
        state_json: JSON string representation
        
    Returns:
        QuizState object
        
    Raises:
        ValueError: If deserialization fails
    """
    try:
        state_dict = json.loads(state_json)
        
        # Remove serialization metadata
        state_dict.pop('_serialized_at', None)
        state_dict.pop('_version', None)
        
        # Convert ISO strings back to datetime objects
        for key in ['created_at', 'updated_at']:
            if key in state_dict and isinstance(state_dict[key], str):
                state_dict[key] = datetime.fromisoformat(state_dict[key])
        
        return QuizState(**state_dict)
        
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        raise ValueError(f"Failed to deserialize state: {str(e)}")

__all__ = [
    "serialize_state",
    "deserialize_state"
] 