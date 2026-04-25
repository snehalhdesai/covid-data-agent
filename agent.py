import json
import time
import warnings
warnings.filterwarnings("ignore")
from openai import OpenAI
from config import OPENAI_API_KEY, OPENAI_MODEL
from database import get_hospitalizations, get_positive_cases, get_top_states, get_schema

client = OpenAI(api_key=OPENAI_API_KEY)

TOOLS = [
    {"type":"function","function":{"name":"get_hospitalizations","description":"Get hospitalization data for a US state and date","parameters":{"type":"object","properties":{"state":{"type":"string","description":"2-letter state code"},"date":{"type":"integer","description":"Date YYYYMMDD"}},"required":["state","date"]}}},
    {"type":"function","function":{"name":"get_positive_cases","description":"Get positive COVID cases for a US state and date","parameters":{"type":"object","properties":{"state":{"type":"string","description":"2-letter state code"},"date":{"type":"integer","description":"Date YYYYMMDD"}},"required":["state","date"]}}},
    {"type":"function","function":{"name":"get_top_states","description":"Get top states ranked by a COVID metric","parameters":{"type":"object","properties":{"metric":{"type":"string","description":"One of: death, positive, hospitalizedCumulative, deathIncrease, positiveIncrease"},"limit":{"type":"integer","description":"Number of states to return"}},"required":["metric"]}}}
]

FUNCTION_MAP = {
    "get_hospitalizations": lambda a: get_hospitalizations(a["state"], a["date"]),
    "get_positive_cases": lambda a: get_positive_cases(a["state"], a["date"]),
    "get_top_states": lambda a: get_top_states(a["metric"], a.get("limit", 5))
}

def create_assistant():
    schema = get_schema()
    return client.beta.assistants.create(
        name="COVID Data Agent",
        instructions=f"You are a COVID-19 data analyst. Always use functions to fetch real data. Schema: {schema}",
        model=OPENAI_MODEL,
        tools=TOOLS
    )

def create_thread():
    return client.beta.threads.create()

def ask(thread_id, assistant_id, question):
    client.beta.threads.messages.create(thread_id=thread_id, role="user", content=question)
    run = client.beta.threads.runs.create(thread_id=thread_id, assistant_id=assistant_id)
    logs = []
    while True:
        time.sleep(1)
        run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
        if run.status == "requires_action":
            outputs = []
            for tc in run.required_action.submit_tool_outputs.tool_calls:
                args = json.loads(tc.function.arguments)
                logs.append({"function": tc.function.name, "args": args})
                result = FUNCTION_MAP.get(tc.function.name, lambda a: "Unknown")(args)
                outputs.append({"tool_call_id": tc.id, "output": str(result)})
            client.beta.threads.runs.submit_tool_outputs(thread_id=thread_id, run_id=run.id, tool_outputs=outputs)
        elif run.status == "completed":
            messages = client.beta.threads.messages.list(thread_id=thread_id)
            return {"answer": messages.data[0].content[0].text.value, "logs": logs}
        elif run.status in ["failed","cancelled","expired"]:
            return {"answer": "Run failed: " + run.status, "logs": logs}
