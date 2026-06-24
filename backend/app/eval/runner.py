import time
import json
import random
from pathlib import Path
from typing import Dict, List, Any, Optional

from app.pipeline.orchestrator import orchestrator
from app.eval.prompts import REAL_PROMPTS, EDGE_CASE_PROMPTS
from app.schemas.pipeline_state import PipelineState

# Cost configuration (Groq Llama-3.3-70b rates per 1M tokens)
# Input: $0.59 / 1M tokens, Output: $0.79 / 1M tokens
INPUT_TOKEN_COST_PER_M = 0.59
OUTPUT_TOKEN_COST_PER_M = 0.79

class EvaluationRunner:
    def __init__(self, mode: str = "mock"):
        """
        Initialize the runner.
        mode: "real" (actually calls LLM pipeline) or "mock" (simulates pipeline responses)
        """
        self.mode = mode.lower()
        if self.mode not in ["real", "mock"]:
            raise ValueError("Mode must be 'real' or 'mock'")

    def run_single(self, prompt_id: str, prompt_text: str, category: str) -> Dict[str, Any]:
        """Run evaluation for a single prompt."""
        print(f"[{self.mode.upper()}] Evaluating '{prompt_id}' ({category})...")
        start_time = time.time()
        
        if self.mode == "real":
            try:
                state = orchestrator.start(prompt_text)
                latency_ms = int((time.time() - start_time) * 1000)
                
                # Estimate cost (rough tokens: 1 token ~ 4 chars)
                input_tokens = len(prompt_text) // 4 + 4000  # prompt + system instructions
                # Output tokens estimate from generated schemas
                output_tokens = 0
                if state.intent: output_tokens += len(state.intent.model_dump_json()) // 4
                if state.architecture: output_tokens += len(state.architecture.model_dump_json()) // 4
                if state.ui: output_tokens += len(state.ui.model_dump_json()) // 4
                if state.api: output_tokens += len(state.api.model_dump_json()) // 4
                if state.db: output_tokens += len(state.db.model_dump_json()) // 4
                if state.auth: output_tokens += len(state.auth.model_dump_json()) // 4
                if state.business_logic: output_tokens += len(state.business_logic.model_dump_json()) // 4
                
                cost_usd = (input_tokens / 1e6 * INPUT_TOKEN_COST_PER_M) + (output_tokens / 1e6 * OUTPUT_TOKEN_COST_PER_M)
                
                if state.needs_clarification:
                    status = "needs_clarification"
                    failure_type = "vague_clarification"
                elif state.status == "failed":
                    status = "failed"
                    failure_type = "validation_unrepairable"
                else:
                    status = "success"
                    failure_type = "none"

                return {
                    "prompt_id": prompt_id,
                    "category": category,
                    "prompt": prompt_text,
                    "status": status,
                    "latency_ms": latency_ms,
                    "repair_attempts": len(state.repair_log),
                    "validation_issues": len(state.validation_issues),
                    "failure_type": failure_type,
                    "cost_usd": round(cost_usd, 6),
                    "needs_clarification": state.needs_clarification,
                    "clarification_questions": state.clarification_questions,
                }
            except Exception as e:
                latency_ms = int((time.time() - start_time) * 1000)
                return {
                    "prompt_id": prompt_id,
                    "category": category,
                    "prompt": prompt_text,
                    "status": "failed",
                    "latency_ms": latency_ms,
                    "repair_attempts": 0,
                    "validation_issues": 1,
                    "failure_type": "api_error",
                    "cost_usd": 0.0,
                    "needs_clarification": False,
                    "clarification_questions": [str(e)],
                }
        else:
            # ── Mock Simulation Mode ──────────────────────────────────────────
            # Emulates pipeline output characteristics for testing & validation
            time.sleep(random.uniform(0.5, 1.5))  # mock delay
            latency_ms = int((time.time() - start_time) * 1000)
            
            if category == "real":
                # Real prompts mostly succeed, some require repairs
                needs_repair = random.random() < 0.25
                repair_attempts = random.choice([1, 2]) if needs_repair else 0
                latency_ms = latency_ms + (repair_attempts * 1200)
                cost_usd = 0.015 + (repair_attempts * 0.005)
                
                return {
                    "prompt_id": prompt_id,
                    "category": category,
                    "prompt": prompt_text,
                    "status": "success",
                    "latency_ms": latency_ms,
                    "repair_attempts": repair_attempts,
                    "validation_issues": 0,
                    "failure_type": "none",
                    "cost_usd": round(cost_usd, 4),
                    "needs_clarification": False,
                    "clarification_questions": [],
                }
            else:
                # Edge cases
                # Find if vague, conflict, or incomplete
                if "vague" in prompt_id:
                    # Vague prompts trigger clarification engine instantly
                    return {
                        "prompt_id": prompt_id,
                        "category": category,
                        "prompt": prompt_text,
                        "status": "needs_clarification",
                        "latency_ms": int(random.uniform(50, 150)),
                        "repair_attempts": 0,
                        "validation_issues": 0,
                        "failure_type": "vague_clarification",
                        "cost_usd": 0.0005,
                        "needs_clarification": True,
                        "clarification_questions": ["Can you specify the core business entity?", "What user roles should access this page?"],
                    }
                elif "conflict" in prompt_id:
                    # Conflicting prompts run but fail validation (repair engine cannot resolve contradictions)
                    repair_attempts = random.choice([2, 3])
                    latency_ms = latency_ms + (repair_attempts * 1500)
                    cost_usd = 0.02 + (repair_attempts * 0.006)
                    return {
                        "prompt_id": prompt_id,
                        "category": category,
                        "prompt": prompt_text,
                        "status": "failed",
                        "latency_ms": latency_ms,
                        "repair_attempts": repair_attempts,
                        "validation_issues": random.randint(1, 3),
                        "failure_type": "logical_conflict",
                        "cost_usd": round(cost_usd, 4),
                        "needs_clarification": False,
                        "clarification_questions": [],
                    }
                else:
                    # Incomplete prompts can either request clarification (50%) or make assumptions (50%)
                    is_vague = random.random() < 0.5
                    if is_vague:
                        return {
                            "prompt_id": prompt_id,
                            "category": category,
                            "prompt": prompt_text,
                            "status": "needs_clarification",
                            "latency_ms": int(random.uniform(100, 300)),
                            "repair_attempts": 0,
                            "validation_issues": 0,
                            "failure_type": "incomplete_clarification",
                            "cost_usd": 0.001,
                            "needs_clarification": True,
                            "clarification_questions": ["Which payment gateways should be configured?", "Describe the layout of the check-in screen."],
                        }
                    else:
                        repair_attempts = random.choice([0, 1])
                        latency_ms = latency_ms + (repair_attempts * 1000)
                        cost_usd = 0.012 + (repair_attempts * 0.004)
                        return {
                            "prompt_id": prompt_id,
                            "category": category,
                            "prompt": prompt_text,
                            "status": "success",
                            "latency_ms": latency_ms,
                            "repair_attempts": repair_attempts,
                            "validation_issues": 0,
                            "failure_type": "none",
                            "cost_usd": round(cost_usd, 4),
                            "needs_clarification": False,
                            "clarification_questions": [],
                        }

    def run_all(self) -> Dict[str, Any]:
        """Run evaluation on the entire dataset (10 real + 10 edge cases)."""
        results = []
        
        print("\n=== STARTING COMPILER EVALUATION SYSTEM ===")
        print(f"Mode: {self.mode.upper()}\n")

        # Run real prompts
        for p in REAL_PROMPTS:
            res = self.run_single(p["id"], p["prompt"], "real")
            results.append(res)

        # Run edge cases
        for p in EDGE_CASE_PROMPTS:
            res = self.run_single(p["id"], p["prompt"], p["type"])
            results.append(res)

        # Compute aggregate metrics
        total = len(results)
        real_results = [r for r in results if r["category"] == "real"]
        edge_results = [r for r in results if r["category"] != "real"]

        successes = [r for r in results if r["status"] == "success"]
        clarifications = [r for r in results if r["status"] == "needs_clarification"]
        failures = [r for r in results if r["status"] == "failed"]

        avg_latency = sum(r["latency_ms"] for r in results) / total
        avg_latency_real = sum(r["latency_ms"] for r in real_results) / len(real_results)
        
        total_repairs = sum(r["repair_attempts"] for r in results)
        avg_repairs_real = sum(r["repair_attempts"] for r in real_results) / len(real_results)

        total_cost = sum(r["cost_usd"] for r in results)

        # Breakdown of failure types
        failure_types: Dict[str, int] = {}
        for r in results:
            ft = r["failure_type"]
            failure_types[ft] = failure_types.get(ft, 0) + 1

        summary = {
            "metadata": {
                "mode": self.mode,
                "timestamp": time.asctime(),
                "total_prompts": total,
            },
            "metrics": {
                "success_rate": round(len(successes) / total * 100, 2),
                "clarification_rate": round(len(clarifications) / total * 100, 2),
                "failure_rate": round(len(failures) / total * 100, 2),
                "avg_latency_ms": round(avg_latency, 2),
                "avg_latency_real_ms": round(avg_latency_real, 2),
                "total_repair_loops": total_repairs,
                "avg_repairs_real": round(avg_repairs_real, 2),
                "total_cost_usd": round(total_cost, 4),
                "avg_cost_per_prompt_usd": round(total_cost / total, 4)
            },
            "failure_breakdown": failure_types,
            "results": results
        }
        
        return summary

    def generate_markdown_report(self, summary: Dict[str, Any]) -> str:
        """Create a beautiful markdown report of the evaluation run."""
        m = summary["metrics"]
        metadata = summary["metadata"]
        
        report = f"""# AI App Compiler — Evaluation & Metrics Report

This report summarizes the performance metrics of the AI App Compiler pipeline running in **{metadata['mode'].upper()}** mode. 
The test suite consists of **10 real-world product prompts** and **10 edge cases** (vague, conflicting, incomplete).

## Core Metrics Summary

| Metric | Value | Notes |
|:---|:---|:---|
| **Pipeline Mode** | `{metadata['mode'].upper()}` | Execution mode |
| **Total Test Dataset** | {metadata['total_prompts']} prompts | 10 Real + 10 Edge cases |
| **Compilation Success Rate** | `{m['success_rate']}%` | Code generated & runnable |
| **Clarification Rate** | `{m['clarification_rate']}%` | Handled ambiguous requests gracefully |
| **Pipeline Failure Rate** | `{m['failure_rate']}%` | Fatal schema errors / conflicts |
| **Average Latency (All)** | `{m['avg_latency_ms']} ms` | Across the full dataset |
| **Average Latency (Real Apps)** | `{m['avg_latency_real_ms']} ms` | Excludes instant vague detection |
| **Total Cost** | `${m['total_cost_usd']}` | Estimated LLM token cost |
| **Avg Cost / Prompt** | `${m['avg_cost_per_prompt_usd']}` | Average generation cost |
| **Total Repair Loops Run** | `{m['total_repair_loops']}` | Self-repair triggers |
| **Avg Repairs (Real Apps)** | `{m['avg_repairs_real']}` | Self-repair attempts per real app |

## Failure Breakdown

| Failure Type | Count | Description |
|:---|:---|:---|
| `none` | {summary['failure_breakdown'].get('none', 0)} | Successful execution |
| `vague_clarification` | {summary['failure_breakdown'].get('vague_clarification', 0)} | Gracefully paused to request details on vague input |
| `incomplete_clarification` | {summary['failure_breakdown'].get('incomplete_clarification', 0)} | Paused for missing details |
| `logical_conflict` | {summary['failure_breakdown'].get('logical_conflict', 0)} | Rejected conflicting schemas after repair attempts |
| `validation_unrepairable` | {summary['failure_breakdown'].get('validation_unrepairable', 0)} | Core structure could not be automatically repaired |
| `api_error` | {summary['failure_breakdown'].get('api_error', 0)} | Network, model rate-limit, or token limits |

## Detailed Prompt Results Table

| Prompt ID | Category | Status | Latency | Repairs | Cost | Failure Mode |
|:---|:---|:---|:---|:---|:---|:---|
"""
        for r in summary["results"]:
            status_emoji = "✅" if r["status"] == "success" else "⚠️" if r["status"] == "needs_clarification" else "❌"
            report += f"| `{r['prompt_id']}` | {r['category']} | {status_emoji} `{r['status']}` | {r['latency_ms']} ms | {r['repair_attempts']} | ${r['cost_usd']:.4f} | `{r['failure_type']}` |\n"
            
        return report
