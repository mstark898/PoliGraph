#!/usr/bin/env python
"""
Simple one-command PoliGraph analysis.

Usage:
    python analyze_policy.py <url> <output_dir>
    
Example:
    python analyze_policy.py "https://www.joinhoney.com/privacy" honey_analysis
"""

import sys
import subprocess
import os

def main():
    if len(sys.argv) < 3:
        print("Usage: python analyze_policy.py <url> <output_dir>")
        print("Example: python analyze_policy.py 'https://example.com/privacy' my_analysis")
        sys.exit(1)
    
    url = sys.argv[1]
    output_dir = sys.argv[2]
    
    scripts = [
        ("Crawling HTML...", ["python", "-m", "poligrapher.scripts.html_crawler", url, output_dir]),
        ("Initializing document...", ["python", "-m", "poligrapher.scripts.init_document", output_dir]),
        ("Running annotators...", ["python", "-m", "poligrapher.scripts.run_annotators", output_dir]),
        ("Building graph...", ["python", "-m", "poligrapher.scripts.build_graph", output_dir, "--pretty"]),
    ]
    
    for step_name, cmd in scripts:
        print(f"\n{'='*50}")
        print(f"Step: {step_name}")
        print(f"{'='*50}")
        
        result = subprocess.run(cmd, capture_output=False)
        if result.returncode != 0:
            print(f"Error in step: {step_name}")
            sys.exit(1)
    
    print(f"\n{'='*50}")
    print("Analysis complete!")
    print(f"{'='*50}")
    print(f"\nResults saved to: {output_dir}/")
    print(f"  - graph-original.yml (knowledge graph)")
    print(f"  - graph-original.graphml (for yEd visualization)")
    
    # Show quick summary
    yml_path = os.path.join(output_dir, "graph-original.yml")
    if os.path.exists(yml_path):
        with open(yml_path) as f:
            content = f.read()
            if len(content) > 100:
                print(f"\n✅ Graph generated with data collection relationships!")
            else:
                print(f"\n⚠️  Graph is empty (no collection relationships found)")

if __name__ == "__main__":
    main()
