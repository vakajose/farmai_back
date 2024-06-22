from pydantic import BaseModel, Field
from typing import Optional, List


class UserCreate(BaseModel):
    username: str = Field(..., example="devuser", description="El nombre de usuario para registro")
    password: str = Field(..., min_length=8, example="devpassw",
                          description="La contraseña del usuario para registro")


class UserLogin(BaseModel):
    username: str = Field(..., example="devuser", description="El nombre de usuario para inicio de sesión")
    password: str = Field(..., example="devpassw", description="La contraseña del usuario para inicio de sesión")


class UserResponse(BaseModel):
    username: str = Field(..., description="El nombre de usuario")

class Punto(BaseModel):
    latitude: float = Field(..., example="-17.816365", description="Valor de la latitud del punto en coordenadas")
    longitude: float = Field(..., example="-17.816365", description="Valor de la longitud del punto en coordenadas")

class ParcelaBase(BaseModel):
    nombre: str = Field(..., example="Mi Parcela", description="El nombre referencial de la parcela")
    ubicacion: List[Punto] = Field(..., example="[{\"latitude\":-17.816365,\"longitude\":-17.816365},{\"latitude\":-17.816365,\"longitude\":-17.816365}]", description="Lista de puntos de coordenadas que determina el poligono de la parcela")


class ParcelaCreate(ParcelaBase):
    usuario_id: str = Field(..., example="devuser", description="El username del usuario propietario de la parcela")


class ParcelaResponse(ParcelaBase):
    id: Optional[str] = Field(None, example="parcela_id_123", description="El ID de la parcela, es unico y no admite espacios")
    usuario_id: str = Field(..., example="devuser", description="El username del usuario propietario de la parcela")

    class Config:
        orm_mode = True
