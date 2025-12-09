"""
Policy Text Analyzer - Direct text scanning for privacy policy analysis.

This module complements PoliGraph's NLP pipeline by directly scanning policy text
for explicit mentions of data categories and data types. This is especially useful
for modern privacy policies that use structured formats like:

    "Financial Data - such as third-party recipient account"
    "Identity Data - such as account credentials, username"

The NLP pipeline may miss these because:
1. phrase_map.yml doesn't have patterns for all modern policy terminology
2. Structured list formats don't parse well with dependency-based extraction
3. Category headers (like "Financial Data") need explicit recognition

This analyzer provides a complementary approach using regex-based pattern matching.
"""

import re
from dataclasses import dataclass
from typing import Optional
from pathlib import Path

from extension_privacy_analysis.data_categories import DataCategory


@dataclass
class CategoryMatch:
    """Represents a matched data category in policy text."""
    category: DataCategory
    matched_text: str
    context: str  # Surrounding text for verification
    confidence: float  # 0.0-1.0 confidence score


# Comprehensive patterns for detecting each data category in policy text
# These are designed to catch both explicit category mentions and specific data types
CATEGORY_PATTERNS = {
    DataCategory.PII: {
        # Explicit category mentions
        "category_patterns": [
            r"personal\s+(information|data|identifier)",
            r"personally\s+identifiable\s+(information|data)",
            r"identity\s+data",
            r"contact\s+data",
            r"profile\s+data",
            r"\bPII\b",
        ],
        # Specific data type mentions that indicate this category
        "data_type_patterns": [
            r"(your\s+)?name",
            r"(e-?mail|email)\s*(address)?",
            r"phone\s*number",
            r"(postal|mailing|home|street|billing|shipping)\s*address",
            r"(social\s+security|SSN)",
            r"passport",
            r"driver'?s?\s+license",
            r"date\s+of\s+birth|birthday|birthdate",
            r"(age|gender|sex)\b",
            r"(device|advertising)\s+(id|identifier)",
            r"account\s+(name|credentials|information)",
            r"user\s*name",
            r"(biometric|fingerprint|face\s+recognition|voiceprint)",
            r"demographic\s+(information|data)",
            r"identification\s+number",
        ],
        # Context phrases that strengthen confidence
        "context_phrases": [
            r"collect.{0,50}(name|email|address|phone)",
            r"(name|email|address|phone).{0,30}collect",
            r"provide.{0,30}(name|email|address)",
        ]
    },

    DataCategory.FINANCIAL: {
        "category_patterns": [
            r"financial\s+(information|data)",
            r"payment\s+(information|data)",
            r"transaction\s+data",
            r"billing\s+(information|data)",
        ],
        "data_type_patterns": [
            r"(credit|debit)\s+card",
            r"card\s+number",
            r"bank\s+account",
            r"payment\s+(method|history|information)",
            r"transaction\s+(history|data|information)",
            r"(purchase|order)\s+(history|information|data)",
            r"billing\s+(address|information|history)",
            r"(credit\s+rating|credit\s+score)",
            r"financial\s+(statement|account)",
            r"(income|salary)",
            r"(CVV|CVC|security\s+code)",
            r"routing\s+number",
            r"(recipient|payee)\s+account",
            r"third[- ]party\s+recipient",
        ],
        "context_phrases": [
            r"collect.{0,50}(payment|transaction|financial|credit\s+card|bank)",
            r"(payment|financial).{0,30}information",
            r"purchase.{0,30}(history|data)",
        ]
    },

    DataCategory.AUTHENTICATION: {
        "category_patterns": [
            r"authentication\s+(information|data|credentials)",
            r"login\s+(information|credentials|data)",
            r"security\s+(information|credentials)",
        ],
        "data_type_patterns": [
            r"\bpassword",
            r"\bcredentials?\b",
            r"(access|api|auth|session)\s+token",
            r"security\s+question",
            r"\bPIN\b",
            r"(two[- ]factor|2FA|MFA)",
            r"(verification|authentication)\s+code",
            r"one[- ]time\s+password",
            r"\bOTP\b",
            r"OAuth",
        ],
        "context_phrases": [
            r"collect.{0,50}(password|credential|login|authentication)",
            r"(store|save).{0,30}password",
        ]
    },

    DataCategory.LOCATION: {
        "category_patterns": [
            r"location\s*(information|data)?",
            r"geo-?location",
            r"geographic(al)?\s+(information|data|location)",
        ],
        "data_type_patterns": [
            r"\bIP\s*(address)?",
            r"internet\s+protocol\s+address",
            r"\bGPS\b",
            r"(precise|coarse|approximate)\s+location",
            r"(latitude|longitude|coordinates)",
            r"(region|country|city|state|zip\s*code|postal\s*code)",
            r"(travel|location)\s+history",
            r"geo-?graphic",
            r"time\s+zone",
        ],
        "context_phrases": [
            r"collect.{0,50}(location|IP|GPS|geographic)",
            r"(location|IP).{0,30}(collect|gather|obtain)",
            r"track.{0,30}location",
        ]
    },

    DataCategory.WEB_HISTORY: {
        "category_patterns": [
            r"(web|browsing|browser|internet)\s+history",
            r"(browsing|online)\s+(data|behavior|activity)",
        ],
        "data_type_patterns": [
            r"(browsing|search|browser)\s+history",
            r"(search\s+)?(queries|terms)",
            r"(page|site)\s+visit",
            r"visited\s+(pages?|sites?|URLs?|websites?)",
            r"(websites?|URLs?)\s+visited",
            r"\bcookies?\b",
            r"(web\s+)?beacons?",
            r"(tracking|pixel)\s+(pixel|tag|beacon)",
            r"(HTTP|user[- ]agent|referer|referrer)\s+header",
            r"(access|visit)\s+(log|timestamp)",
            r"(log|logging)\s+data",
        ],
        "context_phrases": [
            r"collect.{0,50}(browsing|search|history|cookie|URL)",
            r"(browsing|history).{0,30}(collect|track|record)",
        ]
    },

    DataCategory.USER_ACTIVITY: {
        "category_patterns": [
            r"(user|usage)\s+(activity|data|behavior)",
            r"(online|internet|network)\s+activity",
            r"interaction\s+data",
            r"behavioral\s+data",
            r"technical\s+data",
        ],
        "data_type_patterns": [
            r"\bclicks?\b",
            r"mouse\s+(position|movement|click)",
            r"scroll\s*(position|data|behavior)?",
            r"keystroke\s*(logging|data)?",
            r"(typing|keyboard)\s+(data|pattern)",
            r"network\s+(monitoring|traffic|activity)",
            r"(app|application|extension)\s+(usage|activity|list)",
            r"installed\s+(apps?|applications?|software|extensions?)",
            r"(operating|OS)\s+system",
            r"(browser|device)\s+(type|version|information)",
            r"platform\b",
            r"session\s+(duration|data)",
            r"(time|date)\s+(stamp|spent)",
            r"engagement\s+(data|metrics)",
        ],
        "context_phrases": [
            r"collect.{0,50}(click|mouse|scroll|keystroke|usage|activity)",
            r"(monitor|track).{0,30}(activity|behavior|usage)",
        ]
    },

    DataCategory.WEBSITE_CONTENT: {
        "category_patterns": [
            r"(website|web|page|site)\s+content",
            r"content\s+(you\s+)?(view|access|read)",
        ],
        "data_type_patterns": [
            r"(page|web)\s+(text|content)",
            r"(images?|pictures?|photos?|graphics?)\s+(on|from|you)",
            r"(videos?|audio|sounds?|media)\s+(content|on|from|you)",
            r"(hyperlinks?|links?|URLs?)\s+(on|from)",
            r"(form\s+)?(data|content|input)\s*(you\s+)?(enter|submit|type|provide)",
            r"(document|file)\s+content",
            r"(text|content)\s+(from|on)\s+(web|page|site)",
        ],
        "context_phrases": [
            r"(access|read|collect).{0,50}(content|text|images|page)",
            r"content.{0,30}(access|read|collect)",
        ]
    },
}


class PolicyTextAnalyzer:
    """
    Analyzes privacy policy text to detect data categories through direct pattern matching.

    This complements the PoliGraph NLP pipeline by catching explicit category mentions
    and structured data type lists that may not parse well with dependency-based extraction.
    """

    def __init__(self, debug: bool = False):
        """
        Initialize the analyzer.

        Args:
            debug: If True, print debug information about matches
        """
        self.debug = debug
        # Compile all patterns for efficiency
        self._compiled_patterns = {}
        for category, pattern_groups in CATEGORY_PATTERNS.items():
            self._compiled_patterns[category] = {
                "category": [re.compile(p, re.IGNORECASE) for p in pattern_groups["category_patterns"]],
                "data_type": [re.compile(p, re.IGNORECASE) for p in pattern_groups["data_type_patterns"]],
                "context": [re.compile(p, re.IGNORECASE) for p in pattern_groups["context_phrases"]],
            }

    def analyze_text(self, text: str, min_confidence: float = 0.3) -> dict[DataCategory, list[CategoryMatch]]:
        """
        Analyze policy text and return detected data categories with matches.

        Args:
            text: The privacy policy text to analyze
            min_confidence: Minimum confidence threshold for including a category

        Returns:
            Dictionary mapping categories to list of matches
        """
        results = {}

        for category in DataCategory:
            matches = self._find_category_matches(text, category)
            if matches:
                # Filter by confidence
                confident_matches = [m for m in matches if m.confidence >= min_confidence]
                if confident_matches:
                    results[category] = confident_matches

        return results

    def extract_categories(self, text: str, min_confidence: float = 0.3) -> set[DataCategory]:
        """
        Extract just the set of detected data categories from policy text.

        Args:
            text: The privacy policy text to analyze
            min_confidence: Minimum confidence threshold

        Returns:
            Set of detected DataCategory values
        """
        matches = self.analyze_text(text, min_confidence)
        return set(matches.keys())

    def _find_category_matches(self, text: str, category: DataCategory) -> list[CategoryMatch]:
        """Find all matches for a specific category in the text."""
        matches = []
        patterns = self._compiled_patterns[category]

        # Check category patterns (high confidence)
        for pattern in patterns["category"]:
            for match in pattern.finditer(text):
                context = self._get_context(text, match.start(), match.end())
                matches.append(CategoryMatch(
                    category=category,
                    matched_text=match.group(),
                    context=context,
                    confidence=0.9  # High confidence for explicit category mentions
                ))

        # Check data type patterns (medium confidence)
        for pattern in patterns["data_type"]:
            for match in pattern.finditer(text):
                # Check if this match is in a collection context
                context = self._get_context(text, match.start(), match.end(), window=100)
                confidence = 0.5  # Base confidence for data type mentions

                # Boost confidence if in collection context
                if self._is_collection_context(context):
                    confidence = 0.7

                matches.append(CategoryMatch(
                    category=category,
                    matched_text=match.group(),
                    context=context,
                    confidence=confidence
                ))

        # Check context patterns (medium-high confidence)
        for pattern in patterns["context"]:
            for match in pattern.finditer(text):
                context = self._get_context(text, match.start(), match.end())
                matches.append(CategoryMatch(
                    category=category,
                    matched_text=match.group(),
                    context=context,
                    confidence=0.8
                ))

        # Deduplicate by matched text while keeping highest confidence
        seen = {}
        for match in matches:
            key = match.matched_text.lower()
            if key not in seen or match.confidence > seen[key].confidence:
                seen[key] = match

        return list(seen.values())

    def _get_context(self, text: str, start: int, end: int, window: int = 50) -> str:
        """Extract surrounding context for a match."""
        context_start = max(0, start - window)
        context_end = min(len(text), end + window)
        return text[context_start:context_end]

    def _is_collection_context(self, context: str) -> bool:
        """Check if the context indicates data collection."""
        collection_indicators = [
            r"\bcollect",
            r"\bgather",
            r"\bobtain",
            r"\breceive",
            r"\baccess",
            r"\buse\b",
            r"\bprocess",
            r"\bstore",
            r"\bretain",
            r"\brecord",
            r"\btrack",
            r"\bmonitor",
            r"\blog\b",
            r"\bshare",
            r"we\s+(may\s+)?",
            r"(this|the)\s+(app|extension|service|website)",
        ]
        for indicator in collection_indicators:
            if re.search(indicator, context, re.IGNORECASE):
                return True
        return False

    def analyze_policy_file(self, file_path: str | Path) -> dict[DataCategory, list[CategoryMatch]]:
        """
        Analyze a policy file (HTML or text).

        Args:
            file_path: Path to the policy file

        Returns:
            Dictionary mapping categories to matches
        """
        file_path = Path(file_path)

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # If HTML, strip tags
        if file_path.suffix.lower() in ['.html', '.htm']:
            content = self._strip_html(content)

        return self.analyze_text(content)

    def _strip_html(self, html: str) -> str:
        """Strip HTML tags and decode entities."""
        # Remove script and style content
        html = re.sub(r'<script[^>]*>.*?</script>', ' ', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<style[^>]*>.*?</style>', ' ', html, flags=re.DOTALL | re.IGNORECASE)
        # Remove tags
        text = re.sub(r'<[^>]+>', ' ', html)
        # Decode common entities
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&quot;', '"')
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()


def analyze_policy_url(url: str, debug: bool = False) -> set[DataCategory]:
    """
    Convenience function to analyze a privacy policy from a URL.

    Note: This requires the policy HTML to already be fetched.
    For URL fetching, use the pipeline's crawl functionality.

    Args:
        url: URL of the policy (for reference only)
        debug: Enable debug output

    Returns:
        Set of detected categories
    """
    # This is a stub - actual URL fetching should be done by the pipeline
    raise NotImplementedError("Use PolicyTextAnalyzer.analyze_text() with fetched content")


if __name__ == "__main__":
    # Test with Coupert's policy excerpt
    test_policy = """
    2. What Information We Collect
    We may collect and process various categories of personal information, which refers to any information that identifies or relates to an identifiable individual. These categories include:

    Identity Data – such as account credentials, username, and third-party authentication data (e.g., OAuth login from Google, Apple).
    Contact Data – such as your email address and phone number.
    Financial Data – such as third-party recipient account.
    Transaction Data – such as order information collected when you make purchases while using Coupert, and details about products or services you purchased via merchants through Coupert links.
    Technical Data – such as your IP address, cookies, browser type and version, time zone setting, browser extension version, operating system, platform, URLs, and device identifiers.
    Profile Data – such as your account settings, preferences, survey responses, reviews, ratings, and feedback.
    Usage Data – such as how you use Coupert's services.
    Marketing and Communications Data – such as your notification preferences.
    """

    print("=" * 60)
    print("TESTING POLICY TEXT ANALYZER")
    print("=" * 60)
    print("\nInput text (Coupert policy excerpt):")
    print(test_policy[:200] + "...")
    print()

    analyzer = PolicyTextAnalyzer(debug=True)
    results = analyzer.analyze_text(test_policy)

    print("\nDetected Categories:")
    print("-" * 40)
    for category, matches in results.items():
        print(f"\n{category.value.upper()}:")
        for match in matches[:3]:  # Show first 3 matches
            print(f"  - '{match.matched_text}' (confidence: {match.confidence:.2f})")

    print("\n" + "=" * 60)
    print("EXTRACTED CATEGORIES (Set):")
    print("=" * 60)
    categories = analyzer.extract_categories(test_policy)
    print([c.value for c in categories])
