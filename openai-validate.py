
import os
from util import InputItem, InputItemSection
from indices import Index
from rsgpt.prompt import PromptFormat, get_chat_prompt
from langchain.chat_models import ChatOpenAI
from langchain.schema.output_parser import StrOutputParser
from dotenv import load_dotenv

load_dotenv()

answer_formats = [PromptFormat.JSON]
model_names = ['ft:gpt-3.5-turbo-1106:personal::8VK9DJbK']
chains = []

for model_name in model_names:
  for answer_format in answer_formats:
    model = ChatOpenAI(model=model_name, temperature=0)
    prompt = get_chat_prompt(answer_format)
    chain = (f'{model_name}-{answer_format.name}', (
      prompt |
      model |
      StrOutputParser()
    ))
    chains.append(chain)

datapath = './dataset/'
outpath = './output/'

# Ensure output directory exists
if not os.path.exists(outpath):
  os.makedirs(outpath)

# Get all files in the dataset folder that end with .md and start with a 'v'(alidate)
files = [f for f in os.listdir(datapath) if f.endswith(".md") and f.startswith("v")]
files.sort()

# Loop through all input files
for i in range(len(files)):
  item = InputItem(datapath + files[i])
  index = Index(item.post['index'])
  question = '\n'.join(item.get('Question'))
  answer = repr(item.get('ARGS'))
  for c in chains:
    chain_name = c[0]
    chain = c[1]
    print(chain_name)
    output = chain.invoke({
      "input": question,
      "context": index.describe()
    })
    item.append(InputItemSection(chain_name, [
      '',
      '```python',
      output,
      '```']))
  item.dump(outpath + files[i])