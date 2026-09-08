# example2_history_harness.py

from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

# Connect to local Ollama instance with Gemma model
llm = ChatOllama(
    model="gemma3:4b",
    temperature=0
)

# Define prompt template for iterative code generation
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful developer agent. Generate Python code based on user requests."),
    ("human", "{task}")
])

# Build chain
chain = prompt | llm

# Add history wrapper
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
