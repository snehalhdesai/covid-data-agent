import os
import time
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

# Step 1: Create Assistant (once)
assistant = client.beta.assistants.create(
    name="COVID Data Analyst",
    instructions="You are a data analyst expert on US COVID-19 data. The dataset covers 2020-2021 with columns: date (YYYYMMDD integer), state (2-letter), positive, death, hospitalizedCurrently, hospitalizedCumulative, deathIncrease, positiveIncrease. Answer questions clearly and concisely.",
    model="gpt-3.5-turbo"
)
print("Assistant created:", assistant.id)

# Step 2: Create Thread (persistent conversation)
thread = client.beta.threads.create()
print("Thread created:", thread.id)
print("\nCOVID Assistant ready! Type quit to exit.\n")

while True:
    question = input("You: ")
    if question.lower() == "quit":
        break

    # Step 3: Add message to thread
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=question
    )

    # Step 4: Run assistant on thread
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id
    )

    # Step 5: Wait for completion
    while run.status in ["queued", "in_progress"]:
        time.sleep(1)
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
        )

    # Step 6: Get response
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    answer = messages.data[0].content[0].text.value
    print("\nAgent:", answer, "\n")
