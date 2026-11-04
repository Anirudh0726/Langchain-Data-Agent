import pyodbc
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL


# Windows Authentication (connected as JOBS-PC\Anirudh)
connection_string = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    r"SERVER=Jobs-PC\SQLEXPRESS;"
    "DATABASE=MY_DATABASE;"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;"
)

connection_url = URL.create(
    "mssql+pyodbc",
    query={"odbc_connect": connection_string}
)

engine = create_engine(connection_url)


def execute_query(query):
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
    return df


def get_schema(schema_name="dbo"):
    query = text("""
        SELECT
            cols.TABLE_NAME,
            cols.COLUMN_NAME,
            cols.DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS cols
        JOIN INFORMATION_SCHEMA.TABLES t
            ON  t.TABLE_SCHEMA = cols.TABLE_SCHEMA
            AND t.TABLE_NAME   = cols.TABLE_NAME
        WHERE cols.TABLE_SCHEMA = :schema_name
          AND t.TABLE_TYPE = 'BASE TABLE'
        ORDER BY cols.TABLE_NAME, cols.ORDINAL_POSITION;
    """)

    with engine.connect() as conn:
        df = pd.read_sql(query, conn, params={"schema_name": schema_name})

    if df.empty:
        raise ValueError(f"No tables found in schema '{schema_name}'.")

    # Build a text description the LLM can use directly in the prompt
    lines = []
    for table_name, group in df.groupby("TABLE_NAME", sort=False):
        lines.append(f"Table: {schema_name}.{table_name}")
        lines.append("Columns:")
        for _, row in group.iterrows():
            lines.append(f"  - [{row['COLUMN_NAME']}] {row['DATA_TYPE']}")
        lines.append("")   # blank line between tables

    return "\n".join(lines).strip()


# Runs only with `python tools.py`, not when main.py imports this file
if __name__ == "__main__":
    print(get_schema())