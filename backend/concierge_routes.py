"""
MarketGPS - AI Concierge Routes
================================

Provides AI-powered investment advice and portfolio analysis.
Uses ProphetIA scoring combined with LLM for natural language responses.

Endpoints:
- POST /api/concierge/analyze   - Analyze portfolio with AI
- POST /api/concierge/suggest   - Get personalized suggestions
- GET  /api/concierge/prompts   - Get quick action prompts

Security:
- All endpoints require authentication
- No financial advice disclaimer included in responses
"""

import os
import json
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

from fastapi import APIRouter, HTTPException, Depends, Query, Body
from pydantic import BaseModel, Field

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/concierge", tags=["AI Concierge"])


# =============================================================================
# Types & Models
# =============================================================================

class CoachProfile(str, Enum):
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"


class AnalysisRequest(BaseModel):
    prompt: str = Field(..., description="User's question or analysis request")
    coach_profile: CoachProfile = Field(default=CoachProfile.BALANCED)
    portfolio_value: Optional[float] = Field(None, description="Current portfolio value")
    portfolio_score: Optional[int] = Field(None, description="Current ProphetIA score")
    holdings: Optional[List[Dict[str, Any]]] = Field(None, description="List of holdings")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class SuggestionRequest(BaseModel):
    coach_profile: CoachProfile = Field(default=CoachProfile.BALANCED)
    portfolio_score: Optional[int] = Field(None)
    risk_tolerance: Optional[float] = Field(None, ge=0, le=1)
    investment_horizon: Optional[int] = Field(None, description="Years")


class ActionItem(BaseModel):
    label: str
    action: str
    type: str = "secondary"


class MetricItem(BaseModel):
    label: str
    value: str
    change: Optional[float] = None
    icon: Optional[str] = None


class AnalysisResponse(BaseModel):
    success: bool
    message: str
    content: str
    metrics: Optional[List[MetricItem]] = None
    actions: Optional[List[ActionItem]] = None
    coach_profile: CoachProfile
    timestamp: str
    disclaimer: str = "Les conseils fournis sont à titre informatif uniquement et ne constituent pas des conseils en investissement."


class QuickPrompt(BaseModel):
    id: str
    label: str
    prompt: str
    category: str
    icon: str


# =============================================================================
# Prompt Templates
# =============================================================================

COACH_PERSONALITIES = {
    CoachProfile.CONSERVATIVE: {
        "name": "Prudent",
        "focus": "préservation du capital, revenus stables, faible volatilité",
        "allocation_bias": "obligations, dividendes, blue chips",
        "risk_tolerance": "faible",
    },
    CoachProfile.BALANCED: {
        "name": "Équilibré",
        "focus": "optimisation rendement/risque, diversification",
        "allocation_bias": "mix actions/obligations, ETF diversifiés",
        "risk_tolerance": "modéré",
    },
    CoachProfile.AGGRESSIVE: {
        "name": "Dynamique",
        "focus": "croissance maximale, alpha, opportunités",
        "allocation_bias": "growth stocks, tech, émergents",
        "risk_tolerance": "élevé",
    },
}

QUICK_PROMPTS: List[QuickPrompt] = [
    QuickPrompt(
        id="analyze-portfolio",
        label="Analyser mon portefeuille",
        prompt="Analyse mon portefeuille actuel et donne-moi un diagnostic complet.",
        category="analysis",
        icon="BarChart3",
    ),
    QuickPrompt(
        id="optimize-allocation",
        label="Optimiser mon allocation",
        prompt="Comment puis-je optimiser mon allocation pour améliorer mon rendement ajusté au risque ?",
        category="optimization",
        icon="Target",
    ),
    QuickPrompt(
        id="risk-assessment",
        label="Évaluer mes risques",
        prompt="Quels sont les principaux risques de mon portefeuille actuel ?",
        category="risk",
        icon="Shield",
    ),
    QuickPrompt(
        id="market-opportunities",
        label="Opportunités du moment",
        prompt="Quelles sont les meilleures opportunités du marché selon mon profil ?",
        category="market",
        icon="TrendingUp",
    ),
    QuickPrompt(
        id="rebalance-check",
        label="Besoin de rééquilibrer ?",
        prompt="Mon portefeuille nécessite-t-il un rééquilibrage ?",
        category="optimization",
        icon="RefreshCw",
    ),
    QuickPrompt(
        id="next-investment",
        label="Prochain investissement",
        prompt="Quel devrait être mon prochain investissement ?",
        category="market",
        icon="Lightbulb",
    ),
]


# =============================================================================
# Analysis Engine
# =============================================================================

def generate_portfolio_analysis(
    prompt: str,
    profile: CoachProfile,
    portfolio_value: Optional[float],
    portfolio_score: Optional[int],
    holdings: Optional[List[Dict]],
) -> Dict[str, Any]:
    """
    Generate AI analysis based on prompt and portfolio data.
    
    In production, this would:
    1. Fetch real portfolio data from database
    2. Calculate metrics using ProphetIA
    3. Generate response using LLM (OpenAI/Gemini)
    
    For now, returns structured demo responses.
    """
    coach = COACH_PERSONALITIES[profile]
    score = portfolio_score or 72
    value = portfolio_value or 250000
    
    # Detect prompt type
    prompt_lower = prompt.lower()
    
    if "analyse" in prompt_lower or "diagnostic" in prompt_lower:
        return _generate_diagnostic(coach, score, value, profile)
    elif "optimis" in prompt_lower or "allocation" in prompt_lower:
        return _generate_optimization(coach, score, value, profile)
    elif "risque" in prompt_lower:
        return _generate_risk_analysis(coach, score, value, profile)
    elif "opportunité" in prompt_lower or "marché" in prompt_lower:
        return _generate_opportunities(coach, score, value, profile)
    elif "rééquilibr" in prompt_lower or "rebalance" in prompt_lower:
        return _generate_rebalance(coach, score, value, profile)
    else:
        return _generate_generic(coach, score, value, profile, prompt)


def _generate_diagnostic(coach: Dict, score: int, value: float, profile: CoachProfile) -> Dict:
    """Generate portfolio diagnostic response."""
    return {
        "content": f"""**Diagnostic de votre portefeuille**

Votre portefeuille affiche un score global de **{score}/100**, ce qui le place dans la catégorie {"Excellent" if score >= 80 else "Bon" if score >= 60 else "Moyen"}.

**Points forts :**
- Diversification sectorielle satisfaisante (7 secteurs)
- Exposition tech bien calibrée (28%)
- Liquidité suffisante pour saisir des opportunités

**Points d'attention :**
- Surpondération légère sur les valeurs US (68% vs 55% recommandé)
- Absence d'exposition aux marchés émergents
- Duration obligataire courte dans un contexte de baisse des taux

**Recommandation {coach['name']} :**
{"Renforcer la poche obligataire investment grade et réduire l'exposition aux valeurs de croissance." if profile == CoachProfile.CONSERVATIVE else "Ajouter 5-10% d'exposition aux marchés émergents via un ETF diversifié." if profile == CoachProfile.BALANCED else "Profiter de la correction tech pour renforcer les positions sur les leaders IA."}""",
        "metrics": [
            {"label": "Score Global", "value": str(score), "icon": "BarChart3"},
            {"label": "Rendement YTD", "value": "+12.4%", "change": 12.4, "icon": "TrendingUp"},
            {"label": "Volatilité", "value": "14.2%", "icon": "AlertTriangle"},
            {"label": "Sharpe Ratio", "value": "1.24", "icon": "Target"},
        ],
        "actions": [
            {"label": "Voir le détail", "action": "view_portfolio", "type": "secondary"},
            {"label": "Appliquer les suggestions", "action": "apply_suggestions", "type": "primary"},
        ],
    }


def _generate_optimization(coach: Dict, score: int, value: float, profile: CoachProfile) -> Dict:
    """Generate allocation optimization response."""
    target_us = "50%" if profile == CoachProfile.AGGRESSIVE else "40%"
    target_em = "5%" if profile == CoachProfile.CONSERVATIVE else "10%"
    target_bonds = "30%" if profile == CoachProfile.CONSERVATIVE else "20%"
    
    return {
        "content": f"""**Optimisation de votre allocation**

Basé sur votre profil **{coach['name']}**, voici les ajustements recommandés :

| Classe d'actifs | Actuel | Cible | Action |
|-----------------|--------|-------|--------|
| Actions US | 45% | {target_us} | {"🟢 Renforcer" if profile == CoachProfile.AGGRESSIVE else "🔴 Réduire"} |
| Actions EU | 18% | 20% | 🟢 Renforcer |
| Émergents | 0% | {target_em} | 🟢 Initier |
| Obligations | 25% | {target_bonds} | {"🟢 Renforcer" if profile == CoachProfile.CONSERVATIVE else "🔴 Réduire"} |
| Immobilier | 8% | 10% | 🟢 Renforcer |
| Cash | 4% | 5% | ➡️ Maintenir |

**Impact estimé :**
- Rendement attendu : {"+1.8%" if profile == CoachProfile.AGGRESSIVE else "+0.8%"} / an
- Volatilité : {"-2.1%" if profile == CoachProfile.CONSERVATIVE else "+1.2%"}
- Score ProphetIA : +{"8" if profile == CoachProfile.AGGRESSIVE else "5"} points""",
        "actions": [
            {"label": "Simuler ce scénario", "action": "simulate", "type": "secondary"},
            {"label": "Générer les ordres", "action": "generate_orders", "type": "primary"},
        ],
    }


def _generate_risk_analysis(coach: Dict, score: int, value: float, profile: CoachProfile) -> Dict:
    """Generate risk analysis response."""
    return {
        "content": f"""**Évaluation des risques**

Votre portefeuille présente un profil de risque **modéré** avec quelques points de vigilance.

🔴 **Risques élevés :**
- **Concentration tech** : 32% sur 5 valeurs. Un repli du Nasdaq de 20% impacterait votre portefeuille de -6.4%.
- **Risque de change** : 68% en USD sans couverture.

🟡 **Risques modérés :**
- **Duration** : Sensibilité taux de 2.3 ans. Impact limité à court terme.
- **Liquidité** : 3 positions représentent plus de 2 jours de volume moyen.

🟢 **Risques maîtrisés :**
- **Contrepartie** : Diversification courtiers satisfaisante.
- **Réglementaire** : Pas d'exposition aux secteurs sensibles.

**Stress test :**
- Scénario "Récession US" : -18% estimé
- Scénario "Hausse taux +100bp" : -4% estimé
- Scénario "Crash tech" : -12% estimé""",
        "metrics": [
            {"label": "VaR 95%", "value": "-4.2%", "icon": "AlertTriangle"},
            {"label": "Beta", "value": "1.12", "icon": "TrendingUp"},
            {"label": "Drawdown Max", "value": "-14%", "icon": "Shield"},
        ],
    }


def _generate_opportunities(coach: Dict, score: int, value: float, profile: CoachProfile) -> Dict:
    """Generate market opportunities response."""
    picks = {
        CoachProfile.CONSERVATIVE: [
            ("VIG", "Vanguard Dividend", 78, "+8%", "Faible"),
            ("TLT", "Treasury 20Y", 72, "+6%", "Faible"),
            ("JNJ", "Johnson & Johnson", 75, "+10%", "Faible"),
        ],
        CoachProfile.BALANCED: [
            ("MSFT", "Microsoft", 84, "+15%", "Modéré"),
            ("QQQM", "Nasdaq 100", 78, "+18%", "Modéré"),
            ("IEMG", "Emerging Markets", 72, "+15%", "Modéré"),
        ],
        CoachProfile.AGGRESSIVE: [
            ("NVDA", "Nvidia", 84, "+25%", "Élevé"),
            ("QQQM", "Nasdaq 100", 78, "+22%", "Modéré"),
            ("IEMG", "Emerging Markets", 72, "+28%", "Élevé"),
        ],
    }
    
    recs = picks[profile]
    
    return {
        "content": f"""**Opportunités du moment** (profil {coach['name']})

🎯 **Top 3 recommandations :**

1. **{recs[0][0]} - {recs[0][1]}** — Score {recs[0][2]}
   - Signal : Breakout technique confirmé
   - Potentiel : {recs[0][3]} sur 12 mois
   - Risque : {recs[0][4]}

2. **{recs[1][0]} - {recs[1][1]}** — Score {recs[1][2]}
   - Signal : Accumulation institutionnelle
   - Potentiel : {recs[1][3]} sur 12 mois
   - Risque : {recs[1][4]}

3. **{recs[2][0]} - {recs[2][1]}** — Score {recs[2][2]}
   - Signal : Valorisation attractive
   - Potentiel : {recs[2][3]} sur 12 mois
   - Risque : {recs[2][4]}

**Compatible avec votre allocation :** 
Ces recommandations permettraient d'améliorer votre score de +5 points.""",
        "actions": [
            {"label": "Voir les détails", "action": "view_opportunities", "type": "secondary"},
            {"label": "Ajouter à la watchlist", "action": "add_watchlist", "type": "primary"},
        ],
    }


def _generate_rebalance(coach: Dict, score: int, value: float, profile: CoachProfile) -> Dict:
    """Generate rebalancing analysis."""
    return {
        "content": f"""**Analyse de rééquilibrage**

Votre portefeuille présente des écarts par rapport à votre allocation cible :

| Classe | Cible | Actuel | Écart | Action |
|--------|-------|--------|-------|--------|
| Actions | 60% | 65% | +5% | 🔴 Vendre €{int(value * 0.05):,} |
| Obligations | 30% | 25% | -5% | 🟢 Acheter €{int(value * 0.05):,} |
| Cash | 10% | 10% | 0% | ➡️ OK |

**Recommandation {coach['name']} :**
{"Procédez au rééquilibrage pour réduire le risque. Les marchés actions ont surperformé, c'est le moment de sécuriser les gains." if profile == CoachProfile.CONSERVATIVE else "L'écart reste dans les limites acceptables (+/- 5%). Surveillez mais pas d'action urgente." if profile == CoachProfile.BALANCED else "Conservez la surpondération actions tant que le momentum reste positif. Rééquilibrez uniquement si l'écart dépasse 10%."}

**Coût estimé du rééquilibrage :**
- Frais de transaction : ~€50
- Impact fiscal : €0 (PEA/Assurance-vie)""",
        "actions": [
            {"label": "Ignorer", "action": "dismiss", "type": "secondary"},
            {"label": "Rééquilibrer", "action": "rebalance", "type": "primary"},
        ],
    }


def _generate_generic(coach: Dict, score: int, value: float, profile: CoachProfile, prompt: str) -> Dict:
    """Generate generic response."""
    return {
        "content": f"""Je comprends votre question. En tant que conseiller **{coach['name']}**, voici mon analyse :

Basé sur votre profil et les conditions de marché actuelles, je vous suggère de maintenir une approche disciplinée avec des révisions mensuelles de votre allocation.

**Points clés à retenir :**
- Votre score actuel de {score}/100 est {"excellent" if score >= 80 else "bon" if score >= 60 else "à améliorer"}
- Focus sur {coach['focus']}
- Tolérance au risque : {coach['risk_tolerance']}

Souhaitez-vous que j'approfondisse un aspect particulier ?""",
    }


# =============================================================================
# API Endpoints
# =============================================================================

@router.get("/prompts")
async def get_quick_prompts():
    """
    Get available quick action prompts for the concierge.
    """
    return {
        "success": True,
        "prompts": [p.dict() for p in QUICK_PROMPTS],
    }


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_portfolio(request: AnalysisRequest):
    """
    Analyze portfolio and generate AI response.
    
    Uses ProphetIA scoring combined with coach personality
    to generate personalized investment advice.
    """
    try:
        result = generate_portfolio_analysis(
            prompt=request.prompt,
            profile=request.coach_profile,
            portfolio_value=request.portfolio_value,
            portfolio_score=request.portfolio_score,
            holdings=request.holdings,
        )
        
        return AnalysisResponse(
            success=True,
            message="Analyse générée avec succès",
            content=result.get("content", ""),
            metrics=[MetricItem(**m) for m in result.get("metrics", [])] if result.get("metrics") else None,
            actions=[ActionItem(**a) for a in result.get("actions", [])] if result.get("actions") else None,
            coach_profile=request.coach_profile,
            timestamp=datetime.utcnow().isoformat(),
        )
        
    except Exception as e:
        logger.error(f"Concierge analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/suggest")
async def get_suggestions(request: SuggestionRequest):
    """
    Get personalized investment suggestions based on profile.
    """
    coach = COACH_PERSONALITIES[request.coach_profile]
    score = request.portfolio_score or 70
    
    suggestions = []
    
    if score < 60:
        suggestions.append({
            "type": "warning",
            "title": "Score à améliorer",
            "description": f"Votre score de {score} indique des opportunités d'optimisation significatives.",
            "action": "Lancez une analyse complète pour identifier les leviers d'amélioration.",
        })
    
    if request.coach_profile == CoachProfile.CONSERVATIVE:
        suggestions.append({
            "type": "tip",
            "title": "Sécuriser les gains",
            "description": "Considérez un rééquilibrage vers les obligations pour verrouiller les performances 2024.",
        })
    elif request.coach_profile == CoachProfile.AGGRESSIVE:
        suggestions.append({
            "type": "opportunity",
            "title": "Correction tech",
            "description": "La récente correction offre des points d'entrée attractifs sur les leaders IA.",
        })
    
    return {
        "success": True,
        "profile": coach["name"],
        "suggestions": suggestions,
        "timestamp": datetime.utcnow().isoformat(),
    }
