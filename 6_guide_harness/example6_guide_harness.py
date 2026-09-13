# Demo query: count vowels in a string
# example6_guide_harness.py

import re
import shutil
import subprocess
import sys
import logging
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from langchain_core.prompts import ChatPromptTemplate
from harness_llm import get_llm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Connect to the shared inference endpoint (openai/gpt-oss-120b)
llm = get_llm()

# --- FEEDFORWARD CONTROL: AGENTS.md / Repository Architecture Guide -------
# Instead of hardcoding the Guide and Sprint Contract as Python strings, the
# harness reads them from a repo-level AGENTS.md file, exactly like a real
# coding agent would pick up workspace rules before generating anything.
AGENTS_MD_PATH = Path(__file__).resolve().parent / "AGENTS.md"


def load_agents_md_section(heading: str) -> str:
    """Extract one '## <heading>' section's body out of AGENTS.md."""
    text = AGENTS_MD_PATH.read_text(encoding="utf-8")
    match = re.search(rf"## {re.escape(heading)}\n(.*?)(?=\n## |\Z)", text, re.DOTALL)
    if not match:
        raise ValueError(f"Section '## {heading}' not found in {AGENTS_MD_PATH}")
    return match.group(1).strip()


# Feedforward control: the Guide steers generation *before* the model ever runs.
CODING_STANDARDS_GUIDE = load_agents_md_section("Coding Standards (must follow)")

# Feedforward control: the Sprint Contract negotiated up front (Definition of Done).
SPRINT_CONTRACT_TEXT = load_agents_md_section("Sprint Contract (Definition of Done)")

# Feedforward control: the Guide and Sprint Contract are injected into every
# generation request, straight from AGENTS.md, before the model writes a line of code.
prompt = ChatPromptTemplate.from_template(
    "Coding Standards (from AGENTS.md):\n{guide}\n\n"
    "Sprint Contract (from AGENTS.md):\n{contract}\n\n"
    "Write a Python program to {task}.\n"
    "Return only valid Python source code. Do not include explanations, "
    "Markdown fences, headings, or examples.\n"
    "Previous code:\n{previous_code}\n"
    "Contract check failures:\n{errors}"
)

chain = prompt | llm


def print_section(title: str, content: str = ""):
    separator = "*" * 72
    print(f"\n{separator}\n* {title}\n{separator}")
    if content:
        print(content)


def extract_code(response: str) -> str:
    """Remove optional Markdown fences from an LLM response."""
    fenced_code = re.search(r"```(?:python)?\s*(.*?)```", response, re.DOTALL | re.IGNORECASE)
    if fenced_code:
        return fenced_code.group(1).strip() + "\n"
    return response.strip() + "\n"


def run_compile_check(filename: str):
    """Sensor: confirm the file at least compiles."""
    compile_result = subprocess.run(
        [sys.executable, "-m", "py_compile", filename],
        capture_output=True,
        text=True
    )
    if compile_result.returncode != 0:
        return False, compile_result.stderr
    return True, "No errors"


def check_sprint_contract(code: str):
    """Feedback control (Sensor): programmatically verifies the AGENTS.md
    Sprint Contract was actually met, instead of trusting the model's word."""
    failures = []
    if "input(" not in code:
        failures.append("Contract item failed: program does not read user input.")
    if not re.search(r'""".*?"""', code, re.DOTALL) and not re.search(r"'''.*?'''", code, re.DOTALL):
        failures.append("Contract item failed: no docstring found on any function.")
    if not re.search(r"def \w+\([^)]*:\s*\w+", code):
        failures.append("Contract item failed: no type hints found on any function signature.")
    return failures


def guide_harness(task: str, filename: str = "guide_harness_code.py", max_attempts: int = 5):
    """Combine a feedforward Guide + Sprint Contract with a compile Sensor and retry loop."""
    previous_code = ""
    errors = "None - this is the first attempt."

    for attempt in range(1, max_attempts + 1):
        print_section("GUIDE HARNESS ATTEMPT", f"{attempt}/{max_attempts} - {task}")
        logger.info("=== Guide Harness Attempt %d: Generating code for '%s' ===", attempt, task)

        code_output = ""
        for chunk in chain.stream({
            "guide": CODING_STANDARDS_GUIDE,
            "contract": SPRINT_CONTRACT_TEXT,
            "task": task,
            "previous_code": previous_code,
            "errors": errors
        }):
            code_output += chunk.content
        code_output = extract_code(code_output)
        print_section("GENERATED CODE", code_output)

        with open(filename, "w", encoding="utf-8") as f:
            f.write(code_output)

        compiled, message = run_compile_check(filename)
        if not compiled:
            previous_code = code_output
            errors = message
            print_section("SENSOR (COMPILE)", f"FAILED\n{message}")
            continue

        contract_failures = check_sprint_contract(code_output)
        if contract_failures:
            previous_code = code_output
            errors = "\n".join(contract_failures)
            print_section("SPRINT CONTRACT CHECK", "FAILED\n" + errors)
            logger.warning("Contract not met:\n%s", errors)
            continue

        print_section("SPRINT CONTRACT CHECK", "PASSED - Definition of Done satisfied")
        logger.info("Guide Harness satisfied the Sprint Contract on attempt %d.", attempt)
        return True

    print_section("HARNESS RESULT", f"FAILED - stopped after {max_attempts} attempts")
    logger.error("Guide Harness stopped after %s attempts.", max_attempts)
    return False


if __name__ == "__main__":
    task = input("Enter the programming task: ")
    guide_harness(task, max_attempts=5)
