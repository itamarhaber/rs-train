import json
from redis import Redis
from pprint import pprint

conn = Redis(encoding='utf-8', decode_responses=True, protocol=3)
inames = conn.execute_command('FT._LIST')

for iname in inames:
  idxdef = conn.ft(iname).info()
  cleandef = {
    'index_name': idxdef['index_name'],
    'key_type': idxdef['index_definition']['key_type'],
    'attributes': idxdef['attributes'],
  }
  print(json.dumps(cleandef, indent=2))
  break