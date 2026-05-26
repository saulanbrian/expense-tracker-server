import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_async_client, AsyncClient, Client, create_client

load_dotenv()

supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_PUBLISHABLE_KEY')

if not supabase_url or not supabase_key:
    raise Exception('Missing SUPABASE_URL or SUPABASE_PUBLISHABLE_KEY')

supabase_client: Client = create_client(
        supabase_url,
        supabase_key
)

