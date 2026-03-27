# SecureCodeOpsEnv 🛡️
### AI DevSecOps Debugging & Security Audit Environment (OpenEnv)

SecureCodeOpsEnv is a high-fidelity sandbox for evaluating AI agents on complex, multi-turn software debugging and security auditing tasks. It moves beyond static code fixes by enforcing structured reasoning through a phase-based state machine.

---

## 🚀 Why Existing Benchmarks Fail
Most existing AI coding benchmarks (e.g., HumanEval, MBPP) suffer from:
- **Static Evaluation**: They test isolated functions rather than system-wide interactions.
- **No Multi-Turn Reasoning**: Agents are rarely required to fetch logs or inspect multiple files.
- **No Trajectory Rewards**: They prioritize pass/fail over the logical investigation path.

## ✨ The Solution: SecureCodeOpsEnv
- **Phased State Machine**: `INIT → CONTEXT_FETCH → ROOT_CAUSE → FINAL`.
- **Dynamic Information Reveal**: System visibility is gated by the agent's current phase.
- **Trajectory-Aware Grading**: Composite score of phase completion, precise identification, semantic fix quality, and efficiency.

---

## 🛠️ API Usage

### 1. Reset Environment
```bash
curl -X POST "http://localhost:7860/reset?task_id=system_debug"
```

### 2. Execution Step
```bash
curl -X POST "http://localhost:7860/step" \
     -H "Content-Type: application/json" \
     -d '{"action_type": "REQUEST_FILE", "file_name": "db.py"}'
```

### 3. Calculate Grade
```bash
curl -X POST "http://localhost:7860/grader" \
     -H "Content-Type: application/json" \
     -d '{"episode_id": "YOUR_EPISODE_ID", "task_id": "system_debug"}'
```

---

## 🏆 Reward Design
The environment uses a multi-factor trajectory reward ∈ [0, 1]:
- **Phase Completion (+0.3)**: Moving logically through investigation phases.
- **Root Cause Access (+0.2)**: Successfully identifying and inspecting the buggy file.
- **Fix Correctness (+0.3)**: Semantic similarity and deterministic correctness of the fix.
- **Efficiency (+0.2)**: Penalty-free investigation within optimal step counts.

---

## 🎯 Use Cases
- **RL Agent Training**: Bridge the gap between code generation and system debugging.
- **LLM Evaluation**: Benchmark reasoning capabilities of advanced models.
- **DevSecOps Automation**: Evaluate automated security auditing tools.

---

## 🏗️ Quick Start
```bash
docker build -t securecodops .
docker run -p 7860:7860 securecodops
```
`curl http://localhost:7860/health`
