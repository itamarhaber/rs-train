import os
import pandas as pd
from redis import Redis
from redis.commands.search.field import TextField, NumericField, TagField, GeoField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def load_data(r: Redis) -> None:
  print("Loading cities", end="")
  # Get the local directory of this file
  dir_path = os.path.dirname(os.path.realpath(__file__))
  # Load the data
  df = pd.read_csv(f'{dir_path}/data.csv')

  df['capital'] = df['capital'].fillna('')
  df['admin_name'] = df['admin_name'].fillna('')
  df['population'] = df['population'].fillna(0)

  # Create a new location column with the string representation of the lng and lat columns
  df['location'] = df['lng'].astype(str) + ',' + df['lat'].astype(str)
  df = df.drop(columns=['lng', 'lat'])

  # Create the index
  schema = (
    TextField("city_ascii", as_name="city"),
    GeoField("location", as_name="location"),
    TextField("country", as_name="country"),
    TextField("admin_name", as_name="admin_name"),
    TagField("capital", as_name="capital"),
    NumericField("population", as_name="population"),
  )
  r.ft('cities').create_index(schema, definition=IndexDefinition(prefix=["city:"], index_type=IndexType.HASH))

  # Iterate over the rows of the dataframe and add them to Redis
  for index, row in df.iterrows():
      if index % 100 == 0:
        print(".", end="")
      key = f'city:{row["id"]}'
      r.hset(key, mapping=row.to_dict())

  print(" Done")
