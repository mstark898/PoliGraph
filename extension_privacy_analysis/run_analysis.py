#!/usr/bin/env python3
"""
Simple runner script for extension privacy analysis.

Prerequisites:
1. PoliGraph conda environment activated:
   conda activate poligraph

2. PoliGraph installed:
   pip install --editable .

3. Anthropic package installed:
   pip install anthropic

4. API key set (optional, for better disclosure preprocessing):
   export ANTHROPIC_API_KEY="your-key-here"

Usage:
   python extension_privacy_analysis/run_analysis.py
"""

import os
import sys
import subprocess
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def check_dependencies():
    """Check if required dependencies are available."""
    print("Checking dependencies...")

    # Check spaCy
    try:
        import spacy
        print(f"  ✓ spaCy {spacy.__version__}")
    except ImportError:
        print("  ✗ spaCy not installed")
        return False

    # Check if PoliGraph is installed
    try:
        import poligrapher
        print(f"  ✓ poligrapher installed")
    except ImportError:
        print("  ✗ poligrapher not installed (run: pip install --editable .)")
        return False

    # Check anthropic (optional)
    try:
        import anthropic
        print(f"  ✓ anthropic installed")
    except ImportError:
        print("  ⚠ anthropic not installed (optional - run: pip install anthropic)")

    # Check API key (optional)
    if os.environ.get("ANTHROPIC_API_KEY"):
        print("  ✓ ANTHROPIC_API_KEY set")
    else:
        print("  ⚠ ANTHROPIC_API_KEY not set (optional - will use rule-based preprocessing)")

    return True


def run_single_extension(extension_name: str):
    """Run analysis on a single extension."""
    from extension_privacy_analysis.run_pipeline import ExtensionPrivacyPipeline
    from extension_privacy_analysis.extensions_data import get_extension_by_name
    from extension_privacy_analysis.comparison_analysis import generate_comparison_table

    ext = get_extension_by_name(extension_name)
    if not ext:
        print(f"Extension '{extension_name}' not found")
        return None

    pipeline = ExtensionPrivacyPipeline(output_dir="extension_analysis_output")
    result = pipeline.analyze_extension(ext)

    return result


def run_all_extensions():
    """Run analysis on all configured extensions."""
    from extension_privacy_analysis.run_pipeline import ExtensionPrivacyPipeline
    from extension_privacy_analysis.extensions_data import EXTENSIONS
    from extension_privacy_analysis.comparison_analysis import (
        generate_comparison_table,
        save_results_csv,
        save_results_html
    )

    pipeline = ExtensionPrivacyPipeline(output_dir="extension_analysis_output")
    results = []

    for ext in EXTENSIONS:
        print(f"\n{'='*60}")
        print(f"Processing: {ext.name}")
        print(f"{'='*60}")

        try:
            result = pipeline.analyze_extension(ext)
            results.append(result)
        except Exception as e:
            print(f"Error: {e}")
            results.append({
                "extension_name": ext.name,
                "extension_id": ext.extension_id,
                "error": str(e),
                "policy_categories": set(),
                "disclosure_categories": set(),
            })

    # Save results
    results_dir = Path("extension_analysis_output/results")
    results_dir.mkdir(parents=True, exist_ok=True)

    save_results_csv(results, results_dir / "comparison_table.csv")
    save_results_html(results, results_dir / "comparison_table.html")

    # Print summary
    print("\n" + "="*60)
    print("FINAL RESULTS")
    print("="*60)
    print(generate_comparison_table(results))

    return results


if __name__ == "__main__":
    print("Extension Privacy Analysis Pipeline")
    print("="*60)

    if not check_dependencies():
        print("\nPlease install missing dependencies and try again.")
        sys.exit(1)

    print("\nStarting analysis...")
    print("This will analyze all 13 extensions.")
    print("Each extension takes 1-3 minutes to process.\n")

    results = run_all_extensions()

    print("\n" + "="*60)
    print("Analysis complete!")
    print("Results saved to: extension_analysis_output/results/")
    print("  - comparison_table.html (open in browser)")
    print("  - comparison_table.csv (open in Excel)")
