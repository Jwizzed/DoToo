import datetime

from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    # Common configuration for all schemas
    model_config = ConfigDict(
        from_attributes=True,  # Allow creating schemas from ORM objects
        populate_by_name=True,  # Allow using alias for field names
    )


class TunedModel(BaseSchema):
    # If I need further common config like alias generators
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )


class IDModelMixin(BaseModel):
    id: int


class DateTimeModelMixin(BaseModel):
    created_at: datetime.datetime
    updated_at: datetime.datetime
