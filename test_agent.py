from rsgpt.agent import invoke_agent

if __name__ == "__main__":
  messages = [
    'Which indexes can I query?',
    'How many biters are there?',
    'Describe the schema',
    "Based on the boroughs, which city is that?",
  ]
  chat_history = []
  model = 'ft:gpt-3.5-turbo-1106:personal::8WtvQgm8'
  for message in messages:
    res = invoke_agent(model, 0, message, chat_history)
    chat_history.append([res['input'], res['output']])
    print(([res['input'], res['output']]))