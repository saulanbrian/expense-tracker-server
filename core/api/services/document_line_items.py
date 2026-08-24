from core.api.schemas import DocumentLineItemsInsert
from core.supabase import supabase_client as supabase


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
