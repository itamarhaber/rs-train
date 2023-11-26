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
  print("Loading cars", end="")
  # Get the local directory of this file
  dir_path = os.path.dirname(os.path.realpath(__file__))
  # Load the data
  df = pd.read_csv(f'{dir_path}/data.csv')
  # Delete the columns that are not needed
  df = df.drop([
    'Used/New', 'DealType', 'ComfortRating', 'InteriorDesignRating', 'ConsumerRating', 'ConsumerReviews',
    'PerformanceRating', 'ValueForMoneyRating', 'ExteriorStylingRating', 'SellerRating', 'SellerReviews',
    'ReliabilityRating', 'ExteriorColor', 'InteriorColor', 'Drivetrain', 
    'MinMPG', 'MaxMPG', 'FuelType', 'Transmission', 'Engine', 'VIN', 'Stock#'
  ], axis=1)
  # Strip the dollar and commas from the price column
  df['Price'] = df['Price'].str.replace('$', '').str.replace(',', '')
  # Delete rows where the price column is not numeric
  df = df[df['Price'].apply(lambda x: is_number(x))]
  # Convert the price column to numeric
  df['Price'] = df['Price'].astype(int)

  # Create the index
  schema = (
    NumericField("Year", as_name="Year"),
    TagField("Make", as_name="Make"),
    TagField("Model", as_name="Model"),
    NumericField("Price", as_name="Price"),
    TagField("SellerType", as_name="SellerType"),
    TextField("SellerName", as_name="SellerName"),
    TagField("State", as_name="State"),
    NumericField("Mileage", as_name="Mileage"),
  )
  r.ft('cars').create_index(schema, definition=IndexDefinition(prefix=["listing:"], index_type=IndexType.HASH))

  # Iterate over the rows of the dataframe and add them to Redis
  for index, row in df.iterrows():
      if index % 100 == 0:
        print(".", end="")
      key = f'listing:{index+1}'
      r.hset(key, mapping=row.to_dict())
  print(" Done")
