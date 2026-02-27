Run an autonomous simulated student session against the FAIR-LLM tutor.

## What to do

**Always activate the virtual environment first:**
```bash
cd ~/fair_llm_tutor && source .venv/bin/activate
```

Then run the session runner script as a single long-lived process. It handles everything: starting the tutor, generating student responses, capturing tutor responses, and logging to JSONL.

Parse the user's arguments from: `$ARGUMENTS`

**If arguments are empty**, run a default scenario:
```bash
python -m student_mode.session_runner --scenario derivatives --student-llm anthropic
```

**If the user provides a built-in scenario name** (derivatives, recursion, matrices, statistics, ml_basics):
```bash
python -m student_mode.session_runner --scenario <name> --student-llm anthropic
```

**If the user provides a topic and problem**:
```bash
python -m student_mode.session_runner --topic "<topic>" --problem "<problem>" --initial-work "<work>" --student-llm anthropic
```

**If the user says "all"**:
```bash
python -m student_mode.session_runner --all --student-llm anthropic
```

**If the user says "deterministic" or "no llm"**, drop the `--student-llm` flag to use canned responses instead of LLM-generated ones.

## After the script finishes

1. Run the aggregate results script to display session data:
```bash
python -m student_mode.aggregate_results --detail
```
2. Summarize the key findings: how many turns, average latency, any notable moments
3. Quality scoring: read the JSONL and assess each tutor response for safety, pedagogy, helpfulness, and domain accuracy

## Important constraints

- Run the script from `~/fair_llm_tutor` (it needs to find `main.py`)
- Do NOT read or modify tutor source code (`agents/`, `tools/`, `main.py`)
- Do NOT interact with the tutor in any way other than through `session_runner.py`
- The script's output timeout is 300s by default — use `--timeout` to increase for slow models
