from sqlalchemy import create_engine, text, inspect
from config import DATABASE_URL

engine = create_engine(DATABASE_URL)

def get_schema():
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    schema = {}
    for table in tables:
        cols = [c["name"] + " (" + str(c["type"]) + ")" for c in inspector.get_columns(table)]
        schema[table] = cols
    return schema

def run_query(sql, params=None):
    with engine.connect() as conn:
        result = conn.execute(text(sql), params or {})
        rows = result.fetchall()
        cols = result.keys()
        return [dict(zip(cols, row)) for row in rows]

def get_hospitalizations(state, date):
    rows = run_query(
        "SELECT state, date, hospitalizedIncrease, hospitalizedCurrently FROM states_history WHERE state=:s AND date=:d",
        {"s": state, "d": date}
    )
    return rows if rows else "No data found"

def get_positive_cases(state, date):
    rows = run_query(
        "SELECT state, date, positiveIncrease, positive FROM states_history WHERE state=:s AND date=:d",
        {"s": state, "d": date}
    )
    return rows if rows else "No data found"

def get_top_states(metric, limit=5):
    allowed = ["death", "positive", "hospitalizedCumulative", "deathIncrease", "positiveIncrease"]
    if metric not in allowed:
        return "Invalid metric"
    rows = run_query(
        f"SELECT state, MAX({metric}) as value FROM states_history GROUP BY state ORDER BY value DESC LIMIT :l",
        {"l": limit}
    )
    return rows if rows else "No data found"

def get_mental_health_by_gender(gender):
    rows = run_query(
        "SELECT gender, AVG(stress_level) as avg_stress, AVG(anxiety_level) as avg_anxiety, AVG(depression_label) as avg_depression, AVG(addiction_level) as avg_addiction FROM teen_mental_health WHERE gender=:g GROUP BY gender",
        {"g": gender}
    )
    return rows if rows else "No data found"

def get_mental_health_by_age(age):
    rows = run_query(
        "SELECT age, AVG(stress_level) as avg_stress, AVG(anxiety_level) as avg_anxiety, AVG(sleep_hours) as avg_sleep, AVG(daily_social_media_hours) as avg_social_media FROM teen_mental_health WHERE age=:a",
        {"a": age}
    )
    return rows if rows else "No data found"

def get_top_mental_health_stats(metric, limit=5):
    allowed = ["stress_level", "anxiety_level", "addiction_level", "depression_label", "daily_social_media_hours"]
    if metric not in allowed:
        return "Invalid metric"
    rows = run_query(
        f"SELECT age, gender, platform_usage, {metric} FROM teen_mental_health ORDER BY {metric} DESC LIMIT :l",
        {"l": limit}
    )
    return rows if rows else "No data found"
