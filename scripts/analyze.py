import pandas as pd
from sqlalchemy import create_engine

engine = create_engine("sqlite:///patents.db")

# Top inventors
query = """
SELECT inventor_id, COUNT(*) AS total
FROM relationships
GROUP BY inventor_id
ORDER BY total DESC
LIMIT 10;
"""

df = pd.read_sql(query, engine)
print(df)