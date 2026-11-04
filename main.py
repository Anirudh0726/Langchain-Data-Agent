from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from tools import execute_query, get_schema

load_dotenv()

model = ChatOpenAI(model='gpt-6-luna')
schema = get_schema ()

def clean_sql(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        text = text.rsplit("```", 1)[0]
    return text.strip()

while True:
    user_input = input("Ask Questions Please : ").strip()

    if user_input.lower() == 'exit':
        break
    if not user_input:
        continue

    prompt = f"""You are a SQL Server (T-SQL) expert.
            Write a T-SQL query for the question below using only this table and these columns.
            Return ONLY the SQL query. No explanation, no markdown.
            Wrap column names with special characters (like Country/Region) in square brackets.
            schema : {schema}
            question : {user_input}
        """
    # print (prompt)

    response = model.invoke(prompt)
    sql = clean_sql(response.text)
    print(sql)

    if not sql.upper().startswith("SELECT"):
        print("Blocked: only SELECT queries are allowed.")
        continue

    try:
        result = execute_query(sql)
        print(result.to_string(index=False))
    except Exception as e:
        print("Query failed:")
        print(e)