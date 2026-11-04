from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from agent_tools import execute_query, get_schema
from langchain.agents import create_agent

load_dotenv()

tools = [get_schema, execute_query]
model = ChatOpenAI(model='gpt-6-luna')

agent = create_agent(
    model=model,
    tools=tools,
    system_prompt=(
        "You are a MS SQL Server expert. "
        "First call get_schema to see the available tables and columns, "
        "then use execute_query to run a SELECT query and answer the user's question. "
        "Use T-SQL syntax (TOP instead of LIMIT) and wrap names with special "
        "characters like [Country/Region] in square brackets. Only run SELECT queries."
    )
)

while True:
    user_input = input("Ask Questions Please : ").strip()

    if user_input.lower() == 'exit':
        break
    if not user_input:
        continue

    response = agent.invoke({"messages": [("user", user_input)]})
    print(response["messages"][-1].text)