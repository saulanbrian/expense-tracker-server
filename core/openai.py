from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise Exception("Missing GROQ_API_KEY")

groq = OpenAI(
    api_key=api_key,
    base_url="https://api.groq.com/openai/v1",
)
