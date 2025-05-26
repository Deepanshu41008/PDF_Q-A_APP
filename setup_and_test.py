#!/usr/bin/env python3
"""
Setup and test script for PDF Q&A Application
"""
import os
import sys
import subprocess
from pathlib import Path
import shutil

def check_python_version():
    """Check if Python version is 3.8 or higher."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"   Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True

def check_openai_key():
    """Check if OpenAI API key is set."""
    env_file = Path("backend/.env")
    if not env_file.exists():
        print("❌ Backend .env file not found")
        return False
    
    with open(env_file, 'r') as f:
        content = f.read()
        if 'sk-YOUR_ACTUAL_API_KEY_HERE' in content or not any('OPENAI_API_KEY=' in line for line in content.split('\n')):
            print("⚠️  OpenAI API key not set!")
            print("   Please edit backend/.env and add your OpenAI API key")
            print("   Get one from: https://platform.openai.com/api-keys")
            return False
    
    print("✅ OpenAI API key found in .env")
    return True

def setup_backend():
    """Set up backend dependencies and directories."""
    print("\n🔧 Setting up backend...")
    
    # Change to backend directory
    os.chdir("backend")
    
    # Create virtual environment if it doesn't exist
    if not Path(".venv").exists():
        print("   Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", ".venv"], check=True)
    
    # Determine pip command based on OS
    if sys.platform == "win32":
        pip_cmd = [".venv\\Scripts\\python.exe", "-m", "pip"]
    else:
        pip_cmd = [".venv/bin/python", "-m", "pip"]
    
    # Upgrade pip
    print("   Upgrading pip...")
    subprocess.run(pip_cmd + ["install", "--upgrade", "pip"], check=True)
    
    # Install requirements
    print("   Installing requirements...")
    subprocess.run(pip_cmd + ["install", "-r", "requirements.txt"], check=True)
    
    # Create data directories
    for dir_name in ["data", "data/documents", "data/indices"]:
        Path(dir_name).mkdir(parents=True, exist_ok=True)
    
    print("✅ Backend setup complete")
    os.chdir("..")

def setup_frontend():
    """Set up frontend dependencies."""
    print("\n🔧 Setting up frontend...")
    
    # Check if npm is installed
    try:
        subprocess.run(["npm", "--version"], check=True, capture_output=True)
    except:
        print("❌ npm not found. Please install Node.js from https://nodejs.org/")
        return False
    
    # Change to frontend directory
    os.chdir("frontend")
    
    # Install dependencies
    print("   Installing npm packages...")
    subprocess.run(["npm", "install"], check=True)
    
    print("✅ Frontend setup complete")
    os.chdir("..")
    return True

def create_test_files():
    """Create test files if needed."""
    # Create a simple test PDF if needed
    test_pdf_path = Path("test_documents")
    test_pdf_path.mkdir(exist_ok=True)
    
    # Create instructions file
    with open(test_pdf_path / "README.txt", "w") as f:
        f.write("""
Test Documents Directory
========================

Place your PDF files here for testing the application.

If you don't have any PDFs, you can:
1. Download sample PDFs from https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf
2. Create a PDF from any document using Print -> Save as PDF
3. Use any existing PDF documents you have

Note: The application only supports PDF files.
""")
    print(f"✅ Created test documents directory at: {test_pdf_path.absolute()}")

def print_instructions():
    """Print instructions for running the application."""
    print("\n" + "="*60)
    print("🚀 Setup Complete! Here's how to run the application:")
    print("="*60)
    print("\n1. Make sure you've set your OpenAI API key in backend/.env")
    print("\n2. Start the backend server:")
    print("   cd backend")
    if sys.platform == "win32":
        print("   .venv\\Scripts\\python.exe run.py")
    else:
        print("   .venv/bin/python run.py")
    print("\n3. In a new terminal, start the frontend:")
    print("   cd frontend")
    print("   npm run dev")
    print("\n4. Open your browser to http://localhost:12001")
    print("\n5. Upload a PDF and start asking questions!")
    print("\n" + "="*60)

def main():
    """Main setup function."""
    print("🎯 PDF Q&A Application Setup")
    print("="*60)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Check if we're in the right directory
    if not Path("backend").exists() or not Path("frontend").exists():
        print("❌ Please run this script from the project root directory")
        print("   (the directory containing 'backend' and 'frontend' folders)")
        sys.exit(1)
    
    # Setup backend
    try:
        setup_backend()
    except Exception as e:
        print(f"❌ Backend setup failed: {e}")
        sys.exit(1)
    
    # Check OpenAI key
    check_openai_key()
    
    # Setup frontend
    if not setup_frontend():
        sys.exit(1)
    
    # Create test files
    create_test_files()
    
    # Print instructions
    print_instructions()

if __name__ == "__main__":
    main()