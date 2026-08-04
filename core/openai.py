import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(override=True)

api_key = os.getenv("OPENROUTER_API_KEY")

if not api_key:
    raise Exception("Missing OPENROUTER_API_KEY")

groq = OpenAI(
    api_key=api_key,
    base_url="https://openrouter.ai/api/v1",
)
