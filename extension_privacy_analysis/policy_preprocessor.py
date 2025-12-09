"""
Policy Preprocessor - Transform structured privacy policies for better NLP parsing.

Modern privacy policies often use structured formats like:
    "Identity Data – such as account credentials, username"
    "Financial Data – such as third-party recipient account"

These structured formats don't parse well with PoliGraph's dependency-based NLP.
This preprocessor transforms them into explicit collection statements:
    "We collect Identity Data. We collect account credentials. We collect username."

This complements the PolicyTextAnalyzer by helping the PoliGraph NLP pipeline
extract more data types from policies.
"""

import re
import os
from typing import Optional
from pathlib import Path

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False


# Claude prompt for policy transformation
POLICY_TRANSFORMATION_PROMPT = """You are transforming a privacy policy section into explicit data collection statements that an NLP system can parse.

The NLP system looks for EXPLICIT data collection statements using these verbs:
- COLLECT: collect, gather, obtain, receive, acquire, request
- USE: use, access, process, utilize, analyze
- SHARE: share, disclose, provide, transfer, transmit
- STORE: store, save, retain, maintain, keep, record

CRITICAL RULES:
1. For EACH data category AND data type mentioned, write SEPARATE sentences using "We collect"
2. EXPAND structured lists like "Financial Data – such as X, Y, Z" into multiple sentences
3. Use ACTIVE VOICE: "We collect your email address" NOT "Email may be collected"
4. Make each sentence STANDALONE - the NLP processes sentences independently
5. Preserve ALL specific data types mentioned (don't summarize)

INPUT FORMAT EXAMPLES:
- "Identity Data – such as account credentials, username"
- "We may collect the following categories of information"
- "Personal Information: name, email, phone number"

OUTPUT FORMAT:
Transform each into explicit collection statements like:
"We collect Identity Data. We collect account credentials. We collect your username."

POLICY TEXT TO TRANSFORM:
{policy_text}

Transform this into explicit privacy policy statements. Be thorough - include EVERY data type mentioned:"""


class PolicyPreprocessor:
    """
    Preprocesses privacy policy text to help PoliGraph's NLP pipeline.

    Transforms structured policy formats into explicit collection statements
    that parse better with dependency-based extraction.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-haiku-20240307"):
        """
        Initialize the preprocessor.

        Args:
            api_key: Anthropic API key. If not provided, uses env var or falls back to rules.
            model: Claude model to use. Defaults to Haiku for cost efficiency.
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.model = model
        self.client = None
        if self.api_key and HAS_ANTHROPIC:
            self.client = anthropic.Anthropic(api_key=self.api_key)

    def transform_policy(self, policy_text: str, company_name: str = "We") -> str:
        """
        Transform policy text into explicit collection statements.

        Args:
            policy_text: Raw policy text (can be HTML or plain text)
            company_name: Name of the company (used in statements)

        Returns:
            Transformed text with explicit collection statements
        """
        # Strip HTML if present
        text = self._strip_html(policy_text)

        # First apply rule-based transformation
        transformed = self._rule_based_transform(text, company_name)

        # If Claude is available, enhance with LLM
        if self.client:
            try:
                enhanced = self._claude_transform(text, company_name)
                # Combine both for maximum coverage
                transformed = transformed + "\n\n" + enhanced
            except Exception as e:
                print(f"Warning: Claude transformation failed ({e}), using rule-based only")

        return transformed

    def _strip_html(self, text: str) -> str:
        """Strip HTML tags from text."""
        # Remove script and style
        text = re.sub(r'<script[^>]*>.*?</script>', ' ', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', ' ', text, flags=re.DOTALL | re.IGNORECASE)
        # Remove tags
        text = re.sub(r'<[^>]+>', ' ', text)
        # Decode entities
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&quot;', '"')
        text = text.replace('&#39;', "'")
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _rule_based_transform(self, text: str, company_name: str = "We") -> str:
        """
        Apply rule-based transformations to policy text.

        Handles common structured formats like:
        - "Category Data – such as item1, item2"
        - "Category Data: item1, item2"
        - "Category Data (e.g., item1, item2)"
        """
        output_lines = []

        # Pattern for "Category Data – such as items" or "Category Data: items"
        # Handles em-dash, en-dash, regular dash, colon
        category_pattern = r'([A-Z][a-zA-Z]+(?:\s+[A-Z]?[a-z]+)*\s+(?:Data|Information))[\s–—\-:]+(?:such as|including|e\.g\.|for example|like)?\s*([^\.]+)'

        for match in re.finditer(category_pattern, text, re.IGNORECASE):
            category = match.group(1).strip()
            items_text = match.group(2).strip()

            # Generate statement for the category
            output_lines.append(f"{company_name} collect {category.lower()}.")

            # Split items by common delimiters
            items = re.split(r',\s*|\band\b|\bor\b', items_text)

            for item in items:
                item = item.strip()
                # Clean up item
                item = re.sub(r'\([^)]*\)', '', item)  # Remove parenthetical notes
                item = item.strip(' .,;')

                if item and len(item) > 2:
                    output_lines.append(f"{company_name} collect {item}.")

        # Pattern for "We collect/gather/obtain X"
        collect_pattern = r'(?:we|the company|this service)\s+(?:may\s+)?(?:collect|gather|obtain|receive|access|process)\s+([^\.]+)'

        for match in re.finditer(collect_pattern, text, re.IGNORECASE):
            items_text = match.group(1).strip()

            # If it's a list, split it
            if ',' in items_text or ' and ' in items_text:
                items = re.split(r',\s*|\band\b', items_text)
                for item in items:
                    item = item.strip(' .,;')
                    if item and len(item) > 2:
                        output_lines.append(f"{company_name} collect {item}.")
            else:
                output_lines.append(f"{company_name} collect {items_text}.")

        # Pattern for "For example: item1, item2" or "such as item1, item2"
        example_pattern = r'(?:for example|such as|e\.g\.|including)[:\s]+([^\.]+)'

        for match in re.finditer(example_pattern, text, re.IGNORECASE):
            items_text = match.group(1).strip()
            items = re.split(r',\s*|\band\b|\bor\b', items_text)

            for item in items:
                item = item.strip(' .,;')
                if item and len(item) > 2:
                    output_lines.append(f"{company_name} collect {item}.")

        # Filter out noisy/invalid matches
        filtered_lines = []
        noise_patterns = [
            r'^\w+ collect we\b',  # "We collect We..."
            r'^\w+ collect what\b',  # "We collect What..."
            r'^\w+ collect which\b',  # "We collect which..."
            r'^\w+ collect \d',  # "We collect 2..."
            r'^\w+ collect may\b',  # "We collect may..."
            r'^\w+ collect (the|a|an)\s*$',  # "We collect the."
            r'^\w+ collect [a-z]{1,2}\.$',  # Very short items
        ]

        for line in output_lines:
            is_noise = False
            for pattern in noise_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    is_noise = True
                    break
            if not is_noise:
                filtered_lines.append(line)

        # Deduplicate while preserving order
        seen = set()
        unique_lines = []
        for line in filtered_lines:
            line_lower = line.lower()
            if line_lower not in seen:
                seen.add(line_lower)
                unique_lines.append(line)

        return '\n'.join(unique_lines)

    def _claude_transform(self, text: str, company_name: str) -> str:
        """Use Claude to transform policy text."""
        if not self.client:
            return ""

        prompt = POLICY_TRANSFORMATION_PROMPT.format(policy_text=text[:8000])  # Limit input size

        message = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        return message.content[0].text

    def transform_policy_file(self, file_path: str | Path, company_name: str = "We") -> str:
        """
        Transform a policy file.

        Args:
            file_path: Path to HTML or text file
            company_name: Name of the company

        Returns:
            Transformed policy text
        """
        file_path = Path(file_path)

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        return self.transform_policy(content, company_name)


def preprocess_policy_for_analysis(policy_html: str, company_name: str = "We",
                                    api_key: Optional[str] = None) -> str:
    """
    Convenience function to preprocess policy text.

    Args:
        policy_html: Raw policy HTML/text
        company_name: Company name for statements
        api_key: Optional Anthropic API key

    Returns:
        Preprocessed policy text ready for PoliGraph
    """
    preprocessor = PolicyPreprocessor(api_key=api_key)
    return preprocessor.transform_policy(policy_html, company_name)


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
    print("ORIGINAL POLICY TEXT:")
    print("=" * 60)
    print(test_policy[:500] + "...")
    print()

    # Test rule-based preprocessing (no API needed)
    preprocessor = PolicyPreprocessor()
    transformed = preprocessor._rule_based_transform(test_policy, "Coupert")

    print("=" * 60)
    print("RULE-BASED TRANSFORMATION:")
    print("=" * 60)
    print(transformed)
    print()

    # Full transformation with Claude if API key available
    if os.environ.get("ANTHROPIC_API_KEY"):
        print("=" * 60)
        print("CLAUDE-ENHANCED TRANSFORMATION:")
        print("=" * 60)
        full_transform = preprocessor.transform_policy(test_policy, "Coupert")
        print(full_transform)
    else:
        print("Set ANTHROPIC_API_KEY to test Claude transformation")
