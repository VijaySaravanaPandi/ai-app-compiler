"""
Run Evaluation Script
=====================
Command line interface to run evaluation metrics on the compiler pipeline.
Supports both mock (simulation) mode and real LLM mode.

Usage:
    python scripts/run_eval.py --mode mock
    python scripts/run_eval.py --mode real
"""
import sys
import json
import argparse
from pathlib import Path

# Add backend folder to python path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.eval.runner import EvaluationRunner

def main():
    parser = argparse.ArgumentParser(description="AI App Compiler Evaluation Suite")
    parser.add_argument(
        "--mode",
        choices=["real", "mock"],
        default="mock",
        help="Run mode. 'mock' simulates pipeline runs, 'real' uses Groq API (needs GROQ_API_KEY)"
    )
    parser.add_argument(
        "--output-json",
        default="evaluation_results.json",
        help="Filename to save raw JSON results"
    )
    parser.add_argument(
        "--output-md",
        default="EVAL_REPORT.md",
        help="Filename to save the markdown report"
    )

    args = parser.parse_args()

    # Initialize runner
    runner = EvaluationRunner(mode=args.mode)
    
    # Run all evaluation prompts
    summary = runner.run_all()

    # Generate files
    workspace_root = Path(__file__).resolve().parent.parent.parent
    
    json_path = workspace_root / args.output_json
    with open(json_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"[OK] Raw JSON results saved to: {json_path.resolve()}")

    md_report = runner.generate_markdown_report(summary)
    md_path = workspace_root / args.output_md
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_report)
    print(f"[OK] Markdown report saved to: {md_path.resolve()}")

    # Print summary metrics to console
    print("\n" + "=" * 40)
    print("         EVALUATION RUN COMPLETED")
    print("=" * 40)
    m = summary["metrics"]
    print(f"Success Rate:      {m['success_rate']}%")
    print(f"Clarification Rate: {m['clarification_rate']}%")
    print(f"Failure Rate:       {m['failure_rate']}%")
    print(f"Avg Latency:        {m['avg_latency_ms']} ms")
    print(f"Total Repair Loops: {m['total_repair_loops']}")
    print(f"Total Cost:         ${m['total_cost_usd']:.4f}")
    print("=" * 40)

if __name__ == "__main__":
    main()
