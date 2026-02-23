#!/bin/bash

# VPS-də Flask app-ı yenidən başlatmaq üçün script

echo "🔄 Restarting Flask application..."

# Find and kill existing Flask processes
pkill -f "python.*app.py" || echo "No existing Flask process found"

# Wait a moment
sleep 2

# Activate virtual environment and start Flask
source .venv/bin/activate

# Start Flask in background
nohup python app.py > flask_app.log 2>&1 &

echo "✅ Flask application restarted"
echo "📝 Check logs: tail -f flask_app.log"
