#!/bin/bash

# Intelipro Insurance Policy Renewal System - Quick Start Script

echo "🚀 Starting Intelipro Insurance Policy Renewal System Backend"
echo "============================================================"

# Check if Docker is available
if command -v docker &> /dev/null; then
    echo "🐳 Docker detected. Starting with Docker Compose..."
    
    # Build and start services
    docker-compose up --build -d
    
    echo "⏳ Waiting for services to start..."
    sleep 10
    
    # Check service health
    echo "🔍 Checking service health..."
    docker-compose ps
    
    echo ""
    echo "✅ Services started successfully!"
    echo ""
    echo "🌐 Access points:"
    echo "   - API: http://localhost:8000/api/"
    echo "   - Admin: http://localhost:8000/admin/"
    echo "   - API Docs: http://localhost:8000/api/docs/"
    echo "   - Health Check: http://localhost:8000/health/"
    echo "   - Celery Monitor: http://localhost:5555/"
    echo ""
    echo "📊 To view logs:"
    echo "   docker-compose logs -f web"
    echo ""
    echo "🛑 To stop services:"
    echo "   docker-compose down"
    
else
    echo "🐍 Docker not found. Starting with Python virtual environment..."
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        echo "Creating virtual environment..."
        python -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install dependencies
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
    
    # Set up environment
    if [ ! -f ".env" ]; then
        cp env.example .env
        echo "📝 Environment file created. Please edit .env with your configuration."
    fi
    
    # Run migrations
    echo "🗄️ Running database migrations..."
    python manage.py migrate
    
    # Collect static files
    echo "📁 Collecting static files..."
    python manage.py collectstatic --noinput
    
    # Start development server
    echo "🌐 Starting development server..."
    echo ""
    echo "✅ Server will be available at:"
    echo "   - API: http://localhost:8000/api/"
    echo "   - Admin: http://localhost:8000/admin/"
    echo "   - API Docs: http://localhost:8000/api/docs/"
    echo ""
    echo "📝 Remember to start Celery worker in another terminal:"
    echo "   source venv/bin/activate"
    echo "   celery -A renewal_backend worker -l info"
    echo ""
    
    python manage.py runserver
fi 