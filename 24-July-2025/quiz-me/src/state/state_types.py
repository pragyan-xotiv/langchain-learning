"""Enums and data structures for state management"""

from typing import Literal

# Type aliases for better readability and consistency
UserIntent = Literal[
    "start_quiz", "answer_question", "new_quiz", 
    "exit", "continue", "clarification"
]

QuizPhase = Literal[
    "topic_selection", "topic_validation", "quiz_active", 
    "question_answered", "quiz_complete"
]

QuestionType = Literal[
    "multiple_choice", "open_ended", "true_false", "fill_in_blank"
]

QuizType = Literal["finite", "infinite"] 