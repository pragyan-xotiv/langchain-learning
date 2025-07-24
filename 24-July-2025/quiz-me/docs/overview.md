# Interactive Quiz Generator - Overview

## What is the Interactive Quiz Generator?

The Interactive Quiz Generator is a sophisticated LLM-powered application built with LangChain and LangGraph that creates dynamic, personalized quiz experiences. The app intelligently manages the entire quiz lifecycle - from topic validation to question generation, answer evaluation, and scoring.

## Key Features

- **Dynamic Topic Selection**: Users can choose any quiz topic, which is validated for appropriateness and feasibility
- **Intelligent Question Generation**: Creates either finite or infinite question sets based on the selected topic
- **Real-time Answer Validation**: Evaluates user responses and provides immediate feedback
- **Contextual Intent Recognition**: Uses a query analyzer to understand user intent at any point in the conversation
- **Flexible User Control**: Users can start new quizzes, exit, or navigate the app naturally using conversational commands
- **Comprehensive Scoring**: Tracks and calculates quiz performance with detailed feedback

## How It Works

The application uses a state-driven architecture powered by LangGraph, where each interaction flows through specialized nodes that handle different aspects of the quiz experience. The system maintains context throughout the entire session, allowing for natural conversation flow while ensuring proper quiz progression.

### Core Components

1. **State Management**: Centralized state object tracks all quiz data and user progress
2. **Node Network**: Specialized processing nodes handle specific tasks (analysis, validation, generation, scoring)
3. **Edge Logic**: Smart transitions between nodes based on current state and user input
4. **LLM Integration**: Strategic use of language models for content generation and validation

## Architecture Overview

```
User Input → Query Analyzer → Topic Validator → Quiz Generator
                ↓               ↓                    ↓
            Intent Detection   Topic Validation   Question Creation
                ↓               ↓                    ↓
         Answer Validator ← Score Generator ← User Response
```

## Documentation Structure

This documentation is organized into the following sections:

### Technical Documentation

- **[State Management](./state.md)** - Complete state object schema and update patterns
- **[Node Architecture](./nodes.md)** - Detailed description of each processing node
- **[Edge Logic](./edges.md)** - Transition rules and conditional flows
- **[Application Flow](./flow.md)** - Step-by-step user journey and system behavior

### Implementation Guides

- **[Prompt Templates](./prompts.md)** - LLM prompt examples and best practices
- **[Deployment Guide](./deployment.md)** - Complete setup, tech stack, and hosting instructions

## Getting Started

**For Understanding the System:**
1. Start with **[Application Flow](./flow.md)** to understand the user experience
2. Review **[State Management](./state.md)** to understand data flow
3. Explore **[Node Architecture](./nodes.md)** for implementation details
4. Check **[Edge Logic](./edges.md)** for transition rules
5. Reference **[Prompt Templates](./prompts.md)** for LLM integration patterns

**For Implementation and Deployment:**
- Jump to **[Deployment Guide](./deployment.md)** for complete setup instructions, tech stack details, and hosting on Hugging Face Spaces

## Technology Stack

- **LangChain**: Framework for LLM application development
- **LangGraph**: State graph orchestration and workflow management
- **Python**: Core implementation language
- **OpenAI/Anthropic APIs**: Language model providers

---

*This documentation provides a comprehensive guide to understanding, maintaining, and extending the Interactive Quiz Generator application.* 