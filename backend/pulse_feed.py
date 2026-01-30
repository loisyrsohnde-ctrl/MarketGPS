"""
MarketGPS - Pulse Feed Service
Veille réglementaire, macro-économique et marché immobilier.

Fonctionnalités:
- Agrégation de news multi-sources
- Taux directeurs (BCE, Fed, BoE, BoC)
- Impact sur portefeuille
- Traduction en recommandations actionnables
"""

import logging
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, List, Any
from enum import Enum
from datetime import datetime, timedelta
import hashlib

logger = logging.getLogger(__name__)


# =============================================================================
# Enums
# =============================================================================

class PulseCategory(str, Enum):
    REGULATION = "regulation"      # Lois, réglementation
    RATES = "rates"                # Taux directeurs
    MARKET = "market"              # Tendances marché
    LOCAL = "local"                # Actualités locales/quartier
    FISCAL = "fiscal"              # Fiscalité
    ENERGY = "energy"              # Réglementation énergétique


class ImpactLevel(str, Enum):
    CRITICAL = "critical"  # Action requise
    HIGH = "high"          # Impact significatif
    MEDIUM = "medium"      # À surveiller
    LOW = "low"            # Information
    INFO = "info"          # FYI


class ImpactType(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"


# =============================================================================
# Modèles de données
# =============================================================================

@dataclass
class CentralBankRate:
    """Taux directeur d'une banque centrale."""
    bank: str  # BCE, Fed, BoE, BoC
    bank_full_name: str
    rate: float
    previous_rate: float
    trend: str  # up, stable, down
    last_change_date: str
    next_decision_date: Optional[str] = None
    change_amount: float = 0.0
    countries_affected: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PulseItem:
    """
    Élément du Pulse Feed.
    Une actualité avec son analyse d'impact.
    """
    id: str
    
    # Contenu
    title: str
    summary: str
    source: str
    source_url: Optional[str] = None
    published_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    # Classification
    category: PulseCategory = PulseCategory.MARKET
    countries_affected: List[str] = field(default_factory=list)
    
    # Impact
    impact_level: ImpactLevel = ImpactLevel.INFO
    impact_type: ImpactType = ImpactType.NEUTRAL
    impact_description: str = ""
    
    # Scores affectés
    affected_scores: Dict[str, float] = field(default_factory=dict)  # {"yield": +2, "risk": -5}
    
    # Actions
    user_action_required: bool = False
    recommended_actions: List[str] = field(default_factory=list)
    
    # Métadonnées
    is_read: bool = False
    is_bookmarked: bool = False
    expires_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["category"] = self.category.value
        data["impact_level"] = self.impact_level.value
        data["impact_type"] = self.impact_type.value
        return data
    
    @classmethod
    def generate_id(cls, title: str, source: str) -> str:
        raw = f"{source}:{title}"
        return hashlib.sha256(raw.encode()).hexdigest()[:12]


@dataclass
class PortfolioImpact:
    """Impact d'une actualité sur un portefeuille."""
    pulse_item_id: str
    
    # Impact financier estimé
    estimated_cashflow_impact_annual: float = 0.0
    estimated_value_impact_percent: float = 0.0
    
    # Propriétés affectées
    affected_properties: List[str] = field(default_factory=list)
    affected_properties_count: int = 0
    
    # Détail
    impact_breakdown: str = ""
    mitigation_steps: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# =============================================================================
# Données de référence
# =============================================================================

CENTRAL_BANK_RATES: Dict[str, CentralBankRate] = {
    "BCE": CentralBankRate(
        bank="BCE",
        bank_full_name="Banque Centrale Européenne",
        rate=4.25,
        previous_rate=4.50,
        trend="stable",
        last_change_date="2024-06-06",
        next_decision_date="2025-03-06",
        change_amount=-0.25,
        countries_affected=["FR", "BE", "DE", "ES", "IT"],
    ),
    "Fed": CentralBankRate(
        bank="Fed",
        bank_full_name="Federal Reserve",
        rate=5.50,
        previous_rate=5.50,
        trend="stable",
        last_change_date="2024-07-26",
        next_decision_date="2025-03-19",
        change_amount=0.0,
        countries_affected=["US"],
    ),
    "BoE": CentralBankRate(
        bank="BoE",
        bank_full_name="Bank of England",
        rate=5.25,
        previous_rate=5.25,
        trend="stable",
        last_change_date="2024-08-01",
        next_decision_date="2025-02-06",
        change_amount=0.0,
        countries_affected=["UK"],
    ),
    "BoC": CentralBankRate(
        bank="BoC",
        bank_full_name="Banque du Canada",
        rate=5.00,
        previous_rate=5.25,
        trend="down",
        last_change_date="2024-12-11",
        next_decision_date="2025-01-29",
        change_amount=-0.25,
        countries_affected=["CA"],
    ),
}


# =============================================================================
# Actualités de démo
# =============================================================================

DEMO_PULSE_ITEMS: List[PulseItem] = [
    # Réglementation énergétique
    PulseItem(
        id="pulse_dpe_2025",
        title="Interdiction location logements G dès 2025",
        summary="Les logements classés G au DPE ne pourront plus être loués à compter du 1er janvier 2025. Les propriétaires concernés doivent réaliser des travaux de rénovation énergétique ou se mettre en conformité.",
        source="Légifrance",
        source_url="https://www.legifrance.gouv.fr",
        category=PulseCategory.ENERGY,
        countries_affected=["FR"],
        impact_level=ImpactLevel.CRITICAL,
        impact_type=ImpactType.NEGATIVE,
        impact_description="Les biens classés G deviennent non-louables. Obligation de travaux ou revente.",
        affected_scores={"risk": 15, "yield": -10},
        user_action_required=True,
        recommended_actions=[
            "Vérifier le DPE de tous vos biens",
            "Planifier un audit énergétique pour les biens E, F, G",
            "Budgéter les travaux d'isolation",
            "Envisager les aides MaPrimeRénov'",
        ],
    ),
    PulseItem(
        id="pulse_dpe_2028",
        title="Calendrier DPE : F interdit en 2028, E en 2034",
        summary="Le calendrier réglementaire prévoit l'interdiction de louer les logements F en 2028 et E en 2034. Anticiper les travaux permet de lisser les coûts et de maintenir la valeur patrimoniale.",
        source="Ministère Transition Écologique",
        category=PulseCategory.ENERGY,
        countries_affected=["FR"],
        impact_level=ImpactLevel.HIGH,
        impact_type=ImpactType.NEGATIVE,
        impact_description="Calendrier à anticiper pour les biens E et F.",
        affected_scores={"risk": 8},
        user_action_required=False,
        recommended_actions=[
            "Établir un plan de rénovation pluriannuel",
            "Prioriser les biens les plus énergivores",
        ],
    ),
    
    # Taux BCE
    PulseItem(
        id="pulse_bce_stable",
        title="BCE : maintien du taux directeur à 4.25%",
        summary="La Banque Centrale Européenne maintient son taux directeur principal à 4.25%. Le conseil indique que les prochaines décisions dépendront des données d'inflation. Une baisse est envisageable au T2 2025.",
        source="BCE",
        source_url="https://www.ecb.europa.eu",
        category=PulseCategory.RATES,
        countries_affected=["FR", "BE", "DE", "ES", "IT"],
        impact_level=ImpactLevel.MEDIUM,
        impact_type=ImpactType.NEUTRAL,
        impact_description="Stabilité des conditions de financement. Surveiller les décisions futures.",
        affected_scores={},
        user_action_required=False,
        recommended_actions=[
            "Opportunité de renégociation si taux variable",
            "Surveiller les offres de crédit",
        ],
    ),
    
    # BoC Canada
    PulseItem(
        id="pulse_boc_cut",
        title="Banque du Canada : baisse de 25 points de base",
        summary="La BoC réduit son taux directeur de 5.25% à 5.00%, première baisse depuis 2020. Cette décision reflète le ralentissement de l'inflation et devrait stimuler le marché immobilier canadien.",
        source="Banque du Canada",
        source_url="https://www.bankofcanada.ca",
        category=PulseCategory.RATES,
        countries_affected=["CA"],
        impact_level=ImpactLevel.HIGH,
        impact_type=ImpactType.POSITIVE,
        impact_description="Amélioration des conditions de financement au Canada. Potentiel de hausse des prix.",
        affected_scores={"yield": 3, "growth": 5},
        user_action_required=False,
        recommended_actions=[
            "Renégocier les prêts à taux variable",
            "Accélérer les projets d'acquisition au Canada",
            "Surveiller l'évolution des prix",
        ],
    ),
    
    # Marché local
    PulseItem(
        id="pulse_metro_bruxelles",
        title="Bruxelles : nouveau métro ligne 3 en 2028",
        summary="La ligne 3 du métro bruxellois reliera le nord au sud de la ville via Forest, Saint-Gilles et Ixelles. Mise en service prévue fin 2028. Impact attendu sur les valeurs immobilières des quartiers desservis.",
        source="STIB",
        source_url="https://www.stib-mivb.be",
        category=PulseCategory.LOCAL,
        countries_affected=["BE"],
        impact_level=ImpactLevel.MEDIUM,
        impact_type=ImpactType.POSITIVE,
        impact_description="Valorisation attendue de +8-12% pour les biens proches des nouvelles stations.",
        affected_scores={"growth": 10, "yield": 2},
        user_action_required=False,
        recommended_actions=[
            "Identifier les biens proches du tracé",
            "Surveiller les opportunités dans ces zones",
            "Anticiper la hausse des prix pré-ouverture",
        ],
    ),
    
    # Fiscalité
    PulseItem(
        id="pulse_lmnp_2024",
        title="LMNP : régime maintenu mais sous surveillance",
        summary="Le gouvernement confirme le maintien du régime LMNP pour 2025. Toutefois, des discussions sont en cours sur un plafonnement des avantages fiscaux. Aucun changement immédiat mais vigilance requise.",
        source="Ministère des Finances",
        category=PulseCategory.FISCAL,
        countries_affected=["FR"],
        impact_level=ImpactLevel.LOW,
        impact_type=ImpactType.NEUTRAL,
        impact_description="Pas de changement immédiat. Surveiller les évolutions législatives.",
        affected_scores={},
        user_action_required=False,
        recommended_actions=[
            "Optimiser les déclarations LMNP en cours",
            "Anticiper un éventuel durcissement",
        ],
    ),
    
    # Réglementation location courte durée
    PulseItem(
        id="pulse_airbnb_paris",
        title="Paris : renforcement restrictions Airbnb",
        summary="La mairie de Paris durcit les conditions de location courte durée : limite abaissée à 90 jours/an (vs 120) et contrôles renforcés. Amendes jusqu'à 50 000€ pour non-respect.",
        source="Mairie de Paris",
        category=PulseCategory.REGULATION,
        countries_affected=["FR"],
        impact_level=ImpactLevel.HIGH,
        impact_type=ImpactType.NEGATIVE,
        impact_description="Réduction du potentiel de revenus en location courte durée à Paris.",
        affected_scores={"yield": -5, "risk": 8},
        user_action_required=True,
        recommended_actions=[
            "Vérifier la conformité de vos locations",
            "Calculer la rentabilité en location classique",
            "Envisager la transformation en bail mobilité",
        ],
    ),
    
    # Marché
    PulseItem(
        id="pulse_prix_idf_q4",
        title="Île-de-France : baisse des prix de 3.2% en 2024",
        summary="Selon les notaires, les prix immobiliers en Île-de-France ont reculé de 3.2% sur l'année 2024. Paris intra-muros affiche -4.1%. Les premières couronnes résistent mieux avec -1.8%.",
        source="Notaires de France",
        source_url="https://www.notaires.fr",
        category=PulseCategory.MARKET,
        countries_affected=["FR"],
        impact_level=ImpactLevel.MEDIUM,
        impact_type=ImpactType.MIXED,
        impact_description="Baisse des valorisations mais opportunités d'achat. Les rendements s'améliorent.",
        affected_scores={"yield": 3, "growth": -5},
        user_action_required=False,
        recommended_actions=[
            "Réévaluer les biens en portefeuille",
            "Opportunités d'acquisition à prix corrigés",
            "Négocier plus agressivement",
        ],
    ),
    
    # UK spécifique
    PulseItem(
        id="pulse_uk_epc",
        title="UK : EPC minimum C pour locations dès 2028",
        summary="Le gouvernement britannique confirme l'obligation d'un certificat EPC minimum C pour toutes les locations à partir de 2028. Les propriétaires de biens D à G doivent planifier des travaux.",
        source="UK Government",
        source_url="https://www.gov.uk",
        category=PulseCategory.ENERGY,
        countries_affected=["UK"],
        impact_level=ImpactLevel.HIGH,
        impact_type=ImpactType.NEGATIVE,
        impact_description="Travaux obligatoires pour les biens D-G avant 2028.",
        affected_scores={"risk": 12},
        user_action_required=True,
        recommended_actions=[
            "Commander un audit énergétique",
            "Planifier les travaux d'ici 2027",
            "Explorer les financements Green Deal",
        ],
    ),
]


# =============================================================================
# Pulse Feed Service
# =============================================================================

class PulseFeedService:
    """
    Service de gestion du Pulse Feed.
    Agrège les actualités et calcule leur impact.
    """
    
    def __init__(self):
        self._items: List[PulseItem] = DEMO_PULSE_ITEMS.copy()
    
    def get_central_bank_rates(
        self,
        countries: Optional[List[str]] = None,
    ) -> List[CentralBankRate]:
        """
        Récupérer les taux directeurs pertinents.
        """
        rates = []
        
        for bank, rate in CENTRAL_BANK_RATES.items():
            if countries:
                # Vérifier si le pays est affecté par cette banque centrale
                if any(c in rate.countries_affected for c in countries):
                    rates.append(rate)
            else:
                rates.append(rate)
        
        return rates
    
    def get_pulse_items(
        self,
        countries: Optional[List[str]] = None,
        categories: Optional[List[PulseCategory]] = None,
        impact_levels: Optional[List[ImpactLevel]] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[PulseItem]:
        """
        Récupérer les éléments du Pulse Feed.
        """
        items = self._items.copy()
        
        # Filtrer par pays
        if countries:
            items = [
                item for item in items
                if any(c in item.countries_affected for c in countries)
            ]
        
        # Filtrer par catégorie
        if categories:
            items = [
                item for item in items
                if item.category in categories
            ]
        
        # Filtrer par niveau d'impact
        if impact_levels:
            items = [
                item for item in items
                if item.impact_level in impact_levels
            ]
        
        # Trier par date puis par impact
        impact_order = {
            ImpactLevel.CRITICAL: 0,
            ImpactLevel.HIGH: 1,
            ImpactLevel.MEDIUM: 2,
            ImpactLevel.LOW: 3,
            ImpactLevel.INFO: 4,
        }
        
        items.sort(
            key=lambda x: (
                impact_order.get(x.impact_level, 5),
                x.published_at,
            ),
            reverse=False,
        )
        
        return items[offset:offset + limit]
    
    def get_pulse_summary(
        self,
        countries: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Résumé du Pulse Feed pour le dashboard.
        """
        items = self.get_pulse_items(countries=countries, limit=100)
        rates = self.get_central_bank_rates(countries=countries)
        
        # Compter par catégorie
        by_category = {}
        for item in items:
            cat = item.category.value
            by_category[cat] = by_category.get(cat, 0) + 1
        
        # Compter par niveau d'impact
        by_impact = {}
        for item in items:
            level = item.impact_level.value
            by_impact[level] = by_impact.get(level, 0) + 1
        
        # Items nécessitant une action
        action_required = [
            item for item in items
            if item.user_action_required
        ]
        
        # Top 5 items critiques/high
        critical_items = [
            item for item in items
            if item.impact_level in [ImpactLevel.CRITICAL, ImpactLevel.HIGH]
        ][:5]
        
        return {
            "total_items": len(items),
            "by_category": by_category,
            "by_impact_level": by_impact,
            "action_required_count": len(action_required),
            "central_bank_rates": [r.to_dict() for r in rates],
            "critical_items": [item.to_dict() for item in critical_items],
            "action_required_items": [item.to_dict() for item in action_required[:5]],
        }
    
    def calculate_portfolio_impact(
        self,
        pulse_item_id: str,
        portfolio_properties: List[Dict[str, Any]],
    ) -> Optional[PortfolioImpact]:
        """
        Calculer l'impact d'une actualité sur un portefeuille.
        """
        # Trouver l'item
        item = None
        for i in self._items:
            if i.id == pulse_item_id:
                item = i
                break
        
        if not item:
            return None
        
        # Filtrer les propriétés affectées
        affected = []
        for prop in portfolio_properties:
            prop_country = prop.get("country", "")
            if prop_country in item.countries_affected:
                affected.append(prop.get("id", ""))
        
        if not affected:
            return PortfolioImpact(
                pulse_item_id=pulse_item_id,
                affected_properties_count=0,
                impact_breakdown="Aucun bien de votre portefeuille n'est directement concerné.",
            )
        
        # Calculer l'impact
        cashflow_impact = 0.0
        value_impact = 0.0
        
        if "yield" in item.affected_scores:
            yield_change = item.affected_scores["yield"]
            # Estimation simplifiée
            cashflow_impact = yield_change * 100 * len(affected)  # €/an par bien
        
        if "growth" in item.affected_scores:
            growth_change = item.affected_scores["growth"]
            value_impact = growth_change * 0.5  # % de la valeur
        
        breakdown = f"{len(affected)} bien(s) concerné(s). "
        if cashflow_impact != 0:
            sign = "+" if cashflow_impact > 0 else ""
            breakdown += f"Impact cash-flow estimé: {sign}{cashflow_impact:.0f}€/an. "
        if value_impact != 0:
            sign = "+" if value_impact > 0 else ""
            breakdown += f"Impact valorisation estimé: {sign}{value_impact:.1f}%. "
        
        return PortfolioImpact(
            pulse_item_id=pulse_item_id,
            estimated_cashflow_impact_annual=cashflow_impact,
            estimated_value_impact_percent=value_impact,
            affected_properties=affected,
            affected_properties_count=len(affected),
            impact_breakdown=breakdown,
            mitigation_steps=item.recommended_actions[:3],
        )
    
    def get_items_for_property(
        self,
        country: str,
        city: Optional[str] = None,
        energy_rating: Optional[str] = None,
    ) -> List[PulseItem]:
        """
        Récupérer les actualités pertinentes pour une propriété spécifique.
        """
        items = self.get_pulse_items(countries=[country], limit=50)
        
        relevant = []
        for item in items:
            # Toujours inclure les items critiques
            if item.impact_level == ImpactLevel.CRITICAL:
                relevant.append(item)
                continue
            
            # Items énergie si mauvais DPE
            if energy_rating and energy_rating.upper() in ["E", "F", "G"]:
                if item.category == PulseCategory.ENERGY:
                    relevant.append(item)
                    continue
            
            # Items taux et fiscalité
            if item.category in [PulseCategory.RATES, PulseCategory.FISCAL]:
                relevant.append(item)
                continue
            
            # Items locaux si ville correspond
            if city and item.category == PulseCategory.LOCAL:
                if city.lower() in item.title.lower() or city.lower() in item.summary.lower():
                    relevant.append(item)
        
        return relevant[:10]
    
    def generate_notification_text(
        self,
        item: PulseItem,
        format: str = "short",
    ) -> str:
        """
        Générer le texte de notification pour un item.
        """
        if format == "short":
            # Format push notification
            icon = {
                ImpactLevel.CRITICAL: "🔴",
                ImpactLevel.HIGH: "🟠",
                ImpactLevel.MEDIUM: "🟡",
                ImpactLevel.LOW: "🟢",
                ImpactLevel.INFO: "ℹ️",
            }.get(item.impact_level, "")
            
            return f"{icon} {item.title}"
        
        elif format == "medium":
            # Format card
            return f"{item.title}\n{item.summary[:150]}..."
        
        else:
            # Format complet
            actions = "\n".join([f"• {a}" for a in item.recommended_actions[:3]])
            return f"""**{item.title}**

{item.summary}

**Impact**: {item.impact_description}

**Actions recommandées**:
{actions}
"""


# Instance singleton
pulse_feed_service = PulseFeedService()
