import os
from dotenv import load_dotenv
import tarfile
import io

from models import Parcela, ImagenSatelital

load_dotenv()


class StorageService:
    def __init__(self, parcela: Parcela, analisis_id: str):
        # Obtener la ruta raiz del proyecto
        self.folder_path = None
        self.relative_path = None
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.storage_path = f"{self.project_root}{os.getenv('STORAGE_CONTAINER_PATH', 'img')}"
        # Crear directorio si no existe
        os.makedirs(self.storage_path, exist_ok=True)
        self.create_folder_structure(parcela, analisis_id)

    def create_folder_structure(self, parcela: Parcela, analisis_id: str):
        # Crear la estructura de carpetas
        self.relative_path = os.path.join(parcela.usuario_id, parcela.id, analisis_id)
        self.folder_path = os.path.join(self.storage_path,self.relative_path)
        os.makedirs(self.folder_path, exist_ok=True)
        print(f"Ruta de almacenamiento de imagenes: {self.folder_path}")

    def save_image_from_tar(self, response):
        saved_images = []
        tar_content = io.BytesIO(response.content)
        with tarfile.open(fileobj=tar_content) as tar_file:
            for member in tar_file.getmembers():
                file = tar_file.extractfile(member)
                if file:
                    content = file.read()
                    filename = member.name
                    relativepath = self.save_image(content, filename)
                    image_type = filename.split('.')[0]
                    saved_images.append(ImagenSatelital(ruta=relativepath, tipo=image_type))
        return saved_images

    def save_image(self, image_data: bytes, filename: str) -> str:
        # Definir la ruta completa del archivo
        filepath = os.path.join(self.folder_path, filename)
        print(f"Imagen guardada: {filepath}")
        # Escribir los datos de la imagen en el archivo
        with open(filepath, 'wb') as file:
            file.write(image_data)
        return os.path.join(self.relative_path, filename)
