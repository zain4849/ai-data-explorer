from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
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
    try:

        # Read CSV into pandas
        df = pd.read_csv(file.file)
        
        # Store in DuckDB
        db.execute("CREATE OR REPLACE TABLE data AS SELECT * FROM df")

        # Confirm storage by querying rwo count
        row_count = db.execute("SELECT (*) FROM data").fetchall()[0][0]
        col_count = len(df.columns)
        print(f"Rows stored in DuckDB: {row_count}")
        

        # Return first 5 rows as JSON
        return JSONResponse(content={
            "success": True,
            "message": f"File uploaded successfully",
            "rows": row_count,
            "columns": col_count,
            "column_names": list(df.columns),
            "sample_data": dataframe_to_json_records(df) # df.head(5).to_dict(orient="records")            
            })

    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "message": f"Error uploading file: {str(e)}"
            }
        )
