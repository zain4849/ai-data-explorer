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
        clean_sql = sql.strip().rstrip(";").strip()
        return self.conn.execute(clean_sql).fetchdf()

    def _quote_ident(self, ident: str) -> str:
        # Escape embedded quotes for safe quoted identifiers.
        safe_ident = ident.replace('"', '""')
        return f'"{safe_ident}"'

    def get_schema(self):
        # if I didn't add .fetchall() then result would be a Cursor object (Cursor object does't contain the data, it's a pointer to the data).
        result = self.conn.execute("PRAGMA table_info(data)").fetchall() # .fetchall() returns a list[tuple(s)]
        #          cid, name, type, notnull, dflt_value, pk
        # result = [(0, 'id', 'INTEGER', 0,  None, 1),
        #           (1, 'username', 'TEXT', 1, None, 0),
        #           (2, 'age', 'INTEGER', 0, 18, 0), 
        #           (3, 'status', 'TEXT', 0, None, 0)]
        columns = [{"name": row[1], "type": row[2]} for row in result]
        # columns = [{
        #    "name": "id",
        #    "type": "INTEGER",
        # }, {
        #    "name": "username",
        #    "type": "TEXT",
        # }, {
        #    "name": "age",
        #    "type": "INTEGER",
        # }, {
        #    "name": "status",
        #    "type": "TEXT",
        #    "known_values": ["pending", "approved", "rejected"]
        # }]
        #

        # Add representative values for low-cardinality text columns to reduce LLM value hallucinations.
        for col in columns:
            col_type = col["type"].upper()
            if "CHAR" not in col_type and "TEXT" not in col_type and "VARCHAR" not in col_type: # only process text cols
                continue

            col_name = col["name"]
            ident = self._quote_ident(col_name) # ident = '"status"', cuz in PostgreSQL status is keyword
            distinct_count = self.conn.execute(
                f"SELECT COUNT(DISTINCT {ident}) FROM data WHERE {ident} IS NOT NULL"
            ).fetchone()[0] # fetchone() = [(3,)], [0] -> 3
            # cuz distinct vals are: pending, approved, rejected

            if distinct_count <= 30:
                sample_values = self.conn.execute(
                    f"""
                    SELECT {ident}
                    FROM data
                    WHERE {ident} IS NOT NULL
                    GROUP BY {ident}
                    ORDER BY COUNT(*) DESC, {ident}
                    LIMIT 20
                    """
                ).fetchall()
                # [('pending',), ('approved',), ('rejected',)]

                col["known_values"] = [row[0] for row in sample_values]
                # new key = 'known_values' & value = ['pending', 'approved', 'rejected']

        # columns = [{
        #    "name": "id",
        #    "type": "INTEGER",
        # }, {
        #    "name": "username",
        #    "type": "TEXT",
        # }, {
        #    "name": "age",
        #    "type": "INTEGER",
        # }, {
        #    "name": "status",
        #    "type": "TEXT",
        #    "known_values": ["pending", "approved", "rejected"]
        # }]
        return columns

db = Database()
