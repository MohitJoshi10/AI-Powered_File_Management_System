#!/usr/bin/env python3
"""
SmartFile AI Runner
Convenient script to run the SmartFile AI application
"""

import os
import sys
import subprocess
import time
import requests
from pathlib import Path

def check_elasticsearch():
    """Check if Elasticsearch is running"""
    try:
        response = requests.get('http://localhost:9200', timeout=5)
        return response.status_code == 200
    except:
        return False

def start_elasticsearch():
    """Start Elasticsearch service (platform-specific)"""
    print("🔍 Checking Elasticsearch...")
    
    if check_elasticsearch():
        print("✅ Elasticsearch is already running")
        return True
    
    print("⚠️  Elasticsearch is not running")
    print("Attempting to start Elasticsearch...")
    
    # Try to find and start Elasticsearch
    elasticsearch_paths = [
        "C:/elasticsearch/elasticsearch-8.10.0/bin/elasticsearch.bat",
        "C:/Program Files/Elastic/Elasticsearch/8.10.0/bin/elasticsearch.bat",
        "/usr/local/bin/elasticsearch",
        "/usr/share/elasticsearch/bin/elasticsearch"
    ]
    
    for path in elasticsearch_paths:
        if os.path.exists(path):
            try:
                print(f"Starting Elasticsearch from: {path}")
                if path.endswith('.bat'):
                    subprocess.Popen(path, shell=True)
                else:
                    subprocess.Popen([path])
                
                # Wait for Elasticsearch to start
                print("Waiting for Elasticsearch to start...")
                for i in range(30):  # Wait up to 30 seconds
                    time.sleep(1)
                    if check_elasticsearch():
                        print("✅ Elasticsearch started successfully")
                        return True
                    print(f"Waiting... ({i+1}/30)")
                
                print("❌ Elasticsearch failed to start within timeout")
                return False
            except Exception as e:
                print(f"❌ Failed to start Elasticsearch: {e}")
                continue
    
    print("❌ Could not find Elasticsearch installation")
    print("Please start Elasticsearch manually and run this script again")
    return False

def check_dependencies():
    """Check if required dependencies are installed"""
    print("🔍 Checking dependencies...")
    
    required_packages = [
        'flask',
        'elasticsearch',
        'spacy',
        'cryptography',
        'PyPDF2',
        'python-docx',
        'Pillow',
        'pytesseract',
        'SpeechRecognition',
        'pydub',
        'nltk'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - Missing")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("Please run: pip install -r requirements.txt")
        return False
    
    print("✅ All dependencies are installed")
    return True

def check_spacy_model():
    """Check if spaCy model is downloaded"""
    try:
        import spacy
        nlp = spacy.load('en_core_web_sm')
        print("✅ spaCy English model is available")
        return True
    except OSError:
        print("❌ spaCy English model is not downloaded")
        print("Please run: python -m spacy download en_core_web_sm")
        return False

def create_directories():
    """Create necessary directories"""
    directories = ['uploads', 'encrypted_files']
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"✅ Created directory: {directory}")
        else:
            print(f"✅ Directory exists: {directory}")

def main():
    """Main function to run SmartFile AI"""
    print("🚀 Starting SmartFile AI...")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check spaCy model
    if not check_spacy_model():
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Check/start Elasticsearch
    if not start_elasticsearch():
        print("\n⚠️  Continuing without Elasticsearch...")
        print("Some features may not work properly")
    
    print("\n" + "=" * 50)
    print("🎯 Starting SmartFile AI application...")
    
    # Set environment variables
    os.environ['FLASK_ENV'] = 'development'
    
    try:
        # Import and run the Flask app
        from app import app
        print("🌐 SmartFile AI is running at: http://localhost:5000")
        print("📝 Press Ctrl+C to stop the application")
        print("=" * 50)
        
        # Run the Flask application
        app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
        
    except KeyboardInterrupt:
        print("\n👋 SmartFile AI stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
