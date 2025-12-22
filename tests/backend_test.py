#!/usr/bin/env python3
"""
BetGenius EPL Sports Betting Analytics - Backend API Test Suite
Tests all API endpoints for functionality and integration
"""

import requests
import sys
import json
from datetime import datetime

class BetGeniusAPITester:
    def __init__(self, base_url="https://bet-genius-31.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.created_model_id = None
        self.created_entry_id = None

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details
        })

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, params=params)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            details = f"Status: {response.status_code}"
            
            if not success:
                details += f" (Expected {expected_status})"
                if response.text:
                    try:
                        error_data = response.json()
                        details += f" - {error_data.get('detail', response.text[:100])}"
                    except:
                        details += f" - {response.text[:100]}"

            self.log_test(name, success, details)
            
            if success:
                try:
                    return response.json()
                except:
                    return {}
            return None

        except Exception as e:
            self.log_test(name, False, f"Error: {str(e)}")
            return None

    def test_root_endpoint(self):
        """Test API root endpoint"""
        return self.run_test("API Root", "GET", "", 200)

    def test_get_teams(self):
        """Test teams endpoint"""
        teams = self.run_test("Get Teams", "GET", "teams", 200)
        if teams and len(teams) > 0:
            self.log_test("Teams Data Validation", True, f"Found {len(teams)} teams")
            return teams
        else:
            self.log_test("Teams Data Validation", False, "No teams returned")
            return None

    def test_get_games(self):
        """Test games endpoint"""
        games = self.run_test("Get Games", "GET", "games", 200)
        if games and len(games) > 0:
            self.log_test("Games Data Validation", True, f"Found {len(games)} games")
            # Validate game structure
            game = games[0]
            required_fields = ['id', 'home_team', 'away_team', 'home_odds', 'draw_odds', 'away_odds']
            missing_fields = [field for field in required_fields if field not in game]
            if missing_fields:
                self.log_test("Game Structure Validation", False, f"Missing fields: {missing_fields}")
            else:
                self.log_test("Game Structure Validation", True, "All required fields present")
            return games
        else:
            self.log_test("Games Data Validation", False, "No games returned")
            return None

    def test_get_models(self):
        """Test models endpoint"""
        models = self.run_test("Get Models", "GET", "models", 200)
        if models and len(models) >= 3:
            preset_models = [m for m in models if m.get('model_type') == 'preset']
            self.log_test("Preset Models Validation", len(preset_models) >= 3, 
                         f"Found {len(preset_models)} preset models")
            return models
        else:
            self.log_test("Models Data Validation", False, "Insufficient models returned")
            return None

    def test_create_custom_model(self):
        """Test creating a custom model"""
        model_data = {
            "name": "Test Model",
            "description": "Test model for API testing",
            "weights": {
                "team_offense": 25,
                "team_defense": 25,
                "recent_form": 20,
                "injuries": 15,
                "home_advantage": 15
            }
        }
        
        result = self.run_test("Create Custom Model", "POST", "models", 201, model_data)
        if result and 'id' in result:
            self.created_model_id = result['id']
            self.log_test("Model Creation Validation", True, f"Model ID: {self.created_model_id}")
            return result
        else:
            self.log_test("Model Creation Validation", False, "No model ID returned")
            return None

    def test_get_single_model(self):
        """Test getting a single model"""
        if not self.created_model_id:
            self.log_test("Get Single Model", False, "No model ID available")
            return None
            
        model = self.run_test("Get Single Model", "GET", f"models/{self.created_model_id}", 200)
        if model and model.get('name') == 'Test Model':
            self.log_test("Single Model Validation", True, "Model data matches")
            return model
        else:
            self.log_test("Single Model Validation", False, "Model data mismatch")
            return None

    def test_generate_picks(self):
        """Test generating picks with a model"""
        if not self.created_model_id:
            self.log_test("Generate Picks", False, "No model ID available")
            return None
            
        picks = self.run_test("Generate Picks", "POST", "picks/generate", 200, 
                             params={"model_id": self.created_model_id})
        
        if picks and len(picks) > 0:
            self.log_test("Picks Generation Validation", True, f"Generated {len(picks)} picks")
            # Validate pick structure
            pick = picks[0]
            required_fields = ['id', 'game_id', 'model_id', 'home_team', 'away_team', 
                             'predicted_outcome', 'market_odds', 'confidence_score', 'edge_percentage']
            missing_fields = [field for field in required_fields if field not in pick]
            if missing_fields:
                self.log_test("Pick Structure Validation", False, f"Missing fields: {missing_fields}")
            else:
                self.log_test("Pick Structure Validation", True, "All required fields present")
            return picks
        else:
            self.log_test("Picks Generation Validation", False, "No picks generated")
            return None

    def test_journal_operations(self):
        """Test journal CRUD operations"""
        # First get picks to add to journal
        picks = self.run_test("Generate Picks for Journal", "POST", "picks/generate", 200, 
                             params={"model_id": "preset-balanced"})
        
        if not picks or len(picks) == 0:
            self.log_test("Journal Test Setup", False, "No picks available for journal test")
            return None

        # Test adding to journal
        journal_data = {
            "pick_id": picks[0]['id'],
            "stake": 50.0,
            "odds_taken": 2.0
        }
        
        entry = self.run_test("Add to Journal", "POST", "journal", 201, journal_data)
        if entry and 'id' in entry:
            self.created_entry_id = entry['id']
            self.log_test("Journal Entry Creation", True, f"Entry ID: {self.created_entry_id}")
        else:
            self.log_test("Journal Entry Creation", False, "No entry ID returned")
            return None

        # Test getting journal
        journal = self.run_test("Get Journal", "GET", "journal", 200)
        if journal and len(journal) > 0:
            self.log_test("Journal Retrieval", True, f"Found {len(journal)} entries")
        else:
            self.log_test("Journal Retrieval", False, "No journal entries found")

        # Test settling bet
        settle_data = {"result": "home"}
        settled = self.run_test("Settle Bet", "PATCH", f"journal/{self.created_entry_id}/settle", 200, settle_data)
        if settled and settled.get('status') in ['won', 'lost']:
            self.log_test("Bet Settlement", True, f"Status: {settled.get('status')}")
        else:
            self.log_test("Bet Settlement", False, "Settlement failed or invalid status")

        return journal

    def test_stats_endpoint(self):
        """Test stats endpoint"""
        stats = self.run_test("Get Stats", "GET", "stats", 200)
        if stats:
            required_fields = ['total_bets', 'pending_bets', 'won_bets', 'lost_bets', 
                             'win_rate', 'total_staked', 'total_profit', 'roi']
            missing_fields = [field for field in required_fields if field not in stats]
            if missing_fields:
                self.log_test("Stats Structure Validation", False, f"Missing fields: {missing_fields}")
            else:
                self.log_test("Stats Structure Validation", True, "All required fields present")
            return stats
        else:
            self.log_test("Stats Validation", False, "No stats returned")
            return None

    def test_delete_operations(self):
        """Test delete operations"""
        # Delete journal entry
        if self.created_entry_id:
            result = self.run_test("Delete Journal Entry", "DELETE", f"journal/{self.created_entry_id}", 200)
            if result:
                self.log_test("Journal Entry Deletion", True, "Entry deleted successfully")

        # Delete custom model
        if self.created_model_id:
            result = self.run_test("Delete Custom Model", "DELETE", f"models/{self.created_model_id}", 200)
            if result:
                self.log_test("Custom Model Deletion", True, "Model deleted successfully")

    def test_error_handling(self):
        """Test error handling for invalid requests"""
        # Test invalid model ID
        self.run_test("Invalid Model ID", "GET", "models/invalid-id", 404)
        
        # Test invalid journal entry ID
        self.run_test("Invalid Journal ID", "DELETE", "journal/invalid-id", 404)
        
        # Test deleting preset model (should fail)
        self.run_test("Delete Preset Model (Should Fail)", "DELETE", "models/preset-balanced", 400)

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting BetGenius API Test Suite")
        print("=" * 50)
        
        # Basic endpoint tests
        self.test_root_endpoint()
        self.test_get_teams()
        self.test_get_games()
        self.test_get_models()
        
        # Model operations
        self.test_create_custom_model()
        self.test_get_single_model()
        
        # Picks generation
        self.test_generate_picks()
        
        # Journal operations
        self.test_journal_operations()
        
        # Stats
        self.test_stats_endpoint()
        
        # Error handling
        self.test_error_handling()
        
        # Cleanup
        self.test_delete_operations()
        
        # Print summary
        print("\n" + "=" * 50)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return 0
        else:
            print("⚠️  Some tests failed. Check the details above.")
            return 1

def main():
    """Main test runner"""
    tester = BetGeniusAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())