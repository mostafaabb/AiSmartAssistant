#!/bin/bash
# NexusAI Backend - Quick Setup Script
# Run from project root: bash backend/setup.sh

set -e  # Exit on error

echo "🚀 NexusAI Backend Setup"
echo "======================="
echo ""

# Check Python version
echo "✓ Checking Python version..."
python_version=$(python --version 2>&1 | awk '{print $2}')
echo "  Python $python_version"

# Create virtual environment
if [ ! -d "backend/venv" ]; then
    echo "✓ Creating virtual environment..."
    python -m venv backend/venv
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo "✓ Activating virtual environment..."
source backend/venv/bin/activate || . backend/venv/Scripts/activate

# Upgrade pip
echo "✓ Upgrading pip..."
pip install --upgrade pip setuptools wheel > /dev/null 2>&1

# Install dependencies
echo "✓ Installing dependencies..."
pip install -r backend/requirements.txt > /dev/null 2>&1

# Create .env file
if [ ! -f "backend/.env" ]; then
    echo "✓ Creating .env file from template..."
    cp backend/.env.example backend/.env
    echo "  ⚠️  Update backend/.env with your settings"
else
    echo "✓ .env file already exists"
fi

# Create workspace directory
if [ ! -d "workspace" ]; then
    echo "✓ Creating workspace directory..."
    mkdir -p workspace
fi

echo ""
echo "✅ Setup Complete!"
echo ""
echo "📋 Next Steps:"
echo "  1. Update backend/.env with your database URL:"
echo "     DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/nexusai"
echo ""
echo "  2. Start PostgreSQL (Docker):"
echo "     docker run -d -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=nexusai -p 5432:5432 postgres:15-alpine"
echo ""
echo "  3. Run database migrations:"
echo "     cd backend"
echo "     source venv/bin/activate"
echo "     alembic upgrade head"
echo ""
echo "  4. Start FastAPI server:"
echo "     uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "  5. Open browser:"
echo "     http://localhost:8000/docs  (API docs)"
echo ""
echo "🎉 Happy coding!"
