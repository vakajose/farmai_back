from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


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


class ImagenSatelital(BaseModel):
    tipo: str = Field(..., example="NDVI", description="Tipo de imagen satelital")
    ruta: str = Field(..., example="/path/to/image.png",
                      description="Ruta de la imagen satelital en el servidor de contenido estatico")


class ParcelaBase(BaseModel):
    nombre: str = Field(..., example="Mi Parcela", description="El nombre referencial de la parcela")
    ubicacion: List[Punto] = Field(...,
                                   example="[{\"latitude\":-17.816365,\"longitude\":-17.816365},{\"latitude\":-17.816365,\"longitude\":-17.816365}]",
                                   description="Lista de puntos de coordenadas que determina el poligono de la parcela")
    tipo_monitoreo: Optional[List[str]] = Field(None, example=["NDVI", "EVI"],
                                                description="Tipos de monitoreo asignados a la parcela")
    proximo_monitoreo: Optional[datetime] = Field(None, example="2024-06-21T00:00:00",
                                                  description="Fecha y hora del proximo monitoreo programado")


class ParcelaCreate(ParcelaBase):
    usuario_id: str = Field(..., example="devuser", description="El username del usuario propietario de la parcela")


class ParcelaResponse(ParcelaBase):
    id: Optional[str] = Field(None, example="parcela_id_123",
                              description="El ID de la parcela, es unico y no admite espacios")
    usuario_id: str = Field(..., example="devuser", description="El username del usuario propietario de la parcela")

    class Config:
        from_attributes = True


class AnalisisCreate(BaseModel):
    imagenes: List[ImagenSatelital] = Field(...,
                                            example="[{\"tipo\":\"ROJO\",\"ruta\":\"/path/to/image.png\"},{\"tipo\":\"NIR\",\"ruta\":\"/path/to/image.png\"}]",
                                            description="Lista de imagenes satelitales")
    tipo: str = Field(..., example="NDVI", description="Tipo de analisis")


class AnalisisBase(AnalisisCreate):
    fecha: datetime = Field(..., example="2024-06-21T00:00:00", description="Fecha y hora del analisis")
    evaluacion: Optional[str] = Field(None, example="Healthy",
                            description="Resultado de la evaluacion del diagnostico hecho por la IA")


class AnalisisResponse(AnalisisBase):
    id: Optional[str] = Field(None, example="20240621_NDVI", description="Identificador del analisis")

    class Config:
        from_attributes = True
