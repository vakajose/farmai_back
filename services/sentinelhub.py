from typing import List
import requests
from models import Parcela, Analisis, Punto
from services.storage import StorageService
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta

load_dotenv()


def convert_points_to_coordinates(points: List[Punto]):
    coordinates = []
    for point in points:
        coordinates.append([point.longitude, point.latitude])
    # Append the first point at the end to close the polygon
    coordinates.append(coordinates[0])
    return [coordinates]


def fetch_images_analisis(parcela: Parcela, tipo_analisis: str) -> Analisis:
    return Analisis()


class SentinelHubService:
    def __init__(self):
        self.instance_id = os.getenv('SENTINEL_INSTANCE_ID')
        self.client_id = os.getenv('SENTINEL_CLIENT_ID')
        self.client_secret = os.getenv('SENTINEL_CLIENT_SECRET')
        self.oauth_url = os.getenv('SENTINEL_OAUTH_URL')
        self.process_url = os.getenv('SENTINEL_PROCESS_URL')
        self.access_token = self.get_access_token()

    def get_access_token(self):
        print('Getting access token')
        url = self.oauth_url
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        payload = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        response = requests.post(url, data=payload, headers=headers)
        response.raise_for_status()
        return response.json()['access_token']

    def fetch_images(self, parcela: Parcela, tipo_analisis: str):

        polygon_coords = convert_points_to_coordinates(parcela.ubicacion)
        print('PolygonCords: ', polygon_coords)
        analisis_id = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{tipo_analisis}"

        images = self._fetch_images_from_sentinel(polygon_coords, analisis_id, parcela, tipo_analisis)
        return images, analisis_id

    def _fetch_images_from_sentinel(self, polygon_coords, analisis_id, parcela, tipo_analisis):
        url = self.process_url
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.access_token}',
            "Accept": "application/tar"
        }

        payload = self._get_data_by_tipo(tipo_analisis, polygon_coords)
        if payload:
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 401:
                # Token expirado, obtener uno nuevo y reintentar
                self.access_token = self.get_access_token()
                headers['Authorization'] = f'Bearer {self.access_token}'
                response = requests.post(url, headers=headers, json=payload)

            print(f"Response Status Code: {response.status_code}")
            print(f"Response Headers: {response.headers}")

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
        else:
            raise Exception(f"Tipo de análisis no válido: {tipo_analisis}")

    def _get_data_by_tipo(self, tipo: str, polygon_coords):
        # Obtener la fecha actual y la fecha de hace un mes
        to_date = datetime.now()
        from_date = to_date - timedelta(days=30)

        # Formatear las fechas
        to_date_str = to_date.strftime('%Y-%m-%dT%H:%M:%SZ')
        from_date_str = from_date.strftime('%Y-%m-%dT%H:%M:%SZ')

        if tipo == 'maleza':

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
                            "dataFilter": {
                                "timeRange": {
                                    "from": from_date_str,
                                    "to": to_date_str
                                },
                                "maxCloudCoverage": 20
                            },
                            "processing": {
                                "harmonizeValues": True
                            },
                            "type": "sentinel-2-l2a"
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
                    ]
                },
                "evalscript": "//VERSION=3\n\nfunction setup() {\n  return {\n    input: [\"B02\", \"B03\", \"B04\", \"B08\"],\n    output: [\n      { id: \"blue\", bands: 1 },\n      { id: \"green\", bands: 1 },\n      { id: \"red\", bands: 1 },\n      { id: \"nir\", bands: 1 },\n      { id: \"combined\", bands: 3 }\n    ]\n  }\n}\n\nfunction evaluatePixel(sample) {\n  let blue = sample.B02;\n  let green = sample.B03;\n  let red = sample.B04;\n  let nir = sample.B08;\n\n  return {\n    blue: [blue],\n    green: [green],\n    red: [red],\n    nir: [nir],\n    combined: [nir, red, green]\n  }\n}"
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
                    ]
                },
                "evalscript": evalscript
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
                    ]
                },
                "evalscript": evalscript
            }

            return payload
        else:
            return None
