---
title: SecureCodeOpsEnv
emoji: 🛡️
colorFrom: blue
colorTo: green
sdk: docker
pinned: true
tags:
  - openenv
  - devsecops
  - code-review
  - security
  - reinforcement-learning
  - agent-evaluation
---

# SecureCodeOpsEnv 🛡️
### AI DevSecOps Debugging & Security Audit Environment

> An OpenEnv environment that simulates real-world DevSecOps investigation — from reading logs to proposing production-ready fixes — across 3 difficulty tiers with trajectory-aware grading.

---

## 🎯 Why This Exists

Code review and security auditing are high-leverage tasks, yet most benchmarks are static and provide only pass/fail signals. SecureCodeOpsEnv introduces interactive trajectories, partial rewards, and realistic artifacts (logs, stack traces, multi-file code).

---

## 🏗️ Environment Design

### Observation Space
| Field | Type | Description |
|---|---|---|
| task_id | string | Current task identifier |
| step_count | int | Steps taken in episode |
| code_snippet | string | Code to review (easy/medium) |
| logs | string | System error logs (hard) |
| stack_trace | string | Error stack trace (hard) |
| available_files | list | Files agent can request (hard) |
| revealed_files | dict | Files already revealed |
| current_phase | enum | INIT / CONTEXT_FETCH / ROOT_CAUSE / FINAL |

### Action Space
| Field | Type | Description |
|---|---|---|
| action_type | enum | IDENTIFY_ISSUE, REQUEST_FILE, NARROW_DOWN, PROPOSE_FIX, ASK_QUESTION, FORM_HYPOTHESIS |
| line_numbers | list[int] | Flagged line numbers |
| issue_type | enum | BUG, SECURITY, PERFORMANCE, LOGIC, RACE_CONDITION |
| severity | enum | LOW, MEDIUM, HIGH, CRITICAL |
| suggested_fix | string | Proposed fix |
| explanation | string | Agent's reasoning |
| confidence | float | 0.0–1.0 |
| file_name | string | File requested (hard task) |

---

## 🧭 Tasks

### 🟢 Task 1 — `spot_the_bug` (Easy)
- Input: Single Python function with a real bug (BugsInPy-style).
- Agent must: Identify buggy lines + propose fix in one step.
- Expected frontier model score: ~0.75

### 🟡 Task 2 — `security_audit` (Medium)
- Input: Web application code with hidden vulnerability (CWE-89, CWE-798, CWE-22 patterns).
- Agent must: Classify vulnerability + identify lines + fix.
- Expected frontier model score: ~0.45

### 🔴 Task 3 — `system_debug` (Hard)
- Input: Multi-file project with logs + stack trace.
- Agent must: Multi-turn investigation across 4 phases.
- Expected frontier model score: ~0.35

Hard task state machine:
```
INIT → CONTEXT_FETCH → ROOT_CAUSE → FINAL
```

---

## 🧮 Reward Function
```
TOTAL REWARD = (
    0.25 × line_detection_score
  + 0.20 × issue_classification_score
  + 0.25 × fix_quality_score
  + 0.15 × explanation_quality_score
  + 0.15 × investigation_efficiency_score
) − penalties
```

Penalties:
- −0.10 per false-positive line flagged
- −0.05 for wrong severity classification

Rewards are emitted at every step (not just terminal) to encourage trajectory learning.

---

## 📊 Baseline Scores (heuristic agent)

| Task | Score |
|---|---|
| spot_the_bug | 0.7464 |
| security_audit | 0.0901 |
| system_debug | 0.1887 |

---

## 🌐 API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Health check |
| `/reset` | POST | Initialize episode |
| `/step` | POST | Submit action |
| `/state` | GET | Current state |
| `/tasks` | GET | All tasks + schemas |
| `/grader` | POST | Score completed episode |
| `/baseline` | POST | Run baseline agent |
| `/episode_summary` | GET | Full trajectory analysis |

---

## 🚀 Quick Start
```bash
docker build -t securecodops .
docker run -p 7860:7860 securecodops
```

Test it:
```bash
curl http://localhost:7860/health
curl -X POST "http://localhost:7860/reset?task_id=spot_the_bug"
curl -X POST "http://localhost:7860/baseline"
```

---

## 🔍 Failure Mode Analysis

Example grader output:
```json
{
  "score": 0.62,
  "missed_issues": ["SQL injection not detected"],
  "false_positives": ["line 45 incorrectly flagged"],
  "reasoning_gap": "Agent did not inspect DB layer"
}
```

---

## Inference Script

`inference.py` emits mandatory `[START]/[STEP]/[END]` logs per task and reads:
- `API_BASE_URL`
- `MODEL_NAME`
- `HF_TOKEN`

Example:
```
[START] task=spot_the_bug env=securecodops-env model=Qwen/Qwen2.5-72B-Instruct
[STEP] step=1 action={"action_type": "..."} reward=0.74 done=true error=null
[END] success=true steps=1 score=0.74 rewards=0.74
```
