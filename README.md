# SecureCodeOpsEnv 🛡️

**AI DevSecOps Debugging & Security Audit Environment**

SecureCodeOpsEnv is a production-ready OpenEnv environment designed to challenge and evaluate AI agents on their ability to identify, analyze, and fix software bugs and security vulnerabilities.

## 🚀 Quick Start

### Build and Run with Docker
```bash
docker build -t securecodops .
docker run -p 7860:7860 securecodops
```

### Run Locally
```bash
pip install -r requirements.txt
python app.py
```

### Health Check
```bash
curl http://localhost:7860/health
```

## 🛠️ Tasks

1. **spot_the_bug (Easy)**: Identify obvious bugs in single-function snippets.
2. **security_audit (Medium)**: Detect real-world security vulnerabilities (CWE-89, CWE-798, etc.).
3. **system_debug (Hard)**: Multi-turn debugging involving logs, stack traces, and multi-file dependencies.

## 📡 API Endpoints

- `GET /health`: Server status.
- `POST /reset?task_id={id}`: Initialize a new debugging episode.
- `POST /step`: Submit an action and get an observation/reward.
- `GET /state`: View current environment state.
- `GET /tasks`: List all available tasks and schemas.
- `POST /grader`: Calculate final trajectory score.
- `POST /baseline`: Execute heuristic baseline evaluation.

## 🧪 Testing

Run integration tests:
```bash
pytest tests/test_env.py
```

## 📊 Environment Details

- **Observation Space**: Includes code snippets, logs, stack traces, and revealed files.
- **Action Space**: IDENTIFY_ISSUE, REQUEST_FILE, ASK_QUESTION, FORM_HYPOTHESIS, NARROW_DOWN, PROPOSE_FIX.
- **Reward Algorithm**: Deterministic calculation based on line detection, issue classification, fix quality, explanation quality, and efficiency.
