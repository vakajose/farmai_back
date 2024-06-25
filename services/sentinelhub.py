from typing import List

import requests
from models import Parcela, Analisis, ImagenSatelital
from services.storage import StorageService
from dotenv import load_dotenv
import os
import logging
from datetime import datetime

load_dotenv()


class SentinelHubService:
    def __init__(self):
        self.instance_id = os.getenv('SENTINEL_INSTANCE_ID')
        self.client_id = os.getenv('SENTINEL_CLIENT_ID')
        self.client_secret = os.getenv('SENTINEL_CLIENT_SECRET')
        self.access_token = self.get_access_token()
        print(self.access_token)

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

    def fetch_images(self, parcela: Parcela, tipo_analisis: str):
        # Mapear tipo_analisis a bandas específicas
        bandas_map = {
            'estado_vegetacion': ['B04', 'B08'],  # NDVI
            'stress_hidrico': ['B11', 'B12'],  # SWIR bands
            'identificacion_plagas': ['B02', 'B03', 'B04', 'B08'],  # RGB + NIR
            'deteccion_enfermedades': ['B02', 'B03', 'B04', 'B08'],  # RGB + NIR
            'analisis_suelo': ['B02', 'B03', 'B04', 'B08', 'VV', 'VH'],  # RGB + NIR + Radar
            'monitoreo_crecimiento': ['B02', 'B03', 'B04', 'B08'],  # RGB + NIR
            'deteccion_malezas': ['B02', 'B03', 'B04', 'B08'],  # RGB + NIR
            'estimacion_productividad': ['B02', 'B03', 'B04', 'B08'],  # RGB + NIR
            'evaluacion_danos_clima': ['B02', 'B03', 'B04', 'B08', 'B10'],  # RGB + NIR + Thermal
            'mapeo_cultivos': ['B02', 'B03', 'B04', 'B08', 'VV', 'VH'],  # RGB + NIR + Radar
        }

        bandas = bandas_map.get(tipo_analisis)
        if not bandas:
            raise ValueError(f"Tipo de análisis no soportado: {tipo_analisis}")

        polygon_coords = [(punto.longitude, punto.latitude) for punto in parcela.ubicacion]
        polygon_coords.append(polygon_coords[0])  # Cerrar el polígono

        img_prefix = f'{datetime.now().strftime('%Y%m%d')}_{tipo_analisis}-{parcela.id}-{parcela.usuario_id}'

        images = self._fetch_images_from_sentinel(polygon_coords, bandas,img_prefix,tipo_analisis)
        return images

    def _fetch_images_from_sentinel(self, polygon_coords, bandas, img_prefix,tipo_analisis):
        url = f'https://services.sentinel-hub.com/api/v1/process'
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.access_token}',
        }

        # payload = {
        #     "input": {
        #         "bounds": {
        #             "geometry": {
        #                 "type": "Polygon",
        #                 "coordinates": [polygon_coords]
        #             }
        #         },
        #         "data": [
        #             {
        #                 "type": "sentinel-2-l2a",
        #                 "dataFilter": {
        #                     "timeRange": {
        #                         "from": "2024-05-23T00:00:00Z",
        #                         "to": "2024-06-24T23:59:59Z"
        #                     }
        #                 }
        #             }
        #         ]
        #     },
        #     "output": {
        #         "width": 512,
        #         "height": 512,
        #         "responses": [
        #             {
        #                 "identifier": f"band_{band}",
        #                 "format": {
        #                     "type": "image/png"
        #                 },
        #                 "evalscript": f"return [{band}];"
        #             } for band in bandas
        #         ]
        #     }
        # }


        payload  = _get_data_by_tipo(tipo_analisis, polygon_coords,img_prefix)


        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 401:
            # Token expirado, obtener uno nuevo y reintentar
            self.access_token = self.get_access_token()
            headers['Authorization'] = f'Bearer {self.access_token}'
            response = requests.post(url, headers=headers, json=payload)

        print(f"Response Status Code: {response.status_code}")
        print(f"Response Headers: {response.headers}")
        #print(f"Response Content: {response.content}")

        if response.status_code == 200:
            try:
                saved_images = List[ImagenSatelital]
                for idx, band in enumerate(bandas):
                    filename = f'band_{band}-{img_prefix}.png'
                    storage_service = StorageService()
                    filepath = storage_service.save_image(response.content, filename)
                    saved_images.append(ImagenSatelital(ruta=filepath, tipo=band))
                return saved_images
            except ValueError as e:
                raise Exception(f"Error parsing JSON response: {e}")
        else:
            raise Exception(f"Error fetching images: {response.status_code} - {response.text}")


def _get_data_by_tipo(tipo: str, polygon_coords,img_prefix):
    if tipo == 'estres_hidrico':
        return """
            //VERSION=3
            
            function setup() {
              return {
                input: ["B11", "B12"],
                output: [
                  { id: "swir1", bands: 1 },
                  { id: "swir2", bands: 1 },
                  { id: "combined", bands: 3 }
                ]
              };
            }
            
            function evaluatePixel(sample) {
              let swir1 = sample.B11;
              let swir2 = sample.B12;
            
              return {
                swir1: [swir1],
                swir2: [swir2],
                combined: [swir1, swir2, swir1]
              };
            }
            """
    elif tipo == 'estado_vegetacion':
        return """
            //VERSION=3

            function setup() {
              return {
                input: ["B04", "B08"],
                output: [
                  { id: "nir", bands: 1 },
                  { id: "red", bands: 1 },
                  { id: "false_color", bands: 3 }
                ]
              };
            }
            
            function evaluatePixel(sample) {
              let red = sample.B04;
              let nir = sample.B08;
            
              return {
                nir: [nir],
                red: [red],
                false_color: [nir, red, red]
              };
            }
            """
    elif tipo == 'identificacion_plagas':
        return {
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
                    "from": "2024-05-25T00:00:00Z",
                    "to": "2024-06-25T23:59:59Z"
                  }
                },
                "type": "sentinel-2-l2a"
              }
            ]
          },
          "output": {
            "width": 512,
            "height": 645.157,
            "responses": [
              {
                "identifier": f"blue-{img_prefix}",
                "format": {
                  "type": "image/png"
                }
              },
              {
                "identifier": f"green-{img_prefix}",
                "format": {
                  "type": "image/png"
                }
              },
              {
                "identifier": f"red-{img_prefix}",
                "format": {
                  "type": "image/png"
                }
              },
              {
                "identifier": f"nir-{img_prefix}",
                "format": {
                  "type": "image/png"
                }
              },
              {
                "identifier": f"combined-{img_prefix}",
                "format": {
                  "type": "image/png"
                }
              }
            ]
          },
          "evalscript": "//VERSION=3\n\nfunction setup() {\n  return {\n    input: [\"B02\", \"B03\", \"B04\", \"B08\"],\n    output: [\n      { id: \"blue\", bands: 1 },\n      { id: \"green\", bands: 1 },\n      { id: \"red\", bands: 1 },\n      { id: \"nir\", bands: 1 },\n      { id: \"combined\", bands: 3 }\n    ]\n  };\n}\n\nfunction evaluatePixel(sample) {\n  let blue = sample.B02;\n  let green = sample.B03;\n  let red = sample.B04;\n  let nir = sample.B08;\n\n  return {\n    blue: [blue],\n    green: [green],\n    red: [red],\n    nir: [nir],\n    combined: [nir, red, green]\n  };\n}\n"
        }
