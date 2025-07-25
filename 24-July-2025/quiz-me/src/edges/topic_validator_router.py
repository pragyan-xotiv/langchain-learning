"""Topic Validator Router for the Interactive Quiz Generator

This module implements routing logic after topic validation, handling validation
results, failure recovery, and alternative topic suggestions.
"""

from typing import List, Dict, Optional
import logging

from ..state import QuizState

logger = logging.getLogger(__name__)

def route_after_topic_validation(state: QuizState) -> str:
    """
    Route after topic validation based on validation results.
    
    Args:
        state: Current quiz state with topic validation results
        
    Returns:
        Next node identifier based on validation outcome
    """
    logger.info(f"Routing after topic validation: validated={state.topic_validated}, topic='{state.topic}'")
    
    try:
        if state.topic_validated and state.topic:
            # Successful validation - proceed to question generation
            logger.info(f"Topic '{state.topic}' validated successfully")
            return "quiz_generator"
        
        else:
            # Validation failed - handle appropriately
            return handle_validation_failure(state)
            
    except Exception as e:
        logger.error(f"Topic validation routing error: {str(e)}")
        return handle_validation_error(state, str(e))

def handle_validation_failure(state: QuizState) -> str:
    """
    Handle topic validation failure with appropriate recovery.
    
    Args:
        state: Current quiz state with failed validation
        
    Returns:
        Next node for recovery
    """
    logger.info("Handling topic validation failure")
    
    # Check retry count to avoid infinite loops
    if state.retry_count >= 3:
        logger.warning("Maximum validation retries reached")
        return handle_max_retries_reached(state)
    
    # Analyze the failure reason
    failure_reason = analyze_validation_failure(state)
    
    if failure_reason == "inappropriate_topic":
        return handle_inappropriate_topic(state)
    elif failure_reason == "unclear_topic":
        return handle_unclear_topic(state)
    elif failure_reason == "complex_topic":
        return handle_complex_topic(state)
    else:
        # Generic failure handling
        return "clarification_handler"

def suggest_alternative_topics(state: QuizState) -> List[str]:
    """
    Suggest alternative topics based on failed validation.
    
    Args:
        state: Current quiz state
        
    Returns:
        List of suggested alternative topics
    """
    logger.debug("Generating alternative topic suggestions")
    
    # Extract keywords from original input
    original_input = state.user_input.lower()
    
    # Common topic suggestions based on keywords
    topic_suggestions = {
        "python": ["Python Basics", "Python Data Structures", "Python Functions"],
        "javascript": ["JavaScript Fundamentals", "Web Development", "Node.js Basics"],
        "math": ["Basic Math", "Algebra", "Geometry"],
        "science": ["General Science", "Biology Basics", "Chemistry Fundamentals"],
        "history": ["World History", "American History", "Ancient Civilizations"],
        "programming": ["Programming Concepts", "Computer Science Basics", "Software Development"],
        "language": ["English Grammar", "Vocabulary Building", "Reading Comprehension"]
    }
    
    suggestions = []
    
    # Find matching suggestions
    for keyword, topics in topic_suggestions.items():
        if keyword in original_input:
            suggestions.extend(topics)
    
    # If no specific matches, provide general suggestions
    if not suggestions:
        suggestions = [
            "General Knowledge",
            "Science Basics", 
            "Math Fundamentals",
            "History Overview",
            "Geography Basics"
        ]
    
    # Store suggestions in metadata for the clarification handler
    state.quiz_metadata["suggested_topics"] = suggestions[:5]  # Limit to 5
    
    return suggestions[:5]

# === FAILURE TYPE HANDLERS ===

def handle_inappropriate_topic(state: QuizState) -> str:
    """Handle inappropriate topic with suggestions"""
    logger.info("Handling inappropriate topic")
    
    # Generate alternative suggestions
    suggestions = suggest_alternative_topics(state)
    
    # Store context for clarification handler
    state.quiz_metadata["validation_failure_type"] = "inappropriate"
    state.quiz_metadata["failure_context"] = {
        "original_topic": state.topic,
        "reason": "Topic not suitable for quiz generation",
        "suggestions": suggestions
    }
    
    return "clarification_handler"

def handle_unclear_topic(state: QuizState) -> str:
    """Handle unclear or ambiguous topic"""
    logger.info("Handling unclear topic")
    
    # Try to extract more specific topic from input
    potential_topics = extract_potential_topics(state.user_input)
    
    state.quiz_metadata["validation_failure_type"] = "unclear"
    state.quiz_metadata["failure_context"] = {
        "original_input": state.user_input,
        "reason": "Topic not clearly specified",
        "potential_topics": potential_topics
    }
    
    return "clarification_handler"

def handle_complex_topic(state: QuizState) -> str:
    """Handle overly complex topic that needs simplification"""
    logger.info("Handling complex topic")
    
    # Suggest breaking down the topic
    simplified_topics = simplify_complex_topic(state.topic)
    
    state.quiz_metadata["validation_failure_type"] = "complex"
    state.quiz_metadata["failure_context"] = {
        "original_topic": state.topic,
        "reason": "Topic too complex for focused quiz",
        "simplified_options": simplified_topics
    }
    
    return "clarification_handler"

def handle_max_retries_reached(state: QuizState) -> str:
    """Handle case where maximum retries have been reached"""
    logger.warning("Maximum topic validation retries reached")
    
    # Offer to end session or try completely different approach
    state.quiz_metadata["max_retries_reached"] = True
    state.quiz_metadata["failure_context"] = {
        "retry_count": state.retry_count,
        "reason": "Unable to find suitable quiz topic after multiple attempts"
    }
    
    # Give user option to try default topics or end session
    default_topics = [
        "General Knowledge",
        "Basic Math",
        "Science Facts",
        "History Timeline",
        "Geography Basics"
    ]
    
    state.quiz_metadata["default_topic_options"] = default_topics
    
    return "clarification_handler"

def handle_validation_error(state: QuizState, error_message: str) -> str:
    """Handle technical validation errors"""
    logger.error(f"Technical validation error: {error_message}")
    
    # Classify error type
    if "network" in error_message.lower() or "timeout" in error_message.lower():
        return handle_network_error(state)
    elif "api" in error_message.lower() or "llm" in error_message.lower():
        return handle_llm_error(state)
    else:
        return handle_generic_error(state)

# === ERROR TYPE HANDLERS ===

def handle_network_error(state: QuizState) -> str:
    """Handle network-related validation errors"""
    logger.info("Handling network error in topic validation")
    
    if state.retry_count < 2:  # Allow fewer retries for network issues
        state.retry_count += 1
        return "topic_validator"  # Retry validation
    else:
        state.quiz_metadata["error_type"] = "network"
        return "clarification_handler"

def handle_llm_error(state: QuizState) -> str:
    """Handle LLM-related validation errors"""
    logger.info("Handling LLM error in topic validation")
    
    if state.retry_count < 3:
        state.retry_count += 1
        return "topic_validator"  # Retry validation
    else:
        # Switch to fallback validation mode
        state.quiz_metadata["error_type"] = "llm"
        state.quiz_metadata["fallback_mode"] = True
        return "fallback_topic_handler"

def handle_generic_error(state: QuizState) -> str:
    """Handle generic validation errors"""
    logger.info("Handling generic validation error")
    
    state.quiz_metadata["error_type"] = "generic"
    return "clarification_handler"

# === ANALYSIS HELPERS ===

def analyze_validation_failure(state: QuizState) -> str:
    """
    Analyze why topic validation failed.
    
    Args:
        state: Current quiz state
        
    Returns:
        Failure type classification
    """
    error_message = state.last_error or ""
    topic = state.topic or ""
    
    # Check error message for clues
    if "inappropriate" in error_message.lower() or "not suitable" in error_message.lower():
        return "inappropriate_topic"
    
    if "unclear" in error_message.lower() or "ambiguous" in error_message.lower():
        return "unclear_topic"
    
    if "complex" in error_message.lower() or "broad" in error_message.lower():
        return "complex_topic"
    
    # Analyze topic characteristics
    if not topic or len(topic.strip()) < 3:
        return "unclear_topic"
    
    if len(topic.split()) > 8:  # Very long topics might be complex
        return "complex_topic"
    
    # Check for inappropriate content indicators
    inappropriate_indicators = ["inappropriate", "adult", "offensive", "controversial"]
    if any(indicator in topic.lower() for indicator in inappropriate_indicators):
        return "inappropriate_topic"
    
    return "unclear_topic"  # Default classification

def extract_potential_topics(user_input: str) -> List[str]:
    """
    Extract potential topics from unclear user input.
    
    Args:
        user_input: User's original input
        
    Returns:
        List of potential topic interpretations
    """
    input_lower = user_input.lower()
    potential_topics = []
    
    # Common subject keywords
    subjects = {
        "math": "Mathematics",
        "science": "Science",
        "history": "History",
        "english": "English Literature",
        "programming": "Programming",
        "python": "Python Programming",
        "javascript": "JavaScript",
        "biology": "Biology",
        "chemistry": "Chemistry",
        "physics": "Physics",
        "geography": "Geography"
    }
    
    # Find subject matches
    for keyword, full_name in subjects.items():
        if keyword in input_lower:
            potential_topics.append(full_name)
    
    # Extract noun phrases (simple approach)
    words = user_input.split()
    if len(words) >= 2:
        # Take combinations of words
        for i in range(len(words) - 1):
            phrase = " ".join(words[i:i+2])
            if len(phrase) > 3:  # Avoid very short phrases
                potential_topics.append(phrase.title())
    
    return potential_topics[:5]  # Limit to 5 suggestions

def simplify_complex_topic(topic: str) -> List[str]:
    """
    Break down complex topic into simpler components.
    
    Args:
        topic: Complex topic string
        
    Returns:
        List of simplified topic options
    """
    if not topic:
        return []
    
    simplified = []
    words = topic.split()
    
    # Try individual components
    for word in words:
        if len(word) > 3:  # Skip short words
            simplified.append(word.title())
    
    # Try pairs of words
    for i in range(len(words) - 1):
        pair = f"{words[i]} {words[i+1]}"
        if len(pair) > 5:
            simplified.append(pair.title())
    
    # Add generic alternatives based on domain
    domain_alternatives = {
        "science": ["General Science", "Science Basics", "Science Facts"],
        "math": ["Basic Math", "Math Fundamentals", "Arithmetic"],
        "history": ["Historical Events", "World History", "History Timeline"],
        "programming": ["Programming Basics", "Coding Fundamentals", "Software Development"]
    }
    
    topic_lower = topic.lower()
    for domain, alternatives in domain_alternatives.items():
        if domain in topic_lower:
            simplified.extend(alternatives)
    
    return simplified[:5]  # Limit to 5 options

# === ROUTING VALIDATION ===

def validate_topic_routing(state: QuizState, next_node: str) -> bool:
    """
    Validate topic validator routing decision.
    
    Args:
        state: Current quiz state
        next_node: Proposed next node
        
    Returns:
        True if routing is valid
    """
    # Valid nodes after topic validation
    valid_nodes = [
        "quiz_generator",           # Successful validation
        "clarification_handler",    # Failed validation or error
        "fallback_topic_handler",   # Technical issues
        "end"                      # Max retries or user exit
    ]
    
    if next_node not in valid_nodes:
        logger.warning(f"Invalid node '{next_node}' after topic validation")
        return False
    
    # Specific validations
    if next_node == "quiz_generator":
        if not (state.topic_validated and state.topic):
            logger.warning("Cannot route to quiz_generator without validated topic")
            return False
    
    return True

if __name__ == "__main__":
    # Test topic validator routing
    from ..state import create_test_state
    
    # Test successful validation
    state = create_test_state()
    state.topic = "Python Programming"
    state.topic_validated = True
    result = route_after_topic_validation(state)
    print(f"Successful validation: {result}")
    
    # Test failed validation
    state = create_test_state()
    state.topic = "Inappropriate Topic"
    state.topic_validated = False
    state.last_error = "Topic not suitable for quiz generation"
    result = route_after_topic_validation(state)
    print(f"Failed validation: {result}")
    
    # Test alternative suggestions
    state.user_input = "I want to learn about python programming"
    suggestions = suggest_alternative_topics(state)
    print(f"Suggestions: {suggestions}") 