from langchain_ollama import ChatOllama

# Initialize the LLM
llm = ChatOllama(
    model="llama3.1", # change to qwen2.5:7b if you pulled that instead
    temperature=0,    # We want deterministic, analytical responses
)

response = llm.invoke("You are an SRE. Respond with 'System is online.' if you can hear me.")
print(response.content)
