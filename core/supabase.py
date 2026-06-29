import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import httpx
from supabase import create_client, Client
from supabase.lib.client_options import SyncClientOptions

load_dotenv(override=True)

supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_PUBLISHABLE_KEY')

if not supabase_url or not supabase_key:
    raise Exception('Missing SUPABASE_URL or SUPABASE_PUBLISHABLE_KEY')

_httpx_client = httpx.Client(
    transport=httpx.HTTPTransport(http2=False),
    limits=httpx.Limits(max_keepalive_connections=5, keepalive_expiry=30),
)
_supabase_options = SyncClientOptions(httpx_client=_httpx_client)

supabase_client: Client = create_client(
    supabase_url,
    supabase_key,
    options=_supabase_options,
)

