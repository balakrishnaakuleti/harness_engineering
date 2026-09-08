# example5_parallel_orchestrator_harness.py

import logging
import re
import shutil
import subprocess
import sys
import threading
import time
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

# Configure logging for observability
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Connect to local Ollama instance with Gemma model
llm = ChatOllama(model="gemma3:4b", temperature=0)

# Developer prompt
developer_prompt = ChatPromptTemplate.from_template(
    "Write a Python program to {task}.\n"
    "The program should take input from the user and print the result.\n"
    "Return only valid Python source code. Do not include explanations, "
    "Markdown fences, headings, or examples.\n"
    "Previous code:\n{previous_code}\n"
    "Feedback from validation:\n{feedback}"
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
        logger.info("DeveloperAgent: Streaming code generation for '%s'", task)
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
                    [flake8, filename], capture_output=True, text=True
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
        except Exception as error:
            logger.exception("TesterAgent: Unexpected error.")
            return False, str(error)

class SecurityAgent:
    def scan_code(self, filename: str):
        logger.info("SecurityAgent: Scanning code for unsafe patterns...")
        with open(filename, encoding="utf-8") as f:
            code = f.read()
        if "os.system" in code or "subprocess" in code:
            logger.warning("SecurityAgent: Unsafe system call detected.")
            return False, "Unsafe system call detected"
        logger.info("SecurityAgent: Security check passed.")
        return True, "Security check passed"

class FinalizerAgent:
    def package_code(self, filename: str):
        logger.info("FinalizerAgent: Packaging code into final bundle.")
        return f"Final code saved in {filename}"

class OrchestratorHarness:
    def __init__(self):
        self.developer = DeveloperAgent()
        self.tester = TesterAgent()
        self.security = SecurityAgent()
        self.finalizer = FinalizerAgent()

    def run(
        self,
        task: str,
        filename: str = "parallel_harness_code.py",
        max_attempts: int = 5
    ):
        previous_code = ""
        feedback = "No previous feedback - this is the first attempt."

        for attempt in range(1, max_attempts + 1):
            attempt_started = time.perf_counter()
            logger.info("=== Parallel Harness Attempt %d ===", attempt)
            print_section("PARALLEL HARNESS ATTEMPT", f"{attempt}/{max_attempts}")
            print_section("DEVELOPER STREAM")
            code = self.developer.generate_code(task, previous_code, feedback)
            print_section("GENERATED CODE", code)

            with open(filename, "w", encoding="utf-8") as f:
                f.write(code)

            # Run tester + security in parallel
            results = {}
            def run_tester():
                results["tester"] = self.tester.run_checks(filename)
            def run_security():
                results["security"] = self.security.scan_code(filename)

            t1 = threading.Thread(target=run_tester)
            t2 = threading.Thread(target=run_security)
            t1.start(); t2.start()
            t1.join(); t2.join()

            tester_ok, tester_msg = results["tester"]
            security_ok, security_msg = results["security"]
            print_section("PARALLEL VALIDATION", (
                f"Tester: {'PASSED' if tester_ok else 'FAILED'}\n"
                f"Security: {'PASSED' if security_ok else 'FAILED'}"
            ))

            if not tester_ok:
                previous_code = code
                feedback = f"Tester errors:\n{tester_msg}"
                print_section("TESTER FEEDBACK", feedback)
                logger.warning("TesterAgent failed:\n%s", tester_msg)
                continue

            if not security_ok:
                previous_code = code
                feedback = f"Security issues:\n{security_msg}"
                print_section("SECURITY FEEDBACK", feedback)
                logger.warning("SecurityAgent failed:\n%s", security_msg)
                continue

            result = self.finalizer.package_code(filename)
            duration = time.perf_counter() - attempt_started
            print_section("PARALLEL HARNESS RESULT", f"PASSED - {result}\nDuration: {duration:.2f}s")
            logger.info("Workflow complete: %s", result)
            return True

        result = f"Failed after {max_attempts} attempts"
        print_section("PARALLEL HARNESS RESULT", f"FAILED - {result}")
        logger.error(result)
        return False

if __name__ == "__main__":
    task = input("Enter the programming task: ")
    orchestrator = OrchestratorHarness()
    orchestrator.run(task, max_attempts=5)
