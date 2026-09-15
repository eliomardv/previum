from typing import Annotated
from pydantic import BaseModel, ConfigDict, StringConstraints, model_validator

CompanyName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]


class CompanyCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: CompanyName
    is_active: bool = True


class CompanyUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: CompanyName | None = None
    is_active: bool | None = None

    @model_validator(mode="after")
    def validate_changes(self):
        if not self.model_fields_set:
            raise ValueError("Informe ao menos um campo para atualizar")
        if any(getattr(self, field) is None for field in self.model_fields_set):
            raise ValueError("Os campos não podem ser nulos")
        return self


class CompanyPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    tenant_id: str
    name: str
    is_active: bool
