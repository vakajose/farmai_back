import requests
from models import Parcela
from services.storage import StorageService
from dotenv import load_dotenv
import os

load_dotenv()

class SentinelHubService:
    def __init__(self):
        self.instance_id = os.getenv('SENTINEL_INSTANCE_ID')
        self.storage_service = StorageService()

    def fetch_images(self, parcela: Parcela, tipo_analisis: str):
        # Mapear tipo_analisis a bandas específicas
        bandas_map = {
            'NDVI': ['B04', 'B08'],
            'stress_hidrico': ['B11', 'B12'],
            # Agregar más mappings según sea necesario
        }

        bandas = bandas_map.get(tipo_analisis)
        if not bandas:
            raise ValueError(f"Tipo de análisis no soportado: {tipo_analisis}")

        lon1, lat1 = parcela.ubicacion[0].longitude, parcela.ubicacion[0].latitude
        lon2, lat2 = parcela.ubicacion[2].longitude, parcela.ubicacion[2].latitude

        images = self._fetch_images_from_sentinel(lon1, lat1, lon2, lat2, bandas)
        return images

    def _fetch_images_from_sentinel(self, lon1, lat1, lon2, lat2, bandas):
        url = f'https://services.sentinel-hub.com/api/v1/process'
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.instance_id}',
        }

        payload = {
            "input": {
                "bounds": {
                    "bbox": [lon1, lat1, lon2, lat2]
                },
                "data": [
                    {
                        "type": "sentinel-2-l2a",
                        "dataFilter": {
                            "timeRange": {
                                "from": "2024-01-01T00:00:00Z",
                                "to": "2024-01-31T23:59:59Z"
                            }
                        }
                    }
                ]
            },
            "output": {
                "width": 512,
                "height": 512,
                "responses": [
                    {
                        "identifier": f"band_{band}",
                        "format": {
                            "type": "image/png"
                        },
                        "evalscript": f"return [{band}];"
                    } for band in bandas
                ]
            }
        }

        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            image_links = response.json()
            saved_images = []
            for idx, image in enumerate(image_links):
                image_data = requests.get(image['href']).content
                filename = f'{bandas[idx]}_{lon1}_{lat1}.png'
                filepath = self.storage_service.save_image(image_data, filename)
                saved_images.append(filepath)
            return saved_images
        else:
            raise Exception(f"Error fetching images: {response.status_code} - {response.text}")
