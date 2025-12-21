# BetGenius - Project Structure

Complete directory structure and file organization for the BetGenius application.

---

## 📁 Root Directory Structure

```
betgenius/
├── backend/                   # FastAPI backend application
├── frontend/                  # React frontend application
├── tests/                     # Test files
├── test_reports/             # Test execution reports
├── .git/                     # Git version control
├── .emergent/                # Emergent platform configuration
├── .gitignore               # Git ignore rules
├── DOCUMENTATION.md         # Detailed technical documentation
├── README.md                # Quick start guide (this file)
├── SETUP.md                 # Detailed setup instructions
├── API.md                   # API reference documentation
├── QUICKSTART.md            # 5-minute quick start guide
├── PROJECT_STRUCTURE.md     # This file - project structure
├── requirements.md          # Original project requirements
├── design_guidelines.json   # UI/UX design guidelines
├── backend_test.py          # Backend testing script
└── test_result.md           # Testing protocol and results
```

---

## 🔧 Backend Directory (`/backend`)

```
backend/
├── server.py                # Main FastAPI application
├── requirements.txt         # Python dependencies
└── .env                     # Environment variables (not in git)
```

### Backend File Details

#### `server.py` (22KB)
Main application file containing:
- **FastAPI app initialization** with CORS middleware
- **MongoDB connection** using Motor (async driver)
- **Data models** (Pydantic):
  - `BettingModel` - Custom and preset betting models
  - `Game` - EPL fixtures with odds
  - `Pick` - Generated betting picks
  - `JournalEntry` - Bet tracking records
- **API Endpoints**:
  - `/api/models` - Model CRUD operations
  - `/api/games` - Fixture management
  - `/api/picks/generate` - Pick generation engine
  - `/api/journal` - Bet tracking
  - `/api/stats` - Performance statistics
- **Dynamic data generator**:
  - EPL team base ratings (20 teams)
  - Randomized form/injury factors
  - Odds generation algorithm
  - Projected score calculation
- **Confidence scoring system** (1-10 scale)

#### `requirements.txt`
Key dependencies:
- `fastapi==0.110.1` - Web framework
- `uvicorn==0.25.0` - ASGI server
- `motor==3.3.1` - Async MongoDB driver
- `pymongo==4.5.0` - MongoDB sync driver
- `pydantic>=2.6.4` - Data validation
- Development tools: `pytest`, `black`, `flake8`, `mypy`
- Data processing: `pandas`, `numpy`

#### `.env`
```env
MONGO_URL="mongodb://localhost:27017"
DB_NAME="test_database"
CORS_ORIGINS="*"
```

---

## 🎨 Frontend Directory (`/frontend`)

```
frontend/
├── public/                  # Static assets
│   └── index.html          # HTML template
├── src/                    # Source code
│   ├── components/         # React components
│   │   ├── ui/            # Shadcn/UI components
│   │   ├── Dashboard.js   # Main dashboard tab
│   │   ├── ModelsTab.js   # Model management tab
│   │   ├── ValueFinder.js # Pick generation tab
│   │   └── Journal.js     # Bet tracking tab
│   ├── hooks/             # Custom React hooks
│   ├── lib/               # Utility libraries
│   │   └── utils.js       # Helper functions
│   ├── App.js             # Main application component
│   ├── App.css            # App-specific styles
│   ├── index.js           # Entry point
│   └── index.css          # Global styles (Tailwind)
├── plugins/               # Custom plugins
│   ├── health-check/      # Health monitoring
│   └── visual-edits/      # Visual editing tools
├── package.json           # Node dependencies & scripts
├── .env                   # Environment variables
├── tailwind.config.js     # Tailwind CSS configuration
├── postcss.config.js      # PostCSS configuration
├── craco.config.js        # Create React App override
├── jsconfig.json          # JavaScript configuration
├── components.json        # Shadcn/UI component config
└── README.md              # Frontend-specific readme
```

### Frontend File Details

#### `src/App.js`
Main application component featuring:
- **4 main tabs** using Shadcn Tabs component:
  1. Dashboard - Overview and statistics
  2. Models - Model creation and management
  3. Value Finder - Pick generation
  4. Journal - Bet tracking
- **State management** with React hooks
- **API integration** using Axios
- **Dark theme** implementation
- **Responsive design** with Tailwind CSS

#### `src/components/ui/`
Shadcn/UI components (30+ components):
- `button.jsx` - Button component
- `card.jsx` - Card container
- `tabs.jsx` - Tab navigation
- `slider.jsx` - Range slider (for model weights)
- `dialog.jsx` - Modal dialogs
- `badge.jsx` - Status badges
- `table.jsx` - Data tables
- And many more...

#### `package.json`
Key dependencies:
- `react@^19.0.0` - UI library
- `react-router-dom@^7.5.1` - Routing
- `axios@^1.8.4` - HTTP client
- `@radix-ui/*` - 30+ Radix UI primitives
- `tailwindcss@^3.4.17` - Utility-first CSS
- `lucide-react@^0.507.0` - Icon library
- `recharts@^3.6.0` - Chart library
- `date-fns@^4.1.0` - Date utilities

#### `tailwind.config.js`
Custom Tailwind configuration:
- **Dark theme** (neon quant aesthetic)
- **Custom colors**: Primary, secondary, accent
- **Custom fonts**: Chivo, JetBrains Mono
- **Custom animations**: Fade in, slide up
- **Extended utilities**: Backdrop blur, gradients

#### `.env`
```env
REACT_APP_BACKEND_URL=https://bet-genius-31.preview.emergentagent.com
WDS_SOCKET_PORT=443
ENABLE_HEALTH_CHECK=false
```

---

## 🧪 Tests Directory (`/tests`)

```
tests/
└── __init__.py             # Test package marker
```

Currently minimal - ready for test expansion.

---

## 📊 Test Reports Directory (`/test_reports`)

```
test_reports/
└── iteration_1.json        # First iteration test results
```

Contains JSON-formatted test execution reports.

---

## 🗄️ Database Schema (MongoDB)

### Collections

#### `models` Collection
```javascript
{
  _id: ObjectId,
  id: String (UUID),
  name: String,
  description: String,
  model_type: "preset" | "custom",
  weights: {
    team_offense: Float,
    team_defense: Float,
    recent_form: Float,
    injuries: Float,
    home_advantage: Float
  },
  created_at: ISODate,
  is_active: Boolean
}
```

#### `picks` Collection (Generated on-demand)
```javascript
{
  _id: ObjectId,
  id: String (UUID),
  game_id: String,
  model_id: String,
  model_name: String,
  home_team: String,
  away_team: String,
  match_date: ISODate,
  predicted_outcome: "home" | "draw" | "away",
  projected_home_score: Float,
  projected_away_score: Float,
  market_odds: Float,
  confidence_score: Int (1-10),
  edge_percentage: Float,
  created_at: ISODate
}
```

#### `journal` Collection
```javascript
{
  _id: ObjectId,
  id: String (UUID),
  pick_id: String,
  game_id: String,
  model_name: String,
  home_team: String,
  away_team: String,
  match_date: ISODate,
  predicted_outcome: String,
  stake: Float,
  odds_taken: Float,
  status: "pending" | "won" | "lost" | "void",
  profit_loss: Float,
  result: String | null,
  created_at: ISODate,
  settled_at: ISODate | null
}
```

---

## 🔐 Environment Variables

### Backend (`.env`)

| Variable | Purpose | Default |
|----------|---------|---------|
| `MONGO_URL` | MongoDB connection string | `mongodb://localhost:27017` |
| `DB_NAME` | Database name | `test_database` |
| `CORS_ORIGINS` | Allowed CORS origins | `*` |

### Frontend (`.env`)

| Variable | Purpose | Example |
|----------|---------|---------|
| `REACT_APP_BACKEND_URL` | Backend API endpoint | `http://localhost:8001` |
| `WDS_SOCKET_PORT` | Webpack dev server port | `443` |
| `ENABLE_HEALTH_CHECK` | Enable health monitoring | `false` |

---

## 📝 Configuration Files

### Root Level

#### `.gitignore`
Excludes from version control:
- `node_modules/`
- `venv/`
- `.env`
- `__pycache__/`
- Build artifacts
- IDE files

### Backend

#### `requirements.txt`
Python package dependencies with pinned versions for reproducibility.

### Frontend

#### `package.json`
- **Scripts**:
  - `start` - Development server (port 3000)
  - `build` - Production build
  - `test` - Run tests
- **Yarn** as package manager (v1.22.22)

#### `craco.config.js`
Create React App configuration override:
- Custom webpack configuration
- Path aliases (`@/components`)
- PostCSS configuration

#### `tailwind.config.js`
Tailwind CSS customization:
- Dark theme presets
- Custom color palette
- Typography settings
- Animation definitions

#### `postcss.config.js`
PostCSS plugins:
- `tailwindcss` - Tailwind processing
- `autoprefixer` - Browser prefixes

#### `jsconfig.json`
JavaScript/React configuration:
- Path mapping for imports
- Module resolution
- JSX support

#### `components.json`
Shadcn/UI configuration:
- Component library settings
- Styling preferences
- Import aliases

---

## 🎯 Key Features by File

### Model Engine (`backend/server.py`)
Lines 40-60: Model weights definition
Lines 200-350: Projected score calculation
Lines 128-200: Dynamic data generator

### Value Finder (`backend/server.py`)
Lines 450-550: Pick generation algorithm
Lines 350-450: Odds comparison logic
Lines 550-600: Confidence scoring

### Journal (`backend/server.py`)
Lines 600-700: Bet tracking CRUD
Lines 700-750: Settlement logic
Lines 750-800: Statistics aggregation

### Dashboard (`frontend/src/App.js`)
Lines 1-200: Dashboard tab component
- Stats cards
- Active models
- Recent bets
- Upcoming fixtures

### Models Tab (`frontend/src/App.js`)
Lines 200-400: Model management
- Preset models display
- Custom model builder
- Weight sliders (5 factors)
- Model deletion

### Value Finder (`frontend/src/App.js`)
Lines 400-600: Pick generation
- Model selection
- Pick generation trigger
- Confidence-sorted picks
- Add to journal action

### Journal Tab (`frontend/src/App.js`)
Lines 600-800: Bet tracking
- Pending bets list
- Settle bet dialog
- Delete bet action
- P/L calculation display

---

## 📦 Build Artifacts (Not in Git)

### Backend
```
backend/
├── venv/                   # Virtual environment
├── __pycache__/           # Python bytecode
└── *.pyc                  # Compiled Python files
```

### Frontend
```
frontend/
├── node_modules/          # Node packages (1GB+)
├── build/                 # Production build output
├── .cache/                # Build cache
└── yarn.lock              # Dependency lock file
```

---

## 🔄 Data Flow

```
User Input (Frontend)
    ↓
React Components (App.js)
    ↓
Axios HTTP Requests
    ↓
FastAPI Backend (server.py)
    ↓
MongoDB (Motor Driver)
    ↓
Database (test_database)
    ↓
Response (JSON)
    ↓
React State Update
    ↓
UI Re-render
```

---

## 🏗️ Architecture Layers

### Presentation Layer
- **Location**: `frontend/src/`
- **Technology**: React 19, Tailwind CSS, Shadcn/UI
- **Responsibility**: User interface, user interactions

### API Layer
- **Location**: `backend/server.py`
- **Technology**: FastAPI, Pydantic
- **Responsibility**: HTTP endpoints, validation, business logic

### Data Access Layer
- **Location**: `backend/server.py` (embedded)
- **Technology**: Motor (async MongoDB driver)
- **Responsibility**: Database operations, queries

### Data Layer
- **Technology**: MongoDB 6.0+
- **Database**: `test_database`
- **Collections**: `models`, `journal`, (picks generated on-demand)

---

## 🚀 Deployment Structure

### Development
```
Localhost
├── MongoDB: localhost:27017
├── Backend: localhost:8001
└── Frontend: localhost:3000
```

### Production (Kubernetes/Supervisor)
```
Container
├── MongoDB: localhost:27017 (internal)
├── Backend: 0.0.0.0:8001 → External URL
└── Frontend: 0.0.0.0:3000 → External URL
```

### Supervisor Configuration
- **Config**: `/etc/supervisor/conf.d/`
- **Logs**: `/var/log/supervisor/`
- **Services**: backend, frontend, mongodb

---

## 📚 Documentation Hierarchy

1. **README.md** - Start here! Quick overview & installation
2. **QUICKSTART.md** - 5-minute setup guide
3. **SETUP.md** - Detailed installation & troubleshooting
4. **DOCUMENTATION.md** - Complete technical specifications
5. **API.md** - REST API reference
6. **PROJECT_STRUCTURE.md** - This file! Project organization
7. **requirements.md** - Original project requirements

---

## 🔧 Development Workflow

### Making Changes

1. **Backend changes**:
   ```bash
   cd backend
   # Edit server.py
   # Auto-reloads via uvicorn --reload
   ```

2. **Frontend changes**:
   ```bash
   cd frontend
   # Edit src/App.js or components
   # Auto-reloads via webpack dev server
   ```

3. **Adding dependencies**:
   ```bash
   # Backend
   cd backend
   pip install <package>
   pip freeze > requirements.txt
   
   # Frontend
   cd frontend
   yarn add <package>
   ```

---

## 📈 Future Structure (Planned)

```
betgenius/
├── backend/
│   ├── models/            # Separate model definitions
│   ├── routes/            # Split API routes
│   ├── services/          # Business logic
│   ├── utils/             # Helper functions
│   └── tests/             # Backend tests
├── frontend/
│   ├── src/
│   │   ├── pages/         # Page components
│   │   ├── features/      # Feature modules
│   │   ├── services/      # API service layer
│   │   └── tests/         # Frontend tests
├── docs/                  # Enhanced documentation
└── deployment/            # Deployment configs
```

---

## 🎓 Learning Path

### For New Developers

1. **Start with documentation**:
   - Read `README.md` for overview
   - Follow `QUICKSTART.md` to run app
   - Explore UI in browser

2. **Understand the backend**:
   - Open `backend/server.py`
   - Find preset models initialization (line ~150)
   - Trace pick generation logic (line ~450)

3. **Understand the frontend**:
   - Open `frontend/src/App.js`
   - Find tab switching logic
   - Trace API calls with Axios

4. **Modify something small**:
   - Add a new team to EPL_TEAMS_BASE
   - Change a color in tailwind.config.js
   - Add a new stat to the dashboard

5. **Deep dive**:
   - Read `DOCUMENTATION.md` for algorithms
   - Study `API.md` for endpoint details
   - Review `SETUP.md` for deployment

---

<div align="center">
  <p>📖 Complete project structure documented!</p>
  <p>Ready to explore and build amazing features 🚀</p>
</div>
