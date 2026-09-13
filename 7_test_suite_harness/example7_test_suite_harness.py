# Demo query: returns the nth Fibonacci number, 0-indexed (function name: fib)
# example7_test_suite_harness.py

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

developer_prompt = ChatPromptTemplate.from_template(
    "Write a single Python function named `{function_name}` that {task}.\n"
    "Return only the function definition. Do not include explanations, "
    "Markdown fences, headings, input()/print() calls, or example usage.\n"
    "Previous code:\n{previous_code}\n"
    "Test failures:\n{errors}"
)
developer_chain = developer_prompt | llm

# CONCEPT: Feedback evaluator (independent test-generator agent).
# It writes assertions, the developer never sees them - decoupling generation
# from evaluation so the same model can't grade its own homework.
test_prompt = ChatPromptTemplate.from_template(
    "Write 3 to 5 pytest-style `assert` statements (no imports, no function definitions, "
    "no explanations, no Markdown fences) that verify a function named `{function_name}` "
    "which {task}. Reference the function directly, e.g. `assert {function_name}(...) == ...`."
)
test_chain = test_prompt | llm


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
    """Baseline sensor: syntax must be valid before functional tests even run."""
    result = subprocess.run(
        [sys.executable, "-m", "py_compile", filename],
        capture_output=True,
        text=True
    )
    return result.returncode == 0, result.stderr


# CONCEPT: Feedback control (Sensor) - Automated Test Execution Suite.
# Verifies functional correctness, a deeper check than the lint/compile Sensor.
def run_test_suite(code_filename: str, test_assertions: str, function_name: str):
    """Verification control: run *functional* unit tests, not just syntax checks."""
    harness_test_file = "_generated_test_runner.py"
    module_name = code_filename[:-3]
    with open(harness_test_file, "w", encoding="utf-8") as f:
        f.write(f"from {module_name} import {function_name}\n\n")
        f.write(test_assertions)
        f.write("\nprint('ALL_TESTS_PASSED')\n")

    result = subprocess.run(
        [sys.executable, harness_test_file],
        capture_output=True,
        text=True
    )
    passed = result.returncode == 0 and "ALL_TESTS_PASSED" in result.stdout
    message = result.stdout + result.stderr
    return passed, message


def test_suite_harness(task: str, function_name: str = "solve", filename: str = "test_suite_harness_code.py", max_attempts: int = 5):
    """Developer generates code; an independent Test Sensor verifies functional correctness."""
    print_section("GENERATING TEST SUITE", f"Independent test agent writing assertions for '{function_name}'")
    test_assertions = ""
    for chunk in test_chain.stream({"function_name": function_name, "task": task}):
        test_assertions += chunk.content
    test_assertions = extract_code(test_assertions)
    print_section("TEST SUITE (fixed for all attempts)", test_assertions)

    previous_code = ""
    errors = "None - this is the first attempt."

    for attempt in range(1, max_attempts + 1):
        print_section("TEST SUITE HARNESS ATTEMPT", f"{attempt}/{max_attempts} - {task}")
        logger.info("=== Attempt %d: generating '%s' ===", attempt, function_name)

        code_output = ""
        for chunk in developer_chain.stream({
            "function_name": function_name,
            "task": task,
            "previous_code": previous_code,
            "errors": errors
        }):
            code_output += chunk.content
        code_output = extract_code(code_output)
        print_section("GENERATED CODE", code_output)

        with open(filename, "w", encoding="utf-8") as f:
            f.write(code_output)

        compiled, compile_errors = run_compile_check(filename)
        if not compiled:
            previous_code, errors = code_output, compile_errors
            print_section("SENSOR (COMPILE)", f"FAILED\n{compile_errors}")
            continue

        passed, message = run_test_suite(filename, test_assertions, function_name)
        if not passed:
            previous_code, errors = code_output, message
            print_section("SENSOR (UNIT TESTS)", f"FAILED\n{message}")
            logger.warning("Unit tests failed on attempt %d.", attempt)
            continue

        print_section("SENSOR (UNIT TESTS)", "PASSED - functional correctness verified")
        logger.info("Test Suite Harness verified correctness on attempt %d.", attempt)
        return True

    print_section("HARNESS RESULT", f"FAILED - stopped after {max_attempts} attempts")
    logger.error("Test Suite Harness stopped after %s attempts.", max_attempts)
    return False


if __name__ == "__main__":
    task = input("Describe what the function should do (e.g., 'returns the nth Fibonacci number'): ")
    function_name = input("Enter the function name (default 'solve'): ") or "solve"
    test_suite_harness(task, function_name=function_name, max_attempts=5)
