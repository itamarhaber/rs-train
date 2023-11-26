import os
import pandas as pd
from redis import Redis
from redis.commands.search.field import TextField, NumericField, TagField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def load_data(r: Redis) -> None:
  print("Loading bites", end="")
  # Get the local directory of this file
  dir_path = os.path.dirname(os.path.realpath(__file__))
  # Load the data
  df = pd.read_csv(f'{dir_path}/data.csv')
  # Delete the columns that are not needed
  df = df.drop(['Species'], axis=1)
  # Delete rows where the Age column is NaN
  df = df.dropna(subset=['Age'])
  # Delete rows where the Age column is not numeric
  df = df[df['Age'].apply(lambda x: is_number(x))]
  # Cast bool SpayNeuter column to string
  df['SpayNeuter'] = df['SpayNeuter'].astype(str)
  # Convert the DateOfBite column from string to integer timestamp
  df['DateOfBite'] = pd.to_datetime(df['DateOfBite']).astype(int) / 10**9
  df['DateOfBite'] = pd.to_numeric(df['DateOfBite'], downcast='integer')

  # Create the index
  schema = (
    NumericField("DateOfBite", as_name="DateOfBite"),
    TextField("Breed", as_name="Breed"),
    NumericField("Age", as_name="Age"),
    TagField("Gender", as_name="Gender"),
    TagField("SpayNeuter", as_name="SpayNeuter"),
    TagField("Borough", as_name="Borough"),
  )
  r.ft('bites').create_index(schema, definition=IndexDefinition(prefix=["incident:"], index_type=IndexType.HASH))

  # Iterate over the rows of the dataframe and add them to Redis
  for index, row in df.iterrows():
      if index % 100 == 0:
        print(".", end="")
      key = f'incident:{index+1}'
      r.hset(key, mapping=row.to_dict())

  print(" Done")
  