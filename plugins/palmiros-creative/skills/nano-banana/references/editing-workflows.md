# Editing Workflows — Nano Banana

Workflows avançados de edição que são o diferencial real do Nano Banana vs
competidores: consistency, multi-turn conversation, blending.

## Workflow 1 — Multi-turn Conversational Editing

Uso: refinar uma imagem iterativamente mantendo contexto. Cada turno é
continuação natural da conversa.

```python
from google import genai
from PIL import Image
from io import BytesIO

client = genai.Client()
chat = client.chats.create(model="gemini-2.5-flash-image")

def save_response(response, path):
    for part in response.candidates[0].content.parts:
        if part.inline_data:
            Image.open(BytesIO(part.inline_data.data)).save(path)
            return True
    return False

# Iteração 1 — geração inicial
r1 = chat.send_message(
    "Generate a professional photograph for a clinic website hero: "
    "modern medical reception area, minimalist design"
)
save_response(r1, "iter_01.png")

# Iteração 2 — ajuste de iluminação (contexto preservado)
r2 = chat.send_message(
    "Same scene, but change the lighting to warm golden hour"
)
save_response(r2, "iter_02.png")

# Iteração 3 — adicionar elemento específico
r3 = chat.send_message(
    "Add a small potted monstera plant near the reception desk"
)
save_response(r3, "iter_03.png")

# Iteração 4 — cor específica
r4 = chat.send_message(
    "Change the wall color to sage green (#7A9B8E) but keep everything else identical"
)
save_response(r4, "iter_04.png")
```

**Vantagem**: sem precisar re-descrever a cena inteira. Modelo "lembra" o que
foi gerado.

## Workflow 2 — Character Consistency

Uso: mesmo personagem aparece em múltiplas imagens (série Instagram, livro
educativo, material de marketing).

```python
# Passo 1: criar o personagem "canônico"
canon_prompt = """
Portrait of a fictional female endocrinologist:
- Age: early 40s
- Hair: shoulder-length dark brown, slightly wavy
- Eyes: warm brown
- Expression: confident, welcoming smile
- Clothing: clean white lab coat over navy blouse
- Accessories: simple gold necklace, minimal makeup
- Build: average, good posture
Photorealistic, neutral gray studio background, centered portrait
"""

r = client.models.generate_content(
    model="gemini-2.5-flash-image",
    contents=canon_prompt,
)
canon = extract_image(r)
canon.save("dra_canon.png")

# Passo 2: reusar em novos cenários
scenes = [
    "examining a thyroid ultrasound on a monitor",
    "in conversation with a patient at her desk",
    "reviewing lab results, reading glasses on",
    "walking through a modern clinic hallway",
    "explaining a treatment plan using a tablet",
]

for i, scene in enumerate(scenes):
    r = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=[
            f"Same woman as reference image, now {scene}. "
            f"Keep facial features, hair, and general appearance identical. "
            f"Natural photography, professional clinic setting.",
            canon,
        ],
    )
    extract_image(r).save(f"dra_scene_{i:02d}.png")
```

**Dicas para consistency**:
- Use termos descritivos específicos ("dark brown hair" > "dark hair")
- Passe imagem de referência TODA vez (não confie só em chat history)
- Mantenha vestuário e acessórios descritos (eles "ancoram" a identidade)
- Iluminação pode mudar; features não devem

## Workflow 3 — Image Blending

Uso: fundir elementos de múltiplas imagens. Ex: sua sala de espera real +
iluminação de uma foto de referência profissional.

```python
real_photo = Image.open("minha_clinica.jpg")
style_ref = Image.open("referencia_magazine.jpg")

r = client.models.generate_content(
    model="gemini-2.5-flash-image",
    contents=[
        """
        Apply the visual style from image 2 to image 1:
        - Same lighting quality (golden hour warmth)
        - Same color grading (muted earth tones)
        - Same photographic mood (editorial magazine)

        CRITICAL: Keep these elements from image 1 unchanged:
        - Architecture and room layout
        - Furniture position and design
        - Any visible text or branding

        Output: photorealistic image with image 1's content
        and image 2's aesthetic.
        """,
        real_photo,
        style_ref,
    ],
)
```

**Variações**:
- **Style transfer**: "apply painterly style of image 2 to image 1"
- **Element insertion**: "add the lamp from image 2 to the room in image 1"
- **Composition merge**: "create a scene combining the foreground of image 1 with the background of image 2"

## Workflow 4 — Variações Controladas

Uso: gerar 4-6 variações de uma mesma idea para A/B testing.

```python
base_prompt = "Instagram post about thyroid health awareness, minimalist design"

variations = [
    f"{base_prompt}, color scheme: sage green and cream",
    f"{base_prompt}, color scheme: navy blue and gold",
    f"{base_prompt}, color scheme: warm terracotta and ivory",
    f"{base_prompt}, illustration style with abstract shapes",
    f"{base_prompt}, photographic style with real objects",
    f"{base_prompt}, vector art style, flat colors",
]

for i, v in enumerate(variations):
    r = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=v,
        config=types.GenerateContentConfig(
            image_config=types.ImageConfig(aspect_ratio="1:1")
        ),
    )
    extract_image(r).save(f"var_{i:02d}.png")
```

Ou usando `candidate_count` para múltiplos resultados em uma chamada:
```python
config=types.GenerateContentConfig(
    candidate_count=4,  # gera 4 versões do mesmo prompt
)
# Depois itera response.candidates em vez de .candidates[0]
```

## Workflow 5 — Inpainting Implícito

Nano Banana não tem inpainting oficial (máscara), mas edição localizada via
linguagem natural funciona surpreendentemente bem:

```python
original = Image.open("foto_clinica.jpg")

r = client.models.generate_content(
    model="gemini-2.5-flash-image",
    contents=[
        "In this clinic photo, remove the cluttered papers on the desk "
        "and replace with a clean tablet and a small plant. "
        "Keep everything else identical: walls, lighting, furniture, angle.",
        original,
    ],
)
```

**Limitações**:
- Edições sutis (< 10% da imagem) funcionam bem
- Mudanças grandes podem "contaminar" áreas que não deveriam mudar
- Para inpainting preciso com máscara → usar Imagen 3 `inpaintingInsert`

## Workflow 6 — Upscale / Refinement

Nano Banana v1 output nativo = 1024x1024. Para resoluções maiores:

### Opção A — Real-ESRGAN local (gratuito)
```bash
# Depois de gerar, upscale com Real-ESRGAN
realesrgan-ncnn-vulkan -i output.png -o output_4k.png -s 4
```

### Opção B — Nano Banana 2 (nativo 4K)
```python
response = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",  # v2
    contents=prompt,
    config=types.GenerateContentConfig(
        image_config=types.ImageConfig(
            resolution="4K",  # se disponível
        ),
    ),
)
```

### Opção C — Refinement via re-generation
```python
low_res = generate_at_1024(prompt)
high_res = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents=[
        f"Recreate this exact image at maximum resolution with sharper details. "
        f"Keep every element identical. Original prompt: {prompt}",
        low_res,
    ],
)
```

## Workflow 7 — Série Temática Coesa

Uso: 10 posts Instagram para campanha mensal, cada um sobre tema diferente
mas com identidade visual consistente.

```python
BRAND_STYLE = """
Consistent visual identity for Clínica Palmiros series:
- Color palette: muted sage green (#7A9B8E), brushed brass (#C9A876),
  warm cream (#F4F1EB), charcoal text (#2B2B2B)
- Typography implied: elegant serif headers, clean sans-serif body
- Composition: rule of thirds, generous negative space, centered subject
- Photography: editorial, soft natural light, 4:5 portrait ratio
- Mood: calm confidence, medical-grade trust, approachable sophistication
- AVOID: cold clinical blue, hard shadows, busy layouts, stock-photo feel
"""

topics = [
    "Diabetes tipo 2 - sinais precoces",
    "Tireoide - importância do check-up anual",
    "Menopausa - cuidados e qualidade de vida",
    "Síndrome dos ovários policísticos",
    "Osteoporose - prevenção começa cedo",
    "Obesidade - abordagem multidisciplinar",
    "Resistência à insulina - entenda o que é",
    "Hormônios e saúde mental",
    "Colesterol - o que é bom saber",
    "Vitamina D - por que dosar",
]

# Primeiro post define estética canônica
canon_r = client.models.generate_content(
    model="gemini-2.5-flash-image",
    contents=f"{BRAND_STYLE}\n\nFirst post of series: {topics[0]}. "
             f"Establish the canonical visual style for the series."
)
canon_img = extract_image(canon_r)
canon_img.save("posts/post_00_canon.png")

# Posts subsequentes referenciam o canon
for i, topic in enumerate(topics[1:], start=1):
    r = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=[
            f"{BRAND_STYLE}\n\nNew post in the same series as reference image: "
            f"topic is {topic}. Maintain exact same visual style, palette, "
            f"composition approach, and mood. Only content changes.",
            canon_img,
        ],
    )
    extract_image(r).save(f"posts/post_{i:02d}.png")
```

## Workflow 8 — Before/After Mockup (compliance!)

**IMPORTANTE — CFM 1.974/2011**: antes/depois em procedimentos estéticos é
PROIBIDO na publicidade médica brasileira, mesmo que a imagem seja gerada
por IA. Use apenas para:
- Educação médica (material didático não-publicitário)
- Discussão em prontuário interno
- Comunicação médico↔paciente privada (não marketing)

```python
# Uso EDUCATIVO apenas (não publicitário)
r = client.models.generate_content(
    model="gemini-2.5-flash-image",
    contents="""
    Medical educational illustration (NOT for advertising):
    split-screen showing conceptual before/after of hormonal balance restoration,
    left side: stressed fatigued cellular visualization,
    right side: balanced harmonious cellular visualization,
    abstract scientific style, labeled in Portuguese,
    clearly marked 'Ilustração Educativa / Educational Illustration'
    """,
)
```

## Workflow 9 — Formato Impresso (alta resolução)

Para panfletos, cartões, banners físicos — precisa 300dpi+.

```python
# Gerar em 1:1 ou 4:5 e upscale
r = generate(
    prompt="Brochure cover for Clínica Palmiros",
    aspect="4:5",
    model="gemini-3.1-flash-image-preview",  # v2 tem melhor text rendering
)
img = extract_image(r)

# Upscale local para 300dpi
from PIL import Image
img = img.resize((img.width * 3, img.height * 3), Image.LANCZOS)
img.save("brochure.png", dpi=(300, 300))

# Ou use Real-ESRGAN para qualidade máxima
# realesrgan-ncnn-vulkan -i brochure.png -o brochure_print.png -s 4
```

## Helper Function Completa

```python
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
from pathlib import Path
import hashlib, json, time

class NanoBananaClient:
    def __init__(self, model="gemini-2.5-flash-image", output_dir="./gen"):
        self.client = genai.Client()
        self.model = model
        self.out = Path(output_dir)
        self.out.mkdir(exist_ok=True)

    def generate(self, prompt, refs=None, aspect="1:1", save=True):
        contents = [prompt]
        if refs:
            contents.extend(refs if isinstance(refs, list) else [refs])

        config = types.GenerateContentConfig(
            image_config=types.ImageConfig(aspect_ratio=aspect)
        )

        r = self.client.models.generate_content(
            model=self.model, contents=contents, config=config
        )

        for part in r.candidates[0].content.parts:
            if part.inline_data:
                img = Image.open(BytesIO(part.inline_data.data))
                if save:
                    # Filename: hash(prompt)_timestamp.png
                    h = hashlib.md5(prompt.encode()).hexdigest()[:8]
                    path = self.out / f"{h}_{int(time.time())}.png"
                    img.save(path)
                    # Metadata sidecar
                    meta = {"prompt": prompt, "model": self.model,
                            "aspect": aspect, "timestamp": time.time()}
                    path.with_suffix(".json").write_text(json.dumps(meta, indent=2))
                    print(f"Saved: {path}")
                return img
        return None

# Uso
nb = NanoBananaClient(output_dir="~/nano-banana-output")
img = nb.generate("Modern medical clinic hero banner",
                  aspect="16:9")
```
