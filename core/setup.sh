#!/bin/bash
echo "🚀 Gamora AI Setup"
echo "=================="

# Check prerequisites
command -v docker >/dev/null 2>&1 || { echo "❌ Docker required"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "❌ Python 3.11+ required"; exit 1; }

# Setup environment
if [ ! -f .env ]; then
    cp .env.example .env
    echo "⚠️  Please add your API keys to .env file"
    read -p "OpenAI API Key: " openai_key
    read -p "DeepSeek API Key: " deepseek_key
    sed -i "s/OPENAI_API_KEY=.*/OPENAI_API_KEY=$openai_key/" .env
    sed -i "s/DEEPSEEK_API_KEY=.*/DEEPSEEK_API_KEY=$deepseek_key/" .env
fi

# Create directories
mkdir -p projects exports logs

# Start services
echo "🐳 Starting Docker services..."
docker-compose up -d

echo "✅ Gamora AI is ready!"
echo "📍 API: http://localhost:8000"
echo "📚 Docs: http://localhost:8000/docs"
