# Quick Start - Running Both Servers

## TL;DR - Just Run This!

### macOS/Linux
```bash
./start-dev.sh both
```

### Windows
```batch
start-dev.bat
```

### Any OS (Node.js)
```bash
node start-dev.js both
```

### With Make
```bash
make start
```

---

## Then Open Your Browser

**Frontend**: http://localhost:3000  
**API Health**: http://localhost:5000/api/health

---

## What Each Script Does

| Script | OS | Benefits | How to Run |
|--------|----|---------|-----------| 
| `start-dev.sh` | macOS/Linux | Built-in setup, single window | `./start-dev.sh both` |
| `start-dev.bat` | Windows | Opens servers in separate windows | Double-click or run in terminal |
| `start-dev.js` | Any OS | Cross-platform, works everywhere | `node start-dev.js both` |
| `Makefile` | macOS/Linux | Powerful build tool, lots of commands | `make start` |

---

## Features

All scripts provide:
- ✅ Automatic dependency installation
- ✅ Virtual environment setup
- ✅ Color-coded output
- ✅ URLs for quick access
- ✅ Graceful shutdown (Ctrl+C)

---

## Full Guide

See `STARTUP_GUIDE.md` for detailed instructions, troubleshooting, and advanced usage.

---

## Manual Alternative

If scripts don't work:

```bash
# Terminal 1: Backend
cd backend
python -m app.main

# Terminal 2: Frontend  
cd frontend
npm start
```

---

**That's it! Happy developing! 🚀**
