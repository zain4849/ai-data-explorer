from fastapi import FastAPI, UploadFile, File, Query
from fastapi.responses import JSONResponse

from .db import db # When Python imports a module (here db.py), it runs the top-level code (db = Database()) of that module once.
from .sql_validator import validate_sql
from .logger_config import logger 
from .llm import generate_sql, generate_insights
from .charting.charting import generate_chart

import pandas as pd

app = FastAPI()


# Convert to object dtype first so None can replace NaN in numeric columns.
def dataframe_to_json_records(df: pd.DataFrame, limit: int = 5):
    safe_df = df.head(limit).astype(object).where(pd.notna(df.head(limit)), None)
    return safe_df.to_dict(orient="records")

@app.post("/upload_csv")
async def upload_csv(file: UploadFile = File(...)):
    df = pd.read_csv(file.file) # Read CSV into pandas
    db.load_dataframe(df) # After this DuckDB has a table named data w/ contents of df
    return dataframe_to_json_records(df) # Return first 5 rows as JSON records for confirmation to client
    '''
    [
        {"Name": "John", "Age": 25, "City": "New York"},
        {"Name": "Alice", "Age": 30, "City": "Paris"}
    ]
    '''

@app.get("/query")
async def query_data(nl_query: str = Query(...)):
    # http://localhost:8000/query?nl_query=top%2010%20customers

    schema = db.get_schema()
    sql = generate_sql(nl_query, schema)

    logger.info(f"Generated SQL: {sql}")

    validate_sql(sql)

    # At this point I have the result not the raw table the user uploaded at the start
    try:
        df = db.query(sql) # df contains the results of the SQL query as a pandas DataFrame

        insights = generate_insights(df.head(10).to_string()) # Generate insights based on a preview of the data
        chart_html = generate_chart(df)

        return {
            "sql": sql,
            "result": dataframe_to_json_records(df, 50),
            "insights": insights,
            "chart_html": chart_html
        }
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e), "sql": sql})
