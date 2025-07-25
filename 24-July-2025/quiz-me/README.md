# 🧠 Interactive Quiz Generator

An intelligent, conversational quiz application powered by LangChain, LangGraph, and OpenAI.

## 🎯 Overview

The Interactive Quiz Generator is a sophisticated LLM-powered educational application that creates dynamic, personalized quiz experiences. Users can choose any topic, and the system intelligently generates questions, validates answers in real-time, and provides comprehensive feedback and scoring.

### ✨ Key Features

- **🎨 Dynamic Topic Selection**: Choose any subject with intelligent validation
- **❓ Smart Question Generation**: Creates diverse question types (multiple choice, open-ended, true/false)
- **✅ Real-time Answer Validation**: Intelligent scoring with detailed feedback
- **💬 Natural Conversation Flow**: Chat-based interface with intent recognition
- **📊 Comprehensive Scoring**: Progress tracking and performance analytics
- **🔄 Flexible Control**: Switch topics mid-quiz, get help, or exit anytime

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                   Interactive Quiz Generator                     │
├─────────────────────────────────────────────────────────────────┤
│  Gradio Interface → LangGraph Workflow → Processing Nodes        │
│       ↓                     ↓                      ↓            │
│  User Input → Query Analyzer → Topic Validator → Quiz Generator │
│                     ↓                ↓                ↓         │
│             Answer Validator ← Score Generator ← User Response   │
└─────────────────────────────────────────────────────────────────┘
```

### 🛠️ Tech Stack

- **[LangGraph](https://langchain-ai.github.io/langgraph/)**: State management and workflow orchestration
- **[LangChain](https://langchain.com/)**: LLM integration and prompt management
- **[OpenAI API](https://openai.com/)**: Language model provider (GPT-4)
- **[Gradio](https://gradio.app/)**: Web interface framework
- **[Pydantic](https://docs.pydantic.dev/)**: Data validation and serialization

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- OpenAI API key

### 1. Clone and Setup

```bash
git clone <repository-url>
cd quiz-me
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### 4. Validate Setup

```bash
python validate_setup.py
```

### 5. Run Application

```bash
python app.py
```

## 📁 Project Structure

```
quiz-me/
├── app.py                    # Main Gradio application entry point
├── requirements.txt          # Python dependencies
├── .env.example             # Environment variables template
├── validate_setup.py        # Setup validation script
├── src/                     # Core application modules (modular architecture)
│   ├── __init__.py         # Package initialization and imports
│   ├── workflow.py         # LangGraph workflow assembly
│   ├── utils.py            # Helper functions and configuration
│   ├── nodes/              # 🆕 Processing nodes package
│   │   ├── __init__.py     # Node function imports
│   │   ├── query_analyzer.py    # User input intent analysis
│   │   ├── topic_validator.py   # Topic appropriateness validation
│   │   ├── quiz_generator.py    # Question generation logic
│   │   ├── answer_validator.py  # Response evaluation and scoring
│   │   └── score_generator.py   # Progress tracking and analytics
│   ├── edges/              # 🆕 Routing logic package
│   │   ├── __init__.py     # Router function imports
│   │   ├── conversation_router.py     # Main conversation flow
│   │   ├── query_analyzer_router.py   # Post-analysis routing
│   │   ├── topic_validator_router.py  # Post-validation routing
│   │   ├── quiz_generator_router.py   # Post-generation routing
│   │   ├── answer_validator_router.py # Post-evaluation routing
│   │   └── score_generator_router.py  # Post-scoring routing
│   ├── prompts/            # 🆕 LLM prompt templates package
│   │   ├── __init__.py     # Prompt template imports
│   │   ├── prompt_types.py # Shared types and enumerations
│   │   ├── prompt_manager.py      # Template management system
│   │   ├── intent_classification.py  # Intent analysis prompts
│   │   ├── topic_extraction.py       # Topic extraction prompts
│   │   ├── topic_validation.py       # Topic validation prompts
│   │   ├── question_generation.py    # Question creation prompts
│   │   ├── answer_validation.py      # Answer evaluation prompts
│   │   ├── clarification.py          # Clarification request prompts
│   │   └── summary_generation.py     # Performance summary prompts
│   └── state/              # 🆕 State management package
│       ├── __init__.py     # State management imports
│       ├── state_types.py  # Enums and data structures
│       ├── quiz_state.py   # Main QuizState class (20+ fields)
│       ├── state_validators.py   # State transition validation
│       ├── state_serializers.py  # Serialization utilities
│       └── state_factory.py      # Factory functions for testing
├── tests/                  # Comprehensive test suite
│   ├── __init__.py
│   ├── conftest.py         # Test configuration and fixtures
│   ├── test_state.py       # State management tests
│   ├── test_prompts.py     # Prompt template tests
│   ├── test_nodes.py       # Node functionality tests
│   ├── test_edges.py       # Edge logic tests
│   ├── test_workflow.py    # Workflow integration tests
│   └── test_utils.py       # Utility function tests
└── docs/                   # Comprehensive documentation
    ├── overview.md         # System overview
    ├── state.md           # State management design
    ├── nodes.md           # Node architecture
    ├── edges.md           # Edge logic and transitions
    ├── flow.md            # Application flow
    ├── prompts.md         # Prompt templates
    ├── deployment.md      # Deployment guide
    └── implementation/    # Step-by-step implementation guides
        ├── 00-implementation-overview.md
        ├── 01-project-setup.md
        ├── 02-state-management.md
        ├── 03-prompt-templates.md
        ├── 04-node-implementations.md
        ├── 05-edge-logic.md
        ├── 06-workflow-assembly.md
        └── 07-gradio-interface.md
```

## 🔧 Development

### Implementation Status

| Component | Status | Implementation Guide |
|-----------|--------|---------------------|
| 📁 Project Setup | ✅ **Complete** | `docs/implementation/01-project-setup.md` |
| 🗂️ State Management | 🚧 **Ready for Implementation** | `docs/implementation/02-state-management.md` |
| 📝 Prompt Templates | 🚧 **Ready for Implementation** | `docs/implementation/03-prompt-templates.md` |
| ⚙️ Processing Nodes | 🚧 **Ready for Implementation** | `docs/implementation/04-node-implementations.md` |
| 🔀 Edge Logic | 🚧 **Ready for Implementation** | `docs/implementation/05-edge-logic.md` |
| 🔄 Workflow Assembly | 🚧 **Ready for Implementation** | `docs/implementation/06-workflow-assembly.md` |
| 🌐 Gradio Interface | 🚧 **Ready for Implementation** | `docs/implementation/07-gradio-interface.md` |

### 📋 Implementation Roadmap

**Phase 1: Foundation (Days 1-2)**
1. ✅ Project Setup - Complete
2. 🚧 State Management - Ready
3. 🚧 Prompt Templates - Ready

**Phase 2: Core Logic (Days 3-5)**
4. 🚧 Node Implementations - Ready
5. 🚧 Edge Logic - Ready
6. 🚧 Workflow Assembly - Ready

**Phase 3: Interface & Deployment (Days 6-7)**
7. 🚧 Gradio Interface - Ready
8. 🚧 Testing & Validation - Ready
9. 🚧 Deployment - Ready

### 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_utils.py

# Run tests with specific markers
pytest -m unit
pytest -m integration
```

### 🔍 Code Quality

```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Type checking
mypy src/

# Pre-commit hooks
pre-commit install
pre-commit run --all-files
```

## 📚 Documentation

### 🎯 For Understanding the System
1. **[Application Flow](docs/flow.md)** - Complete user journey
2. **[State Management](docs/state.md)** - Data flow and state schema
3. **[Node Architecture](docs/nodes.md)** - Processing logic details
4. **[Edge Logic](docs/edges.md)** - Routing and transitions

### 🛠️ For Implementation
- **[Implementation Overview](docs/implementation/00-implementation-overview.md)** - Complete roadmap
- **[Implementation Guides](docs/implementation/)** - Step-by-step instructions
- **[Deployment Guide](docs/deployment.md)** - Production deployment

## 🌐 Deployment

The application is designed for easy deployment to **Hugging Face Spaces**:

1. **Create Hugging Face Space**
2. **Upload project files**
3. **Configure environment variables**
4. **Automatic deployment**

See [docs/deployment.md](docs/deployment.md) for complete instructions.

## 🤝 Contributing

1. **Follow the implementation guides** in `docs/implementation/`
2. **Write tests** for all new functionality
3. **Use type hints** throughout
4. **Follow code quality standards** (black, isort, mypy)
5. **Update documentation** as needed

## 🔧 Troubleshooting

### Common Issues

**❌ Import Errors**
```bash
# Ensure proper setup
python validate_setup.py

# Check Python path
python -c "import sys; print(sys.path)"
```

**❌ Missing Dependencies**
```bash
# Install all requirements
pip install -r requirements.txt

# Check specific package
pip show gradio langgraph langchain
```

**❌ Environment Variables**
```bash
# Check configuration
python -c "from src.utils import Config; Config.log_configuration()"

# Validate .env file
cat .env.example
```

**❌ OpenAI API Issues**
```bash
# Test API key
curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models
```

### Getting Help

1. **Run validation script**: `python validate_setup.py`
2. **Check logs**: Look for detailed error messages
3. **Review documentation**: `docs/implementation/`
4. **Check test results**: `pytest -v`

## 📄 License

[Your License Here]

## 🙏 Acknowledgments

- **LangChain** team for the excellent LLM framework
- **LangGraph** for powerful workflow orchestration
- **Gradio** for making ML interfaces simple
- **OpenAI** for providing powerful language models

---

**Ready to build?** 🚀

1. Run `python validate_setup.py` to check your setup
2. Install dependencies with `pip install -r requirements.txt`
3. Configure your `.env` file with OpenAI API key
4. Follow the implementation guides in `docs/implementation/`
5. Start with Phase 1: State Management

**Questions?** Check the comprehensive documentation in the `docs/` directory! 