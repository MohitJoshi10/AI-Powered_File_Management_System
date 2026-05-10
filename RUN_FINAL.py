#!/usr/bin/env python3
"""
SmartFile AI - Final Runner
Run the error-free final version of SmartFile AI
"""

import sys
import os

def main():
    print("🚀 SmartFile AI - Final Version")
    print("=" * 50)
    print("📋 Features:")
    print("  ✅ AI-powered search with natural language")
    print("  ✅ Multi-format file support (PDF, DOCX, TXT, Images, Audio)")
    print("  ✅ Voice command interaction")
    print("  ✅ File encryption and security")
    print("  ✅ Automatic categorization and tagging")
    print("  ✅ Modern responsive web interface")
    print("  ✅ Robust error handling")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists('app_final.py'):
        print("❌ Error: app_final.py not found")
        print("📁 Please run this script from the SmartFile-AI-Final directory")
        sys.exit(1)
    
    print("🌐 Starting application...")
    print("📍 URL: http://localhost:5000")
    print("🔧 Press Ctrl+C to stop")
    print("=" * 50)
    
    try:
        # Import and run the final application
        import app_final
    except KeyboardInterrupt:
        print("\n👋 SmartFile AI stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
