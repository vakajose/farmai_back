from google.cloud.firestore import GeoPoint
from pydantic import BaseModel
from services.firebase import db, prefix
from typing import Optional, List



class User(BaseModel):
    username: str
    password: str

    @staticmethod
    def from_dict(source):
        return User(
            username=source.get('username'),
            password=source.get('password')
        )

    def to_dict(self):
        return {
            "username": self.username,
            "password": self.password
        }

    def create_user(self):
        user_ref = db.collection(f'{prefix}users').document(self.username)
        user_ref.set(self.to_dict())

    @staticmethod
    def get_user_by_username(username):
        user_ref = db.collection(f'{prefix}users').document(username)
        user = user_ref.get()
        if user.exists:
            return user.to_dict()
        return None

    @staticmethod
    def delete(user_id):
        user_ref = db.collection(f'{prefix}users').document(user_id)
        user_ref.delete()

class Punto(BaseModel):
    latitude: float
    longitude: float

    @staticmethod
    def from_dict(source):
        return Punto(
            latitude=source.latitude,
            longitude=source.longitude
        )

    def to_geopoint(self):
        return GeoPoint(self.latitude, self.longitude)

    @staticmethod
    def from_geopoint(geo_point):
        return Punto(
            latitude=geo_point.latitude,
            longitude=geo_point.longitude
        )

class Parcela(BaseModel):
    id: Optional[str]
    nombre: str
    ubicacion: List[Punto]
    usuario_id: str

    @staticmethod
    def from_dict(source):
        ubicacion = [Punto.from_geopoint(punto) for punto in source.get('ubicacion', [])]
        return Parcela(
            id=source.get('id'),
            nombre=source.get('nombre'),
            ubicacion=ubicacion,
            usuario_id=source.get('usuario_id')
        )

    def to_dict(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "ubicacion": [punto.to_geopoint() for punto in self.ubicacion],
            "usuario_id": self.usuario_id
        }

    def save(self):
        # Verificar si el usuario existe
        user_ref = db.document(f'{prefix}users/{self.usuario_id}')
        user_doc = user_ref.get()
        if not user_doc.exists:
            raise ValueError("Usuario no existe")

        parcela_ref = user_ref.collection('parcelas').document(self.id)
        parcela_ref.set(self.to_dict())

    @staticmethod
    def get_by_id(usuario_id, parcela_id):
        user_ref = db.document(f'{prefix}users/{usuario_id}')
        user_doc = user_ref.get()
        if not user_doc.exists:
            raise ValueError("Usuario no existe")

        parcela_ref = db.document(f'{prefix}users/{usuario_id}/parcelas/{parcela_id}')
        parcela_doc = parcela_ref.get()
        if parcela_doc.exists:
            return Parcela.from_dict(parcela_doc.to_dict())
        return None

    @staticmethod
    def get_by_name(usuario_id, nombre):
        user_ref = db.document(f'{prefix}users/{usuario_id}')
        user_doc = user_ref.get()
        if not user_doc.exists:
            raise ValueError("Usuario no existe")

        parcelas_ref = user_ref.collection('parcelas').where('nombre', '==', nombre).stream()
        for parcela in parcelas_ref:
            return Parcela.from_dict(parcela.to_dict())
        return None

    @staticmethod
    def get_all(usuario_id):
        user_ref = db.document(f'{prefix}users/{usuario_id}')
        user_doc = user_ref.get()
        if not user_doc.exists:
            raise ValueError("Usuario no existe")

        parcelas_ref = user_ref.collection('parcelas').stream()
        parcelas = []
        for parcela in parcelas_ref:
            parcelas.append(Parcela.from_dict(parcela.to_dict()))
        return parcelas

    @staticmethod
    def delete(usuario_id, parcela_id):
        user_ref = db.document(f'{prefix}users/{usuario_id}')
        user_doc = user_ref.get()
        if not user_doc.exists:
            raise ValueError("Usuario no existe")

        parcela_ref = db.document(f'{prefix}users/{usuario_id}/parcelas/{parcela_id}')
        parcela_ref.delete()
