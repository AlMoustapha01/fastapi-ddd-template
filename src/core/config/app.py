from pydantic import BaseModel, Field


class AppSettings(BaseModel):
    name: str = Field(alias="NAME")
    project_description: str = Field(alias="PROJECT_DESCRIPTION")
    version: str = Field(alias="VERSION")
