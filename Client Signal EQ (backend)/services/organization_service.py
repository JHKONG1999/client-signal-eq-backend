from db import organization_collection
from datetime import datetime
from fastapi import HTTPException

def create_organization(data: dict):
    latest = organization_collection.find_one({}, sort=[("organization_id", -1)])
    next_id = latest["organization_id"] + 1 if latest else 1
    data["organization_id"] = next_id
    data["created_date"] = datetime.utcnow()

    result = organization_collection.insert_one(data)
    return str(result.inserted_id)

def get_all_organizations():
    return [
        {**org, "_id": str(org["_id"])}
        for org in organization_collection.find({})
    ]

def get_organization_by_id(org_id: int):
    org = organization_collection.find_one({"organization_id": org_id})
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    org["_id"] = str(org["_id"])
    return org

def update_organization(org_id: int, update_data: dict):
    update_data.pop("created_date", None)
    update_data["updated_at"] = datetime.utcnow()
    result = organization_collection.update_one(
        {"organization_id": org_id},
        {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Organization not found")
    return {"message": "Organization updated successfully"}

def delete_organization(org_id: int):
    result = organization_collection.delete_one({"organization_id": org_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Organization not found")
    return {"message": "Organization deleted successfully"}
