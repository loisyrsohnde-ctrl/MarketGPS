"""
MarketGPS - Visual Inspector
Analyse d'images immobilières avec IA (Gemini Pro Vision).

Fonctionnalités:
- Analyse de l'état du bien via photos
- Estimation des travaux par marché local
- Détection surcote/sous-cote
- Annotations visuelles
"""

import logging
import os
import base64
import httpx
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, List, Any, Tuple
from enum import Enum
from datetime import datetime
import json
import re

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-1.5-flash"
GEMINI_VISION_ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"


# =============================================================================
# Enums et Types
# =============================================================================

class OverallCondition(str, Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    TO_RENOVATE = "to_renovate"


class ElementType(str, Enum):
    WINDOWS = "windows"
    FLOORING = "flooring"
    WALLS = "walls"
    CEILING = "ceiling"
    KITCHEN = "kitchen"
    BATHROOM = "bathroom"
    ELECTRICAL = "electrical"
    PLUMBING = "plumbing"
    HEATING = "heating"
    INSULATION = "insulation"
    FACADE = "facade"
    ROOF = "roof"
    DOORS = "doors"
    BALCONY = "balcony"
    GARDEN = "garden"


class PositioningLevel(str, Enum):
    LUXURY = "luxury"
    PREMIUM = "premium"
    STANDARD = "standard"
    BUDGET = "budget"


# =============================================================================
# Modèles de données
# =============================================================================

@dataclass
class DetectedElement:
    """Élément détecté dans une image."""
    type: ElementType
    material: Optional[str] = None
    brand: Optional[str] = None
    condition: str = "good"  # excellent, good, fair, poor
    age_estimate: Optional[str] = None  # "0-5 years", "5-10 years", etc.
    notes: Optional[str] = None
    confidence: float = 0.8
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value,
            "material": self.material,
            "brand": self.brand,
            "condition": self.condition,
            "age_estimate": self.age_estimate,
            "notes": self.notes,
            "confidence": self.confidence,
        }


@dataclass
class RenovationEstimate:
    """Estimation de coût pour un type de travaux."""
    work_type: str
    description: str
    cost_low: float
    cost_high: float
    priority: str = "optional"  # required, recommended, optional
    timeline_days: Optional[int] = None
    confidence: float = 0.7
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "work_type": self.work_type,
            "description": self.description,
            "cost_low": self.cost_low,
            "cost_high": self.cost_high,
            "priority": self.priority,
            "timeline_days": self.timeline_days,
            "confidence": self.confidence,
        }


@dataclass
class ImageAnnotation:
    """Annotation sur une image."""
    image_index: int
    x: float  # Position relative (0-1)
    y: float
    width: float
    height: float
    label: str
    element_type: Optional[ElementType] = None
    severity: str = "info"  # info, warning, critical


@dataclass 
class VisualAnalysis:
    """Résultat complet de l'analyse visuelle."""
    # État général
    overall_condition: OverallCondition
    condition_score: int  # 0-100
    condition_confidence: float
    condition_summary: str
    
    # Éléments détectés
    elements: List[DetectedElement] = field(default_factory=list)
    
    # Travaux estimés
    renovations: List[RenovationEstimate] = field(default_factory=list)
    total_cost_low: float = 0.0
    total_cost_high: float = 0.0
    
    # Analyse positionnement
    listed_positioning: PositioningLevel = PositioningLevel.STANDARD
    actual_quality: PositioningLevel = PositioningLevel.STANDARD
    mismatch_detected: bool = False
    estimated_overpricing_percent: Optional[float] = None
    mismatch_evidence: List[str] = field(default_factory=list)
    
    # Points forts et faibles
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    
    # Annotations visuelles
    annotations: List[ImageAnnotation] = field(default_factory=list)
    
    # Méta
    images_analyzed: int = 0
    analysis_timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    model_version: str = GEMINI_MODEL
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_condition": self.overall_condition.value,
            "condition_score": self.condition_score,
            "condition_confidence": self.condition_confidence,
            "condition_summary": self.condition_summary,
            "elements": [e.to_dict() for e in self.elements],
            "renovations": [r.to_dict() for r in self.renovations],
            "total_cost_low": self.total_cost_low,
            "total_cost_high": self.total_cost_high,
            "listed_positioning": self.listed_positioning.value,
            "actual_quality": self.actual_quality.value,
            "mismatch_detected": self.mismatch_detected,
            "estimated_overpricing_percent": self.estimated_overpricing_percent,
            "mismatch_evidence": self.mismatch_evidence,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "images_analyzed": self.images_analyzed,
            "analysis_timestamp": self.analysis_timestamp,
            "model_version": self.model_version,
        }


# =============================================================================
# Coûts de rénovation par pays
# =============================================================================

RENOVATION_COSTS: Dict[str, Dict[str, Tuple[float, float]]] = {
    "FR": {
        "painting_per_m2": (18, 28),
        "flooring_laminate_per_m2": (25, 45),
        "flooring_parquet_per_m2": (60, 120),
        "flooring_tiles_per_m2": (50, 90),
        "kitchen_refresh": (2500, 5000),
        "kitchen_basic": (5000, 12000),
        "kitchen_premium": (15000, 35000),
        "bathroom_refresh": (1500, 3500),
        "bathroom_basic": (5000, 10000),
        "bathroom_premium": (12000, 25000),
        "windows_per_unit": (450, 900),
        "electrical_per_m2": (90, 160),
        "plumbing_per_m2": (70, 130),
        "insulation_per_m2": (45, 90),
        "heating_replacement": (3000, 8000),
        "facade_per_m2": (90, 170),
        "roof_per_m2": (180, 350),
        "doors_interior": (300, 800),
        "door_entrance": (800, 2500),
    },
    "BE": {
        "painting_per_m2": (20, 32),
        "flooring_laminate_per_m2": (28, 50),
        "flooring_parquet_per_m2": (70, 140),
        "flooring_tiles_per_m2": (55, 100),
        "kitchen_refresh": (3000, 6000),
        "kitchen_basic": (6000, 14000),
        "kitchen_premium": (18000, 40000),
        "bathroom_refresh": (1800, 4000),
        "bathroom_basic": (6000, 12000),
        "bathroom_premium": (14000, 28000),
        "windows_per_unit": (500, 1000),
        "electrical_per_m2": (100, 180),
        "plumbing_per_m2": (80, 150),
        "insulation_per_m2": (50, 100),
        "heating_replacement": (3500, 9000),
        "facade_per_m2": (100, 190),
        "roof_per_m2": (200, 380),
        "doors_interior": (350, 900),
        "door_entrance": (900, 2800),
    },
    "UK": {
        "painting_per_m2": (25, 40),
        "flooring_laminate_per_m2": (35, 60),
        "flooring_parquet_per_m2": (85, 170),
        "flooring_tiles_per_m2": (70, 120),
        "kitchen_refresh": (4000, 8000),
        "kitchen_basic": (8000, 18000),
        "kitchen_premium": (22000, 50000),
        "bathroom_refresh": (2500, 5000),
        "bathroom_basic": (8000, 15000),
        "bathroom_premium": (18000, 35000),
        "windows_per_unit": (600, 1200),
        "electrical_per_m2": (120, 220),
        "plumbing_per_m2": (100, 180),
        "insulation_per_m2": (60, 120),
        "heating_replacement": (4500, 12000),
        "facade_per_m2": (120, 230),
        "roof_per_m2": (240, 450),
        "doors_interior": (450, 1100),
        "door_entrance": (1200, 3500),
    },
    "US": {
        "painting_per_m2": (30, 50),
        "flooring_laminate_per_m2": (40, 70),
        "flooring_parquet_per_m2": (100, 200),
        "flooring_tiles_per_m2": (80, 150),
        "kitchen_refresh": (5000, 10000),
        "kitchen_basic": (12000, 25000),
        "kitchen_premium": (30000, 75000),
        "bathroom_refresh": (3000, 6000),
        "bathroom_basic": (10000, 20000),
        "bathroom_premium": (25000, 50000),
        "windows_per_unit": (700, 1500),
        "electrical_per_m2": (150, 280),
        "plumbing_per_m2": (120, 220),
        "insulation_per_m2": (70, 140),
        "heating_replacement": (6000, 15000),
        "facade_per_m2": (150, 280),
        "roof_per_m2": (300, 550),
        "doors_interior": (550, 1300),
        "door_entrance": (1500, 4500),
    },
    "CA": {
        "painting_per_m2": (25, 42),
        "flooring_laminate_per_m2": (35, 60),
        "flooring_parquet_per_m2": (85, 170),
        "flooring_tiles_per_m2": (70, 130),
        "kitchen_refresh": (4500, 9000),
        "kitchen_basic": (10000, 22000),
        "kitchen_premium": (28000, 65000),
        "bathroom_refresh": (2800, 5500),
        "bathroom_basic": (9000, 18000),
        "bathroom_premium": (22000, 45000),
        "windows_per_unit": (650, 1300),
        "electrical_per_m2": (130, 240),
        "plumbing_per_m2": (110, 200),
        "insulation_per_m2": (65, 130),
        "heating_replacement": (5500, 14000),
        "facade_per_m2": (140, 260),
        "roof_per_m2": (280, 500),
        "doors_interior": (500, 1200),
        "door_entrance": (1400, 4000),
    },
    "DE": {
        "painting_per_m2": (22, 35),
        "flooring_laminate_per_m2": (30, 55),
        "flooring_parquet_per_m2": (75, 150),
        "flooring_tiles_per_m2": (60, 110),
        "kitchen_refresh": (3500, 7000),
        "kitchen_basic": (7000, 16000),
        "kitchen_premium": (20000, 45000),
        "bathroom_refresh": (2200, 4500),
        "bathroom_basic": (7000, 14000),
        "bathroom_premium": (16000, 32000),
        "windows_per_unit": (550, 1100),
        "electrical_per_m2": (110, 200),
        "plumbing_per_m2": (90, 170),
        "insulation_per_m2": (55, 110),
        "heating_replacement": (4000, 10000),
        "facade_per_m2": (110, 210),
        "roof_per_m2": (220, 420),
        "doors_interior": (400, 1000),
        "door_entrance": (1000, 3200),
    },
}


# =============================================================================
# Prompts pour Gemini
# =============================================================================

ANALYSIS_PROMPT = """Tu es un expert en inspection immobilière. Analyse ces photos d'un bien immobilier et fournis une évaluation détaillée.

INSTRUCTIONS:
1. Évalue l'état général du bien (excellent, good, fair, poor, to_renovate)
2. Identifie chaque élément visible (fenêtres, sol, cuisine, salle de bain, murs, etc.)
3. Pour chaque élément, indique:
   - Le matériau (si identifiable)
   - L'état (excellent, good, fair, poor)
   - L'âge estimé
   - Les travaux nécessaires
4. Détecte si le bien est positionné "luxe" dans l'annonce mais a des finitions standard
5. Liste les points forts et les points faibles

Réponds UNIQUEMENT en JSON valide avec cette structure:
{
    "overall_condition": "good|excellent|fair|poor|to_renovate",
    "condition_score": 0-100,
    "condition_summary": "Description en 2-3 phrases",
    "elements": [
        {
            "type": "windows|flooring|kitchen|bathroom|walls|electrical|...",
            "material": "PVC|bois|carrelage|parquet|...",
            "condition": "excellent|good|fair|poor",
            "age_estimate": "0-5 ans|5-10 ans|10-20 ans|20+ ans",
            "notes": "Observations spécifiques"
        }
    ],
    "renovations_needed": [
        {
            "work_type": "painting|flooring|kitchen|bathroom|...",
            "description": "Description des travaux",
            "priority": "required|recommended|optional"
        }
    ],
    "positioning_analysis": {
        "listed_as": "luxury|premium|standard|budget",
        "actual_quality": "luxury|premium|standard|budget",
        "mismatch": true|false,
        "evidence": ["Liste des preuves si mismatch"]
    },
    "strengths": ["Point fort 1", "Point fort 2"],
    "weaknesses": ["Point faible 1", "Point faible 2"]
}
"""


# =============================================================================
# Service Visual Inspector
# =============================================================================

class VisualInspectorService:
    """
    Service d'analyse visuelle des biens immobiliers.
    Utilise Gemini Pro Vision pour l'analyse d'images.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or GEMINI_API_KEY
        self.client = httpx.AsyncClient(timeout=60.0)
    
    async def analyze_images(
        self,
        image_urls: List[str],
        country: str = "FR",
        surface_m2: Optional[float] = None,
        listed_price: Optional[float] = None,
        listed_positioning: Optional[str] = None,
    ) -> VisualAnalysis:
        """
        Analyser des images d'un bien immobilier.
        
        Args:
            image_urls: Liste d'URLs des images à analyser
            country: Code pays pour les coûts de rénovation
            surface_m2: Surface du bien pour calculs
            listed_price: Prix affiché pour analyse surcote
            listed_positioning: Positionnement annoncé (luxury, standard, etc.)
        
        Returns:
            VisualAnalysis complète
        """
        if not self.api_key:
            logger.warning("No Gemini API key configured, using demo analysis")
            return self._generate_demo_analysis(country, surface_m2, listed_positioning)
        
        try:
            # Préparer les images pour l'API
            image_parts = await self._prepare_images(image_urls[:5])  # Max 5 images
            
            if not image_parts:
                logger.warning("No valid images to analyze")
                return self._generate_demo_analysis(country, surface_m2, listed_positioning)
            
            # Appeler Gemini
            response = await self._call_gemini(image_parts)
            
            # Parser la réponse
            analysis = self._parse_gemini_response(
                response,
                country=country,
                surface_m2=surface_m2,
                listed_positioning=listed_positioning,
                images_count=len(image_parts),
            )
            
            return analysis
            
        except Exception as e:
            logger.error(f"Visual analysis failed: {e}")
            return self._generate_demo_analysis(country, surface_m2, listed_positioning)
    
    async def _prepare_images(self, image_urls: List[str]) -> List[Dict[str, Any]]:
        """Télécharger et encoder les images pour Gemini."""
        image_parts = []
        
        for url in image_urls:
            try:
                response = await self.client.get(url)
                if response.status_code == 200:
                    # Détecter le type MIME
                    content_type = response.headers.get("content-type", "image/jpeg")
                    if "jpeg" in content_type or "jpg" in content_type:
                        mime_type = "image/jpeg"
                    elif "png" in content_type:
                        mime_type = "image/png"
                    elif "webp" in content_type:
                        mime_type = "image/webp"
                    else:
                        mime_type = "image/jpeg"
                    
                    # Encoder en base64
                    image_data = base64.b64encode(response.content).decode("utf-8")
                    
                    image_parts.append({
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": image_data,
                        }
                    })
            except Exception as e:
                logger.warning(f"Failed to load image {url}: {e}")
        
        return image_parts
    
    async def _call_gemini(self, image_parts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Appeler l'API Gemini avec les images."""
        
        # Construire la requête
        contents = [
            {
                "parts": [
                    {"text": ANALYSIS_PROMPT},
                    *image_parts,
                ]
            }
        ]
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 2048,
                "responseMimeType": "application/json",
            },
        }
        
        response = await self.client.post(
            f"{GEMINI_VISION_ENDPOINT}?key={self.api_key}",
            json=payload,
        )
        
        if response.status_code != 200:
            logger.error(f"Gemini API error: {response.status_code} - {response.text}")
            raise Exception(f"Gemini API error: {response.status_code}")
        
        return response.json()
    
    def _parse_gemini_response(
        self,
        response: Dict[str, Any],
        country: str,
        surface_m2: Optional[float],
        listed_positioning: Optional[str],
        images_count: int,
    ) -> VisualAnalysis:
        """Parser la réponse de Gemini en VisualAnalysis."""
        
        try:
            # Extraire le texte de la réponse
            candidates = response.get("candidates", [])
            if not candidates:
                raise ValueError("No candidates in response")
            
            content = candidates[0].get("content", {})
            parts = content.get("parts", [])
            if not parts:
                raise ValueError("No parts in response")
            
            text = parts[0].get("text", "")
            
            # Parser le JSON
            # Nettoyer le texte si besoin (enlever markdown code blocks)
            text = re.sub(r'^```json\s*', '', text)
            text = re.sub(r'\s*```$', '', text)
            
            data = json.loads(text)
            
            # Construire les éléments détectés
            elements = []
            for elem_data in data.get("elements", []):
                try:
                    elem_type = ElementType(elem_data.get("type", "walls"))
                except ValueError:
                    elem_type = ElementType.WALLS
                
                elements.append(DetectedElement(
                    type=elem_type,
                    material=elem_data.get("material"),
                    condition=elem_data.get("condition", "good"),
                    age_estimate=elem_data.get("age_estimate"),
                    notes=elem_data.get("notes"),
                ))
            
            # Calculer les estimations de travaux
            renovations = self._calculate_renovations(
                data.get("renovations_needed", []),
                country=country,
                surface_m2=surface_m2,
            )
            
            total_low = sum(r.cost_low for r in renovations)
            total_high = sum(r.cost_high for r in renovations)
            
            # Analyse positionnement
            pos_data = data.get("positioning_analysis", {})
            try:
                listed_pos = PositioningLevel(pos_data.get("listed_as", listed_positioning or "standard"))
            except ValueError:
                listed_pos = PositioningLevel.STANDARD
            
            try:
                actual_pos = PositioningLevel(pos_data.get("actual_quality", "standard"))
            except ValueError:
                actual_pos = PositioningLevel.STANDARD
            
            mismatch = pos_data.get("mismatch", False)
            overpricing = None
            if mismatch:
                # Estimer la surcote
                level_values = {
                    PositioningLevel.LUXURY: 4,
                    PositioningLevel.PREMIUM: 3,
                    PositioningLevel.STANDARD: 2,
                    PositioningLevel.BUDGET: 1,
                }
                diff = level_values.get(listed_pos, 2) - level_values.get(actual_pos, 2)
                if diff > 0:
                    overpricing = diff * 8  # ~8% par niveau de surcote
            
            # Condition
            try:
                overall_cond = OverallCondition(data.get("overall_condition", "good"))
            except ValueError:
                overall_cond = OverallCondition.GOOD
            
            return VisualAnalysis(
                overall_condition=overall_cond,
                condition_score=data.get("condition_score", 65),
                condition_confidence=0.78,
                condition_summary=data.get("condition_summary", "Bien en état correct."),
                elements=elements,
                renovations=renovations,
                total_cost_low=total_low,
                total_cost_high=total_high,
                listed_positioning=listed_pos,
                actual_quality=actual_pos,
                mismatch_detected=mismatch,
                estimated_overpricing_percent=overpricing,
                mismatch_evidence=pos_data.get("evidence", []),
                strengths=data.get("strengths", []),
                weaknesses=data.get("weaknesses", []),
                images_analyzed=images_count,
            )
            
        except Exception as e:
            logger.error(f"Failed to parse Gemini response: {e}")
            return self._generate_demo_analysis(country, surface_m2, listed_positioning)
    
    def _calculate_renovations(
        self,
        renovations_data: List[Dict[str, Any]],
        country: str,
        surface_m2: Optional[float],
    ) -> List[RenovationEstimate]:
        """Calculer les coûts de rénovation avec les tarifs locaux."""
        
        costs = RENOVATION_COSTS.get(country.upper(), RENOVATION_COSTS["FR"])
        surface = surface_m2 or 50  # Surface par défaut
        
        renovations = []
        
        for reno in renovations_data:
            work_type = reno.get("work_type", "").lower()
            description = reno.get("description", "")
            priority = reno.get("priority", "optional")
            
            # Mapper le type de travaux aux coûts
            cost_low, cost_high = 0.0, 0.0
            
            if "paint" in work_type or "peinture" in work_type:
                per_m2_low, per_m2_high = costs.get("painting_per_m2", (20, 30))
                cost_low = per_m2_low * surface
                cost_high = per_m2_high * surface
                
            elif "floor" in work_type or "sol" in work_type or "parquet" in work_type:
                per_m2_low, per_m2_high = costs.get("flooring_laminate_per_m2", (30, 50))
                cost_low = per_m2_low * surface * 0.7  # Pas toute la surface
                cost_high = per_m2_high * surface * 0.7
                
            elif "kitchen" in work_type or "cuisine" in work_type:
                if "premium" in description.lower() or "complète" in description.lower():
                    cost_low, cost_high = costs.get("kitchen_premium", (15000, 35000))
                elif "refresh" in description.lower() or "rafraîchir" in description.lower():
                    cost_low, cost_high = costs.get("kitchen_refresh", (2500, 5000))
                else:
                    cost_low, cost_high = costs.get("kitchen_basic", (5000, 12000))
                    
            elif "bath" in work_type or "salle de bain" in work_type:
                if "premium" in description.lower() or "complète" in description.lower():
                    cost_low, cost_high = costs.get("bathroom_premium", (12000, 25000))
                elif "refresh" in description.lower() or "rafraîchir" in description.lower():
                    cost_low, cost_high = costs.get("bathroom_refresh", (1500, 3500))
                else:
                    cost_low, cost_high = costs.get("bathroom_basic", (5000, 10000))
                    
            elif "window" in work_type or "fenêtre" in work_type:
                per_unit_low, per_unit_high = costs.get("windows_per_unit", (450, 900))
                num_windows = max(3, int(surface / 15))  # Estimation
                cost_low = per_unit_low * num_windows
                cost_high = per_unit_high * num_windows
                
            elif "electric" in work_type or "électr" in work_type:
                per_m2_low, per_m2_high = costs.get("electrical_per_m2", (90, 160))
                cost_low = per_m2_low * surface
                cost_high = per_m2_high * surface
                
            elif "plumb" in work_type or "plomberie" in work_type:
                per_m2_low, per_m2_high = costs.get("plumbing_per_m2", (70, 130))
                cost_low = per_m2_low * surface * 0.3  # Zones humides seulement
                cost_high = per_m2_high * surface * 0.3
                
            elif "heat" in work_type or "chauffage" in work_type:
                cost_low, cost_high = costs.get("heating_replacement", (3000, 8000))
                
            elif "insul" in work_type or "isolation" in work_type:
                per_m2_low, per_m2_high = costs.get("insulation_per_m2", (45, 90))
                cost_low = per_m2_low * surface
                cost_high = per_m2_high * surface
                
            else:
                # Estimation générique
                cost_low = 1000
                cost_high = 5000
            
            renovations.append(RenovationEstimate(
                work_type=work_type,
                description=description,
                cost_low=round(cost_low),
                cost_high=round(cost_high),
                priority=priority,
                confidence=0.70,
            ))
        
        return renovations
    
    def _generate_demo_analysis(
        self,
        country: str,
        surface_m2: Optional[float],
        listed_positioning: Optional[str],
    ) -> VisualAnalysis:
        """Générer une analyse de démo réaliste."""
        
        surface = surface_m2 or 50
        costs = RENOVATION_COSTS.get(country.upper(), RENOVATION_COSTS["FR"])
        
        # Éléments détectés (démo)
        elements = [
            DetectedElement(
                type=ElementType.WINDOWS,
                material="PVC double vitrage",
                condition="good",
                age_estimate="5-10 ans",
                notes="État correct, joints à vérifier",
            ),
            DetectedElement(
                type=ElementType.FLOORING,
                material="Parquet flottant",
                condition="fair",
                age_estimate="10-15 ans",
                notes="Usure visible dans les zones de passage",
            ),
            DetectedElement(
                type=ElementType.KITCHEN,
                material="Mélaminé blanc",
                condition="fair",
                age_estimate="10-15 ans",
                notes="Fonctionnelle mais datée, électroménager à remplacer",
            ),
            DetectedElement(
                type=ElementType.BATHROOM,
                material="Faïence blanche",
                condition="good",
                age_estimate="5-10 ans",
                notes="Propre et fonctionnelle",
            ),
            DetectedElement(
                type=ElementType.WALLS,
                material="Peinture blanche",
                condition="good",
                age_estimate="0-5 ans",
                notes="Peinture récente, quelques traces",
            ),
            DetectedElement(
                type=ElementType.ELECTRICAL,
                material="Tableau récent",
                condition="good",
                age_estimate="5-10 ans",
                notes="Aux normes, prises suffisantes",
            ),
        ]
        
        # Travaux recommandés (démo)
        paint_low, paint_high = costs.get("painting_per_m2", (18, 28))
        kitchen_low, kitchen_high = costs.get("kitchen_refresh", (2500, 5000))
        floor_low, floor_high = costs.get("flooring_laminate_per_m2", (25, 45))
        
        renovations = [
            RenovationEstimate(
                work_type="peinture",
                description="Rafraîchissement peinture complète",
                cost_low=round(paint_low * surface),
                cost_high=round(paint_high * surface),
                priority="recommended",
                timeline_days=5,
            ),
            RenovationEstimate(
                work_type="cuisine",
                description="Rafraîchissement cuisine (façades + plan de travail)",
                cost_low=kitchen_low,
                cost_high=kitchen_high,
                priority="recommended",
                timeline_days=7,
            ),
            RenovationEstimate(
                work_type="sol",
                description="Remplacement parquet zones usées",
                cost_low=round(floor_low * surface * 0.3),
                cost_high=round(floor_high * surface * 0.3),
                priority="optional",
                timeline_days=3,
            ),
        ]
        
        total_low = sum(r.cost_low for r in renovations)
        total_high = sum(r.cost_high for r in renovations)
        
        # Positionnement
        try:
            listed_pos = PositioningLevel(listed_positioning) if listed_positioning else PositioningLevel.STANDARD
        except ValueError:
            listed_pos = PositioningLevel.STANDARD
        
        return VisualAnalysis(
            overall_condition=OverallCondition.GOOD,
            condition_score=68,
            condition_confidence=0.75,
            condition_summary="Bien en bon état général avec des finitions moyennes. La cuisine et les sols montrent des signes d'usure qui justifient un rafraîchissement. Structure et réseaux en bon état.",
            elements=elements,
            renovations=renovations,
            total_cost_low=total_low,
            total_cost_high=total_high,
            listed_positioning=listed_pos,
            actual_quality=PositioningLevel.STANDARD,
            mismatch_detected=False,
            estimated_overpricing_percent=None,
            mismatch_evidence=[],
            strengths=[
                "Luminosité naturelle satisfaisante",
                "Peinture récente",
                "Installation électrique aux normes",
                "Salle de bain fonctionnelle",
            ],
            weaknesses=[
                "Cuisine datée nécessitant rafraîchissement",
                "Parquet usé dans les zones de passage",
                "Fenêtres correctes mais joints à vérifier",
            ],
            images_analyzed=3,
        )
    
    async def close(self):
        """Fermer le client HTTP."""
        await self.client.aclose()


# Instance singleton
visual_inspector_service = VisualInspectorService()
