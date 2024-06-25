import os
from typing import List
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(
    api_key=os.getenv('OPENAI_API_KEY'),
    organization=os.getenv('OPENAI_ORG_ID'),
    project=os.getenv('OPENAI_PROJECT_ID'),
)

def analyze_images(diagnosis_type: str, image_paths: List[str]) -> str:
    msgInstructions = f"Analiza estas imágenes para: {diagnosis_type}, devuelve si hay alguna enfermedad o plaga, que tipo de enfermedad o plaga es y si es necesario aplicar algún tratamiento. Determina si es necesario realizar un análisis más profundo y qué tipo de análisis sería. Especifica si es necesario realizar un análisis más profundo y qué tipo de análisis sería. La respuesta debe estar en formato Markdown y contener máximo 2800 caracteres con espacios."
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