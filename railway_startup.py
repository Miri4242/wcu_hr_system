#!/usr/bin/env python3
"""
Railway startup script
Ensures proper initialization for Railway deployment
"""

import os
import sys
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    """Main startup function"""
    print("🚀 Railway startup script starting...")
    
    # Add current directory to Python path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    print(f"📁 Added to Python path: {current_dir}")
    
    # Test imports
    try:
        print("🔍 Testing imports...")
        from late_arrival_system import check_all_employees_late_arrivals
        print("✅ late_arrival_system imported successfully")
    except ImportError as e:
        print(f"⚠️  late_arrival_system import failed: {e}")
    
    # Import and start the Flask app
    try:
        print("🔍 Importing Flask app...")
        from app import app
        print("✅ Flask app imported successfully")
        
        # Start the app
        port = int(os.environ.get('PORT', 8080))
        print(f"🌐 Starting Flask app on port {port}...")
        
        app.run(host='0.0.0.0', port=port, debug=False)
        
    except Exception as e:
        print(f"❌ Failed to start Flask app: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()