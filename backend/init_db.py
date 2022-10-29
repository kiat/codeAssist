import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host="localhost",
    database="codeassist",
    user="rickywoodruff",
    password=os.getenv("DB_PASSWORD")
)

cur = conn.cursor()

print(cur.execute("select * from information_schema.columns where table_name='students'"))

conn.commit()
cur.close()
conn.close()