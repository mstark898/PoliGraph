"""
Extension Privacy Analysis Pipeline for PoliGraph

This package provides tools for analyzing discrepancies between Chrome extension
privacy policies and their Chrome Web Store developer disclosures.

Main components:
- extensions_data: Extension definitions and metadata
- data_categories: Mapping of data types to analysis categories
- disclosure_preprocessor: Claude API-based text transformation
- comparison_analysis: Comparison and tabulation tools
- run_pipeline: Main pipeline orchestration

Usage:
    # Run full analysis on all extensions
    python -m extension_privacy_analysis.run_pipeline --all

    # Analyze specific extension
    python -m extension_privacy_analysis.run_pipeline -e "Grammarly"

    # Quick disclosure-only analysis
    python -m extension_privacy_analysis.comparison_analysis
"""

from extension_privacy_analysis.extensions_data import EXTENSIONS, Extension
from extension_privacy_analysis.data_categories import DataCategory
from extension_privacy_analysis.comparison_analysis import (
    ComparisonResult,
    ComparisonAnalyzer,
    generate_comparison_table
)

__all__ = [
    'EXTENSIONS',
    'Extension',
    'DataCategory',
    'ComparisonResult',
    'ComparisonAnalyzer',
    'generate_comparison_table',
]
