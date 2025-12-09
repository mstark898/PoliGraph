"""
Comparison Analysis Module

Compares PoliGraph analysis results between privacy policies and developer disclosures,
generating tabular reports showing discrepancies.

Output format:
- Rows: Extensions
- Columns: Data categories (PII, Financial, Authentication, Location, Web History)
- Values:
  - "neither" - neither source mentions this data category
  - "disclosure_only" - only disclosure mentions it
  - "policy_only" - only privacy policy mentions it
  - "both" - both mention it
"""

import csv
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional

from extension_privacy_analysis.data_categories import (
    DataCategory,
    get_category_display_name,
    parse_chrome_disclosure_categories
)


class ComparisonResult(Enum):
    """Result of comparing a data category between policy and disclosure."""
    NEITHER = "neither"
    DISCLOSURE_ONLY = "disclosure_only"
    POLICY_ONLY = "policy_only"
    BOTH = "both"


@dataclass
class ExtensionComparison:
    """Comparison results for a single extension."""
    extension_name: str
    extension_id: str
    comparisons: dict  # DataCategory -> ComparisonResult
    policy_analyzed: bool = False
    disclosure_analyzed: bool = False
    notes: str = ""


class ComparisonAnalyzer:
    """
    Analyzes and compares privacy policies with developer disclosures.
    """

    def __init__(self):
        self.categories = list(DataCategory)

    def compare_extension(self, result: dict) -> ExtensionComparison:
        """
        Compare policy and disclosure for a single extension.

        Args:
            result: Analysis result dictionary from the pipeline

        Returns:
            ExtensionComparison with category-by-category comparison
        """
        extension_name = result.get("extension_name", "Unknown")
        extension_id = result.get("extension_id", "")

        policy_categories = result.get("policy_categories", set())
        disclosure_categories = result.get("disclosure_categories", set())

        # Also use raw disclosure categories if analyzed categories are empty
        if not disclosure_categories:
            disclosure_categories = result.get("disclosure_raw_categories", set())

        comparisons = {}

        for category in self.categories:
            in_policy = category in policy_categories
            in_disclosure = category in disclosure_categories

            if in_policy and in_disclosure:
                comparisons[category] = ComparisonResult.BOTH
            elif in_policy:
                comparisons[category] = ComparisonResult.POLICY_ONLY
            elif in_disclosure:
                comparisons[category] = ComparisonResult.DISCLOSURE_ONLY
            else:
                comparisons[category] = ComparisonResult.NEITHER

        notes = []
        if not result.get("policy_analyzed"):
            notes.append("Policy not analyzed")
        if not result.get("disclosure_analyzed"):
            notes.append("Disclosure not analyzed (using raw categories)")

        return ExtensionComparison(
            extension_name=extension_name,
            extension_id=extension_id,
            comparisons=comparisons,
            policy_analyzed=result.get("policy_analyzed", False),
            disclosure_analyzed=result.get("disclosure_analyzed", False),
            notes="; ".join(notes) if notes else ""
        )

    def compare_all(self, results: list) -> list:
        """Compare all extensions."""
        return [self.compare_extension(r) for r in results]


def generate_comparison_table(results: list, use_symbols: bool = False) -> str:
    """
    Generate a text-based comparison table.

    Args:
        results: List of analysis results from the pipeline
        use_symbols: If True, use symbols instead of text for values

    Returns:
        Formatted table string
    """
    analyzer = ComparisonAnalyzer()
    comparisons = analyzer.compare_all(results)

    # Define column widths
    name_width = max(len(c.extension_name) for c in comparisons) + 2
    cat_width = 18  # Width for each category column

    # Value display mapping
    if use_symbols:
        value_display = {
            ComparisonResult.NEITHER: "  -  ",
            ComparisonResult.DISCLOSURE_ONLY: "  D  ",
            ComparisonResult.POLICY_ONLY: "  P  ",
            ComparisonResult.BOTH: " D+P ",
        }
    else:
        value_display = {
            ComparisonResult.NEITHER: "neither",
            ComparisonResult.DISCLOSURE_ONLY: "disclosure_only",
            ComparisonResult.POLICY_ONLY: "policy_only",
            ComparisonResult.BOTH: "both",
        }

    # Build header
    categories = list(DataCategory)
    header_parts = [f"{'Extension':<{name_width}}"]
    for cat in categories:
        header_parts.append(f"{get_category_display_name(cat):^{cat_width}}")
    header = "|".join(header_parts)
    separator = "-" * len(header)

    # Build rows
    rows = [header, separator]
    for comp in comparisons:
        row_parts = [f"{comp.extension_name:<{name_width}}"]
        for cat in categories:
            result = comp.comparisons.get(cat, ComparisonResult.NEITHER)
            value = value_display[result]
            row_parts.append(f"{value:^{cat_width}}")
        rows.append("|".join(row_parts))

    # Add legend
    rows.append(separator)
    rows.append("\nLegend:")
    rows.append("  neither         = Neither policy nor disclosure mention this data category")
    rows.append("  disclosure_only = Only developer disclosure mentions it (potential under-disclosure in policy)")
    rows.append("  policy_only     = Only privacy policy mentions it (potential over-disclosure)")
    rows.append("  both            = Both sources mention this data category (consistent)")

    return "\n".join(rows)


def save_results_csv(results: list, output_path: Path):
    """
    Save comparison results to CSV file.

    Args:
        results: List of analysis results
        output_path: Path to save CSV file
    """
    analyzer = ComparisonAnalyzer()
    comparisons = analyzer.compare_all(results)
    categories = list(DataCategory)

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        # Header row
        header = ['Extension', 'Extension ID']
        for cat in categories:
            header.append(get_category_display_name(cat))
        header.extend(['Policy Analyzed', 'Disclosure Analyzed', 'Notes'])
        writer.writerow(header)

        # Data rows
        for comp in comparisons:
            row = [comp.extension_name, comp.extension_id]
            for cat in categories:
                result = comp.comparisons.get(cat, ComparisonResult.NEITHER)
                row.append(result.value)
            row.extend([
                'Yes' if comp.policy_analyzed else 'No',
                'Yes' if comp.disclosure_analyzed else 'No',
                comp.notes
            ])
            writer.writerow(row)

    print(f"CSV saved to {output_path}")


def save_results_html(results: list, output_path: Path):
    """
    Save comparison results to an HTML file with color-coded table.

    Args:
        results: List of analysis results
        output_path: Path to save HTML file
    """
    analyzer = ComparisonAnalyzer()
    comparisons = analyzer.compare_all(results)
    categories = list(DataCategory)

    # Color coding
    colors = {
        ComparisonResult.NEITHER: "#f0f0f0",  # Light gray
        ComparisonResult.DISCLOSURE_ONLY: "#ffcccc",  # Light red (potential issue)
        ComparisonResult.POLICY_ONLY: "#ffffcc",  # Light yellow (potential issue)
        ComparisonResult.BOTH: "#ccffcc",  # Light green (consistent)
    }

    html = """<!DOCTYPE html>
<html>
<head>
    <title>Extension Privacy Analysis Results</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #333; }
        table { border-collapse: collapse; width: 100%; margin-top: 20px; }
        th, td { border: 1px solid #ddd; padding: 12px; text-align: center; }
        th { background-color: #4CAF50; color: white; }
        tr:nth-child(even) { background-color: #f9f9f9; }
        .extension-name { text-align: left; font-weight: bold; }
        .legend { margin-top: 20px; padding: 15px; background-color: #f5f5f5; border-radius: 5px; }
        .legend-item { margin: 5px 0; display: flex; align-items: center; }
        .legend-color { width: 20px; height: 20px; margin-right: 10px; border: 1px solid #ccc; }
        .neither { background-color: #f0f0f0; }
        .disclosure_only { background-color: #ffcccc; }
        .policy_only { background-color: #ffffcc; }
        .both { background-color: #ccffcc; }
    </style>
</head>
<body>
    <h1>Extension Privacy Analysis: Policy vs Disclosure Comparison</h1>
    <p>This table compares what data categories are mentioned in privacy policies vs Chrome Web Store developer disclosures.</p>

    <table>
        <tr>
            <th>Extension</th>
"""

    # Add category headers
    for cat in categories:
        html += f"            <th>{get_category_display_name(cat)}</th>\n"
    html += "        </tr>\n"

    # Add data rows
    for comp in comparisons:
        html += "        <tr>\n"
        html += f'            <td class="extension-name">{comp.extension_name}</td>\n'

        for cat in categories:
            result = comp.comparisons.get(cat, ComparisonResult.NEITHER)
            color = colors[result]
            display = result.value.replace('_', ' ')
            html += f'            <td style="background-color: {color}">{display}</td>\n'

        html += "        </tr>\n"

    html += """    </table>

    <div class="legend">
        <h3>Legend</h3>
        <div class="legend-item">
            <div class="legend-color neither"></div>
            <span><strong>neither</strong> - Neither privacy policy nor disclosure mention this data category</span>
        </div>
        <div class="legend-item">
            <div class="legend-color disclosure_only"></div>
            <span><strong>disclosure only</strong> - Only developer disclosure mentions it (potential under-disclosure in policy)</span>
        </div>
        <div class="legend-item">
            <div class="legend-color policy_only"></div>
            <span><strong>policy only</strong> - Only privacy policy mentions it (potential over-disclosure in store listing)</span>
        </div>
        <div class="legend-item">
            <div class="legend-color both"></div>
            <span><strong>both</strong> - Both sources mention this data category (consistent)</span>
        </div>
    </div>

    <div style="margin-top: 20px; color: #666;">
        <p><em>Generated by PoliGraph Extension Privacy Analysis Pipeline</em></p>
    </div>
</body>
</html>
"""

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"HTML report saved to {output_path}")


def quick_disclosure_analysis(extensions_data: list) -> str:
    """
    Quickly analyze just the developer disclosures (without running full PoliGraph pipeline).

    This is useful for a quick overview based only on the raw disclosure text.

    Args:
        extensions_data: List of Extension objects

    Returns:
        Formatted table string
    """
    results = []

    for ext in extensions_data:
        categories = parse_chrome_disclosure_categories(ext.developer_disclosure)
        results.append({
            "extension_name": ext.name,
            "extension_id": ext.extension_id,
            "disclosure_raw_categories": categories,
            "policy_categories": set(),  # Empty - we're only looking at disclosures
            "policy_analyzed": False,
            "disclosure_analyzed": False
        })

    return generate_comparison_table(results)


if __name__ == "__main__":
    # Quick test with disclosure-only analysis
    from extension_privacy_analysis.extensions_data import EXTENSIONS

    print("Quick Disclosure Analysis (Raw Categories Only)")
    print("=" * 80)
    print()
    print(quick_disclosure_analysis(EXTENSIONS))
