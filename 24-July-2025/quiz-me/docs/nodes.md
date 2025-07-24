# Node Architecture

## Overview

The Interactive Quiz Generator uses a node-based architecture where each node handles a specific aspect of the quiz workflow. Nodes are connected through conditional edges and communicate via the shared state object.

## Node Specifications

### 1. Query Analyzer Node

**Purpose**: Analyzes user input to determine intent and context, enabling flexible conversation flow.

**Input State Requirements**:
- `user_input`: Raw user text input
- `current_phase`: Current application phase
- `conversation_history`: Previous interactions for context

**Core Logic**:
```python
def query_analyzer(state: QuizState) -> QuizState:
    """
    Analyzes user input to determine intent and appropriate response path
    """
    # Use LLM to analyze intent with context
    context = {
        "user_input": state.user_input,
        "current_phase": state.current_phase,
        "quiz_active": state.quiz_active,
        "topic": state.topic,
        "conversation_history": state.conversation_history[-3:]  # Last 3 interactions
    }
    
    # LLM prompt to classify intent
    intent_result = llm_classify_intent(context)
    
    # Update state based on analysis
    state.user_intent = intent_result.intent
    state.conversation_history.append({
        "user": state.user_input,
        "analysis": intent_result.reasoning,
        "timestamp": datetime.now().isoformat()
    })
    
    return state
```

**Intent Classifications**:
- `start_quiz`: User wants to begin a new quiz
- `answer_question`: User is responding to a quiz question
- `new_quiz`: User wants to restart with a different topic
- `exit`: User wants to end the session
- `continue`: User wants to proceed to next question
- `clarification`: User needs help or has questions

**Output State Updates**:
- `user_intent`: Classified intent
- `conversation_history`: Updated with new interaction

**LLM Integration**:
Uses structured prompts to analyze user intent considering current context and conversation history.

---

### 2. Topic Validator Node

**Purpose**: Validates quiz topics for appropriateness, feasibility, and educational value.

**Input State Requirements**:
- `user_input`: Contains topic information
- `user_intent`: Should be "start_quiz"

**Core Logic**:
```python
def topic_validator(state: QuizState) -> QuizState:
    """
    Validates and processes quiz topic selection
    """
    # Extract topic from user input
    topic_extraction_result = llm_extract_topic(state.user_input)
    
    if not topic_extraction_result.topic:
        state.last_error = "Could not identify a clear quiz topic"
        state.current_phase = "topic_selection"
        return state
    
    # Validate topic appropriateness
    validation_result = llm_validate_topic(topic_extraction_result.topic)
    
    state.topic = topic_extraction_result.topic
    state.topic_validated = validation_result.is_valid
    
    if validation_result.is_valid:
        state.current_phase = "quiz_active"
        state.quiz_active = True
        state.quiz_metadata.update({
            "topic_category": validation_result.category,
            "difficulty_level": validation_result.difficulty,
            "estimated_questions": validation_result.estimated_questions
        })
    else:
        state.last_error = validation_result.reason
        state.current_phase = "topic_selection"
    
    return state
```

**Validation Criteria**:
- **Appropriateness**: Content suitable for educational purposes
- **Specificity**: Topic is neither too broad nor too narrow
- **Feasibility**: Sufficient content available for question generation
- **Safety**: No harmful, offensive, or inappropriate content

**Output State Updates**:
- `topic`: Extracted and cleaned topic string
- `topic_validated`: Boolean validation result
- `current_phase`: Updated based on validation result
- `quiz_metadata`: Topic classification and metadata
- `last_error`: Error message if validation fails

**LLM Integration**:
Uses topic extraction and validation prompts with safety filtering.

---

### 3. Quiz Generator Node

**Purpose**: Generates diverse, engaging quiz questions based on the validated topic.

**Input State Requirements**:
- `topic`: Validated quiz topic
- `topic_validated`: Must be True
- `current_question_index`: Current position in quiz
- `quiz_metadata`: Topic context and difficulty

**Core Logic**:
```python
def quiz_generator(state: QuizState) -> QuizState:
    """
    Generates questions based on topic and current quiz progress
    """
    # Determine question type based on topic and progression
    question_strategy = determine_question_strategy(
        state.topic,
        state.current_question_index,
        state.quiz_metadata
    )
    
    # Generate question using LLM
    generation_context = {
        "topic": state.topic,
        "question_number": state.current_question_index + 1,
        "difficulty": state.quiz_metadata.get("difficulty_level", "medium"),
        "previous_questions": [qa["question"] for qa in state.user_answers],
        "question_type": question_strategy.type
    }
    
    question_result = llm_generate_question(generation_context)
    
    # Update state with new question
    state.current_question = question_result.question
    state.question_type = question_result.type
    state.correct_answer = question_result.correct_answer
    state.question_options = question_result.options if question_result.options else None
    
    return state
```

**Question Types**:
- **Multiple Choice**: 4 options with single correct answer
- **Open Ended**: Free-form text response
- **True/False**: Binary choice questions
- **Fill in the Blank**: Complete the statement
- **Scenario-Based**: Context-driven questions

**Question Generation Strategies**:
- **Progressive Difficulty**: Start easy, gradually increase complexity
- **Topic Coverage**: Ensure broad coverage of subject matter
- **Variety**: Mix question types to maintain engagement
- **Uniqueness**: Avoid repetitive or similar questions

**Output State Updates**:
- `current_question`: Generated question text
- `question_type`: Classification of question format
- `correct_answer`: Expected correct response
- `question_options`: Multiple choice options (if applicable)

**LLM Integration**:
Uses sophisticated question generation prompts with context awareness and difficulty progression.

---

### 4. Answer Validator Node

**Purpose**: Evaluates user answers for correctness and provides constructive feedback.

**Input State Requirements**:
- `current_answer`: User's response to current question
- `current_question`: The question being answered
- `correct_answer`: Expected correct answer
- `question_type`: Question format for validation strategy

**Core Logic**:
```python
def answer_validator(state: QuizState) -> QuizState:
    """
    Validates user answers and provides feedback
    """
    validation_strategy = get_validation_strategy(state.question_type)
    
    validation_context = {
        "question": state.current_question,
        "user_answer": state.current_answer,
        "correct_answer": state.correct_answer,
        "question_type": state.question_type,
        "options": state.question_options
    }
    
    validation_result = validation_strategy.validate(validation_context)
    
    # Update state with validation results
    state.answer_is_correct = validation_result.is_correct
    state.answer_feedback = validation_result.feedback
    
    # Store answer in history
    answer_record = {
        "question_index": state.current_question_index,
        "question": state.current_question,
        "user_answer": state.current_answer,
        "correct_answer": state.correct_answer,
        "is_correct": validation_result.is_correct,
        "feedback": validation_result.feedback,
        "explanation": validation_result.explanation,
        "timestamp": datetime.now().isoformat()
    }
    
    state.user_answers.append(answer_record)
    state.current_phase = "question_answered"
    
    return state
```

**Validation Strategies**:

**Multiple Choice**:
- Exact match against correct option
- Case-insensitive comparison
- Option letter/number recognition

**Open Ended**:
- Semantic similarity using embeddings
- Key concept identification
- Flexible matching with partial credit

**True/False**:
- Boolean value extraction
- Synonym recognition ("yes"/"true", "no"/"false")

**Fill in the Blank**:
- Multiple acceptable answers support
- Fuzzy matching for spelling variations

**Output State Updates**:
- `answer_is_correct`: Boolean correctness indicator
- `answer_feedback`: Immediate feedback message
- `user_answers`: Complete answer history
- `current_phase`: Transition to "question_answered"

**LLM Integration**:
Uses context-aware validation prompts for subjective answer evaluation.

---

### 5. Score Generator Node

**Purpose**: Calculates scores, tracks progress, and determines quiz completion status.

**Input State Requirements**:
- `answer_is_correct`: Result from answer validation
- `total_questions_answered`: Current progress counter
- `quiz_type`: Finite or infinite quiz mode
- `max_questions`: Maximum questions for finite quizzes

**Core Logic**:
```python
def score_generator(state: QuizState) -> QuizState:
    """
    Updates scoring and determines quiz progression
    """
    # Update question counters
    state.total_questions_answered += 1
    
    # Update score based on correctness
    if state.answer_is_correct:
        state.correct_answers_count += 1
        # Dynamic scoring based on difficulty and question type
        base_score = 10
        difficulty_multiplier = state.quiz_metadata.get("difficulty_multiplier", 1.0)
        question_type_bonus = get_question_type_bonus(state.question_type)
        
        points_earned = int(base_score * difficulty_multiplier + question_type_bonus)
        state.total_score += points_earned
    
    # Calculate progress and completion
    if state.quiz_type == "finite":
        state.quiz_completion_percentage = (
            state.total_questions_answered / state.max_questions * 100
        )
        
        if state.total_questions_answered >= state.max_questions:
            state.quiz_completed = True
            state.quiz_active = False
            state.current_phase = "quiz_complete"
    
    # Generate performance insights
    accuracy = state.correct_answers_count / state.total_questions_answered * 100
    state.quiz_metadata["current_accuracy"] = accuracy
    state.quiz_metadata["performance_trend"] = calculate_performance_trend(state.user_answers)
    
    return state
```

**Scoring System**:
- **Base Points**: 10 points per correct answer
- **Difficulty Multiplier**: 0.5x (easy), 1.0x (medium), 1.5x (hard)
- **Question Type Bonuses**:
  - Multiple Choice: +0 points
  - True/False: +0 points
  - Open Ended: +5 points
  - Fill in Blank: +3 points
  - Scenario-Based: +7 points

**Progress Tracking**:
- Total questions answered
- Correct answer percentage
- Score accumulation
- Performance trends
- Completion status

**Output State Updates**:
- `total_score`: Updated cumulative score
- `total_questions_answered`: Incremented counter
- `correct_answers_count`: Updated if answer was correct
- `quiz_completion_percentage`: Progress percentage
- `quiz_completed`: Completion status
- `quiz_active`: Active status
- `current_phase`: May transition to "quiz_complete"

---

## Node Interaction Patterns

### Sequential Processing
```
Query Analyzer → Topic Validator → Quiz Generator → Answer Validator → Score Generator
```

### Conditional Flows
```python
# After Query Analyzer
if user_intent == "new_quiz":
    → Topic Validator
elif user_intent == "answer_question":
    → Answer Validator
elif user_intent == "exit":
    → End Session
```

### Error Handling
Each node implements error recovery:
- Input validation
- Graceful degradation
- Error state updates
- Retry mechanisms

### State Consistency
Nodes validate state consistency:
- Required field checks
- Phase transition validation
- Data integrity verification

## Performance Considerations

1. **LLM Call Optimization**: Cache similar requests
2. **State Size Management**: Limit conversation history size
3. **Async Processing**: Use async/await for LLM calls
4. **Error Recovery**: Implement retry logic with exponential backoff
5. **Memory Management**: Clean up unused state data

## Testing Strategies

Each node should be tested with:
- Valid input scenarios
- Edge cases and error conditions
- State consistency validation
- LLM response mocking
- Performance benchmarks 