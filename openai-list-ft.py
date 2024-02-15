from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI()

models = []
for model in models:
  try:
    client.models.delete(model)
  except Exception as e:
    print(e)

import datetime
ft = []
for m in client.models.list():
  if m.id.startswith('ft:'):
    model = client.models.retrieve(m.id)
    ft.append((model.id, model.created))
ft.sort(key=lambda x: x[1], reverse=True)
ft = [f[0] for f in ft]
print(ft)

for f in client.files.list():
  break
  print(f.id, f.purpose)
  if f.purpose.startswith('fine-tune'):
    client.files.delete(f.id)