#!/usr/bin/env node
/**
 * Duplicate Photos Finder - Development Server Launcher
 * Starts both backend (Flask) and frontend (React) simultaneously
 * Works on Windows, macOS, and Linux
 * 
 * Usage: node start-dev.js [backend|frontend|both]
 */

const { spawn } = require('child_process');
const path = require('path');
const os = require('os');
const fs = require('fs');

const BACKEND_PORT = 5000;
const FRONTEND_PORT = 3000;
const BACKEND_DIR = path.join(__dirname, 'backend');
const FRONTEND_DIR = path.join(__dirname, 'frontend');

// ANSI color codes
const colors = {
  reset: '\x1b[0m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
};

function log(color, message) {
  console.log(`${color}${message}${colors.reset}`);
}

function logSection(title) {
  log(colors.blue, '================================================');
  log(colors.blue, title);
  log(colors.blue, '================================================');
}

function logSuccess(message) {
  log(colors.green, `✓ ${message}`);
}

function logError(message) {
  log(colors.red, `✗ Error: ${message}`);
  process.exit(1);
}

function logWarning(message) {
  log(colors.yellow, `⚠ ${message}`);
}

// Parse arguments
const target = process.argv[2] || 'both';
if (!['backend', 'frontend', 'both'].includes(target)) {
  logError(`Invalid target: ${target}`);
  console.log('Usage: node start-dev.js [backend|frontend|both]');
  process.exit(1);
}

// Track child processes
const processes = [];

// Cleanup on exit
function cleanup() {
  logWarning('Stopping servers...');
  processes.forEach((proc) => {
    if (proc && !proc.killed) {
      proc.kill();
    }
  });
  process.exit(0);
}

process.on('SIGINT', cleanup);
process.on('SIGTERM', cleanup);

// Start backend
function startBackend() {
  logSection(`Starting Backend (Flask) on port ${BACKEND_PORT}`);

  if (!fs.existsSync(BACKEND_DIR)) {
    logError(`Backend directory not found at ${BACKEND_DIR}`);
  }

  const pythonCmd = os.platform() === 'win32' ? 'python' : 'python3';
  const proc = spawn(pythonCmd, ['-m', 'app.main'], {
    cwd: BACKEND_DIR,
    stdio: 'inherit',
    shell: true,
  });

  processes.push(proc);
  logSuccess(`Backend started (PID: ${proc.pid})`);

  proc.on('error', (err) => {
    logError(`Backend failed to start: ${err.message}`);
  });

  proc.on('exit', (code) => {
    if (code !== 0) {
      logError(`Backend exited with code ${code}`);
    }
  });

  return proc;
}

// Start frontend
function startFrontend() {
  logSection(`Starting Frontend (React) on port ${FRONTEND_PORT}`);

  if (!fs.existsSync(FRONTEND_DIR)) {
    logError(`Frontend directory not found at ${FRONTEND_DIR}`);
  }

  // Check if node_modules exists
  if (!fs.existsSync(path.join(FRONTEND_DIR, 'node_modules'))) {
    logWarning('Dependencies not found. Running npm install...');
    const install = spawn('npm', ['install'], {
      cwd: FRONTEND_DIR,
      stdio: 'inherit',
      shell: true,
    });

    return new Promise((resolve) => {
      install.on('exit', (code) => {
        if (code !== 0) {
          logError(`npm install failed with code ${code}`);
        }
        const proc = spawn('npm', ['start'], {
          cwd: FRONTEND_DIR,
          stdio: 'inherit',
          shell: true,
        });
        processes.push(proc);
        logSuccess(`Frontend started (PID: ${proc.pid})`);
        resolve(proc);
      });
    });
  }

  const proc = spawn('npm', ['start'], {
    cwd: FRONTEND_DIR,
    stdio: 'inherit',
    shell: true,
  });

  processes.push(proc);
  logSuccess(`Frontend started (PID: ${proc.pid})`);

  proc.on('error', (err) => {
    logError(`Frontend failed to start: ${err.message}`);
  });

  proc.on('exit', (code) => {
    if (code !== 0) {
      logError(`Frontend exited with code ${code}`);
    }
  });

  return proc;
}

// Main
async function main() {
  console.log();

  if (target === 'backend' || target === 'both') {
    startBackend();
  }

  if (target === 'frontend' || target === 'both') {
    await startFrontend();
  }

  console.log();
  log(colors.green, '================================================');
  log(colors.green, '✓ Development Servers Running');
  log(colors.green, '================================================');
  console.log();

  if (target === 'backend' || target === 'both') {
    log(colors.blue, 'Backend:');
    console.log(`  URL: http://localhost:${BACKEND_PORT}`);
    console.log(`  API Health: http://localhost:${BACKEND_PORT}/api/health`);
    console.log();
  }

  if (target === 'frontend' || target === 'both') {
    log(colors.blue, 'Frontend:');
    console.log(`  URL: http://localhost:${FRONTEND_PORT}`);
    console.log();
  }

  logWarning('Press Ctrl+C to stop both servers');
  console.log();
}

main().catch((err) => {
  logError(err.message);
});
