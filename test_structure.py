#!/usr/bin/env python3
"""
Test script to validate SmartFile AI project structure
"""

import os
import sys

def test_project_structure():
    """Test if all required files and directories exist"""
    print("🔍 Testing SmartFile AI Project Structure")
    print("=" * 50)
    
    # Required directories
    required_dirs = [
        'static',
        'static/css',
        'static/js', 
        'static/images',
        'templates',
        'uploads',
        'encrypted_files'
    ]
    
    # Required files
    required_files = [
        'app.py',
        'requirements.txt',
        'README.md',
        'setup.py',
        'run.py',
        'templates/index.html',
        'static/css/style.css',
        'static/js/app.js'
    ]
    
    # Test directories
    print("📁 Testing directories:")
    all_dirs_exist = True
    for directory in required_dirs:
        exists = os.path.exists(directory)
        status = "✅" if exists else "❌"
        print(f"  {status} {directory}")
        if not exists:
            all_dirs_exist = False
    
    # Test files
    print("\n📄 Testing files:")
    all_files_exist = True
    for file_path in required_files:
        exists = os.path.exists(file_path)
        status = "✅" if exists else "❌"
        print(f"  {status} {file_path}")
        if not exists:
            all_files_exist = False
    
    # Test Python imports
    print("\n🐍 Testing Python imports:")
    try:
        import flask
        print("  ✅ Flask")
    except ImportError:
        print("  ❌ Flask - Not installed")
        all_files_exist = False
    
    try:
        import elasticsearch
        print("  ✅ Elasticsearch")
    except ImportError:
        print("  ❌ Elasticsearch - Not installed")
        all_files_exist = False
    
    try:
        import spacy
        print("  ✅ spaCy")
    except ImportError:
        print("  ❌ spaCy - Not installed")
        all_files_exist = False
    
    # Summary
    print("\n" + "=" * 50)
    if all_dirs_exist and all_files_exist:
        print("🎉 Project structure is complete!")
        print("🚀 Ready to run: python setup.py")
        return True
    else:
        print("❌ Project structure is incomplete")
        print("🔧 Please fix the missing items above")
        return False

if __name__ == "__main__":
    success = test_project_structure()
    sys.exit(0 if success else 1)
