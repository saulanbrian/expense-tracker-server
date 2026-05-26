from core.supabase import supabase_client as supabase

async def ingest_document(ctx,document_id: str):
    try:
        response = supabase.table("documents").select("*").eq("id",document_id).execute()
    except Exception as e:
        raise Exception(e)
    return response
