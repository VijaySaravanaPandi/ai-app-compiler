# AI App Compiler — Evaluation & Metrics Report

This report summarizes the performance metrics of the AI App Compiler pipeline running in **MOCK** mode. 
The test suite consists of **10 real-world product prompts** and **10 edge cases** (vague, conflicting, incomplete).

## Core Metrics Summary

| Metric | Value | Notes |
|:---|:---|:---|
| **Pipeline Mode** | `MOCK` | Execution mode |
| **Total Test Dataset** | 20 prompts | 10 Real + 10 Edge cases |
| **Compilation Success Rate** | `60.0%` | Code generated & runnable |
| **Clarification Rate** | `25.0%` | Handled ambiguous requests gracefully |
| **Pipeline Failure Rate** | `15.0%` | Fatal schema errors / conflicts |
| **Average Latency (All)** | `1227.0 ms` | Across the full dataset |
| **Average Latency (Real Apps)** | `896.2 ms` | Excludes instant vague detection |
| **Total Cost** | `$0.277` | Estimated LLM token cost |
| **Avg Cost / Prompt** | `$0.0139` | Average generation cost |
| **Total Repair Loops Run** | `7` | Self-repair triggers |
| **Avg Repairs (Real Apps)** | `0.0` | Self-repair attempts per real app |

## Failure Breakdown

| Failure Type | Count | Description |
|:---|:---|:---|
| `none` | 12 | Successful execution |
| `vague_clarification` | 4 | Gracefully paused to request details on vague input |
| `incomplete_clarification` | 1 | Paused for missing details |
| `logical_conflict` | 3 | Rejected conflicting schemas after repair attempts |
| `validation_unrepairable` | 0 | Core structure could not be automatically repaired |
| `api_error` | 0 | Network, model rate-limit, or token limits |

## Detailed Prompt Results Table

| Prompt ID | Category | Status | Latency | Repairs | Cost | Failure Mode |
|:---|:---|:---|:---|:---|:---|:---|
| `real-crm` | real | ✅ `success` | 1005 ms | 0 | $0.0150 | `none` |
| `real-blog` | real | ✅ `success` | 710 ms | 0 | $0.0150 | `none` |
| `real-ecommerce` | real | ✅ `success` | 742 ms | 0 | $0.0150 | `none` |
| `real-booking` | real | ✅ `success` | 1304 ms | 0 | $0.0150 | `none` |
| `real-lms` | real | ✅ `success` | 1028 ms | 0 | $0.0150 | `none` |
| `real-helpdesk` | real | ✅ `success` | 501 ms | 0 | $0.0150 | `none` |
| `real-fitness` | real | ✅ `success` | 1145 ms | 0 | $0.0150 | `none` |
| `real-inventory` | real | ✅ `success` | 1166 ms | 0 | $0.0150 | `none` |
| `real-expense` | real | ✅ `success` | 802 ms | 0 | $0.0150 | `none` |
| `real-realestate` | real | ✅ `success` | 559 ms | 0 | $0.0150 | `none` |
| `edge-vague-1` | vague | ⚠️ `needs_clarification` | 94 ms | 0 | $0.0005 | `vague_clarification` |
| `edge-vague-2` | vague | ⚠️ `needs_clarification` | 113 ms | 0 | $0.0005 | `vague_clarification` |
| `edge-vague-3` | vague | ⚠️ `needs_clarification` | 113 ms | 0 | $0.0005 | `vague_clarification` |
| `edge-vague-4` | vague | ⚠️ `needs_clarification` | 68 ms | 0 | $0.0005 | `vague_clarification` |
| `edge-conflict-1` | conflict | ❌ `failed` | 3900 ms | 2 | $0.0320 | `logical_conflict` |
| `edge-conflict-2` | conflict | ❌ `failed` | 4303 ms | 2 | $0.0320 | `logical_conflict` |
| `edge-conflict-3` | conflict | ❌ `failed` | 3823 ms | 2 | $0.0320 | `logical_conflict` |
| `edge-incomplete-1` | incomplete | ✅ `success` | 1383 ms | 0 | $0.0120 | `none` |
| `edge-incomplete-2` | incomplete | ✅ `success` | 1590 ms | 1 | $0.0160 | `none` |
| `edge-incomplete-3` | incomplete | ⚠️ `needs_clarification` | 191 ms | 0 | $0.0010 | `incomplete_clarification` |
