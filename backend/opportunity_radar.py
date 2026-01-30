"""
MarketGPS - Opportunity Radar
Scanner de marché avec détection de signaux et pré-scoring ProphetIA.

Fonctionnalités:
- Modèle de données normalisé pour les annonces
- Détection de 6 types de signaux d'opportunité
- Intégration avec ProphetIA pour scoring
- Génération de notifications intelligentes
"""

import logging
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, List, Any, Tuple
from enum import Enum
from datetime import datetime, timedelta
from decimal import Decimal
import hashlib
import json
import random

from engines.prophetia_scoring import ProphetIAScoring, PropertyMetrics, ProphetIAScore, ScoreWeights, RiskProfile

logger = logging.getLogger(__name__)


# =============================================================================
# Enums et Types
# =============================================================================

class PropertyType(str, Enum):
    APARTMENT = "apartment"
    HOUSE = "house"
    STUDIO = "studio"
    DUPLEX = "duplex"
    TRIPLEX = "triplex"
    BUILDING = "building"
    COMMERCIAL = "commercial"
    LAND = "land"
    PARKING = "parking"


class ListingSource(str, Enum):
    SELOGER = "seloger"
    LEBONCOIN = "leboncoin"
    PAP = "pap"
    IMMOWEB = "immoweb"
    ZIMMO = "zimmo"
    IMMOSCOUT24 = "immobilienscout24"
    RIGHTMOVE = "rightmove"
    ZOOPLA = "zoopla"
    ZILLOW = "zillow"
    REDFIN = "redfin"
    REALTOR_CA = "realtor_ca"
    CENTRIS = "centris"
    MANUAL = "manual"


class SignalType(str, Enum):
    PRICE_DROP = "price_drop"           # Baisse de prix > 3%
    REACTIVATED = "reactivated"          # Annonce republiée
    LONG_LISTING = "long_listing"        # > 60 jours sur marché
    YIELD_ANOMALY = "yield_anomaly"      # Yield > 1.5σ du quartier
    UNDERPRICED = "underpriced"          # Prix < P25 du quartier
    ZONE_ACCELERATION = "zone_acceleration"  # Transactions +20% QoQ


class SignalPriority(str, Enum):
    CRITICAL = "critical"  # Action immédiate recommandée
    HIGH = "high"          # Opportunité rare
    MEDIUM = "medium"      # À surveiller
    LOW = "low"            # Information


# =============================================================================
# Modèles de données
# =============================================================================

@dataclass
class PriceChange:
    """Historique de changement de prix."""
    date: str
    old_price: float
    new_price: float
    change_percent: float


@dataclass
class NormalizedListing:
    """
    Annonce immobilière normalisée.
    Format unifié pour toutes les sources.
    """
    # Identifiants
    id: str                          # UUID interne MarketGPS
    source_id: str                   # ID sur la source originale
    source: ListingSource
    
    # Localisation
    country: str                     # Code ISO
    city: str
    postal_code: str
    neighborhood: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    
    # Caractéristiques du bien
    property_type: PropertyType = PropertyType.APARTMENT
    surface_m2: float = 0.0
    rooms: Optional[int] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    floor: Optional[int] = None
    total_floors: Optional[int] = None
    has_elevator: Optional[bool] = None
    has_balcony: Optional[bool] = None
    has_terrace: Optional[bool] = None
    has_parking: Optional[bool] = None
    has_garage: Optional[bool] = None
    has_garden: Optional[bool] = None
    orientation: Optional[str] = None  # N, S, E, W, NE, etc.
    
    # Construction
    construction_year: Optional[int] = None
    renovation_year: Optional[int] = None
    building_condition: str = "good"  # excellent, good, fair, poor, to_renovate
    energy_rating: Optional[str] = None  # A-G
    ghg_rating: Optional[str] = None  # A-G (GES)
    
    # Prix
    price: float = 0.0
    currency: str = "EUR"
    price_per_m2: float = 0.0
    charges_monthly: Optional[float] = None
    property_tax_annual: Optional[float] = None
    
    # Location (si investissement locatif)
    is_rented: bool = False
    current_rent_monthly: Optional[float] = None
    rental_yield_gross: Optional[float] = None
    
    # Méta
    title: str = ""
    description: str = ""
    images: List[str] = field(default_factory=list)
    url: str = ""
    agent_name: Optional[str] = None
    agent_phone: Optional[str] = None
    
    # Timestamps
    published_at: Optional[str] = None
    updated_at: Optional[str] = None
    scraped_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    # Signaux détectés (remplis par le système)
    days_on_market: int = 0
    price_changes: List[PriceChange] = field(default_factory=list)
    is_reactivated: bool = False
    reactivation_count: int = 0
    
    # Scoring ProphetIA (rempli par le système)
    prophetia_score: Optional[float] = None
    prophetia_yield: Optional[float] = None
    prophetia_safety: Optional[float] = None
    prophetia_growth: Optional[float] = None
    prophetia_legal: Optional[float] = None
    
    def __post_init__(self):
        """Calculer les champs dérivés."""
        if self.surface_m2 > 0 and self.price > 0:
            self.price_per_m2 = round(self.price / self.surface_m2, 2)
        
        if self.current_rent_monthly and self.price > 0:
            annual_rent = self.current_rent_monthly * 12
            self.rental_yield_gross = round((annual_rent / self.price) * 100, 2)
        
        if self.published_at:
            try:
                pub_date = datetime.fromisoformat(self.published_at.replace('Z', '+00:00'))
                self.days_on_market = (datetime.now(pub_date.tzinfo) - pub_date).days
            except:
                pass
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir en dictionnaire."""
        data = asdict(self)
        data['source'] = self.source.value
        data['property_type'] = self.property_type.value
        data['price_changes'] = [asdict(pc) for pc in self.price_changes]
        return data
    
    @classmethod
    def generate_id(cls, source: str, source_id: str) -> str:
        """Générer un ID unique basé sur source + source_id."""
        raw = f"{source}:{source_id}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]


@dataclass
class DealSignal:
    """
    Signal d'opportunité détecté sur une annonce.
    """
    id: str
    listing_id: str
    signal_type: SignalType
    priority: SignalPriority
    detected_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    # Scores
    score_before: Optional[float] = None
    score_after: Optional[float] = None
    score_delta: Optional[float] = None
    
    # Contexte
    evidence: List[str] = field(default_factory=list)
    confidence: float = 0.8
    
    # Recommandation générée
    summary: str = ""
    summary_long: str = ""
    risks: List[str] = field(default_factory=list)
    next_steps: List[str] = field(default_factory=list)
    
    # Metadata
    expires_at: Optional[str] = None
    is_read: bool = False
    is_dismissed: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['signal_type'] = self.signal_type.value
        data['priority'] = self.priority.value
        return data


@dataclass
class MarketStats:
    """Statistiques de marché pour une zone."""
    country: str
    city: str
    postal_code: Optional[str] = None
    
    # Prix
    median_price_per_m2: float = 0.0
    p25_price_per_m2: float = 0.0
    p75_price_per_m2: float = 0.0
    price_trend_3m: float = 0.0  # % change
    
    # Loyers
    median_rent_per_m2: float = 0.0
    avg_yield_gross: float = 0.0
    yield_std_dev: float = 0.0
    
    # Activité
    listings_count: int = 0
    new_listings_30d: int = 0
    transactions_count_qoq: float = 0.0  # % change quarter over quarter
    avg_days_on_market: int = 60
    
    # Timestamp
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class Watchlist:
    """Liste de surveillance personnalisée."""
    id: str
    user_id: str
    name: str
    
    # Critères de surveillance
    countries: List[str] = field(default_factory=list)
    cities: List[str] = field(default_factory=list)
    postal_codes: List[str] = field(default_factory=list)
    property_types: List[PropertyType] = field(default_factory=list)
    
    # Filtres prix
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    price_per_m2_max: Optional[float] = None
    
    # Filtres surface
    surface_min: Optional[float] = None
    surface_max: Optional[float] = None
    
    # Filtres rendement
    yield_min: Optional[float] = None
    score_min: Optional[float] = None
    
    # Signaux à surveiller
    signals_enabled: List[SignalType] = field(default_factory=lambda: list(SignalType))
    
    # Notification settings
    notify_email: bool = True
    notify_push: bool = True
    notify_frequency: str = "instant"  # instant, daily, weekly
    
    # Status
    is_active: bool = True
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    last_match_at: Optional[str] = None
    match_count: int = 0


# =============================================================================
# Signal Detector
# =============================================================================

class SignalDetector:
    """
    Détecteur de signaux d'opportunité.
    Analyse les annonces et génère des alertes intelligentes.
    """
    
    # Seuils de détection
    PRICE_DROP_THRESHOLD = 0.03  # 3%
    LONG_LISTING_DAYS = 60
    YIELD_ANOMALY_SIGMA = 1.5
    UNDERPRICED_PERCENTILE = 25
    ZONE_ACCELERATION_THRESHOLD = 0.20  # 20%
    
    def __init__(self, scorer: Optional[ProphetIAScoring] = None):
        self.scorer = scorer or ProphetIAScoring()
    
    def detect_signals(
        self,
        listing: NormalizedListing,
        market_stats: MarketStats,
        previous_listing: Optional[NormalizedListing] = None,
    ) -> List[DealSignal]:
        """
        Détecter tous les signaux sur une annonce.
        """
        signals = []
        
        # 1. Baisse de prix
        price_signal = self._detect_price_drop(listing, previous_listing)
        if price_signal:
            signals.append(price_signal)
        
        # 2. Annonce réactivée
        reactivation_signal = self._detect_reactivation(listing, previous_listing)
        if reactivation_signal:
            signals.append(reactivation_signal)
        
        # 3. Longue durée sur marché
        long_listing_signal = self._detect_long_listing(listing)
        if long_listing_signal:
            signals.append(long_listing_signal)
        
        # 4. Yield anormal
        yield_signal = self._detect_yield_anomaly(listing, market_stats)
        if yield_signal:
            signals.append(yield_signal)
        
        # 5. Sous-coté
        underpriced_signal = self._detect_underpriced(listing, market_stats)
        if underpriced_signal:
            signals.append(underpriced_signal)
        
        # 6. Zone en accélération
        zone_signal = self._detect_zone_acceleration(listing, market_stats)
        if zone_signal:
            signals.append(zone_signal)
        
        return signals
    
    def _detect_price_drop(
        self,
        listing: NormalizedListing,
        previous: Optional[NormalizedListing],
    ) -> Optional[DealSignal]:
        """Détecter une baisse de prix significative."""
        if not previous or previous.price <= 0:
            # Vérifier l'historique interne
            if not listing.price_changes:
                return None
            
            last_change = listing.price_changes[-1]
            if last_change.change_percent >= -self.PRICE_DROP_THRESHOLD * 100:
                return None
            
            drop_pct = abs(last_change.change_percent)
            old_price = last_change.old_price
            new_price = last_change.new_price
        else:
            if listing.price >= previous.price:
                return None
            
            drop_pct = ((previous.price - listing.price) / previous.price) * 100
            if drop_pct < self.PRICE_DROP_THRESHOLD * 100:
                return None
            
            old_price = previous.price
            new_price = listing.price
        
        # Calculer score avant/après
        score_after = listing.prophetia_score or 0
        score_before = max(0, score_after - (drop_pct * 1.2))  # Estimation
        
        # Estimer marge de négociation
        nego_margin = min(15, drop_pct * 0.8 + 3)
        
        return DealSignal(
            id=f"sig_{listing.id}_price_drop",
            listing_id=listing.id,
            signal_type=SignalType.PRICE_DROP,
            priority=SignalPriority.HIGH if drop_pct >= 8 else SignalPriority.MEDIUM,
            score_before=round(score_before, 1),
            score_after=round(score_after, 1),
            score_delta=round(score_after - score_before, 1),
            evidence=[
                f"Prix passé de {old_price:,.0f}€ à {new_price:,.0f}€",
                f"Baisse de {drop_pct:.1f}%",
                f"Nouveau prix/m²: {listing.price_per_m2:,.0f}€",
            ],
            confidence=0.95,
            summary=f"Baisse de {drop_pct:.0f}% → Score Yield amélioré",
            summary_long=f"Le vendeur a réduit son prix de {drop_pct:.1f}%. Cette baisse suggère une motivation à vendre. Marge de négociation estimée: {nego_margin:.0f}%.",
            risks=self._generate_risks_for_price_drop(listing, drop_pct),
            next_steps=[
                "Vérifier les raisons de la baisse (défauts cachés?)",
                f"Préparer une offre à -{nego_margin:.0f}% du nouveau prix",
                "Demander les diagnostics techniques complets",
            ],
        )
    
    def _detect_reactivation(
        self,
        listing: NormalizedListing,
        previous: Optional[NormalizedListing],
    ) -> Optional[DealSignal]:
        """Détecter une annonce réactivée."""
        if not listing.is_reactivated and listing.reactivation_count == 0:
            return None
        
        return DealSignal(
            id=f"sig_{listing.id}_reactivated",
            listing_id=listing.id,
            signal_type=SignalType.REACTIVATED,
            priority=SignalPriority.MEDIUM,
            evidence=[
                f"Annonce republiée {listing.reactivation_count + 1} fois",
                "Vente précédente annulée ou retirée du marché",
            ],
            confidence=0.85,
            summary="Annonce réactivée → Vendeur potentiellement plus flexible",
            summary_long="Cette annonce a été retirée puis republiée. Cela peut indiquer une vente tombée à l'eau ou un repositionnement prix. Le vendeur pourrait être plus enclin à négocier.",
            risks=[
                "Possible problème ayant fait échouer la vente précédente",
                "Vérifier s'il y a eu des changements de prix",
            ],
            next_steps=[
                "Demander pourquoi la vente précédente n'a pas abouti",
                "Négocier plus agressivement (-10% minimum)",
                "Vérifier l'historique complet de l'annonce",
            ],
        )
    
    def _detect_long_listing(
        self,
        listing: NormalizedListing,
    ) -> Optional[DealSignal]:
        """Détecter une annonce en ligne depuis longtemps."""
        if listing.days_on_market < self.LONG_LISTING_DAYS:
            return None
        
        # Plus c'est long, plus le signal est fort
        if listing.days_on_market >= 120:
            priority = SignalPriority.HIGH
            nego_margin = 12
        elif listing.days_on_market >= 90:
            priority = SignalPriority.MEDIUM
            nego_margin = 8
        else:
            priority = SignalPriority.LOW
            nego_margin = 5
        
        return DealSignal(
            id=f"sig_{listing.id}_long_listing",
            listing_id=listing.id,
            signal_type=SignalType.LONG_LISTING,
            priority=priority,
            evidence=[
                f"{listing.days_on_market} jours sur le marché",
                f"Moyenne du quartier: ~60 jours",
            ],
            confidence=0.90,
            summary=f"{listing.days_on_market}j sur marché → Négociation ~{nego_margin}%",
            summary_long=f"Ce bien est en vente depuis {listing.days_on_market} jours, bien au-dessus de la moyenne du marché. Le vendeur accumule les frais et pourrait accepter une offre agressive.",
            risks=[
                "Vérifier pourquoi le bien ne se vend pas",
                "Possible surévaluation initiale",
                "Potentiels défauts cachés",
            ],
            next_steps=[
                f"Proposer une offre à -{nego_margin}% minimum",
                "Demander un historique des visites",
                "Négocier les conditions (délai, mobilier, etc.)",
            ],
        )
    
    def _detect_yield_anomaly(
        self,
        listing: NormalizedListing,
        market_stats: MarketStats,
    ) -> Optional[DealSignal]:
        """Détecter un yield anormalement élevé."""
        if not listing.rental_yield_gross or market_stats.avg_yield_gross <= 0:
            return None
        
        if market_stats.yield_std_dev <= 0:
            # Estimation si pas de std dev
            market_stats.yield_std_dev = market_stats.avg_yield_gross * 0.2
        
        z_score = (listing.rental_yield_gross - market_stats.avg_yield_gross) / market_stats.yield_std_dev
        
        if z_score < self.YIELD_ANOMALY_SIGMA:
            return None
        
        return DealSignal(
            id=f"sig_{listing.id}_yield_anomaly",
            listing_id=listing.id,
            signal_type=SignalType.YIELD_ANOMALY,
            priority=SignalPriority.HIGH if z_score >= 2.0 else SignalPriority.MEDIUM,
            evidence=[
                f"Rendement brut: {listing.rental_yield_gross:.1f}%",
                f"Moyenne zone: {market_stats.avg_yield_gross:.1f}%",
                f"Écart: +{z_score:.1f} écarts-types",
            ],
            confidence=0.80,
            summary=f"Yield {listing.rental_yield_gross:.1f}% vs {market_stats.avg_yield_gross:.1f}% marché",
            summary_long=f"Ce bien affiche un rendement brut de {listing.rental_yield_gross:.1f}%, significativement supérieur à la moyenne du quartier ({market_stats.avg_yield_gross:.1f}%). Vérifiez la qualité du locataire et la durabilité du loyer.",
            risks=[
                "Loyer potentiellement surévalué ou locataire fragile",
                "Travaux importants à prévoir non comptabilisés",
                "Zone en déclin pouvant expliquer le prix bas",
            ],
            next_steps=[
                "Vérifier la solvabilité du locataire actuel",
                "Comparer avec les loyers du quartier",
                "Inspecter l'état réel du bien",
            ],
        )
    
    def _detect_underpriced(
        self,
        listing: NormalizedListing,
        market_stats: MarketStats,
    ) -> Optional[DealSignal]:
        """Détecter un bien sous-coté."""
        if listing.price_per_m2 <= 0 or market_stats.p25_price_per_m2 <= 0:
            return None
        
        if listing.price_per_m2 >= market_stats.p25_price_per_m2:
            return None
        
        discount = ((market_stats.median_price_per_m2 - listing.price_per_m2) / market_stats.median_price_per_m2) * 100
        
        return DealSignal(
            id=f"sig_{listing.id}_underpriced",
            listing_id=listing.id,
            signal_type=SignalType.UNDERPRICED,
            priority=SignalPriority.CRITICAL if discount >= 15 else SignalPriority.HIGH,
            evidence=[
                f"Prix/m²: {listing.price_per_m2:,.0f}€",
                f"P25 zone: {market_stats.p25_price_per_m2:,.0f}€",
                f"Médiane zone: {market_stats.median_price_per_m2:,.0f}€",
                f"Décote: {discount:.0f}%",
            ],
            confidence=0.88,
            summary=f"Sous-coté de {discount:.0f}% vs médiane quartier",
            summary_long=f"Ce bien est affiché {discount:.0f}% sous la médiane du quartier ({listing.price_per_m2:,.0f}€/m² vs {market_stats.median_price_per_m2:,.0f}€/m²). Opportunité rare si l'état est correct.",
            risks=[
                "Vérifier l'état réel (travaux importants?)",
                "Vérifier les nuisances (bruit, vis-à-vis)",
                "Confirmer la surface réelle (Carrez)",
            ],
            next_steps=[
                "Visiter rapidement avant d'autres acheteurs",
                "Préparer le financement en amont",
                "Commander une estimation indépendante",
            ],
        )
    
    def _detect_zone_acceleration(
        self,
        listing: NormalizedListing,
        market_stats: MarketStats,
    ) -> Optional[DealSignal]:
        """Détecter une zone en accélération."""
        if market_stats.transactions_count_qoq < self.ZONE_ACCELERATION_THRESHOLD * 100:
            return None
        
        growth = market_stats.transactions_count_qoq
        
        return DealSignal(
            id=f"sig_{listing.id}_zone_acceleration",
            listing_id=listing.id,
            signal_type=SignalType.ZONE_ACCELERATION,
            priority=SignalPriority.MEDIUM,
            evidence=[
                f"Transactions +{growth:.0f}% ce trimestre",
                f"Prix en hausse de {market_stats.price_trend_3m:.1f}%",
                f"{market_stats.new_listings_30d} nouvelles annonces/30j",
            ],
            confidence=0.75,
            summary=f"Zone dynamique (+{growth:.0f}% transactions QoQ)",
            summary_long=f"Cette zone montre une accélération significative: +{growth:.0f}% de transactions ce trimestre. Les prix suivent avec +{market_stats.price_trend_3m:.1f}% sur 3 mois. Potentiel de plus-value.",
            risks=[
                "Risque de surchauffe à court terme",
                "Concurrence accrue des acheteurs",
            ],
            next_steps=[
                "Sécuriser rapidement si le bien correspond",
                "Surveiller les nouvelles annonces du quartier",
                "Analyser les projets d'infrastructure prévus",
            ],
        )
    
    def _generate_risks_for_price_drop(
        self,
        listing: NormalizedListing,
        drop_pct: float,
    ) -> List[str]:
        """Générer les risques spécifiques pour une baisse de prix."""
        risks = []
        
        if drop_pct >= 10:
            risks.append("Baisse importante: vérifier absence de vice caché")
        
        if listing.days_on_market > 90:
            risks.append("Bien difficile à vendre malgré la baisse")
        
        if listing.energy_rating and listing.energy_rating.upper() in ["E", "F", "G"]:
            risks.append(f"DPE {listing.energy_rating}: travaux énergétiques à prévoir")
        
        if listing.construction_year and listing.construction_year < 1950:
            risks.append("Bâtiment ancien: vérifier structure et réseaux")
        
        if not risks:
            risks.append("Vérifier les motivations du vendeur")
        
        return risks
    
    def score_listing(self, listing: NormalizedListing) -> ProphetIAScore:
        """
        Calculer le score ProphetIA pour une annonce.
        """
        # Estimer le loyer si non fourni
        estimated_rent = listing.current_rent_monthly
        if not estimated_rent and listing.price_per_m2 > 0:
            # Estimation grossière: loyer mensuel = ~0.4% du prix
            estimated_rent = listing.price * 0.004
        
        # Construire les métriques
        metrics = PropertyMetrics(
            purchase_price=listing.price,
            annual_rent=(estimated_rent or 0) * 12,
            annual_expenses=(estimated_rent or 0) * 12 * 0.25,  # 25% de charges
            year_built=listing.construction_year or 2000,
            energy_rating=listing.energy_rating or "C",
            last_renovation_year=listing.renovation_year,
            building_condition=listing.building_condition,
            days_on_market_avg=listing.days_on_market or 60,
            vacancy_rate_area=0.05,  # Défaut
        )
        
        return self.scorer.score(metrics)


# =============================================================================
# Service Opportunity Radar
# =============================================================================

class OpportunityRadarService:
    """
    Service principal de l'Opportunity Radar.
    Gère le scan, le scoring et les alertes.
    """
    
    def __init__(self):
        self.detector = SignalDetector()
        self._listings_cache: Dict[str, NormalizedListing] = {}
        self._market_stats_cache: Dict[str, MarketStats] = {}
    
    def get_opportunities(
        self,
        countries: List[str],
        cities: Optional[List[str]] = None,
        price_min: Optional[float] = None,
        price_max: Optional[float] = None,
        yield_min: Optional[float] = None,
        score_min: Optional[float] = None,
        signals_only: bool = False,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Récupérer les opportunités filtrées.
        """
        # Générer des données de démo pour l'instant
        opportunities = self._generate_demo_opportunities(countries, limit)
        
        # Filtrer
        filtered = []
        for opp in opportunities:
            listing = opp["listing"]
            
            if price_min and listing.price < price_min:
                continue
            if price_max and listing.price > price_max:
                continue
            if yield_min and (listing.rental_yield_gross or 0) < yield_min:
                continue
            if score_min and (listing.prophetia_score or 0) < score_min:
                continue
            if signals_only and not opp["signals"]:
                continue
            if cities and listing.city not in cities:
                continue
            
            filtered.append(opp)
        
        # Trier par score puis par nombre de signaux
        filtered.sort(
            key=lambda x: (
                len(x["signals"]),
                x["listing"].prophetia_score or 0
            ),
            reverse=True
        )
        
        return [
            {
                "listing": opp["listing"].to_dict(),
                "signals": [s.to_dict() for s in opp["signals"]],
                "market_stats": asdict(opp["market_stats"]) if opp.get("market_stats") else None,
            }
            for opp in filtered[:limit]
        ]
    
    def get_signals_summary(
        self,
        countries: List[str],
    ) -> Dict[str, Any]:
        """
        Résumé des signaux par type pour le dashboard.
        """
        opportunities = self._generate_demo_opportunities(countries, 100)
        
        summary = {
            "total_opportunities": len(opportunities),
            "signals_by_type": {},
            "high_priority_count": 0,
            "top_opportunities": [],
        }
        
        all_signals = []
        for opp in opportunities:
            for signal in opp["signals"]:
                all_signals.append(signal)
                signal_type = signal.signal_type.value
                summary["signals_by_type"][signal_type] = summary["signals_by_type"].get(signal_type, 0) + 1
                
                if signal.priority in [SignalPriority.CRITICAL, SignalPriority.HIGH]:
                    summary["high_priority_count"] += 1
        
        # Top 5 opportunités
        top = sorted(opportunities, key=lambda x: len(x["signals"]), reverse=True)[:5]
        summary["top_opportunities"] = [
            {
                "listing": opp["listing"].to_dict(),
                "signal_count": len(opp["signals"]),
                "top_signal": opp["signals"][0].to_dict() if opp["signals"] else None,
            }
            for opp in top
        ]
        
        return summary
    
    def _generate_demo_opportunities(
        self,
        countries: List[str],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """
        Générer des opportunités de démo réalistes.
        En production, cela viendrait du scraper.
        """
        demo_listings = self._get_demo_listings(countries)
        opportunities = []
        
        for listing in demo_listings[:limit]:
            # Scorer le listing
            score = self.detector.score_listing(listing)
            listing.prophetia_score = score.total_score
            listing.prophetia_yield = score.yield_score
            listing.prophetia_safety = score.safety_score
            listing.prophetia_growth = score.growth_score
            listing.prophetia_legal = score.legal_score
            
            # Générer des stats de marché
            market_stats = self._get_market_stats(listing.country, listing.city)
            
            # Détecter les signaux
            signals = self.detector.detect_signals(listing, market_stats)
            
            opportunities.append({
                "listing": listing,
                "signals": signals,
                "market_stats": market_stats,
            })
        
        return opportunities
    
    def _get_demo_listings(self, countries: List[str]) -> List[NormalizedListing]:
        """Générer des listings de démo."""
        listings = []
        
        demo_data = [
            # France
            {
                "country": "FR", "city": "Paris", "postal_code": "75011",
                "neighborhood": "Bastille", "property_type": PropertyType.APARTMENT,
                "surface_m2": 45, "rooms": 2, "bedrooms": 1,
                "price": 420000, "current_rent_monthly": 1450,
                "construction_year": 1925, "energy_rating": "D",
                "days_on_market": 35, "title": "T2 lumineux proche Bastille",
            },
            {
                "country": "FR", "city": "Lyon", "postal_code": "69007",
                "neighborhood": "Jean Macé", "property_type": PropertyType.APARTMENT,
                "surface_m2": 55, "rooms": 3, "bedrooms": 2,
                "price": 245000, "current_rent_monthly": 950,
                "construction_year": 1985, "energy_rating": "C",
                "days_on_market": 72, "title": "T3 rénové proche métro",
                "is_reactivated": True, "reactivation_count": 1,
            },
            {
                "country": "FR", "city": "Bordeaux", "postal_code": "33000",
                "neighborhood": "Chartrons", "property_type": PropertyType.STUDIO,
                "surface_m2": 28, "rooms": 1, "bedrooms": 0,
                "price": 165000, "current_rent_monthly": 680,
                "construction_year": 2018, "energy_rating": "B",
                "days_on_market": 12, "title": "Studio neuf rentabilité 5%+",
            },
            # Belgique
            {
                "country": "BE", "city": "Bruxelles", "postal_code": "1050",
                "neighborhood": "Ixelles", "property_type": PropertyType.STUDIO,
                "surface_m2": 32, "rooms": 1, "bedrooms": 0,
                "price": 189000, "current_rent_monthly": 850,
                "construction_year": 1960, "energy_rating": "D",
                "days_on_market": 45, "title": "Studio Ixelles - vendeur pressé",
                "price_changes": [
                    PriceChange(
                        date=(datetime.now() - timedelta(days=7)).isoformat(),
                        old_price=205000, new_price=189000, change_percent=-7.8
                    )
                ],
            },
            {
                "country": "BE", "city": "Bruxelles", "postal_code": "1060",
                "neighborhood": "Saint-Gilles", "property_type": PropertyType.APARTMENT,
                "surface_m2": 65, "rooms": 2, "bedrooms": 1,
                "price": 275000, "current_rent_monthly": 1100,
                "construction_year": 1910, "energy_rating": "E",
                "days_on_market": 95, "title": "Bel appartement haussmannien",
            },
            # UK
            {
                "country": "UK", "city": "London", "postal_code": "E1",
                "neighborhood": "Whitechapel", "property_type": PropertyType.APARTMENT,
                "surface_m2": 48, "rooms": 2, "bedrooms": 1,
                "price": 450000, "current_rent_monthly": 1800,
                "construction_year": 2015, "energy_rating": "B",
                "days_on_market": 28, "title": "Modern 1-bed near tube",
            },
            # Canada
            {
                "country": "CA", "city": "Montréal", "postal_code": "H2T",
                "neighborhood": "Plateau", "property_type": PropertyType.TRIPLEX,
                "surface_m2": 280, "rooms": 9, "bedrooms": 6,
                "price": 890000, "current_rent_monthly": 4200,
                "construction_year": 1925, "energy_rating": "D",
                "days_on_market": 22, "title": "Triplex Plateau - Cash-flow positif",
            },
            # US
            {
                "country": "US", "city": "New York", "postal_code": "11201",
                "neighborhood": "Brooklyn Heights", "property_type": PropertyType.APARTMENT,
                "surface_m2": 65, "rooms": 2, "bedrooms": 1,
                "price": 850000, "current_rent_monthly": 3500,
                "construction_year": 1920, "energy_rating": "C",
                "days_on_market": 35, "title": "Classic Brooklyn brownstone unit",
            },
        ]
        
        for i, data in enumerate(demo_data):
            if countries and data["country"] not in countries:
                continue
            
            listing = NormalizedListing(
                id=f"demo_{i}_{data['city'].lower()}",
                source_id=f"src_{i}",
                source=ListingSource.MANUAL,
                country=data["country"],
                city=data["city"],
                postal_code=data["postal_code"],
                neighborhood=data.get("neighborhood"),
                property_type=data["property_type"],
                surface_m2=data["surface_m2"],
                rooms=data.get("rooms"),
                bedrooms=data.get("bedrooms"),
                price=data["price"],
                current_rent_monthly=data.get("current_rent_monthly"),
                construction_year=data.get("construction_year"),
                energy_rating=data.get("energy_rating"),
                days_on_market=data.get("days_on_market", 30),
                title=data["title"],
                is_reactivated=data.get("is_reactivated", False),
                reactivation_count=data.get("reactivation_count", 0),
                price_changes=data.get("price_changes", []),
                published_at=(datetime.now() - timedelta(days=data.get("days_on_market", 30))).isoformat(),
            )
            listings.append(listing)
        
        return listings
    
    def _get_market_stats(self, country: str, city: str) -> MarketStats:
        """Obtenir les stats de marché pour une ville."""
        # Données de démo
        stats_data = {
            ("FR", "Paris"): MarketStats(
                country="FR", city="Paris",
                median_price_per_m2=10500, p25_price_per_m2=8500, p75_price_per_m2=13000,
                price_trend_3m=-1.2, median_rent_per_m2=28, avg_yield_gross=4.8, yield_std_dev=0.8,
                listings_count=4500, new_listings_30d=850, transactions_count_qoq=-5, avg_days_on_market=55,
            ),
            ("FR", "Lyon"): MarketStats(
                country="FR", city="Lyon",
                median_price_per_m2=5200, p25_price_per_m2=4200, p75_price_per_m2=6500,
                price_trend_3m=0.5, median_rent_per_m2=15, avg_yield_gross=5.5, yield_std_dev=0.9,
                listings_count=2200, new_listings_30d=450, transactions_count_qoq=8, avg_days_on_market=62,
            ),
            ("FR", "Bordeaux"): MarketStats(
                country="FR", city="Bordeaux",
                median_price_per_m2=4800, p25_price_per_m2=3800, p75_price_per_m2=6000,
                price_trend_3m=-0.8, median_rent_per_m2=14, avg_yield_gross=5.2, yield_std_dev=0.7,
                listings_count=1800, new_listings_30d=380, transactions_count_qoq=-2, avg_days_on_market=68,
            ),
            ("BE", "Bruxelles"): MarketStats(
                country="BE", city="Bruxelles",
                median_price_per_m2=3400, p25_price_per_m2=2800, p75_price_per_m2=4200,
                price_trend_3m=1.5, median_rent_per_m2=16, avg_yield_gross=5.8, yield_std_dev=1.0,
                listings_count=3200, new_listings_30d=620, transactions_count_qoq=12, avg_days_on_market=72,
            ),
            ("UK", "London"): MarketStats(
                country="UK", city="London",
                median_price_per_m2=12500, p25_price_per_m2=9500, p75_price_per_m2=18000,
                price_trend_3m=-0.5, median_rent_per_m2=45, avg_yield_gross=4.5, yield_std_dev=0.6,
                listings_count=8500, new_listings_30d=1200, transactions_count_qoq=3, avg_days_on_market=48,
            ),
            ("CA", "Montréal"): MarketStats(
                country="CA", city="Montréal",
                median_price_per_m2=5800, p25_price_per_m2=4500, p75_price_per_m2=7500,
                price_trend_3m=2.1, median_rent_per_m2=22, avg_yield_gross=5.6, yield_std_dev=0.9,
                listings_count=4800, new_listings_30d=920, transactions_count_qoq=18, avg_days_on_market=52,
            ),
            ("US", "New York"): MarketStats(
                country="US", city="New York",
                median_price_per_m2=14500, p25_price_per_m2=11000, p75_price_per_m2=22000,
                price_trend_3m=1.8, median_rent_per_m2=58, avg_yield_gross=4.2, yield_std_dev=0.5,
                listings_count=12000, new_listings_30d=2100, transactions_count_qoq=8, avg_days_on_market=42,
            ),
        }
        
        key = (country, city)
        if key in stats_data:
            return stats_data[key]
        
        # Fallback générique
        return MarketStats(
            country=country, city=city,
            median_price_per_m2=5000, p25_price_per_m2=4000, p75_price_per_m2=6500,
            avg_yield_gross=5.0, yield_std_dev=1.0, avg_days_on_market=60,
        )


# Instance singleton
opportunity_radar_service = OpportunityRadarService()
