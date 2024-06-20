from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    username: str = Field(..., example="user123", description="El nombre de usuario para registro")
    password: str = Field(..., min_length=8, example="password123",
                          description="La contraseña del usuario para registro")


class UserLogin(BaseModel):
    username: str = Field(..., example="user123", description="El nombre de usuario para inicio de sesión")
    password: str = Field(..., example="password123", description="La contraseña del usuario para inicio de sesión")


class UserResponse(BaseModel):
    username: str = Field(..., description="El nombre de usuario")
