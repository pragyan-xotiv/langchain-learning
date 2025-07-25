"""Test package for the Interactive Quiz Generator

This package contains comprehensive tests for all components of the Interactive Quiz Generator.
Tests are organized by module and include unit tests, integration tests, and end-to-end tests.

Test organization:
- test_state.py: State management tests
- test_prompts.py: Prompt template tests  
- test_nodes.py: Node functionality tests
- test_edges.py: Edge logic tests
- test_workflow.py: Workflow integration tests
- test_utils.py: Utility function tests
- test_integration.py: End-to-end tests

Run tests with: pytest
Run with coverage: pytest --cov=src
"""

import pytest
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Test configuration
pytest_plugins = ["pytest_asyncio"] 