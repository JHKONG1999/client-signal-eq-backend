from pydantic import BaseModel
from typing import Optional

class OrganizationModel(BaseModel):
    organization_id: Optional[int] = None
    organization_name: str

class UpdateOrganizationModel(BaseModel):
    organization_name: Optional[str] = None
