import pandas as pd
from sqlalchemy import create_engine

engine = create_engine('mysql://root:12345678@127.0.0.1:3306/cloudcomputing')

df = pd.read_csv("./static/data-3.csv", sep=',', encoding='utf8')
# df['time'] = pd.to_datetime(df['time'], format='%Y-%m-%dT%H:%M:%S.%fZ')
df.to_sql('quiz4', con=engine, index=False, if_exists='append')
