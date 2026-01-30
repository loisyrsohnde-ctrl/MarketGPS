"""
MarketGPS - Geo-Context Service
Détection automatique du contexte géographique et adaptation de l'expérience.

Fonctionnalités:
- Détection pays/ville via IP
- Adaptation devise, unités, langue
- Terminologie juridique localisée
- Market Pulse avec données locales (taux, prix, tendances)
"""

import logging
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, List, Any
from enum import Enum
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


class Country(str, Enum):
    """Pays supportés par MarketGPS."""
    FR = "FR"  # France
    BE = "BE"  # Belgique
    DE = "DE"  # Allemagne
    UK = "UK"  # Royaume-Uni
    ES = "ES"  # Espagne
    IT = "IT"  # Italie
    US = "US"  # États-Unis
    CA = "CA"  # Canada
    
    @classmethod
    def from_code(cls, code: str) -> "Country":
        """Convertir un code pays en enum."""
        code = code.upper().strip()
        try:
            return cls(code)
        except ValueError:
            # Fallback pour codes alternatifs
            mapping = {
                "FRA": cls.FR, "BEL": cls.BE, "DEU": cls.DE,
                "GBR": cls.UK, "ESP": cls.ES, "ITA": cls.IT,
                "USA": cls.US, "CAN": cls.CA,
                "FRANCE": cls.FR, "BELGIUM": cls.BE, "GERMANY": cls.DE,
                "UNITED KINGDOM": cls.UK, "SPAIN": cls.ES, "ITALY": cls.IT,
                "UNITED STATES": cls.US, "CANADA": cls.CA,
            }
            return mapping.get(code.upper(), cls.FR)


@dataclass
class CurrencyConfig:
    """Configuration devise par pays."""
    code: str
    symbol: str
    position: str = "after"  # "before" ou "after"
    decimal_separator: str = ","
    thousands_separator: str = " "
    
    def format(self, amount: float) -> str:
        """Formater un montant selon la configuration."""
        int_part = int(amount)
        dec_part = int(round((amount - int_part) * 100))
        
        # Formatage avec séparateurs
        int_str = f"{int_part:,}".replace(",", self.thousands_separator)
        formatted = f"{int_str}{self.decimal_separator}{dec_part:02d}"
        
        if self.position == "before":
            return f"{self.symbol}{formatted}"
        else:
            return f"{formatted} {self.symbol}"


@dataclass
class UnitConfig:
    """Configuration des unités par pays."""
    system: str  # "metric" ou "imperial"
    area_unit: str  # "m²" ou "sq ft"
    area_multiplier: float = 1.0  # Pour conversion
    distance_unit: str = "km"


@dataclass
class TaxJurisdictionConfig:
    """Configuration fiscale par juridiction."""
    code: str
    name: str
    rental_income_tax_type: str  # "LMNP", "buy_to_let", "schedule_e", etc.
    default_tax_rate: float
    depreciation_available: bool
    special_regimes: List[str] = field(default_factory=list)
    

@dataclass
class MarketPulse:
    """Données Market Pulse pour une région."""
    # Champs obligatoires (sans valeur par défaut)
    country: str
    central_bank: str  # BCE, BoE, Fed, BoC
    central_bank_rate: float
    rate_trend: str  # "up", "stable", "down"
    avg_price_per_m2: float
    price_trend_yoy: float  # Variation annuelle en %
    avg_rent_per_m2: float
    rent_trend_yoy: float
    avg_yield: float
    vacancy_rate: float
    days_on_market_avg: int
    transaction_volume_trend: str  # "up", "stable", "down"
    
    # Champs optionnels (avec valeur par défaut)
    city: Optional[str] = None
    last_rate_change: Optional[str] = None
    next_rate_decision: Optional[str] = None
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class LocalTerminology:
    """Terminologie localisée pour l'immobilier."""
    rental_income: str
    net_operating_income: str
    cap_rate: str
    cash_flow: str
    depreciation: str
    capital_gains_tax: str
    property_tax: str
    rental_yield: str
    tenant: str
    landlord: str
    lease: str
    furnished_rental: str
    unfurnished_rental: str
    short_term_rental: str
    mortgage: str
    down_payment: str
    notary_fees: str
    stamp_duty: str
    renovation_costs: str
    energy_rating: str


# =============================================================================
# Données de référence par pays
# =============================================================================

CURRENCY_CONFIG: Dict[Country, CurrencyConfig] = {
    Country.FR: CurrencyConfig("EUR", "€", "after", ",", " "),
    Country.BE: CurrencyConfig("EUR", "€", "after", ",", " "),
    Country.DE: CurrencyConfig("EUR", "€", "after", ",", "."),
    Country.IT: CurrencyConfig("EUR", "€", "after", ",", "."),
    Country.ES: CurrencyConfig("EUR", "€", "after", ",", "."),
    Country.UK: CurrencyConfig("GBP", "£", "before", ".", ","),
    Country.US: CurrencyConfig("USD", "$", "before", ".", ","),
    Country.CA: CurrencyConfig("CAD", "$", "before", ".", ","),
}

UNIT_CONFIG: Dict[Country, UnitConfig] = {
    Country.FR: UnitConfig("metric", "m²", 1.0, "km"),
    Country.BE: UnitConfig("metric", "m²", 1.0, "km"),
    Country.DE: UnitConfig("metric", "m²", 1.0, "km"),
    Country.IT: UnitConfig("metric", "m²", 1.0, "km"),
    Country.ES: UnitConfig("metric", "m²", 1.0, "km"),
    Country.UK: UnitConfig("imperial", "sq ft", 10.764, "mi"),
    Country.US: UnitConfig("imperial", "sq ft", 10.764, "mi"),
    Country.CA: UnitConfig("metric", "sq ft", 10.764, "km"),  # Canada utilise les deux
}

TAX_CONFIG: Dict[Country, TaxJurisdictionConfig] = {
    Country.FR: TaxJurisdictionConfig(
        code="FR",
        name="France",
        rental_income_tax_type="LMNP",
        default_tax_rate=0.30,
        depreciation_available=True,
        special_regimes=["LMNP", "LMP", "Pinel", "Denormandie", "Malraux"]
    ),
    Country.BE: TaxJurisdictionConfig(
        code="BE",
        name="Belgique",
        rental_income_tax_type="revenus_immobiliers",
        default_tax_rate=0.50,
        depreciation_available=False,
        special_regimes=["Revenu cadastral indexé"]
    ),
    Country.DE: TaxJurisdictionConfig(
        code="DE",
        name="Allemagne",
        rental_income_tax_type="vermietung_verpachtung",
        default_tax_rate=0.42,
        depreciation_available=True,
        special_regimes=["AfA linéaire", "Denkmal-AfA"]
    ),
    Country.UK: TaxJurisdictionConfig(
        code="UK",
        name="Royaume-Uni",
        rental_income_tax_type="buy_to_let",
        default_tax_rate=0.40,
        depreciation_available=False,
        special_regimes=["Section 24", "Wear and Tear Allowance"]
    ),
    Country.US: TaxJurisdictionConfig(
        code="US",
        name="États-Unis",
        rental_income_tax_type="schedule_e",
        default_tax_rate=0.37,
        depreciation_available=True,
        special_regimes=["Section 1031", "MACRS", "Cost Segregation", "Opportunity Zones"]
    ),
    Country.CA: TaxJurisdictionConfig(
        code="CA",
        name="Canada",
        rental_income_tax_type="rental_income",
        default_tax_rate=0.33,
        depreciation_available=True,
        special_regimes=["CCA", "Principal Residence Exemption"]
    ),
    Country.ES: TaxJurisdictionConfig(
        code="ES",
        name="Espagne",
        rental_income_tax_type="rendimientos_capital_inmobiliario",
        default_tax_rate=0.24,
        depreciation_available=True,
        special_regimes=["Deducción vivienda habitual"]
    ),
    Country.IT: TaxJurisdictionConfig(
        code="IT",
        name="Italie",
        rental_income_tax_type="cedolare_secca",
        default_tax_rate=0.21,
        depreciation_available=False,
        special_regimes=["Cedolare secca 21%", "Canone concordato 10%"]
    ),
}

TERMINOLOGY_FR: LocalTerminology = LocalTerminology(
    rental_income="Revenus locatifs",
    net_operating_income="Résultat net d'exploitation",
    cap_rate="Taux de capitalisation",
    cash_flow="Cash-flow",
    depreciation="Amortissement",
    capital_gains_tax="Plus-value immobilière",
    property_tax="Taxe foncière",
    rental_yield="Rendement locatif",
    tenant="Locataire",
    landlord="Bailleur",
    lease="Bail",
    furnished_rental="Location meublée",
    unfurnished_rental="Location nue",
    short_term_rental="Location courte durée",
    mortgage="Crédit immobilier",
    down_payment="Apport personnel",
    notary_fees="Frais de notaire",
    stamp_duty="Droits d'enregistrement",
    renovation_costs="Travaux de rénovation",
    energy_rating="DPE"
)

TERMINOLOGY_EN: LocalTerminology = LocalTerminology(
    rental_income="Rental Income",
    net_operating_income="Net Operating Income",
    cap_rate="Cap Rate",
    cash_flow="Cash Flow",
    depreciation="Depreciation",
    capital_gains_tax="Capital Gains Tax",
    property_tax="Property Tax",
    rental_yield="Rental Yield",
    tenant="Tenant",
    landlord="Landlord",
    lease="Lease",
    furnished_rental="Furnished Rental",
    unfurnished_rental="Unfurnished Rental",
    short_term_rental="Short-Term Rental",
    mortgage="Mortgage",
    down_payment="Down Payment",
    notary_fees="Closing Costs",
    stamp_duty="Stamp Duty",
    renovation_costs="Renovation Costs",
    energy_rating="EPC Rating"
)

TERMINOLOGY_DE: LocalTerminology = LocalTerminology(
    rental_income="Mieteinnahmen",
    net_operating_income="Nettobetriebsergebnis",
    cap_rate="Kapitalisierungssatz",
    cash_flow="Cashflow",
    depreciation="Abschreibung (AfA)",
    capital_gains_tax="Spekulationssteuer",
    property_tax="Grundsteuer",
    rental_yield="Mietrendite",
    tenant="Mieter",
    landlord="Vermieter",
    lease="Mietvertrag",
    furnished_rental="Möblierte Vermietung",
    unfurnished_rental="Unmöblierte Vermietung",
    short_term_rental="Kurzzeitvermietung",
    mortgage="Hypothek",
    down_payment="Eigenkapital",
    notary_fees="Notarkosten",
    stamp_duty="Grunderwerbsteuer",
    renovation_costs="Renovierungskosten",
    energy_rating="Energieausweis"
)

TERMINOLOGY_BY_LANG: Dict[str, LocalTerminology] = {
    "fr": TERMINOLOGY_FR,
    "en": TERMINOLOGY_EN,
    "de": TERMINOLOGY_DE,
}

# Market Pulse data (simulated - would be fetched from real APIs)
MARKET_PULSE_DATA: Dict[Country, MarketPulse] = {
    Country.FR: MarketPulse(
        country="FR",
        city="Paris",
        central_bank="BCE",
        central_bank_rate=4.25,
        rate_trend="stable",
        last_rate_change="2024-06-06",
        next_rate_decision="2025-03-06",
        avg_price_per_m2=10500,
        price_trend_yoy=-2.3,
        avg_rent_per_m2=28.5,
        rent_trend_yoy=3.2,
        avg_yield=5.2,
        vacancy_rate=0.028,
        days_on_market_avg=65,
        transaction_volume_trend="down"
    ),
    Country.BE: MarketPulse(
        country="BE",
        city="Bruxelles",
        central_bank="BCE",
        central_bank_rate=4.25,
        rate_trend="stable",
        last_rate_change="2024-06-06",
        next_rate_decision="2025-03-06",
        avg_price_per_m2=3200,
        price_trend_yoy=1.5,
        avg_rent_per_m2=15.8,
        rent_trend_yoy=4.1,
        avg_yield=5.8,
        vacancy_rate=0.035,
        days_on_market_avg=72,
        transaction_volume_trend="stable"
    ),
    Country.DE: MarketPulse(
        country="DE",
        city="Berlin",
        central_bank="BCE",
        central_bank_rate=4.25,
        rate_trend="stable",
        last_rate_change="2024-06-06",
        next_rate_decision="2025-03-06",
        avg_price_per_m2=4800,
        price_trend_yoy=-4.1,
        avg_rent_per_m2=14.2,
        rent_trend_yoy=5.8,
        avg_yield=4.2,
        vacancy_rate=0.018,
        days_on_market_avg=45,
        transaction_volume_trend="down"
    ),
    Country.UK: MarketPulse(
        country="UK",
        city="London",
        central_bank="BoE",
        central_bank_rate=5.25,
        rate_trend="stable",
        last_rate_change="2024-08-01",
        next_rate_decision="2025-02-06",
        avg_price_per_m2=12500,
        price_trend_yoy=-1.2,
        avg_rent_per_m2=42.5,
        rent_trend_yoy=8.5,
        avg_yield=4.8,
        vacancy_rate=0.022,
        days_on_market_avg=58,
        transaction_volume_trend="stable"
    ),
    Country.US: MarketPulse(
        country="US",
        city="New York",
        central_bank="Fed",
        central_bank_rate=5.50,
        rate_trend="stable",
        last_rate_change="2024-07-26",
        next_rate_decision="2025-03-19",
        avg_price_per_m2=14200,
        price_trend_yoy=2.8,
        avg_rent_per_m2=58.0,
        rent_trend_yoy=4.2,
        avg_yield=4.5,
        vacancy_rate=0.032,
        days_on_market_avg=42,
        transaction_volume_trend="up"
    ),
    Country.CA: MarketPulse(
        country="CA",
        city="Montréal",
        central_bank="BoC",
        central_bank_rate=5.00,
        rate_trend="down",
        last_rate_change="2024-12-11",
        next_rate_decision="2025-01-29",
        avg_price_per_m2=5800,
        price_trend_yoy=1.2,
        avg_rent_per_m2=22.5,
        rent_trend_yoy=6.8,
        avg_yield=5.4,
        vacancy_rate=0.025,
        days_on_market_avg=55,
        transaction_volume_trend="stable"
    ),
}


@dataclass
class GeoContext:
    """Contexte géographique complet pour un utilisateur."""
    country: str
    city: Optional[str]
    language: str
    
    # Configuration
    currency: CurrencyConfig
    units: UnitConfig
    tax_jurisdiction: TaxJurisdictionConfig
    terminology: LocalTerminology
    
    # Market data
    market_pulse: MarketPulse
    
    # Metadata
    detected_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    detection_method: str = "ip"  # "ip", "browser", "user_choice"
    confidence: float = 0.85
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir en dictionnaire pour l'API."""
        return {
            "country": self.country,
            "city": self.city,
            "language": self.language,
            "currency": asdict(self.currency),
            "units": asdict(self.units),
            "tax_jurisdiction": asdict(self.tax_jurisdiction),
            "terminology": asdict(self.terminology),
            "market_pulse": self.market_pulse.to_dict(),
            "detected_at": self.detected_at,
            "detection_method": self.detection_method,
            "confidence": self.confidence,
        }


class GeoContextService:
    """
    Service de détection et gestion du contexte géographique.
    """
    
    # Mapping IP ranges vers pays (simplifié - en prod, utiliser MaxMind GeoIP2)
    IP_COUNTRY_FALLBACK = {
        "192.168": Country.FR,  # Local dev = France
        "127.0": Country.FR,
        "10.0": Country.FR,
    }
    
    # Mapping Accept-Language vers langue/pays
    LANG_COUNTRY_MAP = {
        "fr-FR": (Country.FR, "fr"),
        "fr-BE": (Country.BE, "fr"),
        "fr-CA": (Country.CA, "fr"),
        "fr": (Country.FR, "fr"),
        "en-US": (Country.US, "en"),
        "en-GB": (Country.UK, "en"),
        "en-CA": (Country.CA, "en"),
        "en": (Country.US, "en"),
        "de-DE": (Country.DE, "de"),
        "de": (Country.DE, "de"),
        "es-ES": (Country.ES, "es"),
        "es": (Country.ES, "es"),
        "it-IT": (Country.IT, "it"),
        "it": (Country.IT, "it"),
        "nl-BE": (Country.BE, "nl"),
    }
    
    def __init__(self):
        self._cache: Dict[str, GeoContext] = {}
        self._cache_ttl = timedelta(hours=1)
    
    def detect_from_ip(self, ip_address: str) -> Optional[Country]:
        """
        Détecter le pays depuis l'adresse IP.
        
        En production, utiliser MaxMind GeoIP2 ou un service similaire.
        """
        # Pour le développement, retourner France par défaut
        for prefix, country in self.IP_COUNTRY_FALLBACK.items():
            if ip_address.startswith(prefix):
                return country
        
        # TODO: Intégrer GeoIP2 pour la production
        # import geoip2.database
        # reader = geoip2.database.Reader('GeoLite2-City.mmdb')
        # response = reader.city(ip_address)
        # return Country.from_code(response.country.iso_code)
        
        return Country.FR  # Fallback
    
    def detect_from_accept_language(self, accept_language: str) -> tuple[Country, str]:
        """
        Détecter pays et langue depuis l'en-tête Accept-Language.
        """
        if not accept_language:
            return Country.FR, "fr"
        
        # Parser Accept-Language (ex: "fr-FR,fr;q=0.9,en;q=0.8")
        languages = []
        for part in accept_language.split(","):
            lang = part.split(";")[0].strip()
            languages.append(lang)
        
        # Chercher la première correspondance
        for lang in languages:
            if lang in self.LANG_COUNTRY_MAP:
                return self.LANG_COUNTRY_MAP[lang]
            # Essayer juste le code langue (sans région)
            lang_code = lang.split("-")[0]
            if lang_code in self.LANG_COUNTRY_MAP:
                return self.LANG_COUNTRY_MAP[lang_code]
        
        return Country.FR, "fr"
    
    def get_context(
        self,
        ip_address: Optional[str] = None,
        accept_language: Optional[str] = None,
        user_country: Optional[str] = None,
        user_language: Optional[str] = None,
    ) -> GeoContext:
        """
        Obtenir le contexte géographique complet.
        
        Priorité:
        1. Choix explicite de l'utilisateur
        2. Détection IP
        3. Accept-Language
        4. Défaut (France)
        """
        detection_method = "default"
        confidence = 0.5
        
        # 1. Choix utilisateur (priorité maximale)
        if user_country:
            country = Country.from_code(user_country)
            detection_method = "user_choice"
            confidence = 1.0
        # 2. Détection IP
        elif ip_address:
            country = self.detect_from_ip(ip_address)
            detection_method = "ip"
            confidence = 0.85
        # 3. Accept-Language
        elif accept_language:
            country, _ = self.detect_from_accept_language(accept_language)
            detection_method = "browser"
            confidence = 0.70
        else:
            country = Country.FR
        
        # Déterminer la langue
        if user_language:
            language = user_language
        elif accept_language:
            _, language = self.detect_from_accept_language(accept_language)
        else:
            # Langue par défaut selon le pays
            lang_defaults = {
                Country.FR: "fr", Country.BE: "fr", Country.CA: "fr",
                Country.DE: "de", Country.UK: "en", Country.US: "en",
                Country.ES: "es", Country.IT: "it",
            }
            language = lang_defaults.get(country, "en")
        
        # Construire le contexte
        terminology = TERMINOLOGY_BY_LANG.get(language, TERMINOLOGY_EN)
        market_pulse = MARKET_PULSE_DATA.get(country, MARKET_PULSE_DATA[Country.FR])
        
        return GeoContext(
            country=country.value,
            city=market_pulse.city,
            language=language,
            currency=CURRENCY_CONFIG.get(country, CURRENCY_CONFIG[Country.FR]),
            units=UNIT_CONFIG.get(country, UNIT_CONFIG[Country.FR]),
            tax_jurisdiction=TAX_CONFIG.get(country, TAX_CONFIG[Country.FR]),
            terminology=terminology,
            market_pulse=market_pulse,
            detection_method=detection_method,
            confidence=confidence,
        )
    
    def get_market_pulse(self, country: str, city: Optional[str] = None) -> MarketPulse:
        """
        Obtenir le Market Pulse pour un pays/ville spécifique.
        """
        try:
            country_enum = Country.from_code(country)
            pulse = MARKET_PULSE_DATA.get(country_enum)
            if pulse:
                return pulse
        except Exception as e:
            logger.warning(f"Unknown country for market pulse: {country}")
        
        return MARKET_PULSE_DATA[Country.FR]
    
    def get_supported_countries(self) -> List[Dict[str, Any]]:
        """
        Retourner la liste des pays supportés avec leurs configurations.
        """
        countries = []
        for country in Country:
            tax = TAX_CONFIG.get(country)
            currency = CURRENCY_CONFIG.get(country)
            countries.append({
                "code": country.value,
                "name": tax.name if tax else country.value,
                "currency": currency.code if currency else "EUR",
                "tax_regimes": tax.special_regimes if tax else [],
            })
        return countries
    
    def get_renovation_costs(self, country: str) -> Dict[str, tuple[float, float]]:
        """
        Retourner les coûts de rénovation par type de travaux pour un pays.
        Valeurs en monnaie locale par m² ou par unité.
        """
        # Coûts de base (France = référence)
        base_costs = {
            "painting_per_m2": (15, 25),
            "flooring_per_m2": (30, 80),
            "kitchen_basic": (3000, 8000),
            "kitchen_premium": (10000, 25000),
            "bathroom_basic": (4000, 8000),
            "bathroom_premium": (10000, 20000),
            "windows_per_unit": (400, 800),
            "electrical_per_m2": (80, 150),
            "plumbing_per_m2": (60, 120),
            "insulation_per_m2": (40, 80),
            "roof_per_m2": (150, 300),
            "facade_per_m2": (80, 150),
        }
        
        # Multiplicateurs par pays (coût de la main d'œuvre)
        multipliers = {
            "FR": 1.0,
            "BE": 1.15,
            "DE": 1.25,
            "UK": 1.40,
            "US": 1.80,
            "CA": 1.50,
            "ES": 0.85,
            "IT": 0.95,
        }
        
        mult = multipliers.get(country.upper(), 1.0)
        
        return {
            key: (round(low * mult), round(high * mult))
            for key, (low, high) in base_costs.items()
        }


# Instance singleton
geo_context_service = GeoContextService()
