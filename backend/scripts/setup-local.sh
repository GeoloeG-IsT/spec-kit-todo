#!/bin/bash

# Local Development Setup Script for TODO Backend
# This script sets up the local development environment

set -e

echo "🚀 Setting up local TODO backend development environment..."

# Check if we're in the backend directory
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: Please run this script from the backend directory"
    exit 1
fi

# Create .env file from .env.local template if it doesn't exist
if [ ! -f ".env" ]; then
    if [ -f ".env.local" ]; then
        echo "📋 Copying .env.local to .env..."
        cp .env.local .env
        echo "⚠️  Please edit .env file with your actual Clerk keys"
    else
        echo "❌ Error: .env.local template not found"
        exit 1
    fi
else
    echo "✅ .env file already exists"
fi

# Create Python virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "🐍 Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Check if Docker is available for database
if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
    echo "🐳 Docker found. Starting PostgreSQL database..."

    # Start only the database service
    cd ..
    docker-compose up -d db
    cd backend

    # Wait for database to be ready
    echo "⏳ Waiting for database to be ready..."
    sleep 10

    # Run database migrations
    echo "🗄️  Running database migrations..."
    alembic upgrade head

    echo "✅ Database setup complete!"
else
    echo "⚠️  Docker not found. Please:"
    echo "   1. Install Docker and Docker Compose"
    echo "   2. Or manually set up PostgreSQL database"
    echo "   3. Update DATABASE_URL in .env file accordingly"
fi

echo ""
echo "🎉 Local development environment setup complete!"
echo ""
echo "To start the development server:"
echo "  source venv/bin/activate"
echo "  uvicorn src.main:app --reload --port 8000"
echo ""
echo "API will be available at: http://localhost:8000"
echo "API docs will be available at: http://localhost:8000/docs"
echo ""
echo "Remember to:"
echo "  1. Update CLERK_SECRET_KEY and CLERK_PUBLISHABLE_KEY in .env"
echo "  2. Make sure PostgreSQL is running (docker-compose up -d db)"