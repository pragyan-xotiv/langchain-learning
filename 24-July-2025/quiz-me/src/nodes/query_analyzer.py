"""Query Analyzer Node for the Interactive Quiz Generator

This module implements the query analyzer node that analyzes user input to determine 
intent and context. This is typically the first node in the workflow that processes
user messages.
"""

from typing import Dict, Any, Optional
import asyncio
import logging
from datetime import datetime
from langchain_openai import ChatOpenAI

from ..state import QuizState
from ..prompts import format_intent_classification_prompt, extract_json_from_response
from ..utils import Config

logger = logging.getLogger(__name__)

class QueryAnalyzerError(Exception):
    """Exception raised during query analysis"""
    pass

class LLMCallError(QueryAnalyzerError):
    """Error in LLM communication"""
    pass

def create_llm_client() -> ChatOpenAI:
    """Create and configure LLM client"""
    return ChatOpenAI(
        api_key=Config.OPENAI_API_KEY,
        model=Config.OPENAI_MODEL,
        temperature=Config.OPENAI_TEMPERATURE,
        max_tokens=Config.OPENAI_MAX_TOKENS
    )

async def safe_llm_call(llm: ChatOpenAI, prompt: str, max_retries: int = 3) -> str:
    """Make LLM call with error handling and retries"""
    for attempt in range(max_retries):
        try:
            response = await llm.ainvoke(prompt)
            return response.content
        except Exception as e:
            logger.warning(f"LLM call attempt {attempt + 1} failed: {str(e)}")
            if attempt == max_retries - 1:
                raise LLMCallError(f"LLM call failed after {max_retries} attempts: {str(e)}")
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
    
    raise LLMCallError("Unexpected error in LLM call")

def query_analyzer(state: QuizState, llm: Optional[ChatOpenAI] = None) -> QuizState:
    """
    Analyzes user input to determine intent and context.
    
    Args:
        state: Current quiz state with user_input populated
        llm: Language model client (optional, will create if not provided)
        
    Returns:
        Updated state with user_intent and conversation_history
    """
    logger.info(f"Query Analyzer processing: '{state.user_input}' in phase '{state.current_phase}'")
    
    if llm is None:
        llm = create_llm_client()
    
    try:
        # Validate input state
        if not state.user_input or not state.user_input.strip():
            state.last_error = "Empty user input provided"
            return state
        
        # Format prompt for intent classification
        prompt = format_intent_classification_prompt(state)
        
        # Call LLM for intent classification
        response = asyncio.run(safe_llm_call(llm, prompt))
        
        # Parse response
        result = extract_json_from_response(response)
        
        if "error" in result:
            logger.error(f"Intent classification failed: {result['error']}")
            state.last_error = f"Intent analysis failed: {result['error']}"
            state.user_intent = "clarification"  # Default fallback
        else:
            # Extract intent information
            state.user_intent = result.get("intent", "clarification")
            confidence = result.get("confidence", 0.0)
            reasoning = result.get("reasoning", "No reasoning provided")
            
            logger.info(f"Intent classified as '{state.user_intent}' with confidence {confidence}")
            
            # Store analysis in metadata
            state.quiz_metadata["last_intent_analysis"] = {
                "intent": state.user_intent,
                "confidence": confidence,
                "reasoning": reasoning,
                "timestamp": datetime.now().isoformat()
            }
        
        # Update conversation history
        state.add_conversation_entry(
            user_input=state.user_input,
            system_response=f"Intent classified as: {state.user_intent}"
        )
        
        # Clear any previous errors on successful processing
        if not state.last_error:
            state.last_error = None
        
        return state
        
    except Exception as e:
        logger.error(f"Query analyzer error: {str(e)}")
        state.last_error = f"Query analysis failed: {str(e)}"
        state.user_intent = "clarification"
        return state

def validate_query_analyzer_prerequisites(state: QuizState) -> list[str]:
    """Validate that state meets query analyzer prerequisites"""
    errors = []
    
    if not hasattr(state, 'user_input') or not state.user_input:
        errors.append("Query analyzer requires 'user_input' field")
    
    return errors 