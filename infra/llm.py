import os

from dotenv import load_dotenv
from google import genai
from openai import OpenAI

load_dotenv(override=True)

openrouter_key = os.getenv("OPENROUTER_API_KEY")
gemini_key = os.getenv("GEMINI_API_KEY")

if not openrouter_key or not gemini_key:
    raise Exception("Missing OPENROUTER_API_KEY or GEMINI_API_KEY")

openrouter_client = OpenAI(
    api_key=openrouter_key,
    base_url="https://openrouter.ai/api/v1",
)

gemini_client = genai.Client(api_key=gemini_key)
