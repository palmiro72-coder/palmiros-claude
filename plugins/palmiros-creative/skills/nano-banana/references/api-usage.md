# API Usage — Gemini Flash Image (Nano Banana)

Referência técnica completa de uso da API. Copie-cole os padrões.

## Autenticação

### Google AI Studio (mais simples)
```python
import os
from google import genai

os.environ["GEMINI_API_KEY"] = "sua-key-aqui"
# ou export GEMINI_API_KEY=... no shell
client = genai.Client()
```

### Vertex AI (enterprise, GCP)
```python
from google import genai

client = genai.Client(
    vertexai=True,
    project="palmiros-ai",
    location="us-central1",
)
```

## 1. Text-to-Image (básico)

```python
from google import genai
from PIL import Image
from io import BytesIO

client = genai.Client()

prompt = """
Professional photograph of a modern medical clinic reception desk,
soft natural lighting, minimalist design with sage green and brushed brass accents,
no people, wide angle, architectural photography style, 4:5 aspect ratio
"""

response = client.models.generate_content(
    model="gemini-2.5-flash-image",
    contents=prompt,
)

for part in response.candidates[0].content.parts:
    if part.inline_data is not None:
        img = Image.open(BytesIO(part.inline_data.data))
        img.save("clinica_hero.png")
        print(f"Saved: {img.size}, {img.mode}")
    elif part.text is not None:
        print(f"Text response: {part.text}")
```

## 2. Image Editing (img2img via prompt)

```python
input_img = Image.open("original_photo.jpg")

response = client.models.generate_content(
    model="gemini-2.5-flash-image",
    contents=[
        "Transform this photo to have warm golden-hour lighting. "
        "Keep the composition, architecture, and all objects identical. "
        "Only change the light quality and color temperature.",
        input_img,
    ],
)

for part in response.candidates[0].content.parts:
    if part.inline_data:
        Image.open(BytesIO(part.inline_data.data)).save("edited.png")
```

## 3. Multi-Image Blend

```python
img_a = Image.open("clinica_interior.jpg")
img_b = Image.open("referencia_iluminacao.jpg")

response = client.models.generate_content(
    model="gemini-2.5-flash-image",
    contents=[
        "Apply the lighting and color grading style from image 2 "
        "to the clinic interior shown in image 1. "
        "Preserve the architecture and all furniture from image 1 exactly.",
        img_a,
        img_b,
    ],
)
```

## 4. Character Consistency (multi-turn)

Mantém mesma "personagem" através de múltiplas gerações usando output anterior
como referência.

```python
# Primeira geração — define a personagem
r1 = client.models.generate_content(
    model="gemini-2.5-flash-image",
    contents=[
        "Portrait of a fictional female endocrinologist, 40s, "
        "warm smile, white coat, stethoscope, clinic background, "
        "professional but approachable, photorealistic"
    ],
)
persona_img = extract_image(r1)  # função helper abaixo
persona_img.save("persona_dra.png")

# Segunda geração — reusa a personagem em nova cena
r2 = client.models.generate_content(
    model="gemini-2.5-flash-image",
    contents=[
        "Same woman from reference image, now examining a patient "
        "at a modern diagnostic clinic, warm lighting, side angle",
        persona_img,
    ],
)
extract_image(r2).save("persona_exame.png")

# Helper
def extract_image(response):
    for part in response.candidates[0].content.parts:
        if part.inline_data:
            return Image.open(BytesIO(part.inline_data.data))
    return None
```

## 5. Aspect Ratio Control

```python
from google.genai import types

response = client.models.generate_content(
    model="gemini-2.5-flash-image",
    contents="Hero banner for medical clinic website",
    config=types.GenerateContentConfig(
        response_modalities=["IMAGE"],
        image_config=types.ImageConfig(
            aspect_ratio="16:9",     # opções: 1:1, 4:5, 9:16, 16:9, 4:3, 3:4, 21:9, 3:2, 2:3
        ),
    ),
)
```

## 6. Multi-turn Conversational Editing

Com sessão chat, cada edit refina a anterior no mesmo contexto.

```python
chat = client.chats.create(model="gemini-2.5-flash-image")

# Primeira geração
r1 = chat.send_message("Generate: minimalist infographic of HPA axis, "
                       "vector style, labeled in Portuguese")
save(r1, "hpa_v1.png")

# Refinamento mantendo contexto
r2 = chat.send_message("Make the labels larger and add a subtle background gradient")
save(r2, "hpa_v2.png")

# Outro refinamento
r3 = chat.send_message("Change the color palette to our brand: #2C5F6F and #D4A574")
save(r3, "hpa_v3.png")
```

## 7. REST API direto (sem SDK)

```bash
curl -s "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent?key=$GEMINI_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{
    "contents": [{
      "parts": [{"text": "a nano banana wearing a doctor coat, studio photo"}]
    }],
    "generationConfig": {
      "responseModalities": ["IMAGE"]
    }
  }' | jq -r '.candidates[0].content.parts[] | select(.inlineData) | .inlineData.data' \
    | base64 -d > output.png
```

## 8. Batch Generation (múltiplos prompts)

```python
import asyncio
from google import genai

client = genai.Client()
prompts = [
    "Instagram post: 'Check-up anual de tireoide', minimalist, sage green",
    "Instagram post: 'Hipertireoidismo - sintomas', infographic style",
    "Instagram post: 'Diabetes tipo 2 - prevenção', warm illustration",
    # ... 10 posts da mesma série
]

async def generate_one(prompt, idx):
    response = await client.aio.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=prompt,
    )
    for p in response.candidates[0].content.parts:
        if p.inline_data:
            with open(f"post_{idx:02d}.png", "wb") as f:
                f.write(p.inline_data.data)
    return idx

async def main():
    await asyncio.gather(*[generate_one(p, i) for i, p in enumerate(prompts)])

asyncio.run(main())
```

## 9. Integração com n8n

Nodo HTTP Request:
```json
{
  "method": "POST",
  "url": "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent",
  "queryParameters": {
    "key": "{{$credentials.gemini.apiKey}}"
  },
  "headers": {
    "Content-Type": "application/json"
  },
  "body": {
    "contents": [{
      "parts": [{"text": "{{$json.prompt}}"}]
    }],
    "generationConfig": {
      "responseModalities": ["IMAGE"]
    }
  }
}
```

Nodo Function para extrair imagem:
```javascript
const imgBase64 = $input.first().json.candidates[0].content.parts
  .find(p => p.inlineData)?.inlineData.data;

return {
  json: { prompt: $input.first().json.prompt },
  binary: {
    data: {
      data: imgBase64,
      mimeType: "image/png",
      fileName: `img_${Date.now()}.png`
    }
  }
};
```

## 10. Error Handling

```python
from google.genai.errors import APIError

try:
    response = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=prompt,
    )
except APIError as e:
    if e.code == 400:
        print("Prompt violated safety filters or is malformed")
    elif e.code == 429:
        print("Rate limit exceeded")
    elif e.code == 503:
        print("Model overloaded, retry")
    else:
        print(f"Error {e.code}: {e.message}")

# Checar se imagem foi realmente gerada (pode retornar só texto se bloqueado)
got_image = any(p.inline_data for p in response.candidates[0].content.parts)
if not got_image:
    text = "".join(p.text or "" for p in response.candidates[0].content.parts)
    print(f"Model refused: {text}")
```

## 11. Tracking de Custo

```python
def log_cost(response, model="gemini-2.5-flash-image"):
    usage = response.usage_metadata
    input_tokens = usage.prompt_token_count
    output_tokens = usage.candidates_token_count

    input_cost = (input_tokens / 1_000_000) * 0.30
    # Output: se tem imagem, conta como image output @ $30/1M
    has_image = any(
        p.inline_data for p in response.candidates[0].content.parts
    )
    if has_image:
        # Cada imagem 1024x1024 = ~1290 tokens
        image_tokens = 1290
        image_cost = (image_tokens / 1_000_000) * 30.00
        text_tokens = output_tokens - image_tokens
        text_cost = max(0, text_tokens / 1_000_000) * 2.50
        output_cost = image_cost + text_cost
    else:
        output_cost = (output_tokens / 1_000_000) * 2.50

    total = input_cost + output_cost
    print(f"Cost: ${total:.4f} (in: ${input_cost:.4f}, out: ${output_cost:.4f})")
    return total
```

## 12. Safety Settings

```python
from google.genai import types

config = types.GenerateContentConfig(
    safety_settings=[
        types.SafetySetting(
            category="HARM_CATEGORY_DANGEROUS_CONTENT",
            threshold="BLOCK_ONLY_HIGH",  # ou BLOCK_NONE em context médico
        ),
        types.SafetySetting(
            category="HARM_CATEGORY_MEDICAL",
            threshold="BLOCK_NONE",  # necessário para conteúdo clínico
        ),
    ]
)

response = client.models.generate_content(
    model="gemini-2.5-flash-image",
    contents=prompt,
    config=config,
)
```

## Comparativo de Endpoints

| Endpoint | Uso | Vantagem |
|----------|-----|----------|
| `generate_content` | Single request | Simples, maioria dos casos |
| `generate_content_stream` | Stream parcial | UX em tempo real |
| `chat.send_message` | Multi-turn | Consistency, refinamento iterativo |
| `aio.models.*` | Async | Batch paralelo |
| Vertex AI batch prediction | Jobs batch | 50% desconto, 24h turnaround |
