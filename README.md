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

> The first OpenEnv environment that simulates real-world DevSecOps investigation — from reading logs to proposing production-ready fixes — across 3 difficulty tiers with trajectory-aware grading.

---

## 🎯 Why This Exists

Code review and security auditing are among the highest-leverage tasks in software engineering — yet no OpenEnv environment exists to train or evaluate agents on them.

**Existing benchmarks fail because:**
- They are static (no interaction, no reward shaping)
- They test knowledge, not reasoning
- They have no trajectory signal — just binary pass/fail
- They don't simulate real debugging workflows

SecureCodeOpsEnv fills this gap.

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
| current_phase | enum | INIT/CONTEXT_FETCH/ROOT_CAUSE/FINAL |

### Action Space
| Field | Type | Description |
|---|---|---|
| action_type | enum | IDENTIFY_ISSUE, REQUEST_FILE, NARROW_DOWN, PROPOSE_FIX |
| line_numbers | list[int] | Flagged line numbers |
| issue_type | enum | BUG, SECURITY, PERFORMANCE, LOGIC, RACE_CONDITION |
| severity | enum | LOW, MEDIUM, HIGH, CRITICAL |
| suggested_fix | string | Proposed fix |
| explanation | string | Agent's reasoning |
| confidence | float | 0.0–1.0 |

---

## 🗂️ Tasks

### 🟢 Task 1 — `spot_the_bug` (Easy)
- **Input:** Single Python function with a real bug
- **Source:** BugsInPy-inspired real bug patterns
- **Agent must:** Identify buggy lines + propose fix in one step
- **Expected frontier model score:** ~0.75

### 🟡 Task 2 — `security_audit` (Medium)
- **Input:** Web application code with hidden vulnerability
- **Source:** Real CVE patterns (CWE-89, CWE-798, CWE-22)
- **Agent must:** Classify vulnerability + identify lines + fix
- **Expected frontier model score:** ~0.45

### 🔴 Task 3 — `system_debug` (Hard)
- **Input:** Multi-file project with logs + stack trace
- **Source:** Real race condition / deadlock patterns
- **Agent must:** Multi-turn investigation across 4 phases
- **Expected frontier model score:** ~0.35

#### Hard Task State Machine:
```
INIT → CONTEXT_FETCH → ROOT_CAUSE → FINAL
```
Agent cannot jump to a fix without investigating logs and files first.

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

**Penalties:**
- −0.10 per false positive line flagged
- −0.05 for wrong severity classification

**Key property:** Rewards partial progress at every step — not just binary end-of-episode.

---

## 📊 Baseline Scores

| Task | Heuristic Agent Score |
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
# Clone and run locally
git clone https://github.com/rahul-69/securecodops-env
cd securecodops-env
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

After each episode, the grader returns:
```json
{
  "score": 0.62,
  "missed_issues": ["SQL injection not detected"],
  "false_positives": ["line 45 incorrectly flagged"],
  "reasoning_gap": "Agent did not inspect DB layer"
}
```

This makes the environment useful for **agent debugging**, not just evaluation.

## Inference Script

The baseline inference script is located at:

inference.py

It reads environment variables:
- API_BASE_URL
- MODEL_NAME
- HF_TOKEN

and produces baseline_scores JSON output.