
import json
import os
from util import InputItem, InputItemSection
from indices import Index
from langchain.prompts import ChatPromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.schema.output_parser import StrOutputParser
from dotenv import load_dotenv

load_dotenv()

prompt = ChatPromptTemplate.from_messages([
  ('system', '''You are a creative assistant.'''),
  ('human', '''I have an index with the following description:
   {description}
   Here's a list of questions in natural language about it:
   {questions}
   Make a list of 10 additional questions that you think are relevant to the index.
   Try to be creative and think of questions that are not obvious.
   Do not number them, just write them in a list.'''),
  ])
model = ChatOpenAI(model='gpt-4')
chain = prompt | model | StrOutputParser()

datapath = './dataset/'
outpath = './output/'

questions = {}

# Ensure output directory exists
if not os.path.exists(outpath):
  os.makedirs(outpath)

files = [f for f in os.listdir(datapath) if f.endswith(".md")]
files.sort()

# Loop through all input files
for i in range(len(files)):
  item = InputItem(datapath + files[i])
  iname = item.post['index']
  index = Index(iname)
  question = '\n'.join(item.get('Question'))
  if iname not in questions:
    questions[iname] = {
      'index': json.loads(json.dumps(index.definition)),
      'questions': []
    }
  questions[iname]['questions'].append(question.strip())

for iname in questions:
  print('Generating questions for index ' + iname)
  with open(outpath + 'questions-' + iname + '.json', 'w') as f:
    f.write(json.dumps(questions[iname], indent=2))
  continue
  q = '* ' + '\n* '.join(questions[iname]['questions'])
  output = chain.invoke({
    "description": questions[iname]['description'],
    "questions": q
  })
  with open(outpath + 'questions-' + iname + '.md', 'w') as f:
    f.write(q)
    f.write('\n---\n')
    f.write(output)