.PHONY: help start start-backend start-frontend test test-backend test-frontend lint lint-backend lint-frontend build setup clean

help:
	@echo "Duplicate Photos Finder - Makefile Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make setup              Install dependencies for both backend and frontend"
	@echo ""
	@echo "Development:"
	@echo "  make start              Start both backend and frontend servers"
	@echo "  make start-backend      Start only backend (Flask) on port 5000"
	@echo "  make start-frontend     Start only frontend (React) on port 3000"
	@echo ""
	@echo "Testing:"
	@echo "  make test               Run all tests (backend + frontend)"
	@echo "  make test-backend       Run backend tests only"
	@echo "  make test-frontend      Run frontend tests only"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint               Lint all code (backend + frontend)"
	@echo "  make lint-backend       Lint backend code (Black + Flake8)"
	@echo "  make lint-frontend      Lint frontend code (ESLint)"
	@echo ""
	@echo "Building:"
	@echo "  make build              Build frontend for production"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean              Remove build artifacts and caches"

# Setup
setup:
	@echo "Setting up backend dependencies..."
	cd backend && pip install -e ".[dev]" && cd ..
	@echo "Setting up frontend dependencies..."
	cd frontend && npm install && cd ..
	@echo "Setup complete!"

# Development servers
start: start-backend start-frontend
	@echo "Both servers started!"

start-backend:
	cd backend && python -m app.main

start-frontend:
	cd frontend && npm start

# Testing
test: test-backend test-frontend
	@echo "All tests completed!"

test-backend:
	cd backend && pytest -v

test-frontend:
	cd frontend && npm test -- --watchAll=false

# Code quality
lint: lint-backend lint-frontend
	@echo "Linting completed!"

lint-backend:
	@echo "Formatting with Black..."
	cd backend && black app/ tests/ && cd ..
	@echo "Checking with Flake8..."
	cd backend && flake8 app/ tests/ && cd ..

lint-frontend:
	@echo "Linting TypeScript..."
	cd frontend && npm run lint && cd ..

# Build
build:
	@echo "Building frontend for production..."
	cd frontend && npm run build && cd ..
	@echo "Build complete! Output in frontend/build/"

# Cleanup
clean:
	@echo "Cleaning up..."
	rm -rf backend/.pytest_cache backend/__pycache__ backend/app/__pycache__ backend/tests/__pycache__
	rm -rf backend/.coverage backend/htmlcov
	rm -rf frontend/build frontend/node_modules/.cache
	@echo "Cleanup complete!"

.DEFAULT_GOAL := help
