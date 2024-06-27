import os
from typing import List
from dotenv import load_dotenv
from openai import OpenAI
from models import ImagenSatelital

load_dotenv()
client = OpenAI(
    api_key=os.getenv('OPENAI_API_KEY'),
    organization=os.getenv('OPENAI_ORG_ID'),
    project=os.getenv('OPENAI_PROJECT_ID'),
)




def analyze_images(diagnosis_type: str, images: List[ImagenSatelital]) -> str:
    url = os.getenv('CDN_URL' or 'http://cdn.vakajose.live')
    image_paths = [f"{url}/{img.ruta}" for img in images]

    msgInstructions = _get_instructions(diagnosis_type)
    messages = [
    {
      "role": "user",
      "content": [
        {"type": "text", "text": msgInstructions},
      ],
    }
  ]

    # Adding each image URL to the messages list
    for path in image_paths:
        messages[0]["content"].append({
          "type": "image_url",
          "image_url": {
            "url": path,
          },
        })

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        max_tokens=1000,
    )

    return response.choices[0].message.content.strip()


def _get_instructions(diagnosis_type):
    gen = os.getenv('PROMPT_BASE' or '')
    if diagnosis_type == 'maleza':
        return f"Por favor, analiza las siguientes imágenes satelitales para la detección de malezas en el área agrícola especificada. Las imágenes corresponden a las bandas B02 (Blue), B03 (Green), B04 (Red) y B08 (NIR) y la combinada de todas las anteriores. Evalúa la presencia de malezas y genera un informe detallado. {gen}"
    elif diagnosis_type == 'nutricion':
        return f"Por favor, analiza las siguientes imágenes satelitales para la detección de deficiencias nutricionales en el área agrícola especificada. Las imágenes corresponden a las bandas B04 (Red), B08 (NIR) y B11 (SWIR) y la combinada de todas las anteriores. Evalúa la presencia de deficiencias nutricionales y genera un informe detallado. {gen}"
    elif diagnosis_type == 'plagas':
        return f"Por favor, analiza las siguientes imágenes satelitales para la detección de plagas en el área agrícola especificada. Las imágenes corresponden a las bandas B08 (NIR), B11 (SWIR) y B12 (SWIR) y la combinada de las anteriores. Evalúa la presencia de plagas y genera un informe detallado. {gen}"


def analyze_images_b(image_paths: List[str]) -> str:
    msgInstructions = f"Analiza estas imágenes para realizar un diagnóstico agrícola y de suelo, ya sea falta de nutrientes, sospecha de plagas, malezas, falta de agua o algún indicio de enfermedades en las plantas o cultivos. Devuelve si hay alguna enfermedad o plaga, que tipo de enfermedad o plaga es y si es necesario aplicar algún tratamiento. Determina si es necesario realizar un análisis más profundo y qué tipo de análisis sería. Especifica si es necesario realizar un análisis más profundo y qué tipo de análisis sería. La respuesta debe estar en formato Markdown y contener máximo 2800 caracteres con espacios."
    messages = [
    {
      "role": "user",
      "content": [
        {"type": "text", "text": msgInstructions},
      ],
    }
  ]

    # Adding each image URL to the messages list
    for path in image_paths:
        messages[0]["content"].append({
          "type": "image_url",
          "image_url": {
            "url": path,
          },
        })

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        max_tokens=1000,
    )
    
    #return response.choices[0].message['content'].strip()
    return response.choices[0].message.content.strip()