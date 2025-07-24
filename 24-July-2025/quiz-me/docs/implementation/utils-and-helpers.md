# Utilities and Helpers Implementation

## 🎯 Overview

This guide implements utility functions and helper classes that support the Interactive Quiz Generator application. These utilities provide common functionality used across multiple components.

## 🏗️ Core Utilities Implementation

Enhance the existing `src/utils.py` with comprehensive utilities:

```python
"""Utility functions and helper classes for the Interactive Quiz Generator"""

import os
import re
import json
import logging
import hashlib
import asyncio
from typing import Dict, List, Any, Optional, Union, Callable, TypeVar, Generic
from datetime import datetime, timedelta
from functools import wraps, lru_cache
from dataclasses import dataclass
from enum import Enum
import time
import uuid
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# === CONFIGURATION MANAGEMENT ===

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
    
    # Performance Settings
    MAX_RETRY_ATTEMPTS: int = int(os.getenv('MAX_RETRY_ATTEMPTS', '3'))
    RETRY_DELAY: float = float(os.getenv('RETRY_DELAY', '1.0'))
    CACHE_TTL: int = int(os.getenv('CACHE_TTL', '3600'))  # 1 hour
    
    @classmethod
    def validate_required(cls) -> None:
        """Validate that required environment variables are set"""
        required_vars = ['OPENAI_API_KEY'] if not cls.MOCK_LLM_RESPONSES else []
        missing_vars = [var for var in required_vars if not getattr(cls, var)]
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {missing_vars}")
    
    @classmethod
    def get_all_config(cls) -> Dict[str, Any]:
        """Get all configuration as dictionary"""
        return {
            key: getattr(cls, key) 
            for key in dir(cls) 
            if not key.startswith('_') and not callable(getattr(cls, key))
        }
    
    @classmethod
    def update_config(cls, updates: Dict[str, Any]) -> None:
        """Update configuration with new values"""
        for key, value in updates.items():
            if hasattr(cls, key):
                setattr(cls, key, value)
            else:
                logger.warning(f"Unknown configuration key: {key}")

# === TEXT PROCESSING UTILITIES ===

class TextProcessor:
    """Utilities for text processing and cleaning"""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize text input"""
        if not text:
            return ""
        
        # Basic cleaning
        text = text.strip()
        text = re.sub(r'\s+', ' ', text)  # Multiple spaces to single
        text = re.sub(r'\n+', '\n', text)  # Multiple newlines to single
        
        return text
    
    @staticmethod
    def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
        """Extract keywords from text using simple frequency analysis"""
        if not text:
            return []
        
        # Remove common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have',
            'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
            'may', 'might', 'can', 'this', 'that', 'these', 'those', 'i', 'you',
            'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'
        }
        
        # Extract words
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        
        # Filter stop words and count frequency
        word_freq = {}
        for word in words:
            if word not in stop_words:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Sort by frequency and return top keywords
        keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in keywords[:max_keywords]]
    
    @staticmethod
    def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
        """Truncate text to specified length"""
        if len(text) <= max_length:
            return text
        
        return text[:max_length - len(suffix)] + suffix
    
    @staticmethod
    def similarity_score(text1: str, text2: str) -> float:
        """Calculate basic similarity score between two texts"""
        if not text1 or not text2:
            return 0.0
        
        # Simple Jaccard similarity using word sets
        words1 = set(re.findall(r'\b\w+\b', text1.lower()))
        words2 = set(re.findall(r'\b\w+\b', text2.lower()))
        
        if not words1 and not words2:
            return 1.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    @staticmethod
    def contains_question_indicators(text: str) -> bool:
        """Check if text contains question indicators"""
        question_patterns = [
            r'\bwhat\b', r'\bwhere\b', r'\bwhen\b', r'\bwhy\b', r'\bhow\b',
            r'\bwhich\b', r'\bwho\b', r'\?', r'\bcan\s+you\b', r'\bis\s+it\b'
        ]
        
        text_lower = text.lower()
        return any(re.search(pattern, text_lower) for pattern in question_patterns)

# === VALIDATION UTILITIES ===

class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass

class Validator:
    """Input validation utilities"""
    
    @staticmethod
    def validate_topic(topic: str) -> Dict[str, Any]:
        """Validate quiz topic"""
        if not topic or not topic.strip():
            return {"valid": False, "error": "Topic cannot be empty"}
        
        topic = topic.strip()
        
        # Length validation
        if len(topic) < 3:
            return {"valid": False, "error": "Topic too short (minimum 3 characters)"}
        
        if len(topic) > 100:
            return {"valid": False, "error": "Topic too long (maximum 100 characters)"}
        
        # Content validation
        if not re.match(r'^[a-zA-Z0-9\s\-_.,:()]+$', topic):
            return {"valid": False, "error": "Topic contains invalid characters"}
        
        # Inappropriate content check (basic)
        inappropriate_terms = ['hate', 'violence', 'inappropriate', 'nsfw']
        if any(term in topic.lower() for term in inappropriate_terms):
            return {"valid": False, "error": "Topic contains inappropriate content"}
        
        return {"valid": True, "cleaned_topic": topic}
    
    @staticmethod
    def validate_user_answer(answer: str, question_type: str = "open_ended") -> Dict[str, Any]:
        """Validate user answer"""
        if not answer or not answer.strip():
            return {"valid": False, "error": "Answer cannot be empty"}
        
        answer = answer.strip()
        
        # Length validation
        if len(answer) > 1000:
            return {"valid": False, "error": "Answer too long (maximum 1000 characters)"}
        
        # Type-specific validation
        if question_type == "multiple_choice":
            # Should be A, B, C, D or similar
            if not re.match(r'^[A-Da-d]$|^[1-4]$|^(option\s+)?[A-Da-d]$', answer.lower()):
                # If not exact match, check if answer might be valid anyway
                pass  # Let it through for fuzzy matching
        
        elif question_type == "true_false":
            # Should be true/false or similar
            valid_answers = ['true', 'false', 't', 'f', 'yes', 'no', 'y', 'n', '1', '0']
            if answer.lower() not in valid_answers:
                # Let it through for fuzzy matching
                pass
        
        return {"valid": True, "cleaned_answer": answer}
    
    @staticmethod
    def validate_json_response(response: str) -> Dict[str, Any]:
        """Validate and parse JSON response"""
        if not response or not response.strip():
            return {"valid": False, "error": "Empty response"}
        
        try:
            parsed = json.loads(response)
            return {"valid": True, "data": parsed}
        except json.JSONDecodeError as e:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                try:
                    parsed = json.loads(json_match.group())
                    return {"valid": True, "data": parsed}
                except json.JSONDecodeError:
                    pass
            
            return {"valid": False, "error": f"Invalid JSON: {str(e)}", "raw_response": response}

# === CACHING UTILITIES ===

T = TypeVar('T')

class SimpleCache(Generic[T]):
    """Simple in-memory cache with TTL support"""
    
    def __init__(self, ttl: int = 3600):
        """Initialize cache with TTL in seconds"""
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl = ttl
    
    def get(self, key: str) -> Optional[T]:
        """Get item from cache"""
        if key not in self.cache:
            return None
        
        entry = self.cache[key]
        if time.time() > entry['expires']:
            del self.cache[key]
            return None
        
        return entry['value']
    
    def set(self, key: str, value: T) -> None:
        """Set item in cache"""
        self.cache[key] = {
            'value': value,
            'expires': time.time() + self.ttl,
            'created': time.time()
        }
    
    def delete(self, key: str) -> bool:
        """Delete item from cache"""
        if key in self.cache:
            del self.cache[key]
            return True
        return False
    
    def clear(self) -> None:
        """Clear all cache entries"""
        self.cache.clear()
    
    def size(self) -> int:
        """Get cache size"""
        return len(self.cache)
    
    def cleanup_expired(self) -> int:
        """Clean up expired entries and return count"""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self.cache.items()
            if current_time > entry['expires']
        ]
        
        for key in expired_keys:
            del self.cache[key]
        
        return len(expired_keys)

# Global cache instances
response_cache = SimpleCache[str](ttl=Config.CACHE_TTL)
topic_cache = SimpleCache[Dict[str, Any]](ttl=Config.CACHE_TTL)

def cached_function(cache_key_func: Callable = None, ttl: int = None):
    """Decorator for caching function results"""
    def decorator(func):
        cache = SimpleCache(ttl or Config.CACHE_TTL)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if cache_key_func:
                key = cache_key_func(*args, **kwargs)
            else:
                key = f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # Try to get from cache
            result = cache.get(key)
            if result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(key, result)
            logger.debug(f"Cache miss for {func.__name__}, result cached")
            
            return result
        
        return wrapper
    return decorator

# === RETRY UTILITIES ===

def retry_on_exception(
    exceptions: Union[Exception, tuple] = Exception,
    max_attempts: int = None,
    delay: float = None,
    exponential_backoff: bool = True
):
    """Decorator for retrying functions on exception"""
    
    max_attempts = max_attempts or Config.MAX_RETRY_ATTEMPTS
    delay = delay or Config.RETRY_DELAY
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts - 1:
                        logger.error(f"{func.__name__} failed after {max_attempts} attempts: {str(e)}")
                        raise
                    
                    wait_time = delay * (2 ** attempt if exponential_backoff else 1)
                    logger.warning(f"{func.__name__} attempt {attempt + 1} failed: {str(e)}, retrying in {wait_time}s")
                    time.sleep(wait_time)
            
            raise last_exception
        
        return wrapper
    return decorator

async def async_retry_on_exception(
    exceptions: Union[Exception, tuple] = Exception,
    max_attempts: int = None,
    delay: float = None,
    exponential_backoff: bool = True
):
    """Async version of retry decorator"""
    
    max_attempts = max_attempts or Config.MAX_RETRY_ATTEMPTS  
    delay = delay or Config.RETRY_DELAY
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts - 1:
                        logger.error(f"{func.__name__} failed after {max_attempts} attempts: {str(e)}")
                        raise
                    
                    wait_time = delay * (2 ** attempt if exponential_backoff else 1)
                    logger.warning(f"{func.__name__} attempt {attempt + 1} failed: {str(e)}, retrying in {wait_time}s")
                    await asyncio.sleep(wait_time)
            
            raise last_exception
        
        return wrapper
    return decorator

# === PERFORMANCE MONITORING UTILITIES ===

class PerformanceMonitor:
    """Monitor function performance and resource usage"""
    
    def __init__(self):
        self.metrics: Dict[str, List[Dict[str, Any]]] = {}
    
    def record_execution(self, func_name: str, duration: float, success: bool, **metadata):
        """Record function execution metrics"""
        if func_name not in self.metrics:
            self.metrics[func_name] = []
        
        self.metrics[func_name].append({
            'duration': duration,
            'success': success,
            'timestamp': time.time(),
            **metadata
        })
        
        # Keep only last 100 records per function
        if len(self.metrics[func_name]) > 100:
            self.metrics[func_name] = self.metrics[func_name][-100:]
    
    def get_stats(self, func_name: str) -> Dict[str, Any]:
        """Get performance statistics for a function"""
        if func_name not in self.metrics:
            return {"error": "No metrics found"}
        
        records = self.metrics[func_name]
        durations = [r['duration'] for r in records]
        successes = sum(1 for r in records if r['success'])
        
        return {
            "total_calls": len(records),
            "success_rate": successes / len(records) * 100,
            "avg_duration": sum(durations) / len(durations),
            "min_duration": min(durations),
            "max_duration": max(durations),
            "recent_calls": records[-10:]
        }
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all monitored functions"""
        return {func_name: self.get_stats(func_name) for func_name in self.metrics.keys()}

# Global performance monitor
performance_monitor = PerformanceMonitor()

def monitor_performance(func):
    """Decorator to monitor function performance"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        success = False
        error = None
        
        try:
            result = func(*args, **kwargs)
            success = True
            return result
        except Exception as e:
            error = str(e)
            raise
        finally:
            duration = time.time() - start_time
            performance_monitor.record_execution(
                func_name=func.__name__,
                duration=duration,
                success=success,
                error=error
            )
    
    return wrapper

async def monitor_async_performance(func):
    """Async version of performance monitor decorator"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        success = False
        error = None
        
        try:
            result = await func(*args, **kwargs)
            success = True
            return result
        except Exception as e:
            error = str(e)
            raise
        finally:
            duration = time.time() - start_time
            performance_monitor.record_execution(
                func_name=func.__name__,
                duration=duration,
                success=success,
                error=error
            )
    
    return wrapper

# === FILE UTILITIES ===

class FileUtils:
    """File and directory utilities"""
    
    @staticmethod
    def ensure_directory(path: str) -> None:
        """Ensure directory exists, create if it doesn't"""
        os.makedirs(path, exist_ok=True)
    
    @staticmethod
    def safe_write_file(filepath: str, content: str, encoding: str = 'utf-8') -> bool:
        """Safely write content to file with error handling"""
        try:
            # Ensure directory exists
            directory = os.path.dirname(filepath)
            if directory:
                FileUtils.ensure_directory(directory)
            
            # Write file
            with open(filepath, 'w', encoding=encoding) as f:
                f.write(content)
            
            return True
        except Exception as e:
            logger.error(f"Failed to write file {filepath}: {str(e)}")
            return False
    
    @staticmethod
    def safe_read_file(filepath: str, encoding: str = 'utf-8') -> Optional[str]:
        """Safely read file content with error handling"""
        try:
            with open(filepath, 'r', encoding=encoding) as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to read file {filepath}: {str(e)}")
            return None
    
    @staticmethod
    def get_file_size(filepath: str) -> Optional[int]:
        """Get file size in bytes"""
        try:
            return os.path.getsize(filepath)
        except Exception:
            return None
    
    @staticmethod
    def cleanup_old_files(directory: str, max_age_days: int = 7) -> int:
        """Clean up files older than specified days"""
        if not os.path.exists(directory):
            return 0
        
        cutoff_time = time.time() - (max_age_days * 24 * 3600)
        removed_count = 0
        
        try:
            for filename in os.listdir(directory):
                filepath = os.path.join(directory, filename)
                if os.path.isfile(filepath) and os.path.getmtime(filepath) < cutoff_time:
                    os.remove(filepath)
                    removed_count += 1
        except Exception as e:
            logger.error(f"Error cleaning up files in {directory}: {str(e)}")
        
        return removed_count

# === SECURITY UTILITIES ===

class SecurityUtils:
    """Security and hashing utilities"""
    
    @staticmethod
    def generate_session_id() -> str:
        """Generate secure session ID"""
        return str(uuid.uuid4())
    
    @staticmethod
    def hash_string(text: str, algorithm: str = 'sha256') -> str:
        """Hash string using specified algorithm"""
        hash_obj = hashlib.new(algorithm)
        hash_obj.update(text.encode('utf-8'))
        return hash_obj.hexdigest()
    
    @staticmethod
    def sanitize_input(text: str) -> str:
        """Sanitize user input to prevent injection attacks"""
        if not text:
            return ""
        
        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>"\']', '', text)
        
        # Limit length
        sanitized = sanitized[:1000]
        
        return sanitized.strip()
    
    @staticmethod
    def is_safe_filename(filename: str) -> bool:
        """Check if filename is safe (no path traversal)"""
        if not filename:
            return False
        
        # Check for path traversal attempts
        if '..' in filename or '/' in filename or '\\' in filename:
            return False
        
        # Check for reserved names (Windows)
        reserved_names = ['CON', 'PRN', 'AUX', 'NUL'] + [f'COM{i}' for i in range(1, 10)] + [f'LPT{i}' for i in range(1, 10)]
        if filename.upper() in reserved_names:
            return False
        
        return True

# === DATETIME UTILITIES ===

class DateTimeUtils:
    """Date and time utilities"""
    
    @staticmethod
    def format_duration(seconds: float) -> str:
        """Format duration in human-readable format"""
        if seconds < 60:
            return f"{seconds:.1f} seconds"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f} minutes"
        else:
            hours = seconds / 3600
            return f"{hours:.1f} hours"
    
    @staticmethod
    def format_timestamp(timestamp: Optional[datetime] = None, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
        """Format timestamp in specified format"""
        if timestamp is None:
            timestamp = datetime.now()
        return timestamp.strftime(format_str)
    
    @staticmethod
    def parse_timestamp(timestamp_str: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> Optional[datetime]:
        """Parse timestamp string"""
        try:
            return datetime.strptime(timestamp_str, format_str)
        except ValueError:
            return None
    
    @staticmethod
    def is_expired(timestamp: datetime, ttl_seconds: int) -> bool:
        """Check if timestamp is expired"""
        return datetime.now() > timestamp + timedelta(seconds=ttl_seconds)

# === TESTING UTILITIES ===

class TestUtils:
    """Utilities for testing"""
    
    @staticmethod
    def create_mock_llm_response(response_type: str = "intent_classification") -> str:
        """Create mock LLM responses for testing"""
        mock_responses = {
            "intent_classification": '{"intent": "start_quiz", "confidence": 0.9, "reasoning": "User wants to start"}',
            "topic_extraction": '{"topic": "Python Programming", "confidence": 0.9, "specificity_level": "specific"}',
            "topic_validation": '{"is_valid": true, "category": "programming", "difficulty_level": "intermediate", "estimated_questions": 10}',
            "question_generation": '{"question": "What is a Python list?", "type": "open_ended", "correct_answer": "A mutable sequence", "explanation": "Lists store multiple items"}',
            "answer_validation": '{"is_correct": true, "score_percentage": 100, "feedback": "Correct answer!"}'
        }
        
        return mock_responses.get(response_type, '{"error": "Unknown response type"}')
    
    @staticmethod
    def create_test_data(data_type: str) -> Dict[str, Any]:
        """Create test data for various components"""
        test_data = {
            "quiz_state": {
                "topic": "Test Topic",
                "topic_validated": True,
                "current_phase": "quiz_active",
                "quiz_active": True,
                "current_question": "Test question?",
                "question_type": "open_ended",
                "correct_answer": "Test answer"
            },
            "conversation_history": [
                {"user": "Hello", "system": "Hi there!", "timestamp": datetime.now().isoformat()},
                {"user": "Start quiz", "system": "What topic?", "timestamp": datetime.now().isoformat()}
            ],
            "user_answers": [
                {
                    "question": "Test question",
                    "user_answer": "User response",
                    "correct_answer": "Correct response",
                    "is_correct": True,
                    "timestamp": datetime.now().isoformat()
                }
            ]
        }
        
        return test_data.get(data_type, {})

# Initialize configuration validation
try:
    Config.validate_required()
    logger.info("Configuration validated successfully")
except ValueError as e:
    logger.error(f"Configuration validation failed: {str(e)}")
    if Config.ENVIRONMENT == 'production':
        raise

# Export commonly used utilities
__all__ = [
    'Config', 'TextProcessor', 'Validator', 'SimpleCache', 'PerformanceMonitor',
    'FileUtils', 'SecurityUtils', 'DateTimeUtils', 'TestUtils',
    'cached_function', 'retry_on_exception', 'monitor_performance',
    'response_cache', 'topic_cache', 'performance_monitor'
]

if __name__ == "__main__":
    # Test utilities
    print("Testing utilities...")
    
    # Test text processing
    processor = TextProcessor()
    print(f"Keywords: {processor.extract_keywords('Python programming is great for machine learning')}")
    
    # Test validation
    validator = Validator()
    print(f"Topic validation: {validator.validate_topic('Python Programming')}")
    
    # Test cache
    cache = SimpleCache(ttl=60)
    cache.set("test", "value")
    print(f"Cache test: {cache.get('test')}")
    
    # Test performance monitor
    @monitor_performance
    def test_function():
        time.sleep(0.1)
        return "test"
    
    test_function()
    print(f"Performance stats: {performance_monitor.get_stats('test_function')}")
    
    print("All utilities tested successfully!")
```

## 🧪 Utilities Testing

Create comprehensive tests in `tests/test_utils.py`:

```python
"""Tests for utility functions"""

import pytest
import time
import tempfile
import os
from datetime import datetime, timedelta
from unittest.mock import patch, Mock

from src.utils import (
    Config, TextProcessor, Validator, SimpleCache, PerformanceMonitor,
    FileUtils, SecurityUtils, DateTimeUtils, TestUtils,
    cached_function, retry_on_exception, monitor_performance,
    response_cache, topic_cache, performance_monitor
)

class TestConfig:
    """Test configuration management"""
    
    def test_config_validation_success(self):
        """Test successful configuration validation"""
        with patch.object(Config, 'OPENAI_API_KEY', 'test_key'):
            Config.validate_required()  # Should not raise
    
    def test_config_validation_failure(self):
        """Test configuration validation failure"""
        with patch.object(Config, 'OPENAI_API_KEY', ''):
            with patch.object(Config, 'MOCK_LLM_RESPONSES', False):
                with pytest.raises(ValueError):
                    Config.validate_required()
    
    def test_get_all_config(self):
        """Test getting all configuration"""
        config = Config.get_all_config()
        assert 'APP_TITLE' in config
        assert 'OPENAI_MODEL' in config
    
    def test_update_config(self):
        """Test updating configuration"""
        original_title = Config.APP_TITLE
        Config.update_config({'APP_TITLE': 'Test Title'})
        assert Config.APP_TITLE == 'Test Title'
        
        # Restore original
        Config.APP_TITLE = original_title

class TestTextProcessor:
    """Test text processing utilities"""
    
    def test_clean_text(self):
        """Test text cleaning"""
        dirty_text = "  This   has    multiple\n\n\nspaces  "
        clean = TextProcessor.clean_text(dirty_text)
        assert clean == "This has multiple\nspaces"
    
    def test_extract_keywords(self):
        """Test keyword extraction"""
        text = "Python programming is great for machine learning and data science"
        keywords = TextProcessor.extract_keywords(text, max_keywords=5)
        
        assert len(keywords) <= 5
        assert 'python' in keywords
        assert 'programming' in keywords
        # Stop words should be filtered out
        assert 'is' not in keywords
        assert 'and' not in keywords
    
    def test_truncate_text(self):
        """Test text truncation"""
        long_text = "This is a very long text that should be truncated"
        truncated = TextProcessor.truncate_text(long_text, max_length=20)
        
        assert len(truncated) <= 20
        assert truncated.endswith("...")
    
    def test_similarity_score(self):
        """Test text similarity calculation"""
        text1 = "Python programming"
        text2 = "Python coding"
        text3 = "Java development"
        
        # Similar texts should have higher score
        score1 = TextProcessor.similarity_score(text1, text2)
        score2 = TextProcessor.similarity_score(text1, text3)
        
        assert score1 > score2
        assert 0 <= score1 <= 1
        assert 0 <= score2 <= 1
    
    def test_contains_question_indicators(self):
        """Test question indicator detection"""
        question = "What is Python programming?"
        statement = "Python is a programming language"
        
        assert TextProcessor.contains_question_indicators(question) is True
        assert TextProcessor.contains_question_indicators(statement) is False

class TestValidator:
    """Test validation utilities"""
    
    def test_validate_topic_success(self):
        """Test successful topic validation"""
        result = Validator.validate_topic("Python Programming")
        assert result["valid"] is True
        assert result["cleaned_topic"] == "Python Programming"
    
    def test_validate_topic_failure(self):
        """Test topic validation failures"""
        # Empty topic
        result = Validator.validate_topic("")
        assert result["valid"] is False
        
        # Too short
        result = Validator.validate_topic("AB")
        assert result["valid"] is False
        
        # Too long
        result = Validator.validate_topic("A" * 101)
        assert result["valid"] is False
        
        # Invalid characters
        result = Validator.validate_topic("Topic<script>")
        assert result["valid"] is False
    
    def test_validate_user_answer(self):
        """Test user answer validation"""
        # Valid answer
        result = Validator.validate_user_answer("This is a valid answer")
        assert result["valid"] is True
        
        # Empty answer
        result = Validator.validate_user_answer("")
        assert result["valid"] is False
        
        # Too long answer
        result = Validator.validate_user_answer("A" * 1001)
        assert result["valid"] is False
    
    def test_validate_json_response(self):
        """Test JSON response validation"""
        # Valid JSON
        result = Validator.validate_json_response('{"key": "value"}')
        assert result["valid"] is True
        assert result["data"]["key"] == "value"
        
        # Invalid JSON
        result = Validator.validate_json_response('{"invalid": json}')
        assert result["valid"] is False
        
        # JSON embedded in text
        result = Validator.validate_json_response('Here is JSON: {"key": "value"} end')
        assert result["valid"] is True
        assert result["data"]["key"] == "value"

class TestSimpleCache:
    """Test caching utilities"""
    
    def test_cache_basic_operations(self):
        """Test basic cache operations"""
        cache = SimpleCache(ttl=60)
        
        # Test set and get
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        
        # Test non-existent key
        assert cache.get("nonexistent") is None
        
        # Test size
        assert cache.size() == 1
    
    def test_cache_expiration(self):
        """Test cache expiration"""
        cache = SimpleCache(ttl=1)  # 1 second TTL
        
        cache.set("key", "value")
        assert cache.get("key") == "value"
        
        # Wait for expiration
        time.sleep(1.1)
        assert cache.get("key") is None
    
    def test_cache_cleanup(self):
        """Test cache cleanup"""
        cache = SimpleCache(ttl=1)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        time.sleep(1.1)  # Wait for expiration
        
        cleaned = cache.cleanup_expired()
        assert cleaned == 2
        assert cache.size() == 0

class TestCachedFunction:
    """Test cached function decorator"""
    
    def test_cached_function_decorator(self):
        """Test cached function decorator"""
        call_count = 0
        
        @cached_function(ttl=60)
        def test_func(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        # First call
        result1 = test_func(5)
        assert result1 == 10
        assert call_count == 1
        
        # Second call should use cache
        result2 = test_func(5)
        assert result2 == 10
        assert call_count == 1  # Should not increment
        
        # Different argument should call function
        result3 = test_func(6)
        assert result3 == 12
        assert call_count == 2

class TestRetryDecorator:
    """Test retry decorator"""
    
    def test_retry_success(self):
        """Test retry decorator with eventual success"""
        attempt_count = 0
        
        @retry_on_exception(max_attempts=3, delay=0.1)
        def flaky_function():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 2:
                raise ValueError("Temporary error")
            return "success"
        
        result = flaky_function()
        assert result == "success"
        assert attempt_count == 2
    
    def test_retry_failure(self):
        """Test retry decorator with persistent failure"""
        @retry_on_exception(max_attempts=2, delay=0.1)
        def failing_function():
            raise ValueError("Persistent error")
        
        with pytest.raises(ValueError):
            failing_function()

class TestPerformanceMonitor:
    """Test performance monitoring"""
    
    def test_performance_monitoring(self):
        """Test performance monitoring decorator"""
        monitor = PerformanceMonitor()
        
        @monitor_performance
        def test_function():
            time.sleep(0.1)
            return "result"
        
        result = test_function()
        assert result == "result"
        
        stats = performance_monitor.get_stats("test_function")
        assert stats["total_calls"] == 1
        assert stats["success_rate"] == 100.0
        assert stats["avg_duration"] > 0.1

class TestFileUtils:
    """Test file utilities"""
    
    def test_safe_write_read_file(self):
        """Test safe file operations"""
        with tempfile.TemporaryDirectory() as temp_dir:
            filepath = os.path.join(temp_dir, "test.txt")
            content = "Test content"
            
            # Test write
            success = FileUtils.safe_write_file(filepath, content)
            assert success is True
            
            # Test read
            read_content = FileUtils.safe_read_file(filepath)
            assert read_content == content
    
    def test_ensure_directory(self):
        """Test directory creation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            new_dir = os.path.join(temp_dir, "new", "nested", "directory")
            
            FileUtils.ensure_directory(new_dir)
            assert os.path.exists(new_dir)
    
    def test_get_file_size(self):
        """Test file size calculation"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_path = f.name
        
        try:
            size = FileUtils.get_file_size(temp_path)
            assert size > 0
        finally:
            os.unlink(temp_path)

class TestSecurityUtils:
    """Test security utilities"""
    
    def test_generate_session_id(self):
        """Test session ID generation"""
        id1 = SecurityUtils.generate_session_id()
        id2 = SecurityUtils.generate_session_id()
        
        assert len(id1) > 0
        assert id1 != id2  # Should be unique
    
    def test_hash_string(self):
        """Test string hashing"""
        text = "test string"
        hash1 = SecurityUtils.hash_string(text)
        hash2 = SecurityUtils.hash_string(text)
        
        assert hash1 == hash2  # Same input should produce same hash
        assert len(hash1) == 64  # SHA256 produces 64-char hex string
    
    def test_sanitize_input(self):
        """Test input sanitization"""
        dangerous_input = '<script>alert("xss")</script>'
        sanitized = SecurityUtils.sanitize_input(dangerous_input)
        
        assert '<' not in sanitized
        assert '>' not in sanitized
        assert 'script' in sanitized  # Content should remain, just tags removed
    
    def test_is_safe_filename(self):
        """Test filename safety check"""
        assert SecurityUtils.is_safe_filename("safe_file.txt") is True
        assert SecurityUtils.is_safe_filename("../../../etc/passwd") is False
        assert SecurityUtils.is_safe_filename("CON") is False  # Windows reserved
        assert SecurityUtils.is_safe_filename("") is False

class TestDateTimeUtils:
    """Test datetime utilities"""
    
    def test_format_duration(self):
        """Test duration formatting"""
        assert "seconds" in DateTimeUtils.format_duration(30)
        assert "minutes" in DateTimeUtils.format_duration(120)
        assert "hours" in DateTimeUtils.format_duration(7200)
    
    def test_format_timestamp(self):
        """Test timestamp formatting"""
        now = datetime.now()
        formatted = DateTimeUtils.format_timestamp(now)
        
        assert len(formatted) > 0
        assert str(now.year) in formatted
    
    def test_parse_timestamp(self):
        """Test timestamp parsing"""
        timestamp_str = "2023-12-25 15:30:45"
        parsed = DateTimeUtils.parse_timestamp(timestamp_str)
        
        assert parsed is not None
        assert parsed.year == 2023
        assert parsed.month == 12
        assert parsed.day == 25
    
    def test_is_expired(self):
        """Test expiration check"""
        old_time = datetime.now() - timedelta(hours=2)
        recent_time = datetime.now() - timedelta(minutes=5)
        
        assert DateTimeUtils.is_expired(old_time, 3600) is True  # 1 hour TTL
        assert DateTimeUtils.is_expired(recent_time, 3600) is False

class TestTestUtils:
    """Test testing utilities"""
    
    def test_create_mock_llm_response(self):
        """Test mock LLM response creation"""
        response = TestUtils.create_mock_llm_response("intent_classification")
        
        assert len(response) > 0
        assert "intent" in response
        # Should be valid JSON
        import json
        parsed = json.loads(response)
        assert "intent" in parsed
    
    def test_create_test_data(self):
        """Test test data creation"""
        quiz_data = TestUtils.create_test_data("quiz_state")
        
        assert "topic" in quiz_data
        assert "topic_validated" in quiz_data
        assert quiz_data["topic"] == "Test Topic"

if __name__ == "__main__":
    pytest.main([__file__])
```

## 📋 Implementation Checklist

### Core Utilities
- [ ] **Configuration Management**: Environment-based config with validation
- [ ] **Text Processing**: Cleaning, keyword extraction, similarity scoring
- [ ] **Input Validation**: Topic, answer, and JSON response validation
- [ ] **Caching System**: TTL-based caching with cleanup
- [ ] **Retry Logic**: Exponential backoff retry decorator

### Advanced Features
- [ ] **Performance Monitoring**: Function execution tracking
- [ ] **File Operations**: Safe file I/O with error handling
- [ ] **Security Utilities**: Input sanitization and hashing
- [ ] **DateTime Utilities**: Formatting and expiration checking
- [ ] **Testing Utilities**: Mock data and response generation

### Testing
- [ ] **Unit Tests**: All utility functions tested independently
- [ ] **Integration Tests**: Utility interaction with other components
- [ ] **Edge Cases**: Error conditions and boundary cases tested
- [ ] **Performance Tests**: Caching and retry mechanisms validated

## ✅ Completion Criteria

Utilities implementation is complete when:

1. **All utility classes implemented** with comprehensive functionality
2. **Configuration management working** with environment variable support
3. **Caching system functional** with TTL and cleanup mechanisms
4. **Error handling robust** throughout all utilities
5. **Security measures implemented** for input sanitization
6. **Complete test suite passing** with >90% coverage

**Next Step**: The utilities provide the foundation for all other components and should be implemented early in the development process. 