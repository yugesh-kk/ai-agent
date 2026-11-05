from langgraph.checkpoint.memory import MemorySaver
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_ollama import ChatOllama

# Import the tools we built in Stage 2
from sre_tools import get_system_metrics, read_local_log

# ---------------------------------------------------------
# 1. Define the Graph State
# ---------------------------------------------------------
# The "State" is the agent's memory. As it moves through the loop, 
# it continually adds new messages (user inputs, tool results, AI thoughts) to this list.
class State(TypedDict):
    messages: Annotated[list, add_messages]

# ---------------------------------------------------------
# 2. Initialize LLM and Tools
# ---------------------------------------------------------
tools = [get_system_metrics, read_local_log]
llm = ChatOllama(model="llama3.1", temperature=0)

# We must explicitly "bind" the tools to the LLM so it knows what its hands can do.
llm_with_tools = llm.bind_tools(tools)

# ---------------------------------------------------------
# 3. Define the Nodes (The Actors)
# ---------------------------------------------------------
# Node A: The AI Agent
system_prompt = SystemMessage(
    content="""You are a strict, senior on-premises SRE Agent running on a macOS environment.
    You have tools to check system metrics and read logs. 
    Never guess or hallucinate answers. If you do not know, use a tool to find out. 
    Provide concise, technical summaries of your findings."""
)

def agent_node(state: State):
    # The agent always reads the system prompt plus all history in its state
    messages = [system_prompt] + state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

# Node B: The Tool Execution Node
# LangGraph provides a prebuilt node that catches tool requests, runs the Python function, 
# and formats the output as a ToolMessage to send back to the AI.
tool_node = ToolNode(tools)

# ---------------------------------------------------------
# 4. Define the Routing Logic (The Brain's Decision)
# ---------------------------------------------------------
def should_continue(state: State):
    # Check the very last message the AI generated
    last_message = state["messages"][-1]
    
    # If the AI decided to call a tool, route to the tool node
    if last_message.tool_calls:
        return "tools"
    # Otherwise, it gave a conversational answer, so we stop the loop
    return END

# ---------------------------------------------------------
# 5. Build and Compile the Graph (UPDATED)
# ---------------------------------------------------------
workflow = StateGraph(State)

workflow.add_node("agent", agent_node)
workflow.add_node("tools", tool_node)

workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", should_continue, ["tools", END])
workflow.add_edge("tools", "agent")

# Initialize memory so the agent remembers state between pauses
memory = MemorySaver()

# Compile the graph with a breakpoint right before the 'tools' node
app = workflow.compile(
    checkpointer=memory,
    interrupt_before=["tools"]
)

# ---------------------------------------------------------
# 6. Run the Interactive Loop (UPDATED)
# ---------------------------------------------------------
if __name__ == "__main__":
    print("🤖 Local SRE Agent Booted (HITL Enabled). Type 'exit' to quit.")
    
    # LangGraph uses thread IDs to track different conversations in memory
    config = {"configurable": {"thread_id": "1"}}
    
    while True:
        user_input = input("\nAdmin: ")
        if user_input.lower() == 'exit':
            break
            
        inputs = {"messages": [HumanMessage(content=user_input)]}
        
        print("--- Execution Trace ---")
        # Run the graph until it hits an interrupt (or finishes)
        for event in app.stream(inputs, config=config, stream_mode="values"):
            event["messages"][-1].pretty_print()
            
        # Check the state of the graph. If 'next' contains 'tools', it means
        # the graph paused because it hit our interrupt_before condition.
        snapshot = app.get_state(config)
        if snapshot.next and snapshot.next[0] == "tools":
            
            # Extract what the AI wants to do
            last_message = snapshot.values["messages"][-1]
            tool_call = last_message.tool_calls[0]
            
            print(f"\n🛑 HOLD UP! The Agent wants to touch the system.")
            print(f"Tool Requested: {tool_call['name']}")
            print(f"Arguments: {tool_call['args']}")
            
            approval = input("\nDo you approve this execution? (y/n): ")
            
            if approval.lower() == 'y':
                print("Executing tool...")
                # Resume the graph by passing None. It will pick up exactly where it paused.
                for event in app.stream(None, config=config, stream_mode="values"):
                    event["messages"][-1].pretty_print()
            else:
                print("Execution denied. Agent stopped.")
                # We would normally handle the rejection gracefully here, but we will break for simplicity
                break
