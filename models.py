from google.cloud.firestore import GeoPoint
from pydantic import BaseModel
from services.firebase import db, prefix
from typing import Optional, List
from datetime import datetime


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


class ImagenSatelital(BaseModel):
    tipo: str
    ruta: str


class Parcela(BaseModel):
    id: Optional[str]
    nombre: str
    ubicacion: List[Punto]
    usuario_id: str
    tipo_monitoreo: Optional[List[str]]
    proximo_monitoreo: Optional[datetime]

    @staticmethod
    def from_dict(source):
        ubicacion = [Punto.from_geopoint(punto) for punto in source.get('ubicacion', [])]
        tipo_monitoreo = source.get('tipo_monitoreo', [])
        proximo_monitoreo = source.get('proximo_monitoreo')
        if proximo_monitoreo:
            proximo_monitoreo = datetime.fromisoformat(proximo_monitoreo)
        return Parcela(
            id=source.get('id'),
            nombre=source.get('nombre'),
            ubicacion=ubicacion,
            usuario_id=source.get('usuario_id'),
            tipo_monitoreo=tipo_monitoreo,
            proximo_monitoreo=proximo_monitoreo
        )

    def to_dict(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "ubicacion": [punto.to_geopoint() for punto in self.ubicacion],
            "usuario_id": self.usuario_id,
            "tipo_monitoreo": self.tipo_monitoreo,
            "proximo_monitoreo": self.proximo_monitoreo.isoformat() if self.proximo_monitoreo else None
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


class Analisis(BaseModel):
    fecha: Optional[datetime] = None
    imagenes: List[ImagenSatelital]
    tipo: str
    evaluacion: Optional[str] = None
    id: Optional[str] = None

    @staticmethod
    def from_dict(source):
        imagenes = [ImagenSatelital(**imagen) for imagen in source.get('imagenes', [])]
        return Analisis(
            fecha=datetime.fromisoformat(source.get('fecha')),
            imagenes=imagenes,
            tipo=source.get('tipo'),
            evaluacion=source.get('evaluacion'),
            id=source.get('id')
        )

    def to_dict(self):
        return {
            "fecha": self.fecha.isoformat(),
            "imagenes": [imagen.dict() for imagen in self.imagenes],
            "tipo": self.tipo,
            "evaluacion": self.evaluacion,
            "id": self.id
        }

    def save(self, usuario_id: str, parcela_id: str):
        if not self.fecha:
            self.fecha = datetime.now()
        if not self.id:
            self.id = f"{self.fecha.strftime('%Y%m%d')}_{self.tipo}"
        parcela_ref = db.document(f'{prefix}users/{usuario_id}/parcelas/{parcela_id}')
        if not parcela_ref.get().exists:
            raise ValueError("Parcela no existe")
        analisis_ref = parcela_ref.collection('analisis').document(self.id)
        analisis_ref.set(self.to_dict())

    @staticmethod
    def get_by_id(usuario_id: str, parcela_id: str, analisis_id: str):
        analisis_ref = db.document(f'{prefix}users/{usuario_id}/parcelas/{parcela_id}/analisis/{analisis_id}')
        analisis_doc = analisis_ref.get()
        if analisis_doc.exists:
            return Analisis.from_dict(analisis_doc.to_dict())
        return None

    @staticmethod
    def get_all(usuario_id: str, parcela_id: str):
        analisis_ref = db.collection(f'{prefix}users/{usuario_id}/parcelas/{parcela_id}/analisis').stream()
        analisis_list = []
        for analisis in analisis_ref:
            analisis_list.append(Analisis.from_dict(analisis.to_dict()))
        return analisis_list

    @staticmethod
    def delete(usuario_id: str, parcela_id: str, analisis_id: str):
        analisis_ref = db.document(f'{prefix}users/{usuario_id}/parcelas/{parcela_id}/analisis/{analisis_id}')
        analisis_ref.delete()

    @staticmethod
    def get_last_analisis_by_tipo(usuario_id: str, parcela_id: str, tipo: str):
        analisis_ref = db.collection(f'{prefix}users/{usuario_id}/parcelas/{parcela_id}/analisis').where('tipo', '==', tipo).order_by('fecha', direction='DESCENDING').limit(1).stream()
        for analisis in analisis_ref:
            return Analisis.from_dict(analisis.to_dict())
        return None
