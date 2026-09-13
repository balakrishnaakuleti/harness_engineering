# Harness Engineering

Eight progressively richer examples of LLM-powered Python code-generation harnesses, evolving
from a raw model call to a fully governed harness with guides, sensors, feedback loops, test
suites, sandboxing, and human-in-the-loop safety gates.

## Prerequisites

- Python 3.10 or newer
- Access to the shared inference endpoint: an OpenAI-compatible (vLLM) server at
  `https://100.82.5.75:443/v1/` hosting `openai/gpt-oss-120b`. No API key is required.
  All examples read this from `harness_llm.py`, which can be overridden with the
  `HARNESS_LLM_BASE_URL` / `HARNESS_LLM_MODEL` / `HARNESS_LLM_API_KEY` environment
  variables if you point the examples at a different endpoint or model.

Set up a virtual environment and install dependencies:

```powershell
python -m venv .venv
.venv\Scripts\activate        # on Linux/macOS: source .venv/bin/activate
python -m pip install -r requirements.txt
```

Activating `.venv` also puts `flake8` on `PATH`, which examples 3 onward use for
linting when available (they fall back to a compile-only check if it's missing).

> The inference endpoint uses a self-signed certificate, so `harness_llm.py`
> disables TLS verification by default. Set `HARNESS_LLM_VERIFY_SSL=true` if
> your endpoint has a trusted certificate.

## Examples

Run each command from its example folder:

| Example | Concept | Command |
| --- | --- | --- |
| 1 | Basic prompt and streaming (model only, no controls) | `python example1_basic_harness.py` |
| 2 | Conversation history (memory & state) | `python example2_history_harness.py` |
| 3 | Generate, validate, and retry with feedback (Sensor + feedback loop) | `python example3_feedback_harness.py` |
| 4 | Developer, tester, reviewer, and finalizer agents (role-split architecture) | `python example4_multi_agent_harness.py` |
| 5 | Parallel validation and security scanning (parallel orchestration + guardrails) | `python example5_parallel_orchestrator_harness.py` |
| 6 | Coding-standards Guide + upfront Sprint Contract (feedforward controls) | `python example6_guide_harness.py` |
| 7 | Independent test-generator agent + functional unit test suite (verification beyond lint/compile) | `python example7_test_suite_harness.py` |
| 8 | Ephemeral sandbox execution + pre-execution guardrails + Human-in-the-Loop approval gate | `python example8_sandbox_hitl_harness.py` |

For example:

```powershell
cd 3_feedback_harness
python example3_feedback_harness.py
```

Examples 3 and up create temporary generated Python files in their current folder. Those output files are ignored by Git. Example 5 also includes `workflow5_parallel_orchestrator_harness.yaml` as a reference workflow definition.

## How the examples map to harness concepts

| Concept | First introduced in |
| --- | --- |
| Feedforward Guide (coding standards / system prompt) | 6 |
| Sprint Contract / Definition of Done | 6 |
| Feedback Sensor (lint/compile) | 3 |
| Feedback loop / retry-on-failure | 3 |
| Memory & conversation state | 2 |
| Role-split agents (developer/tester/reviewer/finalizer) | 4 |
| Parallel validation orchestration | 5 |
| Guardrails (post-hoc security scan) | 5 |
| Guardrails (pre-execution block) | 8 |
| Functional unit test suite | 7 |
| Ephemeral sandbox execution | 8 |
| Human-in-the-Loop approval gate | 8 |

Together, examples 1 through 8 tell the same story as the "Anatomy of an Agent Harness" and
"Evolution of Harness Engineering" slides: each stage adds exactly one control the previous
stage was missing, and the failures at each stage motivate why the next control exists.