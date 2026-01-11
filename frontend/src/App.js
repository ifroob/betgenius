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
  ChevronDown,
  Trophy,
  AlertCircle,
  Clock,
  DollarSign,
  Percent,
  Zap,
  RefreshCw,
  Info,
  Play,
  CheckCircle,
  XCircle,
  BarChart2,
  HelpCircle,
  PieChart,
} from "lucide-react";
import { PieChart as RechartsPieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip as RechartsTooltip } from "recharts";

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Slider } from "@/components/ui/slider";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
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
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

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

const FactorBreakdown = ({ breakdown, teamName }) => {
  if (!breakdown) return null;
  
  const factorNames = {
    team_offense: "Offense",
    team_defense: "Defense",
    recent_form: "Form",
    injuries: "Injuries",
    home_advantage: "Home/Away",
    head_to_head: "H2H Record",
    rest_days: "Rest",
    travel_distance: "Travel",
    referee_influence: "Referee",
    weather_conditions: "Weather",
    motivation_level: "Motivation",
    goals_differential: "Goal Diff",
    win_rate: "Win Rate"
  };
  
  return (
    <div className="space-y-2">
      <p className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-3">{teamName}</p>
      {Object.entries(breakdown).map(([key, data]) => {
        const contribution = data.contribution || 0;
        const weight = data.weight || 0;
        const isNegative = contribution < 0;
        const barWidth = Math.min(Math.abs(contribution) * 25, 100);
        
        return (
          <div key={key} className="space-y-1">
            <div className="flex justify-between items-center text-xs">
              <span className="text-zinc-400">{factorNames[key] || key}</span>
              <div className="flex items-center gap-2">
                <span className="text-zinc-500 font-mono">{weight.toFixed(0)}%</span>
                <span className={`font-mono font-semibold ${isNegative ? 'text-red-400' : 'text-green-400'}`}>
                  {contribution >= 0 ? '+' : ''}{contribution.toFixed(2)}
                </span>
              </div>
            </div>
            <div className="h-1.5 bg-zinc-800 rounded-full overflow-hidden">
              <div 
                className={`h-full ${isNegative ? 'bg-red-500/60' : 'bg-green-500/60'}`}
                style={{ width: `${barWidth}%` }}
              />
            </div>
            <p className="text-xs text-zinc-600 italic">{data.description}</p>
          </div>
        );
      })}
    </div>
  );
};

// Data source information component
const DataSourceInfo = ({ factor }) => {
  const dataSourceMap = {
    team_offense: {
      source: "Football-Data.org API",
      calculation: "Goals scored per match from historical data",
      flow: "API → Historical Matches → Statistical Average"
    },
    team_defense: {
      source: "Football-Data.org API",
      calculation: "Goals conceded per match from historical data",
      flow: "API → Historical Matches → Statistical Average"
    },
    recent_form: {
      source: "Football-Data.org API",
      calculation: "Win rate from last N matches",
      flow: "API → Recent Match Results → Win Percentage"
    },
    injuries: {
      source: "Derived from Form Data",
      calculation: "Estimated from recent performance variance",
      flow: "Form Variance → Squad Availability Estimate"
    },
    home_advantage: {
      source: "Statistical Constant",
      calculation: "Fixed home advantage boost/away penalty",
      flow: "Home: +45% boost, Away: -35% penalty"
    },
    head_to_head: {
      source: "Not Available (Neutral)",
      calculation: "Historical matchup data not in current API",
      flow: "Default: 50% neutral value"
    },
    rest_days: {
      source: "Derived from Match Count",
      calculation: "Estimated from total matches played",
      flow: "More matches → Potentially less rest"
    },
    travel_distance: {
      source: "Home/Away Status",
      calculation: "Home: minimal, Away: distance-based fatigue",
      flow: "Home: 95% fitness, Away: 65-85% based on team strength"
    },
    referee_influence: {
      source: "Not Available (Neutral)",
      calculation: "Referee data not in current API",
      flow: "Default: 50% neutral value"
    },
    weather_conditions: {
      source: "Not Available (Neutral)",
      calculation: "Weather data not in current API",
      flow: "Default: 50% neutral value"
    },
    motivation_level: {
      source: "Derived from Win/Loss Record",
      calculation: "Based on win-loss ratio and league position",
      flow: "Win Rate → Motivation Score (40-100%)"
    },
    goals_differential: {
      source: "Football-Data.org API",
      calculation: "Goals For minus Goals Against from period",
      flow: "API → Historical Matches → GF - GA"
    },
    win_rate: {
      source: "Football-Data.org API",
      calculation: "Wins divided by total matches from period",
      flow: "API → Historical Matches → Win Percentage"
    }
  };
  
  const info = dataSourceMap[factor] || {
    source: "Unknown",
    calculation: "No information available",
    flow: "N/A"
  };
  
  return (
    <div className="text-xs space-y-1 p-2 bg-zinc-800/30 rounded border border-zinc-700/30">
      <div>
        <span className="text-zinc-500">Source:</span>
        <span className="ml-2 text-zinc-300">{info.source}</span>
      </div>
      <div>
        <span className="text-zinc-500">Calculation:</span>
        <span className="ml-2 text-zinc-300">{info.calculation}</span>
      </div>
      <div>
        <span className="text-zinc-500">Data Flow:</span>
        <span className="ml-2 text-green-400 font-mono text-[10px]">{info.flow}</span>
      </div>
    </div>
  );
};

// Weights Pie Chart Visualization Component
const WeightsVisualization = ({ weights }) => {
  const [hoveredFactor, setHoveredFactor] = useState(null);
  
  const COLORS = [
    '#10b981', '#3b82f6', '#8b5cf6', '#ec4899', '#f59e0b',
    '#06b6d4', '#14b8a6', '#84cc16', '#f97316', '#6366f1',
    '#a855f7', '#ef4444', '#22c55e'
  ];
  
  const factorNames = {
    team_offense: "Offense",
    team_defense: "Defense",
    recent_form: "Recent Form",
    injuries: "Injuries",
    home_advantage: "Home Advantage",
    head_to_head: "Head-to-Head",
    rest_days: "Rest Days",
    travel_distance: "Travel",
    referee_influence: "Referee",
    weather_conditions: "Weather",
    motivation_level: "Motivation",
    goals_differential: "Goal Diff",
    win_rate: "Win Rate"
  };
  
  // Filter out period settings and zero values
  const chartData = Object.entries(weights)
    .filter(([key, value]) => !key.endsWith('_period') && value > 0)
    .map(([key, value]) => ({
      name: factorNames[key] || key,
      value: value,
      fullKey: key
    }))
    .sort((a, b) => b.value - a.value);
  
  if (chartData.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-zinc-500">
        <p>No weights assigned yet</p>
      </div>
    );
  }
  
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 mb-2">
        <PieChart className="w-4 h-4 text-green-500" />
        <h4 className="text-sm font-semibold text-zinc-300">Factor Weight Distribution</h4>
      </div>
      
      <div className="grid md:grid-cols-2 gap-4">
        {/* Pie Chart */}
        <div className="bg-zinc-800/30 rounded-lg p-4 border border-zinc-700/30">
          <ResponsiveContainer width="100%" height={250}>
            <RechartsPieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
                onMouseEnter={(_, index) => setHoveredFactor(chartData[index].fullKey)}
                onMouseLeave={() => setHoveredFactor(null)}
              >
                {chartData.map((entry, index) => (
                  <Cell 
                    key={`cell-${index}`} 
                    fill={COLORS[index % COLORS.length]}
                    opacity={hoveredFactor && hoveredFactor !== entry.fullKey ? 0.3 : 1}
                  />
                ))}
              </Pie>
              <RechartsTooltip 
                contentStyle={{ 
                  backgroundColor: '#18181b', 
                  border: '1px solid #3f3f46',
                  borderRadius: '4px',
                  color: '#e4e4e7'
                }}
              />
            </RechartsPieChart>
          </ResponsiveContainer>
        </div>
        
        {/* Factor List with Data Sources */}
        <div className="space-y-2 max-h-[250px] overflow-y-auto custom-scrollbar">
          {chartData.map((item, index) => (
            <div 
              key={item.fullKey}
              className={`p-2 rounded border transition-all ${
                hoveredFactor === item.fullKey 
                  ? 'bg-zinc-700/50 border-green-500/50' 
                  : 'bg-zinc-800/30 border-zinc-700/30'
              }`}
              onMouseEnter={() => setHoveredFactor(item.fullKey)}
              onMouseLeave={() => setHoveredFactor(null)}
            >
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-2">
                  <div 
                    className="w-3 h-3 rounded-full" 
                    style={{ backgroundColor: COLORS[index % COLORS.length] }}
                  />
                  <span className="text-sm font-medium text-zinc-200">{item.name}</span>
                </div>
                <span className="text-sm font-mono font-bold text-green-400">{item.value}%</span>
              </div>
              <DataSourceInfo factor={item.fullKey} />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

// xG Poisson Model Display Component
const PoissonModelDisplay = ({ pick }) => {
  const xgBreakdown = pick.xg_breakdown;
  if (!xgBreakdown) return null;

  return (
    <div className="space-y-6">
      {/* Model Type Badge */}
      <div className="flex items-center gap-2">
        <Badge className="bg-purple-500/20 text-purple-400 border-purple-500/40">
          xG POISSON MODEL
        </Badge>
        <span className="text-xs text-zinc-500">Advanced statistical prediction using Expected Goals</span>
      </div>

      {/* Poisson Formula */}
      <div className="bg-gradient-to-br from-purple-500/10 to-transparent border border-purple-500/30 rounded-lg p-4">
        <h5 className="text-xs font-semibold text-purple-400 uppercase tracking-wider mb-3 flex items-center gap-2">
          <HelpCircle className="w-4 h-4" />
          Poisson Formula
        </h5>
        <div className="space-y-3">
          <div className="bg-zinc-900/50 border border-zinc-700 rounded p-3 font-mono text-sm text-zinc-200 text-center">
            P(k goals) = (e<sup>-λ</sup> × λ<sup>k</sup>) / k!
          </div>
          <p className="text-xs text-zinc-400 italic">
            Where λ (lambda) is the expected number of goals. This formula calculates the probability of scoring exactly k goals.
          </p>
        </div>
      </div>

      {/* Lambda Calculations */}
      <div className="grid md:grid-cols-2 gap-4">
        <div className="bg-gradient-to-br from-blue-500/10 to-transparent border border-blue-500/30 rounded-lg p-4">
          <h5 className="text-xs font-semibold text-blue-400 uppercase tracking-wider mb-3">
            {pick.home_team} Expected Goals (λ)
          </h5>
          <div className="space-y-2 text-xs">
            <div className="flex justify-between items-center">
              <span className="text-zinc-400">Lambda (λ):</span>
              <span className="font-mono font-bold text-2xl text-blue-400">{pick.projected_home_score}</span>
            </div>
            <div className="border-t border-zinc-700/50 pt-2 mt-2">
              <p className="text-zinc-500 font-semibold mb-2">Calculation:</p>
              <div className="space-y-1 text-zinc-400">
                <div className="flex justify-between">
                  <span>League Avg (Home):</span>
                  <span className="font-mono">{xgBreakdown.league_averages?.home || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span>Attack Strength:</span>
                  <span className="font-mono text-green-400">{xgBreakdown.home_team?.attack_strength || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span>Opponent Def Strength:</span>
                  <span className="font-mono text-red-400">{xgBreakdown.away_team?.defense_strength || 0}</span>
                </div>
              </div>
              <div className="mt-2 pt-2 border-t border-zinc-700/50 bg-zinc-900/50 p-2 rounded">
                <span className="text-zinc-500">λ_home = </span>
                <span className="font-mono text-zinc-200">
                  {xgBreakdown.league_averages?.home || 0} × {xgBreakdown.home_team?.attack_strength || 0} × {xgBreakdown.away_team?.defense_strength || 0}
                </span>
              </div>
            </div>
            <div className="mt-3 text-xs text-zinc-500 italic">
              Data: {xgBreakdown.home_team?.matches || 0} matches analyzed
            </div>
          </div>
        </div>

        <div className="bg-gradient-to-br from-orange-500/10 to-transparent border border-orange-500/30 rounded-lg p-4">
          <h5 className="text-xs font-semibold text-orange-400 uppercase tracking-wider mb-3">
            {pick.away_team} Expected Goals (λ)
          </h5>
          <div className="space-y-2 text-xs">
            <div className="flex justify-between items-center">
              <span className="text-zinc-400">Lambda (λ):</span>
              <span className="font-mono font-bold text-2xl text-orange-400">{pick.projected_away_score}</span>
            </div>
            <div className="border-t border-zinc-700/50 pt-2 mt-2">
              <p className="text-zinc-500 font-semibold mb-2">Calculation:</p>
              <div className="space-y-1 text-zinc-400">
                <div className="flex justify-between">
                  <span>League Avg (Away):</span>
                  <span className="font-mono">{xgBreakdown.league_averages?.away || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span>Attack Strength:</span>
                  <span className="font-mono text-green-400">{xgBreakdown.away_team?.attack_strength || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span>Opponent Def Strength:</span>
                  <span className="font-mono text-red-400">{xgBreakdown.home_team?.defense_strength || 0}</span>
                </div>
              </div>
              <div className="mt-2 pt-2 border-t border-zinc-700/50 bg-zinc-900/50 p-2 rounded">
                <span className="text-zinc-500">λ_away = </span>
                <span className="font-mono text-zinc-200">
                  {xgBreakdown.league_averages?.away || 0} × {xgBreakdown.away_team?.attack_strength || 0} × {xgBreakdown.home_team?.defense_strength || 0}
                </span>
              </div>
            </div>
            <div className="mt-3 text-xs text-zinc-500 italic">
              Data: {xgBreakdown.away_team?.matches || 0} matches analyzed
            </div>
          </div>
        </div>
      </div>

      {/* Step-by-Step Calculation */}
      {xgBreakdown.calculation_steps && (
        <div className="bg-zinc-800/50 border border-zinc-700/50 rounded-lg p-4">
          <h5 className="text-xs font-semibold text-zinc-300 uppercase tracking-wider mb-3">
            Step-by-Step Calculation Process
          </h5>
          <div className="space-y-2">
            {Object.entries(xgBreakdown.calculation_steps).map(([step, description]) => (
              <div key={step} className="flex gap-3 text-xs">
                <span className="text-green-500 font-semibold min-w-[60px]">{step.replace('step_', 'Step ')}:</span>
                <span className="text-zinc-400 font-mono">{description}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Team xG Statistics */}
      <div className="grid md:grid-cols-2 gap-4">
        <div className="bg-zinc-800/30 border border-zinc-700/30 rounded-lg p-4">
          <h5 className="text-xs font-semibold text-blue-400 uppercase tracking-wider mb-3">
            {pick.home_team} xG Stats
          </h5>
          <div className="space-y-2 text-xs">
            <div className="flex justify-between">
              <span className="text-zinc-400">xG per match:</span>
              <span className="font-mono text-green-400">{xgBreakdown.home_team?.xG_per_match || 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-zinc-400">xGA per match:</span>
              <span className="font-mono text-red-400">{xgBreakdown.home_team?.xGA_per_match || 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-zinc-400">Attack strength:</span>
              <span className="font-mono text-blue-400">{xgBreakdown.home_team?.attack_strength || 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-zinc-400">Defense strength:</span>
              <span className="font-mono text-blue-400">{xgBreakdown.home_team?.defense_strength || 0}</span>
            </div>
          </div>
        </div>

        <div className="bg-zinc-800/30 border border-zinc-700/30 rounded-lg p-4">
          <h5 className="text-xs font-semibold text-orange-400 uppercase tracking-wider mb-3">
            {pick.away_team} xG Stats
          </h5>
          <div className="space-y-2 text-xs">
            <div className="flex justify-between">
              <span className="text-zinc-400">xG per match:</span>
              <span className="font-mono text-green-400">{xgBreakdown.away_team?.xG_per_match || 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-zinc-400">xGA per match:</span>
              <span className="font-mono text-red-400">{xgBreakdown.away_team?.xGA_per_match || 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-zinc-400">Attack strength:</span>
              <span className="font-mono text-orange-400">{xgBreakdown.away_team?.attack_strength || 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-zinc-400">Defense strength:</span>
              <span className="font-mono text-orange-400">{xgBreakdown.away_team?.defense_strength || 0}</span>
            </div>
          </div>
        </div>
      </div>

      {/* League Context */}
      <div className="bg-gradient-to-br from-green-500/10 to-transparent border border-green-500/30 rounded-lg p-4">
        <h5 className="text-xs font-semibold text-green-400 uppercase tracking-wider mb-3">
          League Context (EPL Averages)
        </h5>
        <div className="grid grid-cols-3 gap-4 text-xs text-center">
          <div>
            <p className="text-zinc-500 mb-1">Overall</p>
            <p className="font-mono text-lg text-zinc-200">{xgBreakdown.league_averages?.overall || 0}</p>
            <p className="text-zinc-600 text-xs">goals/match</p>
          </div>
          <div>
            <p className="text-zinc-500 mb-1">Home Teams</p>
            <p className="font-mono text-lg text-blue-400">{xgBreakdown.league_averages?.home || 0}</p>
            <p className="text-zinc-600 text-xs">goals/match</p>
          </div>
          <div>
            <p className="text-zinc-500 mb-1">Away Teams</p>
            <p className="font-mono text-lg text-orange-400">{xgBreakdown.league_averages?.away || 0}</p>
            <p className="text-zinc-600 text-xs">goals/match</p>
          </div>
        </div>
      </div>

      {/* Outcome Probabilities from Poisson */}
      <div className="bg-zinc-800/50 border border-zinc-700/50 rounded p-4">
        <h5 className="text-xs font-semibold text-zinc-300 uppercase tracking-wider mb-3">
          Poisson Outcome Probabilities
        </h5>
        <div className="grid grid-cols-3 gap-4 text-xs">
          <div className="text-center p-3 bg-blue-500/10 rounded border border-blue-500/30">
            <p className="text-zinc-500 mb-2">HOME WIN</p>
            <p className="font-mono text-2xl text-blue-400 mb-1">{pick.all_probabilities?.home || 0}%</p>
            <p className="text-zinc-600 text-xs">vs Market: {(100 / pick.all_market_odds?.home).toFixed(1)}%</p>
          </div>
          <div className="text-center p-3 bg-zinc-500/10 rounded border border-zinc-500/30">
            <p className="text-zinc-500 mb-2">DRAW</p>
            <p className="font-mono text-2xl text-zinc-400 mb-1">{pick.all_probabilities?.draw || 0}%</p>
            <p className="text-zinc-600 text-xs">vs Market: {(100 / pick.all_market_odds?.draw).toFixed(1)}%</p>
          </div>
          <div className="text-center p-3 bg-orange-500/10 rounded border border-orange-500/30">
            <p className="text-zinc-500 mb-2">AWAY WIN</p>
            <p className="font-mono text-2xl text-orange-400 mb-1">{pick.all_probabilities?.away || 0}%</p>
            <p className="text-zinc-600 text-xs">vs Market: {(100 / pick.all_market_odds?.away).toFixed(1)}%</p>
          </div>
        </div>
        <p className="text-xs text-zinc-500 italic mt-3 text-center">
          Calculated by evaluating all possible score combinations using Poisson distribution
        </p>
      </div>
    </div>
  );
};

// Tooltip wrapper for numbers with explanations
const TooltipNumber = ({ value, tooltip, className = "" }) => (
  <TooltipProvider delayDuration={200}>
    <Tooltip>
      <TooltipTrigger asChild>
        <span className={`cursor-help border-b border-dotted border-zinc-600 ${className}`}>
          {value}
        </span>
      </TooltipTrigger>
      <TooltipContent className="bg-zinc-800 border-zinc-700 max-w-xs">
        <p className="text-xs">{tooltip}</p>
      </TooltipContent>
    </Tooltip>
  </TooltipProvider>
);

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
    team_offense: 0,
    team_defense: 0,
    recent_form: 0,
    injuries: 0,
    home_advantage: 0
  });
  
  // Matchday range state
  const [matchdayRange, setMatchdayRange] = useState({
    min_matchday: 1,
    max_matchday: 38,
    available_matchdays: 0
  });
  
  // Expanded pick reasoning state
  const [expandedPick, setExpandedPick] = useState(null);

  // Dialog states
  const [showAddBetDialog, setShowAddBetDialog] = useState(false);
  const [selectedPick, setSelectedPick] = useState(null);
  const [betStake, setBetStake] = useState("");
  const [betOdds, setBetOdds] = useState("");

  const [showSettleDialog, setShowSettleDialog] = useState(false);
  const [selectedEntry, setSelectedEntry] = useState(null);
  const [settleResult, setSettleResult] = useState("");

  // Simulation states
  const [simulationResults, setSimulationResults] = useState(null);
  const [simulationLoading, setSimulationLoading] = useState(false);
  const [selectedSimModel, setSelectedSimModel] = useState("");

  // Team details modal states
  const [showTeamDetailsDialog, setShowTeamDetailsDialog] = useState(false);
  const [selectedTeamName, setSelectedTeamName] = useState(null);
  const [teamDetails, setTeamDetails] = useState(null);
  const [teamDetailsLoading, setTeamDetailsLoading] = useState(false);

  // Matchday states
  const [matchdays, setMatchdays] = useState([]);
  const [expandedMatchday, setExpandedMatchday] = useState(null);
  const [showOnlyUpcoming, setShowOnlyUpcoming] = useState(true);
  const [selectedMatchdayForSim, setSelectedMatchdayForSim] = useState(null);

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

  // Fetch team details
  const fetchTeamDetails = async (teamName) => {
    setTeamDetailsLoading(true);
    setShowTeamDetailsDialog(true);
    setSelectedTeamName(teamName);
    try {
      const res = await axios.get(`${API}/teams/${encodeURIComponent(teamName)}`);
      setTeamDetails(res.data);
    } catch (err) {
      console.error("Error fetching team details:", err);
      toast.error("Failed to load team details");
      setShowTeamDetailsDialog(false);
    }
    setTeamDetailsLoading(false);
  };

  // Handle team name click
  const handleTeamClick = (teamName) => {
    fetchTeamDetails(teamName);
  };

  // Fetch matchdays
  const fetchMatchdays = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/matchdays`);
      setMatchdays(res.data.matchdays || []);
    } catch (err) {
      console.error("Error fetching matchdays:", err);
    }
  }, []);
  
  // Fetch matchday range
  const fetchMatchdayRange = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/matchday-range`);
      setMatchdayRange(res.data);
    } catch (err) {
      console.error("Error fetching matchday range:", err);
    }
  }, []);

  useEffect(() => {
    fetchData();
    fetchMatchdays();
    fetchMatchdayRange();
  }, [fetchData, fetchMatchdays, fetchMatchdayRange]);

  // Generate picks for selected model
  const generatePicks = async (modelId) => {
    setLoading(true);
    try {
      const res = await axios.post(`${API}/picks/generate?model_id=${modelId}`);
      setPicks(res.data);
      setSelectedModel(modelId);
      
      // Determine current matchday and set it as expanded by default
      if (res.data.length > 0) {
        const picksWithMatchday = res.data.filter(p => p.matchday);
        if (picksWithMatchday.length > 0) {
          const minMatchday = Math.min(...picksWithMatchday.map(p => p.matchday));
          setExpandedMatchday(minMatchday);
        }
      }
      
      toast.success("Picks generated!");
    } catch (err) {
      toast.error("Failed to generate picks");
    }
    setLoading(false);
  };

  // Generate picks for a specific matchday
  const generateMatchdayPicks = async (matchdayNum, modelId) => {
    if (!modelId) {
      toast.error("Please select a model first");
      return;
    }
    
    setLoading(true);
    try {
      const res = await axios.post(`${API}/matchdays/${matchdayNum}/picks?model_id=${modelId}`);
      
      // Merge with existing picks, replacing picks for this matchday
      const otherPicks = picks.filter(p => p.matchday !== matchdayNum);
      const allPicks = [...otherPicks, ...res.data];
      
      setPicks(allPicks);
      setExpandedMatchday(matchdayNum);
      toast.success(`Generated ${res.data.length} picks for Matchday ${matchdayNum}`);
    } catch (err) {
      toast.error(`Failed to generate picks for Matchday ${matchdayNum}`);
      console.error(err);
    }
    setLoading(false);
  };

  // Create new model
  const createModel = async () => {
    if (!newModelName.trim()) {
      toast.error("Please enter a model name");
      return;
    }
    
    if (totalWeights > 100) {
      toast.error(`Total weight cannot exceed 100% (currently ${totalWeights}%)`);
      return;
    }
    
    if (totalWeights === 0) {
      toast.error("Please assign at least some weight to factors");
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
      setWeights({ 
        team_offense: 0,
        team_defense: 0,
        recent_form: 0,
        injuries: 0,
        home_advantage: 0
      });
      fetchData();
    } catch (err) {
      toast.error("Failed to create model");
    }
  };

  // Reset all factors to 0
  const resetAllFactors = () => {
    setWeights({
      team_offense: 0,
      team_defense: 0,
      recent_form: 0,
      injuries: 0,
      home_advantage: 0
    });
    toast.success("All factors reset to 0%");
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
        odds_taken: parseFloat(betOdds),
        predicted_outcome: selectedPick.predicted_outcome
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

  const runSimulation = async (modelId, matchdayFilter = null) => {
    if (!modelId) {
      toast.error("Please select a model");
      return;
    }

    setSimulationLoading(true);
    try {
      const payload = { model_id: modelId };
      if (matchdayFilter) {
        payload.matchday = matchdayFilter;
      }
      
      const response = await axios.post(`${API}/simulate`, payload);
      setSimulationResults(response.data);
      toast.success(`Simulation complete: ${response.data.accuracy_percentage}% accuracy`);
    } catch (err) {
      toast.error("Failed to run simulation");
      console.error(err);
    } finally {
      setSimulationLoading(false);
    }
  };

  // Calculate total weights (excluding period settings)
  const totalWeights = Object.entries(weights)
    .filter(([key]) => !key.endsWith('_period'))
    .reduce((sum, [, value]) => sum + value, 0);
  
  // Check if total weight exceeds 100
  const isWeightExceeded = totalWeights > 100;
  const weightWarningMessage = isWeightExceeded 
    ? `Total weight is ${totalWeights}% (exceeds 100%)` 
    : totalWeights === 100 
    ? "Perfect! Total weight is 100%" 
    : `${100 - totalWeights}% remaining`;

  // Helper function to group picks by matchday
  const groupPicksByMatchday = () => {
    const grouped = {};
    picks.forEach(pick => {
      const matchday = pick.matchday || 0;
      if (!grouped[matchday]) {
        grouped[matchday] = [];
      }
      grouped[matchday].push(pick);
    });
    
    // Sort picks within each matchday by confidence
    Object.keys(grouped).forEach(matchday => {
      grouped[matchday].sort((a, b) => b.confidence_score - a.confidence_score);
    });
    
    return grouped;
  };

  // Get current and next matchday
  const getCurrentAndNextMatchday = () => {
    if (picks.length === 0) return { current: null, next: null };
    
    const picksWithMatchday = picks.filter(p => p.matchday);
    if (picksWithMatchday.length === 0) return { current: null, next: null };
    
    const matchdayNumbers = [...new Set(picksWithMatchday.map(p => p.matchday))].sort((a, b) => a - b);
    
    return {
      current: matchdayNumbers[0] || null,
      next: matchdayNumbers[1] || null
    };
  };

  const groupedPicks = groupPicksByMatchday();
  const { current: currentMatchday, next: nextMatchday } = getCurrentAndNextMatchday();

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
              <Button
                size="sm"
                variant="outline"
                className="border-zinc-700 text-zinc-400 hover:text-green-500 hover:border-green-500/50"
                onClick={refreshFixtures}
                disabled={loading}
                data-testid="refresh-fixtures-btn"
              >
                <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                New Fixtures
              </Button>
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
            <TabsTrigger value="simulation" className="data-[state=active]:bg-green-500/20 data-[state=active]:text-green-500" data-testid="tab-simulation">
              <Play className="w-4 h-4 mr-2" />
              Simulation
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
                      <div className="flex-1">
                        <p className="text-sm font-medium text-zinc-200">
                          <button
                            onClick={() => handleTeamClick(game.home_team)}
                            className="text-green-400 hover:text-green-300 hover:underline cursor-pointer transition-colors"
                            data-testid={`team-link-${game.home_team.replace(/\s+/g, '-')}`}
                          >
                            {game.home_team}
                          </button>
                          {' vs '}
                          <button
                            onClick={() => handleTeamClick(game.away_team)}
                            className="text-green-400 hover:text-green-300 hover:underline cursor-pointer transition-colors"
                            data-testid={`team-link-${game.away_team.replace(/\s+/g, '-')}`}
                          >
                            {game.away_team}
                          </button>
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
                            <button
                              onClick={() => handleTeamClick(entry.home_team)}
                              className="text-green-400 hover:text-green-300 hover:underline cursor-pointer transition-colors"
                            >
                              {entry.home_team}
                            </button>
                            {' vs '}
                            <button
                              onClick={() => handleTeamClick(entry.away_team)}
                              className="text-green-400 hover:text-green-300 hover:underline cursor-pointer transition-colors"
                            >
                              {entry.away_team}
                            </button>
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

                  {/* Reset All Factors Button */}
                  <Button
                    variant="outline"
                    className="w-full border-red-500/50 text-red-400 hover:bg-red-500/10 hover:text-red-300"
                    onClick={resetAllFactors}
                    data-testid="reset-all-factors-btn"
                  >
                    <RefreshCw className="w-4 h-4 mr-2" />
                    RESET ALL FACTORS
                  </Button>

                  <div className="space-y-5">
                    <div className="text-xs font-semibold text-green-500 uppercase tracking-wider mb-2 flex items-center gap-2">
                      <div className="h-px flex-1 bg-green-500/30"></div>
                      Core Factors
                      <div className="h-px flex-1 bg-green-500/30"></div>
                    </div>
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

                  {/* Weights Visualization */}
                  <Card className="bg-zinc-800/50 border-zinc-700">
                    <CardContent className="p-4">
                      <WeightsVisualization weights={weights} />
                    </CardContent>
                  </Card>

                  <div className={`flex items-center justify-between p-3 rounded-sm border ${
                    isWeightExceeded 
                      ? 'bg-red-500/10 border-red-500/50' 
                      : totalWeights === 100 
                      ? 'bg-green-500/10 border-green-500/50' 
                      : 'bg-zinc-800/50 border-zinc-700/50'
                  }`}>
                    <div>
                      <span className="text-sm text-zinc-400">Total Weight</span>
                      <p className="text-xs text-zinc-500 mt-0.5">{weightWarningMessage}</p>
                    </div>
                    <span className={`font-mono font-bold text-lg ${
                      isWeightExceeded 
                        ? 'text-red-500' 
                        : totalWeights === 100 
                        ? 'text-green-500' 
                        : 'text-yellow-500'
                    }`}>
                      {totalWeights}%
                    </span>
                  </div>

                  <Button
                    className={`w-full font-bold uppercase tracking-wider ${
                      isWeightExceeded 
                        ? 'bg-red-600 hover:bg-red-500 cursor-not-allowed' 
                        : 'bg-green-600 hover:bg-green-500'
                    } text-white`}
                    onClick={createModel}
                    disabled={isWeightExceeded}
                    data-testid="create-model-btn"
                  >
                    <Plus className="w-4 h-4 mr-2" />
                    {isWeightExceeded ? 'Weight Exceeds 100%' : 'Create Model'}
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
            {/* Model Selector and Filters */}
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
                    <>
                      <Badge className="bg-green-500/20 text-green-500 border-green-500/40">
                        {picks.length} picks generated
                      </Badge>
                      
                      {/* Filter Toggle */}
                      <Button
                        size="sm"
                        variant={showOnlyUpcoming ? "default" : "outline"}
                        className={showOnlyUpcoming ? "bg-green-600 hover:bg-green-500 text-white" : "border-zinc-700 text-zinc-400"}
                        onClick={() => setShowOnlyUpcoming(!showOnlyUpcoming)}
                      >
                        {showOnlyUpcoming ? "Showing Upcoming" : "Show All"}
                      </Button>
                    </>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Matchday Information */}
            {matchdays.length > 0 && selectedModel && (
              <Card className="bg-zinc-900/50 border-zinc-800">
                <CardHeader>
                  <CardTitle className="text-lg font-display text-zinc-100">Match Days</CardTitle>
                  <CardDescription className="text-zinc-500">
                    Generate picks for specific matchdays or view all matches organized by gameweek
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
                    {matchdays
                      .filter(md => !showOnlyUpcoming || md.upcoming_games > 0)
                      .map((md) => (
                        <Card 
                          key={md.matchday} 
                          className={`bg-zinc-800/50 border-zinc-700 cursor-pointer hover:border-green-500/50 transition-colors ${
                            expandedMatchday === md.matchday ? 'border-green-500' : ''
                          }`}
                          onClick={() => setExpandedMatchday(expandedMatchday === md.matchday ? null : md.matchday)}
                        >
                          <CardContent className="p-3">
                            <div className="flex items-center justify-between mb-2">
                              <p className="text-xs text-zinc-500 uppercase">MD {md.matchday}</p>
                              {md.upcoming_games > 0 && (
                                <Badge className="bg-green-500/20 text-green-400 border-green-500/40 text-xs px-1">
                                  Live
                                </Badge>
                              )}
                            </div>
                            <p className="text-xl font-bold font-mono text-zinc-200">{md.total_games}</p>
                            <p className="text-xs text-zinc-500 mt-1">
                              {md.upcoming_games} upcoming
                            </p>
                            {md.upcoming_games > 0 && (
                              <Button
                                size="sm"
                                className="w-full mt-2 bg-green-600 hover:bg-green-500 text-white text-xs"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  generateMatchdayPicks(md.matchday, selectedModel);
                                }}
                                disabled={loading}
                              >
                                Generate Picks
                              </Button>
                            )}
                          </CardContent>
                        </Card>
                      ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Picks Display by Matchday */}
            {picks.length > 0 ? (
              <div className="space-y-4">
                {Object.keys(groupedPicks)
                  .sort((a, b) => parseInt(a) - parseInt(b))
                  .filter(matchdayNum => {
                    if (!showOnlyUpcoming) return true;
                    // Check if this matchday has any upcoming games
                    const matchdayInfo = matchdays.find(md => md.matchday === parseInt(matchdayNum));
                    return matchdayInfo && matchdayInfo.upcoming_games > 0;
                  })
                  .map((matchdayNum) => {
                    const matchdayPicks = groupedPicks[matchdayNum];
                    const matchdayInfo = matchdays.find(md => md.matchday === parseInt(matchdayNum));
                    const isExpanded = expandedMatchday === parseInt(matchdayNum);
                    const isCurrent = matchdayInfo && matchdayInfo.upcoming_games > 0;

                    return (
                      <Card key={matchdayNum} className="bg-zinc-900/50 border-zinc-800 overflow-hidden">
                        <CardHeader 
                          className="cursor-pointer hover:bg-zinc-800/50 transition-colors"
                          onClick={() => setExpandedMatchday(isExpanded ? null : parseInt(matchdayNum))}
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                              <div className="flex items-center gap-2">
                                <CardTitle className="text-lg font-display text-zinc-100">
                                  Matchday {matchdayNum}
                                </CardTitle>
                                {isCurrent && (
                                  <Badge className="bg-green-500/20 text-green-500 border-green-500/40 text-xs">
                                    Current
                                  </Badge>
                                )}
                              </div>
                              <CardDescription className="text-zinc-500">
                                {matchdayPicks.length} {matchdayPicks.length === 1 ? 'match' : 'matches'} • Sorted by confidence
                              </CardDescription>
                            </div>
                            <div className="flex items-center gap-2">
                              {matchdayInfo && matchdayInfo.upcoming_games > 0 && (
                                <Button
                                  size="sm"
                                  variant="ghost"
                                  className="text-green-500 hover:text-green-400 hover:bg-green-500/10"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    generateMatchdayPicks(parseInt(matchdayNum), selectedModel);
                                  }}
                                  disabled={loading}
                                >
                                  <RefreshCw className={`w-4 h-4 mr-1 ${loading ? 'animate-spin' : ''}`} />
                                  Regenerate
                                </Button>
                              )}
                              {isExpanded ? (
                                <ChevronDown className="w-5 h-5 text-zinc-500" />
                              ) : (
                                <ChevronRight className="w-5 h-5 text-zinc-500" />
                              )}
                            </div>
                          </div>
                        </CardHeader>
                        
                        {isExpanded && (
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
                                  {matchdayPicks.map((pick) => (
                          <>
                            <tr key={pick.id} className="border-b border-zinc-800/50 table-row-hover">
                              <td className="p-4">
                                <div className="space-y-1">
                                  <p className="text-sm font-medium text-zinc-200">
                                    <button
                                      onClick={() => handleTeamClick(pick.home_team)}
                                      className="text-green-400 hover:text-green-300 hover:underline cursor-pointer transition-colors"
                                      data-testid={`team-link-${pick.home_team}`}
                                    >
                                      {pick.home_team}
                                    </button>
                                    {' vs '}
                                    <button
                                      onClick={() => handleTeamClick(pick.away_team)}
                                      className="text-green-400 hover:text-green-300 hover:underline cursor-pointer transition-colors"
                                      data-testid={`team-link-${pick.away_team}`}
                                    >
                                      {pick.away_team}
                                    </button>
                                  </p>
                                  <div className="flex items-center gap-2">
                                    <p className="text-xs text-zinc-500">{pick.match_date}</p>
                                    {pick.model_type === "xg_poisson" && (
                                      <Badge className="bg-purple-500/20 text-purple-400 border-purple-500/40 text-xs">
                                        xG Poisson
                                      </Badge>
                                    )}
                                  </div>
                                </div>
                              </td>
                              <td className="p-4 text-center">
                                <TooltipProvider delayDuration={200}>
                                  <Tooltip>
                                    <TooltipTrigger asChild>
                                      <span className="font-mono text-sm text-zinc-300 cursor-help border-b border-dotted border-zinc-600">
                                        {pick.projected_home_score} - {pick.projected_away_score}
                                      </span>
                                    </TooltipTrigger>
                                    <TooltipContent className="bg-zinc-800 border-zinc-700 max-w-sm">
                                      <div className="space-y-1">
                                        {pick.model_type === "xg_poisson" ? (
                                          <>
                                            <p className="font-semibold text-purple-400">xG Poisson Expected Goals (λ)</p>
                                            <p className="text-xs">Home λ: {pick.projected_home_score}</p>
                                            <p className="text-xs">Away λ: {pick.projected_away_score}</p>
                                            <p className="text-xs text-zinc-400 mt-2 italic">
                                              Lambda values represent expected goals calculated from team xG statistics and league averages
                                            </p>
                                          </>
                                        ) : (
                                          <>
                                            <p className="font-semibold text-green-400">Projected Score Calculation</p>
                                            <p className="text-xs">Base: 1.5 goals/team (EPL average)</p>
                                            <p className="text-xs">Home: 1.5 {pick.calculation_summary?.home_adjustments >= 0 ? '+' : ''}{pick.calculation_summary?.home_adjustments?.toFixed(2) || '0.00'} = {pick.projected_home_score}</p>
                                            <p className="text-xs">Away: 1.5 {pick.calculation_summary?.away_adjustments >= 0 ? '+' : ''}{pick.calculation_summary?.away_adjustments?.toFixed(2) || '0.00'} = {pick.projected_away_score}</p>
                                            <p className="text-xs text-zinc-400 mt-2 italic">Adjustments from all weighted factors (offense, defense, form, etc.)</p>
                                          </>
                                        )}
                                      </div>
                                    </TooltipContent>
                                  </Tooltip>
                                </TooltipProvider>
                              </td>
                              <td className="p-4 text-center">
                                <OutcomeBadge outcome={pick.predicted_outcome} />
                              </td>
                              <td className="p-4 text-center">
                                <TooltipProvider delayDuration={200}>
                                  <Tooltip>
                                    <TooltipTrigger asChild>
                                      <span className="font-mono text-sm text-green-400 cursor-help border-b border-dotted border-green-600">
                                        {pick.market_odds.toFixed(2)}
                                      </span>
                                    </TooltipTrigger>
                                    <TooltipContent className="bg-zinc-800 border-zinc-700 max-w-xs">
                                      <div className="space-y-1">
                                        <p className="font-semibold text-green-400">Market Odds</p>
                                        <p className="text-xs">Current bookmaker odds for {pick.predicted_outcome.toUpperCase()}</p>
                                        <p className="text-xs text-zinc-400 mt-2">All odds:</p>
                                        <p className="text-xs">Home: {pick.all_market_odds?.home?.toFixed(2)}</p>
                                        <p className="text-xs">Draw: {pick.all_market_odds?.draw?.toFixed(2)}</p>
                                        <p className="text-xs">Away: {pick.all_market_odds?.away?.toFixed(2)}</p>
                                      </div>
                                    </TooltipContent>
                                  </Tooltip>
                                </TooltipProvider>
                              </td>
                              <td className="p-4 text-center">
                                <TooltipProvider delayDuration={200}>
                                  <Tooltip>
                                    <TooltipTrigger asChild>
                                      <span className={`font-mono text-sm cursor-help border-b border-dotted ${pick.edge_percentage > 0 ? 'text-green-500 border-green-600' : 'text-red-500 border-red-600'}`}>
                                        {pick.edge_percentage > 0 ? '+' : ''}{pick.edge_percentage}%
                                      </span>
                                    </TooltipTrigger>
                                    <TooltipContent className="bg-zinc-800 border-zinc-700 max-w-xs">
                                      <div className="space-y-1">
                                        <p className="font-semibold text-green-400">Edge Percentage</p>
                                        <p className="text-xs">Model prob: {pick.model_probability}%</p>
                                        <p className="text-xs">Market prob: {pick.market_probability}%</p>
                                        <p className="text-xs text-zinc-400 mt-2 italic">Edge = (Model - Market) / Market × 100</p>
                                        <p className="text-xs text-zinc-400">Positive edge suggests value bet opportunity</p>
                                      </div>
                                    </TooltipContent>
                                  </Tooltip>
                                </TooltipProvider>
                              </td>
                              <td className="p-4 text-center">
                                <TooltipProvider delayDuration={200}>
                                  <Tooltip>
                                    <TooltipTrigger asChild>
                                      <span className="cursor-help">
                                        <ConfidenceBadge score={pick.confidence_score} />
                                      </span>
                                    </TooltipTrigger>
                                    <TooltipContent className="bg-zinc-800 border-zinc-700 max-w-sm">
                                      <div className="space-y-1">
                                        <p className="font-semibold text-green-400">Confidence Score (1-10)</p>
                                        <p className="text-xs font-semibold">{pick.confidence_explanation?.strength || 'N/A'}</p>
                                        <p className="text-xs text-zinc-300">{pick.confidence_explanation?.reasoning || 'Based on edge and probability'}</p>
                                        <div className="text-xs text-zinc-400 mt-2 space-y-0.5">
                                          <p>• Edge: {pick.confidence_explanation?.edge?.toFixed(1)}%</p>
                                          <p>• Score diff: {pick.confidence_explanation?.score_differential?.toFixed(2)}</p>
                                        </div>
                                      </div>
                                    </TooltipContent>
                                  </Tooltip>
                                </TooltipProvider>
                              </td>
                              <td className="p-4 text-right">
                                <div className="flex items-center justify-end gap-2">
                                  <Button
                                    size="sm"
                                    variant="ghost"
                                    className="text-zinc-400 hover:text-green-500 hover:bg-green-500/10"
                                    onClick={() => setExpandedPick(expandedPick === pick.id ? null : pick.id)}
                                    data-testid={`expand-reasoning-${pick.id}`}
                                  >
                                    {expandedPick === pick.id ? <ChevronDown className="w-4 h-4" /> : <Info className="w-4 h-4" />}
                                  </Button>
                                  <Button
                                    size="sm"
                                    className="bg-green-600 hover:bg-green-500 text-white text-xs"
                                    onClick={() => { setSelectedPick(pick); setBetOdds(pick.market_odds.toString()); setShowAddBetDialog(true); }}
                                    data-testid={`add-bet-${pick.id}`}
                                  >
                                    Add to Journal
                                  </Button>
                                </div>
                              </td>
                            </tr>
                            {expandedPick === pick.id && (
                              <tr key={`${pick.id}-reasoning`} className="border-b border-zinc-800/50 bg-zinc-900/80">
                                <td colSpan="7" className="p-6">
                                  <div className="space-y-6">
                                    {/* Header */}
                                    <div className="flex items-center justify-between">
                                      <h4 className="text-sm font-semibold text-zinc-100 uppercase tracking-wider flex items-center gap-2">
                                        <Info className="w-4 h-4 text-green-500" />
                                        Pick Reasoning & Calculation Details
                                      </h4>
                                      <div className="flex items-center gap-4 text-xs">
                                        <div>
                                          <span className="text-zinc-500">Model Probability: </span>
                                          <span className="font-mono font-semibold text-green-400">{pick.model_probability}%</span>
                                        </div>
                                        <div>
                                          <span className="text-zinc-500">Market Probability: </span>
                                          <span className="font-mono font-semibold text-zinc-400">{pick.market_probability}%</span>
                                        </div>
                                      </div>
                                    </div>

                                    {/* Conditional Display: xG Poisson Model vs Regular Model */}
                                    {pick.model_type === "xg_poisson" ? (
                                      <PoissonModelDisplay pick={pick} />
                                    ) : (
                                      <>
                                        {/* Regular Model Display */}
                                        {/* Calculation Summary Section */}
                                        <div className="grid md:grid-cols-2 gap-4">
                                      <div className="bg-gradient-to-br from-green-500/10 to-transparent border border-green-500/30 rounded-lg p-4">
                                        <h5 className="text-xs font-semibold text-green-400 uppercase tracking-wider mb-3">Score Calculation</h5>
                                        <div className="space-y-2 text-xs text-zinc-300">
                                          <div className="flex justify-between">
                                            <span className="text-zinc-500">Base Score (EPL avg):</span>
                                            <span className="font-mono">1.50</span>
                                          </div>
                                          <div className="flex justify-between border-t border-zinc-700/50 pt-2">
                                            <span className="text-blue-400">{pick.home_team} Adjustments:</span>
                                            <span className="font-mono text-blue-400">
                                              {pick.calculation_summary?.home_adjustments >= 0 ? '+' : ''}{pick.calculation_summary?.home_adjustments?.toFixed(3) || '0.000'}
                                            </span>
                                          </div>
                                          <div className="flex justify-between font-semibold text-blue-400">
                                            <span>{pick.home_team} Final Score:</span>
                                            <span className="font-mono">{pick.projected_home_score}</span>
                                          </div>
                                          <div className="flex justify-between border-t border-zinc-700/50 pt-2">
                                            <span className="text-orange-400">{pick.away_team} Adjustments:</span>
                                            <span className="font-mono text-orange-400">
                                              {pick.calculation_summary?.away_adjustments >= 0 ? '+' : ''}{pick.calculation_summary?.away_adjustments?.toFixed(3) || '0.000'}
                                            </span>
                                          </div>
                                          <div className="flex justify-between font-semibold text-orange-400">
                                            <span>{pick.away_team} Final Score:</span>
                                            <span className="font-mono">{pick.projected_away_score}</span>
                                          </div>
                                        </div>
                                        <p className="text-xs text-zinc-500 italic mt-3">
                                          Adjustments come from weighted factors: offense, defense, form, injuries, home advantage, etc.
                                        </p>
                                      </div>

                                      <div className="bg-gradient-to-br from-blue-500/10 to-transparent border border-blue-500/30 rounded-lg p-4">
                                        <h5 className="text-xs font-semibold text-blue-400 uppercase tracking-wider mb-3">Confidence Breakdown</h5>
                                        <div className="space-y-2 text-xs text-zinc-300">
                                          <div className="flex justify-between">
                                            <span className="text-zinc-500">Confidence Score:</span>
                                            <span className="font-mono font-bold text-green-400">{pick.confidence_score}/10</span>
                                          </div>
                                          <div className="flex justify-between">
                                            <span className="text-zinc-500">Strength:</span>
                                            <span className="font-semibold">{pick.confidence_explanation?.strength || 'N/A'}</span>
                                          </div>
                                          <div className="border-t border-zinc-700/50 pt-2 space-y-1">
                                            <p className="text-zinc-400">{pick.confidence_explanation?.reasoning || 'Based on edge and probabilities'}</p>
                                          </div>
                                          <div className="border-t border-zinc-700/50 pt-2 space-y-1">
                                            <div className="flex justify-between">
                                              <span className="text-zinc-500">Edge:</span>
                                              <span className={`font-mono ${pick.edge_percentage > 0 ? 'text-green-400' : 'text-red-400'}`}>
                                                {pick.edge_percentage > 0 ? '+' : ''}{pick.edge_percentage}%
                                              </span>
                                            </div>
                                            <div className="flex justify-between">
                                              <span className="text-zinc-500">Score Differential:</span>
                                              <span className="font-mono">{Math.abs(pick.projected_home_score - pick.projected_away_score).toFixed(2)}</span>
                                            </div>
                                          </div>
                                        </div>
                                        <p className="text-xs text-zinc-500 italic mt-3">
                                          Confidence considers edge %, model probability strength, and score clarity
                                        </p>
                                      </div>
                                    </div>

                                    {/* All Outcome Probabilities */}
                                    <div className="bg-zinc-800/50 border border-zinc-700/50 rounded p-4">
                                      <h5 className="text-xs font-semibold text-zinc-300 uppercase tracking-wider mb-3">All Outcome Probabilities</h5>
                                      <div className="grid grid-cols-3 gap-4 text-xs">
                                        <div className="text-center">
                                          <p className="text-zinc-500 mb-2">HOME WIN</p>
                                          <p className="font-mono text-sm text-blue-400 mb-1">{pick.all_probabilities?.home || 0}%</p>
                                          <p className="text-zinc-600">vs Market: {(100 / pick.all_market_odds?.home).toFixed(1)}%</p>
                                        </div>
                                        <div className="text-center">
                                          <p className="text-zinc-500 mb-2">DRAW</p>
                                          <p className="font-mono text-sm text-zinc-400 mb-1">{pick.all_probabilities?.draw || 0}%</p>
                                          <p className="text-zinc-600">vs Market: {(100 / pick.all_market_odds?.draw).toFixed(1)}%</p>
                                        </div>
                                        <div className="text-center">
                                          <p className="text-zinc-500 mb-2">AWAY WIN</p>
                                          <p className="font-mono text-sm text-orange-400 mb-1">{pick.all_probabilities?.away || 0}%</p>
                                          <p className="text-zinc-600">vs Market: {(100 / pick.all_market_odds?.away).toFixed(1)}%</p>
                                        </div>
                                      </div>
                                    </div>
                                    
                                    {/* Factor Breakdowns */}
                                    <div>
                                      <h5 className="text-xs font-semibold text-zinc-300 uppercase tracking-wider mb-3">Factor-by-Factor Breakdown</h5>
                                      <div className="grid md:grid-cols-2 gap-6">
                                        <div className="bg-zinc-800/30 border border-zinc-700/30 rounded-lg p-4">
                                          <FactorBreakdown 
                                            breakdown={pick.home_breakdown} 
                                            teamName={`${pick.home_team} (Home)`}
                                          />
                                        </div>
                                        <div className="bg-zinc-800/30 border border-zinc-700/30 rounded-lg p-4">
                                          <FactorBreakdown 
                                            breakdown={pick.away_breakdown} 
                                            teamName={`${pick.away_team} (Away)`}
                                          />
                                        </div>
                                      </div>
                                    </div>
                                    
                                    {/* Summary */}
                                    <div className="text-xs text-zinc-500 italic border-t border-zinc-800 pt-4">
                                      💡 <span className="font-semibold">How it works:</span> Each factor&apos;s contribution = (team rating - baseline) × factor weight × multiplier. 
                                      Positive contributions increase the projected score. The final score determines outcome probabilities, 
                                      which are compared to market odds to find value bets.
                                    </div>
                                      </>
                                    )}
                                  </div>
                                </td>
                              </tr>
                            )}
                          </>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              )}
            </Card>
          );
        })}
      </div>
    ) : (
            <Card className="bg-zinc-900/50 border-zinc-800">
                <CardContent className="p-12 text-center">
                  <Target className="w-12 h-12 text-zinc-700 mx-auto mb-4" />
                  <p className="text-zinc-500">Select a model above to generate value picks</p>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* Simulation Tab */}
          <TabsContent value="simulation" className="space-y-6" data-testid="simulation-content">
            <Card className="bg-zinc-900/50 border-zinc-800">
              <CardHeader>
                <CardTitle className="text-lg font-display text-zinc-100 flex items-center gap-2">
                  <Play className="w-5 h-5 text-green-500" />
                  Model Simulation & Backtesting
                </CardTitle>
                <CardDescription className="text-zinc-500">
                  Test your models against historical games to validate accuracy
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="flex flex-col gap-4">
                  <div className="flex items-end gap-4">
                    <div className="flex-1">
                      <label className="text-sm text-zinc-400 mb-2 block">Select Model</label>
                      <Select value={selectedSimModel} onValueChange={setSelectedSimModel}>
                        <SelectTrigger className="bg-zinc-800 border-zinc-700" data-testid="sim-model-select">
                          <SelectValue placeholder="Choose a model to test" />
                        </SelectTrigger>
                        <SelectContent className="bg-zinc-800 border-zinc-700">
                          {models.map(m => (
                            <SelectItem key={m.id} value={m.id}>
                              {m.name} {m.model_type === 'preset' && '(Preset)'}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    
                    <div className="flex-1">
                      <label className="text-sm text-zinc-400 mb-2 block">Matchday Filter (Optional)</label>
                      <Select value={selectedMatchdayForSim?.toString() || "all"} onValueChange={(v) => setSelectedMatchdayForSim(v === "all" ? null : parseInt(v))}>
                        <SelectTrigger className="bg-zinc-800 border-zinc-700">
                          <SelectValue placeholder="All matchdays" />
                        </SelectTrigger>
                        <SelectContent className="bg-zinc-800 border-zinc-700">
                          <SelectItem value="all">All Matchdays</SelectItem>
                          {matchdays
                            .filter(md => md.completed_games > 0)
                            .map(md => (
                              <SelectItem key={md.matchday} value={md.matchday.toString()}>
                                Matchday {md.matchday} ({md.completed_games} completed)
                              </SelectItem>
                            ))}
                        </SelectContent>
                      </Select>
                    </div>
                    
                    <Button
                      className="bg-green-600 hover:bg-green-500 text-white font-bold"
                      onClick={() => runSimulation(selectedSimModel, selectedMatchdayForSim)}
                      disabled={!selectedSimModel || simulationLoading}
                      data-testid="run-simulation-btn"
                    >
                      {simulationLoading ? (
                        <>
                          <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                          Running...
                        </>
                      ) : (
                        <>
                          <Play className="w-4 h-4 mr-2" />
                          Run Simulation
                        </>
                      )}
                    </Button>
                  </div>
                  
                  {selectedMatchdayForSim && (
                    <div className="flex items-center gap-2 text-xs text-zinc-400">
                      <Info className="w-4 h-4" />
                      <span>Simulating Matchday {selectedMatchdayForSim} only</span>
                    </div>
                  )}
                </div>

                {simulationResults && (
                  <div className="space-y-6 mt-6">
                    {/* Summary Stats */}
                    <div>
                      <h3 className="text-sm font-semibold text-green-500 uppercase tracking-wider mb-3">
                        Simulation Results
                      </h3>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <Card className="bg-zinc-800/50 border-zinc-700">
                          <CardContent className="p-4">
                            <p className="text-xs text-zinc-500 uppercase">Accuracy</p>
                            <p className="text-2xl font-bold font-mono text-green-500">
                              {simulationResults.accuracy_percentage}%
                            </p>
                            <p className="text-xs text-zinc-500 mt-1">
                              {simulationResults.correct_predictions}/{simulationResults.total_games} correct
                            </p>
                          </CardContent>
                        </Card>
                        <Card className="bg-zinc-800/50 border-zinc-700">
                          <CardContent className="p-4">
                            <p className="text-xs text-zinc-500 uppercase">ROI</p>
                            <p className={`text-2xl font-bold font-mono ${simulationResults.simulated_roi >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                              {simulationResults.simulated_roi >= 0 ? '+' : ''}{simulationResults.simulated_roi}%
                            </p>
                            <p className="text-xs text-zinc-500 mt-1">Return on investment</p>
                          </CardContent>
                        </Card>
                        <Card className="bg-zinc-800/50 border-zinc-700">
                          <CardContent className="p-4">
                            <p className="text-xs text-zinc-500 uppercase">Net Profit</p>
                            <p className={`text-2xl font-bold font-mono ${simulationResults.net_profit >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                              {simulationResults.net_profit >= 0 ? '+' : ''}${simulationResults.net_profit}
                            </p>
                            <p className="text-xs text-zinc-500 mt-1">
                              Stake: ${simulationResults.total_stake}
                            </p>
                          </CardContent>
                        </Card>
                        <Card className="bg-zinc-800/50 border-zinc-700">
                          <CardContent className="p-4">
                            <p className="text-xs text-zinc-500 uppercase">Avg Odds</p>
                            <p className="text-2xl font-bold font-mono text-zinc-300">
                              {simulationResults.average_odds}
                            </p>
                            <p className="text-xs text-zinc-500 mt-1">On winning bets</p>
                          </CardContent>
                        </Card>
                      </div>
                    </div>

                    {/* Confidence Breakdown */}
                    <div>
                      <h3 className="text-sm font-semibold text-green-500 uppercase tracking-wider mb-3">
                        Accuracy by Confidence Level
                      </h3>
                      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                        {Object.entries(simulationResults.confidence_breakdown)
                          .sort((a, b) => parseInt(a[0]) - parseInt(b[0]))
                          .map(([level, stats]) => (
                            <Card key={level} className="bg-zinc-800/50 border-zinc-700">
                              <CardContent className="p-3">
                                <div className="flex items-center justify-between mb-2">
                                  <p className="text-xs text-zinc-500">Level {level}</p>
                                  <Badge variant="outline" className="text-xs">
                                    {stats.total}
                                  </Badge>
                                </div>
                                <p className="text-xl font-bold font-mono text-zinc-200">
                                  {stats.accuracy}%
                                </p>
                                <p className="text-xs text-zinc-500 mt-1">
                                  {stats.correct}/{stats.total}
                                </p>
                              </CardContent>
                            </Card>
                          ))}
                      </div>
                    </div>

                    {/* Outcome Breakdown */}
                    <div>
                      <h3 className="text-sm font-semibold text-green-500 uppercase tracking-wider mb-3">
                        Accuracy by Outcome Type
                      </h3>
                      <div className="grid grid-cols-3 gap-4">
                        {Object.entries(simulationResults.outcome_breakdown).map(([outcome, stats]) => (
                          <Card key={outcome} className="bg-zinc-800/50 border-zinc-700">
                            <CardContent className="p-4">
                              <p className="text-xs text-zinc-500 uppercase mb-2">{outcome} Predictions</p>
                              <p className="text-2xl font-bold font-mono text-zinc-200">
                                {stats.accuracy}%
                              </p>
                              <p className="text-xs text-zinc-500 mt-1">
                                {stats.correct}/{stats.total} correct
                              </p>
                            </CardContent>
                          </Card>
                        ))}
                      </div>
                    </div>

                    {/* Prediction Details */}
                    <div>
                      <h3 className="text-sm font-semibold text-green-500 uppercase tracking-wider mb-3 flex items-center justify-between">
                        <span>Prediction Details</span>
                        <Badge variant="outline" className="text-xs">
                          {simulationResults.predictions.length} Games
                        </Badge>
                      </h3>
                      <div className="space-y-4 max-h-96 overflow-y-auto">
                        {(() => {
                          // Group predictions by matchday
                          const grouped = {};
                          simulationResults.predictions.forEach(pred => {
                            const md = pred.matchday || 0;
                            if (!grouped[md]) grouped[md] = [];
                            grouped[md].push(pred);
                          });
                          
                          return Object.keys(grouped)
                            .sort((a, b) => parseInt(a) - parseInt(b))
                            .map(matchdayNum => (
                              <div key={matchdayNum} className="space-y-2">
                                <div className="flex items-center gap-2 mb-2">
                                  <h4 className="text-xs font-semibold text-zinc-400 uppercase">
                                    Matchday {matchdayNum}
                                  </h4>
                                  <Badge variant="outline" className="text-xs">
                                    {grouped[matchdayNum].length} matches
                                  </Badge>
                                  <span className="text-xs text-zinc-500">
                                    • {grouped[matchdayNum].filter(p => p.correct).length} correct
                                  </span>
                                </div>
                                
                                {grouped[matchdayNum].map((pred, idx) => (
                                  <div
                                    key={idx}
                                    className={`p-3 rounded-sm border ${
                                      pred.correct
                                        ? 'bg-green-500/5 border-green-500/20'
                                        : 'bg-red-500/5 border-red-500/20'
                                    }`}
                                  >
                                    <div className="flex items-center justify-between">
                                      <div className="flex items-center gap-3 flex-1">
                                        {pred.correct ? (
                                          <CheckCircle className="w-4 h-4 text-green-500" />
                                        ) : (
                                          <XCircle className="w-4 h-4 text-red-500" />
                                        )}
                                        <div>
                                          <p className="text-sm font-medium text-zinc-200">
                                            {pred.home_team} vs {pred.away_team}
                                          </p>
                                          <p className="text-xs text-zinc-500">
                                            {pred.match_date}
                                          </p>
                                        </div>
                                      </div>
                                      <div className="flex items-center gap-4 text-xs">
                                        <div className="text-center">
                                          <p className="text-zinc-500">Predicted</p>
                                          <p className="font-mono font-bold text-zinc-300 uppercase">
                                            {pred.predicted_outcome}
                                          </p>
                                        </div>
                                        <div className="text-center">
                                          <p className="text-zinc-500">Actual</p>
                                          <p className="font-mono font-bold text-zinc-300 uppercase">
                                            {pred.actual_result}
                                          </p>
                                        </div>
                                        <div className="text-center">
                                          <p className="text-zinc-500">Score</p>
                                          <p className="font-mono font-bold text-zinc-300">
                                            {pred.home_score_actual}-{pred.away_score_actual}
                                          </p>
                                        </div>
                                        <div className="text-center">
                                          <p className="text-zinc-500">Conf</p>
                                          <ConfidenceBadge score={pred.confidence} />
                                        </div>
                                        <div className="text-center">
                                          <p className="text-zinc-500">Odds</p>
                                          <p className="font-mono text-zinc-300">{pred.odds}</p>
                                        </div>
                                      </div>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            ));
                        })()}
                      </div>
                    </div>
                  </div>
                )}

                {!simulationResults && !simulationLoading && (
                  <div className="text-center py-12">
                    <BarChart2 className="w-12 h-12 text-zinc-700 mx-auto mb-4" />
                    <p className="text-zinc-500">Select a model and run simulation to see results</p>
                    <p className="text-zinc-600 text-sm mt-1">Tests against 20 historical games with known outcomes</p>
                  </div>
                )}
              </CardContent>
            </Card>
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

      {/* Team Details Dialog */}
      <Dialog open={showTeamDetailsDialog} onOpenChange={setShowTeamDetailsDialog}>
        <DialogContent className="bg-zinc-900 border-zinc-800 text-zinc-100 max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-2xl font-display text-green-500">
              {selectedTeamName}
            </DialogTitle>
            <DialogDescription className="text-zinc-400">
              Detailed team statistics and recent performance
            </DialogDescription>
          </DialogHeader>
          
          {teamDetailsLoading ? (
            <div className="flex items-center justify-center py-12">
              <RefreshCw className="w-8 h-8 text-green-500 animate-spin" />
            </div>
          ) : teamDetails ? (
            <div className="space-y-6">
              {/* Team Ratings */}
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                <Card className="bg-zinc-800/50 border-zinc-700">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-zinc-400 uppercase">Offense</span>
                      <span className="text-2xl font-bold text-green-500">{teamDetails.ratings.offense}</span>
                    </div>
                    <div className="mt-2 h-2 bg-zinc-700 rounded-full overflow-hidden">
                      <div className="h-full bg-green-500" style={{ width: `${teamDetails.ratings.offense}%` }}></div>
                    </div>
                  </CardContent>
                </Card>

                <Card className="bg-zinc-800/50 border-zinc-700">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-zinc-400 uppercase">Defense</span>
                      <span className="text-2xl font-bold text-blue-500">{teamDetails.ratings.defense}</span>
                    </div>
                    <div className="mt-2 h-2 bg-zinc-700 rounded-full overflow-hidden">
                      <div className="h-full bg-blue-500" style={{ width: `${teamDetails.ratings.defense}%` }}></div>
                    </div>
                  </CardContent>
                </Card>

                <Card className="bg-zinc-800/50 border-zinc-700">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-zinc-400 uppercase">Form</span>
                      <span className="text-2xl font-bold text-orange-500">{teamDetails.ratings.form}</span>
                    </div>
                    <div className="mt-2 h-2 bg-zinc-700 rounded-full overflow-hidden">
                      <div className="h-full bg-orange-500" style={{ width: `${teamDetails.ratings.form}%` }}></div>
                    </div>
                  </CardContent>
                </Card>

                <Card className="bg-zinc-800/50 border-zinc-700">
                  <CardContent className="p-4">
                    <div className="text-center">
                      <span className="text-xs text-zinc-400 uppercase block">Motivation</span>
                      <span className="text-2xl font-bold text-purple-500">{teamDetails.ratings.motivation}</span>
                    </div>
                  </CardContent>
                </Card>

                <Card className="bg-zinc-800/50 border-zinc-700">
                  <CardContent className="p-4">
                    <div className="text-center">
                      <span className="text-xs text-zinc-400 uppercase block">Rest Days</span>
                      <span className="text-2xl font-bold text-cyan-500">{teamDetails.ratings.rest_days}</span>
                    </div>
                  </CardContent>
                </Card>

                <Card className="bg-zinc-800/50 border-zinc-700">
                  <CardContent className="p-4">
                    <div className="text-center">
                      <span className="text-xs text-zinc-400 uppercase block">Injury Impact</span>
                      <span className="text-2xl font-bold text-red-500">{teamDetails.ratings.injury_impact}%</span>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Season Statistics */}
              <Card className="bg-zinc-800/50 border-zinc-700">
                <CardHeader>
                  <CardTitle className="text-lg text-green-500">Season Statistics</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="text-center p-3 bg-zinc-900/50 rounded">
                      <p className="text-xs text-zinc-400 uppercase">Matches</p>
                      <p className="text-2xl font-bold text-zinc-100">{teamDetails.statistics.total_matches}</p>
                    </div>
                    <div className="text-center p-3 bg-zinc-900/50 rounded">
                      <p className="text-xs text-zinc-400 uppercase">Win Rate</p>
                      <p className="text-2xl font-bold text-green-500">{teamDetails.statistics.win_rate}%</p>
                    </div>
                    <div className="text-center p-3 bg-zinc-900/50 rounded">
                      <p className="text-xs text-zinc-400 uppercase">Avg Goals Scored</p>
                      <p className="text-2xl font-bold text-blue-500">{teamDetails.statistics.avg_goals_scored}</p>
                    </div>
                    <div className="text-center p-3 bg-zinc-900/50 rounded">
                      <p className="text-xs text-zinc-400 uppercase">Avg Goals Conceded</p>
                      <p className="text-2xl font-bold text-red-500">{teamDetails.statistics.avg_goals_conceded}</p>
                    </div>
                  </div>
                  <div className="mt-4 grid grid-cols-4 gap-4">
                    <div className="text-center p-3 bg-green-500/10 rounded border border-green-500/30">
                      <p className="text-xs text-zinc-400 uppercase">Wins</p>
                      <p className="text-xl font-bold text-green-500">{teamDetails.statistics.wins}</p>
                    </div>
                    <div className="text-center p-3 bg-yellow-500/10 rounded border border-yellow-500/30">
                      <p className="text-xs text-zinc-400 uppercase">Draws</p>
                      <p className="text-xl font-bold text-yellow-500">{teamDetails.statistics.draws}</p>
                    </div>
                    <div className="text-center p-3 bg-red-500/10 rounded border border-red-500/30">
                      <p className="text-xs text-zinc-400 uppercase">Losses</p>
                      <p className="text-xl font-bold text-red-500">{teamDetails.statistics.losses}</p>
                    </div>
                    <div className="text-center p-3 bg-blue-500/10 rounded border border-blue-500/30">
                      <p className="text-xs text-zinc-400 uppercase">Goal Diff</p>
                      <p className="text-xl font-bold text-blue-500">{teamDetails.statistics.goal_difference > 0 ? '+' : ''}{teamDetails.statistics.goal_difference}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Period-Based Statistics */}
              {teamDetails.period_stats && (
                <Card className="bg-zinc-800/50 border-zinc-700">
                  <CardHeader>
                    <CardTitle className="text-lg text-green-500 flex items-center gap-2">
                      <BarChart2 className="w-5 h-5" />
                      Performance by Time Period
                    </CardTitle>
                    <CardDescription className="text-zinc-500">
                      Stats calculated from different match ranges
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="grid md:grid-cols-3 gap-4">
                      {/* Last 5 Matches */}
                      {teamDetails.period_stats.last_5 && (
                        <div className="p-4 bg-gradient-to-br from-green-500/10 to-transparent border border-green-500/30 rounded-lg">
                          <h4 className="text-sm font-semibold text-green-400 uppercase mb-3 flex items-center gap-2">
                            <Clock className="w-4 h-4" />
                            Last 5 Matches
                          </h4>
                          <div className="space-y-2 text-sm">
                            <div className="flex justify-between items-center">
                              <span className="text-zinc-400">Matches:</span>
                              <span className="font-mono text-zinc-200">{teamDetails.period_stats.last_5.matches}</span>
                            </div>
                            <div className="flex justify-between items-center">
                              <span className="text-zinc-400">Win Rate:</span>
                              <span className="font-mono font-bold text-green-400">{teamDetails.period_stats.last_5.win_rate}%</span>
                            </div>
                            <div className="flex justify-between items-center">
                              <span className="text-zinc-400">Goals For:</span>
                              <span className="font-mono text-blue-400">{teamDetails.period_stats.last_5.avg_goals_for}/match</span>
                            </div>
                            <div className="flex justify-between items-center">
                              <span className="text-zinc-400">Goals Against:</span>
                              <span className="font-mono text-red-400">{teamDetails.period_stats.last_5.avg_goals_against}/match</span>
                            </div>
                            <div className="flex justify-between items-center pt-2 border-t border-zinc-700">
                              <span className="text-zinc-400">Goal Diff:</span>
                              <span className={`font-mono font-bold ${teamDetails.period_stats.last_5.goal_difference >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                {teamDetails.period_stats.last_5.goal_difference > 0 ? '+' : ''}{teamDetails.period_stats.last_5.goal_difference.toFixed(1)}
                              </span>
                            </div>
                            <div className="text-xs text-zinc-500 italic mt-2">
                              W:{teamDetails.period_stats.last_5.wins} D:{teamDetails.period_stats.last_5.draws} L:{teamDetails.period_stats.last_5.losses}
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Last 10 Matches */}
                      {teamDetails.period_stats.last_10 && (
                        <div className="p-4 bg-gradient-to-br from-blue-500/10 to-transparent border border-blue-500/30 rounded-lg">
                          <h4 className="text-sm font-semibold text-blue-400 uppercase mb-3 flex items-center gap-2">
                            <Clock className="w-4 h-4" />
                            Last 10 Matches
                          </h4>
                          <div className="space-y-2 text-sm">
                            <div className="flex justify-between items-center">
                              <span className="text-zinc-400">Matches:</span>
                              <span className="font-mono text-zinc-200">{teamDetails.period_stats.last_10.matches}</span>
                            </div>
                            <div className="flex justify-between items-center">
                              <span className="text-zinc-400">Win Rate:</span>
                              <span className="font-mono font-bold text-green-400">{teamDetails.period_stats.last_10.win_rate}%</span>
                            </div>
                            <div className="flex justify-between items-center">
                              <span className="text-zinc-400">Goals For:</span>
                              <span className="font-mono text-blue-400">{teamDetails.period_stats.last_10.avg_goals_for}/match</span>
                            </div>
                            <div className="flex justify-between items-center">
                              <span className="text-zinc-400">Goals Against:</span>
                              <span className="font-mono text-red-400">{teamDetails.period_stats.last_10.avg_goals_against}/match</span>
                            </div>
                            <div className="flex justify-between items-center pt-2 border-t border-zinc-700">
                              <span className="text-zinc-400">Goal Diff:</span>
                              <span className={`font-mono font-bold ${teamDetails.period_stats.last_10.goal_difference >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                {teamDetails.period_stats.last_10.goal_difference > 0 ? '+' : ''}{teamDetails.period_stats.last_10.goal_difference.toFixed(1)}
                              </span>
                            </div>
                            <div className="text-xs text-zinc-500 italic mt-2">
                              W:{teamDetails.period_stats.last_10.wins} D:{teamDetails.period_stats.last_10.draws} L:{teamDetails.period_stats.last_10.losses}
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Last 15 Matches */}
                      {teamDetails.period_stats.last_15 && (
                        <div className="p-4 bg-gradient-to-br from-orange-500/10 to-transparent border border-orange-500/30 rounded-lg">
                          <h4 className="text-sm font-semibold text-orange-400 uppercase mb-3 flex items-center gap-2">
                            <Clock className="w-4 h-4" />
                            Last 15 Matches
                          </h4>
                          <div className="space-y-2 text-sm">
                            <div className="flex justify-between items-center">
                              <span className="text-zinc-400">Matches:</span>
                              <span className="font-mono text-zinc-200">{teamDetails.period_stats.last_15.matches}</span>
                            </div>
                            <div className="flex justify-between items-center">
                              <span className="text-zinc-400">Win Rate:</span>
                              <span className="font-mono font-bold text-green-400">{teamDetails.period_stats.last_15.win_rate}%</span>
                            </div>
                            <div className="flex justify-between items-center">
                              <span className="text-zinc-400">Goals For:</span>
                              <span className="font-mono text-blue-400">{teamDetails.period_stats.last_15.avg_goals_for}/match</span>
                            </div>
                            <div className="flex justify-between items-center">
                              <span className="text-zinc-400">Goals Against:</span>
                              <span className="font-mono text-red-400">{teamDetails.period_stats.last_15.avg_goals_against}/match</span>
                            </div>
                            <div className="flex justify-between items-center pt-2 border-t border-zinc-700">
                              <span className="text-zinc-400">Goal Diff:</span>
                              <span className={`font-mono font-bold ${teamDetails.period_stats.last_15.goal_difference >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                {teamDetails.period_stats.last_15.goal_difference > 0 ? '+' : ''}{teamDetails.period_stats.last_15.goal_difference.toFixed(1)}
                              </span>
                            </div>
                            <div className="text-xs text-zinc-500 italic mt-2">
                              W:{teamDetails.period_stats.last_15.wins} D:{teamDetails.period_stats.last_15.draws} L:{teamDetails.period_stats.last_15.losses}
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Recent Matches */}
              {teamDetails.recent_matches && teamDetails.recent_matches.length > 0 && (
                <Card className="bg-zinc-800/50 border-zinc-700">
                  <CardHeader>
                    <CardTitle className="text-lg text-green-500">Recent Matches</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {teamDetails.recent_matches.map((match, idx) => (
                        <div key={idx} className="flex items-center justify-between p-3 bg-zinc-900/50 rounded border border-zinc-700/50">
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              <Badge className={`text-xs ${
                                match.result === 'won' ? 'bg-green-500/20 text-green-500 border-green-500/40' :
                                match.result === 'draw' ? 'bg-yellow-500/20 text-yellow-500 border-yellow-500/40' :
                                'bg-red-500/20 text-red-500 border-red-500/40'
                              }`}>
                                {match.result.toUpperCase()}
                              </Badge>
                              <span className="text-sm font-medium text-zinc-200">
                                vs {match.opponent}
                              </span>
                              <span className="text-xs text-zinc-500">({match.home_away})</span>
                            </div>
                            <p className="text-xs text-zinc-500 mt-1">{match.date}</p>
                          </div>
                          <div className="text-right">
                            <p className="text-lg font-bold font-mono text-zinc-100">{match.score}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Upcoming Fixtures */}
              {teamDetails.upcoming_fixtures && teamDetails.upcoming_fixtures.length > 0 && (
                <Card className="bg-zinc-800/50 border-zinc-700">
                  <CardHeader>
                    <CardTitle className="text-lg text-green-500">Upcoming Fixtures</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {teamDetails.upcoming_fixtures.map((fixture, idx) => (
                        <div key={idx} className="flex items-center justify-between p-3 bg-zinc-900/50 rounded border border-zinc-700/50">
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              <span className="text-sm font-medium text-zinc-200">
                                vs {fixture.opponent}
                              </span>
                              <span className="text-xs text-zinc-500">({fixture.home_away})</span>
                            </div>
                            <p className="text-xs text-zinc-500 mt-1">{fixture.date}</p>
                          </div>
                          <div className="flex gap-2 text-xs font-mono">
                            <span className="text-blue-400">{fixture.home_odds}</span>
                            <span className="text-zinc-500">{fixture.draw_odds}</span>
                            <span className="text-orange-400">{fixture.away_odds}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Data Source Badge */}
              <div className="text-center">
                <Badge variant="outline" className={`${
                  teamDetails.data_source === 'api' ? 'border-green-500/40 text-green-500' : 'border-yellow-500/40 text-yellow-500'
                }`}>
                  Data Source: {teamDetails.data_source === 'api' ? 'Real API' : 'Mock Data'}
                </Badge>
              </div>

              {/* API Debugging Information */}
              <Card className="bg-zinc-800/50 border-amber-500/30">
                <CardHeader>
                  <CardTitle className="text-lg text-amber-500 flex items-center gap-2">
                    <Info className="w-5 h-5" />
                    API Debugging Information
                  </CardTitle>
                  <CardDescription className="text-zinc-500">
                    Technical details for debugging and validation
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* API Endpoint */}
                  <div>
                    <h5 className="text-xs font-semibold text-amber-400 uppercase tracking-wider mb-2">
                      API Endpoint Used
                    </h5>
                    <div className="bg-zinc-900 border border-zinc-700 rounded p-3 font-mono text-xs text-green-400">
                      GET {API}/teams/{encodeURIComponent(selectedTeamName)}
                    </div>
                  </div>

                  {/* Response JSON */}
                  <div>
                    <h5 className="text-xs font-semibold text-amber-400 uppercase tracking-wider mb-2">
                      API Response (JSON)
                    </h5>
                    <div className="bg-zinc-900 border border-zinc-700 rounded p-3 max-h-96 overflow-y-auto">
                      <pre className="text-xs text-zinc-300 whitespace-pre-wrap font-mono">
                        {JSON.stringify(teamDetails, null, 2)}
                      </pre>
                    </div>
                  </div>

                  {/* Data Points Used in Calculations */}
                  <div>
                    <h5 className="text-xs font-semibold text-amber-400 uppercase tracking-wider mb-2">
                      Key Data Points Used in Model Calculations
                    </h5>
                    <div className="grid md:grid-cols-2 gap-3">
                      <div className="bg-zinc-900/50 border border-zinc-700/50 rounded p-3">
                        <p className="text-xs text-zinc-500 mb-2">Ratings (used by weighted models)</p>
                        <div className="space-y-1 text-xs font-mono">
                          <div className="flex justify-between">
                            <span className="text-zinc-400">Offense:</span>
                            <span className="text-green-400">{teamDetails.ratings.offense}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-zinc-400">Defense:</span>
                            <span className="text-blue-400">{teamDetails.ratings.defense}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-zinc-400">Form:</span>
                            <span className="text-orange-400">{teamDetails.ratings.form}</span>
                          </div>
                        </div>
                      </div>

                      <div className="bg-zinc-900/50 border border-zinc-700/50 rounded p-3">
                        <p className="text-xs text-zinc-500 mb-2">Stats (used by all models)</p>
                        <div className="space-y-1 text-xs font-mono">
                          <div className="flex justify-between">
                            <span className="text-zinc-400">Avg Goals For:</span>
                            <span className="text-green-400">{teamDetails.statistics.avg_goals_scored}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-zinc-400">Avg Goals Against:</span>
                            <span className="text-red-400">{teamDetails.statistics.avg_goals_conceded}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-zinc-400">Win Rate:</span>
                            <span className="text-blue-400">{teamDetails.statistics.win_rate}%</span>
                          </div>
                        </div>
                      </div>

                      {/* xG Statistics */}
                      {teamDetails.xg_statistics && teamDetails.xg_statistics.matches_analyzed > 0 && (
                        <>
                          <div className="bg-purple-900/30 border border-purple-500/50 rounded p-3">
                            <p className="text-xs text-purple-400 font-semibold mb-2">xG Stats (Poisson Model)</p>
                            <div className="space-y-1 text-xs font-mono">
                              <div className="flex justify-between">
                                <span className="text-zinc-400">xG per match:</span>
                                <span className="text-green-400">{teamDetails.xg_statistics.xG_per_match}</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-zinc-400">xGA per match:</span>
                                <span className="text-red-400">{teamDetails.xg_statistics.xGA_per_match}</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-zinc-400">Attack Strength:</span>
                                <span className="text-purple-400">{teamDetails.xg_statistics.attack_strength}</span>
                              </div>
                            </div>
                          </div>

                          <div className="bg-purple-900/30 border border-purple-500/50 rounded p-3">
                            <p className="text-xs text-purple-400 font-semibold mb-2">xG Home/Away Split</p>
                            <div className="space-y-1 text-xs font-mono">
                              <div className="flex justify-between">
                                <span className="text-zinc-400">Home xG/match:</span>
                                <span className="text-blue-400">{teamDetails.xg_statistics.home_xG_per_match}</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-zinc-400">Away xG/match:</span>
                                <span className="text-orange-400">{teamDetails.xg_statistics.away_xG_per_match}</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-zinc-400">Defense Strength:</span>
                                <span className="text-purple-400">{teamDetails.xg_statistics.defense_strength}</span>
                              </div>
                            </div>
                          </div>
                        </>
                      )}
                    </div>
                  </div>

                  {/* Data Flow Diagram */}
                  <div>
                    <h5 className="text-xs font-semibold text-amber-400 uppercase tracking-wider mb-2">
                      Data Flow & Processing
                    </h5>
                    <div className="bg-zinc-900/50 border border-zinc-700/50 rounded p-4 space-y-3">
                      {teamDetails.api_metadata && (
                        <div className="text-xs text-zinc-400 space-y-1">
                          <p><span className="text-amber-400 font-semibold">Source API:</span> {teamDetails.api_metadata.endpoint}</p>
                          <p><span className="text-amber-400 font-semibold">Matches Analyzed:</span> {teamDetails.api_metadata.matches_analyzed}</p>
                        </div>
                      )}
                      <div className="flex items-center justify-between text-xs text-zinc-400 mt-3">
                        <div className="text-center">
                          <div className="w-20 h-20 rounded-full bg-green-500/20 border-2 border-green-500 flex items-center justify-center mx-auto mb-2">
                            <span className="text-green-400 font-semibold text-xs">API</span>
                          </div>
                          <p>Football-Data.org</p>
                        </div>
                        <ChevronRight className="w-6 h-6 text-zinc-600" />
                        <div className="text-center">
                          <div className="w-20 h-20 rounded-full bg-blue-500/20 border-2 border-blue-500 flex items-center justify-center mx-auto mb-2">
                            <span className="text-blue-400 font-semibold text-xs">Backend</span>
                          </div>
                          <p>Calculate Stats</p>
                        </div>
                        <ChevronRight className="w-6 h-6 text-zinc-600" />
                        <div className="text-center">
                          <div className="w-20 h-20 rounded-full bg-purple-500/20 border-2 border-purple-500 flex items-center justify-center mx-auto mb-2">
                            <span className="text-purple-400 font-semibold text-xs">Model</span>
                          </div>
                          <p>Generate Picks</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          ) : (
            <div className="text-center py-8 text-zinc-500">
              No data available
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default App;
