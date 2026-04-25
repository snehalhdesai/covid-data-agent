import os
from openai import OpenAI
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
engine = create_engine("sqlite:///data/covid.db")

schema = "Table: states_history. Columns: date (integer YYYYMMDD), state (text 2-letter), positive (integer), death (integer), hospitalizedCurrently (integer), hospitalizedCumulative (integer), deathIncrease (integer), positiveIncrease (integer), hospitalizedIncrease (integer)"

history = []

def ask_agent(question, retries=2):
    history.append({"role": "user", "content": question})
    system = "You are a SQL expert. SQLite database schema: " + schema + ". Reply with ONLY a valid SQL SELECT query. No explanation. No markdown."
    messages = [{"role": "system", "content": system}] + history
    for attempt in range(retries + 1):
        try:
            resp = client.chat.completions.create(model="gpt-3.5-turbo", messages=messages)
            sql = resp.choices[0].message.content.strip().replace("```sql","").replace("```","").strip()
            print("[Running: " + sql + "]")
            with engine.connect() as conn:
                rows = conn.execute(text(sql)).fetchall()
            history.append({"role": "assistant", "content": sql})
            return rows
        except Exception as e:
            if attempt < retries:
                messages.append({"role": "user", "content": "Error: " + str(e) + ". Fix and retry."})
            else:
                return "Failed: " + str(e)

print("SQL Agent ready! Type quit to exit.")
while True:
    q = input("You: ")
    if q.lower() == "quit":
        break
    result = ask_agent(q)
    if isinstance(result, list):
        for row in result[:10]:
            print(row)
    else:
        print(result)
    print()
