#!/usr/bin/env python3
"""
Security Headers Testing Script
Validates that all required security headers are present and properly configured.

Usage:
    python test_security_headers.py [url]

Example:
    python test_security_headers.py http://localhost:8501
    python test_security_headers.py https://api.marketgps.online
"""

import sys
import requests
from typing import Dict, Tuple
from urllib.parse import urljoin


class SecurityHeaderValidator:
    """Validates security headers in HTTP responses."""

    # Required security headers and their expected values
    REQUIRED_HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000",  # Partial match
        "Content-Security-Policy": None,  # Just check presence
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": None,  # Just check presence
    }

    def __init__(self, base_url: str):
        """Initialize validator with base URL."""
        self.base_url = base_url if base_url.endswith("/") else base_url + "/"

    def test_endpoint(self, endpoint: str = "health") -> Tuple[bool, Dict[str, any]]:
        """
        Test security headers on a specific endpoint.

        Args:
            endpoint: API endpoint to test (default: 'health')

        Returns:
            Tuple of (all_passed, results_dict)
        """
        url = urljoin(self.base_url, endpoint)
        results = {
            "url": url,
            "status_code": None,
            "headers": {},
            "missing_headers": [],
            "invalid_headers": [],
            "valid_headers": [],
            "all_passed": False,
        }

        try:
            response = requests.get(url, timeout=5)
            results["status_code"] = response.status_code

            if response.status_code != 200:
                results["error"] = f"HTTP {response.status_code}"
                return False, results

            # Check each required header
            for header_name, expected_value in self.REQUIRED_HEADERS.items():
                header_value = response.headers.get(header_name)

                if header_value is None:
                    results["missing_headers"].append(header_name)
                elif expected_value is None:
                    # Header just needs to exist
                    results["valid_headers"].append(
                        f"✓ {header_name}: {header_value[:50]}..."
                        if len(header_value) > 50
                        else f"✓ {header_name}: {header_value}"
                    )
                elif expected_value in header_value:
                    # Partial match (for headers with multiple values)
                    results["valid_headers"].append(f"✓ {header_name}")
                else:
                    results["invalid_headers"].append(
                        {
                            "header": header_name,
                            "expected": expected_value,
                            "actual": header_value,
                        }
                    )

            # All headers must be present and valid
            results["all_passed"] = (
                len(results["missing_headers"]) == 0
                and len(results["invalid_headers"]) == 0
            )

            return results["all_passed"], results

        except requests.exceptions.ConnectionError:
            results["error"] = f"Connection failed - {url} is unreachable"
            return False, results
        except requests.exceptions.Timeout:
            results["error"] = "Request timeout"
            return False, results
        except Exception as e:
            results["error"] = str(e)
            return False, results

    def print_results(self, passed: bool, results: Dict) -> None:
        """Pretty print validation results."""
        print("\n" + "=" * 70)
        print("SECURITY HEADERS TEST RESULTS")
        print("=" * 70)

        print(f"\nURL: {results['url']}")
        print(f"Status Code: {results.get('status_code', 'N/A')}")

        if "error" in results:
            print(f"\n❌ ERROR: {results['error']}")
            print("=" * 70)
            return

        # Valid headers
        if results["valid_headers"]:
            print("\n✅ VALID HEADERS:")
            for header in results["valid_headers"]:
                print(f"  {header}")

        # Missing headers
        if results["missing_headers"]:
            print("\n❌ MISSING HEADERS:")
            for header in results["missing_headers"]:
                print(f"  - {header}")

        # Invalid headers
        if results["invalid_headers"]:
            print("\n⚠️  INVALID/INCORRECT HEADERS:")
            for item in results["invalid_headers"]:
                print(f"  - {item['header']}")
                print(f"    Expected: {item['expected']}")
                print(f"    Got: {item['actual']}")

        # Summary
        print("\n" + "-" * 70)
        if results["all_passed"]:
            print("✅ ALL SECURITY HEADERS ARE PROPERLY CONFIGURED")
        else:
            missing_count = len(results["missing_headers"])
            invalid_count = len(results["invalid_headers"])
            total_issues = missing_count + invalid_count
            print(f"❌ SECURITY HEADER VALIDATION FAILED ({total_issues} issues)")

        print("=" * 70)


def main():
    """Main function."""
    if len(sys.argv) < 2:
        base_url = "http://localhost:8501"
        print(f"No URL provided, using default: {base_url}")
    else:
        base_url = sys.argv[1]

    validator = SecurityHeaderValidator(base_url)
    passed, results = validator.test_endpoint()
    validator.print_results(passed, results)

    # Exit with proper code for CI/CD pipelines
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
