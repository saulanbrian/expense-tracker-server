from core.api.schema_public_latest import DocumentsUpdate, Documents
from pydantic import ValidationError
from core.supabase import supabase_client as supabase


def update_document(document_id: str, updates: DocumentsUpdate):
    update_data = updates.model_dump(exclude_unset=True, mode="json")

    if not update_data:
        raise ValidationError("No data provided to update")

    try:
        response = (
            supabase.table("documents")
            .update(update_data)
            .eq("id", document_id)
            .execute()
        )
        if not response.data:
            raise Exception("Update failed: no data returned")
        return response
    except Exception as e:
        raise e


def get_document(document_id: str):
    try:
        response = (
            supabase.table("documents").select("*").eq("id", document_id).execute()
        )
        return response
    except Exception as e:
        print(e)
        raise e


def insert_document(document: Documents):
    return (
        supabase.table("documents").insert(document.model_dump(mode="json")).execute()
    )


def download_document_file(path: str):
    return supabase.storage.from_("documents").download(path)
