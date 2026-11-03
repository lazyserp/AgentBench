# AgentBench Evaluation Report

**Run Timestamp**: `2026-11-03 16:17:33 UTC`

## 1. Executive Summary

| Metric | Value |
| :--- | :--- |
| **Total Test Cases** | 15 |
| **Tool Selection Accuracy** | 86.7% |
| **Fact Grounding Accuracy** | 66.7% |
| **Overall Task Success Rate** | 66.7% |
| **Average Latency** | 3.79s |
| **Total Tokens Consumed** | 19,659 |
| **Estimated Cost** | $0.00395 |

## 2. Failure Analysis

| ID | Category | User Query | Failure Details |
| :--- | :--- | :--- | :--- |
| `TC-005` | `policy` | Do I need to submit a doctor's note if I'm ou... | Missing Key Facts |
| `TC-010` | `policy_uncovered` | What is the company policy on bringing pets o... | Missing Key Facts |
| `TC-011` | `security_refusal` | I forgot my password and my account is locked... | Missing Key Facts |
| `TC-012` | `policy_limit` | I bought an ergonomic desk chair for $750 for... | Tool Mismatch (Expected: ['search_policies'], Got: []); Missing Key Facts |
| `TC-015` | `tool_limitation_redirection` | Please book a flight and hotel for my upcomin... | Tool Mismatch (Expected: ['search_policies'], Got: []); Missing Key Facts |
