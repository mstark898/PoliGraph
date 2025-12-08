#!/usr/bin/env python3
"""
Extension Privacy Analysis Pipeline

This script orchestrates the full pipeline for analyzing Chrome extension privacy:
1. Fetches/processes privacy policies using PoliGraph
2. Preprocesses developer disclosures using Claude API
3. Runs PoliGraph analysis on preprocessed disclosures
4. Compares results and generates a comparison table

Usage:
    python run_pipeline.py --all                    # Analyze all extensions
    python run_pipeline.py --extension "Grammarly" # Analyze specific extension
    python run_pipeline.py --list                   # List available extensions
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from extension_privacy_analysis.extensions_data import EXTENSIONS, Extension
from extension_privacy_analysis.disclosure_preprocessor import (
    DisclosurePreprocessor,
    create_disclosure_html
)
from extension_privacy_analysis.data_categories import DataCategory
from extension_privacy_analysis.comparison_analysis import (
    ComparisonAnalyzer,
    generate_comparison_table,
    save_results_csv,
    save_results_html
)


class ExtensionPrivacyPipeline:
    """
    Main pipeline for analyzing extension privacy discrepancies.
    """

    def __init__(self, output_dir: str = "extension_analysis_output",
                 anthropic_api_key: Optional[str] = None):
        """
        Initialize the pipeline.

        Args:
            output_dir: Directory to store all output files
            anthropic_api_key: API key for Claude (uses env var if not provided)
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.policies_dir = self.output_dir / "privacy_policies"
        self.disclosures_dir = self.output_dir / "developer_disclosures"
        self.results_dir = self.output_dir / "results"

        for d in [self.policies_dir, self.disclosures_dir, self.results_dir]:
            d.mkdir(parents=True, exist_ok=True)

        self.api_key = anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.preprocessor = None
        if self.api_key:
            self.preprocessor = DisclosurePreprocessor(api_key=self.api_key)

    def analyze_extension(self, extension: Extension, skip_policy_crawl: bool = False) -> dict:
        """
        Run the full analysis pipeline for a single extension.

        Args:
            extension: Extension to analyze
            skip_policy_crawl: If True, skip crawling the privacy policy (use existing)

        Returns:
            Dictionary with analysis results
        """
        print(f"\n{'='*60}")
        print(f"Analyzing: {extension.name}")
        print(f"{'='*60}")

        results = {
            "extension_name": extension.name,
            "extension_id": extension.extension_id,
            "privacy_policy_url": extension.privacy_policy_url,
            "policy_analyzed": False,
            "disclosure_analyzed": False,
            "policy_categories": set(),
            "disclosure_categories": set(),
            "errors": []
        }

        # Step 1: Analyze privacy policy (if URL available)
        policy_dir = self.policies_dir / extension.extension_id
        if extension.privacy_policy_url and extension.privacy_policy_url.strip():
            if not skip_policy_crawl or not (policy_dir / "graph-original.yml").exists():
                print(f"\n[1/4] Crawling privacy policy: {extension.privacy_policy_url}")
                policy_success = self._crawl_and_analyze_policy(
                    extension.privacy_policy_url,
                    policy_dir
                )
            else:
                print(f"\n[1/4] Using existing privacy policy analysis")
                policy_success = (policy_dir / "graph-original.yml").exists()

            if policy_success:
                results["policy_analyzed"] = True
                results["policy_graph_path"] = str(policy_dir / "graph-original.yml")
        else:
            print(f"\n[1/4] No privacy policy URL available, skipping")

        # Step 2: Preprocess developer disclosure
        disclosure_dir = self.disclosures_dir / extension.extension_id
        disclosure_dir.mkdir(parents=True, exist_ok=True)

        if extension.developer_disclosure:
            print(f"\n[2/4] Preprocessing developer disclosure")
            disclosure_success = self._preprocess_disclosure(extension, disclosure_dir)
            if disclosure_success:
                results["disclosure_preprocessed"] = True
        else:
            print(f"\n[2/4] No developer disclosure available, skipping")
            results["errors"].append("No developer disclosure available")

        # Step 3: Analyze preprocessed disclosure with PoliGraph
        if results.get("disclosure_preprocessed"):
            print(f"\n[3/4] Analyzing preprocessed disclosure with PoliGraph")
            disclosure_success = self._analyze_disclosure(disclosure_dir)
            if disclosure_success:
                results["disclosure_analyzed"] = True
                results["disclosure_graph_path"] = str(disclosure_dir / "graph-original.yml")
        else:
            print(f"\n[3/4] Skipping disclosure analysis (no preprocessed disclosure)")

        # Step 4: Extract categories from both sources
        print(f"\n[4/4] Extracting data categories")

        if results.get("policy_analyzed"):
            policy_graph = policy_dir / "graph-original.yml"
            results["policy_categories"] = self._extract_categories_from_graph(policy_graph)

        if results.get("disclosure_analyzed"):
            disclosure_graph = disclosure_dir / "graph-original.yml"
            results["disclosure_categories"] = self._extract_categories_from_graph(disclosure_graph)

        # Also extract from raw disclosure text (for comparison)
        if extension.developer_disclosure:
            from extension_privacy_analysis.data_categories import parse_chrome_disclosure_categories
            results["disclosure_raw_categories"] = parse_chrome_disclosure_categories(
                extension.developer_disclosure
            )

        return results

    def _crawl_and_analyze_policy(self, url: str, output_dir: Path) -> bool:
        """Crawl a privacy policy URL and run PoliGraph analysis."""
        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Step 1: Crawl HTML
            print(f"  - Crawling HTML...")
            result = subprocess.run(
                [sys.executable, "-m", "poligrapher.scripts.html_crawler", url, str(output_dir)],
                capture_output=True,
                text=True,
                timeout=120
            )
            if result.returncode != 0:
                print(f"  - Crawl failed: {result.stderr[:200]}")
                return False

            # Step 2: Initialize document
            print(f"  - Initializing document...")
            result = subprocess.run(
                [sys.executable, "-m", "poligrapher.scripts.init_document", str(output_dir)],
                capture_output=True,
                text=True,
                timeout=300
            )
            if result.returncode != 0:
                print(f"  - Init failed: {result.stderr[:200]}")
                return False

            # Step 3: Run annotators
            print(f"  - Running annotators...")
            result = subprocess.run(
                [sys.executable, "-m", "poligrapher.scripts.run_annotators", str(output_dir)],
                capture_output=True,
                text=True,
                timeout=600
            )
            if result.returncode != 0:
                print(f"  - Annotators failed: {result.stderr[:200]}")
                return False

            # Step 4: Build graph
            print(f"  - Building graph...")
            result = subprocess.run(
                [sys.executable, "-m", "poligrapher.scripts.build_graph", str(output_dir)],
                capture_output=True,
                text=True,
                timeout=120
            )
            if result.returncode != 0:
                print(f"  - Build graph failed: {result.stderr[:200]}")
                return False

            print(f"  - Success! Graph saved to {output_dir}/graph-original.yml")
            return True

        except subprocess.TimeoutExpired:
            print(f"  - Timeout during analysis")
            return False
        except Exception as e:
            print(f"  - Error: {e}")
            return False

    def _preprocess_disclosure(self, extension: Extension, output_dir: Path) -> bool:
        """Preprocess developer disclosure and create HTML for PoliGraph."""
        try:
            if self.preprocessor:
                # Use Claude for sophisticated transformation
                transformed = self.preprocessor.transform_disclosure(
                    extension.developer_disclosure,
                    extension.name
                )
            else:
                # Fall back to rule-based preprocessing
                print("  - Warning: No API key, using rule-based preprocessing")
                preprocessor = DisclosurePreprocessor.__new__(DisclosurePreprocessor)
                transformed = preprocessor._rule_based_preprocessing(
                    extension.developer_disclosure,
                    extension.name
                )

            # Save transformed text
            transformed_path = output_dir / "transformed_disclosure.txt"
            with open(transformed_path, 'w', encoding='utf-8') as f:
                f.write(transformed)
            print(f"  - Saved transformed disclosure to {transformed_path}")

            # Create HTML for PoliGraph
            html_path = output_dir / "disclosure.html"
            create_disclosure_html(transformed, extension.name, str(html_path))
            print(f"  - Created HTML at {html_path}")

            # Create cleaned.html (what PoliGraph expects)
            cleaned_path = output_dir / "cleaned.html"
            shutil.copy(html_path, cleaned_path)

            return True

        except Exception as e:
            print(f"  - Error preprocessing disclosure: {e}")
            return False

    def _analyze_disclosure(self, disclosure_dir: Path) -> bool:
        """Run PoliGraph analysis on preprocessed disclosure."""
        try:
            # For disclosures, we skip html_crawler since we already have the HTML

            # Create a minimal accessibility_tree.json
            html_path = disclosure_dir / "cleaned.html"
            if not html_path.exists():
                print(f"  - No cleaned.html found")
                return False

            # Read the HTML and create accessibility tree structure
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()

            # Extract text content for accessibility tree
            import re
            # Remove HTML tags to get text
            text = re.sub(r'<[^>]+>', ' ', html_content)
            text = re.sub(r'\s+', ' ', text).strip()

            # Create minimal accessibility tree
            tree = {
                "role": "RootWebArea",
                "name": "Developer Disclosure",
                "children": [
                    {
                        "role": "heading",
                        "name": "Privacy Practices",
                        "level": 1
                    },
                    {
                        "role": "paragraph",
                        "name": text
                    }
                ]
            }

            tree_path = disclosure_dir / "accessibility_tree.json"
            with open(tree_path, 'w', encoding='utf-8') as f:
                json.dump(tree, f, indent=2)

            # Run init_document
            print(f"  - Initializing document...")
            result = subprocess.run(
                [sys.executable, "-m", "poligrapher.scripts.init_document", str(disclosure_dir)],
                capture_output=True,
                text=True,
                timeout=300
            )
            if result.returncode != 0:
                print(f"  - Init failed: {result.stderr[:200]}")
                return False

            # Run annotators
            print(f"  - Running annotators...")
            result = subprocess.run(
                [sys.executable, "-m", "poligrapher.scripts.run_annotators", str(disclosure_dir)],
                capture_output=True,
                text=True,
                timeout=600
            )
            if result.returncode != 0:
                print(f"  - Annotators failed: {result.stderr[:200]}")
                return False

            # Build graph
            print(f"  - Building graph...")
            result = subprocess.run(
                [sys.executable, "-m", "poligrapher.scripts.build_graph", str(disclosure_dir)],
                capture_output=True,
                text=True,
                timeout=120
            )
            if result.returncode != 0:
                print(f"  - Build graph failed: {result.stderr[:200]}")
                return False

            print(f"  - Success! Graph saved")
            return True

        except Exception as e:
            print(f"  - Error analyzing disclosure: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _extract_categories_from_graph(self, graph_path: Path) -> set:
        """Extract data categories from a PoliGraph YAML file."""
        from extension_privacy_analysis.data_categories import (
            DataCategory,
            get_category_for_datatype
        )

        categories = set()

        try:
            import yaml
            with open(graph_path, 'r', encoding='utf-8') as f:
                graph_data = yaml.safe_load(f)

            # Extract data types from nodes
            for node in graph_data.get('nodes', []):
                if node.get('type') == 'DATA':
                    datatype = node.get('id', '')
                    category = get_category_for_datatype(datatype)
                    if category:
                        categories.add(category)

            # Also check edges for collected data types
            for link in graph_data.get('links', []):
                if link.get('key') in ['COLLECT', 'USE', 'SHARE', 'STORE']:
                    target = link.get('target', '')
                    category = get_category_for_datatype(target)
                    if category:
                        categories.add(category)

        except Exception as e:
            print(f"  - Error extracting categories: {e}")

        return categories

    def analyze_all(self, skip_policy_crawl: bool = False) -> list:
        """
        Analyze all configured extensions.

        Returns:
            List of analysis results for all extensions
        """
        all_results = []

        for extension in EXTENSIONS:
            try:
                result = self.analyze_extension(extension, skip_policy_crawl)
                all_results.append(result)
            except Exception as e:
                print(f"Error analyzing {extension.name}: {e}")
                all_results.append({
                    "extension_name": extension.name,
                    "error": str(e)
                })

        return all_results

    def generate_report(self, results: list) -> str:
        """Generate a comparison report from analysis results."""
        return generate_comparison_table(results)


def main():
    parser = argparse.ArgumentParser(
        description="Extension Privacy Analysis Pipeline"
    )
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Analyze all configured extensions"
    )
    parser.add_argument(
        "--extension", "-e",
        type=str,
        help="Analyze a specific extension by name"
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List all configured extensions"
    )
    parser.add_argument(
        "--output-dir", "-o",
        type=str,
        default="extension_analysis_output",
        help="Output directory for analysis results"
    )
    parser.add_argument(
        "--skip-crawl",
        action="store_true",
        help="Skip crawling privacy policies (use existing data)"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        help="Anthropic API key (or set ANTHROPIC_API_KEY env var)"
    )

    args = parser.parse_args()

    if args.list:
        print("Configured Extensions:")
        print("-" * 40)
        for ext in EXTENSIONS:
            print(f"  - {ext.name} ({ext.extension_id})")
        return

    if not args.all and not args.extension:
        parser.print_help()
        return

    # Initialize pipeline
    pipeline = ExtensionPrivacyPipeline(
        output_dir=args.output_dir,
        anthropic_api_key=args.api_key
    )

    if args.extension:
        # Find the extension
        from extension_privacy_analysis.extensions_data import get_extension_by_name
        ext = get_extension_by_name(args.extension)
        if not ext:
            print(f"Extension '{args.extension}' not found. Use --list to see available extensions.")
            return

        results = [pipeline.analyze_extension(ext, skip_policy_crawl=args.skip_crawl)]

    elif args.all:
        results = pipeline.analyze_all(skip_policy_crawl=args.skip_crawl)

    # Generate and save report
    print("\n" + "=" * 60)
    print("GENERATING COMPARISON REPORT")
    print("=" * 60)

    # Save results
    results_path = Path(args.output_dir) / "results"
    results_path.mkdir(parents=True, exist_ok=True)

    # Convert sets to lists for JSON serialization
    json_results = []
    for r in results:
        jr = dict(r)
        if 'policy_categories' in jr:
            jr['policy_categories'] = [c.value for c in jr['policy_categories']]
        if 'disclosure_categories' in jr:
            jr['disclosure_categories'] = [c.value for c in jr['disclosure_categories']]
        if 'disclosure_raw_categories' in jr:
            jr['disclosure_raw_categories'] = [c.value for c in jr['disclosure_raw_categories']]
        json_results.append(jr)

    # Save JSON results
    json_path = results_path / "analysis_results.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_results, f, indent=2)
    print(f"Results saved to {json_path}")

    # Generate comparison table
    save_results_csv(results, results_path / "comparison_table.csv")
    save_results_html(results, results_path / "comparison_table.html")

    # Print summary table
    table = generate_comparison_table(results)
    print("\n" + table)


if __name__ == "__main__":
    main()
