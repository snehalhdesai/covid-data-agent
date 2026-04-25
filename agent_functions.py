import os
import json
import time
from openai import OpenAI
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
engine = create_engine("sqlite:///data/covid.db")

# Define functions the assistant can call
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_hospitalizations",
            "description": "Get hospitalization data for a specific state and date",
            "parameters": {
                "type": "object",
                "properties": {
                    "state": {"type": "string", "description": "2-letter state code e.g. CA"},
                    "date": {"type": "integer", "description": "Date as YYYYMMDD integer e.g. 20210305"}
                },
                "required": ["state", "date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_positive_cases",
            "description": "Get positive COVID cases for a specific state and date",
            "parameters": {
                "type": "object",
                "properties": {
                    "state": {"type": "string", "description": "2-letter state code e.g. NY"},
                    "date": {"type": "integer", "description": "Date as YYYYMMDD integer e.g. 20210305"}
                },
                "required": ["state", "date"]
            }
        }
    }
]

def get_hospitalizations(state, date):
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT state, date, hospitalizedIncrease FROM states_history WHERE state=:s AND date=:d"
        ), {"s": state, "d": date}).fetchall()
    return str(result) if result else "No data found"

def get_positive_cases(state, date):
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT state, date, positiveIncrease FROM states_history WHERE state=:s AND date=:d"
        ), {"s": state, "d": date}).fetchall()
    return str(result) if result else "No data found"

# Create assistant with tools
assistant = client.beta.assistants.create(
    name="COVID Function Agent",
    instructions="You are a COVID-19 data analyst. Use the available functions to fetch real data from the database before answering.",
    model="gpt-3.5-turbo",
    tools=tools
)
thread = client.beta.threads.create()
print("Function Agent ready! Type quit to exit.\n")

while True:
    question = input("You: ")
    if question.lower() == "quit":
        break

    client.beta.threads.messages.create(thread_id=thread.id, role="user", content=question)
    run = client.beta.threads.runs.create(thread_id=thread.id, assistant_id=assistant.id)

    while True:
        time.sleep(1)
        run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

        if run.status == "requires_action":
            tool_calls = run.required_action.submit_tool_outputs.tool_calls
            outputs = []
            for tc in tool_calls:
                args = json.loads(tc.function.arguments)
                print("[Calling:", tc.function.name, args, "]")
                if tc.function.name == "get_hospitalizations":
                    result = get_hospitalizations(args["state"], args["date"])
                elif tc.function.name == "get_positive_cases":
                    result = get_positive_cases(args["state"], args["date"])
                outputs.append({"tool_call_id": tc.id, "output": result})
            client.beta.threads.runs.submit_tool_outputs(thread_id=thread.id, run_id=run.id, tool_outputs=outputs)

        elif run.status == "completed":
            messages = client.beta.threads.messages.list(thread_id=thread.id)
            print("\nAgent:", messages.data[0].content[0].text.value, "\n")
            break
        elif run.status in ["failed", "cancelled", "expired"]:
            print("Run failed:", run.status)
            break
