"""
MarketGPS v7.0 - Compliance Module
Text sanitization and regulatory compliance utilities.
"""
import re
from typing import List, Tuple
from core.config import get_config, get_logger

logger = get_logger(__name__)


class ComplianceOfficer:
    """
    Handles text sanitization to ensure no financial advice language.
    All UI text should pass through sanitize() before display.
    """
    
    # Replacement map for forbidden terms
    REPLACEMENTS = {
        r"\bacheter\b": "analyser",
        r"\bvendre\b": "évaluer",
        r"\bbuy\b": "analyze",
        r"\bsell\b": "evaluate",
        r"\bhold\b": "monitor",
        r"\brecommandation\b": "analyse",
        r"\bconseil\b": "information",
        r"\bobjectif de prix\b": "niveau technique",
        r"\btarget\b": "niveau",
        r"\btake profit\b": "niveau haut",
        r"\bstop loss\b": "niveau bas",
        r"\bentry\b": "point d'analyse",
        r"\bshort\b": "position",
        r"\blong position\b": "exposition",
        r"\bgagner\b": "performer",
        r"\bpari\b": "analyse",
        r"\bwin\b": "perform",
        r"\bopportunité\b": "situation",
        r"\bsignal\b": "indicateur",
        r"\balerte trading\b": "notification",
    }
    
    def __init__(self):
        """Initialize the compliance officer."""
        config = get_config()
        self.forbidden_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in config.compliance.forbidden_terms
        ]
        self.replacement_patterns = [
            (re.compile(pattern, re.IGNORECASE), replacement)
            for pattern, replacement in self.REPLACEMENTS.items()
        ]
        self.disclaimer = config.compliance.disclaimer
    
    def check(self, text: str) -> Tuple[bool, List[str]]:
        """
        Check if text contains forbidden terms.
        
        Returns:
            Tuple of (is_compliant, list of found violations)
        """
        if not text:
            return True, []
        
        violations = []
        for pattern in self.forbidden_patterns:
            matches = pattern.findall(text)
            if matches:
                violations.extend(matches)
        
        return len(violations) == 0, violations
    
    def sanitize(self, text: str) -> str:
        """
        Sanitize text by replacing forbidden terms with neutral alternatives.
        Logs warnings for any replacements made.
        
        Args:
            text: Input text to sanitize
            
        Returns:
            Sanitized text safe for display
        """
        if not text:
            return text
        
        result = text
        replacements_made = []
        
        for pattern, replacement in self.replacement_patterns:
            if pattern.search(result):
                original_term = pattern.pattern.replace(r"\b", "")
                replacements_made.append((original_term, replacement))
                result = pattern.sub(replacement, result)
        
        if replacements_made:
            logger.warning(
                f"Compliance: Replaced forbidden terms: {replacements_made}"
            )
        
        return result
    
    def get_disclaimer(self) -> str:
        """Get the regulatory disclaimer text."""
        return self.disclaimer
    
    def wrap_with_disclaimer(self, content: str) -> str:
        """Wrap content with disclaimer."""
        return f"{content}\n\n---\n\n_{self.disclaimer}_"


# Singleton instance
_officer = None


def get_compliance_officer() -> ComplianceOfficer:
    """Get the compliance officer singleton."""
    global _officer
    if _officer is None:
        _officer = ComplianceOfficer()
    return _officer


def sanitize_text(text: str) -> str:
    """Convenience function to sanitize text."""
    return get_compliance_officer().sanitize(text)


def check_compliance(text: str) -> Tuple[bool, List[str]]:
    """Convenience function to check text compliance."""
    return get_compliance_officer().check(text)


def get_disclaimer() -> str:
    """Convenience function to get disclaimer."""
    return get_compliance_officer().get_disclaimer()
