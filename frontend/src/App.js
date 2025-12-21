import { useState, useEffect, useCallback } from "react";
import "@/App.css";
import axios from "axios";
import { Toaster, toast } from "sonner";
import {
  TrendingUp,
  Target,
  BookOpen,
  BarChart3,
  Plus,
  Trash2,
  ChevronRight,
  Trophy,
  AlertCircle,
  Clock,
  DollarSign,
  Percent,
  Zap,
  RefreshCw,
} from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Slider } from "@/components/ui/slider";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// ============ COMPONENTS ============

const StatCard = ({ title, value, subtitle, icon: Icon, trend }) => (
  <Card className="bg-zinc-900/50 border-zinc-800 hover:border-green-500/30 transition-colors">
    <CardContent className="p-4">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs text-zinc-500 uppercase tracking-wider font-display">{title}</p>
          <p className="text-2xl font-bold font-mono mt-1 text-zinc-100">{value}</p>
          {subtitle && <p className="text-xs text-zinc-500 mt-1">{subtitle}</p>}
        </div>
        {Icon && (
          <div className="p-2 bg-green-500/10 rounded-sm">
            <Icon className="w-4 h-4 text-green-500" />
          </div>
        )}
      </div>
      {trend !== undefined && (
        <div className={`mt-2 text-xs ${trend >= 0 ? 'text-green-500' : 'text-red-500'}`}>
          {trend >= 0 ? '+' : ''}{trend}% vs last week
        </div>
      )}
    </CardContent>
  </Card>
);

const WeightSlider = ({ label, value, onChange, description }) => (
  <div className="space-y-3">
    <div className="flex justify-between items-center">
      <div>
        <span className="text-sm font-medium text-zinc-200">{label}</span>
        {description && <p className="text-xs text-zinc-500">{description}</p>}
      </div>
      <span className="text-sm font-mono text-green-500 bg-green-500/10 px-2 py-0.5 rounded">
        {value}%
      </span>
    </div>
    <Slider
      value={[value]}
      onValueChange={([v]) => onChange(v)}
      max={100}
      step={5}
      className="slider-green"
    />
  </div>
);

const ConfidenceBadge = ({ score }) => {
  let className = "confidence-low";
  if (score >= 7) className = "confidence-high";
  else if (score >= 5) className = "confidence-medium";
  
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-mono font-bold ${className}`}>
      {score}/10
    </span>
  );
};

const OutcomeBadge = ({ outcome }) => {
  const labels = { home: "HOME", draw: "DRAW", away: "AWAY" };
  const colors = {
    home: "bg-blue-500/20 text-blue-400 border-blue-500/40",
    draw: "bg-zinc-500/20 text-zinc-400 border-zinc-500/40",
    away: "bg-orange-500/20 text-orange-400 border-orange-500/40"
  };
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-mono border ${colors[outcome]}`}>
      {labels[outcome]}
    </span>
  );
};

const StatusBadge = ({ status }) => {
  const config = {
    pending: { color: "bg-yellow-500/20 text-yellow-500 border-yellow-500/40", icon: Clock },
    won: { color: "bg-green-500/20 text-green-500 border-green-500/40", icon: Trophy },
    lost: { color: "bg-red-500/20 text-red-500 border-red-500/40", icon: AlertCircle }
  };
  const { color, icon: Icon } = config[status] || config.pending;
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-mono border ${color}`}>
      <Icon className="w-3 h-3" />
      {status.toUpperCase()}
    </span>
  );
};

// ============ MAIN APP ============

function App() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [models, setModels] = useState([]);
  const [games, setGames] = useState([]);
  const [picks, setPicks] = useState([]);
  const [journal, setJournal] = useState([]);
  const [stats, setStats] = useState({});
  const [selectedModel, setSelectedModel] = useState(null);
  const [loading, setLoading] = useState(false);

  // Model builder state
  const [newModelName, setNewModelName] = useState("");
  const [weights, setWeights] = useState({
    team_offense: 20,
    team_defense: 20,
    recent_form: 20,
    injuries: 20,
    home_advantage: 20
  });

  // Dialog states
  const [showAddBetDialog, setShowAddBetDialog] = useState(false);
  const [selectedPick, setSelectedPick] = useState(null);
  const [betStake, setBetStake] = useState("");
  const [betOdds, setBetOdds] = useState("");

  const [showSettleDialog, setShowSettleDialog] = useState(false);
  const [selectedEntry, setSelectedEntry] = useState(null);
  const [settleResult, setSettleResult] = useState("");

  // Fetch data
  const fetchData = useCallback(async () => {
    try {
      const [modelsRes, gamesRes, journalRes, statsRes] = await Promise.all([
        axios.get(`${API}/models`),
        axios.get(`${API}/games`),
        axios.get(`${API}/journal`),
        axios.get(`${API}/stats`)
      ]);
      setModels(modelsRes.data);
      setGames(gamesRes.data);
      setJournal(journalRes.data);
      setStats(statsRes.data);
    } catch (err) {
      console.error("Error fetching data:", err);
      toast.error("Failed to load data");
    }
  }, []);

  // Refresh fixtures with new random data
  const refreshFixtures = async () => {
    setLoading(true);
    try {
      await axios.post(`${API}/refresh-data`);
      await fetchData();
      setPicks([]);
      setSelectedModel(null);
      toast.success("Fixtures refreshed with new data!");
    } catch (err) {
      toast.error("Failed to refresh fixtures");
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Generate picks for selected model
  const generatePicks = async (modelId) => {
    setLoading(true);
    try {
      const res = await axios.post(`${API}/picks/generate?model_id=${modelId}`);
      setPicks(res.data);
      setSelectedModel(modelId);
      toast.success("Picks generated!");
    } catch (err) {
      toast.error("Failed to generate picks");
    }
    setLoading(false);
  };

  // Create new model
  const createModel = async () => {
    if (!newModelName.trim()) {
      toast.error("Please enter a model name");
      return;
    }
    try {
      await axios.post(`${API}/models`, {
        name: newModelName,
        description: "Custom model",
        weights
      });
      toast.success("Model created!");
      setNewModelName("");
      setWeights({ team_offense: 20, team_defense: 20, recent_form: 20, injuries: 20, home_advantage: 20 });
      fetchData();
    } catch (err) {
      toast.error("Failed to create model");
    }
  };

  // Delete model
  const deleteModel = async (modelId) => {
    try {
      await axios.delete(`${API}/models/${modelId}`);
      toast.success("Model deleted");
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to delete model");
    }
  };

  // Add bet to journal
  const addToJournal = async () => {
    if (!selectedPick || !betStake || !betOdds) {
      toast.error("Please fill in all fields");
      return;
    }
    try {
      await axios.post(`${API}/journal`, {
        pick_id: selectedPick.id,
        stake: parseFloat(betStake),
        odds_taken: parseFloat(betOdds)
      });
      toast.success("Bet added to journal!");
      setShowAddBetDialog(false);
      setBetStake("");
      setBetOdds("");
      fetchData();
    } catch (err) {
      toast.error("Failed to add bet");
    }
  };

  // Settle bet
  const settleBet = async () => {
    if (!selectedEntry || !settleResult) return;
    try {
      await axios.patch(`${API}/journal/${selectedEntry.id}/settle`, {
        result: settleResult
      });
      toast.success("Bet settled!");
      setShowSettleDialog(false);
      setSelectedEntry(null);
      setSettleResult("");
      fetchData();
    } catch (err) {
      toast.error("Failed to settle bet");
    }
  };

  // Delete journal entry
  const deleteJournalEntry = async (entryId) => {
    try {
      await axios.delete(`${API}/journal/${entryId}`);
      toast.success("Entry deleted");
      fetchData();
    } catch (err) {
      toast.error("Failed to delete entry");
    }
  };

  const totalWeights = Object.values(weights).reduce((a, b) => a + b, 0);

  return (
    <div className="App min-h-screen bg-[#09090b]">
      <Toaster theme="dark" position="top-right" richColors />
      
      {/* Header */}
      <header className="border-b border-zinc-800 bg-zinc-900/50 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-500/10 rounded-sm">
                <Zap className="w-6 h-6 text-green-500" />
              </div>
              <div>
                <h1 className="text-xl font-display font-bold text-zinc-100 tracking-tight">BETGENIUS</h1>
                <p className="text-xs text-zinc-500">EPL Analytics</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <Badge variant="outline" className="border-green-500/40 text-green-500 font-mono text-xs">
                {games.length} MATCHES
              </Badge>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="bg-zinc-900 border border-zinc-800 p-1">
            <TabsTrigger value="dashboard" className="data-[state=active]:bg-green-500/20 data-[state=active]:text-green-500" data-testid="tab-dashboard">
              <BarChart3 className="w-4 h-4 mr-2" />
              Dashboard
            </TabsTrigger>
            <TabsTrigger value="models" className="data-[state=active]:bg-green-500/20 data-[state=active]:text-green-500" data-testid="tab-models">
              <Target className="w-4 h-4 mr-2" />
              Models
            </TabsTrigger>
            <TabsTrigger value="picks" className="data-[state=active]:bg-green-500/20 data-[state=active]:text-green-500" data-testid="tab-picks">
              <TrendingUp className="w-4 h-4 mr-2" />
              Value Finder
            </TabsTrigger>
            <TabsTrigger value="journal" className="data-[state=active]:bg-green-500/20 data-[state=active]:text-green-500" data-testid="tab-journal">
              <BookOpen className="w-4 h-4 mr-2" />
              Journal
            </TabsTrigger>
          </TabsList>

          {/* Dashboard Tab */}
          <TabsContent value="dashboard" className="space-y-6" data-testid="dashboard-content">
            {/* Stats Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <StatCard title="Total Bets" value={stats.total_bets || 0} icon={BookOpen} />
              <StatCard title="Win Rate" value={`${stats.win_rate || 0}%`} icon={Percent} />
              <StatCard title="Total P/L" value={`$${stats.total_profit?.toFixed(2) || '0.00'}`} icon={DollarSign} />
              <StatCard title="ROI" value={`${stats.roi || 0}%`} icon={TrendingUp} />
            </div>

            {/* Quick Actions */}
            <div className="grid md:grid-cols-2 gap-6">
              <Card className="bg-zinc-900/50 border-zinc-800">
                <CardHeader>
                  <CardTitle className="text-lg font-display text-zinc-100">Active Models</CardTitle>
                  <CardDescription className="text-zinc-500">Your betting models</CardDescription>
                </CardHeader>
                <CardContent className="space-y-2">
                  {models.slice(0, 4).map((model) => (
                    <div key={model.id} className="flex items-center justify-between p-3 bg-zinc-800/50 rounded-sm border border-zinc-700/50 hover:border-green-500/30 transition-colors">
                      <div>
                        <p className="text-sm font-medium text-zinc-200">{model.name}</p>
                        <p className="text-xs text-zinc-500">{model.model_type}</p>
                      </div>
                      <Button
                        size="sm"
                        variant="ghost"
                        className="text-green-500 hover:text-green-400 hover:bg-green-500/10"
                        onClick={() => { setActiveTab("picks"); generatePicks(model.id); }}
                        data-testid={`use-model-${model.id}`}
                      >
                        Use <ChevronRight className="w-4 h-4 ml-1" />
                      </Button>
                    </div>
                  ))}
                </CardContent>
              </Card>

              <Card className="bg-zinc-900/50 border-zinc-800">
                <CardHeader>
                  <CardTitle className="text-lg font-display text-zinc-100">Upcoming Matches</CardTitle>
                  <CardDescription className="text-zinc-500">Next EPL fixtures</CardDescription>
                </CardHeader>
                <CardContent className="space-y-2">
                  {games.slice(0, 4).map((game) => (
                    <div key={game.id} className="flex items-center justify-between p-3 bg-zinc-800/50 rounded-sm border border-zinc-700/50">
                      <div>
                        <p className="text-sm font-medium text-zinc-200">
                          {game.home_team} vs {game.away_team}
                        </p>
                        <p className="text-xs text-zinc-500">{game.match_date}</p>
                      </div>
                      <div className="flex gap-2 text-xs font-mono">
                        <span className="text-blue-400">{game.home_odds}</span>
                        <span className="text-zinc-500">{game.draw_odds}</span>
                        <span className="text-orange-400">{game.away_odds}</span>
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </div>

            {/* Recent Journal */}
            <Card className="bg-zinc-900/50 border-zinc-800">
              <CardHeader>
                <CardTitle className="text-lg font-display text-zinc-100">Recent Bets</CardTitle>
              </CardHeader>
              <CardContent>
                {journal.length === 0 ? (
                  <p className="text-zinc-500 text-sm text-center py-8">No bets recorded yet. Start by generating picks!</p>
                ) : (
                  <div className="space-y-2">
                    {journal.slice(0, 5).map((entry) => (
                      <div key={entry.id} className="flex items-center justify-between p-3 bg-zinc-800/50 rounded-sm border border-zinc-700/50">
                        <div>
                          <p className="text-sm font-medium text-zinc-200">
                            {entry.home_team} vs {entry.away_team}
                          </p>
                          <p className="text-xs text-zinc-500">{entry.model_name}</p>
                        </div>
                        <div className="flex items-center gap-3">
                          <span className="font-mono text-sm text-zinc-300">${entry.stake}</span>
                          <StatusBadge status={entry.status} />
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Models Tab */}
          <TabsContent value="models" className="space-y-6" data-testid="models-content">
            <div className="grid md:grid-cols-2 gap-6">
              {/* Preset Models */}
              <Card className="bg-zinc-900/50 border-zinc-800">
                <CardHeader>
                  <CardTitle className="text-lg font-display text-zinc-100">Preset Models</CardTitle>
                  <CardDescription className="text-zinc-500">Ready-to-use strategies</CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  {models.filter(m => m.model_type === "preset").map((model) => (
                    <div key={model.id} className="p-4 bg-zinc-800/50 rounded-sm border border-zinc-700/50 hover:border-green-500/30 transition-colors card-hover">
                      <div className="flex items-start justify-between">
                        <div>
                          <h4 className="font-medium text-zinc-200">{model.name}</h4>
                          <p className="text-xs text-zinc-500 mt-1">{model.description}</p>
                        </div>
                        <Badge variant="outline" className="border-green-500/40 text-green-500 text-xs">
                          PRESET
                        </Badge>
                      </div>
                      <div className="mt-3 grid grid-cols-5 gap-2 text-xs">
                        <div className="text-center">
                          <p className="text-zinc-500">OFF</p>
                          <p className="font-mono text-zinc-300">{model.weights.team_offense}%</p>
                        </div>
                        <div className="text-center">
                          <p className="text-zinc-500">DEF</p>
                          <p className="font-mono text-zinc-300">{model.weights.team_defense}%</p>
                        </div>
                        <div className="text-center">
                          <p className="text-zinc-500">FORM</p>
                          <p className="font-mono text-zinc-300">{model.weights.recent_form}%</p>
                        </div>
                        <div className="text-center">
                          <p className="text-zinc-500">INJ</p>
                          <p className="font-mono text-zinc-300">{model.weights.injuries}%</p>
                        </div>
                        <div className="text-center">
                          <p className="text-zinc-500">HOME</p>
                          <p className="font-mono text-zinc-300">{model.weights.home_advantage}%</p>
                        </div>
                      </div>
                      <Button
                        className="w-full mt-4 bg-green-600 hover:bg-green-500 text-white font-bold uppercase tracking-wider"
                        onClick={() => { setActiveTab("picks"); generatePicks(model.id); }}
                        data-testid={`generate-picks-${model.id}`}
                      >
                        Generate Picks
                      </Button>
                    </div>
                  ))}
                </CardContent>
              </Card>

              {/* Model Builder */}
              <Card className="bg-zinc-900/50 border-zinc-800">
                <CardHeader>
                  <CardTitle className="text-lg font-display text-zinc-100">Build Custom Model</CardTitle>
                  <CardDescription className="text-zinc-500">Create your own strategy</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div>
                    <label className="text-sm text-zinc-400 mb-2 block">Model Name</label>
                    <Input
                      placeholder="My Custom Model"
                      value={newModelName}
                      onChange={(e) => setNewModelName(e.target.value)}
                      className="bg-zinc-800 border-zinc-700 focus:border-green-500"
                      data-testid="model-name-input"
                    />
                  </div>

                  <div className="space-y-5">
                    <WeightSlider
                      label="Team Offense"
                      description="Attacking prowess"
                      value={weights.team_offense}
                      onChange={(v) => setWeights(w => ({ ...w, team_offense: v }))}
                    />
                    <WeightSlider
                      label="Team Defense"
                      description="Defensive solidity"
                      value={weights.team_defense}
                      onChange={(v) => setWeights(w => ({ ...w, team_defense: v }))}
                    />
                    <WeightSlider
                      label="Recent Form"
                      description="Last 5 matches"
                      value={weights.recent_form}
                      onChange={(v) => setWeights(w => ({ ...w, recent_form: v }))}
                    />
                    <WeightSlider
                      label="Injuries"
                      description="Squad availability"
                      value={weights.injuries}
                      onChange={(v) => setWeights(w => ({ ...w, injuries: v }))}
                    />
                    <WeightSlider
                      label="Home Advantage"
                      description="Home/Away factor"
                      value={weights.home_advantage}
                      onChange={(v) => setWeights(w => ({ ...w, home_advantage: v }))}
                    />
                  </div>

                  <div className="flex items-center justify-between p-3 bg-zinc-800/50 rounded-sm border border-zinc-700/50">
                    <span className="text-sm text-zinc-400">Total Weight</span>
                    <span className={`font-mono font-bold ${totalWeights === 100 ? 'text-green-500' : 'text-yellow-500'}`}>
                      {totalWeights}%
                    </span>
                  </div>

                  <Button
                    className="w-full bg-green-600 hover:bg-green-500 text-white font-bold uppercase tracking-wider"
                    onClick={createModel}
                    data-testid="create-model-btn"
                  >
                    <Plus className="w-4 h-4 mr-2" />
                    Create Model
                  </Button>
                </CardContent>
              </Card>
            </div>

            {/* Custom Models List */}
            {models.filter(m => m.model_type === "custom").length > 0 && (
              <Card className="bg-zinc-900/50 border-zinc-800">
                <CardHeader>
                  <CardTitle className="text-lg font-display text-zinc-100">Your Custom Models</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid md:grid-cols-3 gap-4">
                    {models.filter(m => m.model_type === "custom").map((model) => (
                      <div key={model.id} className="p-4 bg-zinc-800/50 rounded-sm border border-zinc-700/50 hover:border-green-500/30 transition-colors">
                        <div className="flex items-start justify-between">
                          <h4 className="font-medium text-zinc-200">{model.name}</h4>
                          <Button
                            size="icon"
                            variant="ghost"
                            className="h-6 w-6 text-red-500 hover:text-red-400 hover:bg-red-500/10"
                            onClick={() => deleteModel(model.id)}
                            data-testid={`delete-model-${model.id}`}
                          >
                            <Trash2 className="w-3 h-3" />
                          </Button>
                        </div>
                        <Button
                          className="w-full mt-3 bg-green-600 hover:bg-green-500 text-white text-xs"
                          onClick={() => { setActiveTab("picks"); generatePicks(model.id); }}
                        >
                          Use Model
                        </Button>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* Picks Tab (Value Finder) */}
          <TabsContent value="picks" className="space-y-6" data-testid="picks-content">
            {/* Model Selector */}
            <Card className="bg-zinc-900/50 border-zinc-800">
              <CardContent className="p-4">
                <div className="flex flex-col md:flex-row items-start md:items-center gap-4">
                  <div className="flex-1">
                    <Select value={selectedModel || ""} onValueChange={(v) => generatePicks(v)} data-testid="model-selector">
                      <SelectTrigger className="bg-zinc-800 border-zinc-700">
                        <SelectValue placeholder="Select a model to generate picks" />
                      </SelectTrigger>
                      <SelectContent className="bg-zinc-800 border-zinc-700">
                        {models.map((model) => (
                          <SelectItem key={model.id} value={model.id}>
                            {model.name} ({model.model_type})
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  {selectedModel && (
                    <Badge className="bg-green-500/20 text-green-500 border-green-500/40">
                      {picks.length} picks generated
                    </Badge>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Picks Table */}
            {picks.length > 0 ? (
              <Card className="bg-zinc-900/50 border-zinc-800 overflow-hidden">
                <CardHeader>
                  <CardTitle className="text-lg font-display text-zinc-100">Value Picks</CardTitle>
                  <CardDescription className="text-zinc-500">Sorted by confidence score</CardDescription>
                </CardHeader>
                <CardContent className="p-0">
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b border-zinc-800 bg-zinc-800/50">
                          <th className="text-left p-4 text-xs text-zinc-500 uppercase tracking-wider">Match</th>
                          <th className="text-center p-4 text-xs text-zinc-500 uppercase tracking-wider">Projected</th>
                          <th className="text-center p-4 text-xs text-zinc-500 uppercase tracking-wider">Pick</th>
                          <th className="text-center p-4 text-xs text-zinc-500 uppercase tracking-wider">Odds</th>
                          <th className="text-center p-4 text-xs text-zinc-500 uppercase tracking-wider">Edge</th>
                          <th className="text-center p-4 text-xs text-zinc-500 uppercase tracking-wider">Confidence</th>
                          <th className="text-right p-4 text-xs text-zinc-500 uppercase tracking-wider">Action</th>
                        </tr>
                      </thead>
                      <tbody>
                        {picks.map((pick) => (
                          <tr key={pick.id} className="border-b border-zinc-800/50 table-row-hover">
                            <td className="p-4">
                              <p className="text-sm font-medium text-zinc-200">
                                {pick.home_team} vs {pick.away_team}
                              </p>
                              <p className="text-xs text-zinc-500">{pick.match_date}</p>
                            </td>
                            <td className="p-4 text-center">
                              <span className="font-mono text-sm text-zinc-300">
                                {pick.projected_home_score} - {pick.projected_away_score}
                              </span>
                            </td>
                            <td className="p-4 text-center">
                              <OutcomeBadge outcome={pick.predicted_outcome} />
                            </td>
                            <td className="p-4 text-center">
                              <span className="font-mono text-sm text-green-400">
                                {pick.market_odds.toFixed(2)}
                              </span>
                            </td>
                            <td className="p-4 text-center">
                              <span className={`font-mono text-sm ${pick.edge_percentage > 0 ? 'text-green-500' : 'text-red-500'}`}>
                                {pick.edge_percentage > 0 ? '+' : ''}{pick.edge_percentage}%
                              </span>
                            </td>
                            <td className="p-4 text-center">
                              <ConfidenceBadge score={pick.confidence_score} />
                            </td>
                            <td className="p-4 text-right">
                              <Button
                                size="sm"
                                className="bg-green-600 hover:bg-green-500 text-white text-xs"
                                onClick={() => { setSelectedPick(pick); setBetOdds(pick.market_odds.toString()); setShowAddBetDialog(true); }}
                                data-testid={`add-bet-${pick.id}`}
                              >
                                Add to Journal
                              </Button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            ) : (
              <Card className="bg-zinc-900/50 border-zinc-800">
                <CardContent className="p-12 text-center">
                  <Target className="w-12 h-12 text-zinc-700 mx-auto mb-4" />
                  <p className="text-zinc-500">Select a model above to generate value picks</p>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* Journal Tab */}
          <TabsContent value="journal" className="space-y-6" data-testid="journal-content">
            {/* Journal Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <StatCard title="Pending" value={stats.pending_bets || 0} icon={Clock} />
              <StatCard title="Won" value={stats.won_bets || 0} icon={Trophy} />
              <StatCard title="Lost" value={stats.lost_bets || 0} icon={AlertCircle} />
              <StatCard
                title="Net P/L"
                value={`$${stats.total_profit?.toFixed(2) || '0.00'}`}
                icon={DollarSign}
              />
            </div>

            {/* Journal Entries */}
            <Card className="bg-zinc-900/50 border-zinc-800">
              <CardHeader>
                <CardTitle className="text-lg font-display text-zinc-100">Bet Journal</CardTitle>
                <CardDescription className="text-zinc-500">Track your betting history</CardDescription>
              </CardHeader>
              <CardContent>
                {journal.length === 0 ? (
                  <div className="text-center py-12">
                    <BookOpen className="w-12 h-12 text-zinc-700 mx-auto mb-4" />
                    <p className="text-zinc-500">No bets recorded yet</p>
                    <p className="text-zinc-600 text-sm mt-1">Add picks from the Value Finder to start tracking</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {journal.map((entry) => (
                      <div key={entry.id} className="p-4 bg-zinc-800/50 rounded-sm border border-zinc-700/50 hover:border-zinc-600 transition-colors">
                        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                          <div className="flex-1">
                            <div className="flex items-center gap-3">
                              <p className="text-sm font-medium text-zinc-200">
                                {entry.home_team} vs {entry.away_team}
                              </p>
                              <StatusBadge status={entry.status} />
                            </div>
                            <p className="text-xs text-zinc-500 mt-1">
                              {entry.model_name} • {entry.match_date}
                            </p>
                          </div>
                          <div className="flex items-center gap-6">
                            <div className="text-center">
                              <p className="text-xs text-zinc-500">Stake</p>
                              <p className="font-mono text-sm text-zinc-300">${entry.stake}</p>
                            </div>
                            <div className="text-center">
                              <p className="text-xs text-zinc-500">Odds</p>
                              <p className="font-mono text-sm text-zinc-300">{entry.odds_taken}</p>
                            </div>
                            <div className="text-center">
                              <p className="text-xs text-zinc-500">P/L</p>
                              <p className={`font-mono text-sm font-bold ${entry.profit_loss > 0 ? 'text-green-500' : entry.profit_loss < 0 ? 'text-red-500' : 'text-zinc-500'}`}>
                                {entry.profit_loss > 0 ? '+' : ''}{entry.profit_loss !== 0 ? `$${entry.profit_loss.toFixed(2)}` : '-'}
                              </p>
                            </div>
                            <div className="flex gap-2">
                              {entry.status === "pending" && (
                                <Button
                                  size="sm"
                                  variant="outline"
                                  className="border-green-500/40 text-green-500 hover:bg-green-500/10"
                                  onClick={() => { setSelectedEntry(entry); setShowSettleDialog(true); }}
                                  data-testid={`settle-bet-${entry.id}`}
                                >
                                  Settle
                                </Button>
                              )}
                              <Button
                                size="icon"
                                variant="ghost"
                                className="h-8 w-8 text-red-500 hover:text-red-400 hover:bg-red-500/10"
                                onClick={() => deleteJournalEntry(entry.id)}
                                data-testid={`delete-entry-${entry.id}`}
                              >
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>

      {/* Add Bet Dialog */}
      <Dialog open={showAddBetDialog} onOpenChange={setShowAddBetDialog}>
        <DialogContent className="bg-zinc-900 border-zinc-800">
          <DialogHeader>
            <DialogTitle className="font-display text-zinc-100">Add to Journal</DialogTitle>
            <DialogDescription className="text-zinc-500">
              {selectedPick && `${selectedPick.home_team} vs ${selectedPick.away_team}`}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="text-sm text-zinc-400 mb-2 block">Stake Amount ($)</label>
              <Input
                type="number"
                placeholder="100"
                value={betStake}
                onChange={(e) => setBetStake(e.target.value)}
                className="bg-zinc-800 border-zinc-700 focus:border-green-500"
                data-testid="stake-input"
              />
            </div>
            <div>
              <label className="text-sm text-zinc-400 mb-2 block">Odds Taken</label>
              <Input
                type="number"
                step="0.01"
                placeholder="2.00"
                value={betOdds}
                onChange={(e) => setBetOdds(e.target.value)}
                className="bg-zinc-800 border-zinc-700 focus:border-green-500"
                data-testid="odds-input"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowAddBetDialog(false)} className="border-zinc-700 text-zinc-400">
              Cancel
            </Button>
            <Button className="bg-green-600 hover:bg-green-500" onClick={addToJournal} data-testid="confirm-add-bet">
              Add Bet
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Settle Bet Dialog */}
      <Dialog open={showSettleDialog} onOpenChange={setShowSettleDialog}>
        <DialogContent className="bg-zinc-900 border-zinc-800">
          <DialogHeader>
            <DialogTitle className="font-display text-zinc-100">Settle Bet</DialogTitle>
            <DialogDescription className="text-zinc-500">
              {selectedEntry && `${selectedEntry.home_team} vs ${selectedEntry.away_team}`}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <label className="text-sm text-zinc-400 block">Match Result</label>
            <Select value={settleResult} onValueChange={setSettleResult} data-testid="settle-result-select">
              <SelectTrigger className="bg-zinc-800 border-zinc-700">
                <SelectValue placeholder="Select result" />
              </SelectTrigger>
              <SelectContent className="bg-zinc-800 border-zinc-700">
                <SelectItem value="home">Home Win</SelectItem>
                <SelectItem value="draw">Draw</SelectItem>
                <SelectItem value="away">Away Win</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowSettleDialog(false)} className="border-zinc-700 text-zinc-400">
              Cancel
            </Button>
            <Button className="bg-green-600 hover:bg-green-500" onClick={settleBet} data-testid="confirm-settle">
              Confirm Result
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default App;
