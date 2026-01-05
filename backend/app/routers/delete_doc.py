from fastapi import  HTTPException, Depends
from supabase import Client
from uuid import UUID
from dotenv import load_dotenv

import os
load_dotenv()
client = Client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_ROLE_KEY"))

def list_docs(db: Client = client):
    return db.storage.list_buckets()

def delete_doc(bucket_id: str, object_name: str, db: Client = client):
    db.storage.from_(bucket_id).remove(object_name)
    return {"message": "Document deleted successfully", "bucket_id": bucket_id, "object_name": object_name}

if __name__ == "__main__":
    print(delete_doc(bucket_id="kb", object_name="cce91727-05be-4479-88b8-fc4d695f48ea/CV_data_scientist__.pdf", db=client))