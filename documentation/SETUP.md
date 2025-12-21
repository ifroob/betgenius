# BetGenius - Detailed Setup Guide

This guide provides step-by-step instructions for setting up the BetGenius application for development.

---

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Initial Setup](#initial-setup)
3. [Backend Setup](#backend-setup)
4. [Frontend Setup](#frontend-setup)
5. [Database Setup](#database-setup)
6. [Running the Application](#running-the-application)
7. [Development Workflow](#development-workflow)
8. [Troubleshooting](#troubleshooting)

---

## System Requirements

### Minimum Requirements

- **Operating System**: Linux, macOS, or Windows 10+
- **Python**: 3.10 or higher
- **Node.js**: 18.x or higher
- **MongoDB**: 6.0 or higher
- **RAM**: 4GB minimum (8GB recommended)
- **Disk Space**: 2GB free space

### Required Tools

```bash
# Check Python version
python --version  # or python3 --version

# Check Node.js version
node --version

# Check npm/yarn version
npm --version
yarn --version

# Check MongoDB version
mongod --version
```

---

## Initial Setup

### 1. Clone the Repository

```bash
# Clone the repository
git clone <repository-url>
cd betgenius

# Verify directory structure
ls -la
# You should see: backend/, frontend/, DOCUMENTATION.md, etc.
```

### 2. Install System Dependencies

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install -y python3-pip python3-venv nodejs npm mongodb
sudo npm install -g yarn
```

#### macOS
```bash
# Install Homebrew if not installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python node mongodb-community yarn

# Start MongoDB
brew services start mongodb-community
```

#### Windows
```powershell
# Install using Chocolatey
choco install python nodejs mongodb yarn

# Or download installers:
# Python: https://www.python.org/downloads/
# Node.js: https://nodejs.org/
# MongoDB: https://www.mongodb.com/try/download/community
# Yarn: https://yarnpkg.com/getting-started/install
```

---

## Backend Setup

### 1. Navigate to Backend Directory

```bash
cd backend
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate

# On Windows:
venv\Scripts\activate

# Verify activation (you should see (venv) in your prompt)
which python  # Should point to venv/bin/python
```

### 3. Install Python Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install all requirements
pip install -r requirements.txt

# Verify installations
pip list | grep fastapi
pip list | grep motor
pip list | grep pymongo
```

### 4. Configure Environment Variables

```bash
# Check if .env exists
cat .env

# If not, create it:
cat > .env << EOF
MONGO_URL="mongodb://localhost:27017"
DB_NAME="test_database"
CORS_ORIGINS="*"
EOF

# Verify .env content
cat .env
```

### 5. Test Backend

```bash
# Run server
uvicorn server:app --host 0.0.0.0 --port 8001 --reload

# In another terminal, test the API
curl http://localhost:8001/api/health
curl http://localhost:8001/api/models

# Open API documentation in browser
# http://localhost:8001/docs
```

---

## Frontend Setup

### 1. Navigate to Frontend Directory

```bash
# Open a new terminal
cd frontend
```

### 2. Install Node Dependencies

```bash
# Install dependencies using Yarn
yarn install

# If you encounter errors, try:
rm -rf node_modules yarn.lock
yarn install

# Verify installation
yarn list --depth=0
```

### 3. Configure Environment Variables

```bash
# Check if .env exists
cat .env

# If not, create it:
cat > .env << EOF
REACT_APP_BACKEND_URL=http://localhost:8001
WDS_SOCKET_PORT=443
ENABLE_HEALTH_CHECK=false
EOF

# For production, update REACT_APP_BACKEND_URL accordingly
```

### 4. Test Frontend

```bash
# Start development server
yarn start

# Frontend should automatically open in browser at:
# http://localhost:3000
```

---

## Database Setup

### 1. Start MongoDB

```bash
# Ubuntu/Debian
sudo systemctl start mongodb
sudo systemctl enable mongodb  # Start on boot
sudo systemctl status mongodb

# macOS
brew services start mongodb-community

# Windows (as Administrator)
net start MongoDB
```

### 2. Verify MongoDB Connection

```bash
# Connect to MongoDB shell
mongosh

# In MongoDB shell:
show dbs
use test_database
show collections

# Exit shell
exit
```

### 3. Optional: MongoDB Compass (GUI)

```bash
# Download and install MongoDB Compass
# https://www.mongodb.com/try/download/compass

# Connect to: mongodb://localhost:27017
```

### 4. Database Initialization

The application will automatically:
- Create the database on first run
- Seed preset betting models
- Generate mock fixtures

No manual database setup is required.

---

## Running the Application

### Development Mode (Manual)

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate  # Activate virtual environment
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

**Terminal 2 - Frontend:**
```bash
cd frontend
yarn start
```

**Terminal 3 - MongoDB (if not running as service):**
```bash
mongod --dbpath /path/to/data/db
```

### Development Mode (Using Supervisor)

If running in a containerized environment:

```bash
# Start all services
sudo supervisorctl start all

# Check status
sudo supervisorctl status

# Should show:
# backend    RUNNING
# frontend   RUNNING
# mongodb    RUNNING
```

### Accessing the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8001
- **API Docs**: http://localhost:8001/docs
- **MongoDB**: localhost:27017

---

## Development Workflow

### Hot Reload

Both frontend and backend support hot reload:

- **Backend**: FastAPI auto-reloads on file changes (with `--reload` flag)
- **Frontend**: React auto-reloads on file changes (webpack dev server)

### Making Changes

1. **Backend changes**:
   - Edit files in `backend/`
   - Server will auto-reload
   - Check terminal for errors

2. **Frontend changes**:
   - Edit files in `frontend/src/`
   - Browser will auto-refresh
   - Check browser console for errors

### Code Formatting

```bash
# Backend (Python)
cd backend
black server.py
isort server.py
flake8 server.py

# Frontend (JavaScript/React)
cd frontend
yarn lint
```

### Testing

```bash
# Backend tests
cd backend
python -m pytest

# Frontend tests
cd frontend
yarn test
```

---

## Troubleshooting

### Issue: MongoDB Connection Failed

**Error**: `pymongo.errors.ServerSelectionTimeoutError`

**Solution**:
```bash
# Check if MongoDB is running
sudo systemctl status mongodb

# Restart MongoDB
sudo systemctl restart mongodb

# Check MongoDB logs
sudo tail -f /var/log/mongodb/mongod.log

# Test connection
mongosh --eval "db.version()"
```

### Issue: Port Already in Use

**Error**: `Address already in use`

**Solution**:
```bash
# Find process using port 8001 (backend)
lsof -i :8001
sudo kill -9 <PID>

# Find process using port 3000 (frontend)
lsof -i :3000
sudo kill -9 <PID>
```

### Issue: Python Module Not Found

**Error**: `ModuleNotFoundError: No module named 'fastapi'`

**Solution**:
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt

# Verify installation
pip list
```

### Issue: React App Won't Start

**Error**: Various npm/yarn errors

**Solution**:
```bash
# Clear cache and reinstall
cd frontend
rm -rf node_modules yarn.lock
yarn cache clean
yarn install

# If still failing, check Node.js version
node --version  # Should be 18+
```

### Issue: CORS Errors

**Error**: `Access to fetch at... has been blocked by CORS policy`

**Solution**:
```bash
# Check backend .env
cd backend
cat .env
# Ensure: CORS_ORIGINS="*"

# Restart backend
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

### Issue: Database Not Initializing

**Solution**:
```bash
# Delete and recreate database
mongosh
use test_database
db.dropDatabase()
exit

# Restart backend (will reinitialize)
```

### Getting Help

1. Check logs:
   ```bash
   # Backend logs
   tail -f /var/log/supervisor/backend.*.log
   
   # Frontend logs
   tail -f /var/log/supervisor/frontend.*.log
   ```

2. Enable debug mode:
   ```bash
   # Backend
   export DEBUG=1
   uvicorn server:app --host 0.0.0.0 --port 8001 --reload --log-level debug
   ```

3. Check API documentation:
   - Open http://localhost:8001/docs
   - Test endpoints directly

---

## Next Steps

Once setup is complete:

1. Read [DOCUMENTATION.md](./DOCUMENTATION.md) for technical details
2. Explore the API at http://localhost:8001/docs
3. Start building betting models in the UI
4. Review the code in `backend/server.py` and `frontend/src/App.js`

---

## Environment Variables Reference

### Backend (.env)

| Variable | Description | Default |
|----------|-------------|--------|
| `MONGO_URL` | MongoDB connection string | `mongodb://localhost:27017` |
| `DB_NAME` | Database name | `test_database` |
| `CORS_ORIGINS` | Allowed CORS origins | `*` |

### Frontend (.env)

| Variable | Description | Default |
|----------|-------------|--------|
| `REACT_APP_BACKEND_URL` | Backend API URL | `http://localhost:8001` |
| `WDS_SOCKET_PORT` | Webpack dev server port | `443` |
| `ENABLE_HEALTH_CHECK` | Enable health check endpoint | `false` |

---

<div align="center">
  <p>Happy Coding! 🚀</p>
</div>
