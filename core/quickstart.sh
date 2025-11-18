#!/bin/bash

# Gamora AI - Quick Start Script
# This script helps you get started quickly

set -e

echo "🎮 Gamora AI - Quick Start Setup"
echo "================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your API keys:"
    echo "   - OPENAI_API_KEY"
    echo "   - DEEPSEEK_API_KEY"
    echo "   - SUPABASE_URL"
    echo "   - SUPABASE_KEY"
    echo ""
    read -p "Press Enter when you've added your keys..."
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt --break-system-packages 2>/dev/null || pip install -r requirements.txt

# Check if Docker is running
if command -v docker &> /dev/null && docker info &> /dev/null; then
    echo "🐳 Docker is running"
    
    read -p "Do you want to start with Docker? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🚀 Starting services with Docker..."
        docker-compose up -d
        
        echo ""
        echo "⏳ Waiting for services to be ready..."
        sleep 10
        
        echo "✅ Services started!"
        echo ""
        echo "📊 Service Status:"
        docker-compose ps
        echo ""
        echo "🌐 API: http://localhost:8000"
        echo "📚 Docs: http://localhost:8000/docs"
        echo "❤️  Health: http://localhost:8000/health"
        echo ""
        echo "📝 View logs: docker-compose logs -f api"
        exit 0
    fi
fi

# Run locally
echo "🚀 Starting Gamora AI locally..."
echo ""

# Check if PostgreSQL is running
if ! nc -z localhost 5432 2>/dev/null; then
    echo "⚠️  PostgreSQL not detected on localhost:5432"
    echo "   Please start PostgreSQL or use Docker"
fi

# Check if Redis is running
if ! nc -z localhost 6379 2>/dev/null; then
    echo "⚠️  Redis not detected on localhost:6379"
    echo "   Please start Redis or use Docker"
fi

echo ""
echo "Starting API server..."
python main.py &

API_PID=$!

echo ""
echo "✅ Gamora AI is starting!"
echo ""
echo "🌐 API: http://localhost:8000"
echo "📚 Docs: http://localhost:8000/docs"
echo "❤️  Health: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Wait for API to be ready
sleep 3

# Test health endpoint
echo "🔍 Testing health endpoint..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ API is healthy!"
else
    echo "⚠️  API might not be ready yet, give it a moment..."
fi

echo ""
echo "🎉 Quick Start Complete!"
echo ""
echo "📖 Next steps:"
echo "   1. Visit http://localhost:8000/docs for API documentation"
echo "   2. Register a user: POST /api/v1/auth/register"
echo "   3. Generate a game: POST /api/v1/generate/game"
echo "   4. Read GODOT_INTEGRATION_GUIDE.md for full details"
echo ""

# Keep running
wait $API_PID
