#!/usr/bin/env python3
"""
SmartFile AI Setup Script
Automated setup and configuration for SmartFile AI
"""

import os
import sys
import subprocess
import platform
import requests
from pathlib import Path

class SmartFileSetup:
    def __init__(self):
        self.system = platform.system().lower()
        self.python_version = sys.version_info
        self.project_root = Path(__file__).parent
        
    def check_python_version(self):
        """Check if Python version is compatible"""
        if self.python_version < (3, 8):
            print("❌ Error: Python 3.8 or higher is required")
            print(f"Current version: {self.python_version.major}.{self.python_version.minor}")
            return False
        print(f"✅ Python version: {self.python_version.major}.{self.python_version.minor}.{self.python_version.micro}")
        return True
    
    def check_elasticsearch(self):
        """Check if Elasticsearch is running"""
        try:
            response = requests.get('http://localhost:9200', timeout=5)
            if response.status_code == 200:
                print("✅ Elasticsearch is running")
                return True
        except:
            pass
        
        print("⚠️  Elasticsearch is not running or not accessible")
        print("Please start Elasticsearch before running the application")
        return False
    
    def install_python_dependencies(self):
        """Install Python dependencies from requirements.txt"""
        print("📦 Installing Python dependencies...")
        try:
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install', '-r', 
                str(self.project_root / 'requirements.txt')
            ])
            print("✅ Python dependencies installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Error installing Python dependencies: {e}")
            return False
    
    def download_spacy_model(self):
        """Download spaCy English model"""
        print("🧠 Downloading spaCy English model...")
        try:
            subprocess.check_call([
                sys.executable, '-m', 'spacy', 'download', 'en_core_web_sm'
            ])
            print("✅ spaCy model downloaded successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Error downloading spaCy model: {e}")
            return False
    
    def create_directories(self):
        """Create necessary directories"""
        print("📁 Creating directories...")
        directories = [
            'uploads',
            'encrypted_files',
            'static/css',
            'static/js',
            'static/images',
            'templates'
        ]
        
        for directory in directories:
            dir_path = self.project_root / directory
            dir_path.mkdir(parents=True, exist_ok=True)
        
        print("✅ Directories created successfully")
        return True
    
    def generate_encryption_key(self):
        """Generate encryption key if it doesn't exist"""
        key_file = self.project_root / 'encryption_key.key'
        if not key_file.exists():
            print("🔐 Generating encryption key...")
            try:
                from cryptography.fernet import Fernet
                key = Fernet.generate_key()
                with open(key_file, 'wb') as f:
                    f.write(key)
                print("✅ Encryption key generated successfully")
            except ImportError:
                print("⚠️  Could not generate encryption key (cryptography not installed)")
            except Exception as e:
                print(f"❌ Error generating encryption key: {e}")
        else:
            print("✅ Encryption key already exists")
        return True
    
    def check_tesseract(self):
        """Check if Tesseract OCR is installed"""
        try:
            result = subprocess.run(['tesseract', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print("✅ Tesseract OCR is installed")
                return True
        except:
            pass
        
        print("⚠️  Tesseract OCR is not installed or not in PATH")
        if self.system == 'windows':
            print("Download from: https://github.com/UB-Mannheim/tesseract/wiki")
        elif self.system == 'darwin':
            print("Install with: brew install tesseract")
        else:
            print("Install with: sudo apt-get install tesseract-ocr")
        return False
    
    def check_ffmpeg(self):
        """Check if FFmpeg is installed"""
        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print("✅ FFmpeg is installed")
                return True
        except:
            pass
        
        print("⚠️  FFmpeg is not installed or not in PATH")
        if self.system == 'windows':
            print("Download from: https://ffmpeg.org/download.html")
        elif self.system == 'darwin':
            print("Install with: brew install ffmpeg")
        else:
            print("Install with: sudo apt-get install ffmpeg")
        return False
    
    def create_env_file(self):
        """Create .env file with default configuration"""
        env_file = self.project_root / '.env'
        if not env_file.exists():
            print("📝 Creating .env file...")
            env_content = """# Flask Configuration
FLASK_ENV=development
SECRET_KEY=your-secret-key-change-this-in-production

# Elasticsearch Configuration
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200

# File Upload Configuration
MAX_CONTENT_LENGTH=16777216
UPLOAD_FOLDER=uploads
ENCRYPTED_FOLDER=encrypted_files

# OCR Configuration
TESSERACT_CMD=tesseract

# Audio Processing
FFMPEG_PATH=ffmpeg
"""
            with open(env_file, 'w') as f:
                f.write(env_content)
            print("✅ .env file created successfully")
        else:
            print("✅ .env file already exists")
        return True
    
    def run_setup(self):
        """Run the complete setup process"""
        print("🚀 Starting SmartFile AI Setup...")
        print("=" * 50)
        
        # Check Python version
        if not self.check_python_version():
            return False
        
        # Create directories
        self.create_directories()
        
        # Install Python dependencies
        if not self.install_python_dependencies():
            return False
        
        # Download spaCy model
        if not self.download_spacy_model():
            return False
        
        # Generate encryption key
        self.generate_encryption_key()
        
        # Create .env file
        self.create_env_file()
        
        # Check optional dependencies
        print("\n🔍 Checking optional dependencies...")
        self.check_tesseract()
        self.check_ffmpeg()
        
        # Check Elasticsearch
        print("\n🔍 Checking Elasticsearch...")
        elasticsearch_running = self.check_elasticsearch()
        
        print("\n" + "=" * 50)
        print("🎉 Setup completed!")
        
        if not elasticsearch_running:
            print("\n⚠️  IMPORTANT: Please start Elasticsearch before running the application:")
            if self.system == 'windows':
                print("   Navigate to Elasticsearch directory and run: .\\bin\\elasticsearch.bat")
            else:
                print("   Run: ./bin/elasticsearch")
        
        print("\n🚀 To start the application:")
        print("   python app.py")
        print("\n🌐 Then open: http://localhost:5000")
        
        return True

def main():
    """Main setup function"""
    setup = SmartFileSetup()
    
    try:
        success = setup.run_setup()
        if success:
            sys.exit(0)
        else:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n❌ Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
