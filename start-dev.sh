#!/bin/bash
# Duplicate Photos Finder - Development Server Startup Script
# Runs both backend (Flask) and frontend (React) servers simultaneously
# Usage: ./start-dev.sh [backend|frontend|both]
# Default: both

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKEND_PORT=5000
FRONTEND_PORT=3000
BACKEND_DIR="backend"
FRONTEND_DIR="frontend"

# Get WSL IP address for external access
get_wsl_ip() {
  hostname -I | awk '{print $1}'
}

# Trap to kill both processes on exit
trap cleanup EXIT INT TERM

cleanup() {
  if [ ! -z "$BACKEND_PID" ]; then
    echo -e "${YELLOW}Stopping backend (PID: $BACKEND_PID)...${NC}"
    kill $BACKEND_PID 2>/dev/null || true
  fi
  if [ ! -z "$FRONTEND_PID" ]; then
    echo -e "${YELLOW}Stopping frontend (PID: $FRONTEND_PID)...${NC}"
    kill $FRONTEND_PID 2>/dev/null || true
  fi
  echo -e "${YELLOW}Development servers stopped.${NC}"
}

# Parse command line argument
TARGET="${1:-both}"

# Validate target
if [[ ! "$TARGET" =~ ^(backend|frontend|both)$ ]]; then
  echo -e "${RED}Invalid target: $TARGET${NC}"
  echo "Usage: $0 [backend|frontend|both]"
  exit 1
fi

# Check Python and Node are installed
if [ "$TARGET" == "backend" ] || [ "$TARGET" == "both" ]; then
  if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
  fi
fi

if [ "$TARGET" == "frontend" ] || [ "$TARGET" == "both" ]; then
  if ! command -v npm &> /dev/null; then
    echo -e "${RED}Error: npm is not installed${NC}"
    exit 1
  fi
fi

# Start backend
if [ "$TARGET" == "backend" ] || [ "$TARGET" == "both" ]; then
  echo -e "${BLUE}================================================${NC}"
  echo -e "${BLUE}Starting Backend (Flask) on port $BACKEND_PORT${NC}"
  echo -e "${BLUE}================================================${NC}"
  
  if [ ! -d "$BACKEND_DIR" ]; then
    echo -e "${RED}Error: Backend directory not found at $BACKEND_DIR${NC}"
    exit 1
  fi
  
  # Check if venv exists, if not create it
  if [ ! -d "$BACKEND_DIR/venv" ]; then
    echo -e "${YELLOW}Virtual environment not found. Creating...${NC}"
    cd "$BACKEND_DIR"
    python3 -m venv venv
    source venv/bin/activate
    pip install -e ".[dev]"
    cd ..
  fi
  
  # Activate venv and start server
  cd "$BACKEND_DIR"
  source venv/bin/activate
  cd ..
  
  python3 -m app.main &
  BACKEND_PID=$!
  echo -e "${GREEN}✓ Backend started (PID: $BACKEND_PID)${NC}"
  sleep 2
fi

# Start frontend
if [ "$TARGET" == "frontend" ] || [ "$TARGET" == "both" ]; then
  echo -e "${BLUE}================================================${NC}"
  echo -e "${BLUE}Starting Frontend (React) on port $FRONTEND_PORT${NC}"
  echo -e "${BLUE}================================================${NC}"
  
  if [ ! -d "$FRONTEND_DIR" ]; then
    echo -e "${RED}Error: Frontend directory not found at $FRONTEND_DIR${NC}"
    exit 1
  fi
  
  # Check if node_modules exists
  if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
    echo -e "${YELLOW}Dependencies not found. Running npm install...${NC}"
    cd "$FRONTEND_DIR"
    npm install
    cd ..
  fi
  
  cd "$FRONTEND_DIR"
  HOST=0.0.0.0 npm start &
  FRONTEND_PID=$!
  cd ..
  echo -e "${GREEN}✓ Frontend started (PID: $FRONTEND_PID)${NC}"
  sleep 2
fi

# Display status
echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}✓ Development Servers Running${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""

if [ "$TARGET" == "backend" ] || [ "$TARGET" == "both" ]; then
  echo -e "${BLUE}Backend:${NC}"
  echo "  URL: http://$(get_wsl_ip):$BACKEND_PORT"
  echo "  API Health: http://$(get_wsl_ip):$BACKEND_PORT/api/health"
  echo ""
fi

if [ "$TARGET" == "frontend" ] || [ "$TARGET" == "both" ]; then
  echo -e "${BLUE}Frontend:${NC}"
  echo "  URL: http://$(get_wsl_ip):$FRONTEND_PORT"
  echo ""
fi

echo -e "${YELLOW}Note: Use the above URLs to access from Windows/Edge.${NC}"
echo -e "${YELLOW}WSL IP may change on restart.${NC}"
echo ""

echo -e "${YELLOW}Press Ctrl+C to stop both servers${NC}"
echo ""

# Wait for both processes to exit
if [ ! -z "$BACKEND_PID" ]; then
  wait $BACKEND_PID 2>/dev/null || true
fi

if [ ! -z "$FRONTEND_PID" ]; then
  wait $FRONTEND_PID 2>/dev/null || true
fi
