import os
import json

class Index(object):
  """A class that represents a RediSearch index in the database."""

  def __init__(self, name: str):
    self.name = name
    dir_path = os.path.dirname(os.path.realpath(__file__))
    self.path = f'{dir_path}/{self.name}/index_definition.json'
    if not os.path.exists(self.path):
      raise FileNotFoundError(f"Index definition file {self.path} not found")
    with open(self.path) as f:
      self.definition = json.load(f)

  def __repr__(self):
    return f"<Index {self.name}>"

  def describe(self) -> str:
    """Returns a string describing the index."""
    s = f'''Index name: {repr(self.definition['name'])}
Index description: "{self.definition['description']}"
The index's schema consists of the following fields:'''

    for a in self.definition['attributes']:
      s += f'\n* The field {repr(a["name"])} is of type `{a["type"]}` and described as "{a["description"]}"'
      if a["type"] == 'TAG' and 'samples' in a:
        s += f' with these possible values: {", ".join([repr(v) for v in a["samples"]])}'

    return s
