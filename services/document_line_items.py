from domain.schemas import DocumentLineItemsInsert
from infra.db import supabase_client as supabase


def delete_document_line_items(document_id: str):
    try:
        return supabase.table("document_line_items").delete().eq("document_id", document_id).execute()
    except Exception as e:
        print(e)
        raise e


def insert_document_line_item(line_item: DocumentLineItemsInsert):
    insert_data = line_item.model_dump(mode="json")

    try:
        response = supabase.table("document_line_items").insert(insert_data).execute()
        if not response.data:
            raise Exception("Insert failed, make sure content is valid")
        return response
    except Exception as e:
        print(e)
        raise e
