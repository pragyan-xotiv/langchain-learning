"""Consolidated prompt template strings for the Interactive Quiz Generator

This module contains all LLM prompt templates used throughout the application.
Each template is a formatted string designed for specific AI tasks.
"""

# Intent Classification Template
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

# Topic Extraction Template
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

# Topic Validation Template
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

# Question Generation Template
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

# Answer Validation Template
ANSWER_VALIDATION_PROMPT = """
Evaluate the user's answer to a quiz question.

QUESTION: "{question}"
CORRECT ANSWER: "{correct_answer}"
USER ANSWER: "{user_answer}"
QUESTION TYPE: {question_type}

EVALUATION CRITERIA:
1. ACCURACY: Does the answer contain the correct information?
2. COMPLETENESS: Does it address the key points?
3. UNDERSTANDING: Does it demonstrate comprehension of the concept?

SCORING GUIDELINES:
- CORRECT: Answer is accurate and demonstrates understanding
- PARTIALLY_CORRECT: Contains some correct elements but missing key points
- INCORRECT: Answer is wrong or shows misunderstanding

For multiple choice questions, use exact matching.
For open-ended questions, be generous with partial credit for answers that show understanding even if not perfectly worded.

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

# Clarification Template
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

# Quiz Summary Template
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

__all__ = [
    "INTENT_CLASSIFICATION_PROMPT",
    "TOPIC_EXTRACTION_PROMPT", 
    "TOPIC_VALIDATION_PROMPT",
    "QUESTION_GENERATION_PROMPT",
    "ANSWER_VALIDATION_PROMPT",
    "CLARIFICATION_PROMPT",
    "QUIZ_SUMMARY_PROMPT"
] 