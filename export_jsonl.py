# Export the dataset in jsonl format

import os
import json
from rsgpt.prompt import get_chat_prompt
from util import InputItem
from indices import Index
from rsgpt.prompt import PromptFormat, get_system_prompt

answer_formats = [PromptFormat.JSON]
datapath = './dataset/'
outpath = './output/'

datasets = [
  ('training', [f for f in os.listdir(datapath) if f.endswith(".md") and f.startswith("t")]),
  ('validation', [f for f in os.listdir(datapath) if f.endswith(".md") and f.startswith("v")]),
]

# Ensure output directory exists
if not os.path.exists(outpath):
  os.makedirs(outpath)

# Iterate through all datasets
for dataset in datasets:
  dataset_name = dataset[0]
  files = dataset[1]
  files.sort()
  output = outpath + dataset_name + '-dataset.jsonl'
  out = open(output, 'w')
  # Loop through all input files
  for i in range(len(files)):
    item = InputItem(datapath + files[i])
    index = Index(item.post['index'])
    question = '\n'.join(item.get('Question'))
    answer = item.get_code('JSON')
    prompt = get_chat_prompt(PromptFormat.JSON)
    messages = prompt.format_messages(context=index.definition, input=question)
    system = messages[0].content
    user = messages[1].content
    row = {
      'messages': [
        {
          'role': 'system',
          'content': system,
        },
        {
          'role': 'user',
          'content': user
        },
        {
          'role': 'assistant',
          'content': answer
        }
      ]
    }
    out.write(json.dumps(row) + '\n')
  out.close()
