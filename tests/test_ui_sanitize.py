"""Tests for UI text sanitization and compliance."""
import pytest

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.compliance import ComplianceOfficer, sanitize_text


class TestComplianceOfficer:
    """Tests for compliance text sanitization."""
    
    def test_sanitize_buy_terms(self):
        """Test buy-related terms are replaced."""
        text = "Vous devriez acheter cette action"
        result = sanitize_text(text)
        
        assert "acheter" not in result.lower()
        assert "observer" in result.lower()
    
    def test_sanitize_sell_terms(self):
        """Test sell-related terms are replaced."""
        text = "Il faut vendre maintenant"
        result = sanitize_text(text)
        
        assert "vendre" not in result.lower()
        assert "observer" in result.lower()
    
    def test_sanitize_recommendation_terms(self):
        """Test recommendation terms are replaced."""
        text = "Notre recommandation est claire"
        result = sanitize_text(text)
        
        assert "recommandation" not in result.lower()
    
    def test_sanitize_target_terms(self):
        """Test target terms are replaced."""
        text = "L'objectif de prix est de 150$"
        result = sanitize_text(text)
        
        assert "objectif de prix" not in result.lower()
    
    def test_sanitize_english_terms(self):
        """Test English terms are also sanitized."""
        text = "This is a buy signal"
        result = sanitize_text(text)
        
        assert "buy" not in result.lower()
    
    def test_sanitize_case_insensitive(self):
        """Test sanitization is case insensitive."""
        text = "ACHETER cette action maintenant"
        result = sanitize_text(text)
        
        assert "acheter" not in result.lower()
    
    def test_sanitize_preserves_neutral_text(self):
        """Test neutral text is preserved."""
        text = "Le score d'analyse est de 75/100"
        result = sanitize_text(text)
        
        assert "score" in result.lower()
        assert "analyse" in result.lower()
        assert "75/100" in result
    
    def test_check_text_violations(self):
        """Test checking text for violations without modification."""
        text = "Acheter et vendre rapidement"
        result = ComplianceOfficer.check_text(text)
        
        assert not result["is_compliant"]
        assert len(result["violations"]) >= 2
    
    def test_check_text_compliant(self):
        """Test compliant text passes check."""
        text = "Le score est de 80 sur 100"
        result = ComplianceOfficer.check_text(text)
        
        assert result["is_compliant"]
        assert len(result["violations"]) == 0
    
    def test_disclaimer_content(self):
        """Test disclaimer contains required warnings."""
        disclaimer = ComplianceOfficer.get_disclaimer()
        
        assert "conseil" in disclaimer.lower()
        assert "risque" in disclaimer.lower()
        assert "performances passées" in disclaimer.lower()
    
    def test_wrap_with_disclaimer(self):
        """Test wrapping content with disclaimer."""
        content = "Score: 75/100"
        result = ComplianceOfficer.wrap_with_disclaimer(content)
        
        assert "Score: 75/100" in result
        assert "conseil" in result.lower()
    
    def test_sanitize_none_input(self):
        """Test handling of None input."""
        result = sanitize_text(None)
        assert result == ""
    
    def test_sanitize_non_string_input(self):
        """Test handling of non-string input."""
        result = sanitize_text(123)
        assert result == "123"
    
    def test_sanitize_gambling_terms(self):
        """Test gambling terms are replaced."""
        text = "C'est un pari gagner"
        result = sanitize_text(text)
        
        assert "pari" not in result.lower()
        assert "gagner" not in result.lower()


class TestBlacklistCompleteness:
    """Tests to ensure blacklist covers all required terms."""
    
    def test_trading_actions_covered(self):
        """Test all trading action terms are in blacklist."""
        terms = [
            "acheter", "vendre", "buy", "sell", "hold",
            "short", "long", "achat", "vente"
        ]
        
        for term in terms:
            result = ComplianceOfficer.check_text(term)
            assert not result["is_compliant"], f"Term '{term}' not blocked"
    
    def test_recommendation_terms_covered(self):
        """Test all recommendation terms are in blacklist."""
        terms = [
            "recommandation", "conseil", "recommend", "advice"
        ]
        
        for term in terms:
            result = ComplianceOfficer.check_text(term)
            assert not result["is_compliant"], f"Term '{term}' not blocked"
    
    def test_target_terms_covered(self):
        """Test all target terms are in blacklist."""
        terms = [
            "objectif", "target", "take profit", "stop loss"
        ]
        
        for term in terms:
            result = ComplianceOfficer.check_text(term)
            assert not result["is_compliant"], f"Term '{term}' not blocked"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
