# Project Setup Implementation

## 🎯 Overview

This guide establishes the foundational project structure, dependencies, and development environment for the Interactive Quiz Generator application.

## 📁 Project Structure Creation

### Directory Structure

Create the following directory structure:

```bash
mkdir -p interactive-quiz-generator/{src,tests,docs/implementation}
cd interactive-quiz-generator

# Create main files
touch app.py README.md requirements.txt .env.example .gitignore

# Create source module files
touch src/__init__.py src/state.py src/nodes.py src/edges.py src/prompts.py src/workflow.py src/utils.py

# Create test files
touch tests/__init__.py tests/test_state.py tests/test_nodes.py tests/test_edges.py tests/test_workflow.py tests/test_integration.py
```

### File Purpose Overview

```
interactive-quiz-generator/
├── app.py                    # Main Gradio application entry point
├── requirements.txt          # Python dependencies
├── .env.example             # Environment variables template
├── .gitignore              # Git ignore patterns
├── README.md               # Project documentation
├── src/
│   ├── __init__.py         # Package initialization
│   ├── state.py            # QuizState Pydantic model
│   ├── nodes.py            # All 5 processing nodes
│   ├── edges.py            # Conditional routing logic
│   ├── prompts.py          # LLM prompt templates
│   ├── workflow.py         # LangGraph workflow assembly
│   └── utils.py            # Helper functions and utilities
├── tests/
│   ├── __init__.py
│   ├── test_state.py       # State management tests
│   ├── test_nodes.py       # Node functionality tests
│   ├── test_edges.py       # Edge logic tests
│   ├── test_workflow.py    # Workflow integration tests
│   └── test_integration.py # End-to-end tests
└── docs/
    ├── implementation/     # Implementation guides (this folder)
    └── ...                # Design documentation
```

## 📦 Dependencies Configuration

### requirements.txt

Create comprehensive dependencies file:

```txt
# Core Framework Dependencies
gradio>=4.0.0
langgraph>=0.1.0
langchain>=0.1.0
langchain-openai>=0.1.0

# LLM Provider
openai>=1.0.0

# Data Models and Validation
pydantic>=2.0.0
typing-extensions>=4.0.0

# Environment and Configuration
python-dotenv>=1.0.0

# Async Support
aiohttp>=3.8.0
asyncio>=3.4.3

# Data Processing
pandas>=1.5.0
numpy>=1.24.0

# Development Dependencies
pytest>=7.0.0
pytest-asyncio>=0.21.0
black>=23.0.0
isort>=5.12.0
mypy>=1.0.0
pre-commit>=3.0.0

# Optional: Enhanced Features
redis>=4.0.0              # Session persistence
streamlit>=1.28.0          # Alternative UI framework
```

### Development Dependencies Setup

```bash
# Install core dependencies
pip install -r requirements.txt

# Install development tools
pip install pytest black isort mypy pre-commit

# Set up pre-commit hooks
pre-commit install
```

## 🔧 Environment Configuration

### .env.example

Create environment variables template:

```env
# LLM Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4
OPENAI_TEMPERATURE=0.7
OPENAI_MAX_TOKENS=1000

# App Configuration
APP_TITLE="Interactive Quiz Generator"
MAX_QUESTIONS_DEFAULT=10
SESSION_TIMEOUT=1800
DEBUG=False

# Gradio Configuration
GRADIO_SERVER_NAME=0.0.0.0
GRADIO_SERVER_PORT=7860
GRADIO_SHARE=False

# Optional: Advanced Features
REDIS_URL=redis://localhost:6379
DATABASE_URL=postgresql://user:pass@localhost/quizdb
LOG_LEVEL=INFO

# Development Settings
ENVIRONMENT=development
ENABLE_CACHING=True
MOCK_LLM_RESPONSES=False
```

### Environment Loading Setup

Create environment configuration utilities in `src/utils.py`:

```python
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration from environment variables"""
    
    # LLM Configuration
    OPENAI_API_KEY: str = os.getenv('OPENAI_API_KEY', '')
    OPENAI_MODEL: str = os.getenv('OPENAI_MODEL', 'gpt-4')
    OPENAI_TEMPERATURE: float = float(os.getenv('OPENAI_TEMPERATURE', '0.7'))
    OPENAI_MAX_TOKENS: int = int(os.getenv('OPENAI_MAX_TOKENS', '1000'))
    
    # App Configuration
    APP_TITLE: str = os.getenv('APP_TITLE', 'Interactive Quiz Generator')
    MAX_QUESTIONS_DEFAULT: int = int(os.getenv('MAX_QUESTIONS_DEFAULT', '10'))
    SESSION_TIMEOUT: int = int(os.getenv('SESSION_TIMEOUT', '1800'))
    DEBUG: bool = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Gradio Configuration
    GRADIO_SERVER_NAME: str = os.getenv('GRADIO_SERVER_NAME', '0.0.0.0')
    GRADIO_SERVER_PORT: int = int(os.getenv('GRADIO_SERVER_PORT', '7860'))
    GRADIO_SHARE: bool = os.getenv('GRADIO_SHARE', 'False').lower() == 'true'
    
    # Optional Features
    REDIS_URL: Optional[str] = os.getenv('REDIS_URL')
    DATABASE_URL: Optional[str] = os.getenv('DATABASE_URL')
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    
    # Development Settings
    ENVIRONMENT: str = os.getenv('ENVIRONMENT', 'development')
    ENABLE_CACHING: bool = os.getenv('ENABLE_CACHING', 'True').lower() == 'true'
    MOCK_LLM_RESPONSES: bool = os.getenv('MOCK_LLM_RESPONSES', 'False').lower() == 'true'
    
    @classmethod
    def validate_required(cls) -> None:
        """Validate that required environment variables are set"""
        required_vars = ['OPENAI_API_KEY']
        missing_vars = [var for var in required_vars if not getattr(cls, var)]
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {missing_vars}")

# Validate configuration on import
Config.validate_required()
```

## 📝 Git Configuration

### .gitignore

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
env/
ENV/

# Environment Variables
.env
.env.local
.env.*.local

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Logs
*.log
logs/

# Cache
.cache/
.pytest_cache/
.mypy_cache/

# Jupyter
.ipynb_checkpoints/

# Application Specific
session_data/
quiz_cache/
user_data/
```

## 🧪 Testing Setup

### pytest Configuration

Create `pytest.ini`:

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --verbose
    --tb=short
    --strict-markers
    --disable-warnings
    --cov=src
    --cov-report=term-missing
    --cov-report=html

markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    unit: marks tests as unit tests
    llm: marks tests that require LLM API calls
```

### Basic Test Structure

Create basic test files structure:

```python
# tests/conftest.py
import pytest
from src.state import QuizState
from src.utils import Config

@pytest.fixture
def sample_state():
    """Create a sample QuizState for testing"""
    return QuizState(
        user_input="Test input",
        topic="Python Programming",
        topic_validated=True,
        current_phase="quiz_active"
    )

@pytest.fixture
def mock_config():
    """Mock configuration for testing"""
    Config.MOCK_LLM_RESPONSES = True
    yield Config
    Config.MOCK_LLM_RESPONSES = False
```

## 🔍 Code Quality Setup

### Pre-commit Configuration

Create `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-json
      - id: check-merge-conflict

  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ["--profile", "black"]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

### Type Checking Configuration

Create `mypy.ini`:

```ini
[mypy]
python_version = 3.8
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
disallow_incomplete_defs = True
check_untyped_defs = True
disallow_untyped_decorators = True
no_implicit_optional = True
warn_redundant_casts = True
warn_unused_ignores = True
warn_no_return = True
warn_unreachable = True
strict_equality = True

[mypy-gradio.*]
ignore_missing_imports = True

[mypy-langgraph.*]
ignore_missing_imports = True

[mypy-langchain.*]
ignore_missing_imports = True
```

## 📋 Initial Implementation Checklist

### Phase 1: Setup Verification

- [ ] **Directory Structure**: All directories and files created
- [ ] **Dependencies**: `requirements.txt` installed without errors
- [ ] **Environment**: `.env` file created with valid API key
- [ ] **Git**: Repository initialized with proper `.gitignore`
- [ ] **Testing**: `pytest` runs without errors (even if no tests yet)
- [ ] **Code Quality**: Pre-commit hooks installed and working
- [ ] **Type Checking**: `mypy` runs without errors on empty modules

### Phase 1: Basic Module Creation

Create basic module structure:

```python
# src/__init__.py
"""Interactive Quiz Generator - Core Package"""

__version__ = "1.0.0"
__author__ = "Your Name"

# src/state.py
"""State management for the quiz application"""
# (Content will be added in 02-state-management.md)

# src/nodes.py
"""Processing nodes for the quiz workflow"""
# (Content will be added in 04-node-implementations.md)

# src/edges.py
"""Edge logic and routing for the quiz workflow"""
# (Content will be added in 05-edge-logic.md)

# src/prompts.py
"""LLM prompt templates and management"""
# (Content will be added in 03-prompt-templates.md)

# src/workflow.py
"""LangGraph workflow assembly"""
# (Content will be added in 06-workflow-assembly.md)
```

## 🚀 Validation Steps

### Environment Validation

Create a validation script `validate_setup.py`:

```python
#!/usr/bin/env python3
"""Setup validation script"""

import os
import sys
from pathlib import Path

def validate_environment():
    """Validate development environment setup"""
    print("🔍 Validating Interactive Quiz Generator Setup...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        return False
    print(f"✅ Python {sys.version}")
    
    # Check required files
    required_files = [
        'requirements.txt', '.env.example', '.gitignore',
        'src/__init__.py', 'src/state.py', 'src/nodes.py',
        'tests/__init__.py'
    ]
    
    for file_path in required_files:
        if not Path(file_path).exists():
            print(f"❌ Missing required file: {file_path}")
            return False
    print("✅ All required files present")
    
    # Check environment variables
    if not os.getenv('OPENAI_API_KEY'):
        print("⚠️  OPENAI_API_KEY not set (required for full functionality)")
    else:
        print("✅ OPENAI_API_KEY configured")
    
    # Test imports
    try:
        import gradio
        import langgraph
        import langchain
        import pydantic
        print("✅ All core dependencies importable")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    
    print("\n🎉 Setup validation completed successfully!")
    print("📋 Next step: Proceed to 02-state-management.md")
    return True

if __name__ == "__main__":
    success = validate_environment()
    sys.exit(0 if success else 1)
```

Run validation:
```bash
python validate_setup.py
```

## 📝 README.md Template

Create initial project README:

```markdown
# Interactive Quiz Generator

An intelligent, conversational quiz application powered by LangChain, LangGraph, and OpenAI.

## 🚀 Quick Start

1. **Clone and Setup**
   ```bash
   git clone <repository-url>
   cd interactive-quiz-generator
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

3. **Run Application**
   ```bash
   python app.py
   ```

## 📁 Project Structure

- `src/` - Core application modules
- `tests/` - Test suite
- `docs/` - Documentation
- `app.py` - Main application entry point

## 🛠 Development

See `docs/implementation/` for detailed implementation guides.

## 📄 License

[Your License Here]
```

---

## ✅ Completion Criteria

Project setup is complete when:

1. **All files and directories created** as specified
2. **Dependencies install without errors**
3. **Environment variables configured**
4. **Validation script passes all checks**
5. **Git repository initialized** with proper ignore patterns
6. **Code quality tools configured** and working

**Next Step**: Proceed to **[02-state-management.md](./02-state-management.md)** to implement the QuizState class. 