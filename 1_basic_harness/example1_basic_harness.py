# example1_basic_harness.py

from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

# Connect to local Ollama instance with Gemma model
llm = ChatOllama(
    model="gemma3:4b",
    temperature=0
)

# Stage 1 harness: basic prompt and model invocation
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
