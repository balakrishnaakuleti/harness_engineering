# example4_multi_agent_harness.py

import re
import shutil
import subprocess
import sys
import logging
import time
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

# Prompt template for developer agent
developer_prompt = ChatPromptTemplate.from_template(
    "Write a Python program to {task}.\n"
    "The program should take input from the user and print the result.\n"
    "Return only valid Python source code. Do not include explanations, "
    "Markdown fences, headings, or examples.\n"
    "Previous code:\n{previous_code}\n"
    "Feedback from the tester or reviewer:\n{feedback}"
)

developer_chain = developer_prompt | llm


def print_section(title: str, content: str = ""):
    separator = "*" * 72
    print(f"\n{separator}\n* {title}\n{separator}")
    if content:
        print(content)


def extract_code(response: str) -> str:
    """Remove optional Markdown fences from an LLM response."""
    fenced_code = re.search(
        r"```(?:python)?\s*(.*?)```", response, re.DOTALL | re.IGNORECASE
    )
    if fenced_code:
        return fenced_code.group(1).strip() + "\n"
    return response.strip() + "\n"


class DeveloperAgent:
    def generate_code(
        self, task: str, previous_code: str = "", feedback: str = ""
    ) -> str:
        logger.info("DeveloperAgent: Generating code for task '%s'", task)
        code_output = ""
        for chunk in developer_chain.stream({
            "task": task,
            "previous_code": previous_code,
            "feedback": feedback
        }):
            text = chunk.content
            print(text, end="", flush=True)
            code_output += text
        print()
        return extract_code(code_output)

class TesterAgent:
    def run_checks(self, filename: str):
        logger.info("TesterAgent: Running lint and compile checks...")
        try:
            flake8 = shutil.which("flake8")
            if flake8:
                lint_result = subprocess.run(
                    [flake8, filename],
                    capture_output=True,
                    text=True
                )
                if lint_result.returncode != 0:
                    logger.error("TesterAgent: Lint errors detected.")
                    return False, lint_result.stdout or lint_result.stderr
            else:
                logger.warning("TesterAgent: flake8 is not installed; skipping lint.")

            compile_result = subprocess.run(
                [sys.executable, "-m", "py_compile", filename],
                capture_output=True,
                text=True
            )
            if compile_result.returncode != 0:
                logger.error("TesterAgent: Compilation errors detected.")
                return False, compile_result.stderr

            logger.info("TesterAgent: Checks passed successfully.")
            return True, "No errors"
        except Exception as e:
            logger.exception("TesterAgent: Unexpected error.")
            return False, str(e)

class ReviewerAgent:
    def validate_output(self, filename: str, expected: str):
        logger.info("ReviewerAgent: Executing file to validate output...")
        try:
            run_result = subprocess.run(
                [sys.executable, filename],
                input="5\n",  # Example input for testing
                capture_output=True,
                text=True
            )
            if expected in run_result.stdout:
                logger.info("ReviewerAgent: Output validation passed.")
                return True, run_result.stdout
            else:
                logger.warning("ReviewerAgent: Output mismatch.")
                return False, run_result.stdout
        except Exception as e:
            logger.exception("ReviewerAgent: Execution error.")
            return False, str(e)

class FinalizerAgent:
    def package_code(self, filename: str):
        logger.info("FinalizerAgent: Packaging code into final bundle.")
        return f"Final code saved in {filename}"

class MultiAgentHarness:
    def __init__(self):
        self.developer = DeveloperAgent()
        self.tester = TesterAgent()
        self.reviewer = ReviewerAgent()
        self.finalizer = FinalizerAgent()

    def run(
        self,
        task: str,
        filename: str = "multi_agent_harness_code.py",
        expected: str = "",
        max_attempts: int = 5
    ):
        previous_code = ""
        feedback = "No previous feedback - this is the first attempt."

        for attempt in range(1, max_attempts + 1):
            attempt_started = time.perf_counter()
            logger.info("=== Multi-Agent Harness Attempt %d ===", attempt)
            print_section("MULTI-AGENT HARNESS ATTEMPT", f"{attempt}/{max_attempts}")
            print_section("DEVELOPER STREAM")
            code = self.developer.generate_code(task, previous_code, feedback)
            print_section("GENERATED CODE", code)

            with open(filename, "w", encoding="utf-8") as f:
                f.write(code)

            success, message = self.tester.run_checks(filename)
            if not success:
                previous_code = code
                feedback = f"Tester errors:\n{message}"
                print_section("TESTER FEEDBACK", feedback)
                logger.info(
                    "Attempt %d failed tester checks in %.2f seconds.",
                    attempt,
                    time.perf_counter() - attempt_started
                )
                continue
            print_section("TESTER RESULT", "PASSED - syntax and lint checks passed")

            success, output = self.reviewer.validate_output(filename, expected)
            if not success:
                previous_code = code
                feedback = (
                    f"Adjust output to match expected: {expected}\n"
                    f"Reviewer saw:\n{output}"
                )
                print_section("REVIEWER FEEDBACK", feedback)
                logger.info(
                    "Attempt %d failed reviewer checks in %.2f seconds.",
                    attempt,
                    time.perf_counter() - attempt_started
                )
                continue
            print_section("REVIEWER RESULT", f"PASSED\n{output}")

            result = self.finalizer.package_code(filename)
            duration = time.perf_counter() - attempt_started
            print_section("MULTI-AGENT HARNESS RESULT", f"PASSED - {result}\nDuration: {duration:.2f}s")
            logger.info("Workflow complete in %.2f seconds: %s", duration, result)
            return True

        result = f"Failed after {max_attempts} attempts"
        print_section("MULTI-AGENT HARNESS RESULT", f"FAILED - {result}")
        logger.error(result)
        return False

if __name__ == "__main__":
    task = input("Enter the programming task: ")
    expected = input("Enter expected output substring (optional): ")
    harness = MultiAgentHarness()
    harness.run(task, expected=expected, max_attempts=5)
