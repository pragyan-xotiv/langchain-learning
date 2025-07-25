#!/usr/bin/env python3
"""Setup validation script for Interactive Quiz Generator

This script validates that the development environment is properly set up
according to the specifications in 01-project-setup.md.

Usage:
    python validate_setup.py

The script performs comprehensive checks on:
- Python version compatibility
- Required files and directory structure
- Environment variables
- Dependencies and imports
- Git repository status
- Development tools configuration

Returns exit code 0 on success, 1 on failure.
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple, Optional

def check_python_version() -> Tuple[bool, str]:
    """Check if Python version meets requirements"""
    if sys.version_info < (3, 8):
        return False, f"Python 3.8+ required, found {sys.version}"
    return True, f"Python {sys.version.split()[0]}"

def check_required_files() -> Tuple[bool, List[str]]:
    """Check if all required files exist"""
    required_files = [
        'requirements.txt',
        '.env.example', 
        '.gitignore',
        'app.py',
        'README.md',
        'pytest.ini',
        'mypy.ini',
        '.pre-commit-config.yaml',
        'src/__init__.py',
        'src/utils.py',
        'src/workflow.py',
        'tests/__init__.py',
        'tests/conftest.py'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    success = len(missing_files) == 0
    return success, missing_files

def check_required_directories() -> Tuple[bool, List[str]]:
    """Check if all required directories exist"""
    required_dirs = [
        'src',
        'src/nodes',
        'src/edges', 
        'src/prompts',
        'src/state',
        'tests',
        'docs'
    ]
    
    missing_dirs = []
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            missing_dirs.append(dir_path)
    
    success = len(missing_dirs) == 0
    return success, missing_dirs

def check_environment_variables() -> Tuple[bool, Dict[str, str]]:
    """Check environment variable status"""
    env_status = {}
    
    # Load from .env if it exists
    env_file = Path('.env')
    if env_file.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv()
            env_status['.env file'] = 'Found and loaded'
        except ImportError:
            env_status['.env file'] = 'Found but python-dotenv not installed'
    else:
        env_status['.env file'] = 'Not found (use .env.example as template)'
    
    # Check critical environment variables
    openai_key = os.getenv('OPENAI_API_KEY')
    if openai_key:
        # Mask the key for security
        masked_key = openai_key[:8] + '...' + openai_key[-4:] if len(openai_key) > 12 else '***'
        env_status['OPENAI_API_KEY'] = f'Set ({masked_key})'
    else:
        env_status['OPENAI_API_KEY'] = 'Not set (required for full functionality)'
    
    # Other optional environment variables
    optional_vars = ['OPENAI_MODEL', 'APP_TITLE', 'GRADIO_SERVER_PORT']
    for var in optional_vars:
        value = os.getenv(var)
        env_status[var] = f'Set to: {value}' if value else 'Using default'
    
    # Success if at least .env.example exists (API key is optional for setup validation)
    success = Path('.env.example').exists()
    return success, env_status

def check_dependencies() -> Tuple[bool, List[str]]:
    """Check if core dependencies can be imported"""
    import_errors = []
    
    try:
        import gradio
        import pydantic
        import langchain
        import langgraph
        import openai
        # Import from our src module
        sys.path.insert(0, 'src')
        from utils import Config
    except ImportError as e:
        import_errors.append(str(e))
    
    success = len(import_errors) == 0
    return success, import_errors

def check_git_repository() -> Tuple[bool, str]:
    """Check git repository status"""
    try:
        # Check if we're in a git repository
        result = subprocess.run(['git', 'rev-parse', '--git-dir'], 
                              capture_output=True, text=True, check=True)
        
        # Check if there are any commits
        result = subprocess.run(['git', 'log', '--oneline', '-1'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            return True, "Git repository initialized with commits"
        else:
            return True, "Git repository initialized (no commits yet)"
            
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False, "Not a git repository or git not installed"

def check_development_tools() -> Tuple[bool, Dict[str, str]]:
    """Check development tools configuration"""
    tools_status = {}
    
    # Check pre-commit
    try:
        result = subprocess.run(['pre-commit', '--version'], 
                              capture_output=True, text=True, check=True)
        tools_status['pre-commit'] = f"Installed: {result.stdout.strip()}"
    except (subprocess.CalledProcessError, FileNotFoundError):
        tools_status['pre-commit'] = "Not installed or not in PATH"
    
    # Check if pre-commit is set up
    if Path('.git/hooks/pre-commit').exists():
        tools_status['pre-commit hooks'] = "Installed"
    else:
        tools_status['pre-commit hooks'] = "Not installed (run: pre-commit install)"
    
    # Check other tools
    for tool in ['black', 'isort', 'mypy', 'pytest']:
        try:
            result = subprocess.run([tool, '--version'], 
                                  capture_output=True, text=True, check=True)
            tools_status[tool] = "Available"
        except (subprocess.CalledProcessError, FileNotFoundError):
            tools_status[tool] = "Not available"
    
    # Success if most tools are available
    available_count = sum(1 for status in tools_status.values() if 'Available' in status or 'Installed' in status)
    success = available_count >= 3
    return success, tools_status

def run_basic_tests() -> Tuple[bool, str]:
    """Run basic validation tests"""
    try:
        # Test basic imports and configuration
        sys.path.insert(0, 'src')
        from utils import Config, validate_environment_setup
        
        # Run environment validation
        results = validate_environment_setup()
        passed = sum(results.values())
        total = len(results)
        
        return True, f"Environment validation: {passed}/{total} checks passed"
        
    except Exception as e:
        return False, f"Basic test failed: {e}"

def print_section(title: str, success: bool, details: any = None):
    """Print a validation section with consistent formatting"""
    status_icon = "✅" if success else "❌"
    print(f"\n{status_icon} {title}")
    
    if details:
        if isinstance(details, list):
            if not success and details:  # Show errors/missing items
                for item in details:
                    print(f"   • {item}")
        elif isinstance(details, dict):
            for key, value in details.items():
                status = "✅" if any(word in value.lower() for word in ['set', 'found', 'available', 'installed']) else "⚠️"
                print(f"   {status} {key}: {value}")
        elif isinstance(details, str):
            print(f"   {details}")

def validate_environment() -> bool:
    """Main validation function"""
    print("🔍 Interactive Quiz Generator - Setup Validation")
    print("=" * 55)
    
    all_checks_passed = True
    
    # Python version check
    success, message = check_python_version()
    print_section("Python Version", success, message)
    all_checks_passed &= success
    
    # Required files check
    success, missing_files = check_required_files()
    print_section("Required Files", success, missing_files if not success else "All files present")
    all_checks_passed &= success
    
    # Required directories check
    success, missing_dirs = check_required_directories()
    print_section("Directory Structure", success, missing_dirs if not success else "All directories present")
    all_checks_passed &= success
    
    # Environment variables check
    success, env_status = check_environment_variables()
    print_section("Environment Configuration", success, env_status)
    # Don't fail overall validation for missing API key in development
    
    # Dependencies check
    success, import_errors = check_dependencies()
    print_section("Dependencies", success, import_errors if not success else "All core dependencies available")
    all_checks_passed &= success
    
    # Git repository check
    success, message = check_git_repository()
    print_section("Git Repository", success, message)
    # Don't fail overall validation for git issues
    
    # Development tools check
    success, tools_status = check_development_tools()
    print_section("Development Tools", success, tools_status)
    # Don't fail overall validation for missing dev tools
    
    # Basic tests
    success, message = run_basic_tests()
    print_section("Basic Tests", success, message)
    all_checks_passed &= success
    
    # Final summary
    print("\n" + "=" * 55)
    if all_checks_passed:
        print("🎉 Setup validation completed successfully!")
        print("📋 Next step: Proceed to 02-state-management.md")
        print("\n💡 To start the application: python app.py")
    else:
        print("⚠️  Setup validation found issues that need attention.")
        print("📖 Please refer to 01-project-setup.md for detailed setup instructions.")
        print("\n🔧 Common fixes:")
        print("   • Run: pip install -r requirements.txt")
        print("   • Copy: cp .env.example .env (and add your OpenAI API key)")
        print("   • Run: pre-commit install")
    
    return all_checks_passed

if __name__ == "__main__":
    try:
        success = validate_environment()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Validation failed with unexpected error: {e}")
        sys.exit(1) 