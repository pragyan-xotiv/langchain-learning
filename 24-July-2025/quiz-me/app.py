#!/usr/bin/env python3
"""Main Gradio Application Entry Point for Interactive Quiz Generator

This is the main entry point for the Interactive Quiz Generator application.
It creates and launches the Gradio web interface that users interact with.

Usage:
    python app.py

The application will start a web server (default: http://localhost:7860)
and provide an interactive chat interface for the quiz system.

To be fully implemented in Phase 3 following 07-gradio-interface.md
"""

import os
import sys
import logging
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

try:
    import gradio as gr
    from src.utils import Config
    from src.workflow import create_quiz_workflow
    from src.state import create_initial_state
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please install dependencies: pip install -r requirements.txt")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_quiz_interface():
    """Create and configure the Gradio interface"""
    
    def process_message(message, history):
        """Process user message and return response"""
        # Placeholder implementation - will be expanded in Phase 3
        if not message.strip():
            return "Please enter a message to start the quiz!"
        
        # Simple placeholder responses based on keywords
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['hello', 'hi', 'start', 'begin']):
            return ("🎉 Welcome to the Interactive Quiz Generator! "
                   "What topic would you like to be quizzed on?")
        
        elif any(word in message_lower for word in ['python', 'programming', 'code']):
            return ("Great choice! Python programming is an excellent topic. "
                   "I'll create some questions for you. "
                   "[Note: Full implementation coming in Phase 3]")
        
        elif any(word in message_lower for word in ['help', 'how', 'instructions']):
            return ("Here's how it works:\n"
                   "1. Tell me what topic you'd like to learn about\n"
                   "2. I'll create personalized quiz questions\n"
                   "3. Answer the questions and get instant feedback\n"
                   "4. Track your progress and improve!\n\n"
                   "Just type a topic to get started!")
        
        else:
            return (f"Interesting topic: '{message}'! "
                   "I'm preparing quiz questions about this subject. "
                   "[Note: This is a placeholder - full LLM integration coming in Phase 3]")
    
    # Create Gradio ChatInterface
    interface = gr.ChatInterface(
        fn=process_message,
        title=Config.APP_TITLE,
        description=("🧠 An intelligent quiz generator powered by AI. "
                    "Choose any topic and start learning interactively!"),
        theme=gr.themes.Default(primary_hue="blue"),
        examples=[
            "I want to learn about Python programming",
            "Quiz me on World History", 
            "Let's practice Mathematics",
            "Help me study Biology"
        ],
        cache_examples=False,
        retry_btn="🔄 Retry",
        undo_btn="↩️ Undo",
        clear_btn="🗑️ Clear Chat"
    )
    
    return interface

def main():
    """Main application entry point"""
    
    try:
        # Validate configuration
        Config.validate_required()
        logger.info("🚀 Starting Interactive Quiz Generator")
        
        if Config.DEBUG:
            logger.info("Debug mode enabled")
            Config.log_configuration()
        
        # Create and launch interface
        interface = create_quiz_interface()
        
        # Launch configuration
        launch_kwargs = {
            'server_name': Config.GRADIO_SERVER_NAME,
            'server_port': Config.GRADIO_SERVER_PORT,
            'share': Config.GRADIO_SHARE,
            'debug': Config.DEBUG,
            'show_error': Config.DEBUG
        }
        
        logger.info(f"Launching on http://{Config.GRADIO_SERVER_NAME}:{Config.GRADIO_SERVER_PORT}")
        interface.launch(**launch_kwargs)
        
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Application failed to start: {e}")
        if Config.DEBUG:
            raise
        sys.exit(1)

if __name__ == "__main__":
    main() 