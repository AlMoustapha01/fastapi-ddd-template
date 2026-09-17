from pydantic import BaseModel, Field


class CookiesSettings(BaseModel):
    secure: bool = Field(alias="SECURE")


class SecuritySettings(BaseModel):
    cookies: CookiesSettings
