import os
from util import InputItem, InputItemSection
from redis import Redis

path = './output/'

# Get all files in the dataset folder that end with .md
files = [f for f in os.listdir(path) if f.endswith(".md")]
files.sort()

conn = Redis(decode_responses=True)

# Loop through all input files
for i in range(len(files)):
  item = InputItem(path + files[i])
  for section in item.sections:
    if section.name.endswith('ARGS') and not section.name.startswith('gpt'):
      args = eval(item.get_code(section.name))
      try:
        res = conn.execute_command(*args)
      except Exception as e:
        res = e
      section.content += [
        '',
        f'## {section.name}-res',
        '',
        '```',
        str(res),
        '```'
      ]
    elif section.name.endswith('-res'):
      item.delete(section.name)
  item.dump()