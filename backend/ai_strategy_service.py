"""
AI Strategy Service - Connects to ChatGPT for intelligent strategy suggestions
"""
import os
import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import httpx

logger = logging.getLogger(__name__)

# OpenAI API Configuration
# Set OPENAI_API_KEY environment variable to enable AI strategy generation
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"


@dataclass
class AIStrategyRecommendation:
    """Structure for AI strategy recommendation"""
    strategy_name: str
    description: str
    risk_profile: str  # conservative, balanced, growth, aggressive
    investment_horizon: int  # years
    rationale: str
    blocks: List[Dict[str, Any]]  # [{name, description, target_weight, asset_types, sectors}]
    key_principles: List[str]
    warnings: List[str]


SYSTEM_PROMPT = """Tu es un conseiller en investissement expert, spécialisé dans la construction de portefeuilles institutionnels. 
Tu analyses les demandes des utilisateurs et proposes des stratégies d'investissement personnalisées.

IMPORTANT: Tu dois TOUJOURS répondre en JSON valide avec la structure exacte suivante:

{
    "strategy_name": "Nom court et mémorable de la stratégie",
    "description": "Description détaillée de la stratégie en 2-3 phrases",
    "risk_profile": "conservative|balanced|growth|aggressive",
    "investment_horizon": 10,
    "rationale": "Explication détaillée du raisonnement derrière cette stratégie, pourquoi ces choix, comment ils s'articulent ensemble",
    "blocks": [
        {
            "name": "Nom du bloc (ex: Core Equity)",
            "description": "Description du rôle de ce bloc",
            "target_weight": 0.40,
            "asset_types": ["ETF", "EQUITY"],
            "sectors": ["Technology", "Healthcare"],
            "criteria": {
                "min_score": 50,
                "max_volatility": 25,
                "min_dividend_yield": 0
            }
        }
    ],
    "key_principles": [
        "Principe 1 de la stratégie",
        "Principe 2 de la stratégie"
    ],
    "warnings": [
        "Avertissement ou risque potentiel"
    ]
}

RÈGLES:
1. Les weights de tous les blocks doivent sommer à 1.0 (100%)
2. Chaque block doit avoir entre 1 et 4 asset_types parmi: ETF, EQUITY, BOND, OPTION, FUTURE, CRYPTO, COMMODITY, FX
3. Les secteurs peuvent inclure: Technology, Healthcare, Finance, Energy, Consumer, Industrial, Materials, Utilities, Real Estate, Communication
4. Le risk_profile doit correspondre à la volatilité acceptée par l'utilisateur
5. Fournis toujours un rationale détaillé expliquant le "pourquoi" de chaque choix
6. Les warnings doivent être pertinents et honnêtes sur les risques
7. Réponds UNIQUEMENT en JSON, sans texte avant ou après
"""


async def get_ai_strategy_suggestion(user_description: str) -> Dict[str, Any]:
    """
    Send user's strategy description to ChatGPT and get structured recommendations.
    """
    if not OPENAI_API_KEY or OPENAI_API_KEY.startswith("sk-proj-xxx"):
        raise ValueError("OpenAI API key not configured")
    
    user_prompt = f"""L'utilisateur décrit sa stratégie d'investissement comme suit:

"{user_description}"

Analyse cette demande et propose une stratégie d'investissement complète et personnalisée.
Assure-toi que:
1. La stratégie correspond au profil de risque implicite de l'utilisateur
2. Les allocations sont cohérentes et réalistes
3. Le rationale explique clairement pourquoi cette stratégie répond aux besoins exprimés
4. Les warnings sont honnêtes sur les risques potentiels

Réponds en JSON valide uniquement."""

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 2000
    }
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                OPENAI_API_URL,
                headers=headers,
                json=payload
            )
            
            if response.status_code != 200:
                logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
                raise Exception(f"OpenAI API error: {response.status_code}")
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            # Parse JSON response
            # Clean up potential markdown code blocks
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            content = content.strip()
            
            strategy_data = json.loads(content)
            
            # Validate structure
            required_fields = ["strategy_name", "description", "risk_profile", "blocks", "rationale"]
            for field in required_fields:
                if field not in strategy_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Validate block weights sum to 1.0
            total_weight = sum(block.get("target_weight", 0) for block in strategy_data["blocks"])
            if abs(total_weight - 1.0) > 0.05:
                # Normalize weights
                for block in strategy_data["blocks"]:
                    block["target_weight"] = block.get("target_weight", 0) / total_weight
            
            return strategy_data
            
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AI response as JSON: {e}")
        raise Exception("L'IA n'a pas pu générer une stratégie valide. Veuillez réessayer.")
    except Exception as e:
        logger.error(f"AI strategy suggestion error: {e}")
        raise


async def match_assets_to_strategy(
    strategy_blocks: List[Dict[str, Any]],
    available_assets: List[Dict[str, Any]]
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Match assets from our universe to each strategy block based on criteria.
    """
    matched_assets = {}
    
    for block in strategy_blocks:
        block_name = block.get("name", "Unknown")
        target_types = [t.upper() for t in block.get("asset_types", ["ETF", "EQUITY"])]
        target_sectors = [s.lower() for s in block.get("sectors", [])]
        criteria = block.get("criteria", {})
        
        min_score = criteria.get("min_score", 40)
        max_volatility = criteria.get("max_volatility", 50)
        
        matching = []
        
        for asset in available_assets:
            # Check asset type
            asset_type = asset.get("asset_type", "EQUITY").upper()
            if asset_type not in target_types:
                continue
            
            # Check score
            score = asset.get("score_total") or asset.get("score", 0)
            if score < min_score:
                continue
            
            # Check volatility
            volatility = asset.get("vol_annual", 0) or 0
            if volatility > max_volatility:
                continue
            
            # Check sector if specified
            asset_sector = (asset.get("sector") or "").lower()
            if target_sectors and asset_sector and asset_sector not in target_sectors:
                continue
            
            # Asset matches criteria
            matching.append({
                "ticker": asset.get("ticker") or asset.get("symbol"),
                "name": asset.get("name", ""),
                "asset_type": asset_type,
                "score": score,
                "volatility": volatility,
                "sector": asset_sector,
            })
        
        # Sort by score and take top 10
        matching.sort(key=lambda x: x.get("score", 0), reverse=True)
        matched_assets[block_name] = matching[:10]
    
    return matched_assets


def generate_strategy_explanation(strategy_data: Dict[str, Any], matched_assets: Dict[str, List]) -> str:
    """
    Generate a human-readable explanation of the strategy.
    """
    lines = []
    
    lines.append(f"## 📊 {strategy_data.get('strategy_name', 'Votre Stratégie')}")
    lines.append("")
    lines.append(strategy_data.get('description', ''))
    lines.append("")
    
    # Risk profile
    risk_labels = {
        "conservative": "🛡️ Conservateur",
        "balanced": "⚖️ Équilibré", 
        "growth": "📈 Croissance",
        "aggressive": "🚀 Dynamique"
    }
    risk = strategy_data.get("risk_profile", "balanced")
    lines.append(f"**Profil de risque:** {risk_labels.get(risk, risk)}")
    lines.append(f"**Horizon d'investissement:** {strategy_data.get('investment_horizon', 10)} ans")
    lines.append("")
    
    # Rationale
    lines.append("### 💡 Pourquoi cette stratégie ?")
    lines.append(strategy_data.get('rationale', ''))
    lines.append("")
    
    # Blocks
    lines.append("### 🧱 Composition du portefeuille")
    for block in strategy_data.get("blocks", []):
        weight_pct = int(block.get("target_weight", 0) * 100)
        lines.append(f"- **{block.get('name')}** ({weight_pct}%): {block.get('description', '')}")
        
        # Show matched assets
        block_assets = matched_assets.get(block.get("name"), [])
        if block_assets:
            asset_tickers = [a["ticker"] for a in block_assets[:5]]
            lines.append(f"  - Actifs suggérés: {', '.join(asset_tickers)}")
    
    lines.append("")
    
    # Key principles
    if strategy_data.get("key_principles"):
        lines.append("### ✅ Principes clés")
        for principle in strategy_data["key_principles"]:
            lines.append(f"- {principle}")
        lines.append("")
    
    # Warnings
    if strategy_data.get("warnings"):
        lines.append("### ⚠️ Points d'attention")
        for warning in strategy_data["warnings"]:
            lines.append(f"- {warning}")
    
    return "\n".join(lines)
