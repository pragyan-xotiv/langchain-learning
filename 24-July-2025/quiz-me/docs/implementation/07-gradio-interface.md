# Gradio Interface Implementation

## 🎯 Overview

This guide implements the Gradio web interface that provides users with an intuitive chat-based interaction with the Interactive Quiz Generator. The interface handles real-time conversations and integrates seamlessly with the LangGraph workflow.

## 📋 Reference Documents

- **Design Specification**: `../deployment.md` (UI section)
- **Previous Step**: `06-workflow-assembly.md`
- **Next Step**: `08-api-integration.md`

## 🏗️ Gradio Interface Implementation

Create the main application file `app.py`:

```python
"""Main Gradio application for the Interactive Quiz Generator"""

import gradio as gr
import asyncio
import logging
from typing import List, Tuple, Optional
from datetime import datetime
import os

from src.workflow import create_quiz_workflow, QuizWorkflow
from src.state import QuizState, create_initial_state
from src.utils import Config

# Configure logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class QuizApplication:
    """Main application class that manages the Gradio interface and workflow"""
    
    def __init__(self):
        """Initialize the quiz application"""
        self.workflow: Optional[QuizWorkflow] = None
        self.current_state: Optional[QuizState] = None
        self.session_history: List[Tuple[str, str]] = []
        self._initialize_workflow()
    
    def _initialize_workflow(self):
        """Initialize the quiz workflow"""
        try:
            logger.info("Initializing quiz workflow...")
            self.workflow = create_quiz_workflow()
            self.current_state = create_initial_state()
            logger.info("Quiz workflow initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize workflow: {str(e)}")
            self.workflow = None
    
    def chat_interface(self, message: str, history: List[List[str]]) -> Tuple[List[List[str]], str]:
        """
        Main chat interface handler for Gradio.
        
        Args:
            message: User's input message
            history: Chat history as list of [user_message, bot_message] pairs
            
        Returns:
            Tuple of (updated_history, empty_string_for_textbox)
        """
        logger.info(f"Processing user message: '{message}'")
        
        try:
            # Check if workflow is available
            if not self.workflow:
                error_response = "❌ System not properly initialized. Please refresh the page."
                history.append([message, error_response])
                return history, ""
            
            # Process the message through workflow
            self.current_state = self.workflow.process_input_sync(message, self.current_state)
            
            # Generate response based on current state
            response = self.workflow.get_response_for_state(self.current_state)
            
            # Add to history
            history.append([message, response])
            
            # Store in session history
            self.session_history.append((message, response))
            
            logger.info(f"Response generated successfully, current phase: {self.current_state.current_phase}")
            
            return history, ""
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            error_response = f"🚨 Sorry, I encountered an error: {str(e)}\n\nPlease try again or refresh the page."
            history.append([message, error_response])
            return history, ""
    
    def reset_quiz(self) -> Tuple[List, str]:
        """
        Reset the quiz session.
        
        Returns:
            Tuple of (empty_history, welcome_message)
        """
        logger.info("Resetting quiz session")
        
        try:
            self.current_state = create_initial_state()
            self.session_history = []
            
            welcome_message = "🔄 **Quiz Reset!**\n\nWhat topic would you like to explore today?"
            
            return [], welcome_message
            
        except Exception as e:
            logger.error(f"Error resetting quiz: {str(e)}")
            return [], f"Error resetting quiz: {str(e)}"
    
    def clear_chat(self) -> Tuple[List, str]:
        """
        Clear the chat history but keep the current state.
        
        Returns:
            Tuple of (empty_history, empty_textbox)
        """
        logger.info("Clearing chat history")
        return [], ""
    
    def get_session_stats(self) -> str:
        """Get current session statistics"""
        if not self.current_state:
            return "No active session"
        
        stats = f"""📊 **Session Statistics**

**Current Quiz:**
- Topic: {self.current_state.topic or 'Not selected'}
- Phase: {self.current_state.current_phase}
- Questions Answered: {self.current_state.total_questions_answered}
- Current Score: {self.current_state.total_score}
- Accuracy: {self.current_state.calculate_accuracy():.1f}%

**Session Info:**
- Total Interactions: {len(self.session_history)}
- Session ID: {self.current_state.session_id[:8]}...
- Started: {self.current_state.created_at.strftime('%H:%M:%S')}
"""
        return stats

# Global application instance
app_instance = QuizApplication()

def create_gradio_interface() -> gr.Blocks:
    """Create and configure the Gradio interface"""
    
    # Custom CSS for enhanced styling
    custom_css = """
    .gradio-container {
        max-width: 900px !important;
        margin: auto !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    .chat-message {
        padding: 15px;
        margin: 8px 0;
        border-radius: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        text-align: right;
    }
    
    .bot-message {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
    }
    
    .quiz-title {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        font-size: 2.5em;
        font-weight: bold;
        margin-bottom: 20px;
    }
    
    .stats-panel {
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
    }
    
    .control-button {
        margin: 5px;
        padding: 10px 20px;
        border-radius: 8px;
        font-weight: 500;
    }
    
    .primary-button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
    }
    
    .secondary-button {
        background: #6c757d;
        color: white;
        border: none;
    }
    
    .danger-button {
        background: #dc3545;
        color: white;
        border: none;
    }
    
    .footer-text {
        text-align: center;
        color: #6c757d;
        font-size: 0.9em;
        margin-top: 20px;
    }
    """
    
    # Create the Gradio interface
    with gr.Blocks(
        title=Config.APP_TITLE,
        theme=gr.themes.Soft(
            primary_hue="blue",
            secondary_hue="purple",
            neutral_hue="gray"
        ),
        css=custom_css
    ) as interface:
        
        # Header
        gr.HTML(f"""
        <div class="quiz-title">
            🧠 {Config.APP_TITLE}
        </div>
        """)
        
        gr.Markdown("""
        <div style="text-align: center; margin-bottom: 30px;">
        
        **Welcome to your personalized learning companion!** 🎯
        
        Choose any topic and I'll create engaging quiz questions tailored just for you.
        Get instant feedback, track your progress, and learn at your own pace.
        
        </div>
        """)
        
        # Instructions Panel
        with gr.Accordion("📖 How to Use", open=False):
            gr.Markdown("""
            ### Getting Started
            1. **Choose a Topic**: Type any subject you'd like to learn about
               - *Examples: "Python programming", "World War II", "Basic chemistry"*
            
            2. **Answer Questions**: Respond in your own words
               - For multiple choice: Say the letter (A, B, C, D) or the full answer
               - For open questions: Explain in your own words
            
            3. **Get Feedback**: Receive instant explanations and scoring
            
            4. **Switch Topics**: Say "new quiz" anytime to change subjects
            
            5. **Exit**: Type "exit" when you're finished
            
            ### Tips for Best Experience
            - Be specific with your topics (e.g., "JavaScript arrays" vs "programming")
            - Take your time to think through answers
            - Ask for clarification if you're unsure about anything
            """)
        
        # Main Chat Interface
        with gr.Row():
            with gr.Column(scale=4):
                chatbot = gr.Chatbot(
                    value=[],
                    height=500,
                    show_label=False,
                    container=True,
                    bubble_full_width=False,
                    avatar_images=(
                        "https://cdn-icons-png.flaticon.com/512/3135/3135715.png",  # User avatar
                        "https://cdn-icons-png.flaticon.com/512/4712/4712109.png"   # Bot avatar
                    )
                )
            
            with gr.Column(scale=1, min_width=200):
                # Statistics Panel
                stats_display = gr.Markdown(
                    value="📊 **Session Stats**\n\nStart a quiz to see statistics!",
                    elem_classes=["stats-panel"]
                )
                
                # Control Buttons
                with gr.Column():
                    stats_button = gr.Button(
                        "📊 Show Stats",
                        elem_classes=["control-button", "primary-button"]
                    )
                    
                    reset_button = gr.Button(
                        "🔄 New Quiz",
                        elem_classes=["control-button", "secondary-button"]
                    )
                    
                    clear_button = gr.Button(
                        "🗑️ Clear Chat",
                        elem_classes=["control-button", "secondary-button"]
                    )
                    
                    help_button = gr.Button(
                        "❓ Get Help",
                        elem_classes=["control-button", "secondary-button"]
                    )
        
        # Input Section
        with gr.Row():
            with gr.Column(scale=5):
                msg_input = gr.Textbox(
                    placeholder="💬 What topic would you like to be quizzed on? (e.g., 'Python programming', 'World history')",
                    show_label=False,
                    container=False,
                    lines=2,
                    max_lines=4
                )
            
            with gr.Column(scale=1, min_width=100):
                send_button = gr.Button(
                    "Send 🚀",
                    variant="primary",
                    elem_classes=["control-button", "primary-button"]
                )
        
        # Quick Start Buttons
        with gr.Row():
            gr.Markdown("**🚀 Quick Start Topics:**")
        
        with gr.Row():
            quick_topics = [
                "Python Programming", "World War II", "Basic Chemistry",
                "Shakespeare", "Solar System", "Machine Learning"
            ]
            
            topic_buttons = []
            for topic in quick_topics:
                btn = gr.Button(
                    topic,
                    size="sm",
                    variant="secondary"
                )
                topic_buttons.append(btn)
        
        # Footer
        gr.HTML("""
        <div class="footer-text">
            <p>Powered by <strong>LangChain</strong>, <strong>LangGraph</strong>, and <strong>OpenAI</strong></p>
            <p>Built with ❤️ for interactive learning</p>
        </div>
        """)
        
        # Event Handlers
        
        # Main chat functionality
        msg_input.submit(
            fn=app_instance.chat_interface,
            inputs=[msg_input, chatbot],
            outputs=[chatbot, msg_input]
        )
        
        send_button.click(
            fn=app_instance.chat_interface,
            inputs=[msg_input, chatbot],
            outputs=[chatbot, msg_input]
        )
        
        # Control buttons
        reset_button.click(
            fn=app_instance.reset_quiz,
            outputs=[chatbot, msg_input]
        )
        
        clear_button.click(
            fn=app_instance.clear_chat,
            outputs=[chatbot, msg_input]
        )
        
        stats_button.click(
            fn=app_instance.get_session_stats,
            outputs=[stats_display]
        )
        
        # Help button
        def show_help():
            help_text = """💡 **Need Help?**

**Starting a Quiz:**
- Type any topic: "I want a quiz about [topic]"
- Or just the topic name: "Python programming"

**During the Quiz:**
- Answer in your own words
- For multiple choice, say the letter: "A", "B", "C", or "D"
- Ask for clarification: "I don't understand"

**Quiz Control:**
- New topic: "new quiz" or "start over"
- Exit: "exit", "quit", or "done"
- Continue: "next question" or "continue"

**Having Issues?**
- Try refreshing the page
- Use more specific topics
- Check your internet connection
"""
            return help_text
        
        help_button.click(
            fn=show_help,
            outputs=[stats_display]
        )
        
        # Quick topic buttons
        def create_topic_handler(topic):
            def handler():
                return f"I want a quiz about {topic}"
            return handler
        
        for i, (topic, btn) in enumerate(zip(quick_topics, topic_buttons)):
            btn.click(
                fn=create_topic_handler(topic),
                outputs=[msg_input]
            )
    
    return interface

def launch_application():
    """Launch the Gradio application"""
    logger.info("Launching Interactive Quiz Generator...")
    
    try:
        # Validate configuration
        Config.validate_required()
        
        # Create interface
        interface = create_gradio_interface()
        
        # Launch with configuration
        interface.launch(
            server_name=Config.GRADIO_SERVER_NAME,
            server_port=Config.GRADIO_SERVER_PORT,
            share=Config.GRADIO_SHARE,
            debug=Config.DEBUG,
            show_error=True,
            quiet=False,
            favicon_path=None,  # Add custom favicon if available
            app_kwargs={
                "title": Config.APP_TITLE,
                "description": "An intelligent quiz generator powered by AI"
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to launch application: {str(e)}")
        print(f"❌ Application launch failed: {str(e)}")
        print("Please check your configuration and try again.")

# Development utilities
def create_demo_interface():
    """Create a simplified demo interface for testing"""
    
    def simple_chat(message, history):
        response = f"Echo: {message} (Demo mode - workflow not connected)"
        history.append([message, response])
        return history, ""
    
    with gr.Blocks(title="Quiz Generator Demo") as demo:
        gr.Markdown("# 🧠 Interactive Quiz Generator (Demo Mode)")
        
        chatbot = gr.Chatbot(height=400)
        msg = gr.Textbox(placeholder="Type a message...")
        
        msg.submit(simple_chat, [msg, chatbot], [chatbot, msg])
        
        gr.Button("Clear").click(lambda: ([], ""), outputs=[chatbot, msg])
    
    return demo

def test_interface_components():
    """Test interface components in isolation"""
    logger.info("Testing interface components...")
    
    try:
        # Test application instance creation
        test_app = QuizApplication()
        logger.info("✅ Application instance created successfully")
        
        # Test chat interface with mock data
        history = []
        result_history, result_msg = test_app.chat_interface("Hello", history)
        logger.info("✅ Chat interface responds to input")
        
        # Test reset functionality
        reset_history, reset_msg = test_app.reset_quiz()
        logger.info("✅ Reset functionality works")
        
        # Test stats
        stats = test_app.get_session_stats()
        logger.info("✅ Stats generation works")
        
        logger.info("All interface components tested successfully")
        
    except Exception as e:
        logger.error(f"Interface component test failed: {str(e)}")
        raise

if __name__ == "__main__":
    # Check if we're in demo mode
    if os.getenv("DEMO_MODE", "false").lower() == "true":
        logger.info("Starting in demo mode...")
        demo = create_demo_interface()
        demo.launch()
    else:
        # Test components first
        test_interface_components()
        
        # Launch full application
        launch_application()
```

## 🎨 Advanced Interface Components

Create additional interface utilities in `src/interface_utils.py`:

```python
"""Utilities for Gradio interface enhancement"""

import gradio as gr
from typing import List, Dict, Any, Tuple
import json
from datetime import datetime

def create_progress_bar(current: int, total: int) -> str:
    """Create a progress bar visualization"""
    if total == 0:
        return "No progress"
    
    percentage = (current / total) * 100
    filled = int(percentage / 10)
    bar = "█" * filled + "░" * (10 - filled)
    
    return f"Progress: {bar} {percentage:.1f}% ({current}/{total})"

def format_quiz_results(state) -> str:
    """Format quiz results for display"""
    if not state or state.total_questions_answered == 0:
        return "No quiz data available"
    
    accuracy = state.calculate_accuracy()
    performance_summary = state.get_performance_summary()
    
    # Performance emoji
    if accuracy >= 90:
        emoji = "🏆"
        level = "Excellent"
    elif accuracy >= 80:
        emoji = "🥇"
        level = "Great"
    elif accuracy >= 70:
        emoji = "🥈"
        level = "Good"
    elif accuracy >= 60:
        emoji = "🥉"
        level = "Fair"
    else:
        emoji = "📚"
        level = "Keep Learning"
    
    results = f"""
{emoji} **{level} Performance!**

**📊 Results Summary:**
- **Topic:** {state.topic}
- **Questions:** {state.total_questions_answered}
- **Correct:** {state.correct_answers_count}
- **Accuracy:** {accuracy:.1f}%
- **Score:** {state.total_score} points

{create_progress_bar(state.correct_answers_count, state.total_questions_answered)}

**💡 Quick Stats:**
- Session Duration: {(state.updated_at - state.created_at).total_seconds():.0f} seconds
- Average Score per Question: {state.total_score / max(state.total_questions_answered, 1):.1f}
"""
    
    return results

def create_topic_suggestions(category: str = "popular") -> List[str]:
    """Generate topic suggestions by category"""
    
    suggestions = {
        "popular": [
            "Python Programming", "JavaScript Basics", "World War II", 
            "Basic Chemistry", "Shakespeare", "Solar System",
            "Machine Learning", "European History", "Human Biology"
        ],
        "academic": [
            "Calculus", "Organic Chemistry", "Classical Literature",
            "Modern Physics", "European Art History", "Microeconomics",
            "Cell Biology", "Linear Algebra", "Political Science"
        ],
        "technology": [
            "React.js", "Data Structures", "Web APIs", "Docker",
            "Kubernetes", "TypeScript", "GraphQL", "AWS Services",
            "Database Design", "Cybersecurity Basics"
        ],
        "science": [
            "Quantum Physics", "Genetics", "Climate Science",
            "Astronomy", "Biochemistry", "Neuroscience",
            "Evolution", "Periodic Table", "Photosynthesis"
        ],
        "arts": [
            "Renaissance Art", "Classical Music", "Modern Dance",
            "Photography", "Film History", "Theater", "Poetry",
            "Sculpture", "Color Theory", "Art Movements"
        ]
    }
    
    return suggestions.get(category, suggestions["popular"])

def create_accessibility_features():
    """Create accessibility enhancement components"""
    
    accessibility_css = """
    /* High contrast mode */
    .high-contrast {
        filter: contrast(150%) brightness(120%);
    }
    
    /* Large text mode */
    .large-text {
        font-size: 1.2em !important;
        line-height: 1.6 !important;
    }
    
    /* Focus indicators */
    button:focus, input:focus, textarea:focus {
        outline: 3px solid #4A90E2 !important;
        outline-offset: 2px !important;
    }
    
    /* Screen reader friendly */
    .sr-only {
        position: absolute;
        width: 1px;
        height: 1px;
        padding: 0;
        margin: -1px;
        overflow: hidden;
        clip: rect(0, 0, 0, 0);
        white-space: nowrap;
        border: 0;
    }
    """
    
    return accessibility_css

def create_keyboard_shortcuts():
    """Define keyboard shortcuts for the interface"""
    
    shortcuts_js = """
    function setupKeyboardShortcuts() {
        document.addEventListener('keydown', function(e) {
            // Ctrl/Cmd + Enter to send message
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                const sendButton = document.querySelector('button[variant="primary"]');
                if (sendButton) sendButton.click();
            }
            
            // Ctrl/Cmd + R to reset quiz
            if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
                e.preventDefault();
                const resetButton = document.querySelector('button:contains("New Quiz")');
                if (resetButton) resetButton.click();
            }
            
            // Ctrl/Cmd + H for help
            if ((e.ctrlKey || e.metaKey) && e.key === 'h') {
                e.preventDefault();
                const helpButton = document.querySelector('button:contains("Get Help")');
                if (helpButton) helpButton.click();
            }
            
            // ESC to clear input
            if (e.key === 'Escape') {
                const textInput = document.querySelector('textarea');
                if (textInput) textInput.value = '';
            }
        });
    }
    
    // Setup shortcuts when page loads
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', setupKeyboardShortcuts);
    } else {
        setupKeyboardShortcuts();
    }
    """
    
    return shortcuts_js

def create_export_functionality(session_data: Dict[str, Any]) -> str:
    """Create session data export functionality"""
    
    export_data = {
        "session_id": session_data.get("session_id"),
        "timestamp": datetime.now().isoformat(),
        "quiz_topic": session_data.get("topic"),
        "questions_answered": session_data.get("total_questions", 0),
        "correct_answers": session_data.get("correct_answers", 0),
        "total_score": session_data.get("total_score", 0),
        "accuracy": session_data.get("accuracy", 0),
        "conversation_history": session_data.get("conversation_history", [])
    }
    
    return json.dumps(export_data, indent=2)

def create_responsive_layout():
    """Create responsive CSS for mobile devices"""
    
    responsive_css = """
    /* Mobile responsiveness */
    @media (max-width: 768px) {
        .gradio-container {
            max-width: 100% !important;
            padding: 10px !important;
        }
        
        .quiz-title {
            font-size: 1.8em !important;
        }
        
        .chat-message {
            padding: 10px !important;
            margin: 5px 0 !important;
        }
        
        .control-button {
            padding: 8px 12px !important;
            font-size: 0.9em !important;
        }
        
        .stats-panel {
            padding: 10px !important;
            font-size: 0.9em !important;
        }
    }
    
    /* Tablet responsiveness */
    @media (min-width: 769px) and (max-width: 1024px) {
        .gradio-container {
            max-width: 95% !important;
        }
        
        .quiz-title {
            font-size: 2.2em !important;
        }
    }
    """
    
    return responsive_css

# Theme variations
def create_dark_theme():
    """Create dark theme variant"""
    return gr.themes.Monochrome(
        primary_hue="blue",
        secondary_hue="gray",
        neutral_hue="gray"
    )

def create_light_theme():
    """Create light theme variant"""
    return gr.themes.Soft(
        primary_hue="blue",
        secondary_hue="green",
        neutral_hue="gray"
    )

def create_colorful_theme():
    """Create colorful theme variant"""
    return gr.themes.Default(
        primary_hue="purple",
        secondary_hue="pink",
        neutral_hue="slate"
    )
```

## 🧪 Interface Testing

Create interface tests in `tests/test_interface.py`:

```python
"""Tests for Gradio interface functionality"""

import pytest
from unittest.mock import Mock, patch
import gradio as gr

from app import QuizApplication, create_gradio_interface, launch_application
from src.interface_utils import (
    create_progress_bar, format_quiz_results, create_topic_suggestions
)
from src.state import create_test_state

class TestQuizApplication:
    """Test main application class"""
    
    @patch('app.create_quiz_workflow')
    def test_application_initialization(self, mock_workflow):
        """Test application initialization"""
        mock_workflow.return_value = Mock()
        
        app = QuizApplication()
        
        assert app.workflow is not None
        assert app.current_state is not None
        assert app.session_history == []
    
    @patch('app.create_quiz_workflow')
    def test_chat_interface_success(self, mock_workflow):
        """Test successful chat interaction"""
        mock_workflow_instance = Mock()
        mock_workflow_instance.process_input_sync.return_value = create_test_state()
        mock_workflow_instance.get_response_for_state.return_value = "Test response"
        mock_workflow.return_value = mock_workflow_instance
        
        app = QuizApplication()
        history = []
        
        result_history, result_msg = app.chat_interface("Test message", history)
        
        assert len(result_history) == 1
        assert result_history[0][0] == "Test message"
        assert result_history[0][1] == "Test response"
        assert result_msg == ""
    
    @patch('app.create_quiz_workflow')
    def test_chat_interface_error(self, mock_workflow):
        """Test chat interface error handling"""
        mock_workflow_instance = Mock()
        mock_workflow_instance.process_input_sync.side_effect = Exception("Test error")
        mock_workflow.return_value = mock_workflow_instance
        
        app = QuizApplication()
        history = []
        
        result_history, result_msg = app.chat_interface("Test message", history)
        
        assert len(result_history) == 1
        assert "error" in result_history[0][1].lower()
    
    @patch('app.create_quiz_workflow')
    def test_reset_quiz(self, mock_workflow):
        """Test quiz reset functionality"""
        mock_workflow.return_value = Mock()
        
        app = QuizApplication()
        app.session_history = [("old", "data")]
        
        result_history, result_msg = app.reset_quiz()
        
        assert result_history == []
        assert "reset" in result_msg.lower()
        assert len(app.session_history) == 0
    
    @patch('app.create_quiz_workflow')
    def test_clear_chat(self, mock_workflow):
        """Test chat clearing functionality"""
        mock_workflow.return_value = Mock()
        
        app = QuizApplication()
        
        result_history, result_msg = app.clear_chat()
        
        assert result_history == []
        assert result_msg == ""
    
    @patch('app.create_quiz_workflow')
    def test_get_session_stats(self, mock_workflow):
        """Test session statistics generation"""
        mock_workflow.return_value = Mock()
        
        app = QuizApplication()
        app.current_state = create_test_state()
        app.current_state.topic = "Test Topic"
        app.current_state.total_questions_answered = 5
        
        stats = app.get_session_stats()
        
        assert "Test Topic" in stats
        assert "5" in stats
        assert "Session Statistics" in stats

class TestInterfaceUtilities:
    """Test interface utility functions"""
    
    def test_create_progress_bar(self):
        """Test progress bar creation"""
        # Normal case
        bar = create_progress_bar(7, 10)
        assert "70.0%" in bar
        assert "7/10" in bar
        
        # Edge cases
        bar_zero = create_progress_bar(0, 0)
        assert "No progress" in bar_zero
        
        bar_complete = create_progress_bar(10, 10)
        assert "100.0%" in bar_complete
    
    def test_format_quiz_results(self):
        """Test quiz results formatting"""
        state = create_test_state()
        state.topic = "Test Topic"
        state.total_questions_answered = 5
        state.correct_answers_count = 4
        state.total_score = 40
        
        results = format_quiz_results(state)
        
        assert "Test Topic" in results
        assert "80.0%" in results  # 4/5 = 80%
        assert "40" in results
        
        # Test with no data
        empty_results = format_quiz_results(None)
        assert "No quiz data" in empty_results
    
    def test_create_topic_suggestions(self):
        """Test topic suggestion generation"""
        # Test different categories
        popular = create_topic_suggestions("popular")
        assert len(popular) > 0
        assert "Python Programming" in popular
        
        academic = create_topic_suggestions("academic")
        assert len(academic) > 0
        assert "Calculus" in academic
        
        technology = create_topic_suggestions("technology")
        assert len(technology) > 0
        assert "React.js" in technology
        
        # Test unknown category (should return popular)
        unknown = create_topic_suggestions("unknown")
        assert unknown == popular

class TestInterfaceCreation:
    """Test Gradio interface creation"""
    
    @patch('app.QuizApplication')
    def test_create_gradio_interface(self, mock_app_class):
        """Test Gradio interface creation"""
        mock_app_class.return_value = Mock()
        
        interface = create_gradio_interface()
        
        assert isinstance(interface, gr.Blocks)
    
    @patch('app.create_gradio_interface')
    @patch('app.Config')
    def test_launch_application(self, mock_config, mock_interface):
        """Test application launch"""
        mock_config.validate_required.return_value = None
        mock_interface_instance = Mock()
        mock_interface.return_value = mock_interface_instance
        
        # This would normally launch the app, but we're just testing the setup
        try:
            launch_application()
        except SystemExit:
            # Gradio may call sys.exit(), which is expected behavior
            pass
        
        mock_interface_instance.launch.assert_called_once()

class TestErrorHandling:
    """Test error handling in interface"""
    
    @patch('app.create_quiz_workflow')
    def test_workflow_initialization_failure(self, mock_workflow):
        """Test handling of workflow initialization failure"""
        mock_workflow.side_effect = Exception("Workflow creation failed")
        
        app = QuizApplication()
        
        assert app.workflow is None
        
        # Test chat with failed workflow
        history = []
        result_history, result_msg = app.chat_interface("Test", history)
        
        assert "not properly initialized" in result_history[0][1]
    
    @patch('app.Config')
    def test_configuration_error_handling(self, mock_config):
        """Test configuration error handling"""
        mock_config.validate_required.side_effect = ValueError("Missing API key")
        
        with pytest.raises(SystemExit):
            launch_application()

if __name__ == "__main__":
    pytest.main([__file__])
```

## 📋 Implementation Checklist

### Core Implementation
- [ ] **QuizApplication Class**: Main application orchestrator
- [ ] **Gradio Interface**: Complete chat-based interface with styling
- [ ] **Event Handlers**: All user interactions properly handled
- [ ] **Error Handling**: Comprehensive error handling throughout interface
- [ ] **Responsive Design**: Mobile and tablet compatible layout

### Advanced Features
- [ ] **Statistics Panel**: Real-time session statistics
- [ ] **Quick Start Buttons**: Topic suggestion buttons
- [ ] **Accessibility**: Screen reader and keyboard navigation support
- [ ] **Progress Tracking**: Visual progress indicators
- [ ] **Export Functionality**: Session data export capability

### Testing
- [ ] **Unit Tests**: All interface components tested
- [ ] **Integration Tests**: Full interface workflow tested
- [ ] **Error Scenarios**: Error handling and recovery tested
- [ ] **Accessibility Tests**: Screen reader and keyboard navigation tested

## ✅ Completion Criteria

Gradio interface implementation is complete when:

1. **Complete chat interface working** with real-time conversations
2. **All control buttons functional** (reset, clear, help, stats)
3. **Error handling robust** for all user interactions
4. **Responsive design working** on mobile and desktop
5. **Accessibility features implemented** for inclusive design
6. **Complete test suite passing** with >90% coverage

**Next Step**: Proceed to **[08-api-integration.md](./08-api-integration.md)** to implement OpenAI API integration and error handling. 