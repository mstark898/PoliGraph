# Extension Privacy Analysis Pipeline

This pipeline compares Chrome extension **privacy policies** with their **Chrome Web Store developer disclosures** to identify discrepancies in what data they claim to collect.

## Quick Start

### 1. Set up PoliGraph environment

```bash
# From the PoliGraph root directory
conda activate poligraph

# Make sure PoliGraph is installed
pip install --editable .

# Install anthropic for better disclosure preprocessing (optional)
pip install anthropic
```

### 2. Set your API key (optional but recommended)

```bash
export ANTHROPIC_API_KEY="your-key-here"
```

Without the API key, the pipeline will use rule-based preprocessing (still works, but less accurate).

### 3. Run the analysis

```bash
# From the PoliGraph root directory
python extension_privacy_analysis/run_analysis.py
```

Or use the module directly:

```bash
# Analyze all extensions
python -m extension_privacy_analysis.run_pipeline --all

# Analyze a specific extension
python -m extension_privacy_analysis.run_pipeline -e "Grammarly"

# List available extensions
python -m extension_privacy_analysis.run_pipeline --list
```

### 4. View results

Results are saved to `extension_analysis_output/results/`:

- `comparison_table.html` - Color-coded table (open in browser)
- `comparison_table.csv` - Spreadsheet format
- `analysis_results.json` - Raw JSON data

## Understanding the Results

The comparison table shows 5 data categories:

| Category | Description |
|----------|-------------|
| **PII** | Personally identifiable information (name, email, etc.) |
| **Financial** | Payment and financial data (credit cards, transactions) |
| **Authentication** | Passwords, credentials, security questions |
| **Location** | GPS, IP address, geographic data |
| **Web History** | Browsing history, cookies, user activity |

Each cell shows one of 4 values:

| Value | Meaning |
|-------|---------|
| `neither` | Neither source mentions this data category |
| `disclosure_only` | Only the Chrome Web Store disclosure mentions it |
| `policy_only` | Only the privacy policy mentions it |
| `both` | Both sources mention it (consistent) |

## Extensions Analyzed

1. PayPal Honey
2. Capital One Shopping
3. Keepa
4. Coupert
5. Rakuten
6. The Camelizer
7. CouponBirds
8. Shein Coupon Finder
9. Cently
10. AliExpress Coupon Finder
11. Grammarly
12. AdBlock
13. Hola VPN

## Adding New Extensions

Edit `extension_privacy_analysis/extensions_data.py` to add new extensions:

```python
Extension(
    name="Extension Name",
    extension_id="chrome-extension-id",
    privacy_policy_url="https://example.com/privacy",
    developer_disclosure="""..."""  # Copy from Chrome Web Store
)
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'spacy'"
Make sure you activated the conda environment: `conda activate poligraph`

### "Crawl failed" errors
Some privacy policy URLs may be inaccessible or have changed. Check the URL manually and update `extensions_data.py` if needed.

### Slow processing
Each extension takes 1-3 minutes due to NLP processing. The full pipeline for 13 extensions takes ~20-30 minutes.
