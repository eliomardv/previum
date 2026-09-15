from typing import Annotated
from pydantic import BaseModel, ConfigDict, StringConstraints, model_validator

WorkerName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Registration = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
CompanyId = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=36)]


class WorkerCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    company_id: CompanyId
    name: WorkerName
    registration: Registration
    is_active: bool = True


class WorkerUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    company_id: CompanyId | None = None
    name: WorkerName | None = None
    registration: Registration | None = None
    is_active: bool | None = None

    @model_validator(mode="after")
    def validate_changes(self):
        if not self.model_fields_set:
            raise ValueError("Informe ao menos um campo para atualizar")
        if any(getattr(self, field) is None for field in self.model_fields_set):
            raise ValueError("Os campos não podem ser nulos")
        return self


class WorkerPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    tenant_id: str
    company_id: str
    name: str
    registration: str
    is_active: bool
