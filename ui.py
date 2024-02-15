import gradio as gr
from redis import Redis
from openai import OpenAI
from dotenv import load_dotenv
from rsgpt.agent import invoke_agent
from rsgpt.db import get_indices as db_get_indices
load_dotenv()

def get_models():
  """Returns a list of fine-tuned (and selected others) models sorted by creation date."""
  client = OpenAI()
  models = [m.id for m in client.models.list() if m.id.startswith('ft:')]
  sorted_models = []
  for m in models:
    model = client.models.retrieve(m)
    sorted_models.append((model.id, model.created))
  sorted_models.sort(key=lambda x: x[1], reverse=True)
  models = [f[0] for f in sorted_models]
  models += ['gpt-4-1106-preview', 'gpt-3.5-turbo-1106']
  return models

def gpt(message, history, model_name, temperature):
  output, steps = invoke_agent(model_name, temperature, message, history)
  return output

def vote(data: gr.LikeData):
  if data.liked:
    print("You upvoted this response: " + data.value)
  else:
    print("You downvoted this response: " + data.value)

def get_chat_interface(conn: Redis) -> gr.Interface:
  models = get_models()

  with gr.Blocks() as ui:
    with gr.Accordion("Settings", open=False):
      with gr.Row():
        model_name = gr.Dropdown(models, value=models[0], label="Model name")
        temperature = gr.Slider(minimum=0, maximum=1, value=0, step=0.1, label="Temperature")

    chatbot = gr.Chatbot(
      show_label=False,
      layout='panel',
      render=False,
      show_copy_button=True,
    )
    chatbot.like(vote, None, None)
    chat_interface = gr.ChatInterface(
      gpt,
      chatbot=chatbot,
      additional_inputs=[model_name, temperature],
    )
  return ui

if __name__ == '__main__':
  conn = Redis(decode_responses=True)
  ui = get_chat_interface(conn)
  ui.queue().launch()
