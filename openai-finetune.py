from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI()
training = client.files.create(
  file=open('./output/training-dataset.jsonl', 'rb'),
  purpose='fine-tune'
)
validation = client.files.create(
  file=open('./output/validation-dataset.jsonl', 'rb'),
  purpose='fine-tune'
)


j = client.fine_tuning.jobs.create(
  training_file=training.id,
  validation_file=validation.id,
  model="gpt-3.5-turbo-1106",
)
print(training.id, validation.id, j.id)