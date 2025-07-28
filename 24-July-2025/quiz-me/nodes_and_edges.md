# Quiz App
Conversational quiz application

## Nodes

- **query_analyzer** - Analyses user input
- **topic_validator** - Validates user topic
- **quiz_generator** - Generates quiz
- **answer_validator** - Validates answers
- **score_generator** - Genearates score and final result

## Flow

1. User asks query.

2. query_analyzer analyzes query.
   - If analyzer says its a 'topic', it will be route to topic_validator
   - If analyzer says its an 'answer', it will be route to answer_validator

3. topic_validator validates topic.
   - If topic is not valid like explicit content it will return back to the user.
   - If topic is valid route to quiz_generator.

4. answer_validator validates answer
   - it routes to score_generator.

5. score_generator generates score.
   - If quiz finish show final result to the user
   - If not then route to quiz_generator.

6. quiz_generator generates quiz and sends back to user.
    