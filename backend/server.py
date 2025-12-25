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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
class ModelWeights(BaseModel):
    model_config = ConfigDict(extra="allow")
    
    def __init__(self, **data):
        validated_data = {}
        for key, value in data.items():
            if isinstance(value, (int, float)):
                validated_data[key] = max(0.0, min(100.0, float(value)))
            else:
                validated_data[key] = 0.0
        super().__init__(**validated_data)
    
    def dict(self, **kwargs):
        return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}
    
    def model_dump(self, **kwargs):
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
    goals_for: int = 0
    goals_against: int = 0

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
    result: Optional[str] = None
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    is_completed: bool = False
    data_source: str = "api"
    api_id: Optional[int] = None

class Pick(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    game_id: str
    model_id: str
    model_name: str
    home_team: str
    away_team: str
    match_date: str
    predicted_outcome: str
    projected_home_score: float
    projected_away_score: float
    market_odds: float
    confidence_score: int
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
    result: str

class SimulationRequest(BaseModel):
    model_id: str
    game_ids: Optional[List[str]] = None
    min_confidence: Optional[int] = None

class SimulationResult(BaseModel):
    model_id: str
    model_name: str
    total_games: int
    correct_predictions: int
    accuracy_percentage: float
    confidence_breakdown: dict
    outcome_breakdown: dict
    simulated_roi: float
    average_odds: float
    total_stake: float
    total_return: float

# ============ GLOBAL DATA STORAGE ============
API_GAMES = []
API_TEAMS = {}
HISTORICAL_GAMES = []

# ============ FOOTBALL-DATA.ORG API INTEGRATION ============
FOOTBALL_API_KEY = os.environ.get('FOOTBALL_API_KEY', '')
FOOTBALL_API_URL = "https://api.football-data.org/v4"

def calculate_period_stats(team_matches, period=None):
    """
    Calculate stats for a specific period (last N matches)
    Args:
        team_matches: List of matches for a team (most recent last)
        period: Number of matches to consider (None = all matches)
    Returns:
        Dictionary with goals_for, goals_against, wins, draws, losses, matches
    """
    if period:
        team_matches = team_matches[-period:]  # Get last N matches
    
    stats = {
        "goals_for": 0,
        "goals_against": 0,
        "wins": 0,
        "draws": 0,
        "losses": 0,
        "matches": len(team_matches)
    }
    
    for match in team_matches:
        stats["goals_for"] += match["goals_scored"]
        stats["goals_against"] += match["goals_conceded"]
        
        if match["result"] == "win":
            stats["wins"] += 1
        elif match["result"] == "draw":
            stats["draws"] += 1
        else:
            stats["losses"] += 1
    
    # Calculate averages and percentages
    if stats["matches"] > 0:
        stats["avg_goals_for"] = round(stats["goals_for"] / stats["matches"], 2)
        stats["avg_goals_against"] = round(stats["goals_against"] / stats["matches"], 2)
        stats["win_rate"] = round((stats["wins"] / stats["matches"]) * 100, 1)
        stats["goal_difference"] = stats["goals_for"] - stats["goals_against"]
    else:
        stats["avg_goals_for"] = 0
        stats["avg_goals_against"] = 0
        stats["win_rate"] = 0
        stats["goal_difference"] = 0
    
    return stats

def get_team_match_history(team_name, matches):
    """
    Extract all matches for a specific team from match list
    Returns list of matches with normalized data (most recent last)
    """
    team_matches = []
    
    for match in matches:
        if not match.get("is_completed") or match.get("home_score") is None:
            continue
            
        home_team = match["home"]
        away_team = match["away"]
        home_score = match["home_score"]
        away_score = match["away_score"]
        
        if home_team == team_name:
            # Team played at home
            if home_score > away_score:
                result = "win"
            elif home_score < away_score:
                result = "loss"
            else:
                result = "draw"
            
            team_matches.append({
                "date": match.get("date"),
                "opponent": away_team,
                "home_away": "home",
                "goals_scored": home_score,
                "goals_conceded": away_score,
                "result": result,
                "match_data": match
            })
        elif away_team == team_name:
            # Team played away
            if away_score > home_score:
                result = "win"
            elif away_score < home_score:
                result = "loss"
            else:
                result = "draw"
            
            team_matches.append({
                "date": match.get("date"),
                "opponent": home_team,
                "home_away": "away",
                "goals_scored": away_score,
                "goals_conceded": home_score,
                "result": result,
                "match_data": match
            })
    
    return team_matches

def calculate_team_stats_from_matches(matches):
    """Calculate team statistics from actual match history - NO RANDOM DATA"""
    logger.info(f"📊 Calculating team stats from {len(matches)} completed matches")
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
    
    # Convert to ratings (0-100 scale) based on ACTUAL performance
    teams = {}
    for team_name, stats in team_stats.items():
        if stats["matches"] > 0:
            # Offense rating based on actual goals scored per match
            avg_goals_scored = stats["goals_scored"] / stats["matches"]
            offense = min(95, max(50, 50 + (avg_goals_scored * 15)))
            
            # Defense rating based on actual goals conceded per match
            avg_goals_conceded = stats["goals_conceded"] / stats["matches"]
            defense = min(95, max(50, 95 - (avg_goals_conceded * 15)))
            
            # Form rating based on actual win percentage
            win_rate = stats["wins"] / stats["matches"]
            form = min(95, max(40, 40 + (win_rate * 55)))
            
            teams[team_name] = {
                "short": team_name[:3].upper(),
                "offense": round(offense, 1),
                "defense": round(defense, 1),
                "form": round(form, 1),
                "goals_for": stats["goals_scored"],
                "goals_against": stats["goals_conceded"],
                "matches_played": stats["matches"],
                "wins": stats["wins"],
                "draws": stats["draws"],
                "losses": stats["losses"],
                "stats": stats
            }
            
            logger.info(f"  ⚽ {team_name}: {stats['goals_scored']} GF, {stats['goals_conceded']} GA, "
                       f"OFF:{offense:.1f}, DEF:{defense:.1f}, FORM:{form:.1f}")
        else:
            # Default values for teams with no completed matches yet
            teams[team_name] = {
                "short": team_name[:3].upper(),
                "offense": 70.0,
                "defense": 70.0,
                "form": 70.0,
                "goals_for": 0,
                "goals_against": 0,
                "matches_played": 0,
                "wins": 0,
                "draws": 0,
                "losses": 0
            }
    
    return teams

def calculate_odds_from_stats(home_stats: dict, away_stats: dict) -> tuple:
    """Calculate odds based purely on team statistics - NO RANDOMNESS"""
    # Calculate team strength from actual stats
    home_strength = (home_stats["offense"] + home_stats["defense"] + home_stats["form"]) / 3
    away_strength = (away_stats["offense"] + away_stats["defense"] + away_stats["form"]) / 3
    
    # Home advantage (fixed 5 points)
    home_strength += 5
    
    # Calculate win probabilities based on strength difference
    diff = home_strength - away_strength
    
    # Convert strength difference to probabilities
    if diff > 20:
        home_prob = 0.65
        draw_prob = 0.20
    elif diff > 10:
        home_prob = 0.55
        draw_prob = 0.25
    elif diff > 0:
        home_prob = 0.45
        draw_prob = 0.30
    elif diff > -10:
        home_prob = 0.35
        draw_prob = 0.30
    elif diff > -20:
        home_prob = 0.25
        draw_prob = 0.25
    else:
        home_prob = 0.20
        draw_prob = 0.20
    
    away_prob = 1 - home_prob - draw_prob
    
    # Convert to decimal odds with 5% bookmaker margin (fixed)
    margin = 1.05
    h_odds = round(margin / home_prob, 2)
    d_odds = round(margin / draw_prob, 2)
    a_odds = round(margin / away_prob, 2)
    
    logger.info(f"    📈 Odds calculated - Home: {h_odds}, Draw: {d_odds}, Away: {a_odds}")
    
    return h_odds, d_odds, a_odds

async def fetch_epl_fixtures_from_api():
    """Fetch real EPL fixtures from football-data.org API"""
    global API_GAMES, API_TEAMS, HISTORICAL_GAMES
    
    if not FOOTBALL_API_KEY:
        logger.error("❌ No Football API key found in environment")
        return False
    
    try:
        import httpx
        headers = {"X-Auth-Token": FOOTBALL_API_KEY}
        
        logger.info("🌐 Making API call to Football-Data.org...")
        logger.info(f"   URL: {FOOTBALL_API_URL}/competitions/PL/matches")
        logger.info(f"   Headers: X-Auth-Token: {FOOTBALL_API_KEY[:10]}...")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{FOOTBALL_API_URL}/competitions/PL/matches",
                headers=headers,
                params={"status": "SCHEDULED,TIMED,IN_PLAY,PAUSED,FINISHED"},
                timeout=15.0
            )
            
            logger.info(f"📡 API Response Status: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"❌ Football API error: {response.status_code}")
                logger.error(f"   Response: {response.text[:500]}")
                return False
            
            data = response.json()
            matches = data.get("matches", [])
            
            logger.info(f"✅ API Response received: {len(matches)} total matches")
            
            if not matches:
                logger.warning("⚠️ No matches returned from API")
                return False
            
            # Separate finished and upcoming matches
            finished_matches = []
            upcoming_matches = []
            
            for match in matches:
                home_team = match["homeTeam"]["name"]
                away_team = match["awayTeam"]["name"]
                match_date_raw = match["utcDate"]
                status = match["status"]
                
                # Format datetime
                from datetime import datetime as dt
                try:
                    match_dt = dt.fromisoformat(match_date_raw.replace('Z', '+00:00'))
                    match_date = match_dt.strftime('%a, %b %d, %Y at %I:%M %p')
                except:
                    match_date = match_date_raw
                
                game = {
                    "id": f"api-{match['id']}",
                    "home": home_team,
                    "away": away_team,
                    "date": match_date,
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
                        logger.info(f"  🏁 Finished: {home_team} {home_score}-{away_score} {away_team}")
                else:
                    upcoming_matches.append(game)
                    logger.info(f"  📅 Upcoming: {home_team} vs {away_team} on {match_date}")
            
            logger.info(f"📊 Processed: {len(finished_matches)} finished, {len(upcoming_matches)} upcoming")
            
            # Calculate team stats from finished matches ONLY
            API_TEAMS = calculate_team_stats_from_matches(finished_matches)
            logger.info(f"✅ Calculated stats for {len(API_TEAMS)} teams from real match data")
            
            # Generate odds for upcoming matches based on real stats
            for game in upcoming_matches:
                home_team = game["home"]
                away_team = game["away"]
                
                home_stats = API_TEAMS.get(home_team, {"offense": 70, "defense": 70, "form": 70})
                away_stats = API_TEAMS.get(away_team, {"offense": 70, "defense": 70, "form": 70})
                
                h_odds, d_odds, a_odds = calculate_odds_from_stats(home_stats, away_stats)
                game["h_odds"] = h_odds
                game["d_odds"] = d_odds
                game["a_odds"] = a_odds
            
            # Also add odds to finished matches for historical analysis
            for game in finished_matches:
                home_team = game["home"]
                away_team = game["away"]
                home_stats = API_TEAMS.get(home_team, {"offense": 70, "defense": 70, "form": 70})
                away_stats = API_TEAMS.get(away_team, {"offense": 70, "defense": 70, "form": 70})
                h_odds, d_odds, a_odds = calculate_odds_from_stats(home_stats, away_stats)
                game["h_odds"] = h_odds
                game["d_odds"] = d_odds
                game["a_odds"] = a_odds
            
            # Store data
            API_GAMES = upcoming_matches[:15]
            HISTORICAL_GAMES = finished_matches[-30:]
            
            logger.info(f"✅ Updated API_GAMES with {len(API_GAMES)} upcoming matches")
            logger.info(f"✅ Updated HISTORICAL_GAMES with {len(HISTORICAL_GAMES)} completed matches")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Error fetching from Football API: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

PRESET_MODELS = [
    {
        "id": "preset-balanced",
        "name": "Balanced Pro",
        "description": "Equal weighting across all factors - great for beginners",
        "model_type": "preset",
        "weights": {
            "team_offense": 15, "team_defense": 15, "recent_form": 15, 
            "home_advantage": 15, "head_to_head": 10, "goals_differential": 15,
            "win_rate": 15,
            # Period settings
            "form_period": 10, "goals_period": 10, "win_rate_period": 10
        },
    },
    {
        "id": "preset-form-focused",
        "name": "Form Hunter",
        "description": "Emphasizes recent form and momentum",
        "model_type": "preset",
        "weights": {
            "team_offense": 10, "team_defense": 10, "recent_form": 30, 
            "home_advantage": 15, "head_to_head": 10, "goals_differential": 10,
            "win_rate": 15,
            # Period settings - shorter periods for form-focused
            "form_period": 5, "goals_period": 5, "win_rate_period": 5
        },
    },
    {
        "id": "preset-stats-heavy",
        "name": "Stats Machine",
        "description": "Heavy focus on offensive, defensive, and goal metrics",
        "model_type": "preset",
        "weights": {
            "team_offense": 25, "team_defense": 25, "recent_form": 10, 
            "home_advantage": 10, "head_to_head": 5, "goals_differential": 15,
            "win_rate": 10,
            # Period settings - longer periods for statistical depth
            "form_period": 15, "goals_period": 15, "win_rate_period": 15
        },
    },
]

# ============ HELPER FUNCTIONS ============
def get_period_based_stats(team_name: str, periods: dict) -> dict:
    """
    Get period-based statistics for a team
    Args:
        team_name: Name of the team
        periods: Dict with form_period, goals_period, win_rate_period
    Returns:
        Dict with period-specific stats
    """
    team_matches = get_team_match_history(team_name, HISTORICAL_GAMES)
    
    if not team_matches:
        return {
            "form_stats": {"win_rate": 50, "matches": 0},
            "goals_stats": {"avg_goals_for": 1.5, "avg_goals_against": 1.5, "matches": 0},
            "win_rate_stats": {"win_rate": 50, "matches": 0}
        }
    
    # Get form period stats
    form_period = periods.get("form_period", 10)
    form_stats = calculate_period_stats(team_matches, form_period)
    
    # Get goals period stats
    goals_period = periods.get("goals_period", 10)
    goals_stats = calculate_period_stats(team_matches, goals_period)
    
    # Get win rate period stats
    win_rate_period = periods.get("win_rate_period", 10)
    win_rate_stats = calculate_period_stats(team_matches, win_rate_period)
    
    return {
        "form_stats": {
            "win_rate": form_stats["win_rate"],
            "matches": form_stats["matches"],
            "period": form_period
        },
        "goals_stats": {
            "avg_goals_for": goals_stats["avg_goals_for"],
            "avg_goals_against": goals_stats["avg_goals_against"],
            "goal_difference": goals_stats["goal_difference"],
            "matches": goals_stats["matches"],
            "period": goals_period
        },
        "win_rate_stats": {
            "win_rate": win_rate_stats["win_rate"],
            "matches": win_rate_stats["matches"],
            "period": win_rate_period
        }
    }

def calculate_team_score(team_name: str, weights: dict, is_home: bool, game_data: dict = None) -> tuple:
    """Calculate projected score based on REAL team data with period-based customization"""
    team = API_TEAMS.get(team_name)
    if not team:
        logger.warning(f"⚠️ Team {team_name} not found in API_TEAMS")
        return 1.5, {}
    
    if game_data is None:
        game_data = {}
    
    # Get period-based stats
    periods = {
        "form_period": weights.get("form_period", 10),
        "goals_period": weights.get("goals_period", 10),
        "win_rate_period": weights.get("win_rate_period", 10)
    }
    period_stats = get_period_based_stats(team_name, periods)
    
    # Normalize weights (exclude period settings from weight calculation)
    weight_keys = [k for k in weights.keys() if not k.endswith('_period')]
    total_weight = sum(weights.get(k, 0) for k in weight_keys)
    if total_weight == 0:
        return 1.5, {}
    
    norm_weights = {k: weights.get(k, 0) / total_weight for k in weight_keys}
    
    # Base score starts at 1.5 (average EPL goals per team per match)
    BASE_SCORE = 1.5
    breakdown = {}
    total_contribution = 0
    
    # 1. OFFENSE - Primary attacking factor (using goals period)
    goals_for = period_stats["goals_stats"]["avg_goals_for"]
    offense_value = min(0.95, max(0.50, 0.50 + (goals_for / 3.0 * 0.45)))
    offense_contrib = (offense_value - 0.5) * norm_weights.get("team_offense", 0) * 2.0
    breakdown["team_offense"] = {
        "raw_value": round(offense_value * 100, 1),
        "normalized": offense_value,
        "weight": norm_weights.get("team_offense", 0) * 100,
        "contribution": offense_contrib,
        "description": f"Offensive rating from last {period_stats['goals_stats']['period']} matches: {goals_for:.2f} goals/match. Higher offense = more goals."
    }
    total_contribution += offense_contrib
    
    # 2. DEFENSE - Affects opponent's scoring but also team confidence (using goals period)
    goals_against = period_stats["goals_stats"]["avg_goals_against"]
    defense_value = min(0.95, max(0.50, 0.95 - (goals_against / 3.0 * 0.45)))
    defense_contrib = (defense_value - 0.5) * norm_weights.get("team_defense", 0) * 0.8
    breakdown["team_defense"] = {
        "raw_value": round(defense_value * 100, 1),
        "normalized": defense_value,
        "weight": norm_weights.get("team_defense", 0) * 100,
        "contribution": defense_contrib,
        "description": f"Defensive rating from last {period_stats['goals_stats']['period']} matches: {goals_against:.2f} goals conceded/match. Strong defense improves team confidence."
    }
    total_contribution += defense_contrib
    
    # 3. RECENT FORM - Current momentum and confidence (using form period)
    form_win_rate = period_stats["form_stats"]["win_rate"]
    form_value = min(0.95, max(0.40, 0.40 + (form_win_rate / 100 * 0.55)))
    form_contrib = (form_value - 0.5) * norm_weights.get("recent_form", 0) * 1.5
    breakdown["recent_form"] = {
        "raw_value": round(form_value * 100, 1),
        "normalized": form_value,
        "weight": norm_weights.get("recent_form", 0) * 100,
        "contribution": form_contrib,
        "description": f"Form rating from last {period_stats['form_stats']['period']} matches: {form_win_rate:.1f}% win rate. Good form = better performance."
    }
    total_contribution += form_contrib
    
    # 4. INJURIES - Squad availability (simulated based on form)
    # In real app, would come from injury API. Here we derive from form variance
    injury_impact = 0.75 + (form_value * 0.25)  # 75-100% squad availability
    injury_contrib = (injury_impact - 0.875) * norm_weights.get("injuries", 0) * 2.0
    breakdown["injuries"] = {
        "raw_value": injury_impact * 100,
        "normalized": injury_impact,
        "weight": norm_weights.get("injuries", 0) * 100,
        "contribution": injury_contrib,
        "description": f"Squad availability ~{injury_impact*100:.0f}%. Injuries reduce attacking options and defensive stability."
    }
    total_contribution += injury_contrib
    
    # 5. HOME ADVANTAGE - Significant factor in football
    if is_home:
        home_advantage_value = 0.85  # 85% advantage
        home_bonus = 0.35 * norm_weights.get("home_advantage", 0)
        description = "Playing at home (+35% boost): crowd support, familiar pitch, no travel fatigue"
    else:
        home_advantage_value = 0.15  # 15% (away disadvantage)
        home_bonus = -0.25 * norm_weights.get("home_advantage", 0)
        description = "Playing away (-25% penalty): hostile crowd, travel fatigue, unfamiliar conditions"
    
    breakdown["home_advantage"] = {
        "raw_value": home_advantage_value * 100,
        "normalized": home_advantage_value,
        "weight": norm_weights.get("home_advantage", 0) * 100,
        "contribution": home_bonus,
        "description": description
    }
    total_contribution += home_bonus
    
    # 6. HEAD-TO-HEAD - Historical matchup record (neutral without API data)
    h2h_value = 0.5  # Neutral
    h2h_contrib = (h2h_value - 0.5) * norm_weights.get("head_to_head", 0) * 1.0
    breakdown["head_to_head"] = {
        "raw_value": 50,
        "normalized": h2h_value,
        "weight": norm_weights.get("head_to_head", 0) * 100,
        "contribution": h2h_contrib,
        "description": "Head-to-head record (neutral 50% - historical data not available from API)"
    }
    total_contribution += h2h_contrib
    
    # 7. REST DAYS - Recovery time between matches (simulated)
    # Derive from matches played - more matches = potentially less rest
    matches = team.get("matches_played", 10)
    rest_quality = max(0.5, min(1.0, 1.0 - (matches / 100)))  # Teams with more matches slightly more fatigued
    rest_contrib = (rest_quality - 0.75) * norm_weights.get("rest_days", 0) * 1.2
    breakdown["rest_days"] = {
        "raw_value": rest_quality * 100,
        "normalized": rest_quality,
        "weight": norm_weights.get("rest_days", 0) * 100,
        "contribution": rest_contrib,
        "description": f"Rest quality ~{rest_quality*100:.0f}%. Adequate rest improves physical performance and reduces injury risk."
    }
    total_contribution += rest_contrib
    
    # 8. TRAVEL DISTANCE - Affects away teams more (simulated)
    if is_home:
        travel_impact = 0.95  # Minimal travel
        travel_contrib = 0.05 * norm_weights.get("travel_distance", 0)
        description = "Home team - minimal travel (95% fitness retained)"
    else:
        # Simulate travel distance based on team strength (stronger teams manage travel better)
        travel_quality = 0.65 + (offense_value * 0.2)  # 65-85% range
        travel_impact = travel_quality
        travel_contrib = (travel_quality - 0.85) * norm_weights.get("travel_distance", 0) * 1.5
        description = f"Away travel impact ~{travel_quality*100:.0f}%. Long travel increases fatigue and disrupts routine."
    
    breakdown["travel_distance"] = {
        "raw_value": travel_impact * 100,
        "normalized": travel_impact,
        "weight": norm_weights.get("travel_distance", 0) * 100,
        "contribution": travel_contrib,
        "description": description
    }
    total_contribution += travel_contrib
    
    # 9. REFEREE INFLUENCE - Officiating style (simulated neutral)
    referee_value = 0.5  # Neutral referee
    referee_contrib = (referee_value - 0.5) * norm_weights.get("referee_influence", 0) * 0.8
    breakdown["referee_influence"] = {
        "raw_value": 50,
        "normalized": referee_value,
        "weight": norm_weights.get("referee_influence", 0) * 100,
        "contribution": referee_contrib,
        "description": "Referee style (neutral 50% - varies by official: strict vs lenient, home bias, etc.)"
    }
    total_contribution += referee_contrib
    
    # 10. WEATHER CONDITIONS - Match day weather (simulated neutral)
    weather_value = 0.5  # Neutral weather
    weather_contrib = (weather_value - 0.5) * norm_weights.get("weather_conditions", 0) * 0.6
    breakdown["weather_conditions"] = {
        "raw_value": 50,
        "normalized": weather_value,
        "weight": norm_weights.get("weather_conditions", 0) * 100,
        "contribution": weather_contrib,
        "description": "Weather conditions (neutral 50% - rain/wind favor defensive teams, good weather favors technical teams)"
    }
    total_contribution += weather_contrib
    
    # 11. MOTIVATION LEVEL - Based on team position and form
    wins = team.get("wins", 0)
    losses = team.get("losses", 0)
    total_matches = team.get("matches_played", 1)
    
    # Teams with more wins are more motivated, losing teams less so
    if total_matches > 0:
        win_loss_ratio = wins / max(1, wins + losses)
        motivation_value = 0.4 + (win_loss_ratio * 0.6)  # 40-100% range
    else:
        motivation_value = 0.7  # Default mid-high
    
    motivation_contrib = (motivation_value - 0.7) * norm_weights.get("motivation_level", 0) * 1.0
    breakdown["motivation_level"] = {
        "raw_value": motivation_value * 100,
        "normalized": motivation_value,
        "weight": norm_weights.get("motivation_level", 0) * 100,
        "contribution": motivation_contrib,
        "description": f"Motivation ~{motivation_value*100:.0f}% based on season performance. Winning teams maintain high motivation."
    }
    total_contribution += motivation_contrib
    
    # 12. GOALS DIFFERENTIAL - Overall team quality indicator (using goals period)
    goals_diff = period_stats["goals_stats"]["goal_difference"]
    goals_diff_normalized = min(max(goals_diff / 15, -1), 1)  # Normalize to -1 to 1
    goals_diff_contrib = goals_diff_normalized * norm_weights.get("goals_differential", 0) * 0.6
    breakdown["goals_differential"] = {
        "raw_value": goals_diff,
        "normalized": goals_diff_normalized,
        "weight": norm_weights.get("goals_differential", 0) * 100,
        "contribution": goals_diff_contrib,
        "description": f"Goal difference from last {period_stats['goals_stats']['period']} matches: {goals_diff:+.1f}. Strong indicator of team quality."
    }
    total_contribution += goals_diff_contrib
    
    # 13. WIN RATE - Historical success rate (using win_rate period)
    win_rate_value = period_stats["win_rate_stats"]["win_rate"] / 100
    win_rate_contrib = (win_rate_value - 0.4) * norm_weights.get("win_rate", 0) * 1.2
    breakdown["win_rate"] = {
        "raw_value": period_stats["win_rate_stats"]["win_rate"],
        "normalized": win_rate_value,
        "weight": norm_weights.get("win_rate", 0) * 100,
        "contribution": win_rate_contrib,
        "description": f"Win rate from last {period_stats['win_rate_stats']['period']} matches: {period_stats['win_rate_stats']['win_rate']:.1f}%. Historical success breeds confidence."
    }
    total_contribution += win_rate_contrib
    
    # Calculate final score: base + weighted contributions
    score = BASE_SCORE + total_contribution
    
    # Clamp to realistic range (0.3 to 4.0 goals)
    score = round(max(0.3, min(4.0, score)), 2)
    
    return score, breakdown

def calculate_confidence(model_prob: float, market_prob: float, home_score: float, away_score: float) -> tuple:
    """
    Calculate confidence score 1-10 based on multiple factors
    Returns: (confidence_score, confidence_explanation)
    """
    # 1. Edge percentage (primary factor)
    edge = (model_prob - market_prob) / market_prob * 100
    
    # Base confidence from edge
    if edge <= -20:
        edge_conf = 1
    elif edge <= -10:
        edge_conf = 2
    elif edge <= -5:
        edge_conf = 3
    elif edge <= 0:
        edge_conf = 4
    elif edge < 5:
        edge_conf = 5
    elif edge < 10:
        edge_conf = 6
    elif edge < 15:
        edge_conf = 7
    elif edge < 20:
        edge_conf = 8
    elif edge < 30:
        edge_conf = 9
    else:
        edge_conf = 10
    
    # 2. Model probability strength (higher probability = more confident)
    if model_prob >= 0.60:
        prob_bonus = 1.0
    elif model_prob >= 0.50:
        prob_bonus = 0.5
    elif model_prob >= 0.40:
        prob_bonus = 0.0
    else:
        prob_bonus = -0.5
    
    # 3. Score differential clarity (clear winner vs tight match)
    score_diff = abs(home_score - away_score)
    if score_diff >= 1.5:
        clarity_bonus = 1.0
    elif score_diff >= 1.0:
        clarity_bonus = 0.5
    elif score_diff >= 0.5:
        clarity_bonus = 0.0
    else:
        clarity_bonus = -0.5
    
    # Combine factors
    final_confidence = edge_conf + prob_bonus + clarity_bonus
    final_confidence = max(1, min(10, int(round(final_confidence))))
    
    # Generate explanation
    if final_confidence >= 8:
        strength = "Very Strong"
        reasoning = f"Significant edge ({edge:+.1f}%), high model probability ({model_prob*100:.1f}%), and clear score projection."
    elif final_confidence >= 6:
        strength = "Strong"
        reasoning = f"Good edge ({edge:+.1f}%) with solid model probability ({model_prob*100:.1f}%)."
    elif final_confidence >= 4:
        strength = "Moderate"
        reasoning = f"Modest edge ({edge:+.1f}%). Consider stake sizing carefully."
    else:
        strength = "Weak"
        reasoning = f"Low edge ({edge:+.1f}%). Market may be efficiently priced here."
    
    explanation = {
        "strength": strength,
        "reasoning": reasoning,
        "edge": round(edge, 2),
        "model_probability": round(model_prob * 100, 1),
        "market_probability": round(market_prob * 100, 1),
        "score_differential": round(score_diff, 2)
    }
    
    return final_confidence, explanation

def calculate_outcome_probabilities(home_score: float, away_score: float) -> dict:
    """
    Convert projected scores to outcome probabilities.
    Dynamic draw probability - increases when teams are more evenly matched.
    """
    diff = home_score - away_score
    
    if diff > 0.8:
        # Clear home advantage
        home_prob = 0.55 + min(diff * 0.1, 0.3)
        draw_prob = 0.25 - min(diff * 0.05, 0.15)
        away_prob = 1 - home_prob - draw_prob
    elif diff < -0.8:
        # Clear away advantage
        away_prob = 0.55 + min(abs(diff) * 0.1, 0.3)
        draw_prob = 0.25 - min(abs(diff) * 0.05, 0.15)
        home_prob = 1 - away_prob - draw_prob
    else:
        # Close match - dynamic draw probability based on how evenly matched
        # Draw probability: 40% when perfectly even (diff=0), declining to 25% at diff=0.8
        evenness_factor = 1 - min(abs(diff), 0.8) / 0.8  # 1.0 when diff=0, 0.0 when diff=0.8
        draw_prob = 0.25 + (0.15 * evenness_factor)
        
        # Split remaining probability between home and away based on score difference
        remaining = 1 - draw_prob
        if diff >= 0:
            home_prob = remaining * (0.5 + diff * 0.1)
            away_prob = remaining - home_prob
        else:
            away_prob = remaining * (0.5 + abs(diff) * 0.1)
            home_prob = remaining - away_prob
    
    return {
        "home": round(max(0.05, min(0.85, home_prob)), 3),
        "draw": round(max(0.10, min(0.40, draw_prob)), 3),
        "away": round(max(0.05, min(0.85, away_prob)), 3)
    }

# ============ API ROUTES ============

@api_router.get("/")
async def root():
    return {
        "message": "BetGenius EPL API - Real Data Only",
        "version": "2.0.0",
        "data_source": "api",
        "games_loaded": len(API_GAMES),
        "teams_loaded": len(API_TEAMS),
        "historical_games": len(HISTORICAL_GAMES)
    }

@api_router.get("/teams")
async def get_teams():
    """Get all teams with stats calculated from real API data"""
    teams = []
    
    for name, data in API_TEAMS.items():
        teams.append({
            "name": name,
            "short_name": data.get("short", name[:3].upper()),
            "offense_rating": data.get("offense", 70),
            "defense_rating": data.get("defense", 70),
            "form_rating": data.get("form", 70),
            "goals_for": data.get("goals_for", 0),
            "goals_against": data.get("goals_against", 0)
        })
    
    logger.info(f"📤 Returning {len(teams)} teams")
    return teams

@api_router.get("/teams/{team_name}")
async def get_team_details(team_name: str):
    """Get detailed information about a specific team from real data with period-based stats"""
    team_data = API_TEAMS.get(team_name)
    if not team_data:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Get all match history for this team
    all_team_matches = get_team_match_history(team_name, HISTORICAL_GAMES)
    
    # Calculate stats for different periods
    period_stats = {}
    for period in [5, 10, 15, None]:  # None = all matches
        period_label = f"last_{period}" if period else "overall"
        period_stats[period_label] = calculate_period_stats(all_team_matches, period)
    
    # Get recent matches for display (last 10)
    recent_matches = []
    for match_data in all_team_matches[-10:]:
        recent_matches.append({
            "date": match_data["date"],
            "opponent": match_data["opponent"],
            "home_away": match_data["home_away"].capitalize(),
            "score": f"{match_data['goals_scored']}-{match_data['goals_conceded']}",
            "result": match_data["result"],
            "goals_scored": match_data["goals_scored"],
            "goals_conceded": match_data["goals_conceded"]
        })
    
    # Get upcoming fixtures
    upcoming_fixtures = []
    for game in API_GAMES[:10]:
        if game.get("home") == team_name or game.get("away") == team_name:
            is_home = game.get("home") == team_name
            opponent = game.get("away") if is_home else game.get("home")
            
            upcoming_fixtures.append({
                "date": game.get("date"),
                "opponent": opponent,
                "home_away": "Home" if is_home else "Away",
                "home_odds": game.get("h_odds"),
                "draw_odds": game.get("d_odds"),
                "away_odds": game.get("a_odds"),
                "home_team": game.get("home"),
                "away_team": game.get("away")
            })
    
    total_matches = team_data.get("matches_played", 0)
    wins = team_data.get("wins", 0)
    draws = team_data.get("draws", 0)
    losses = team_data.get("losses", 0)
    goals_scored = team_data.get("goals_for", 0)
    goals_conceded = team_data.get("goals_against", 0)
    
    win_rate = (wins / total_matches * 100) if total_matches > 0 else 0
    avg_goals_scored = goals_scored / total_matches if total_matches > 0 else 0
    avg_goals_conceded = goals_conceded / total_matches if total_matches > 0 else 0
    
    logger.info(f"📤 Returning details for {team_name} with period-based stats")
    
    return {
        "name": team_name,
        "short_name": team_data.get("short", team_name[:3].upper()),
        "ratings": {
            "offense": team_data.get("offense", 70),
            "defense": team_data.get("defense", 70),
            "form": team_data.get("form", 70)
        },
        "statistics": {
            "total_matches": total_matches,
            "wins": wins,
            "draws": draws,
            "losses": losses,
            "win_rate": round(win_rate, 1),
            "goals_scored": goals_scored,
            "goals_conceded": goals_conceded,
            "avg_goals_scored": round(avg_goals_scored, 2),
            "avg_goals_conceded": round(avg_goals_conceded, 2),
            "goal_difference": goals_scored - goals_conceded
        },
        "period_stats": period_stats,
        "recent_matches": recent_matches[:10],
        "upcoming_fixtures": upcoming_fixtures[:3],
        "data_source": "api"
    }

@api_router.post("/refresh-data")
async def refresh_data():
    """Fetch fresh data from API"""
    logger.info("🔄 Refresh data requested")
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
        raise HTTPException(status_code=503, detail="API unavailable - unable to refresh data")

@api_router.get("/games")
async def get_games(include_historical: bool = False):
    """Get games from real API data"""
    if not API_GAMES:
        logger.warning("⚠️ No API games available")
        raise HTTPException(status_code=503, detail="No games available - API data not loaded")
    
    games = []
    
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
    
    if include_historical:
        for g in HISTORICAL_GAMES:
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
                "data_source": "api"
            })
    
    logger.info(f"📤 Returning {len(games)} games")
    return games

@api_router.get("/models")
async def get_models():
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
    
    custom_models = await db.models.find({}, {"_id": 0}).to_list(100)
    models.extend(custom_models)
    
    logger.info(f"📤 Returning {len(models)} models")
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
    logger.info(f"✅ Created model: {model_input.name}")
    return {k: v for k, v in doc.items() if k != '_id'}

@api_router.get("/models/{model_id}")
async def get_model(model_id: str):
    for p in PRESET_MODELS:
        if p["id"] == model_id:
            return p
    
    model = await db.models.find_one({"id": model_id}, {"_id": 0})
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model

@api_router.delete("/models/{model_id}")
async def delete_model(model_id: str):
    if model_id.startswith("preset-"):
        raise HTTPException(status_code=400, detail="Cannot delete preset models")
    
    result = await db.models.delete_one({"id": model_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Model not found")
    
    logger.info(f"🗑️ Deleted model: {model_id}")
    return {"message": "Model deleted"}

@api_router.post("/picks/generate")
async def generate_picks(model_id: str):
    """Generate picks using real API data with comprehensive analysis"""
    logger.info(f"🎯 Generating picks for model: {model_id}")
    
    if not API_GAMES:
        raise HTTPException(status_code=503, detail="No games available - API data not loaded")
    
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
    
    for i, g in enumerate(API_GAMES):
        home_score, home_breakdown = calculate_team_score(g["home"], weights, is_home=True, game_data=g)
        away_score, away_breakdown = calculate_team_score(g["away"], weights, is_home=False, game_data=g)
        
        probs = calculate_outcome_probabilities(home_score, away_score)
        
        market_probs = {
            "home": 1 / g.get("h_odds", 2.0),
            "draw": 1 / g.get("d_odds", 3.0),
            "away": 1 / g.get("a_odds", 3.0)
        }
        
        # Pick the outcome with highest model probability (aligns with projected scores)
        best_outcome = max(probs.keys(), key=lambda k: probs[k])
        edge = (probs[best_outcome] - market_probs[best_outcome]) / market_probs[best_outcome] * 100
        
        market_odds = {
            "home": g.get("h_odds", 2.0),
            "draw": g.get("d_odds", 3.0),
            "away": g.get("a_odds", 3.0)
        }[best_outcome]
        
        # Use improved confidence calculation
        confidence, confidence_explanation = calculate_confidence(
            probs[best_outcome], 
            market_probs[best_outcome],
            home_score,
            away_score
        )
        
        # Calculate how the projected scores were determined
        calculation_summary = {
            "base_score": 1.5,
            "home_adjustments": sum(v["contribution"] for v in home_breakdown.values()),
            "away_adjustments": sum(v["contribution"] for v in away_breakdown.values()),
            "home_final": home_score,
            "away_final": away_score,
            "formula": f"Base Score (1.5) + Weighted Factor Contributions = Final Score"
        }
        
        pick = {
            "id": f"pick-{model_id}-{g['id']}",
            "game_id": g.get("id"),
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
            "confidence_explanation": confidence_explanation,
            "edge_percentage": round(edge, 1),
            "model_probability": round(probs[best_outcome] * 100, 1),
            "market_probability": round(market_probs[best_outcome] * 100, 1),
            "all_probabilities": {
                "home": round(probs["home"] * 100, 1),
                "draw": round(probs["draw"] * 100, 1),
                "away": round(probs["away"] * 100, 1)
            },
            "all_market_odds": {
                "home": g.get("h_odds", 2.0),
                "draw": g.get("d_odds", 3.0),
                "away": g.get("a_odds", 3.0)
            },
            "home_breakdown": home_breakdown,
            "away_breakdown": away_breakdown,
            "calculation_summary": calculation_summary,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "data_source": "api"
        }
        picks.append(pick)
        
        logger.info(f"  ✅ Pick: {g['home']} vs {g['away']} → {best_outcome.upper()} (conf: {confidence}/10)")
    
    picks.sort(key=lambda x: x["confidence_score"], reverse=True)
    logger.info(f"📤 Generated {len(picks)} picks")
    return picks

@api_router.get("/journal")
async def get_journal():
    entries = await db.journal.find({}, {"_id": 0}).to_list(100)
    logger.info(f"📤 Returning {len(entries)} journal entries")
    return entries

@api_router.post("/journal", status_code=201)
async def create_journal_entry(entry_input: JournalEntryCreate):
    """Add a pick to the journal"""
    parts = entry_input.pick_id.split("-")
    
    # Find the game from pick_id
    game_id = "-".join(parts[2:])  # Everything after "pick-{model_id}-"
    
    game = None
    for g in API_GAMES:
        if g["id"] == game_id:
            game = g
            break
    
    if not game:
        raise HTTPException(status_code=400, detail="Invalid pick")
    
    model_id = parts[1]
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
        game_id=game_id,
        model_name=model_name,
        home_team=game["home"],
        away_team=game["away"],
        match_date=game["date"],
        predicted_outcome="home",
        stake=entry_input.stake,
        odds_taken=entry_input.odds_taken
    )
    
    doc = entry.model_dump()
    await db.journal.insert_one(doc)
    logger.info(f"✅ Added journal entry: {game['home']} vs {game['away']}")
    return {k: v for k, v in doc.items() if k != '_id'}

@api_router.patch("/journal/{entry_id}/settle")
async def settle_bet(entry_id: str, settle_request: SettleBetRequest):
    """Settle a bet with the actual result"""
    entry = await db.journal.find_one({"id": entry_id}, {"_id": 0})
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    
    if entry["status"] != "pending":
        raise HTTPException(status_code=400, detail="Bet already settled")
    
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
    
    logger.info(f"✅ Settled bet: {entry['home_team']} vs {entry['away_team']} → {status.value}")
    
    updated_entry = {**entry, **update_data}
    return updated_entry

@api_router.delete("/journal/{entry_id}")
async def delete_journal_entry(entry_id: str):
    result = await db.journal.delete_one({"id": entry_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    logger.info(f"🗑️ Deleted journal entry: {entry_id}")
    return {"message": "Entry deleted"}

@api_router.post("/simulate")
async def simulate_model(sim_request: SimulationRequest):
    """Run backtesting simulation on real historical data"""
    logger.info(f"🎮 Running simulation for model: {sim_request.model_id}")
    
    if not HISTORICAL_GAMES:
        raise HTTPException(status_code=503, detail="No historical games available for simulation")
    
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
    
    games_to_simulate = []
    if sim_request.game_ids:
        for game_id in sim_request.game_ids:
            for g in HISTORICAL_GAMES:
                if g["id"] == game_id and g.get("is_completed"):
                    games_to_simulate.append(g)
    else:
        games_to_simulate = [g for g in HISTORICAL_GAMES if g.get("is_completed")]
    
    if not games_to_simulate:
        raise HTTPException(status_code=400, detail="No completed games available for simulation")
    
    weights = model["weights"]
    predictions = []
    correct = 0
    confidence_stats = {}
    outcome_stats = {"home": {"total": 0, "correct": 0}, "draw": {"total": 0, "correct": 0}, "away": {"total": 0, "correct": 0}}
    total_stake = 0
    total_return = 0
    stake_per_bet = 10
    
    for g in games_to_simulate:
        home_score, home_breakdown = calculate_team_score(g["home"], weights, is_home=True, game_data=g)
        away_score, away_breakdown = calculate_team_score(g["away"], weights, is_home=False, game_data=g)
        
        probs = calculate_outcome_probabilities(home_score, away_score)
        
        market_probs = {
            "home": 1 / g["h_odds"],
            "draw": 1 / g["d_odds"],
            "away": 1 / g["a_odds"]
        }
        
        # Pick the outcome with highest model probability (aligns with projected scores)
        best_outcome = max(probs.keys(), key=lambda k: probs[k])
        edge = (probs[best_outcome] - market_probs[best_outcome]) / market_probs[best_outcome] * 100
        
        market_odds = {"home": g["h_odds"], "draw": g["d_odds"], "away": g["a_odds"]}[best_outcome]
        confidence, _ = calculate_confidence(probs[best_outcome], market_probs[best_outcome], home_score, away_score)
        
        if sim_request.min_confidence and confidence < sim_request.min_confidence:
            continue
        
        actual_result = g.get("result")
        is_correct = (best_outcome == actual_result)
        
        if is_correct:
            correct += 1
        
        if confidence not in confidence_stats:
            confidence_stats[confidence] = {"total": 0, "correct": 0}
        confidence_stats[confidence]["total"] += 1
        if is_correct:
            confidence_stats[confidence]["correct"] += 1
        
        outcome_stats[best_outcome]["total"] += 1
        if is_correct:
            outcome_stats[best_outcome]["correct"] += 1
        
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
        raise HTTPException(status_code=400, detail="No predictions generated")
    
    accuracy = (correct / total_predictions) * 100
    net_profit = total_return - total_stake
    roi = (net_profit / total_stake) * 100 if total_stake > 0 else 0
    avg_odds = total_return / correct if correct > 0 else 0
    
    confidence_breakdown = {}
    for conf_level, stats in confidence_stats.items():
        acc = (stats["correct"] / stats["total"]) * 100 if stats["total"] > 0 else 0
        confidence_breakdown[str(conf_level)] = {
            "total": stats["total"],
            "correct": stats["correct"],
            "accuracy": round(acc, 1)
        }
    
    outcome_breakdown = {}
    for outcome, stats in outcome_stats.items():
        acc = (stats["correct"] / stats["total"]) * 100 if stats["total"] > 0 else 0
        outcome_breakdown[outcome] = {
            "total": stats["total"],
            "correct": stats["correct"],
            "accuracy": round(acc, 1)
        }
    
    logger.info(f"✅ Simulation complete: {accuracy:.1f}% accuracy, ROI: {roi:.1f}%")
    
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
    
    logger.info(f"📤 Stats: {total_bets} bets, {win_rate:.1f}% win rate, {roi:.1f}% ROI")
    
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

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

@app.on_event("startup")
async def startup_fetch_api_data():
    """Fetch data from API on server startup"""
    logger.info("=" * 80)
    logger.info("🚀 BetGenius Backend Starting - Real API Data Only Mode")
    logger.info("=" * 80)
    success = await fetch_epl_fixtures_from_api()
    if success:
        logger.info("=" * 80)
        logger.info(f"✅ Successfully loaded {len(API_GAMES)} games and {len(API_TEAMS)} teams from API")
        logger.info("=" * 80)
    else:
        logger.error("=" * 80)
        logger.error("❌ Failed to load API data - application will not function properly")
        logger.error("=" * 80)
