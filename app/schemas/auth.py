from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, model_validator

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    full_name: str = Field(min_length=1, max_length=150)
    

class LoginRequest(BaseModel):
    
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    access_token: str
    token_type: str = "bearer"

class ForgotPasswordRequest(BaseModel):
    email: EmailStr



class MessageResponse(BaseModel):
    message: str

class ResetPasswordRequest(BaseModel):
    new_password: str = Field(min_length=8, max_length=72)
    token_hash: str | None = Field(default=None, min_length=10, max_length=512)
    access_token: str | None = Field(default=None, min_length=20, max_length=4096)
    refresh_token: str | None = Field(default=None, min_length=1, max_length=1024)

    @model_validator(mode="after")
    def require_reset_token(self) -> "ResetPasswordRequest":
        if not self.token_hash and not (self.access_token and self.refresh_token):
            raise ValueError("A reset token is required")
        return self