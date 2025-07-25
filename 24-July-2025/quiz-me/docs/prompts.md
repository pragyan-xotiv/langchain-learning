# Prompt Templates

## Overview

This document contains the LLM prompt templates used throughout the Interactive Quiz Generator. Each prompt is designed for specific tasks and includes context variables, structured outputs, and error handling.

## 🆕 Modular Prompt Structure

The prompt system is now organized in a dedicated package (`src/prompts/`) with comprehensive template management:

```
src/prompts/
├── __init__.py                  # Imports all prompt templates and utilities
├── prompt_types.py              # Shared types and enumerations
├── prompt_manager.py            # Template management and formatting system
├── intent_classification.py     # Intent analysis prompts  
├── topic_extraction.py          # Topic extraction prompts
├── topic_validation.py          # Topic validation prompts
├── question_generation.py       # Question creation prompts
├── answer_validation.py         # Answer evaluation prompts
├── clarification.py             # Clarification request prompts
└── summary_generation.py        # Performance summary prompts
```

### Enhanced Prompt Components:
- **Modular Templates**: Each prompt type in its own module for better organization
- **Prompt Manager**: Centralized template loading, formatting, and validation
- **Shared Types**: Common enumerations and data structures across all prompts
- **Response Validation**: Structured output parsing and validation utilities

## Query Analyzer Prompts

### Intent Classification Prompt

**Purpose**: Classify user intent based on input and conversation context

```python
INTENT_CLASSIFICATION_PROMPT = """
You are an intent classifier for an interactive quiz application. Analyze the user's input and determine their intent based on the current context.

CURRENT CONTEXT:
- Current Phase: {current_phase}
- Quiz Active: {quiz_active}
- Current Topic: {topic}
- Recent Conversation: {conversation_history}

USER INPUT: "{user_input}"

POSSIBLE INTENTS:
1. start_quiz - User wants to begin a new quiz on a topic
2. answer_question - User is responding to a quiz question
3. new_quiz - User wants to start over with a different topic
4. exit - User wants to end the session
5. continue - User wants to proceed to the next question
6. clarification - User needs help or has questions

CLASSIFICATION RULES:
- If quiz is active and user provides a direct answer, classify as "answer_question"
- Keywords like "new quiz", "different topic", "start over" indicate "new_quiz"
- Keywords like "exit", "quit", "bye", "done" indicate "exit"
- Keywords like "next", "continue", "more" indicate "continue"
- If input seems unclear or off-topic, classify as "clarification"

Respond with JSON:
{{
    "intent": "one_of_the_intents_above",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation of your classification"
}}
"""

def format_intent_prompt(state: QuizState) -> str:
    return INTENT_CLASSIFICATION_PROMPT.format(
        current_phase=state.current_phase,
        quiz_active=state.quiz_active,
        topic=state.topic or "None",
        conversation_history=format_recent_history(state.conversation_history[-3:]),
        user_input=state.user_input
    )
```

### Context Analysis Prompt

**Purpose**: Analyze conversation context for better intent understanding

```python
CONTEXT_ANALYSIS_PROMPT = """
You are analyzing conversation context for a quiz application. Review the interaction pattern and provide insights.

CONVERSATION HISTORY:
{conversation_history}

CURRENT USER INPUT: "{user_input}"

Analyze:
1. Is the user engaged or showing signs of disinterest?
2. Are they struggling with the current difficulty level?
3. Do they seem confused about the interface or expectations?
4. What is their likely next desired action?

Respond with JSON:
{{
    "engagement_level": "high|medium|low",
    "difficulty_preference": "easier|current|harder",
    "confusion_indicators": ["list", "of", "indicators"],
    "suggested_response_tone": "encouraging|neutral|challenging|helpful",
    "predicted_next_intent": "likely_intent"
}}
"""
```

## Topic Validation Prompts

### Topic Extraction Prompt

**Purpose**: Extract and clean quiz topics from user input

```python
TOPIC_EXTRACTION_PROMPT = """
Extract the quiz topic from the user's input. Clean and standardize the topic name.

USER INPUT: "{user_input}"

EXTRACTION GUIDELINES:
- Identify the main subject the user wants to be quizzed on
- Make the topic specific but not overly narrow
- Clean up grammar and formatting
- Handle multiple topics by selecting the primary one
- If no clear topic, return null

EXAMPLES:
Input: "I want to learn about World War 2" → Topic: "World War II"
Input: "Quiz me on Python programming please" → Topic: "Python Programming"
Input: "Something about space and planets" → Topic: "Astronomy and Planets"
Input: "I don't know, anything" → Topic: null

Respond with JSON:
{{
    "topic": "extracted_topic_or_null",
    "confidence": 0.0-1.0,
    "alternative_topics": ["list", "if", "multiple", "detected"],
    "specificity_level": "very_broad|broad|specific|very_specific"
}}
"""
```

### Topic Validation Prompt

**Purpose**: Validate topic appropriateness and feasibility

```python
TOPIC_VALIDATION_PROMPT = """
Validate whether this topic is suitable for quiz generation.

TOPIC TO VALIDATE: "{topic}"

VALIDATION CRITERIA:
1. APPROPRIATENESS: Educational, safe, non-controversial content
2. SPECIFICITY: Not too broad ("everything") or too narrow ("my pet's name")
3. FEASIBILITY: Sufficient factual content exists for question generation
4. SAFETY: No harmful, offensive, or inappropriate material

CATEGORY GUIDELINES:
- Academic subjects: Usually valid (Science, History, Literature, etc.)
- Professional skills: Usually valid (Programming, Business, etc.)
- Hobbies/Interests: Valid if educational (Photography, Cooking, etc.)
- Personal/Private: Usually invalid (Personal relationships, private data)
- Controversial: Use caution (Politics, Religion - focus on facts only)

Respond with JSON:
{{
    "is_valid": true/false,
    "confidence": 0.0-1.0,
    "category": "academic|professional|hobby|general_knowledge|other",
    "difficulty_level": "beginner|intermediate|advanced",
    "estimated_questions": 5-50,
    "reason": "explanation_if_invalid",
    "suggestions": ["alternative", "topics", "if", "invalid"]
}}
"""
```

## Question Generation Prompts

### Question Generation Master Prompt

**Purpose**: Generate diverse, engaging quiz questions

```python
QUESTION_GENERATION_PROMPT = """
Generate a quiz question for the given topic and context.

QUIZ CONTEXT:
- Topic: {topic}
- Question Number: {question_number}
- Difficulty Level: {difficulty_level}
- Previous Questions: {previous_questions}
- Question Type: {question_type}

QUESTION REQUIREMENTS:
1. Create an educational, factual question about the topic
2. Match the specified difficulty level
3. Avoid repeating previous questions or very similar concepts
4. Make the question clear and unambiguous
5. Ensure there is a definitive correct answer

QUESTION TYPE SPECIFICATIONS:

MULTIPLE_CHOICE:
- Provide exactly 4 options (A, B, C, D)
- Only one correct answer
- Make distractors plausible but clearly incorrect
- Avoid "all of the above" or "none of the above"

OPEN_ENDED:
- Ask for explanation, description, or analysis
- Allow for multiple correct phrasings
- Focus on understanding, not memorization

TRUE_FALSE:
- Create a clear statement that is definitively true or false
- Avoid ambiguous or opinion-based statements

FILL_IN_BLANK:
- Create sentence with one key term missing
- Ensure only one logical answer fits
- Use context clues to guide the answer

Respond with JSON:
{{
    "question": "the_question_text",
    "type": "multiple_choice|open_ended|true_false|fill_in_blank",
    "correct_answer": "the_correct_answer",
    "options": ["A", "B", "C", "D"] or null,
    "explanation": "why_this_is_the_correct_answer",
    "difficulty_justification": "why_this_matches_requested_difficulty",
    "learning_objective": "what_this_question_teaches"
}}
"""
```

### Adaptive Difficulty Prompt

**Purpose**: Adjust question difficulty based on user performance

```python
ADAPTIVE_DIFFICULTY_PROMPT = """
Adjust the difficulty of the next question based on user performance.

PERFORMANCE DATA:
- Current Accuracy: {current_accuracy}%
- Recent Answers: {recent_answers}
- Question Types Struggled With: {difficult_types}
- Current Difficulty: {current_difficulty}

ADAPTATION RULES:
- If accuracy > 85%: Increase difficulty slightly
- If accuracy < 50%: Decrease difficulty
- If accuracy 50-85%: Maintain current level
- Consider question type performance variations

Respond with JSON:
{{
    "recommended_difficulty": "beginner|intermediate|advanced",
    "reasoning": "explanation_for_adjustment",
    "focus_areas": ["concepts", "to", "emphasize"],
    "avoid_areas": ["concepts", "to", "avoid"]
}}
"""
```

## Answer Validation Prompts

### Open-Ended Answer Validation

**Purpose**: Evaluate free-form text responses

```python
ANSWER_VALIDATION_PROMPT = """
Evaluate the user's answer to an open-ended question.

QUESTION: "{question}"
CORRECT ANSWER: "{correct_answer}"
USER ANSWER: "{user_answer}"

EVALUATION CRITERIA:
1. ACCURACY: Does the answer contain the correct information?
2. COMPLETENESS: Does it address the key points?
3. UNDERSTANDING: Does it demonstrate comprehension of the concept?

SCORING GUIDELINES:
- CORRECT: Answer is accurate and demonstrates understanding
- PARTIALLY_CORRECT: Contains some correct elements but missing key points
- INCORRECT: Answer is wrong or shows misunderstanding

Be generous with partial credit for answers that show understanding even if not perfectly worded.

Respond with JSON:
{{
    "is_correct": true/false,
    "partial_credit": true/false,
    "score_percentage": 0-100,
    "feedback": "encouraging_feedback_with_explanation",
    "key_points_covered": ["points", "correctly", "addressed"],
    "missing_points": ["points", "not", "addressed"],
    "suggestion": "how_to_improve_or_expand_answer"
}}
"""
```

### Multiple Choice Validation

**Purpose**: Validate multiple choice responses with flexible input

```python
MC_VALIDATION_PROMPT = """
Validate a multiple choice answer, handling various input formats.

QUESTION: "{question}"
OPTIONS:
A) {option_a}
B) {option_b}
C) {option_c}
D) {option_d}

CORRECT ANSWER: {correct_answer}
USER ANSWER: "{user_answer}"

VALIDATION RULES:
- Accept: "A", "a", "Option A", "A)", "The first one", etc.
- Extract the letter choice from natural language responses
- Handle typos and variations in formatting

Respond with JSON:
{{
    "extracted_choice": "A|B|C|D|unclear",
    "is_correct": true/false,
    "confidence": 0.0-1.0,
    "feedback": "explanation_of_correct_answer"
}}
"""
```

## Clarification and Help Prompts

### Clarification Request Prompt

**Purpose**: Generate helpful clarification when user input is unclear

```python
CLARIFICATION_PROMPT = """
Generate a helpful clarification response for unclear user input.

CONTEXT:
- Current Phase: {current_phase}
- Current Question: {current_question}
- User Input: "{user_input}"
- Issue Type: {issue_type}

CLARIFICATION TYPES:

UNCLEAR_INTENT:
- User input doesn't match expected response format
- Provide examples of valid responses

TOPIC_UNCLEAR:
- User topic request is too vague or broad
- Suggest more specific alternatives

ANSWER_FORMAT:
- User answer format doesn't match question type
- Explain expected answer format with examples

GENERAL_CONFUSION:
- User seems lost or confused about the application
- Provide helpful guidance and options

Response should be:
- Friendly and encouraging
- Specific and actionable
- Include examples where helpful
- Offer multiple options when appropriate

Generate a helpful clarification message (plain text, no JSON needed).
"""
```

### Help System Prompt

**Purpose**: Provide contextual help based on user needs

```python
HELP_SYSTEM_PROMPT = """
Provide contextual help for the quiz application.

USER SITUATION:
- Current Phase: {current_phase}
- Help Request: "{user_input}"
- Quiz Status: {quiz_status}

HELP CATEGORIES:

GETTING_STARTED:
- How to start a quiz
- How to choose topics
- What to expect

DURING_QUIZ:
- How to answer different question types
- How to skip questions
- How to start over

SCORING:
- How scoring works
- What different question types are worth
- How to interpret results

NAVIGATION:
- Available commands
- How to exit or restart
- How to change topics mid-quiz

Provide helpful, specific guidance based on their current situation and request.
Response should be concise but complete.
"""
```

## Completion and Summary Prompts

### Quiz Summary Generation

**Purpose**: Generate comprehensive quiz completion summaries

```python
QUIZ_SUMMARY_PROMPT = """
Generate an engaging completion summary for the quiz.

QUIZ DATA:
- Topic: {topic}
- Total Questions: {total_questions}
- Correct Answers: {correct_answers}
- Final Score: {final_score}
- Accuracy: {accuracy}%
- Question Types: {question_type_breakdown}
- Strong Areas: {strong_areas}
- Improvement Areas: {weak_areas}

SUMMARY REQUIREMENTS:
1. Congratulatory and encouraging tone
2. Highlight achievements and progress
3. Provide specific feedback on performance
4. Suggest next steps or related topics
5. Include relevant emojis for engagement
6. Keep it concise but comprehensive

STRUCTURE:
- Opening congratulations
- Performance highlights
- Areas of strength
- Areas for improvement
- Suggestions for next steps

Generate an encouraging completion message (plain text).
"""
```

### Performance Analysis Prompt

**Purpose**: Analyze user performance patterns for insights

```python
PERFORMANCE_ANALYSIS_PROMPT = """
Analyze user performance patterns and provide educational insights.

PERFORMANCE DATA:
- Answer History: {answer_history}
- Question Types Performance: {type_performance}
- Difficulty Progression: {difficulty_progression}
- Time Patterns: {timing_data}

ANALYSIS FOCUS:
1. Learning pattern identification
2. Knowledge gap detection
3. Strength area recognition
4. Improvement recommendations
5. Next learning steps

Respond with JSON:
{{
    "learning_pattern": "consistent|improving|struggling|variable",
    "strongest_areas": ["area1", "area2"],
    "knowledge_gaps": ["gap1", "gap2"],
    "recommended_focus": ["focus1", "focus2"],
    "next_topics": ["topic1", "topic2"],
    "study_suggestions": ["suggestion1", "suggestion2"]
}}
"""
```

## Prompt Engineering Best Practices

### Template Structure Guidelines

1. **Clear Context**: Always provide relevant context variables
2. **Specific Instructions**: Be explicit about expected output format
3. **Examples**: Include examples for complex tasks
4. **Error Handling**: Account for edge cases and invalid inputs
5. **Consistent Formatting**: Use JSON for structured responses

### Variable Formatting Functions

```python
def format_recent_history(history: List[Dict]) -> str:
    """Format conversation history for prompt inclusion"""
    if not history:
        return "No previous conversation"
    
    formatted = []
    for entry in history[-3:]:  # Last 3 entries
        formatted.append(f"User: {entry.get('user', '')}")
        if entry.get('system'):
            formatted.append(f"System: {entry.get('system', '')}")
    
    return "\n".join(formatted)

def format_question_list(questions: List[str]) -> str:
    """Format previous questions for context"""
    if not questions:
        return "No previous questions"
    
    return "\n".join([f"{i+1}. {q}" for i, q in enumerate(questions)])

def format_performance_data(answers: List[Dict]) -> str:
    """Format answer history for analysis"""
    if not answers:
        return "No previous answers"
    
    recent = answers[-5:]  # Last 5 answers
    formatted = []
    for answer in recent:
        status = "✓" if answer['is_correct'] else "✗"
        formatted.append(f"{status} {answer['question'][:50]}...")
    
    return "\n".join(formatted)
```

### Prompt Testing and Validation

```python
def test_prompt_effectiveness(prompt_template: str, test_cases: List[Dict]):
    """Test prompt templates with various inputs"""
    results = []
    
    for case in test_cases:
        try:
            formatted_prompt = prompt_template.format(**case['input'])
            # Test with LLM
            response = llm_call(formatted_prompt)
            
            results.append({
                'input': case['input'],
                'expected': case['expected'],
                'actual': response,
                'passed': evaluate_response(response, case['expected'])
            })
        except Exception as e:
            results.append({
                'input': case['input'],
                'error': str(e),
                'passed': False
            })
    
    return results
```

## Prompt Optimization Strategies

### Response Time Optimization
- Keep prompts concise while maintaining clarity
- Use caching for frequently used prompt components
- Implement prompt compression techniques

### Accuracy Improvement
- Include few-shot examples for complex tasks
- Use chain-of-thought prompting for reasoning tasks
- Implement consistency checks across related prompts

### Cost Management
- Optimize prompt length without sacrificing quality
- Use appropriate model tiers for different prompt complexities
- Implement prompt result caching where appropriate 