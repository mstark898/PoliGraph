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
import anthropic


# Default prompt template for Claude to transform disclosures
TRANSFORMATION_PROMPT = """You are a privacy policy text converter. Your task is to transform Chrome Web Store developer disclosures into natural language privacy policy text that can be analyzed by NLP tools.

IMPORTANT RULES:
1. Convert each data category mentioned into explicit collection statements
2. Use active voice with the extension/company as the subject (e.g., "We collect...", "[Extension Name] collects...")
3. Expand the "For example" items into the sentence naturally
4. For NEGATIVE declarations (e.g., "Not being sold"), convert them but clearly mark the action being negated
5. Remove bullet points and create flowing paragraphs
6. Be explicit about what data types are collected
7. If the disclosure says they "handle" data, convert it to "collect and use"

INPUT DISCLOSURE:
{disclosure_text}

EXTENSION NAME: {extension_name}

OUTPUT FORMAT:
Produce a natural language privacy policy excerpt that explicitly states what data is collected. Structure it like a real privacy policy section.

For example, if the input mentions:
"Personally identifiable information
For example: name, address, email address"

Output something like:
"[Extension Name] collects personally identifiable information, including your name, address, and email address."

If the disclosure mentions that data is NOT sold or NOT used for certain purposes, include those as separate statements like:
"[Extension Name] does not sell your data to third parties."

Now transform the disclosure:"""


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
            transformed = self._claude_transform(preprocessed, extension_name)
            return transformed
        except Exception as e:
            print(f"Warning: Claude transformation failed ({e}), using rule-based fallback")
            return preprocessed

    def _rule_based_preprocessing(self, disclosure_text: str, extension_name: str) -> str:
        """
        Apply rule-based preprocessing before Claude transformation.
        This handles common patterns and ensures a baseline transformation.
        """
        text = disclosure_text

        # Check if this is a "no data collection" disclosure
        if "will not collect or use your data" in text.lower():
            return f"{extension_name} does not collect or use any user data."

        # Replace "handles the following" with collection language
        text = re.sub(
            r'handles the following:',
            'collects and processes the following types of data:',
            text,
            flags=re.IGNORECASE
        )

        # Convert data category headers to sentences
        category_patterns = [
            (r'Personally identifiable information\s*\nFor example:\s*([^\n]+)',
             f'{extension_name} collects personally identifiable information including \\1.'),
            (r'Personal communications\s*\nFor example:\s*([^\n]+)',
             f'{extension_name} collects personal communications including \\1.'),
            (r'Financial and payment information\s*\nFor example:\s*([^\n]+)',
             f'{extension_name} collects financial and payment information including \\1.'),
            (r'Authentication information\s*\nFor example:\s*([^\n]+)',
             f'{extension_name} collects authentication information including \\1.'),
            (r'Location\s*\nFor example:\s*([^\n]+)',
             f'{extension_name} collects location data including \\1.'),
            (r'Web history\s*\nFor example:\s*([^\n]+)',
             f'{extension_name} collects web history including \\1.'),
            (r'User activity\s*\nFor example:\s*([^\n]+)',
             f'{extension_name} collects user activity data including \\1.'),
            (r'Website content\s*\nFor example:\s*([^\n]+)',
             f'{extension_name} accesses website content including \\1.'),
            (r'Health information\s*\nFor example:\s*([^\n]+)',
             f'{extension_name} collects health information including \\1.'),
        ]

        for pattern, replacement in category_patterns:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

        # Handle negative declarations
        negative_patterns = [
            (r'Not being sold to third parties[^\.]*',
             f'{extension_name} does not sell user data to third parties.'),
            (r'Not being used or transferred for purposes.+?core functionality',
             f'{extension_name} does not use data for purposes unrelated to its core functionality.'),
            (r'Not being used or transferred to determine creditworthiness[^\.]*',
             f'{extension_name} does not use data for creditworthiness determination.'),
        ]

        for pattern, replacement in negative_patterns:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE | re.DOTALL)

        # Clean up "This developer declares that your data is" section
        text = re.sub(
            r'This developer declares that your data is\s*',
            '\n\nRegarding data usage practices: ',
            text,
            flags=re.IGNORECASE
        )

        # Remove header line
        text = re.sub(r'^Privacy practices\s*\n', '', text)
        text = re.sub(r'has disclosed the following information[^\.]+\.', '', text)
        text = re.sub(r'More detailed information can be found[^\.]+\.', '', text)

        # Clean up whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = text.strip()

        return text

    def _claude_transform(self, preprocessed_text: str, extension_name: str) -> str:
        """
        Use Claude to transform the preprocessed disclosure into natural language.
        """
        prompt = TRANSFORMATION_PROMPT.format(
            disclosure_text=preprocessed_text,
            extension_name=extension_name
        )

        message = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
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
    # Test with the Grammarly example from the user's prompt
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
