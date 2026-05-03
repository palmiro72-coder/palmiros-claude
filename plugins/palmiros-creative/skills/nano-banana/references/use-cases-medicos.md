# Use Cases Médicos — Clínica Palmiros & Bella Derm

Aplicações específicas para o stack do Lucas, respeitando CFM e LGPD.

## Regras de Compliance (leia antes)

### CFM Resolução 1.974/2011 + 2.126/2015 — Publicidade Médica
**Proibido em marketing/publicidade:**
- Antes/depois de procedimentos (inclusive gerado por IA)
- Imagens de pacientes (reais ou AI) em contexto promocional
- Promessas de resultado
- Depoimentos de pacientes com foto
- Preços de procedimentos
- Uso de "melhor", "mais moderno", "especialista em..." sem RQE

**Permitido:**
- Ilustrações educativas/científicas genéricas
- Fotos da estrutura física da clínica
- Fotos do médico no ambiente profissional
- Infográficos e material didático

### LGPD
- Imagens de pessoas reais (mesmo como referência) → consentimento explícito
- Imagens AI de pessoas fictícias → sem necessidade de consentimento
- Cuidado com "pessoa fictícia" que se parece demais com alguém real

### Marcar conteúdo AI
Recomendado identificar em metadata ou legenda: "Ilustração gerada por
inteligência artificial" — transparência Art. 20 LGPD.

## Caso 1 — Banner Hero para Site da Clínica

```python
prompt = """
Editorial photograph for endocrinology clinic website hero section:
wide-angle view of a modern, sophisticated medical consultation room,
shot during golden hour with warm natural light streaming through
large windows, minimalist design with sage green and brushed brass accents,
elegant wood furniture, subtle botanical elements (snake plant, monstera),
empty room (no people), inviting and trustworthy atmosphere,
professional architectural photography, 16:9 aspect ratio, 8k quality
"""

# Modelo: v2 para melhor qualidade hero
client.generate(prompt, aspect="16:9", model="gemini-3.1-flash-image-preview")
```

## Caso 2 — Post Instagram Educativo

Série mensal sobre saúde hormonal, mantendo consistency:

```python
BRAND = """
Clínica Palmiros Instagram series visual identity:
- Palette: sage green #7A9B8E, brushed brass #C9A876, warm cream #F4F1EB
- Editorial photography, soft natural light
- Generous negative space, centered subject
- 4:5 aspect ratio for Instagram feed
- Mood: calm, trustworthy, sophisticated, approachable
- NO text in image (text added in post-production)
"""

topics = {
    "tireoide_checkup": "Symbolic visualization of thyroid health: "
                       "small elegant glass butterfly-shaped ornament on "
                       "warm wooden surface, soft morning light",
    "resistencia_insulina": "Abstract metaphor for insulin resistance: "
                           "a beautiful antique brass key near a keyhole "
                           "slightly out of alignment, warm lighting",
    "cortisol_estresse": "Calming scene: a steaming mug of chamomile tea "
                        "on wooden desk next to open journal and fresh "
                        "herbs, soft morning light",
    "vitamina_d": "Warm sunlight streaming through window onto wooden "
                 "surface with a fresh glass of water and vitamin bottle, "
                 "editorial style",
    "menopausa": "Mature woman (fictional, late 50s, confident expression) "
                "in warm lighting, soft editorial portrait, conveying "
                "vitality and wisdom",
}

for slug, specific in topics.items():
    full_prompt = f"{BRAND}\n\nSpecific image: {specific}"
    img = client.generate(full_prompt, aspect="4:5")
    img.save(f"posts_ig/{slug}.png")
```

## Caso 3 — Infográfico Educativo

Para aulas, folders de consultório, LinkedIn:

```python
# Eixo HPA em estilo moderno
prompt = """
Educational medical infographic showing the HPA axis
(hipotálamo → hipófise → adrenais):
- Vertical flow layout, top to bottom
- Each gland drawn in minimalist line-art style
- Arrows showing hormone cascade: CRH → ACTH → Cortisol
- Labels in Portuguese
- Color palette: deep navy #1A365D for primary, warm gold #D4A574 for accents
- Clean white background
- Modern sans-serif typography
- Print-ready quality, 300dpi equivalent
- Attribution space at bottom: 'Clínica Palmiros - Endocrinologia'
- 3:4 portrait aspect ratio for print/LinkedIn
"""

# Usar Nano Banana 2 para texto legível
client.generate(prompt, aspect="3:4",
                model="gemini-3.1-flash-image-preview")
```

## Caso 4 — Material Didático (aulas/CME)

Para apresentações científicas, Hospital Israelita Albert Einstein, aulas de
residência:

```python
# Conceito abstrato de patofisiologia
prompt = """
Scientific illustration for medical lecture on diabetes type 2:
cross-section of a cell membrane showing:
- GLUT4 receptors in different states (active vs internalized)
- Insulin molecules binding to receptors
- Glucose molecules passing through active GLUT4
- Cellular interior with mitochondria
Style: clean medical textbook illustration,
labeled with scientific terminology in English,
muted scientific color palette (teal, soft orange, gray),
white background, 16:9 aspect ratio for slide presentation,
publication quality
"""
```

## Caso 5 — Visualização de Conceito Endo-Complexo

Para explicar para pacientes conceitos difíceis:

```python
# Ritmo circadiano do cortisol
prompt = """
Educational infographic explaining cortisol circadian rhythm:
- 24-hour horizontal timeline at bottom
- Curve showing cortisol levels: peak around 8am, low at midnight
- Small illustrations at key timepoints (waking, mid-morning, afternoon, evening, bedtime)
- Simple language labels in Portuguese
- Warm, approachable color palette
- Patient-friendly style, not overly clinical
- 16:9 aspect ratio for educational handout
"""
```

## Caso 6 — Marketing Bella Derm (Dermatologia)

**ATENÇÃO**: Bella Derm é estética/dermatologia. CFM é ainda mais restritivo
aqui. Nunca gerar antes/depois, pacientes, ou resultados.

### Permitido:
```python
# Ambiente e filosofia
prompt = """
Editorial photography for dermatology clinic:
elegant skincare products arranged on marble surface,
soft natural light, minimalist composition,
muted neutral palette with subtle rose gold accents,
luxury spa aesthetic, no brand names visible,
4:5 aspect ratio for Instagram
"""

# Estrutura da clínica
prompt = """
Modern dermatology clinic treatment room interior,
minimalist design, treatment bed with clean linens,
medical-grade equipment discreetly visible,
warm professional lighting, calming atmosphere,
empty room (no people or patients), editorial style,
16:9 for website
"""

# Conceitos educativos
prompt = """
Educational illustration of skin layers (epidermis, dermis, hypodermis),
anatomical accuracy, labels in Portuguese,
soft clinical style, printed textbook aesthetic,
beige and warm browns palette
"""
```

### Proibido (não gere):
- Rosto de pessoa (mesmo fictícia) em contexto "antes de tratamento X"
- Pele com problema dermatológico específico identificável
- Qualquer imagem que sugira transformação prometida

## Caso 7 — Avatar/Ícone Profissional

Para redes sociais profissionais, email signature, palestras:

```python
# AVATAR PARA O PRÓPRIO LUCAS (com sua foto real como referência)
# Precisa de consentimento próprio (óbvio) e LGPD auto-determinação

prompt = """
Professional stylized portrait based on reference photo:
clean editorial style, minimalist background (sage green gradient),
warm professional lighting, confident expression,
white doctor's coat visible, shoulders-up composition,
slightly stylized (not hyper-realistic) for professional use,
suitable for LinkedIn, email signature, speaker profile,
1:1 square aspect ratio
"""

# Com foto sua como referência
r = client.generate(prompt, refs=[sua_foto])
```

## Caso 8 — Conteúdo Clínico Interno (prontuário, discussão)

Para ilustrar caso em prontuário ou discussão clínica interna (não publicidade):

```python
# Ilustração de conceito para explicar para paciente
prompt = """
Simple medical illustration for patient education:
cross-section of adrenal gland with cortex and medulla clearly differentiated,
pathology highlighted (e.g., adenoma) with subtle red glow,
clean educational style, labeled in Portuguese,
suitable for one-on-one patient consultation,
printable handout style
"""
```

## Caso 9 — Cover de Aula / Palestra

Para cursos, videos educativos, apresentações congressuais:

```python
prompt = """
Conference presentation cover slide:
title 'Resistência à Insulina: Do Conceito à Prática Clínica'
(Nano Banana 2 renders this correctly)
subtitle 'Dr. Lucas Palmiro - Endocrinologia'
background: subtle molecular/cellular pattern in blue-gray,
clean modern academic style, 16:9 aspect ratio,
professional conference aesthetic, CME-appropriate
"""

client.generate(prompt, aspect="16:9",
                model="gemini-3.1-flash-image-preview")
```

## Caso 10 — Ilustração para Patent Documents

Para as patentes que você já desenvolve (Toroidal NVRAM, CrystalShield, AMYGDALA):

```python
# Figura técnica de patente
prompt = """
Technical patent figure illustration:
toroidal power delivery network with cardiac-inspired hierarchy,
three-tier architecture (SA, AV, Purkinje equivalents),
line-art style with numbered callouts,
black and white only, suitable for USPTO/INPI submission,
clear geometric precision, technical drawing aesthetic,
landscape orientation
"""
```

## Integração com Palmiros-Brain (Obsidian + Claudian)

Workflow: geração on-demand dentro do vault.

```python
# Script em LXC 220 (Brain) que observa notas com tag #generate-image
import frontmatter
from pathlib import Path

VAULT = Path("/vault/Palmiros-Brain")
client = NanoBananaClient(output_dir="/vault/Palmiros-Brain/_assets/generated")

for md_file in VAULT.rglob("*.md"):
    post = frontmatter.load(md_file)
    if "generate-image" in post.metadata.get("tags", []):
        prompt = post.metadata.get("image_prompt")
        if prompt and not post.metadata.get("image_generated"):
            img = client.generate(prompt)
            img_filename = f"{md_file.stem}_{int(time.time())}.png"
            img.save(VAULT / "_assets/generated" / img_filename)

            # Atualiza nota com link da imagem e marca como gerada
            post.metadata["image_generated"] = img_filename
            post.content = f"![[{img_filename}]]\n\n" + post.content
            frontmatter.dump(post, md_file)
```

## Integração com n8n (palmiros.app.n8n.cloud)

Fluxo automático: nova postagem de blog → gerar imagem hero → publicar no
Instagram/LinkedIn.

```yaml
# Workflow n8n conceitual
1. Webhook trigger (novo post em CMS)
2. Extract → título + primeiro parágrafo como contexto
3. Function node → compose prompt com BRAND_STYLE + context
4. HTTP Request → Gemini API endpoint
5. Function → extrai base64, converte para binary
6. Google Drive → salva no folder "Marketing/Generated"
7. Instagram Business API → cria post draft
8. Notify Slack / Telegram com preview
```

## Monitoramento de Custo

Projeção realista para stack Palmiros:

| Uso | Imagens/mês | Custo |
|-----|-------------|-------|
| 30 posts Instagram (3 versões A/B) | 90 | $3.51 |
| 4 banners de site | 12 | $0.47 |
| 20 infográficos educativos | 40 | $1.56 |
| 100 edits iterativos | 100 | $3.90 |
| **Total mensal estimado** | **242** | **~$9.44** |

Bem razoável para substituir custo de banco de imagens (Shutterstock ~$29/mo)
+ designer externo para variações rápidas.

## Prompts Templates Prontos

Crie arquivo `~/.nano-banana/templates.yaml`:

```yaml
clinica_hero:
  model: gemini-3.1-flash-image-preview
  aspect: "16:9"
  base: |
    Editorial photograph for Clínica Palmiros website hero.
    Modern medical clinic interior, wide angle, golden hour lighting,
    sage green and brushed brass palette, sophisticated and welcoming.

instagram_educativo:
  model: gemini-2.5-flash-image
  aspect: "4:5"
  base: |
    Clínica Palmiros Instagram post, editorial photography style,
    sage green #7A9B8E and brushed brass #C9A876 palette,
    generous negative space, no text in image.

infografico_medical:
  model: gemini-3.1-flash-image-preview
  aspect: "3:4"
  base: |
    Educational medical infographic, clean modern style,
    labeled in Portuguese, navy #1A365D and gold #D4A574 palette,
    print-ready, white background.
```

Usar via helper:
```python
def from_template(template_name, specific_content):
    tpl = yaml.safe_load(open("~/.nano-banana/templates.yaml"))[template_name]
    return client.generate(
        prompt=f"{tpl['base']}\n\nSpecific: {specific_content}",
        aspect=tpl['aspect'],
        model=tpl['model'],
    )

# Uso
img = from_template("instagram_educativo",
                    "Theme: vitamin D importance for bone health")
```
