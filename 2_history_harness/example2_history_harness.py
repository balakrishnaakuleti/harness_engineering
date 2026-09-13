# Demo query: write a function that adds two numbers
# Then (to show memory in action): now make it subtract instead
# example2_history_harness.py

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from harness_llm import get_llm

# Connect to the shared inference endpoint (openai/gpt-oss-120b)
llm = get_llm()

# Define prompt template for iterative code generation
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful developer agent. Generate Python code based on user requests."),
    ("human", "{task}")
])

# Build chain
chain = prompt | llm

# CONCEPT: Memory & State.
# The harness now remembers prior turns so follow-up requests have context,
# instead of every request being a stateless, isolated model call.
history = InMemoryChatMessageHistory()
chain_with_history = RunnableWithMessageHistory(
    chain,
    lambda session_id: history,
    input_messages_key="task",
    history_messages_key="history"
)

# Interactive loop with command prompt
print("=== History Harness ===")
print("Type your programming requests. Type 'exit' to quit.\n")

session_id = "dev_harness_session"

while True:
    task = input("Enter your request: ")
    additional_context = "Just provide the code without explanations and examples."
    if task.lower() == "exit":
        break

    # Stream response with history
    for chunk in chain_with_history.stream(
        {"task": task+additional_context},   
        config={"configurable": {"session_id": session_id}}
    ):
        print(chunk.content, end="", flush=True)
    print("\n")
