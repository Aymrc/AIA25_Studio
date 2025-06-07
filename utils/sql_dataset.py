import sqlite3
import os

def get_top_low_carbon_high_gfa(
    db_path=None,
    table_name="design_data",
    min_gfa=2000,
    max_results=5
):
    # 🔁 Get absolute path relative to this file
    if db_path is None:
        base_dir = os.path.dirname(os.path.dirname(__file__))  # project root
        db_path = os.path.join(base_dir, "knowledge", "design_data.db")

    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database not found at {db_path}")

    query = f'''
        SELECT * FROM {table_name}
        WHERE CAST("GFA" AS REAL) > ?
        AND "GWP total/m²GFA" IS NOT NULL
        ORDER BY CAST("GWP total/m²GFA" AS REAL) ASC
        LIMIT ?
    '''

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(query, (min_gfa, max_results))
    rows = cursor.fetchall()
    column_names = [description[0] for description in cursor.description]
    conn.close()

    result = [dict(zip(column_names, row)) for row in rows]
    return result
