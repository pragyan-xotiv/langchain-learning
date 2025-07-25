"""Helper functions and utilities for the Interactive Quiz Generator

This module provides utility functions and configuration management for the application.
It includes environment configuration, validation utilities, caching, and other helper functions.

Implementation includes:
- Configuration management from environment variables
- Text processing utilities
- Input validation functions
- Caching mechanisms
- Performance monitoring utilities
- Security helpers

Core utilities implemented for immediate use in setup phase.
"""

import os
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Config:
    """Application configuration from environment variables"""
    
    # LLM Configuration
    OPENAI_API_KEY: str = os.getenv('OPENAI_API_KEY', '')
    OPENAI_MODEL: str = os.getenv('OPENAI_MODEL', 'gpt-4')
    OPENAI_TEMPERATURE: float = float(os.getenv('OPENAI_TEMPERATURE', '0.7'))
    OPENAI_MAX_TOKENS: int = int(os.getenv('OPENAI_MAX_TOKENS', '1000'))
    
    # App Configuration
    APP_TITLE: str = os.getenv('APP_TITLE', 'Interactive Quiz Generator')
    MAX_QUESTIONS_DEFAULT: int = int(os.getenv('MAX_QUESTIONS_DEFAULT', '10'))
    SESSION_TIMEOUT: int = int(os.getenv('SESSION_TIMEOUT', '1800'))
    DEBUG: bool = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Gradio Configuration
    GRADIO_SERVER_NAME: str = os.getenv('GRADIO_SERVER_NAME', '0.0.0.0')
    GRADIO_SERVER_PORT: int = int(os.getenv('GRADIO_SERVER_PORT', '7860'))
    GRADIO_SHARE: bool = os.getenv('GRADIO_SHARE', 'False').lower() == 'true'
    
    # Optional Features
    REDIS_URL: Optional[str] = os.getenv('REDIS_URL')
    DATABASE_URL: Optional[str] = os.getenv('DATABASE_URL')
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    
    # Development Settings
    ENVIRONMENT: str = os.getenv('ENVIRONMENT', 'development')
    ENABLE_CACHING: bool = os.getenv('ENABLE_CACHING', 'True').lower() == 'true'
    MOCK_LLM_RESPONSES: bool = os.getenv('MOCK_LLM_RESPONSES', 'False').lower() == 'true'
    
    @classmethod
    def validate_required(cls) -> None:
        """Validate that required environment variables are set"""
        required_vars = ['OPENAI_API_KEY']
        missing_vars = [var for var in required_vars if not getattr(cls, var)]
        
        if missing_vars:
            logger.warning(f"Missing required environment variables: {missing_vars}")
            if cls.ENVIRONMENT == 'production':
                raise ValueError(f"Missing required environment variables: {missing_vars}")
    
    @classmethod
    def log_configuration(cls) -> None:
        """Log current configuration (excluding sensitive data)"""
        logger.info("=== Interactive Quiz Generator Configuration ===")
        logger.info(f"Environment: {cls.ENVIRONMENT}")
        logger.info(f"App Title: {cls.APP_TITLE}")
        logger.info(f"OpenAI Model: {cls.OPENAI_MODEL}")
        logger.info(f"Server Port: {cls.GRADIO_SERVER_PORT}")
        logger.info(f"Debug Mode: {cls.DEBUG}")
        logger.info(f"Caching Enabled: {cls.ENABLE_CACHING}")
        api_key_status = "✅ Set" if cls.OPENAI_API_KEY else "❌ Missing"
        logger.info(f"OpenAI API Key: {api_key_status}")

# Validate configuration on import
try:
    Config.validate_required()
    if Config.DEBUG:
        Config.log_configuration()
except ValueError as e:
    logger.error(f"Configuration validation failed: {e}")
    # Don't raise in development mode to allow setup to continue

# TODO: Add more utility functions as needed
# TODO: Implement caching mechanisms
# TODO: Add text processing utilities
# TODO: Add validation functions
# TODO: Add performance monitoring utilities

def validate_environment_setup() -> Dict[str, bool]:
    """
    Validate that the development environment is properly set up.
    
    Returns:
        Dict with validation results for different components
    """
    results = {
        'python_version': True,  # We're running Python if we get here
        'openai_api_key': bool(Config.OPENAI_API_KEY),
        'environment_file': os.path.exists('.env'),
        'requirements_file': os.path.exists('requirements.txt'),
        'src_directory': os.path.exists('src'),
        'tests_directory': os.path.exists('tests'),
    }
    
    return results

def format_validation_results(results: Dict[str, bool]) -> str:
    """Format validation results for display"""
    lines = ["🔍 Environment Validation Results:"]
    
    for component, status in results.items():
        status_icon = "✅" if status else "❌"
        component_name = component.replace('_', ' ').title()
        lines.append(f"  {status_icon} {component_name}")
    
    all_passed = all(results.values())
    summary = "🎉 All checks passed!" if all_passed else "⚠️  Some checks failed"
    lines.append(f"\n{summary}")
    
    return "\n".join(lines)

if __name__ == "__main__":
    # Quick validation when run directly
    results = validate_environment_setup()
    print(format_validation_results(results)) 