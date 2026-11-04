import uuid
import json

import streamlit as st
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent

from agent_tools import execute_query, get_schema

load_dotenv()

st.set_page_config(page_title="SQL Data Agent", page_icon="🗄️", layout="wide")

SYSTEM_PROMPT = (
    "You are a MS SQL Server expert. "
    "First call get_schema to see the available tables and columns, "
    "then use execute_query to run a SELECT query and answer the user's question. "
    "Use T-SQL syntax (TOP instead of LIMIT) and wrap names with special "
    "characters like [Country/Region] in square brackets. Only run SELECT queries."
)


@st.cache_resource
def get_agent():
    model = ChatOpenAI(model="gpt-6-luna")
    return create_agent(
        model=model,
        tools=[get_schema, execute_query],
        system_prompt=SYSTEM_PROMPT,
    )


agent = get_agent()


# ---------- Session state ----------
# chats = {chat_id: {"title": str, "messages": [ {role, content, tool_calls} ]}}
if "chats" not in st.session_state:
    st.session_state.chats = {}
if "current_chat" not in st.session_state:
    st.session_state.current_chat = None


def new_chat():
    chat_id = str(uuid.uuid4())
    st.session_state.chats[chat_id] = {"title": "New chat", "messages": []}
    st.session_state.current_chat = chat_id


if st.session_state.current_chat is None:
    new_chat()


# ---------- Helpers ----------
def text_of(message):
    """Safely get plain text from a LangChain message."""
    content = getattr(message, "content", "")
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, dict):
                parts.append(part.get("text", ""))
            else:
                parts.append(str(part))
        return "".join(parts)
    return str(content)


def extract_tool_calls(messages):
    """Pair each tool call (name + args) with its result from the agent's messages."""
    calls = []
    results = {}
    for m in messages:
        if m.type == "tool":
            results[m.tool_call_id] = text_of(m)
    for m in messages:
        if m.type == "ai" and getattr(m, "tool_calls", None):
            for tc in m.tool_calls:
                calls.append(
                    {
                        "name": tc["name"],
                        "args": tc["args"],
                        "result": results.get(tc["id"], ""),
                    }
                )
    return calls


def render_tool_calls(tool_calls):
    for i, tc in enumerate(tool_calls, start=1):
        with st.expander(f"🔧 Tool call {i}: {tc['name']}", expanded=False):
            st.markdown("**Arguments**")
            st.code(json.dumps(tc["args"], indent=2), language="json")
            st.markdown("**Result**")
            st.code(tc["result"] or "(empty)", language="text")


def to_agent_messages(chat_messages):
    """Convert stored chat to the (role, text) format the agent expects."""
    return [(m["role"], m["content"]) for m in chat_messages]


# ---------- Sidebar (left panel) ----------
with st.sidebar:
    st.title("🗄️ SQL Data Agent")

    if st.button("➕ New chat", use_container_width=True):
        new_chat()
        st.rerun()

    show_tools = st.toggle("Show tool calls", value=False)

    st.divider()
    st.subheader("Chat history")

    # newest chat first
    for chat_id in reversed(list(st.session_state.chats.keys())):
        chat = st.session_state.chats[chat_id]
        label = chat["title"]
        is_current = chat_id == st.session_state.current_chat
        if st.button(
            ("👉 " if is_current else "") + label,
            key=f"chat_{chat_id}",
            use_container_width=True,
        ):
            st.session_state.current_chat = chat_id
            st.rerun()


# ---------- Main chat area ----------
chat = st.session_state.chats[st.session_state.current_chat]

st.header(chat["title"] if chat["messages"] else "Ask a question about your data")

for msg in chat["messages"]:
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant" and show_tools and msg.get("tool_calls"):
            render_tool_calls(msg["tool_calls"])
        st.markdown(msg["content"])

user_input = st.chat_input("Ask Questions Please...")

if user_input:
    # Show + store the user message
    chat["messages"].append({"role": "user", "content": user_input, "tool_calls": []})
    if chat["title"] == "New chat":
        chat["title"] = user_input[:40] + ("..." if len(user_input) > 40 else "")

    with st.chat_message("user"):
        st.markdown(user_input)

    # Run the agent with the full history so it remembers the conversation
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                history = to_agent_messages(chat["messages"])
                response = agent.invoke({"messages": history})
                all_messages = response["messages"]

                # Only the messages produced for this turn (after the last human message)
                last_human_idx = max(
                    i for i, m in enumerate(all_messages) if m.type == "human"
                )
                turn_messages = all_messages[last_human_idx + 1 :]

                tool_calls = extract_tool_calls(turn_messages)
                answer = text_of(all_messages[-1])
            except Exception as e:
                tool_calls = []
                answer = f"Something went wrong:\n\n```\n{e}\n```"

        if show_tools and tool_calls:
            render_tool_calls(tool_calls)
        st.markdown(answer)

    chat["messages"].append(
        {"role": "assistant", "content": answer, "tool_calls": tool_calls}
    )
    st.rerun()