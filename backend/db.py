import duckdb
import pandas as pd

class Database:
    def __init__(self):
        self.conn = duckdb.connect(database=':memory:') # In-memory DuckDB
    
    def load_dataframe(self, df: pd.DataFrame):
        # Store in DuckDB, here implicitly creating a table named 'data' is made with the contents of the DataFrame
        self.conn.execute("CREATE OR REPLACE TABLE data AS SELECT * FROM df")
        
    def query(self, sql: str):
        '''
        .fetchdf(): This tells DuckDB: "Take those internal results, convert the columns back into Python types, and wrap them in a pd.DataFrame container."

        return: You now have a standard Pandas object that you can use for .head(), .plot(), or further Python analysis.
        '''
        return self.conn.execute(sql).fetchdf()
    
    db = Database()