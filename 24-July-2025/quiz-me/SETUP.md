# API Setup Guide for Interactive Quiz Generator

## 🚨 Current Status: API NOT CONFIGURED

The quiz application requires an OpenAI API key to function properly. Currently, the API is **not set up**.

## 📋 Required API Keys

### OpenAI API Key (REQUIRED)
- **Purpose**: Powers all LLM functionality (quiz generation, answer validation, etc.)
- **Cost**: ~$0.03 per 1K tokens (typical quiz uses 500-1000 tokens)
- **Get it from**: https://platform.openai.com/api-keys

## 🔧 Step-by-Step Setup

### 1️⃣ Get OpenAI API Key
1. Go to https://platform.openai.com/api-keys
2. Sign in or create an OpenAI account
3. Click "Create new secret key"
4. Copy the key (starts with `sk-...`)

### 2️⃣ Create Environment File
```bash
# Create .env file from example
cp .env.example .env
```

If `.env.example` doesn't exist, create `.env` with this content:
```bash
# Required API key
OPENAI_API_KEY=your_openai_api_key_here

# LLM Configuration
OPENAI_MODEL=gpt-4
OPENAI_TEMPERATURE=0.7
OPENAI_MAX_TOKENS=1000

# App Configuration  
APP_TITLE=Interactive Quiz Generator
MAX_QUESTIONS_DEFAULT=10
SESSION_TIMEOUT=1800
DEBUG=false

# Gradio Web Interface
GRADIO_SERVER_NAME=0.0.0.0
GRADIO_SERVER_PORT=7860
GRADIO_SHARE=false
```

### 3️⃣ Configure Your API Key
Edit the `.env` file and replace `your_openai_api_key_here` with your actual OpenAI API key:
```bash
OPENAI_API_KEY=sk-abc123def456...
```

### 4️⃣ Verify Setup
```bash
python -c "from src.utils import Config; print('✅ API Key configured!' if Config.OPENAI_API_KEY else '❌ Still missing')"
```

## ⚠️ Security & Best Practices

### Security Reminders
- **Never share your API key** with anyone
- **Never commit .env to git** (it's already in .gitignore)
- **Keep your API key private** and secure

### Cost Management
- OpenAI charges per token used
- GPT-4 costs approximately $0.03 per 1K tokens
- A typical quiz interaction uses 500-1000 tokens
- Monitor your usage at https://platform.openai.com/usage

## 🧪 Testing API Setup

Once configured, test the application:

```bash
# Test basic functionality
python -c "
from src.workflow import create_quiz_workflow
workflow = create_quiz_workflow()
print('✅ Workflow created successfully!')
"

# Test with a simple input
python -c "
from src.workflow import create_quiz_workflow
workflow = create_quiz_workflow()
result = workflow.process_input_sync('I want a Python quiz')
print('✅ API working!')
"
```

## 🚀 What Happens After Setup

Once the API is configured:
1. ✅ All LLM calls will work properly
2. ✅ Quiz generation will function
3. ✅ Answer validation will work
4. ✅ Complete workflow will be operational
5. ✅ Ready for Gradio web interface

## 🆘 Troubleshooting

### Common Issues
- **"Missing OPENAI_API_KEY"**: API key not set in .env
- **"Authentication failed"**: Invalid API key
- **"Rate limit exceeded"**: Too many requests, wait and retry
- **"Insufficient credits"**: Add billing to your OpenAI account

### Getting Help
- Check OpenAI documentation: https://platform.openai.com/docs
- Verify API key works: https://platform.openai.com/playground
- Monitor usage: https://platform.openai.com/usage

---

## Current Configuration Status

Run this to check your setup:
```bash
python -c "
from src.utils import Config
print('OPENAI_API_KEY:', '✅ Set' if Config.OPENAI_API_KEY else '❌ NOT SET')
print('Model:', Config.OPENAI_MODEL)
print('Temperature:', Config.OPENAI_TEMPERATURE)
print('Max Tokens:', Config.OPENAI_MAX_TOKENS)
"
``` 