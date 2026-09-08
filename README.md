# Harness Engineering

Five progressively richer examples of LLM-powered Python code-generation harnesses.

## Prerequisites

- Python 3.10 or newer
- An active virtual environment
- [Ollama](https://ollama.com/) running locally with the `gemma3:4b` model
- Python packages: `langchain-core` and `langchain-ollama`

Install the packages with:

```powershell
python -m pip install langchain-core langchain-ollama
ollama pull gemma3:4b
```

## Examples

Run each command from its example folder:

| Example | Concept | Command |
| --- | --- | --- |
| 1 | Basic prompt and streaming | `python example1_basic_harness.py` |
| 2 | Conversation history | `python example2_history_harness.py` |
| 3 | Generate, validate, and retry with feedback | `python example3_feedback_harness.py` |
| 4 | Developer, tester, reviewer, and finalizer agents | `python example4_multi_agent_harness.py` |
| 5 | Parallel validation and security scanning | `python example5_parallel_orchestrator_harness.py` |

For example:

```powershell
cd 3_feedback_harness
python example3_feedback_harness.py
```

Examples 3 to 5 create temporary generated Python files in their current folder. Those output files are ignored by Git. Example 5 also includes `workflow5_parallel_orchestrator_harness.yaml` as a reference workflow definition.