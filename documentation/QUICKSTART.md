# BetGenius - Quick Start Guide

⚡ Get BetGenius running in under 5 minutes!

---

## Prerequisites Check

Before starting, verify you have:

```bash
# Check Python (need 3.10+)
python --version

# Check Node.js (need 18+)
node --version

# Check MongoDB (need 6.0+)
mongod --version

# Check Yarn
yarn --version
```

If any are missing, see [SETUP.md](./SETUP.md) for installation instructions.

---

## 🚀 5-Minute Setup

### Step 1: Start MongoDB

```bash
# Linux/macOS
sudo systemctl start mongodb

# macOS (Homebrew)
brew services start mongodb-community

# Verify it's running
mongosh --eval "db.version()"
```

### Step 2: Setup Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start backend server
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

✅ Backend running at: **http://localhost:8001**

### Step 3: Setup Frontend (New Terminal)

```bash
cd frontend

# Install dependencies
yarn install

# Start frontend
yarn start
```

✅ Frontend running at: **http://localhost:3000**

### Step 4: Access Application

Open your browser:
```
http://localhost:3000
```

🎉 **You're ready!**

---

## 🎯 First Steps in the App

### 1. Explore the Dashboard
- View upcoming EPL fixtures
- See preset betting models
- Check aggregate statistics

### 2. Create a Custom Model
1. Go to **Models** tab
2. Scroll to "Build Custom Model"
3. Adjust the 5 sliders:
   - Team Offense
   - Team Defense
   - Recent Form
   - Injuries
   - Home Advantage
4. Click **Create Model**

### 3. Generate Picks
1. Go to **Value Finder** tab
2. Select a model (click **Use**)
3. Click **Generate Picks**
4. See picks sorted by confidence (1-10)

### 4. Add to Journal
1. Find a pick you like
2. Click **Add to Journal**
3. Enter stake amount and odds
4. Click **Add Entry**

### 5. Settle a Bet
1. Go to **Journal** tab
2. Find a pending bet
3. Click **Settle**
4. Select the actual result
5. See your profit/loss calculated

---

## 🔍 Testing the API

### Option 1: Using Browser

Open the interactive API docs:
```
http://localhost:8001/docs
```

Try these endpoints:
- `GET /api/models` - List all models
- `GET /api/games` - List fixtures
- `GET /api/stats` - Get statistics

### Option 2: Using curl

```bash
# Get all models
curl http://localhost:8001/api/models

# Get all games
curl http://localhost:8001/api/games

# Get statistics
curl http://localhost:8001/api/stats

# Refresh fixtures
curl -X POST http://localhost:8001/api/refresh-data
```

---

## 🛠️ Common Issues

### MongoDB Not Running
```bash
# Start it
sudo systemctl start mongodb

# Check status
sudo systemctl status mongodb
```

### Port Already in Use
```bash
# Backend (port 8001)
lsof -i :8001
kill -9 <PID>

# Frontend (port 3000)
lsof -i :3000
kill -9 <PID>
```

### Module Not Found
```bash
# Backend
cd backend
source venv/bin/activate
pip install -r requirements.txt

# Frontend
cd frontend
rm -rf node_modules
yarn install
```

### CORS Errors
Check `backend/.env` has:
```
CORS_ORIGINS="*"
```

Then restart backend.

---

## 📱 Using with Supervisor

If you're in a Docker/containerized environment:

```bash
# Start all services
sudo supervisorctl start all

# Check status
sudo supervisorctl status

# Restart if needed
sudo supervisorctl restart backend
sudo supervisorctl restart frontend
```

---

## 🎓 Next Steps

1. **Read the docs**:
   - [DOCUMENTATION.md](./DOCUMENTATION.md) - Technical details
   - [API.md](./API.md) - API reference
   - [SETUP.md](./SETUP.md) - Detailed setup

2. **Experiment**:
   - Create multiple models
   - Compare their picks
   - Track performance over time

3. **Customize**:
   - Modify team ratings in `backend/server.py`
   - Adjust UI styling in `frontend/src/`
   - Add new features

---

## 📊 Understanding the Data

### Mock Data
All data is **simulated** for this MVP:
- ✅ Team ratings are semi-realistic
- ✅ Odds are dynamically generated
- ✅ Fixtures refresh on demand
- ❌ No real API integration (yet)

### Next: Real Data
To integrate real data, you'll need:
- **Football-Data.org** - Match results & stats
- **The Odds API** - Live betting odds
- See "Future Enhancements" in README

---

## 🆘 Need Help?

1. **Check logs**:
   ```bash
   # Backend
   # Check terminal where uvicorn is running
   
   # Frontend
   # Check browser console (F12)
   ```

2. **API not working?**
   - Test: http://localhost:8001/docs
   - Should see Swagger UI

3. **UI not loading?**
   - Check: http://localhost:3000
   - Look for errors in terminal

4. **Still stuck?**
   - Review [SETUP.md](./SETUP.md) troubleshooting section
   - Check MongoDB is running
   - Verify .env files are correct

---

<div align="center">
  <p>🎉 <strong>Happy Betting!</strong> (Responsibly, of course)</p>
  <p>⭐ Star this repo if you find it useful!</p>
</div>
