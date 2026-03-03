from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from db import db
import pandas as pd
import duckdb

app = FastAPI()
db = duckdb.connect(database=':memory:') # In-memory DuckDB


def dataframe_to_json_records(df: pd.DataFrame, limit: int = 5):
    # Convert to object dtype first so None can replace NaN in numeric columns.
    safe_df = df.head(limit).astype(object).where(pd.notna(df.head(limit)), None)
    return safe_df.to_dict(orient="records")

@app.post("/upload_csv/")
async def upload_csv(file: UploadFile = File(...)):
    df = pd.read_csv(file.file) # Read CSV into pandas
    db.load_dataframe(df) # After this DuckDB has a table named data w/ contents of df
    return df.head().to_dict(orient="records") # Return first 5 rows as JSON records for confirmation to client

@app.get("/query/")
async def query_data(nl_query: str = Query(...)):
    # http://localhost:8000/query?nl_query=top%2010%20customers
    pass

