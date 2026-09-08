# example3_feedback_harness.py

import re
import shutil
import subprocess
import sys
import logging
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

# Connect to local Ollama instance with Gemma model
llm = ChatOllama(
    model="gemma3:4b",
    temperature=0
)

# Define prompt template for code generation with error feedback
prompt = ChatPromptTemplate.from_template(
    "Write a Python program to {task}.\n"
    "The program should take input from the user and print the result.\n"
    "Return only valid Python source code. Do not include explanations, "
    "Markdown fences, headings, or examples.\n"
    "Previous code:\n{previous_code}\n"
    "Validation errors:\n{errors}"
)

chain = prompt | llm


def print_section(title: str, content: str = ""):
    """Print a clearly separated section for the live harness demo."""
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


def run_lint_and_compile(filename: str):
    """Run available lint checks and compile the generated file."""
    try:
        flake8 = shutil.which("flake8")
        if flake8:
            logger.info("Running lint check with flake8...")
            lint_result = subprocess.run(
                [flake8, filename],
                capture_output=True,
                text=True
            )
            if lint_result.returncode != 0:
                logger.error("Lint errors detected.")
                return False, lint_result.stdout or lint_result.stderr
        else:
            logger.warning("flake8 is not installed; skipping lint check.")

        logger.info("Running compile check with py_compile...")
        compile_result = subprocess.run(
            [sys.executable, "-m", "py_compile", filename],
            capture_output=True,
            text=True
        )
        if compile_result.returncode != 0:
            logger.error("Compilation errors detected.")
            return False, compile_result.stderr

        logger.info("Lint and compile checks passed successfully.")
        return True, "No errors"
    except Exception as e:
        logger.exception("Unexpected error during lint/compile.")
        return False, str(e)

def feedback_loop(task: str, filename: str = "feedback_harness_code.py", max_attempts: int = 5):
    """Generate code, run checks, and stop after the configured attempts."""
    previous_code = ""
    errors = "None - this is the first attempt."

    for attempt in range(1, max_attempts + 1):
        print_section("FEEDBACK HARNESS ATTEMPT", f"{attempt}/{max_attempts} - {task}")
        logger.info(f"=== Feedback Harness Attempt {attempt}: Generating code for '{task}' ===")

        # Get code from LLM
        code_output = ""
        for chunk in chain.stream({
            "task": task,
            "previous_code": previous_code,
            "errors": errors
        }):
            code_output += chunk.content
        code_output = extract_code(code_output)
        print_section("GENERATED CODE", code_output)

        logger.info("Saving generated code to file: %s", filename)
        with open(filename, "w", encoding="utf-8") as f:
            f.write(code_output)

        # Run lint + compile
        success, message = run_lint_and_compile(filename)
        if success:
            print_section("VALIDATION", "PASSED - generated code is valid")
            logger.info("Code passed lint and compile checks!")
            return True

        previous_code = code_output
        errors = message
        print_section("VALIDATION", f"FAILED\n{message}")
        print_section("FEEDBACK", "Sending the generated code and validation errors to the model.")
        logger.warning("Errors found:\n%s", message)

    print_section("HARNESS RESULT", f"FAILED - stopped after {max_attempts} attempts")
    logger.error("Feedback Harness stopped after %s attempts.", max_attempts)
    return False

if __name__ == "__main__":
    task = input("Enter the programming task: ")
    feedback_loop(task, max_attempts=5)
