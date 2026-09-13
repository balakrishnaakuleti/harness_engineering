# Demo query: generate the first n Fibonacci numbers
# example1_basic_harness.py

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from langchain_core.prompts import ChatPromptTemplate
from harness_llm import get_llm

# Connect to the shared inference endpoint (openai/gpt-oss-120b)
llm = get_llm()

# CONCEPT: Model only, no harness controls at all.
# No Guide, no Sensor, no memory, no guardrails - whatever the model returns is final.
prompt = ChatPromptTemplate.from_template(
    "Write a Python program to {task}. "
    "The program should take input from the user and print the result."
)

# Build the chain
chain = prompt | llm

# Always take user input from command prompt
task = input("Enter the programming task (e.g., 'generate the first n Fibonacci numbers'): ")

print(f"\n=== Basic Harness | Request: {task} ===\n")

# Stream the generated code back to console
for chunk in chain.stream({"task": task}):
    print(chunk.content, end="", flush=True)
