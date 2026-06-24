# AI App Compiler — Evaluation & Metrics Report

This report summarizes the performance metrics of the AI App Compiler pipeline running in **MOCK** mode. 
The test suite consists of **10 real-world product prompts** and **10 edge cases** (vague, conflicting, incomplete).

## Core Metrics Summary

| Metric | Value | Notes |
|:---|:---|:---|
| **Pipeline Mode** | `MOCK` | Execution mode |
| **Total Test Dataset** | 20 prompts | 10 Real + 10 Edge cases |
| **Compilation Success Rate** | `50.0%` | Code generated & runnable |
| **Clarification Rate** | `35.0%` | Handled ambiguous requests gracefully |
| **Pipeline Failure Rate** | `15.0%` | Fatal schema errors / conflicts |
| **Average Latency (All)** | `1572.0 ms` | Across the full dataset |
| **Average Latency (Real Apps)** | `1414.8 ms` | Excludes instant vague detection |
| **Total Cost** | `$0.289` | Estimated LLM token cost |
| **Avg Cost / Prompt** | `$0.0144` | Average generation cost |
| **Total Repair Loops Run** | `13` | Self-repair triggers |
| **Avg Repairs (Real Apps)** | `0.4` | Self-repair attempts per real app |

## Failure Breakdown

| Failure Type | Count | Description |
|:---|:---|:---|
| `none` | 10 | Successful execution |
| `vague_clarification` | 4 | Gracefully paused to request details on vague input |
| `incomplete_clarification` | 3 | Paused for missing details |
| `logical_conflict` | 3 | Rejected conflicting schemas after repair attempts |
| `validation_unrepairable` | 0 | Core structure could not be automatically repaired |
| `api_error` | 0 | Network, model rate-limit, or token limits |

## Detailed Prompt Results Table

| Prompt ID | Category | Status | Latency | Repairs | Cost | Failure Mode |
|:---|:---|:---|:---|:---|:---|:---|
| `real-crm` | real | ✅ `success` | 603 ms | 0 | $0.0150 | `none` |
| `real-blog` | real | ✅ `success` | 2433 ms | 1 | $0.0200 | `none` |
| `real-ecommerce` | real | ✅ `success` | 1046 ms | 0 | $0.0150 | `none` |
| `real-booking` | real | ✅ `success` | 3293 ms | 2 | $0.0250 | `none` |
| `real-lms` | real | ✅ `success` | 1219 ms | 0 | $0.0150 | `none` |
| `real-helpdesk` | real | ✅ `success` | 1880 ms | 1 | $0.0200 | `none` |
| `real-fitness` | real | ✅ `success` | 990 ms | 0 | $0.0150 | `none` |
| `real-inventory` | real | ✅ `success` | 1088 ms | 0 | $0.0150 | `none` |
| `real-expense` | real | ✅ `success` | 805 ms | 0 | $0.0150 | `none` |
| `real-realestate` | real | ✅ `success` | 791 ms | 0 | $0.0150 | `none` |
| `edge-vague-1` | vague | ⚠️ `needs_clarification` | 98 ms | 0 | $0.0005 | `vague_clarification` |
| `edge-vague-2` | vague | ⚠️ `needs_clarification` | 132 ms | 0 | $0.0005 | `vague_clarification` |
| `edge-vague-3` | vague | ⚠️ `needs_clarification` | 64 ms | 0 | $0.0005 | `vague_clarification` |
| `edge-vague-4` | vague | ⚠️ `needs_clarification` | 67 ms | 0 | $0.0005 | `vague_clarification` |
| `edge-conflict-1` | conflict | ❌ `failed` | 5150 ms | 3 | $0.0380 | `logical_conflict` |
| `edge-conflict-2` | conflict | ❌ `failed` | 5487 ms | 3 | $0.0380 | `logical_conflict` |
| `edge-conflict-3` | conflict | ❌ `failed` | 5726 ms | 3 | $0.0380 | `logical_conflict` |
| `edge-incomplete-1` | incomplete | ⚠️ `needs_clarification` | 280 ms | 0 | $0.0010 | `incomplete_clarification` |
| `edge-incomplete-2` | incomplete | ⚠️ `needs_clarification` | 124 ms | 0 | $0.0010 | `incomplete_clarification` |
| `edge-incomplete-3` | incomplete | ⚠️ `needs_clarification` | 164 ms | 0 | $0.0010 | `incomplete_clarification` |
