import os
from dotenv import load_dotenv

load_dotenv()

class StorageService:
    def __init__(self):
        # Obtener la ruta raiz del proyecto
        self.storage_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), os.getenv('STORAGE_CONTAINER_PATH', 'images'))
        print(f"Ruta de almacenamiento: Storage path: {self.storage_path}")
    def save_image(self, image_data: bytes, filename: str) -> str:
        # Crear directorio si no existe
        os.makedirs(self.storage_path, exist_ok=True)
        # Definir la ruta completa del archivo
        filepath = os.path.join(self.storage_path, filename)
        # Escribir los datos de la imagen en el archivo
        with open(filepath, 'wb') as file:
            file.write(image_data)
        return filepath
