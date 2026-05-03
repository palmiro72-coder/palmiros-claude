# Prompting Patterns — Nano Banana

Padrões de prompt que funcionam. Baseado em testes e documentação oficial.

## Anatomia de um Prompt Eficaz

Ordem ótima dos componentes:

```
[TIPO DE IMAGEM] + [SUJEITO] + [COMPOSIÇÃO] + [ILUMINAÇÃO] +
[ESTILO] + [DETALHES TÉCNICOS] + [ASPECT RATIO]
```

### Exemplo descontruído

```
Professional editorial photograph  ← TIPO
of a modern medical clinic interior  ← SUJEITO
shot from eye level, wide angle, reception desk in focus  ← COMPOSIÇÃO
natural window light from left, soft shadows, warm golden hour  ← ILUMINAÇÃO
minimalist contemporary aesthetic, sage green and brushed brass accents  ← ESTILO
high resolution, sharp focus, photorealistic, 8k quality  ← DETALHES
4:5 aspect ratio  ← RATIO
```

## Padrões por Tipo de Output

### Fotografia Profissional
```
{subject}, {camera angle}, {lens/focal length}, {lighting}, {mood},
photorealistic, editorial quality, sharp focus, professional photography

Exemplo:
"Flat lay of endocrinology lab equipment (microscope, pipettes, sample tubes),
top-down view, 50mm lens, bright diffused daylight, clinical and organized,
photorealistic, editorial magazine quality, sharp focus"
```

### Ilustração / Vetor
```
Minimalist {style} illustration of {subject}, {color palette},
{line quality}, vector style, clean background, {purpose}

Exemplo:
"Minimalist line-art illustration of the thyroid gland anatomy,
single continuous line, navy blue (#2C5F6F) on white background,
medical education style, clean flat design, no text"
```

### Infográfico
```
Educational infographic showing {concept}, {layout},
labeled in {language}, {color scheme}, {target audience},
print-ready, clean typography

Exemplo:
"Educational infographic of the HPA axis (hypothalamus → pituitary → adrenal),
vertical flow layout, Portuguese labels, two-color palette
(primary #2C5F6F, accent #D4A574), designed for adult patients,
print-ready 300dpi, clean sans-serif typography"
```

### Produto / Mockup
```
Product photography of {object}, {background}, {lighting setup},
{angle}, studio quality, commercial use

Exemplo:
"Product photography of a skincare serum bottle, pure white background,
three-point studio lighting with rim light, 3/4 angle hero shot,
commercial quality, sharp details, reflective glass"
```

### Cenário/Ambiente
```
{Type of space} interior, {architectural style}, {time of day},
{key elements}, {mood}, wide angle

Exemplo:
"Luxury dermatology clinic interior, contemporary design,
mid-afternoon natural light, treatment bed with side cabinet,
plants near window, calming and spa-like atmosphere, wide angle"
```

### Retrato (pessoa fictícia)
```
Portrait of a fictional {description}, {age}, {expression},
{clothing}, {background}, {lighting style}

Exemplo:
"Portrait of a fictional female doctor, early 40s, warm confident smile,
white coat over navy blouse, blurred modern clinic background,
soft window light from left, photorealistic"
```

## Linguagem Técnica de Fotografia

Termos que o Nano Banana entende bem:

### Câmera / Lente
- `eye-level`, `high-angle`, `low-angle`, `overhead`, `dutch angle`
- `wide-angle` (24mm), `standard` (50mm), `telephoto` (85mm, 135mm)
- `macro`, `fish-eye`, `tilt-shift`
- `shallow depth of field`, `bokeh background`
- `rule of thirds`, `centered composition`, `leading lines`

### Iluminação
- `natural light`, `window light`, `golden hour`, `blue hour`
- `studio lighting`, `three-point lighting`, `rim light`, `key light`
- `soft shadows`, `hard shadows`, `diffused`, `dappled light`
- `backlight`, `side-lit`, `overhead lighting`
- `cinematic lighting`, `dramatic chiaroscuro`

### Estilo Visual
- `photorealistic`, `hyperrealistic`, `editorial`, `commercial`
- `film photography`, `analog`, `polaroid`, `35mm`
- `cinematic`, `moody`, `bright airy`, `high-key`, `low-key`
- `minimalist`, `maximalist`, `brutalist`, `scandinavian`

### Qualidade Técnica
- `8k resolution`, `sharp focus`, `high detail`, `crisp`
- `professional`, `commercial quality`, `magazine quality`
- `color grading`, `desaturated`, `vibrant`, `muted tones`

## Controle de Aspect Ratio

No prompt (Nano Banana v1) ou via `image_config.aspect_ratio` (v2):

| Ratio | Uso | Frase no prompt |
|-------|-----|-----------------|
| 1:1 | Instagram post quadrado | "square 1:1 aspect ratio" |
| 4:5 | Instagram post vertical | "4:5 portrait aspect ratio, Instagram feed optimized" |
| 9:16 | Stories, Reels, TikTok | "9:16 vertical aspect ratio, mobile full-screen" |
| 16:9 | Hero banner, YouTube | "16:9 widescreen landscape, hero banner composition" |
| 21:9 | Ultra-wide cinemático | "21:9 ultrawide cinematic aspect ratio" |
| 3:2 | DSLR natural | "3:2 DSLR aspect ratio" |
| 4:3 | Print tradicional | "4:3 aspect ratio, print-ready" |

## Negative Prompts (via descrição positiva)

Nano Banana não tem `negative_prompt` oficial. Descreva negativamente:

```
# Em vez de: "negative: text, people, watermark"
# Use:
"clean composition without any text, signs, or labels visible,
no people in the frame, no watermarks or logos"
```

### Anti-patterns comuns
- **Texto aleatório**: "no text, no lettering, no signs, no numbers"
- **Deformações**: "anatomically correct, natural proportions, realistic hands"
- **Estilo AI-genérico**: "professional photograph, not digital illustration"
- **Over-saturation**: "naturalistic colors, not overly vibrant"

## Prompts para Consistência de Marca

Para gerar série coesa (ex: 10 posts Instagram):

### Template master
```python
BRAND_STYLE = """
Clínica Palmiros visual identity:
- Color palette: sage green (#7A9B8E), brushed brass (#C9A876), warm off-white (#F4F1EB)
- Mood: calm, professional, approachable, medical-grade trust
- Typography implied: modern serif for headers, clean sans-serif for body
- Photography style: editorial, soft natural light, minimal props
- Composition: spacious, breathing room, rule of thirds
- NO: cold clinical blue, harsh lighting, busy compositions
"""

def brand_prompt(specific):
    return f"{BRAND_STYLE}\n\nSpecific image: {specific}"

# Uso
prompt = brand_prompt("Hero banner showing 'Endocrinologia' service, "
                      "abstract representation of hormones as flowing ribbons")
```

## Prompts Médicos Específicos

### Conceitos Abstratos
```
"Abstract artistic visualization of insulin resistance,
cells depicted as doors partially closed, glucose molecules as golden keys,
educational metaphor, soft medical illustration style,
accessible to lay audience, Portuguese context"
```

### Anatomia Educativa
```
"Anatomically accurate illustration of the adrenal gland cross-section,
layers clearly differentiated (zona glomerulosa, fasciculata, reticularis, medulla),
medical textbook style, labeled in Portuguese,
neutral educational color palette, white background"
```

### Lifestyle / Bem-estar
```
"Wellness-themed photograph: woman (mid-30s, fictional) doing morning yoga
in warm natural light, healthy breakfast with whole foods visible in background,
soft editorial style, approachable and aspirational,
conveys hormonal balance through lifestyle, 4:5 for Instagram"
```

## Testes A/B e Iteração

Para encontrar o prompt ótimo, gere variações sistemáticas:

```python
base = "Modern clinic reception, minimalist, natural light"

variations = [
    base,
    base + ", sage green accents, warm wood, brushed brass",
    base + ", editorial photography, magazine quality",
    base + ", architectural photography style, wide angle",
    base + ", soft morning light, 4:5 aspect ratio",
]

for i, v in enumerate(variations):
    generate(v, output=f"test_{i:02d}.png")

# Escolhe a melhor, extrai o padrão que funcionou, refina
```

## Erros Comuns

1. **Prompt muito curto** → resultado genérico. Adicione contexto.
2. **Prompt conflitante** ("minimalist maximalist") → modelo prioriza um.
3. **Lista de tags sem estrutura** → menos eficaz que frases descritivas.
4. **Pedir texto específico** → Nano Banana v1 falha. Use v2 ou Imagen 4.
5. **Personagens nomeados** → filtros bloqueiam. Use "fictional character".
6. **Copyright** → "no Disney characters, no branded elements" se preocupado.
7. **Over-especificação** → modelo ignora tail do prompt se muito longo.

## Prompt Booster Pattern

Padrão para elevar qualidade de prompts curtos:

```python
def enhance_prompt(user_input: str) -> str:
    """Pega prompt simples do usuário e retorna versão enriquecida."""
    return f"""
    {user_input}

    Style: photorealistic editorial photography
    Lighting: soft natural window light, golden hour warmth
    Composition: rule of thirds, balanced, breathing room
    Quality: 8k resolution, sharp focus, professional
    Mood: calm, confident, approachable
    Aspect ratio: 4:5 optimized for Instagram feed
    Avoid: any text or lettering, people in frame,
           watermarks, overly saturated colors
    """.strip()
```

Uso: permite user escrever "foto da minha sala de espera" e receber prompt completo.

## Prompts para Nano Banana 2 (Gemini 3.1)

v2 tem **text rendering** funcional. Novos padrões viáveis:

```
"Instagram post: centered Portuguese text 'Saúde Hormonal' in elegant
serif typography, sage green on warm cream background,
subtle abstract pattern suggesting molecular structures in background,
1:1 square aspect ratio, professional social media design"
```

v2 também tem **4K resolution** e melhor **complex instruction following**.
Prompts podem ser mais longos e detalhados sem perda de fidelidade.
