from fastapi import APIRouter
from typing import List
from models.organization_model import OrganizationModel, UpdateOrganizationModel
from services.organization_service import (
    create_organization,
    get_all_organizations,
    get_organization_by_id,
    update_organization,
    delete_organization
)

router = APIRouter()

@router.post("/api/auth/organization", response_model=dict)
def create_organization_route(data: OrganizationModel):
    inserted_id = create_organization(data.dict())
    return {"inserted_id": inserted_id}

@router.get("/api/auth/organization", response_model=List[OrganizationModel])
def get_all_organizations_route():
    return get_all_organizations()

@router.get("/api/auth/organization/{org_id}", response_model=OrganizationModel)
def get_organization_route(org_id: int):
    return get_organization_by_id(org_id)

@router.put("/api/auth/organization/{org_id}", response_model=dict)
def update_organization_route(org_id: int, update: UpdateOrganizationModel):
    return update_organization(org_id, update.dict(exclude_unset=True))

@router.delete("/api/auth/organization/{org_id}", response_model=dict)
def delete_organization_route(org_id: int):
    return delete_organization(org_id)
