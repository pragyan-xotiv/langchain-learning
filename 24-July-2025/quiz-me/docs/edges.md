# Edge Logic and Transitions

## Overview

The Interactive Quiz Generator uses conditional edges to route the application flow based on the current state. These edges determine which node to execute next, enabling dynamic conversation flow and proper error handling.

## Edge Decision Framework

### Primary Decision Factors

1. **Current Phase**: Application state phase
2. **User Intent**: Classified user intention
3. **Validation Results**: Success/failure of previous operations
4. **Error Conditions**: System errors or invalid states
5. **Completion Status**: Quiz progress and completion state

## Edge Definitions

### 1. Entry Point Edge

**Source**: Graph Entry Point  
**Decision Logic**: Always routes to Query Analyzer  
**Condition**: Initial user input received

```python
def entry_edge(state: QuizState) -> str:
    """
    Entry point for all user interactions
    """
    return "query_analyzer"
```

---

### 2. Query Analyzer Routing Edge

**Source**: Query Analyzer Node  
**Decision Logic**: Routes based on analyzed user intent and current phase

```python
def route_from_query_analyzer(state: QuizState) -> str:
    """
    Routes flow based on user intent analysis
    """
    intent = state.user_intent
    phase = state.current_phase
    
    # Handle exit intent from any phase
    if intent == "exit":
        return "end_session"
    
    # Handle new quiz request from any phase
    if intent == "new_quiz":
        return "topic_validator"
    
    # Phase-specific routing
    if phase == "topic_selection":
        if intent == "start_quiz":
            return "topic_validator"
        else:
            return "clarification_handler"
    
    elif phase == "topic_validation":
        return "topic_validator"
    
    elif phase == "quiz_active":
        if intent == "answer_question":
            return "answer_validator"
        else:
            return "quiz_generator"  # Continue with current question
    
    elif phase == "question_answered":
        if intent == "continue":
            return "score_generator"
        else:
            return "clarification_handler"
    
    elif phase == "quiz_complete":
        if intent == "new_quiz":
            return "topic_validator"
        else:
            return "end_session"
    
    # Default fallback
    return "clarification_handler"
```

**Routing Table**:

| Current Phase | User Intent | Next Node |
|---------------|-------------|-----------|
| topic_selection | start_quiz | topic_validator |
| topic_selection | * | clarification_handler |
| topic_validation | * | topic_validator |
| quiz_active | answer_question | answer_validator |
| quiz_active | * | quiz_generator |
| question_answered | continue | score_generator |
| question_answered | * | clarification_handler |
| quiz_complete | new_quiz | topic_validator |
| quiz_complete | * | end_session |
| any | exit | end_session |
| any | new_quiz | topic_validator |

---

### 3. Topic Validator Routing Edge

**Source**: Topic Validator Node  
**Decision Logic**: Routes based on topic validation results

```python
def route_from_topic_validator(state: QuizState) -> str:
    """
    Routes based on topic validation outcome
    """
    if state.topic_validated:
        return "quiz_generator"
    else:
        # Topic validation failed
        if state.retry_count >= 3:
            return "end_session"  # Too many failed attempts
        else:
            return "clarification_handler"  # Ask for different topic
```

**Routing Conditions**:
- **Success Path**: `topic_validated == True` → `quiz_generator`
- **Failure Path**: `topic_validated == False` → `clarification_handler`
- **Max Retries**: `retry_count >= 3` → `end_session`

---

### 4. Quiz Generator Routing Edge

**Source**: Quiz Generator Node  
**Decision Logic**: Always proceeds to wait for user answer

```python
def route_from_quiz_generator(state: QuizState) -> str:
    """
    After generating question, wait for user response
    """
    # Question generated successfully, wait for user input
    return "query_analyzer"  # Return to analyzer to get user answer
```

**Flow**: `quiz_generator` → `query_analyzer` (waiting for answer)

---

### 5. Answer Validator Routing Edge

**Source**: Answer Validator Node  
**Decision Logic**: Always proceeds to score calculation

```python
def route_from_answer_validator(state: QuizState) -> str:
    """
    After validating answer, always calculate score
    """
    return "score_generator"
```

**Flow**: `answer_validator` → `score_generator`

---

### 6. Score Generator Routing Edge

**Source**: Score Generator Node  
**Decision Logic**: Routes based on quiz completion status

```python
def route_from_score_generator(state: QuizState) -> str:
    """
    Routes based on quiz completion and user preferences
    """
    if state.quiz_completed:
        return "quiz_completion_handler"
    else:
        # Quiz continues, generate next question
        return "quiz_generator"
```

**Routing Conditions**:
- **Quiz Complete**: `quiz_completed == True` → `quiz_completion_handler`
- **Quiz Continues**: `quiz_completed == False` → `quiz_generator`

---

## Special Edge Cases

### Error Handling Edges

```python
def error_recovery_edge(state: QuizState) -> str:
    """
    Handles various error conditions
    """
    if state.last_error:
        error_type = classify_error(state.last_error)
        
        if error_type == "user_input_error":
            return "clarification_handler"
        elif error_type == "llm_error":
            if state.retry_count < 3:
                return "retry_handler"
            else:
                return "end_session"
        elif error_type == "validation_error":
            return "clarification_handler"
        else:
            return "end_session"
    
    return "query_analyzer"  # Default recovery
```

### Timeout Handling

```python
def timeout_edge(state: QuizState) -> str:
    """
    Handles user inactivity timeouts
    """
    if state.last_interaction_time > TIMEOUT_THRESHOLD:
        return "session_timeout_handler"
    
    return "query_analyzer"
```

## Complex Flow Scenarios

### 1. New Quiz During Active Quiz

```python
# Current: quiz_active, Intent: new_quiz
# Flow: query_analyzer → topic_validator (with state reset)

def handle_new_quiz_request(state: QuizState) -> QuizState:
    """Reset state for new quiz"""
    state = reset_quiz_state(state)
    state.current_phase = "topic_selection"
    return state
```

### 2. Ambiguous Answer Classification

```python
# When query_analyzer can't determine if input is answer or command
def handle_ambiguous_intent(state: QuizState) -> str:
    """Handle unclear user intent"""
    if state.current_phase == "quiz_active" and state.current_question:
        # Assume it's an answer attempt
        state.user_intent = "answer_question"
        return "answer_validator"
    else:
        return "clarification_handler"
```

### 3. Infinite Quiz Termination

```python
def infinite_quiz_termination(state: QuizState) -> str:
    """Handle termination of infinite quizzes"""
    if state.quiz_type == "infinite":
        if state.total_questions_answered >= 50:  # Reasonable limit
            state.quiz_completed = True
            return "quiz_completion_handler"
        elif state.user_intent == "continue":
            return "quiz_generator"
        else:
            return "quiz_completion_handler"
    
    return "score_generator"
```

## Edge Configuration

### Graph Structure Definition

```python
from langgraph.graph import StateGraph

def build_quiz_graph():
    """Construct the complete application graph"""
    
    workflow = StateGraph(QuizState)
    
    # Add nodes
    workflow.add_node("query_analyzer", query_analyzer)
    workflow.add_node("topic_validator", topic_validator)
    workflow.add_node("quiz_generator", quiz_generator)
    workflow.add_node("answer_validator", answer_validator)
    workflow.add_node("score_generator", score_generator)
    workflow.add_node("clarification_handler", clarification_handler)
    workflow.add_node("quiz_completion_handler", quiz_completion_handler)
    
    # Define edges
    workflow.set_entry_point("query_analyzer")
    
    workflow.add_conditional_edges(
        "query_analyzer",
        route_from_query_analyzer,
        {
            "topic_validator": "topic_validator",
            "answer_validator": "answer_validator",
            "quiz_generator": "quiz_generator",
            "score_generator": "score_generator",
            "clarification_handler": "clarification_handler",
            "end_session": END
        }
    )
    
    workflow.add_conditional_edges(
        "topic_validator",
        route_from_topic_validator,
        {
            "quiz_generator": "quiz_generator",
            "clarification_handler": "clarification_handler",
            "end_session": END
        }
    )
    
    workflow.add_edge("quiz_generator", "query_analyzer")
    workflow.add_edge("answer_validator", "score_generator")
    
    workflow.add_conditional_edges(
        "score_generator",
        route_from_score_generator,
        {
            "quiz_generator": "quiz_generator",
            "quiz_completion_handler": "quiz_completion_handler"
        }
    )
    
    workflow.add_edge("clarification_handler", "query_analyzer")
    workflow.add_edge("quiz_completion_handler", END)
    
    return workflow.compile()
```

## Edge Testing and Validation

### Edge Coverage Testing

```python
def test_edge_coverage():
    """Ensure all possible state transitions are tested"""
    test_scenarios = [
        # (phase, intent, expected_next_node)
        ("topic_selection", "start_quiz", "topic_validator"),
        ("quiz_active", "answer_question", "answer_validator"),
        ("question_answered", "continue", "score_generator"),
        ("any", "exit", "end_session"),
        ("any", "new_quiz", "topic_validator"),
        # ... additional test cases
    ]
    
    for phase, intent, expected in test_scenarios:
        state = create_test_state(phase, intent)
        actual = route_from_query_analyzer(state)
        assert actual == expected, f"Failed: {phase}, {intent} -> {actual} != {expected}"
```

### State Consistency Validation

```python
def validate_edge_transitions(state: QuizState, next_node: str) -> bool:
    """Validate that state is consistent with next node requirements"""
    
    requirements = {
        "topic_validator": ["user_input"],
        "quiz_generator": ["topic", "topic_validated"],
        "answer_validator": ["current_answer", "current_question"],
        "score_generator": ["answer_is_correct"],
    }
    
    if next_node in requirements:
        for field in requirements[next_node]:
            if not getattr(state, field):
                return False
    
    return True
```

## Performance Optimization

### Edge Decision Caching

```python
@lru_cache(maxsize=100)
def cached_route_decision(phase: str, intent: str, quiz_active: bool) -> str:
    """Cache frequent routing decisions"""
    # Implementation of routing logic with caching
    pass
```

### Parallel Edge Evaluation

For complex conditional logic, edges can be evaluated in parallel:

```python
async def parallel_edge_evaluation(state: QuizState) -> str:
    """Evaluate multiple conditions simultaneously"""
    conditions = await asyncio.gather(
        check_completion_condition(state),
        check_error_condition(state),
        check_intent_condition(state)
    )
    
    return determine_route_from_conditions(conditions)
```

## Best Practices

1. **Explicit Conditions**: Make all routing conditions explicit and testable
2. **Default Routes**: Always provide fallback routes for unexpected states
3. **Error Handling**: Include error recovery paths in all edges
4. **State Validation**: Validate state consistency before routing
5. **Performance**: Cache frequent routing decisions
6. **Testing**: Comprehensive edge coverage testing
7. **Documentation**: Clear documentation of all routing logic 