"""
Disclosure Preprocessor using Claude API.

This module transforms Chrome Web Store developer disclosures into
natural language text that PoliGraph's NLP pipeline can analyze.

The problem with raw developer disclosures:
1. Bullet point format doesn't parse well
2. Negative language ("does NOT collect") isn't handled by PoliGraph
3. Examples are inline with category names
4. Structured format vs natural sentences

This preprocessor converts disclosures into explicit privacy policy-like text.
"""

import os
import re
import json
from typing import Optional

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False


# Improved prompt template optimized for PoliGraph's verb patterns
TRANSFORMATION_PROMPT = """You are converting a Chrome Web Store developer disclosure into privacy policy text that an NLP system can parse.

The NLP system looks for EXPLICIT data collection statements using these verbs:
- COLLECT: collect, gather, obtain, receive, acquire, request
- USE: use, access, process, utilize, analyze
- SHARE: share, disclose, provide, transfer, transmit
- STORE: store, save, retain, maintain, keep, record

CRITICAL RULES:
1. For EACH data category mentioned, write a SEPARATE sentence using "We collect" or "[Extension] collects"
2. List SPECIFIC data types, not just categories. Expand "For example:" items into the sentence.
3. Use ACTIVE VOICE: "We collect your email address" NOT "Email addresses may be collected"
4. Make each sentence STANDALONE - the NLP processes sentences independently
5. Be EXPLICIT and REDUNDANT - repeat the company name in each sentence

INPUT DISCLOSURE:
{disclosure_text}

EXTENSION NAME: {extension_name}

Transform this into privacy policy paragraphs. For each data category mentioned, write explicit sentences.

EXAMPLE INPUT:
"Personally identifiable information
For example: name, address, email address"

EXAMPLE OUTPUT:
"We collect personally identifiable information. We collect your name. We collect your address. We collect your email address. We store this personal information on our servers."

EXAMPLE INPUT:
"User activity
For example: clicks, mouse position, scroll"

EXAMPLE OUTPUT:
"We collect user activity data. We collect information about your clicks. We collect your mouse position. We collect scroll data. We monitor your network activity."

EXAMPLE INPUT:
"Website content
For example: text, images, sounds, videos"

EXAMPLE OUTPUT:
"We access website content. We collect text from webpages. We access images on websites you visit. We collect sounds and videos. We gather hyperlinks from web pages."

Now transform the disclosure. Write one paragraph per data category, with multiple explicit collection statements:"""


class DisclosurePreprocessor:
    """
    Preprocesses Chrome Web Store developer disclosures using Claude API
    to create PoliGraph-analyzable text.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-haiku-20240307"):
        """
        Initialize the preprocessor.

        Args:
            api_key: Anthropic API key. If not provided, reads from ANTHROPIC_API_KEY env var.
            model: Claude model to use. Defaults to Haiku for cost efficiency.
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Anthropic API key required. Set ANTHROPIC_API_KEY environment variable "
                "or pass api_key parameter."
            )

        self.model = model
        self.client = anthropic.Anthropic(api_key=self.api_key)

    def transform_disclosure(self, disclosure_text: str, extension_name: str) -> str:
        """
        Transform a developer disclosure into natural language privacy policy text.

        Args:
            disclosure_text: Raw disclosure text from Chrome Web Store
            extension_name: Name of the extension

        Returns:
            Transformed natural language text suitable for PoliGraph analysis
        """
        # First, do rule-based preprocessing
        preprocessed = self._rule_based_preprocessing(disclosure_text, extension_name)

        # Then use Claude for sophisticated transformation
        try:
            transformed = self._claude_transform(disclosure_text, extension_name)
            return transformed
        except Exception as e:
            print(f"Warning: Claude transformation failed ({e}), using rule-based fallback")
            return preprocessed

    def _rule_based_preprocessing(self, disclosure_text: str, extension_name: str) -> str:
        """
        Apply rule-based preprocessing - creates explicit collection statements.
        This is the fallback when Claude API is not available.
        """
        text = disclosure_text
        output_lines = []

        # Check if this is a "no data collection" disclosure
        if "will not collect or use your data" in text.lower():
            return f"{extension_name} does not collect or use any user data."

        # Parse each category and generate explicit statements
        categories = {
            "Personally identifiable information": {
                "intro": f"We collect personally identifiable information.",
                "items": ["name", "address", "email address", "age", "identification number"],
                "extra": [
                    f"We collect your name.",
                    f"We collect your email address.",
                    f"We collect your postal address.",
                    f"We store personal information.",
                ]
            },
            "Personal communications": {
                "intro": f"We collect personal communications.",
                "items": ["emails", "texts", "chat messages"],
                "extra": [
                    f"We access your emails.",
                    f"We collect your text messages.",
                    f"We collect chat messages.",
                ]
            },
            "Financial and payment information": {
                "intro": f"We collect financial and payment information.",
                "items": ["transactions", "credit card numbers", "credit ratings", "financial statements", "payment history"],
                "extra": [
                    f"We collect transaction data.",
                    f"We collect credit card information.",
                    f"We collect payment history.",
                    f"We store financial information.",
                ]
            },
            "Authentication information": {
                "intro": f"We collect authentication information.",
                "items": ["passwords", "credentials", "security question", "PIN"],
                "extra": [
                    f"We collect your password.",
                    f"We collect login credentials.",
                    f"We store authentication data.",
                ]
            },
            "Location": {
                "intro": f"We collect location data.",
                "items": ["region", "IP address", "GPS coordinates"],
                "extra": [
                    f"We collect your IP address.",
                    f"We collect GPS coordinates.",
                    f"We collect your geographic location.",
                    f"We store location information.",
                ]
            },
            "Web history": {
                "intro": f"We collect web history.",
                "items": ["browsing history", "page visits", "visit timestamps"],
                "extra": [
                    f"We collect your browsing history.",
                    f"We collect page visits.",
                    f"We collect visit timestamps.",
                    f"We store web history data.",
                ]
            },
            "User activity": {
                "intro": f"We collect user activity data.",
                "items": ["network monitoring", "clicks", "mouse position", "scroll", "keystroke logging"],
                "extra": [
                    f"We monitor network activity.",
                    f"We collect click data.",
                    f"We collect mouse position.",
                    f"We collect scroll data.",
                    f"We collect keystroke data.",
                ]
            },
            "Website content": {
                "intro": f"We access website content.",
                "items": ["text", "images", "sounds", "videos", "hyperlinks"],
                "extra": [
                    f"We collect text from websites.",
                    f"We access images on web pages.",
                    f"We collect videos.",
                    f"We gather hyperlinks.",
                ]
            },
        }

        for category_name, category_data in categories.items():
            if category_name.lower() in text.lower():
                output_lines.append(category_data["intro"])
                output_lines.extend(category_data["extra"])
                output_lines.append("")  # Blank line between categories

        # Handle negative declarations
        if "not being sold" in text.lower():
            output_lines.append(f"We do not sell your data to third parties.")
        if "not being used or transferred for purposes" in text.lower():
            output_lines.append(f"We do not use data for purposes unrelated to core functionality.")

        if not output_lines:
            # Fallback to basic transformation
            text = re.sub(r'handles the following:', 'collects the following data:', text, flags=re.IGNORECASE)
            text = re.sub(r'^Privacy practices\s*\n', '', text)
            text = re.sub(r'has disclosed the following information[^\.]+\.', '', text)
            return text

        return "\n".join(output_lines)

    def _claude_transform(self, disclosure_text: str, extension_name: str) -> str:
        """
        Use Claude to transform the disclosure into natural language.
        """
        prompt = TRANSFORMATION_PROMPT.format(
            disclosure_text=disclosure_text,
            extension_name=extension_name
        )

        message = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        return message.content[0].text

    def batch_transform(self, disclosures: list[tuple[str, str]]) -> list[str]:
        """
        Transform multiple disclosures.

        Args:
            disclosures: List of (disclosure_text, extension_name) tuples

        Returns:
            List of transformed texts
        """
        results = []
        for disclosure_text, extension_name in disclosures:
            transformed = self.transform_disclosure(disclosure_text, extension_name)
            results.append(transformed)
        return results


def create_disclosure_html(transformed_text: str, extension_name: str, output_path: str):
    """
    Create an HTML file from transformed disclosure text that can be fed to PoliGraph.

    This mimics the format that PoliGraph's html_crawler expects.
    """
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{extension_name} - Developer Disclosure (Privacy Practices)</title>
</head>
<body>
    <h1>{extension_name} Privacy Practices</h1>
    <article>
        <h2>Data Collection and Usage</h2>
        {_text_to_paragraphs(transformed_text)}
    </article>
</body>
</html>
"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    return output_path


def _text_to_paragraphs(text: str) -> str:
    """Convert plain text to HTML paragraphs."""
    paragraphs = text.split('\n\n')
    html_paragraphs = []
    for p in paragraphs:
        p = p.strip()
        if p:
            # Handle sentences that might be on separate lines
            p = p.replace('\n', ' ')
            html_paragraphs.append(f"<p>{p}</p>")
    return '\n        '.join(html_paragraphs)


# Convenience function for direct use
def preprocess_disclosure(disclosure_text: str, extension_name: str,
                          api_key: Optional[str] = None) -> str:
    """
    Convenience function to preprocess a single disclosure.

    Args:
        disclosure_text: Raw Chrome Web Store disclosure
        extension_name: Name of the extension
        api_key: Optional API key (uses env var if not provided)

    Returns:
        Transformed text ready for PoliGraph analysis
    """
    preprocessor = DisclosurePreprocessor(api_key=api_key)
    return preprocessor.transform_disclosure(disclosure_text, extension_name)


if __name__ == "__main__":
    # Test with the Grammarly example
    test_disclosure = """Privacy practices
Grammarly: AI Writing Assistant and Grammar Checker App has disclosed the following information regarding the collection and usage of your data. More detailed information can be found in the developer's privacy policy.

Grammarly: AI Writing Assistant and Grammar Checker App handles the following:
Personally identifiable information
For example: name, address, email address, age, or identification number

Personal communications
For example: emails, texts, or chat messages

Location
For example: region, IP address, GPS coordinates, or information about things near the user's device

User activity
For example: network monitoring, clicks, mouse position, scroll, or keystroke logging

Website content
For example: text, images, sounds, videos, or hyperlinks

This developer declares that your data is
Not being sold to third parties, outside of the approved use cases
Not being used or transferred for purposes that are unrelated to the item's core functionality
Not being used or transferred to determine creditworthiness or for lending purposes"""

    print("=" * 60)
    print("ORIGINAL DISCLOSURE:")
    print("=" * 60)
    print(test_disclosure)
    print()

    # Test rule-based preprocessing (doesn't require API key)
    preprocessor = DisclosurePreprocessor.__new__(DisclosurePreprocessor)
    rule_based = preprocessor._rule_based_preprocessing(test_disclosure, "Grammarly")

    print("=" * 60)
    print("RULE-BASED TRANSFORMATION:")
    print("=" * 60)
    print(rule_based)
    print()

    # Full transformation requires API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        print("=" * 60)
        print("CLAUDE-ENHANCED TRANSFORMATION:")
        print("=" * 60)
        full_preprocessor = DisclosurePreprocessor(api_key=api_key)
        transformed = full_preprocessor.transform_disclosure(test_disclosure, "Grammarly")
        print(transformed)
    else:
        print("Set ANTHROPIC_API_KEY to test full Claude transformation")
