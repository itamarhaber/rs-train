from typing import Union

def str_if_bytes(value: Union[str, bytes]) -> str:
  return (
    value.decode("utf-8", errors="replace") if isinstance(value, bytes) else value
  )

def pairs_to_dict(response, decode_keys=False, decode_string_values=False):
  """Create a dict given a list of key/value pairs"""
  if response is None:
    return {}
  if decode_keys or decode_string_values:
    # the iter form is faster, but I don't know how to make that work
    # with a str_if_bytes() map
    keys = response[::2]
    if decode_keys:
      keys = map(str_if_bytes, keys)
    values = response[1::2]
    if decode_string_values:
      values = map(str_if_bytes, values)
    return dict(zip(keys, values))
  else:
    it = iter(response)
    return dict(zip(it, it))

def quote_if_necessary(value: str) -> str:
  """Quote a string if it contains spaces"""
  if " " in value:
    return f'"{value}"'
  return value

def str_to_numeric(value: Union[str, bytes]) -> Union[int, float]:
  """Convert a string to an int or float if possible"""
  if "." in str_if_bytes(value):
    return float(value)
  return int(value)
