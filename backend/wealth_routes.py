"""
MarketGPS - Wealth Module API Routes
Routes FastAPI pour l'Agent Patrimonial Intelligent.

Endpoints:
- /wealth/geo-context : Contexte géographique
- /wealth/opportunities : Opportunity Radar
- /wealth/visual-inspector : Visual Inspector
- /wealth/pulse : Pulse Feed (avec données réelles)
- /wealth/onboarding : First Day Experience
- /wealth/watchlist : Gestion des watchlists

Data Sources:
- Taux directeurs: ECB, Fed, BoE, BoC APIs
- Actualités: RSS feeds officiels + NewsAPI
- Données marché: INSEE, Eurostat, FHFA, Statistics Canada
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Query, Request, HTTPException, Body, Header
from pydantic import BaseModel, Field

from ai_quota_service import check_gemini_quota

from geo_context_service import geo_context_service, GeoContext
from opportunity_radar import (
    opportunity_radar_service,
    SignalType,
    PropertyType,
    Watchlist,
)
from visual_inspector import visual_inspector_service, VisualAnalysis
from pulse_feed import (
    pulse_feed_service,
    PulseCategory,
    ImpactLevel,
)
from engines.prophetia_scoring import (
    ProphetIAScoring,
    PropertyMetrics,
    ScoreWeights,
    RiskProfile,
)

# Real data providers
from data_providers import (
    CentralBankRatesProvider,
    RealEstateNewsProvider,
    MarketDataProvider,
)
from data_providers.central_bank_rates import get_rates_provider
from data_providers.real_estate_news import get_news_provider
from data_providers.market_data import get_market_provider

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/wealth", tags=["wealth"])


# =============================================================================
# Pydantic Models
# =============================================================================

class GeoContextRequest(BaseModel):
    """Requête pour obtenir le contexte géographique."""
    country: Optional[str] = None
    language: Optional[str] = None


class OpportunityFilters(BaseModel):
    """Filtres pour la recherche d'opportunités."""
    countries: List[str] = Field(default=["FR"])
    cities: Optional[List[str]] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    yield_min: Optional[float] = None
    score_min: Optional[float] = None
    signals_only: bool = False
    limit: int = Field(default=50, le=100)


class VisualInspectorRequest(BaseModel):
    """Requête pour l'analyse visuelle."""
    image_urls: List[str] = Field(..., min_length=1, max_length=10)
    country: str = "FR"
    surface_m2: Optional[float] = None
    listed_price: Optional[float] = None
    listed_positioning: Optional[str] = None


class PulseFilters(BaseModel):
    """Filtres pour le Pulse Feed."""
    countries: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    impact_levels: Optional[List[str]] = None
    limit: int = Field(default=20, le=50)
    offset: int = Field(default=0, ge=0)


class OnboardingAnswers(BaseModel):
    """Réponses de l'onboarding."""
    locations: List[str] = Field(..., description="Pays/villes d'investissement")
    capital_available: float = Field(..., description="Capital disponible en EUR")
    investment_goal: str = Field(..., description="Objectif: 'income' ou 'wealth'")
    risk_profile: Optional[str] = Field(default="balanced", description="Profil de risque")


class WatchlistCreate(BaseModel):
    """Création d'une watchlist."""
    name: str
    countries: List[str] = Field(default=["FR"])
    cities: Optional[List[str]] = None
    property_types: Optional[List[str]] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    yield_min: Optional[float] = None
    score_min: Optional[float] = None
    notify_email: bool = True
    notify_push: bool = True


class PropertyScoreRequest(BaseModel):
    """Requête pour scorer une propriété."""
    purchase_price: float
    annual_rent: float
    annual_expenses: float
    financing_cost: float = 0.0
    year_built: int = 2000
    energy_rating: str = "C"
    building_condition: str = "good"
    vacancy_rate: float = 0.05
    property_tax_rate: float = 0.01
    rent_control: bool = False
    risk_profile: str = "balanced"
    country: str = "FR"


# =============================================================================
# Geo-Context Endpoints
# =============================================================================

@router.get("/geo-context")
async def get_geo_context(
    request: Request,
    country: Optional[str] = Query(None, description="Code pays forcé"),
    language: Optional[str] = Query(None, description="Langue forcée"),
) -> Dict[str, Any]:
    """
    Obtenir le contexte géographique automatique ou personnalisé.
    
    Détecte automatiquement:
    - Pays et ville via IP
    - Langue via Accept-Language
    - Devise, unités, terminologie
    - Market Pulse local
    """
    # Récupérer l'IP client
    ip_address = request.client.host if request.client else None
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        ip_address = forwarded.split(",")[0].strip()
    
    # Récupérer Accept-Language
    accept_language = request.headers.get("Accept-Language")
    
    context = geo_context_service.get_context(
        ip_address=ip_address,
        accept_language=accept_language,
        user_country=country,
        user_language=language,
    )
    
    return context.to_dict()


@router.get("/geo-context/countries")
async def get_supported_countries() -> List[Dict[str, Any]]:
    """
    Récupérer la liste des pays supportés.
    """
    return geo_context_service.get_supported_countries()


@router.get("/geo-context/market-pulse/{country}")
async def get_market_pulse(
    country: str,
    city: Optional[str] = Query(None),
) -> Dict[str, Any]:
    """
    Obtenir le Market Pulse pour un pays/ville.
    
    Inclut:
    - Taux directeur de la banque centrale
    - Prix moyen au m²
    - Loyer moyen au m²
    - Tendances du marché
    """
    pulse = geo_context_service.get_market_pulse(country, city)
    return pulse.to_dict()


# =============================================================================
# Opportunity Radar Endpoints
# =============================================================================

@router.post("/opportunities")
async def get_opportunities(
    filters: OpportunityFilters,
) -> Dict[str, Any]:
    """
    Rechercher des opportunités immobilières.
    
    Retourne des annonces pré-scorées avec détection de signaux:
    - Baisse de prix
    - Annonce réactivée
    - Longue durée sur marché
    - Yield anormal
    - Sous-coté
    - Zone en accélération
    """
    opportunities = opportunity_radar_service.get_opportunities(
        countries=filters.countries,
        cities=filters.cities,
        price_min=filters.price_min,
        price_max=filters.price_max,
        yield_min=filters.yield_min,
        score_min=filters.score_min,
        signals_only=filters.signals_only,
        limit=filters.limit,
    )
    
    return {
        "opportunities": opportunities,
        "total": len(opportunities),
        "filters_applied": filters.model_dump(),
    }


@router.get("/opportunities/summary")
async def get_opportunities_summary(
    countries: str = Query("FR", description="Codes pays séparés par virgule"),
) -> Dict[str, Any]:
    """
    Résumé des opportunités pour le dashboard.
    
    Retourne:
    - Nombre total d'opportunités
    - Répartition par type de signal
    - Top 5 opportunités
    """
    country_list = [c.strip() for c in countries.split(",")]
    return opportunity_radar_service.get_signals_summary(country_list)


@router.get("/opportunities/{listing_id}")
async def get_opportunity_detail(
    listing_id: str,
) -> Dict[str, Any]:
    """
    Détail d'une opportunité spécifique.
    """
    # Pour la démo, régénérer les opportunités et chercher
    opportunities = opportunity_radar_service.get_opportunities(
        countries=["FR", "BE", "UK", "US", "CA"],
        limit=100,
    )
    
    for opp in opportunities:
        if opp["listing"]["id"] == listing_id:
            return opp
    
    raise HTTPException(status_code=404, detail="Listing not found")


# =============================================================================
# Visual Inspector Endpoints
# =============================================================================

@router.post("/visual-inspector")
async def analyze_images(
    request: VisualInspectorRequest,
    authorization: Optional[str] = Header(None, alias="Authorization")
) -> Dict[str, Any]:
    """
    Analyser des images d'un bien immobilier.
    
    Retourne:
    - État général du bien
    - Éléments détectés (fenêtres, sol, cuisine...)
    - Estimation des travaux
    - Détection surcote/sous-cote
    - Points forts et faibles
    
    Note: Limited to 50 Gemini requests per user. Contact support to renew.
    """
    # Get user ID from authorization header
    user_id = "default"
    if authorization:
        try:
            from security import verify_supabase_token
            parts = authorization.split()
            if len(parts) == 2 and parts[0].lower() == "bearer":
                payload = verify_supabase_token(parts[1])
                if payload and payload.get("sub"):
                    user_id = payload["sub"]
        except Exception as e:
            pass
    
    # Check and consume Gemini quota
    quota_result = check_gemini_quota(user_id)
    if not quota_result["allowed"]:
        raise HTTPException(status_code=429, detail=quota_result["message"])
    
    analysis = await visual_inspector_service.analyze_images(
        image_urls=request.image_urls,
        country=request.country,
        surface_m2=request.surface_m2,
        listed_price=request.listed_price,
        listed_positioning=request.listed_positioning,
    )
    
    return analysis.to_dict()


@router.get("/visual-inspector/renovation-costs/{country}")
async def get_renovation_costs(
    country: str,
) -> Dict[str, Any]:
    """
    Obtenir les coûts de rénovation par type pour un pays.
    """
    costs = geo_context_service.get_renovation_costs(country)
    return {
        "country": country,
        "costs": costs,
        "currency": "EUR" if country.upper() in ["FR", "BE", "DE", "ES", "IT"] else "USD" if country.upper() == "US" else "GBP" if country.upper() == "UK" else "CAD",
    }


# =============================================================================
# Pulse Feed Endpoints
# =============================================================================

@router.post("/pulse")
async def get_pulse_items(
    filters: PulseFilters,
) -> Dict[str, Any]:
    """
    Récupérer les éléments du Pulse Feed.
    
    Actualités classées par:
    - Catégorie (réglementation, taux, marché, local)
    - Niveau d'impact (critical, high, medium, low)
    - Pays concernés
    """
    categories = None
    if filters.categories:
        categories = [PulseCategory(c) for c in filters.categories]
    
    impact_levels = None
    if filters.impact_levels:
        impact_levels = [ImpactLevel(l) for l in filters.impact_levels]
    
    items = pulse_feed_service.get_pulse_items(
        countries=filters.countries,
        categories=categories,
        impact_levels=impact_levels,
        limit=filters.limit,
        offset=filters.offset,
    )
    
    return {
        "items": [item.to_dict() for item in items],
        "total": len(items),
    }


@router.get("/pulse/summary")
async def get_pulse_summary(
    countries: Optional[str] = Query(None, description="Codes pays séparés par virgule"),
) -> Dict[str, Any]:
    """
    Résumé du Pulse Feed pour le dashboard.
    
    Inclut:
    - Taux directeurs pertinents
    - Nombre d'items par catégorie/impact
    - Items nécessitant une action
    """
    country_list = None
    if countries:
        country_list = [c.strip() for c in countries.split(",")]
    
    return pulse_feed_service.get_pulse_summary(countries=country_list)


@router.get("/pulse/rates")
async def get_central_bank_rates(
    countries: Optional[str] = Query(None, description="Codes pays séparés par virgule"),
) -> List[Dict[str, Any]]:
    """
    Récupérer les taux directeurs des banques centrales.
    
    Sources RÉELLES:
    - ECB: data.ecb.europa.eu
    - Fed: FRED API (fred.stlouisfed.org)
    - BoE: bankofengland.co.uk
    - BoC: bankofcanada.ca/valet
    """
    try:
        # Use real data provider
        rates_provider = get_rates_provider()
        rates = await rates_provider.get_all_rates()
        
        # Filter by countries if specified
        if countries:
            country_list = [c.strip().upper() for c in countries.split(",")]
            rates = [r for r in rates if any(
                c in r.countries for c in country_list
            )]
        
        return [r.to_dict() for r in rates]
        
    except Exception as e:
        logger.error(f"Failed to fetch real rates, falling back: {e}")
        # Fallback to old service
        country_list = None
        if countries:
            country_list = [c.strip() for c in countries.split(",")]
        rates = pulse_feed_service.get_central_bank_rates(countries=country_list)
        return [r.to_dict() for r in rates]


@router.post("/pulse/portfolio-impact")
async def calculate_portfolio_impact(
    pulse_item_id: str = Body(...),
    portfolio_properties: List[Dict[str, Any]] = Body(...),
) -> Dict[str, Any]:
    """
    Calculer l'impact d'une actualité sur un portefeuille.
    """
    impact = pulse_feed_service.calculate_portfolio_impact(
        pulse_item_id=pulse_item_id,
        portfolio_properties=portfolio_properties,
    )
    
    if not impact:
        raise HTTPException(status_code=404, detail="Pulse item not found")
    
    return impact.__dict__


# =============================================================================
# Onboarding / First Day Experience
# =============================================================================

@router.post("/onboarding")
async def complete_onboarding(
    answers: OnboardingAnswers,
) -> Dict[str, Any]:
    """
    Compléter l'onboarding et recevoir un plan d'action personnalisé.
    
    Basé sur les réponses, génère:
    - Opportunités recommandées
    - Watchlist configurée automatiquement
    - Plan d'action personnalisé
    """
    # Déterminer les critères de recherche
    countries = []
    cities = []
    for loc in answers.locations:
        loc_upper = loc.upper().strip()
        if loc_upper in ["FR", "BE", "DE", "UK", "US", "CA", "ES", "IT"]:
            countries.append(loc_upper)
        else:
            cities.append(loc.strip())
    
    if not countries:
        countries = ["FR"]  # Défaut
    
    # Définir le budget max
    price_max = answers.capital_available * 4  # Avec emprunt ~75%
    
    # Définir les critères selon l'objectif
    if answers.investment_goal == "income":
        yield_min = 5.0
        score_min = 60
        property_types = ["studio", "apartment"]
        description = "Rente mensuelle maximisée"
    else:
        yield_min = 3.5
        score_min = 70
        property_types = ["apartment", "house", "duplex"]
        description = "Patrimoine long terme"
    
    # Récupérer les opportunités correspondantes
    opportunities = opportunity_radar_service.get_opportunities(
        countries=countries,
        cities=cities if cities else None,
        price_max=price_max,
        yield_min=yield_min,
        score_min=score_min,
        limit=5,
    )
    
    # Créer une watchlist automatique
    watchlist_name = f"Surveillance {answers.investment_goal.capitalize()}"
    watchlist_criteria = {
        "countries": countries,
        "cities": cities if cities else None,
        "price_max": price_max,
        "yield_min": yield_min,
        "score_min": score_min,
        "property_types": property_types,
    }
    
    # Générer le plan d'action
    if answers.investment_goal == "income":
        action_plan = [
            {
                "step": 1,
                "title": "Cibler les petites surfaces",
                "description": f"Avec {answers.capital_available:,.0f}€, privilégiez les studios/T2 pour maximiser le rendement.",
                "priority": "high",
            },
            {
                "step": 2,
                "title": "Vérifier la demande locative",
                "description": "Zones étudiantes, transports, emploi. Vacance minimale = revenus stables.",
                "priority": "high",
            },
            {
                "step": 3,
                "title": "Optimiser la fiscalité",
                "description": "LMNP en France, régime meublé recommandé pour déduire les charges.",
                "priority": "medium",
            },
            {
                "step": 4,
                "title": "Surveiller les signaux",
                "description": "Nous vous alertons automatiquement sur les baisses de prix et yields anormaux.",
                "priority": "medium",
            },
        ]
    else:
        action_plan = [
            {
                "step": 1,
                "title": "Privilégier les emplacements premium",
                "description": "Quartiers en développement, nouvelles infrastructures, écoles réputées.",
                "priority": "high",
            },
            {
                "step": 2,
                "title": "Optimiser l'effet de levier",
                "description": f"Avec {answers.capital_available:,.0f}€ d'apport, visez jusqu'à {price_max:,.0f}€ de patrimoine.",
                "priority": "high",
            },
            {
                "step": 3,
                "title": "Diversifier géographiquement",
                "description": "Répartissez sur plusieurs villes/pays pour limiter le risque.",
                "priority": "medium",
            },
            {
                "step": 4,
                "title": "Anticiper les plus-values",
                "description": "Nous surveillons les zones en accélération pour vous.",
                "priority": "medium",
            },
        ]
    
    # Résumé Market Pulse
    pulses = []
    for country in countries[:2]:
        pulse = geo_context_service.get_market_pulse(country)
        pulses.append(pulse.to_dict())
    
    return {
        "success": True,
        "profile": {
            "locations": answers.locations,
            "capital": answers.capital_available,
            "goal": answers.investment_goal,
            "risk_profile": answers.risk_profile,
        },
        "opportunities": opportunities[:3],
        "watchlist": {
            "name": watchlist_name,
            "description": description,
            "criteria": watchlist_criteria,
            "status": "active",
        },
        "action_plan": action_plan,
        "market_pulse": pulses,
        "next_steps": [
            "Explorez les opportunités recommandées",
            "Affinez votre watchlist si nécessaire",
            "Activez les notifications push",
        ],
    }


@router.get("/onboarding/demo-portfolio")
async def get_demo_portfolio() -> Dict[str, Any]:
    """
    Obtenir un portefeuille de démonstration premium.
    
    Utilisé lors du premier chargement pour montrer les capacités
    de la plateforme avant que l'utilisateur n'ait de données.
    """
    return {
        "properties": [
            {
                "id": "demo-paris",
                "name": "Appartement Marais",
                "city": "Paris",
                "country": "FR",
                "type": "apartment",
                "surface_m2": 42,
                "purchase_price": 485000,
                "current_value": 520000,
                "acquisition_date": "2022-03-15",
                "annual_rent": 21600,
                "annual_expenses": 5400,
                "annual_cashflow": 8200,
                "yield_gross": 4.45,
                "yield_net": 3.34,
                "prophetia_score": 74,
                "energy_rating": "D",
                "status": "rented",
            },
            {
                "id": "demo-berlin",
                "name": "Studio Kreuzberg",
                "city": "Berlin",
                "country": "DE",
                "type": "studio",
                "surface_m2": 35,
                "purchase_price": 285000,
                "current_value": 275000,
                "acquisition_date": "2023-06-20",
                "annual_rent": 12600,
                "annual_expenses": 3150,
                "annual_cashflow": 4800,
                "yield_gross": 4.42,
                "yield_net": 3.32,
                "prophetia_score": 68,
                "energy_rating": "C",
                "status": "rented",
            },
            {
                "id": "demo-montreal",
                "name": "Duplex Plateau",
                "city": "Montréal",
                "country": "CA",
                "type": "duplex",
                "surface_m2": 145,
                "purchase_price": 680000,
                "current_value": 725000,
                "acquisition_date": "2021-09-01",
                "annual_rent": 42000,
                "annual_expenses": 10500,
                "annual_cashflow": 18500,
                "yield_gross": 6.18,
                "yield_net": 4.63,
                "prophetia_score": 82,
                "energy_rating": "C",
                "status": "rented",
            },
        ],
        "summary": {
            "total_value": 1520000,
            "total_invested": 1450000,
            "total_annual_rent": 76200,
            "total_annual_cashflow": 31500,
            "portfolio_yield_gross": 5.01,
            "portfolio_yield_net": 3.76,
            "weighted_score": 75,
            "countries": ["FR", "DE", "CA"],
            "properties_count": 3,
        },
        "alerts": [
            {
                "type": "energy",
                "severity": "warning",
                "property_id": "demo-paris",
                "message": "DPE D - Planifier rénovation avant 2034",
            },
            {
                "type": "market",
                "severity": "info",
                "property_id": "demo-montreal",
                "message": "Zone Plateau +12% transactions - Marché dynamique",
            },
        ],
    }


# =============================================================================
# Scoring Endpoint
# =============================================================================

@router.post("/score")
async def score_property(
    request: PropertyScoreRequest,
) -> Dict[str, Any]:
    """
    Calculer le score ProphetIA pour une propriété.
    """
    # Configurer le scorer selon le profil de risque
    try:
        profile = RiskProfile(request.risk_profile)
    except ValueError:
        profile = RiskProfile.BALANCED
    
    weights = ScoreWeights.for_profile(profile)
    scorer = ProphetIAScoring(weights=weights, jurisdiction=request.country)
    
    # Construire les métriques
    metrics = PropertyMetrics(
        purchase_price=request.purchase_price,
        annual_rent=request.annual_rent,
        annual_expenses=request.annual_expenses,
        financing_cost=request.financing_cost,
        year_built=request.year_built,
        energy_rating=request.energy_rating,
        building_condition=request.building_condition,
        vacancy_rate_area=request.vacancy_rate,
        property_tax_rate=request.property_tax_rate,
        rent_control=request.rent_control,
    )
    
    # Calculer le score
    score = scorer.score(metrics)
    
    return {
        "total_score": score.total_score,
        "rating": score.rating,
        "recommendation": score.recommendation,
        "yield_score": score.yield_score,
        "safety_score": score.safety_score,
        "growth_score": score.growth_score,
        "legal_score": score.legal_score,
        "confidence": score.confidence,
        "risk_flags": score.risk_flags,
        "opportunities": score.opportunities,
        "breakdown": score.breakdown,
    }


# =============================================================================
# Watchlist Endpoints (Placeholder - would use database)
# =============================================================================

# In-memory storage for demo
_watchlists: Dict[str, Dict[str, Any]] = {}


@router.post("/watchlist")
async def create_watchlist(
    watchlist: WatchlistCreate,
    user_id: str = Query("demo-user"),
) -> Dict[str, Any]:
    """
    Créer une nouvelle watchlist.
    """
    import uuid
    
    watchlist_id = str(uuid.uuid4())[:8]
    
    data = {
        "id": watchlist_id,
        "user_id": user_id,
        "name": watchlist.name,
        "countries": watchlist.countries,
        "cities": watchlist.cities,
        "property_types": watchlist.property_types,
        "price_min": watchlist.price_min,
        "price_max": watchlist.price_max,
        "yield_min": watchlist.yield_min,
        "score_min": watchlist.score_min,
        "notify_email": watchlist.notify_email,
        "notify_push": watchlist.notify_push,
        "is_active": True,
        "created_at": datetime.utcnow().isoformat(),
        "match_count": 0,
    }
    
    _watchlists[watchlist_id] = data
    
    return {"success": True, "watchlist": data}


@router.get("/watchlist")
async def get_watchlists(
    user_id: str = Query("demo-user"),
) -> List[Dict[str, Any]]:
    """
    Récupérer les watchlists d'un utilisateur.
    """
    return [
        w for w in _watchlists.values()
        if w.get("user_id") == user_id
    ]


@router.delete("/watchlist/{watchlist_id}")
async def delete_watchlist(
    watchlist_id: str,
) -> Dict[str, Any]:
    """
    Supprimer une watchlist.
    """
    if watchlist_id in _watchlists:
        del _watchlists[watchlist_id]
        return {"success": True}
    
    raise HTTPException(status_code=404, detail="Watchlist not found")


@router.get("/watchlist/{watchlist_id}/matches")
async def get_watchlist_matches(
    watchlist_id: str,
) -> Dict[str, Any]:
    """
    Récupérer les opportunités correspondant à une watchlist.
    """
    if watchlist_id not in _watchlists:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    
    watchlist = _watchlists[watchlist_id]
    
    opportunities = opportunity_radar_service.get_opportunities(
        countries=watchlist.get("countries", ["FR"]),
        cities=watchlist.get("cities"),
        price_min=watchlist.get("price_min"),
        price_max=watchlist.get("price_max"),
        yield_min=watchlist.get("yield_min"),
        score_min=watchlist.get("score_min"),
        limit=20,
    )
    
    return {
        "watchlist": watchlist,
        "matches": opportunities,
        "match_count": len(opportunities),
    }


# =============================================================================
# Real Data Endpoints (Live Sources)
# =============================================================================

@router.get("/live/news")
async def get_live_news(
    countries: Optional[str] = Query("FR", description="Codes pays séparés par virgule"),
    categories: Optional[str] = Query(None, description="Catégories: regulation,rates,market,local,fiscal,energy"),
    limit: int = Query(20, le=50),
) -> Dict[str, Any]:
    """
    Récupérer les actualités immobilières EN TEMPS RÉEL.
    
    Sources:
    - RSS Les Échos Immobilier
    - RSS Le Figaro Immobilier
    - Légifrance (réglementation)
    - ECB/Fed/BoE Press (taux)
    - NewsAPI (si clé configurée)
    """
    try:
        news_provider = get_news_provider()
        
        country_list = [c.strip().upper() for c in countries.split(",")] if countries else None
        category_list = [c.strip() for c in categories.split(",")] if categories else None
        
        news_items = await news_provider.get_news(
            countries=country_list,
            categories=category_list,
            limit=limit,
        )
        
        return {
            "items": [item.to_dict() for item in news_items],
            "total": len(news_items),
            "sources": list(set(item.source for item in news_items)),
            "live": True,
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch live news: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch news: {str(e)}")


@router.get("/live/market-stats")
async def get_live_market_stats(
    country: str = Query(..., description="Code pays (FR, US, UK, etc.)"),
    city: Optional[str] = Query(None, description="Nom de la ville"),
) -> Dict[str, Any]:
    """
    Récupérer les statistiques de marché immobilier.
    
    Sources officielles:
    - FR: INSEE, Notaires de France
    - DE: Destatis
    - UK: ONS, Land Registry
    - US: FHFA, Census Bureau
    - CA: CREA, Statistics Canada
    - BE: Statbel
    - ES: INE
    - IT: ISTAT
    """
    try:
        market_provider = get_market_provider()
        stats = await market_provider.get_market_stats(country, city)
        
        if not stats:
            raise HTTPException(
                status_code=404, 
                detail=f"No market data for {country}" + (f"/{city}" if city else "")
            )
        
        return stats.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch market stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch market data: {str(e)}")


@router.get("/live/market-stats/cities")
async def get_available_cities(
    country: str = Query(..., description="Code pays"),
) -> Dict[str, Any]:
    """
    Récupérer les villes disponibles pour un pays.
    """
    market_provider = get_market_provider()
    cities = await market_provider.get_all_cities(country)
    
    return {
        "country": country,
        "cities": cities,
    }


@router.get("/live/market-stats/countries")
async def get_available_countries() -> Dict[str, Any]:
    """
    Récupérer les pays avec données de marché disponibles.
    """
    market_provider = get_market_provider()
    countries = await market_provider.get_available_countries()
    
    return {
        "countries": countries,
    }


@router.get("/data-sources")
async def get_data_sources() -> Dict[str, Any]:
    """
    Documentation des sources de données utilisées.
    """
    return {
        "central_bank_rates": {
            "description": "Taux directeurs des banques centrales",
            "sources": [
                {
                    "name": "ECB",
                    "url": "https://data.ecb.europa.eu/",
                    "coverage": ["FR", "DE", "BE", "ES", "IT", "NL", "AT", "PT", "IE", "FI", "LU"],
                    "update_frequency": "After each Governing Council meeting (~6 weeks)",
                },
                {
                    "name": "Federal Reserve (FRED)",
                    "url": "https://fred.stlouisfed.org/",
                    "coverage": ["US"],
                    "update_frequency": "After each FOMC meeting (~6 weeks)",
                    "api_key_required": True,
                },
                {
                    "name": "Bank of England",
                    "url": "https://www.bankofengland.co.uk/",
                    "coverage": ["UK"],
                    "update_frequency": "After each MPC meeting (~6 weeks)",
                },
                {
                    "name": "Bank of Canada",
                    "url": "https://www.bankofcanada.ca/valet/",
                    "coverage": ["CA"],
                    "update_frequency": "8 times per year",
                },
            ],
        },
        "real_estate_news": {
            "description": "Actualités immobilières et réglementaires",
            "sources": [
                {"name": "Les Échos Immobilier", "type": "RSS", "coverage": ["FR"]},
                {"name": "Le Figaro Immobilier", "type": "RSS", "coverage": ["FR"]},
                {"name": "Légifrance", "type": "RSS", "coverage": ["FR"], "category": "regulation"},
                {"name": "ECB Press", "type": "RSS", "coverage": ["EU"], "category": "rates"},
                {"name": "Federal Reserve", "type": "RSS", "coverage": ["US"], "category": "rates"},
                {"name": "NewsAPI", "type": "API", "coverage": ["global"], "api_key_required": True},
            ],
        },
        "market_statistics": {
            "description": "Statistiques de marché immobilier",
            "sources": [
                {"name": "INSEE", "coverage": ["FR"], "metrics": ["prices", "rents", "transactions"]},
                {"name": "Notaires de France", "coverage": ["FR"], "metrics": ["prices", "transactions"]},
                {"name": "Destatis", "coverage": ["DE"], "metrics": ["prices", "rents"]},
                {"name": "ONS/Land Registry", "coverage": ["UK"], "metrics": ["prices", "transactions"]},
                {"name": "FHFA/Census Bureau", "coverage": ["US"], "metrics": ["prices", "rents", "vacancy"]},
                {"name": "CREA/Statistics Canada", "coverage": ["CA"], "metrics": ["prices", "transactions"]},
                {"name": "Statbel", "coverage": ["BE"], "metrics": ["prices", "transactions"]},
                {"name": "INE", "coverage": ["ES"], "metrics": ["prices", "rents"]},
                {"name": "ISTAT", "coverage": ["IT"], "metrics": ["prices", "rents"]},
            ],
            "update_frequency": "Updated from official sources (quarterly/monthly depending on source)",
        },
        "visual_analysis": {
            "description": "Analyse visuelle des biens",
            "sources": [
                {
                    "name": "Google Gemini Vision",
                    "type": "AI API",
                    "api_key_required": True,
                    "env_var": "GEMINI_API_KEY",
                },
            ],
        },
    }
