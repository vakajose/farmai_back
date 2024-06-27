from typing import List
import requests
from models import Parcela, Analisis, Punto
from services.storage import StorageService
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta

load_dotenv()


class SentinelHubService:
    def __init__(self):
        self.instance_id = os.getenv('SENTINEL_INSTANCE_ID')
        self.client_id = os.getenv('SENTINEL_CLIENT_ID')
        self.client_secret = os.getenv('SENTINEL_CLIENT_SECRET')
        self.access_token = self.get_access_token()

    def get_access_token(self):
        print('Getting access token')
        url = 'https://services.sentinel-hub.com/oauth/token'
        payload = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        response = requests.post(url, data=payload)
        response.raise_for_status()
        return response.json()['access_token']

    def convert_points_to_coordinates(self, points: List[Punto]):
        coordinates = []
        for point in points:
            coordinates.append([point.longitude, point.latitude])
        # Append the first point at the end to close the polygon
        coordinates.append(coordinates[0])
        return [coordinates]

    def fetch_images_analisis(self, parcela: Parcela, tipo_analisis: str) -> Analisis:
        return Analisis()

    def fetch_images(self, parcela: Parcela, tipo_analisis: str):
        # Mapear tipo_analisis a bandas específicas
        bandas_map = {
            'estado_vegetacion': ['B04', 'B08'],  # NDVI
            'stress_hidrico': ['B11', 'B12'],  # SWIR bands
            'plagas': ['B02', 'B03', 'B04', 'B08'],  # RGB + NIR
            'deteccion_enfermedades': ['B02', 'B03', 'B04', 'B08'],  # RGB + NIR
            'analisis_suelo': ['B02', 'B03', 'B04', 'B08', 'VV', 'VH'],  # RGB + NIR + Radar
            'monitoreo_crecimiento': ['B02', 'B03', 'B04', 'B08'],  # RGB + NIR
            'deteccion_malezas': ['B02', 'B03', 'B04', 'B08'],  # RGB + NIR
            'estimacion_productividad': ['B02', 'B03', 'B04', 'B08'],  # RGB + NIR
            'evaluacion_danos_clima': ['B02', 'B03', 'B04', 'B08', 'B10'],  # RGB + NIR + Thermal
            'mapeo_cultivos': ['B02', 'B03', 'B04', 'B08', 'VV', 'VH'],  # RGB + NIR + Radar
        }

        # polygon_coords = [(punto.longitude, punto.latitude) for punto in parcela.ubicacion]
        # polygon_coords.append(polygon_coords[0])  # Cerrar el polígono

        polygon_coords = self.convert_points_to_coordinates(parcela.ubicacion)
        print('PolygonCords: ', polygon_coords)
        analisis_id = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{tipo_analisis}"

        images = self._fetch_images_from_sentinel(polygon_coords, analisis_id, parcela, tipo_analisis)
        return images, analisis_id

    def _fetch_images_from_sentinel(self, polygon_coords, analisis_id, parcela, tipo_analisis):
        url = f'https://services.sentinel-hub.com/api/v1/process'
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.access_token}',
            "Accept": "application/tar"
        }

        payload = _get_data_by_tipo(tipo_analisis, polygon_coords)
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 401:
            # Token expirado, obtener uno nuevo y reintentar
            self.access_token = self.get_access_token()
            headers['Authorization'] = f'Bearer {self.access_token}'
            response = requests.post(url, headers=headers, json=payload)

        print(f"Response Status Code: {response.status_code}")
        print(f"Response Headers: {response.headers}")
        #print(f"Response Content: {response.content}")

        # if response.status_code == 200:
        #     try:
        #         saved_images = []
        #         for idx, band in enumerate(bandas):
        #             filename = f'band_{band}-{img_prefix}.png'
        #             storage_service = StorageService()
        #             filepath = storage_service.save_image(response.content, filename)
        #             imagen = ImagenSatelital(ruta=filepath, tipo=band)
        #             saved_images.append(imagen)
        #         return saved_images
        #     except ValueError as e:
        #         raise Exception(f"Error parsing JSON response: {e}")
        # else:
        #     raise Exception(f"Error fetching images: {response.status_code} - {response.text}")
        if response.status_code == 200:
            try:
                # Check if the response is a tar file
                if 'application/x-tar' in response.headers.get('Content-Type', ''):
                    storage_service = StorageService(parcela, analisis_id)
                    saved_images = storage_service.save_image_from_tar(response)
                    return saved_images
                else:
                    raise Exception("Unexpected response format")
            except ValueError as e:
                raise Exception(f"Error parsing JSON response: {e}")
        else:
            raise Exception(f"Error fetching images: {response.status_code} - {response.text}")


def _get_data_by_tipo(tipo: str, polygon_coords):
    # Obtener la fecha actual y la fecha de hace un mes
    to_date = datetime.now()
    from_date = to_date - timedelta(days=30)

    # Formatear las fechas al formato ISO 8601
    to_date_str = to_date.isoformat() + "Z"
    from_date_str = from_date.isoformat() + "Z"

    if tipo == 'maleza':
        evalscript = "//VERSION=3\nfunction setup() { return { input: ['B02', 'B03', 'B04', 'B08'], output: [ { id: 'blue', bands: 1 }, { id: 'green', bands: 1 }, { id: 'red', bands: 1 }, { id: 'nir', bands: 1 }, { id: 'combined', bands: 3 } ] }; }\nfunction evaluatePixel(sample) { let blue = sample.B02; let green = sample.B03; let red = sample.B04; let nir = sample.B08; return { blue: [blue], green: [green], red: [red], nir: [nir], combined: [nir, red, green] }; }"

        payload = {
            "input": {
                "bounds": {
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": polygon_coords
                    }
                },
                "data": [
                    {
                        "type": "sentinel-2-l2a",
                        "dataFilter": {
                            "timeRange": {
                                "from": from_date_str,
                                "to": to_date_str
                            },
                            "maxCloudCoverage": 20
                        },
                        "processing": {
                            "harmonizeValues": True
                        }
                    }
                ]
            },
            "output": {
                "width": 2048,
                "height": 2048,
                "responses": [
                    {
                        "identifier": "blue",
                        "format": {
                            "type": "image/png"
                        }
                    },
                    {
                        "identifier": "green",
                        "format": {
                            "type": "image/png"
                        }
                    },
                    {
                        "identifier": "red",
                        "format": {
                            "type": "image/png"
                        }
                    },
                    {
                        "identifier": "nir",
                        "format": {
                            "type": "image/png"
                        }
                    },
                    {
                        "identifier": "combined",
                        "format": {
                            "type": "image/png"
                        }
                    }
                ],
                "evalscript": evalscript
            }
        }

        return payload
    elif tipo == 'nutricion':
        evalscript = "//VERSION=3\nfunction setup() { return { input: ['B04', 'B08', 'B11'], output: [ { id: 'red', bands: 1 }, { id: 'nir', bands: 1 }, { id: 'swir', bands: 1 }, { id: 'combined', bands: 3 } ] }; }\nfunction evaluatePixel(sample) { let red = sample.B04; let nir = sample.B08; let swir = sample.B11; return { red: [red], nir: [nir], swir: [swir], combined: [nir, red, swir] }; }"

        payload = {
            "input": {
                "bounds": {
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": polygon_coords
                    }
                },
                "data": [
                    {
                        "type": "sentinel-2-l2a",
                        "dataFilter": {
                            "timeRange": {
                                "from": from_date_str,
                                "to": to_date_str
                            },
                            "maxCloudCoverage": 20
                        },
                        "processing": {
                            "harmonizeValues": True
                        }
                    }
                ]
            },
            "output": {
                "width": 2048,
                "height": 2048,
                "responses": [
                    {
                        "identifier": "red",
                        "format": {
                            "type": "image/png"
                        }
                    },
                    {
                        "identifier": "nir",
                        "format": {
                            "type": "image/png"
                        }
                    },
                    {
                        "identifier": "swir",
                        "format": {
                            "type": "image/png"
                        }
                    },
                    {
                        "identifier": "combined",
                        "format": {
                            "type": "image/png"
                        }
                    }
                ],
                "evalscript": evalscript
            }
        }

        return payload
    elif tipo == 'plagas':
        evalscript = "//VERSION=3\nfunction setup() { return { input: ['B08', 'B11', 'B12'], output: [ { id: 'nir', bands: 1 }, { id: 'swir1', bands: 1 }, { id: 'swir2', bands: 1 }, { id: 'combined', bands: 3 } ] }; }\nfunction evaluatePixel(sample) { let nir = sample.B08; let swir1 = sample.B11; let swir2 = sample.B12; return { nir: [nir], swir1: [swir1], swir2: [swir2], combined: [swir2, swir1, nir] }; }"

        payload = {
            "input": {
                "bounds": {
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": polygon_coords
                    }
                },
                "data": [
                    {
                        "type": "sentinel-2-l2a",
                        "dataFilter": {
                            "timeRange": {
                                "from": from_date_str,
                                "to": to_date_str
                            },
                            "maxCloudCoverage": 20
                        },
                        "processing": {
                            "harmonizeValues": True
                        }
                    }
                ]
            },
            "output": {
                "width": 2048,
                "height": 2048,
                "responses": [
                    {
                        "identifier": "nir",
                        "format": {
                            "type": "image/png"
                        }
                    },
                    {
                        "identifier": "swir1",
                        "format": {
                            "type": "image/png"
                        }
                    },
                    {
                        "identifier": "swir2",
                        "format": {
                            "type": "image/png"
                        }
                    },
                    {
                        "identifier": "combined",
                        "format": {
                            "type": "image/png"
                        }
                    }
                ],
                "evalscript": evalscript
            }
        }

        return payload
