# Demo query: sum two numbers entered by the user
# Then (to show the HITL gate): delete a file named test.txt
# example8_sandbox_hitl_harness.py

import re
import shutil
import subprocess
import sys
import tempfile
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

developer_prompt = ChatPromptTemplate.from_template(
    "Write a Python program to {task}.\n"
    "The program should take input from the user and print the result.\n"
    "Return only valid Python source code. Do not include explanations, "
    "Markdown fences, headings, or examples.\n"
    "Previous code:\n{previous_code}\n"
    "Feedback:\n{feedback}"
)
developer_chain = developer_prompt | llm

# CONCEPT: Guardrail (pre-execution block).
# Patterns that must never reach execution, sandboxed or not - a hard veto,
# unlike a Sensor's feedback which the model can negotiate around via retries.
DENYLIST_PATTERNS = [
    "os.system", "subprocess", "shutil.rmtree", "eval(", "exec(",
    "__import__", "socket", "urllib", "requests", "open(", "os.remove",
]

# CONCEPT: Human-in-the-Loop (HITL) trigger list.
# High-risk keywords in the *request itself* trigger a HITL gate before the
# harness will even attempt generation.
HITL_TRIGGER_KEYWORDS = ["delete", "remove", "format", "network", "email", "deploy", "payment"]


def print_section(title: str, content: str = ""):
    separator = "*" * 72
    print(f"\n{separator}\n* {title}\n{separator}")
    if content:
        print(content)


def extract_code(response: str) -> str:
    fenced_code = re.search(r"```(?:python)?\s*(.*?)```", response, re.DOTALL | re.IGNORECASE)
    if fenced_code:
        return fenced_code.group(1).strip() + "\n"
    return response.strip() + "\n"


# CONCEPT: Guardrail.
def guardrail_scan(code: str):
    """Guardrail: block unsafe patterns *before* anything runs, sandboxed or not."""
    hits = [pattern for pattern in DENYLIST_PATTERNS if pattern in code]
    return (len(hits) == 0), hits


# CONCEPT: Human-in-the-Loop (HITL) & Safety Fallbacks.
def human_in_the_loop_gate(task: str) -> bool:
    """HITL Gate Intercept: high-risk requests require an explicit human approval."""
    if not any(keyword in task.lower() for keyword in HITL_TRIGGER_KEYWORDS):
        return True  # low-risk / read-only path: proceed automatically

    print_section("HUMAN-IN-THE-LOOP GATE", (
        f"Request '{task}' matches a high-risk keyword.\n"
        "Automated sandbox execution is not allowed for this request without approval."
    ))
    approval = input("Approve generation and sandboxed execution? [y/N]: ").strip().lower()
    return approval == "y"


# CONCEPT: Tool Sandbox (ephemeral micro-VM style isolation).
def run_in_sandbox(filename: str, stdin_text: str = "5\n"):
    """Ephemeral sandbox: execute the generated program in an isolated temp
    directory, with a timeout, instead of the harness's own working directory."""
    with tempfile.TemporaryDirectory(prefix="agent_sandbox_") as sandbox_dir:
        sandbox_path = Path(sandbox_dir) / Path(filename).name
        sandbox_path.write_text(Path(filename).read_text(encoding="utf-8"), encoding="utf-8")

        logger.info("Running generated code inside ephemeral sandbox: %s", sandbox_dir)
        try:
            result = subprocess.run(
                [sys.executable, sandbox_path.name],
                cwd=sandbox_dir,
                input=stdin_text,
                capture_output=True,
                text=True,
                timeout=5,  # runaway/looping code gets killed automatically
            )
            return result.returncode == 0, (result.stdout or result.stderr)
        except subprocess.TimeoutExpired:
            return False, "Execution exceeded sandbox timeout (5s) and was terminated."


def sandbox_hitl_harness(task: str, filename: str = "sandbox_hitl_code.py", max_attempts: int = 3):
    if not human_in_the_loop_gate(task):
        print_section("HARNESS RESULT", "BLOCKED - human approval was not granted")
        logger.info("Request blocked by HITL gate: '%s'", task)
        return False

    previous_code = ""
    feedback = "No previous feedback - this is the first attempt."

    for attempt in range(1, max_attempts + 1):
        print_section("SANDBOX+HITL HARNESS ATTEMPT", f"{attempt}/{max_attempts} - {task}")

        code_output = ""
        for chunk in developer_chain.stream({
            "task": task,
            "previous_code": previous_code,
            "feedback": feedback
        }):
            code_output += chunk.content
        code_output = extract_code(code_output)
        print_section("GENERATED CODE", code_output)

        safe, hits = guardrail_scan(code_output)
        if not safe:
            previous_code = code_output
            feedback = f"Guardrail blocked unsafe pattern(s): {hits}. Rewrite without them."
            print_section("GUARDRAIL", f"BLOCKED\n{feedback}")
            logger.warning("Guardrail blocked patterns: %s", hits)
            continue

        with open(filename, "w", encoding="utf-8") as f:
            f.write(code_output)

        success, output = run_in_sandbox(filename)
        if not success:
            previous_code = code_output
            feedback = f"Sandbox execution failed:\n{output}"
            print_section("SANDBOX EXECUTION", f"FAILED\n{output}")
            continue

        print_section("SANDBOX EXECUTION", f"PASSED\n{output}")
        logger.info("Sandbox+HITL Harness succeeded on attempt %d.", attempt)
        return True

    print_section("HARNESS RESULT", f"FAILED - stopped after {max_attempts} attempts")
    logger.error("Sandbox+HITL Harness stopped after %s attempts.", max_attempts)
    return False


if __name__ == "__main__":
    task = input("Enter the programming task: ")
    sandbox_hitl_harness(task, max_attempts=3)
