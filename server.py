from fastapi import FastAPI
from ui import get_chat_interface
from gradio import mount_gradio_app
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI()

# Chatbot interface
chat = get_chat_interface(None)
app = mount_gradio_app(app=app, blocks=chat, path="/")

if __name__ == '__main__':
  import uvicorn
  uvicorn.run(app, host='127.0.0.1', port=8000)
