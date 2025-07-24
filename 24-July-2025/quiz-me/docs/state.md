# State Management

## Overview

The Interactive Quiz Generator uses a centralized state object to maintain all application data throughout the user session. This state is passed between nodes and updated as the quiz progresses, ensuring consistent data flow and enabling complex conditional logic.

## State Schema

### Core State Structure

```python
from typing import List, Dict, Optional, Literal
from pydantic import BaseModel

class QuizState(BaseModel):
    # User Input & Intent
    user_input: str = ""
    user_intent: Optional[Literal["start_quiz", "answer_question", "new_quiz", "exit", "continue"]] = None
    
    # Current Phase Tracking
    current_phase: Literal["topic_selection", "topic_validation", "quiz_active", "question_answered", "quiz_complete"] = "topic_selection"
    
    # Quiz Configuration
    topic: Optional[str] = None
    topic_validated: bool = False
    quiz_type: Literal["finite", "infinite"] = "finite"
    max_questions: Optional[int] = 10
    
    # Question Management
    current_question_index: int = 0
    current_question: Optional[str] = None
    question_type: Optional[Literal["multiple_choice", "open_ended", "true_false"]] = None
    question_options: Optional[List[str]] = None
    correct_answer: Optional[str] = None
    
    # User Responses & History
    user_answers: List[Dict[str, any]] = []
    current_answer: Optional[str] = None
    answer_is_correct: Optional[bool] = None
    answer_feedback: Optional[str] = None
    
    # Scoring System
    total_score: int = 0
    total_questions_answered: int = 0
    correct_answers_count: int = 0
    quiz_completion_percentage: float = 0.0
    
    # Session Management
    quiz_active: bool = False
    quiz_completed: bool = False
    session_id: Optional[str] = None
    
    # Error Handling
    last_error: Optional[str] = None
    retry_count: int = 0
    
    # Context & Metadata
    conversation_history: List[Dict[str, str]] = []
    quiz_metadata: Dict[str, any] = {}
```

## State Updates by Node

### Query Analyzer Node

**Updates:**
- `user_input`: Stores the latest user input
- `user_intent`: Classifies user intent based on context
- `conversation_history`: Appends new interaction
- `current_phase`: May transition based on detected intent

**Example Update:**
```python
state.user_input = "I want to start a quiz about Python programming"
state.user_intent = "start_quiz"
state.conversation_history.append({
    "user": state.user_input,
    "timestamp": current_timestamp,
    "phase": state.current_phase
})
```

### Topic Validator Node

**Updates:**
- `topic`: Extracts and stores the quiz topic
- `topic_validated`: Boolean indicating validation result
- `current_phase`: Transitions to "topic_validation" or "quiz_active"
- `last_error`: Set if topic validation fails
- `quiz_metadata`: Stores topic-related information

**Example Update:**
```python
state.topic = "Python Programming"
state.topic_validated = True
state.current_phase = "quiz_active"
state.quiz_metadata.update({
    "topic_category": "Programming",
    "difficulty_level": "intermediate",
    "estimated_duration": "15 minutes"
})
```

### Quiz Generator Node

**Updates:**
- `current_question`: Stores the generated question
- `question_type`: Classifies the question format
- `question_options`: Stores multiple choice options if applicable
- `correct_answer`: Stores the correct answer for validation
- `current_question_index`: Increments question counter

**Example Update:**
```python
state.current_question = "What is the difference between a list and a tuple in Python?"
state.question_type = "open_ended"
state.correct_answer = "Lists are mutable, tuples are immutable"
state.current_question_index += 1
```

### Answer Validator Node

**Updates:**
- `current_answer`: Stores user's answer
- `answer_is_correct`: Boolean indicating correctness
- `answer_feedback`: Detailed feedback on the answer
- `user_answers`: Appends answer to history
- `current_phase`: Transitions to "question_answered"

**Example Update:**
```python
answer_record = {
    "question_index": state.current_question_index,
    "question": state.current_question,
    "user_answer": state.current_answer,
    "correct_answer": state.correct_answer,
    "is_correct": state.answer_is_correct,
    "feedback": state.answer_feedback,
    "timestamp": current_timestamp
}
state.user_answers.append(answer_record)
state.current_phase = "question_answered"
```

### Score Generator Node

**Updates:**
- `total_score`: Updates cumulative score
- `total_questions_answered`: Increments question counter
- `correct_answers_count`: Increments if answer was correct
- `quiz_completion_percentage`: Calculates progress percentage
- `quiz_completed`: Set to True if quiz is finished
- `current_phase`: May transition to "quiz_complete"

**Example Update:**
```python
state.total_questions_answered += 1
if state.answer_is_correct:
    state.correct_answers_count += 1
    state.total_score += 10  # 10 points per correct answer

state.quiz_completion_percentage = (
    state.total_questions_answered / state.max_questions * 100
    if state.quiz_type == "finite" else None
)

if state.total_questions_answered >= state.max_questions:
    state.quiz_completed = True
    state.current_phase = "quiz_complete"
```

## State Transition Patterns

### Phase Transitions

```python
# Topic Selection → Topic Validation
current_phase: "topic_selection" → "topic_validation"
trigger: user_intent == "start_quiz" and topic provided

# Topic Validation → Quiz Active
current_phase: "topic_validation" → "quiz_active"
trigger: topic_validated == True

# Quiz Active → Question Answered
current_phase: "quiz_active" → "question_answered"
trigger: user provides answer to current question

# Question Answered → Quiz Active (continue)
current_phase: "question_answered" → "quiz_active"
trigger: user_intent == "continue" and not quiz_completed

# Any Phase → Topic Selection (new quiz)
current_phase: any → "topic_selection"
trigger: user_intent == "new_quiz"
```

### State Reset Patterns

**New Quiz Reset:**
```python
def reset_for_new_quiz(state: QuizState) -> QuizState:
    state.topic = None
    state.topic_validated = False
    state.current_question_index = 0
    state.current_question = None
    state.user_answers = []
    state.total_score = 0
    state.total_questions_answered = 0
    state.correct_answers_count = 0
    state.quiz_completion_percentage = 0.0
    state.quiz_active = False
    state.quiz_completed = False
    state.current_phase = "topic_selection"
    return state
```

## State Validation Rules

### Required Fields by Phase

- **topic_selection**: `user_input`
- **topic_validation**: `user_input`, `topic`
- **quiz_active**: `topic`, `topic_validated`, `current_question`
- **question_answered**: All quiz_active fields + `current_answer`
- **quiz_complete**: All fields populated

### Consistency Checks

```python
def validate_state_consistency(state: QuizState) -> List[str]:
    errors = []
    
    if state.quiz_active and not state.topic_validated:
        errors.append("Quiz cannot be active without validated topic")
    
    if state.current_question_index > len(state.user_answers) + 1:
        errors.append("Question index inconsistent with answer history")
    
    if state.correct_answers_count > state.total_questions_answered:
        errors.append("Correct answers cannot exceed total answered")
    
    return errors
```

## State Persistence

The state object can be serialized for session persistence:

```python
import json
from datetime import datetime

def serialize_state(state: QuizState) -> str:
    """Convert state to JSON for storage"""
    state_dict = state.dict()
    state_dict['serialized_at'] = datetime.now().isoformat()
    return json.dumps(state_dict, indent=2)

def deserialize_state(state_json: str) -> QuizState:
    """Restore state from JSON"""
    state_dict = json.loads(state_json)
    return QuizState(**state_dict)
```

## Best Practices

1. **Immutable Updates**: Always create new state objects rather than modifying in place
2. **Validation**: Validate state consistency after each update
3. **Error Handling**: Always update `last_error` field when errors occur
4. **History Tracking**: Maintain comprehensive conversation and answer history
5. **Reset Patterns**: Use standardized reset functions for state cleanup 