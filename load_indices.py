# Load data and indices into Redis

from indices import load_bites_data, load_cars_data, load_cities_data
from redis import Redis

r = Redis(encoding='utf-8', decode_responses=True)
r.flushall()

load_bites_data(r)
load_cars_data(r)
load_cities_data(r)
