"""Pytest configuration and shared fixtures for Interactive Quiz Generator tests"""

import pytest
import os
import sys
from unittest.mock import Mock, patch
from typing import Dict, Any

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.state import QuizState
from src.utils import Config

@pytest.fixture
def sample_state():
    """Create a sample QuizState for testing"""
    return QuizState(
        user_input="Test input",
        current_phase="topic_selection"
    )

@pytest.fixture  
def quiz_active_state():
    """Create a QuizState in active quiz phase"""
    state = QuizState(
        user_input="Python programming",
        current_phase="quiz_active"
    )
    # Will be expanded when full QuizState is implemented
    return state

@pytest.fixture
def mock_config():
    """Mock configuration for testing"""
    with patch.object(Config, 'MOCK_LLM_RESPONSES', True):
        with patch.object(Config, 'OPENAI_API_KEY', 'test_key'):
            yield Config

@pytest.fixture
def mock_llm_response():
    """Mock LLM response for testing"""
    return {
        "intent": "start_quiz",
        "confidence": 0.9,
        "reasoning": "User wants to start a quiz"
    }

@pytest.fixture
def sample_conversation_history():
    """Sample conversation history for testing"""
    return [
        {
            "user": "I want a quiz about Python",
            "system": "Great! Let me create a Python quiz for you.",
            "timestamp": "2024-01-01T10:00:00"
        },
        {
            "user": "Let's start", 
            "system": "Here's your first question...",
            "timestamp": "2024-01-01T10:01:00"
        }
    ]

@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment before each test"""
    # Set test environment
    os.environ['ENVIRONMENT'] = 'test'
    os.environ['DEBUG'] = 'false'
    os.environ['MOCK_LLM_RESPONSES'] = 'true'
    
    yield
    
    # Cleanup after test
    test_vars = ['ENVIRONMENT', 'DEBUG', 'MOCK_LLM_RESPONSES']
    for var in test_vars:
        if var in os.environ:
            del os.environ[var]

# Test markers
pytestmark = pytest.mark.asyncio 