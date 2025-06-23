import pandas as pd
import sqlite3
import os

def convert_csv_to_sqlite(csv_path="knowledge/dataset.csv",
                          db_path="knowledge/design_data.db",
                          table_name="design_data"):
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV not found at: {csv_path}")

    df = pd.read_csv(csv_path)

    # Optional: Strip whitespace from column names
    df.columns = [col.strip() for col in df.columns]

    conn = sqlite3.connect(db_path)
    df.to_sql(table_name, conn, if_exists="replace", index=False)
    conn.commit()
    conn.close()

    print(f"✅ SQLite DB created at: {db_path} with table: {table_name}")

if __name__ == "__main__":
    convert_csv_to_sqlite()
import pandas as pd
import sqlite3
import os

def convert_csv_to_sqlite(csv_path="knowledge/dataset.csv",
                          db_path="knowledge/design_data.db",
                          table_name="design_data"):
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV not found at: {csv_path}")

    df = pd.read_csv(csv_path)

    # Optional: Strip whitespace from column names
    df.columns = [col.strip() for col in df.columns]

    conn = sqlite3.connect(db_path)
    df.to_sql(table_name, conn, if_exists="replace", index=False)
    conn.commit()
    conn.close()

    print(f"✅ SQLite DB created at: {db_path} with table: {table_name}")

if __name__ == "__main__":
    convert_csv_to_sqlite()
