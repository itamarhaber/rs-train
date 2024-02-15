import json
from typing import Tuple
from redis import Redis
from redis.commands.search.aggregation import AggregateRequest, AggregateResult
from redis.commands.search import reducers
from .util import pairs_to_dict, str_if_bytes, quote_if_necessary, str_to_numeric

def get_index_list(conn: Redis) -> [str]:
  res = conn.execute_command('FT._LIST')
  res = list(map(str_if_bytes, res))
  res.sort()
  return res

def get_create_statement(info: dict) -> str:
  s = f'FT.CREATE {info["index_name"]} '
  d = pairs_to_dict(info['index_definition'], decode_keys=True, decode_string_values=True)
  s += f"ON {d['key_type']} PREFIX {len(d['prefixes'])} "
  for prefix in map(str_if_bytes,d['prefixes']):
    s += f'{quote_if_necessary(prefix)} '

  # TODO: add all index features
  if 'filter' in d:
    s += f"FILTER {quote_if_necessary(d['filter'])} "

  s += "SCHEMA "
  for a in info['attributes']:
    d = pairs_to_dict(a, decode_keys=True, decode_string_values=True)
    s += f"{quote_if_necessary(d['identifier'])} "
    if d['identifier'] != d['attribute']:
      s += f"AS {quote_if_necessary(d['attribute'])} "
    s += f"{d['type']} "
  return s[:-1]

def get_index_schema(conn: Redis, index_name: str) -> [Tuple[str, str]]:
  info = conn.ft(index_name=index_name).info()
  schema = []
  for a in info['attributes']:
    d = pairs_to_dict(a, decode_keys=True, decode_string_values=True)
    schema.append((d['attribute'], d['type']))
  return schema

def get_attribute_stats(conn: Redis, info: dict) -> dict:
  reply = {}
  index = info['index_name']
  for attrib in info['attributes']:
    stats = {}
    attr = pairs_to_dict(attrib, decode_keys=True, decode_string_values=True)
    a = '@' + attr['attribute']

    if attr['type'] in ['TEXT', 'TAG', 'NUMERIC', 'GEO']:
      # Distinct values
      req = AggregateRequest('*').group_by([a], reducers.count())
      res = conn.ft(index_name=index).aggregate(req)
      stats['cardinality'] = len(res.rows)
      # Top values
      req = AggregateRequest('*').group_by([a], reducers.count().alias('count')).sort_by('@count', desc=True, max=10)
      res = conn.ft(index_name=index).aggregate(req)
      stats['top'] = [str_if_bytes(r[1]) for r in res.rows]
    if attr['type'] == 'TEXT':
      pass
    elif attr['type'] == 'TAG':
      pass
    elif attr['type'] == 'NUMERIC':
      # Min value
      req = AggregateRequest('*').group_by([], reducers.min(a))
      res = conn.ft(index_name=index).aggregate(req)
      stats['minimum'] = str_to_numeric(res.rows[0][1])
      # Max value
      req = AggregateRequest('*').group_by([], reducers.max(a))
      res = conn.ft(index_name=index).aggregate(req)
      stats['maximum'] = str_to_numeric(res.rows[0][1])
      # Average value
      req = AggregateRequest('*').group_by([], reducers.avg(a))
      res = conn.ft(index_name=index).aggregate(req)
      stats['average'] = str_to_numeric(res.rows[0][1])
      # Median value
      req = AggregateRequest('*').group_by([], reducers.quantile(a, 0.5))
      res = conn.ft(index_name=index).aggregate(req)
      stats['median'] = str_to_numeric(res.rows[0][1])
      # Standard deviation
      req = AggregateRequest('*').group_by([], reducers.stddev(a))
      res = conn.ft(index_name=index).aggregate(req)
      stats['stddev'] = str_to_numeric(res.rows[0][1])
    elif attr['type'] == 'GEO':
      pass
    reply[attr['attribute']] = stats
  return reply

def get_index_definition(conn: Redis, index_name: str) -> dict:
  info = conn.ft(index_name=index_name).info()
  return {
    'index_name': info['index_name'],
    'num_docs': info['num_docs'],
    'create_statement': get_create_statement(info),
    'attribute_stats': get_attribute_stats(conn, info),
  }

def get_indices(conn: Redis):
  reply = []
  for index_name in get_index_list(conn):
    reply.append(get_index_definition(conn, index_name))
  return reply

if __name__ == '__main__':
  conn = Redis()
  print(json.dumps(get_indices(conn), indent=2))