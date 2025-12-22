from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone
from enum import Enum

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="BetGenius - EPL Betting Analytics")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# ============ ENUMS ============
class BetStatus(str, Enum):
    PENDING = "pending"
    WON = "won"
    LOST = "lost"
    VOID = "void"

class ModelType(str, Enum):
    PRESET = "preset"
    CUSTOM = "custom"

# ============ MODELS ============
# Flexible weights model - accepts any factors as key-value pairs
class ModelWeights(BaseModel):
    model_config = ConfigDict(extra="allow")  # Allow any additional fields
    
    def __init__(self, **data):
        # Ensure all values are floats between 0-100
        validated_data = {}
        for key, value in data.items():
            if isinstance(value, (int, float)):
                validated_data[key] = max(0.0, min(100.0, float(value)))
            else:
                validated_data[key] = 0.0
        super().__init__(**validated_data)
    
    def dict(self, **kwargs):
        # Return all dynamic fields
        return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}
    
    def model_dump(self, **kwargs):
        # Return all dynamic fields
        return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}

class BettingModel(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str = ""
    model_type: ModelType = ModelType.CUSTOM
    weights: ModelWeights
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    is_active: bool = True

class BettingModelCreate(BaseModel):
    name: str
    description: str = ""
    weights: ModelWeights

class EPLTeam(BaseModel):
    name: str
    short_name: str
    offense_rating: float
    defense_rating: float
    form_rating: float
    injury_impact: float

class Game(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    home_team: str
    away_team: str
    match_date: str
    home_odds: float
    draw_odds: float
    away_odds: float
    home_team_data: Optional[dict] = None
    away_team_data: Optional[dict] = None
    result: Optional[str] = None  # "home", "draw", "away", None
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    is_completed: bool = False
    data_source: str = "mock"  # "mock" or "api"
    api_id: Optional[int] = None  # ID from external API

class Pick(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    game_id: str
    model_id: str
    model_name: str
    home_team: str
    away_team: str
    match_date: str
    predicted_outcome: str  # "home", "draw", "away"
    projected_home_score: float
    projected_away_score: float
    market_odds: float
    confidence_score: int  # 1-10
    edge_percentage: float
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class JournalEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    pick_id: str
    game_id: str
    model_name: str
    home_team: str
    away_team: str
    match_date: str
    predicted_outcome: str
    stake: float
    odds_taken: float
    status: BetStatus = BetStatus.PENDING
    profit_loss: float = 0.0
    result: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    settled_at: Optional[str] = None

class JournalEntryCreate(BaseModel):
    pick_id: str
    stake: float
    odds_taken: float

class SettleBetRequest(BaseModel):
    result: str  # "home", "draw", "away"

class SimulationRequest(BaseModel):
    model_id: str
    game_ids: Optional[List[str]] = None  # If None, use all completed games
    min_confidence: Optional[int] = None  # Filter picks by confidence

class SimulationResult(BaseModel):
    model_id: str
    model_name: str
    total_games: int
    correct_predictions: int
    accuracy_percentage: float
    confidence_breakdown: dict  # Accuracy by confidence level
    outcome_breakdown: dict  # Accuracy by outcome type (home/draw/away)
    simulated_roi: float
    average_odds: float
    total_stake: float
    total_return: float

# ============ DYNAMIC DATA GENERATOR ============
import random
from datetime import timedelta

EPL_TEAMS_BASE = {
    "Arsenal": {"short": "ARS", "base_offense": 85, "base_defense": 82},
    "Manchester City": {"short": "MCI", "base_offense": 92, "base_defense": 88},
    "Liverpool": {"short": "LIV", "base_offense": 90, "base_defense": 85},
    "Chelsea": {"short": "CHE", "base_offense": 78, "base_defense": 75},
    "Manchester United": {"short": "MUN", "base_offense": 75, "base_defense": 72},
    "Tottenham": {"short": "TOT", "base_offense": 80, "base_defense": 74},
    "Newcastle": {"short": "NEW", "base_offense": 76, "base_defense": 80},
    "Brighton": {"short": "BHA", "base_offense": 72, "base_defense": 70},
    "Aston Villa": {"short": "AVL", "base_offense": 74, "base_defense": 73},
    "West Ham": {"short": "WHU", "base_offense": 68, "base_defense": 65},
    "Fulham": {"short": "FUL", "base_offense": 70, "base_defense": 68},
    "Brentford": {"short": "BRE", "base_offense": 71, "base_defense": 69},
    "Crystal Palace": {"short": "CRY", "base_offense": 66, "base_defense": 70},
    "Wolves": {"short": "WOL", "base_offense": 65, "base_defense": 72},
    "Bournemouth": {"short": "BOU", "base_offense": 67, "base_defense": 64},
    "Nottingham Forest": {"short": "NFO", "base_offense": 64, "base_defense": 71},
    "Everton": {"short": "EVE", "base_offense": 62, "base_defense": 68},
    "Leicester": {"short": "LEI", "base_offense": 69, "base_defense": 63},
    "Ipswich": {"short": "IPS", "base_offense": 58, "base_defense": 60},
    "Southampton": {"short": "SOU", "base_offense": 60, "base_defense": 58},
}

def get_randomized_teams():
    """Generate team stats with random variations for all factors"""
    teams = {}
    for name, base in EPL_TEAMS_BASE.items():
        # Randomize form (can swing wildly based on recent results)
        form_variation = random.randint(-15, 15)
        form = max(40, min(95, base["base_offense"] + form_variation))
        
        # Randomize injury impact (0-25%)
        injury = random.randint(0, 25)
        
        # Add slight variation to offense/defense
        offense = max(50, min(95, base["base_offense"] + random.randint(-5, 5)))
        defense = max(50, min(95, base["base_defense"] + random.randint(-5, 5)))
        
        # New advanced factors
        rest_days = random.randint(2, 7)  # Days since last match
        motivation = random.randint(60, 95)  # Based on league position/form
        referee_rating = random.randint(65, 85)  # How favorable referee is
        
        teams[name] = {
            "short": base["short"],
            "offense": offense,
            "defense": defense,
            "form": form,
            "injury": injury,
            "rest_days": rest_days,
            "motivation": motivation,
            "referee_rating": referee_rating
        }
    return teams

def generate_odds(home_strength: float, away_strength: float) -> tuple:
    """Generate realistic odds based on team strengths with randomness"""
    diff = home_strength - away_strength + random.uniform(-10, 10)  # Home advantage + noise
    
    # Base probabilities with variation
    if diff > 15:
        home_prob = random.uniform(0.55, 0.70)
        draw_prob = random.uniform(0.18, 0.25)
    elif diff > 5:
        home_prob = random.uniform(0.42, 0.55)
        draw_prob = random.uniform(0.22, 0.30)
    elif diff > -5:
        home_prob = random.uniform(0.32, 0.42)
        draw_prob = random.uniform(0.28, 0.35)
    elif diff > -15:
        home_prob = random.uniform(0.25, 0.35)
        draw_prob = random.uniform(0.25, 0.32)
    else:
        home_prob = random.uniform(0.15, 0.28)
        draw_prob = random.uniform(0.20, 0.28)
    
    away_prob = 1 - home_prob - draw_prob
    
    # Convert to decimal odds with bookmaker margin (5-8%)
    margin = random.uniform(1.05, 1.08)
    h_odds = round(margin / home_prob, 2)
    d_odds = round(margin / draw_prob, 2)
    a_odds = round(margin / away_prob, 2)
    
    return h_odds, d_odds, a_odds

def generate_fixtures():
    """Generate random EPL fixtures with dynamic odds"""
    team_names = list(EPL_TEAMS_BASE.keys())
    random.shuffle(team_names)
    
    fixtures = []
    teams = get_randomized_teams()
    
    # Generate 8 random fixtures
    used_teams = set()
    base_date = datetime.now(timezone.utc)
    
    kickoff_times = ["12:30", "15:00", "17:30", "20:00"]
    
    for i in range(8):
        # Pick two teams that haven't played yet
        available = [t for t in team_names if t not in used_teams]
        if len(available) < 2:
            used_teams.clear()
            available = team_names.copy()
        
        random.shuffle(available)
        home_team = available[0]
        away_team = available[1]
        used_teams.add(home_team)
        used_teams.add(away_team)
        
        # Generate match date (spread over next 7 days)
        match_date = base_date + timedelta(days=i // 2, hours=random.randint(0, 8))
        kickoff = random.choice(kickoff_times)
        date_str = f"{match_date.strftime('%Y-%m-%d')} {kickoff}"
        
        # Generate game-specific advanced factors
        head_to_head_home = random.randint(30, 70)  # Historical home win %
        weather_rating = random.randint(50, 100)  # 100 = perfect, 50 = poor
        travel_distance_km = random.randint(50, 400)  # Distance away team travels
        
        # Generate odds based on team strengths
        home_strength = teams[home_team]["offense"] + teams[home_team]["form"] - teams[home_team]["injury"]
        away_strength = teams[away_team]["offense"] + teams[away_team]["form"] - teams[away_team]["injury"]
        h_odds, d_odds, a_odds = generate_odds(home_strength, away_strength)
        
        fixtures.append({
            "home": home_team,
            "away": away_team,
            "date": date_str,
            "h_odds": h_odds,
            "d_odds": d_odds,
            "a_odds": a_odds,
            "head_to_head_home": head_to_head_home,
            "weather_rating": weather_rating,
            "travel_distance": travel_distance_km
        })
    
    return fixtures, teams

# Generate fresh data on each server restart
MOCK_GAMES, EPL_TEAMS = generate_fixtures()

# Generate historical games with completed results for simulation
HISTORICAL_GAMES = []

# Store API games globally
API_GAMES = []
API_TEAMS = {}

def generate_historical_games(count=20):
    """Generate historical games with completed results for backtesting"""
    global HISTORICAL_GAMES
    team_names = list(EPL_TEAMS_BASE.keys())
    historical = []
    teams = get_randomized_teams()
    
    base_date = datetime.now(timezone.utc) - timedelta(days=30)  # Games from last 30 days
    used_teams = set()
    kickoff_times = ["12:30", "15:00", "17:30", "20:00"]
    
    for i in range(count):
        available = [t for t in team_names if t not in used_teams]
        if len(available) < 2:
            used_teams.clear()
            available = team_names.copy()
        
        random.shuffle(available)
        home_team = available[0]
        away_team = available[1]
        used_teams.add(home_team)
        used_teams.add(away_team)
        
        match_date = base_date + timedelta(days=i // 2, hours=random.randint(0, 8))
        kickoff = random.choice(kickoff_times)
        date_str = f"{match_date.strftime('%Y-%m-%d')} {kickoff}"
        
        home_strength = teams[home_team]["offense"] + teams[home_team]["form"] - teams[home_team]["injury"]
        away_strength = teams[away_team]["offense"] + teams[away_team]["form"] - teams[away_team]["injury"]
        h_odds, d_odds, a_odds = generate_odds(home_strength, away_strength)
        
        # Simulate actual result based on team strengths
        diff = home_strength - away_strength
        rand = random.random()
        if diff > 15 and rand < 0.6:
            result = "home"
            home_score = random.randint(2, 4)
            away_score = random.randint(0, 1)
        elif diff < -15 and rand < 0.6:
            result = "away"
            home_score = random.randint(0, 1)
            away_score = random.randint(2, 4)
        elif abs(diff) < 10 and rand < 0.3:
            result = "draw"
            home_score = random.randint(1, 2)
            away_score = home_score
        else:
            # More realistic distribution
            outcomes = ["home", "draw", "away"]
            weights = [0.45, 0.27, 0.28]
            result = random.choices(outcomes, weights=weights)[0]
            if result == "home":
                home_score = random.randint(1, 3)
                away_score = random.randint(0, home_score - 1) if home_score > 1 else 0
            elif result == "away":
                away_score = random.randint(1, 3)
                home_score = random.randint(0, away_score - 1) if away_score > 1 else 0
            else:
                home_score = random.randint(0, 2)
                away_score = home_score
        
        head_to_head_home = random.randint(30, 70)
        weather_rating = random.randint(50, 100)
        travel_distance_km = random.randint(50, 400)
        
        historical.append({
            "id": f"hist-{i+1}",
            "home": home_team,
            "away": away_team,
            "date": date_str,
            "h_odds": h_odds,
            "d_odds": d_odds,
            "a_odds": a_odds,
            "head_to_head_home": head_to_head_home,
            "weather_rating": weather_rating,
            "travel_distance": travel_distance_km,
            "result": result,
            "home_score": home_score,
            "away_score": away_score,
            "is_completed": True,
            "data_source": "mock"
        })
    
    HISTORICAL_GAMES = historical
    return historical

generate_historical_games()

# ============ FOOTBALL-DATA.ORG API INTEGRATION ============
FOOTBALL_API_KEY = os.environ.get('FOOTBALL_API_KEY', '')  # Get from env or leave empty
FOOTBALL_API_URL = "https://api.football-data.org/v4"

def calculate_team_stats_from_matches(matches):
    """Calculate team statistics from match history"""
    team_stats = {}
    
    for match in matches:
        if match.get("is_completed") and match.get("home_score") is not None:
            home_team = match["home"]
            away_team = match["away"]
            home_score = match["home_score"]
            away_score = match["away_score"]
            
            # Initialize teams if not exists
            if home_team not in team_stats:
                team_stats[home_team] = {
                    "goals_scored": 0,
                    "goals_conceded": 0,
                    "matches": 0,
                    "wins": 0,
                    "draws": 0,
                    "losses": 0,
                    "home_matches": 0,
                    "home_wins": 0
                }
            if away_team not in team_stats:
                team_stats[away_team] = {
                    "goals_scored": 0,
                    "goals_conceded": 0,
                    "matches": 0,
                    "wins": 0,
                    "draws": 0,
                    "losses": 0,
                    "home_matches": 0,
                    "home_wins": 0
                }
            
            # Update home team stats
            team_stats[home_team]["goals_scored"] += home_score
            team_stats[home_team]["goals_conceded"] += away_score
            team_stats[home_team]["matches"] += 1
            team_stats[home_team]["home_matches"] += 1
            
            # Update away team stats
            team_stats[away_team]["goals_scored"] += away_score
            team_stats[away_team]["goals_conceded"] += home_score
            team_stats[away_team]["matches"] += 1
            
            # Update win/draw/loss
            if home_score > away_score:
                team_stats[home_team]["wins"] += 1
                team_stats[home_team]["home_wins"] += 1
                team_stats[away_team]["losses"] += 1
            elif away_score > home_score:
                team_stats[away_team]["wins"] += 1
                team_stats[home_team]["losses"] += 1
            else:
                team_stats[home_team]["draws"] += 1
                team_stats[away_team]["draws"] += 1
    
    # Convert to ratings (0-100 scale)
    teams = {}
    for team_name, stats in team_stats.items():
        if stats["matches"] > 0:
            # Offense rating based on goals scored per match (scale 0-3 goals to 50-95)
            avg_goals = stats["goals_scored"] / stats["matches"]
            offense = min(95, max(50, 50 + (avg_goals * 15)))
            
            # Defense rating based on goals conceded per match (inverse scale)
            avg_conceded = stats["goals_conceded"] / stats["matches"]
            defense = min(95, max(50, 95 - (avg_conceded * 15)))
            
            # Form rating based on win percentage
            win_rate = stats["wins"] / stats["matches"]
            form = min(95, max(40, 40 + (win_rate * 55)))
            
            # Injury impact - random for now since not in API
            injury = random.randint(0, 20)
            
            # Additional factors
            rest_days = random.randint(3, 7)
            motivation = min(95, max(60, 60 + (win_rate * 35)))
            referee_rating = random.randint(70, 85)
            
            teams[team_name] = {
                "short": team_name[:3].upper(),
                "offense": round(offense, 1),
                "defense": round(defense, 1),
                "form": round(form, 1),
                "injury": round(injury, 1),
                "rest_days": rest_days,
                "motivation": round(motivation, 1),
                "referee_rating": referee_rating,
                "stats": stats  # Keep raw stats for reference
            }
        else:
            # Default values for teams with no completed matches
            teams[team_name] = {
                "short": team_name[:3].upper(),
                "offense": 70.0,
                "defense": 70.0,
                "form": 70.0,
                "injury": 10.0,
                "rest_days": 4,
                "motivation": 75.0,
                "referee_rating": 75
            }
    
    return teams

async def fetch_epl_fixtures_from_api():
    """Fetch real EPL fixtures from football-data.org API and update global state"""
    global API_GAMES, API_TEAMS
    
    if not FOOTBALL_API_KEY:
        logger.info("No Football API key found, using mock data")
        return False
    
    try:
        import httpx
        headers = {"X-Auth-Token": FOOTBALL_API_KEY}
        
        async with httpx.AsyncClient() as client:
            # EPL competition code is 'PL' (Premier League)
            # Fetch both scheduled and finished matches
            response = await client.get(
                f"{FOOTBALL_API_URL}/competitions/PL/matches",
                headers=headers,
                params={"status": "SCHEDULED,TIMED,IN_PLAY,PAUSED,FINISHED"},
                timeout=15.0
            )
            
            if response.status_code != 200:
                logger.error(f"Football API error: {response.status_code} - {response.text}")
                return False
            
            data = response.json()
            matches = data.get("matches", [])
            
            if not matches:
                logger.warning("No matches returned from API")
                return False
            
            logger.info(f"Fetched {len(matches)} matches from Football API")
            
            # Separate finished and upcoming matches
            finished_matches = []
            upcoming_matches = []
            
            for match in matches:
                home_team = match["homeTeam"]["name"]
                away_team = match["awayTeam"]["name"]
                match_date = match["utcDate"]
                status = match["status"]
                
                game = {
                    "id": f"api-{match['id']}",
                    "home": home_team,
                    "away": away_team,
                    "date": match_date,
                    "head_to_head_home": 50,
                    "weather_rating": 80,
                    "travel_distance": random.randint(50, 400),
                    "data_source": "api",
                    "api_id": match["id"],
                    "is_completed": status == "FINISHED"
                }
                
                # Add result if finished
                if status == "FINISHED":
                    score = match.get("score", {}).get("fullTime", {})
                    home_score = score.get("home")
                    away_score = score.get("away")
                    
                    if home_score is not None and away_score is not None:
                        game["home_score"] = home_score
                        game["away_score"] = away_score
                        
                        if home_score > away_score:
                            game["result"] = "home"
                        elif away_score > home_score:
                            game["result"] = "away"
                        else:
                            game["result"] = "draw"
                        
                        finished_matches.append(game)
                else:
                    upcoming_matches.append(game)
            
            # Calculate team stats from finished matches
            logger.info(f"Calculating team stats from {len(finished_matches)} completed matches")
            API_TEAMS = calculate_team_stats_from_matches(finished_matches)
            
            # Generate odds for upcoming matches based on team stats
            for game in upcoming_matches:
                home_team = game["home"]
                away_team = game["away"]
                
                # Get team stats or use defaults
                home_stats = API_TEAMS.get(home_team, {"offense": 70, "defense": 70, "form": 70})
                away_stats = API_TEAMS.get(away_team, {"offense": 70, "defense": 70, "form": 70})
                
                # Calculate strength based on stats
                home_strength = (home_stats["offense"] + home_stats["form"]) / 2
                away_strength = (away_stats["offense"] + away_stats["form"]) / 2
                
                h_odds, d_odds, a_odds = generate_odds(home_strength, away_strength)
                game["h_odds"] = h_odds
                game["d_odds"] = d_odds
                game["a_odds"] = a_odds
            
            # Also add odds to finished matches for historical analysis
            for game in finished_matches:
                home_team = game["home"]
                away_team = game["away"]
                home_stats = API_TEAMS.get(home_team, {"offense": 70, "defense": 70, "form": 70})
                away_stats = API_TEAMS.get(away_team, {"offense": 70, "defense": 70, "form": 70})
                home_strength = (home_stats["offense"] + home_stats["form"]) / 2
                away_strength = (away_stats["offense"] + away_stats["form"]) / 2
                h_odds, d_odds, a_odds = generate_odds(home_strength, away_strength)
                game["h_odds"] = h_odds
                game["d_odds"] = d_odds
                game["a_odds"] = a_odds
            
            # Store upcoming matches (limit to 15 for display)
            API_GAMES = upcoming_matches[:15]
            
            # Store finished matches as historical data for simulation
            global HISTORICAL_GAMES
            HISTORICAL_GAMES = finished_matches[-30:]  # Keep last 30 completed matches
            
            logger.info(f"Updated API_GAMES with {len(API_GAMES)} upcoming matches")
            logger.info(f"Updated HISTORICAL_GAMES with {len(HISTORICAL_GAMES)} completed matches")
            logger.info(f"Calculated stats for {len(API_TEAMS)} teams")
            
            return True
            
    except Exception as e:
        logger.error(f"Error fetching from Football API: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

PRESET_MODELS = [
    {
        "id": "preset-balanced",
        "name": "Balanced Pro",
        "description": "Equal weighting across all 11 factors - great for beginners",
        "model_type": "preset",
        "weights": {
            "team_offense": 10, "team_defense": 10, "recent_form": 10, "injuries": 10, "home_advantage": 10,
            "head_to_head": 10, "rest_days": 10, "travel_distance": 10, "referee_influence": 10, 
            "weather_conditions": 5, "motivation_level": 5
        },
    },
    {
        "id": "preset-form-focused",
        "name": "Form Hunter",
        "description": "Emphasizes recent form, rest, and motivation",
        "model_type": "preset",
        "weights": {
            "team_offense": 10, "team_defense": 10, "recent_form": 25, "injuries": 8, "home_advantage": 12,
            "head_to_head": 8, "rest_days": 12, "travel_distance": 5, "referee_influence": 3, 
            "weather_conditions": 2, "motivation_level": 5
        },
    },
    {
        "id": "preset-stats-heavy",
        "name": "Stats Machine",
        "description": "Heavy focus on offensive, defensive, and historical metrics",
        "model_type": "preset",
        "weights": {
            "team_offense": 20, "team_defense": 20, "recent_form": 8, "injuries": 12, "home_advantage": 8,
            "head_to_head": 15, "rest_days": 5, "travel_distance": 5, "referee_influence": 3, 
            "weather_conditions": 2, "motivation_level": 2
        },
    },
]

# ============ HELPER FUNCTIONS ============
def calculate_team_score(team_name: str, weights: dict, is_home: bool, game_data: dict = None) -> tuple:
    """Calculate projected score for a team based on model weights
    Returns: (score, factor_breakdown)
    """
    # Try API teams first, then mock teams
    team = API_TEAMS.get(team_name) or EPL_TEAMS.get(team_name, {})
    if not team:
        return 1.5, {}
    
    if game_data is None:
        game_data = {}
    
    # Normalize weights to sum to 100
    total_weight = sum(weights.values())
    if total_weight == 0:
        return 1.5, {}
    
    norm_weights = {k: v / total_weight for k, v in weights.items()}
    
    # Track each factor's contribution for transparency
    breakdown = {}
    
    # Core factors (0-3 goals range)
    offense_value = team.get("offense", 70) / 100
    offense_contrib = offense_value * norm_weights.get("team_offense", 0) * 3
    breakdown["team_offense"] = {
        "raw_value": team.get("offense", 70),
        "normalized": offense_value,
        "weight": norm_weights.get("team_offense", 0) * 100,
        "contribution": offense_contrib,
        "description": f"Offensive rating of {team.get('offense', 70)}/100"
    }
    
    defense_value = team.get("defense", 70) / 100
    defense_contrib = defense_value * norm_weights.get("team_defense", 0) * 0.5  # Defense helps scoring indirectly
    breakdown["team_defense"] = {
        "raw_value": team.get("defense", 70),
        "normalized": defense_value,
        "weight": norm_weights.get("team_defense", 0) * 100,
        "contribution": defense_contrib,
        "description": f"Defensive rating of {team.get('defense', 70)}/100"
    }
    
    form_value = team.get("form", 70) / 100
    form_contrib = form_value * norm_weights.get("recent_form", 0) * 2
    breakdown["recent_form"] = {
        "raw_value": team.get("form", 70),
        "normalized": form_value,
        "weight": norm_weights.get("recent_form", 0) * 100,
        "contribution": form_contrib,
        "description": f"Recent form rating of {team.get('form', 70)}/100"
    }
    
    injury_value = team.get("injury", 10) / 100
    injury_penalty = injury_value * norm_weights.get("injuries", 0) * 1.5
    breakdown["injuries"] = {
        "raw_value": team.get("injury", 10),
        "normalized": injury_value,
        "weight": norm_weights.get("injuries", 0) * 100,
        "contribution": -injury_penalty,
        "description": f"{team.get('injury', 10)}% squad affected by injuries"
    }
    
    home_bonus = 0.3 * norm_weights.get("home_advantage", 0) if is_home else -0.1 * norm_weights.get("home_advantage", 0)
    breakdown["home_advantage"] = {
        "raw_value": 100 if is_home else 0,
        "normalized": 1.0 if is_home else 0.0,
        "weight": norm_weights.get("home_advantage", 0) * 100,
        "contribution": home_bonus,
        "description": "Playing at home" if is_home else "Playing away"
    }
    
    # Advanced factors
    h2h_value = game_data.get("head_to_head_home", 50) / 100 if is_home else (100 - game_data.get("head_to_head_home", 50)) / 100
    h2h_contrib = h2h_value * norm_weights.get("head_to_head", 0) * 0.5
    breakdown["head_to_head"] = {
        "raw_value": game_data.get("head_to_head_home", 50) if is_home else 100 - game_data.get("head_to_head_home", 50),
        "normalized": h2h_value,
        "weight": norm_weights.get("head_to_head", 0) * 100,
        "contribution": h2h_contrib,
        "description": f"Historical win rate: {int(h2h_value * 100)}%"
    }
    
    rest_value = min(team.get("rest_days", 4) / 7, 1.0)
    rest_contrib = rest_value * norm_weights.get("rest_days", 0) * 0.4
    breakdown["rest_days"] = {
        "raw_value": team.get("rest_days", 4),
        "normalized": rest_value,
        "weight": norm_weights.get("rest_days", 0) * 100,
        "contribution": rest_contrib,
        "description": f"{team.get('rest_days', 4)} days since last match"
    }
    
    # Travel penalty for away team
    travel_value = 0 if is_home else min(game_data.get("travel_distance", 150) / 400, 1.0)
    travel_penalty = travel_value * norm_weights.get("travel_distance", 0) * 0.3
    breakdown["travel_distance"] = {
        "raw_value": 0 if is_home else game_data.get("travel_distance", 150),
        "normalized": travel_value,
        "weight": norm_weights.get("travel_distance", 0) * 100,
        "contribution": -travel_penalty,
        "description": f"No travel" if is_home else f"{game_data.get('travel_distance', 150)}km travel"
    }
    
    referee_value = team.get("referee_rating", 75) / 100
    referee_contrib = referee_value * norm_weights.get("referee_influence", 0) * 0.2
    breakdown["referee_influence"] = {
        "raw_value": team.get("referee_rating", 75),
        "normalized": referee_value,
        "weight": norm_weights.get("referee_influence", 0) * 100,
        "contribution": referee_contrib,
        "description": f"Referee favorability: {team.get('referee_rating', 75)}/100"
    }
    
    weather_value = game_data.get("weather_rating", 80) / 100
    weather_contrib = weather_value * norm_weights.get("weather_conditions", 0) * 0.15
    breakdown["weather_conditions"] = {
        "raw_value": game_data.get("weather_rating", 80),
        "normalized": weather_value,
        "weight": norm_weights.get("weather_conditions", 0) * 100,
        "contribution": weather_contrib,
        "description": f"Weather conditions: {game_data.get('weather_rating', 80)}/100"
    }
    
    motivation_value = team.get("motivation", 75) / 100
    motivation_contrib = motivation_value * norm_weights.get("motivation_level", 0) * 0.3
    breakdown["motivation_level"] = {
        "raw_value": team.get("motivation", 75),
        "normalized": motivation_value,
        "weight": norm_weights.get("motivation_level", 0) * 100,
        "contribution": motivation_contrib,
        "description": f"Team motivation: {team.get('motivation', 75)}/100"
    }
    
    # Calculate final score
    score = (offense_contrib + defense_contrib + form_contrib + home_bonus + 
             h2h_contrib + rest_contrib + referee_contrib + weather_contrib + 
             motivation_contrib - injury_penalty - travel_penalty)
    
    score = round(max(0.5, min(4.0, score)), 2)
    
    return score, breakdown

def calculate_confidence(model_prob: float, market_prob: float) -> int:
    """Calculate confidence score 1-10 based on edge"""
    edge = (model_prob - market_prob) / market_prob * 100
    if edge <= 0:
        return max(1, int(5 + edge / 5))
    elif edge < 5:
        return 6
    elif edge < 10:
        return 7
    elif edge < 15:
        return 8
    elif edge < 25:
        return 9
    else:
        return 10

def calculate_outcome_probabilities(home_score: float, away_score: float) -> dict:
    """Convert projected scores to outcome probabilities"""
    diff = home_score - away_score
    
    # Simple probability model based on score difference
    if diff > 0.8:
        home_prob = 0.55 + min(diff * 0.1, 0.3)
        draw_prob = 0.25 - min(diff * 0.05, 0.15)
        away_prob = 1 - home_prob - draw_prob
    elif diff < -0.8:
        away_prob = 0.55 + min(abs(diff) * 0.1, 0.3)
        draw_prob = 0.25 - min(abs(diff) * 0.05, 0.15)
        home_prob = 1 - away_prob - draw_prob
    else:
        draw_prob = 0.30
        home_prob = 0.35 + diff * 0.1
        away_prob = 1 - home_prob - draw_prob
    
    return {
        "home": round(max(0.05, min(0.85, home_prob)), 3),
        "draw": round(max(0.10, min(0.40, draw_prob)), 3),
        "away": round(max(0.05, min(0.85, away_prob)), 3)
    }

# ============ API ROUTES ============

@api_router.get("/")
async def root():
    return {
        "message": "BetGenius EPL API",
        "version": "1.0.0",
        "data_source": "api" if API_GAMES else "mock",
        "games_loaded": len(API_GAMES) if API_GAMES else len(MOCK_GAMES),
        "teams_loaded": len(API_TEAMS) if API_TEAMS else len(EPL_TEAMS)
    }

# ---- Teams ----
@api_router.get("/teams")
async def get_teams():
    teams = []
    
    # Use API teams if available, otherwise use mock teams
    source_teams = API_TEAMS if API_TEAMS else EPL_TEAMS
    
    for name, data in source_teams.items():
        teams.append({
            "name": name,
            "short_name": data.get("short", name[:3].upper()),
            "offense_rating": data.get("offense", 70),
            "defense_rating": data.get("defense", 70),
            "form_rating": data.get("form", 70),
            "injury_impact": data.get("injury", 10)
        })
    return teams

@api_router.post("/refresh-data")
async def refresh_data():
    """Fetch fresh data from API, fallback to regenerating mock data"""
    success = await fetch_epl_fixtures_from_api()
    
    if success:
        return {
            "message": "Data refreshed from Football API",
            "games": len(API_GAMES),
            "teams": len(API_TEAMS),
            "historical_games": len(HISTORICAL_GAMES),
            "source": "api"
        }
    else:
        # Fallback: regenerate mock data
        global MOCK_GAMES, EPL_TEAMS
        MOCK_GAMES, EPL_TEAMS = generate_fixtures()
        return {
            "message": "API unavailable, regenerated mock data",
            "games": len(MOCK_GAMES),
            "teams": len(EPL_TEAMS),
            "source": "mock"
        }

# ---- Games ----
@api_router.get("/games")
async def get_games(include_historical: bool = False, source: str = "auto"):
    """Get games - tries API first, falls back to mock if API unavailable
    source: 'auto' (default - tries API first), 'api', 'mock', 'all'
    """
    games = []
    
    # Auto mode: Try API first, fallback to mock
    if source == "auto":
        if API_GAMES:
            # Use cached API games
            for g in API_GAMES:
                home_data = API_TEAMS.get(g["home"], {})
                away_data = API_TEAMS.get(g["away"], {})
                games.append({
                    "id": g["id"],
                    "home_team": g["home"],
                    "away_team": g["away"],
                    "match_date": g["date"],
                    "home_odds": g.get("h_odds", 2.0),
                    "draw_odds": g.get("d_odds", 3.0),
                    "away_odds": g.get("a_odds", 3.0),
                    "home_team_data": home_data,
                    "away_team_data": away_data,
                    "result": g.get("result"),
                    "home_score": g.get("home_score"),
                    "away_score": g.get("away_score"),
                    "is_completed": g.get("is_completed", False),
                    "data_source": "api",
                    "api_id": g.get("api_id")
                })
        else:
            # Fallback to mock data
            logger.info("No API data available, using mock data")
            for i, g in enumerate(MOCK_GAMES):
                home_data = EPL_TEAMS.get(g["home"], {})
                away_data = EPL_TEAMS.get(g["away"], {})
                games.append({
                    "id": f"game-{i+1}",
                    "home_team": g["home"],
                    "away_team": g["away"],
                    "match_date": g["date"],
                    "home_odds": g["h_odds"],
                    "draw_odds": g["d_odds"],
                    "away_odds": g["a_odds"],
                    "home_team_data": home_data,
                    "away_team_data": away_data,
                    "result": None,
                    "home_score": None,
                    "away_score": None,
                    "is_completed": False,
                    "data_source": "mock"
                })
    
    # API mode: Only API data
    elif source == "api":
        for g in API_GAMES:
            home_data = API_TEAMS.get(g["home"], {})
            away_data = API_TEAMS.get(g["away"], {})
            games.append({
                "id": g["id"],
                "home_team": g["home"],
                "away_team": g["away"],
                "match_date": g["date"],
                "home_odds": g.get("h_odds", 2.0),
                "draw_odds": g.get("d_odds", 3.0),
                "away_odds": g.get("a_odds", 3.0),
                "home_team_data": home_data,
                "away_team_data": away_data,
                "result": g.get("result"),
                "home_score": g.get("home_score"),
                "away_score": g.get("away_score"),
                "is_completed": g.get("is_completed", False),
                "data_source": "api",
                "api_id": g.get("api_id")
            })
    
    # Mock mode: Only mock data
    elif source == "mock":
        for i, g in enumerate(MOCK_GAMES):
            home_data = EPL_TEAMS.get(g["home"], {})
            away_data = EPL_TEAMS.get(g["away"], {})
            games.append({
                "id": f"game-{i+1}",
                "home_team": g["home"],
                "away_team": g["away"],
                "match_date": g["date"],
                "home_odds": g["h_odds"],
                "draw_odds": g["d_odds"],
                "away_odds": g["a_odds"],
                "home_team_data": home_data,
                "away_team_data": away_data,
                "result": None,
                "home_score": None,
                "away_score": None,
                "is_completed": False,
                "data_source": "mock"
            })
    
    # All mode: Both API and mock
    elif source == "all":
        # Add API games
        for g in API_GAMES:
            home_data = API_TEAMS.get(g["home"], {})
            away_data = API_TEAMS.get(g["away"], {})
            games.append({
                "id": g["id"],
                "home_team": g["home"],
                "away_team": g["away"],
                "match_date": g["date"],
                "home_odds": g.get("h_odds", 2.0),
                "draw_odds": g.get("d_odds", 3.0),
                "away_odds": g.get("a_odds", 3.0),
                "home_team_data": home_data,
                "away_team_data": away_data,
                "result": g.get("result"),
                "home_score": g.get("home_score"),
                "away_score": g.get("away_score"),
                "is_completed": g.get("is_completed", False),
                "data_source": "api",
                "api_id": g.get("api_id")
            })
        
        # Add mock games
        for i, g in enumerate(MOCK_GAMES):
            home_data = EPL_TEAMS.get(g["home"], {})
            away_data = EPL_TEAMS.get(g["away"], {})
            games.append({
                "id": f"game-{i+1}",
                "home_team": g["home"],
                "away_team": g["away"],
                "match_date": g["date"],
                "home_odds": g["h_odds"],
                "draw_odds": g["d_odds"],
                "away_odds": g["a_odds"],
                "home_team_data": home_data,
                "away_team_data": away_data,
                "result": None,
                "home_score": None,
                "away_score": None,
                "is_completed": False,
                "data_source": "mock"
            })
    
    # Add historical games if requested
    if include_historical:
        for g in HISTORICAL_GAMES:
            # Check if using API teams or mock teams
            if g.get("data_source") == "api":
                home_data = API_TEAMS.get(g["home"], {})
                away_data = API_TEAMS.get(g["away"], {})
            else:
                home_data = EPL_TEAMS.get(g["home"], {})
                away_data = EPL_TEAMS.get(g["away"], {})
            
            games.append({
                "id": g["id"],
                "home_team": g["home"],
                "away_team": g["away"],
                "match_date": g["date"],
                "home_odds": g.get("h_odds", 2.0),
                "draw_odds": g.get("d_odds", 3.0),
                "away_odds": g.get("a_odds", 3.0),
                "home_team_data": home_data,
                "away_team_data": away_data,
                "result": g.get("result"),
                "home_score": g.get("home_score"),
                "away_score": g.get("away_score"),
                "is_completed": g.get("is_completed", False),
                "data_source": g.get("data_source", "mock")
            })
    
    return games

# ---- Models ----
@api_router.get("/models")
async def get_models():
    # Get preset models
    models = []
    for p in PRESET_MODELS:
        models.append({
            "id": p["id"],
            "name": p["name"],
            "description": p["description"],
            "model_type": p["model_type"],
            "weights": p["weights"],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "is_active": True
        })
    
    # Get custom models from DB
    custom_models = await db.models.find({}, {"_id": 0}).to_list(100)
    models.extend(custom_models)
    
    return models

@api_router.post("/models", status_code=201)
async def create_model(model_input: BettingModelCreate):
    model = BettingModel(
        name=model_input.name,
        description=model_input.description,
        model_type=ModelType.CUSTOM,
        weights=model_input.weights
    )
    doc = model.model_dump()
    await db.models.insert_one(doc)
    # Return the document without MongoDB's _id field
    return {k: v for k, v in doc.items() if k != '_id'}

@api_router.get("/models/{model_id}")
async def get_model(model_id: str):
    # Check presets first
    for p in PRESET_MODELS:
        if p["id"] == model_id:
            return p
    
    # Check custom models
    model = await db.models.find_one({"id": model_id}, {"_id": 0})
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model

@api_router.delete("/models/{model_id}")
async def delete_model(model_id: str):
    # Can't delete preset models
    if model_id.startswith("preset-"):
        raise HTTPException(status_code=400, detail="Cannot delete preset models")
    
    result = await db.models.delete_one({"id": model_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Model not found")
    return {"message": "Model deleted"}

# ---- Picks (Value Finder) ----
@api_router.post("/picks/generate")
async def generate_picks(model_id: str):
    """Generate picks for all games using the specified model"""
    # Get model
    model = None
    for p in PRESET_MODELS:
        if p["id"] == model_id:
            model = p
            break
    
    if not model:
        model = await db.models.find_one({"id": model_id}, {"_id": 0})
    
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    weights = model["weights"]
    picks = []
    
    # Use API games if available, otherwise use mock games
    games_to_analyze = API_GAMES if API_GAMES else MOCK_GAMES
    teams_data = API_TEAMS if API_TEAMS else EPL_TEAMS
    
    for i, g in enumerate(games_to_analyze):
        # Calculate scores with factor breakdown
        home_score, home_breakdown = calculate_team_score(g["home"], weights, is_home=True, game_data=g)
        away_score, away_breakdown = calculate_team_score(g["away"], weights, is_home=False, game_data=g)
        
        probs = calculate_outcome_probabilities(home_score, away_score)
        
        # Convert market odds to implied probabilities
        market_probs = {
            "home": 1 / g.get("h_odds", 2.0),
            "draw": 1 / g.get("d_odds", 3.0),
            "away": 1 / g.get("a_odds", 3.0)
        }
        
        # Find best value bet
        best_outcome = max(probs.keys(), key=lambda k: probs[k] - market_probs[k])
        edge = (probs[best_outcome] - market_probs[best_outcome]) / market_probs[best_outcome] * 100
        
        market_odds = {
            "home": g.get("h_odds", 2.0),
            "draw": g.get("d_odds", 3.0),
            "away": g.get("a_odds", 3.0)
        }[best_outcome]
        confidence = calculate_confidence(probs[best_outcome], market_probs[best_outcome])
        
        # Generate pick ID based on data source
        if g.get("data_source") == "api":
            pick_id = f"pick-{model_id}-{g['id']}"
        else:
            pick_id = f"pick-{model_id}-game-{i+1}"
        
        pick = {
            "id": pick_id,
            "game_id": g.get("id", f"game-{i+1}"),
            "model_id": model_id,
            "model_name": model["name"],
            "home_team": g["home"],
            "away_team": g["away"],
            "match_date": g["date"],
            "predicted_outcome": best_outcome,
            "projected_home_score": home_score,
            "projected_away_score": away_score,
            "market_odds": market_odds,
            "confidence_score": confidence,
            "edge_percentage": round(edge, 1),
            "model_probability": round(probs[best_outcome] * 100, 1),
            "market_probability": round(market_probs[best_outcome] * 100, 1),
            "home_breakdown": home_breakdown,
            "away_breakdown": away_breakdown,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "data_source": g.get("data_source", "mock")
        }
        picks.append(pick)
    
    # Sort by confidence
    picks.sort(key=lambda x: x["confidence_score"], reverse=True)
    return picks

# ---- Journal ----
@api_router.get("/journal")
async def get_journal():
    entries = await db.journal.find({}, {"_id": 0}).to_list(100)
    return entries

@api_router.post("/journal", status_code=201)
async def create_journal_entry(entry_input: JournalEntryCreate):
    """Add a pick to the journal with stake and odds"""
    # Parse pick_id to get game info
    parts = entry_input.pick_id.split("-")
    model_id = "-".join(parts[1:-2])
    game_idx = int(parts[-1]) - 1
    
    if game_idx < 0 or game_idx >= len(MOCK_GAMES):
        raise HTTPException(status_code=400, detail="Invalid pick")
    
    game = MOCK_GAMES[game_idx]
    
    # Get model name
    model_name = "Custom Model"
    for p in PRESET_MODELS:
        if p["id"] == model_id:
            model_name = p["name"]
            break
    if model_name == "Custom Model":
        custom_model = await db.models.find_one({"id": model_id}, {"_id": 0})
        if custom_model:
            model_name = custom_model["name"]
    
    entry = JournalEntry(
        pick_id=entry_input.pick_id,
        game_id=f"game-{game_idx+1}",
        model_name=model_name,
        home_team=game["home"],
        away_team=game["away"],
        match_date=game["date"],
        predicted_outcome="home",  # Simplified - would come from pick data
        stake=entry_input.stake,
        odds_taken=entry_input.odds_taken
    )
    
    doc = entry.model_dump()
    await db.journal.insert_one(doc)
    # Return the document without MongoDB's _id field
    return {k: v for k, v in doc.items() if k != '_id'}

@api_router.patch("/journal/{entry_id}/settle")
async def settle_bet(entry_id: str, settle_request: SettleBetRequest):
    """Settle a bet with the actual result"""
    entry = await db.journal.find_one({"id": entry_id}, {"_id": 0})
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    
    if entry["status"] != "pending":
        raise HTTPException(status_code=400, detail="Bet already settled")
    
    # Calculate profit/loss
    won = entry["predicted_outcome"] == settle_request.result
    if won:
        profit_loss = entry["stake"] * (entry["odds_taken"] - 1)
        status = BetStatus.WON
    else:
        profit_loss = -entry["stake"]
        status = BetStatus.LOST
    
    update_data = {
        "status": status.value,
        "profit_loss": round(profit_loss, 2),
        "result": settle_request.result,
        "settled_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.journal.update_one({"id": entry_id}, {"$set": update_data})
    
    updated_entry = {**entry, **update_data}
    return updated_entry

@api_router.delete("/journal/{entry_id}")
async def delete_journal_entry(entry_id: str):
    result = await db.journal.delete_one({"id": entry_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    return {"message": "Entry deleted"}

# ---- Simulation ----
@api_router.post("/simulate")
async def simulate_model(sim_request: SimulationRequest):
    """Run backtesting simulation on a model against completed games"""
    # Get model
    model = None
    for p in PRESET_MODELS:
        if p["id"] == sim_request.model_id:
            model = p
            break
    
    if not model:
        model = await db.models.find_one({"id": sim_request.model_id}, {"_id": 0})
    
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    # Get completed games to simulate
    games_to_simulate = []
    if sim_request.game_ids:
        # Use specified games
        for game_id in sim_request.game_ids:
            for g in HISTORICAL_GAMES:
                if g["id"] == game_id and g.get("is_completed"):
                    games_to_simulate.append(g)
    else:
        # Use all completed historical games
        games_to_simulate = [g for g in HISTORICAL_GAMES if g.get("is_completed")]
    
    if not games_to_simulate:
        raise HTTPException(status_code=400, detail="No completed games available for simulation")
    
    weights = model["weights"]
    predictions = []
    correct = 0
    confidence_stats = {}  # Track accuracy by confidence level
    outcome_stats = {"home": {"total": 0, "correct": 0}, "draw": {"total": 0, "correct": 0}, "away": {"total": 0, "correct": 0}}
    total_stake = 0
    total_return = 0
    stake_per_bet = 10  # $10 per bet
    
    for g in games_to_simulate:
        # Calculate scores
        home_score, home_breakdown = calculate_team_score(g["home"], weights, is_home=True, game_data=g)
        away_score, away_breakdown = calculate_team_score(g["away"], weights, is_home=False, game_data=g)
        
        probs = calculate_outcome_probabilities(home_score, away_score)
        
        # Market probabilities
        market_probs = {
            "home": 1 / g["h_odds"],
            "draw": 1 / g["d_odds"],
            "away": 1 / g["a_odds"]
        }
        
        # Find best value bet
        best_outcome = max(probs.keys(), key=lambda k: probs[k] - market_probs[k])
        edge = (probs[best_outcome] - market_probs[best_outcome]) / market_probs[best_outcome] * 100
        
        market_odds = {"home": g["h_odds"], "draw": g["d_odds"], "away": g["a_odds"]}[best_outcome]
        confidence = calculate_confidence(probs[best_outcome], market_probs[best_outcome])
        
        # Apply confidence filter if specified
        if sim_request.min_confidence and confidence < sim_request.min_confidence:
            continue
        
        # Check if prediction was correct
        actual_result = g.get("result")
        is_correct = (best_outcome == actual_result)
        
        if is_correct:
            correct += 1
        
        # Update confidence stats
        if confidence not in confidence_stats:
            confidence_stats[confidence] = {"total": 0, "correct": 0}
        confidence_stats[confidence]["total"] += 1
        if is_correct:
            confidence_stats[confidence]["correct"] += 1
        
        # Update outcome stats
        outcome_stats[best_outcome]["total"] += 1
        if is_correct:
            outcome_stats[best_outcome]["correct"] += 1
        
        # Calculate ROI
        total_stake += stake_per_bet
        if is_correct:
            total_return += stake_per_bet * market_odds
        
        predictions.append({
            "game_id": g["id"],
            "home_team": g["home"],
            "away_team": g["away"],
            "match_date": g["date"],
            "predicted_outcome": best_outcome,
            "actual_result": actual_result,
            "correct": is_correct,
            "confidence": confidence,
            "odds": market_odds,
            "home_score_actual": g.get("home_score"),
            "away_score_actual": g.get("away_score")
        })
    
    total_predictions = len(predictions)
    if total_predictions == 0:
        raise HTTPException(status_code=400, detail="No predictions generated (possibly due to confidence filter)")
    
    accuracy = (correct / total_predictions) * 100
    net_profit = total_return - total_stake
    roi = (net_profit / total_stake) * 100 if total_stake > 0 else 0
    avg_odds = total_return / correct if correct > 0 else 0
    
    # Format confidence breakdown
    confidence_breakdown = {}
    for conf_level, stats in confidence_stats.items():
        acc = (stats["correct"] / stats["total"]) * 100 if stats["total"] > 0 else 0
        confidence_breakdown[str(conf_level)] = {
            "total": stats["total"],
            "correct": stats["correct"],
            "accuracy": round(acc, 1)
        }
    
    # Format outcome breakdown
    outcome_breakdown = {}
    for outcome, stats in outcome_stats.items():
        acc = (stats["correct"] / stats["total"]) * 100 if stats["total"] > 0 else 0
        outcome_breakdown[outcome] = {
            "total": stats["total"],
            "correct": stats["correct"],
            "accuracy": round(acc, 1)
        }
    
    return {
        "model_id": sim_request.model_id,
        "model_name": model["name"],
        "total_games": total_predictions,
        "correct_predictions": correct,
        "accuracy_percentage": round(accuracy, 2),
        "confidence_breakdown": confidence_breakdown,
        "outcome_breakdown": outcome_breakdown,
        "simulated_roi": round(roi, 2),
        "average_odds": round(avg_odds, 2),
        "total_stake": total_stake,
        "total_return": round(total_return, 2),
        "net_profit": round(net_profit, 2),
        "predictions": predictions
    }

# ---- Stats ----
@api_router.get("/stats")
async def get_stats():
    """Get overall betting statistics"""
    entries = await db.journal.find({}, {"_id": 0}).to_list(1000)
    
    total_bets = len(entries)
    pending_bets = len([e for e in entries if e.get("status") == "pending"])
    won_bets = len([e for e in entries if e.get("status") == "won"])
    lost_bets = len([e for e in entries if e.get("status") == "lost"])
    
    total_staked = sum(e.get("stake", 0) for e in entries if e.get("status") != "pending")
    total_profit = sum(e.get("profit_loss", 0) for e in entries)
    
    win_rate = (won_bets / (won_bets + lost_bets) * 100) if (won_bets + lost_bets) > 0 else 0
    roi = (total_profit / total_staked * 100) if total_staked > 0 else 0
    
    return {
        "total_bets": total_bets,
        "pending_bets": pending_bets,
        "won_bets": won_bets,
        "lost_bets": lost_bets,
        "win_rate": round(win_rate, 1),
        "total_staked": round(total_staked, 2),
        "total_profit": round(total_profit, 2),
        "roi": round(roi, 1)
    }

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

@app.on_event("startup")
async def startup_fetch_api_data():
    """Fetch data from API on server startup"""
    logger.info("Fetching initial data from Football API...")
    success = await fetch_epl_fixtures_from_api()
    if success:
        logger.info(f"Successfully loaded {len(API_GAMES)} games from API")
    else:
        logger.warning("Failed to load API data, mock data will be used as fallback")
