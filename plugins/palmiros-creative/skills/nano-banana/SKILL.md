---
name: nano-banana
description: Geração e edição de imagens via Gemini 2.5 Flash Image (Nano Banana) e Gemini 3.1 Flash Image (Nano Banana 2) do Google. Cobre text-to-image, edição iterativa por linguagem natural, blend de múltiplas imagens, consistência de personagem/identidade, multi-turn conversational editing, controle de aspect ratio e uso via Python SDK/REST/curl. Use sempre que o usuário mencionar Nano Banana, Gemini image, geração de imagem, criar imagem, editar imagem com IA, image-to-image, fazer arte com Gemini, gerar foto a partir de texto, modificar imagem com prompt, marketing visual médico, criar banner/post para Clínica Palmiros ou Bella Derm, visualização de caso clínico (sem foto real de paciente), infográfico, ou qualquer workflow de criação visual via IA generativa.
---

# Nano Banana — Skill de Geração e Edição de Imagens via Gemini

Uso do Gemini 2.5 Flash Image ("Nano Banana") e Gemini 3.1 Flash Image
("Nano Banana 2") do Google para geração e edição de imagens por texto.

## Por que Nano Banana

Diferenciais vs concorrentes (DALL-E 3, Imagen 4, Flux, Midjourney):

1. **Multi-turn editing conversacional** — edita iterativamente mantendo contexto
2. **Character consistency** — mantém personagem/identidade entre prompts
3. **Image blending nativo** — funde múltiplas imagens via linguagem natural
4. **World knowledge integrado** — entende conceitos complexos sem overfitting
5. **Preço baixo** — $0.039/imagem 1024x1024 (bem abaixo de DALL-E 3 a $0.08)
6. **Latência baixa** — arquitetura Flash, ideal para aplicações realtime

## Modelos Disponíveis

| Modelo | Model ID | Lançamento | Uso |
|--------|----------|-----------|-----|
| Nano Banana | `gemini-2.5-flash-image` | Out/2025 | Produção, alto volume, baixo custo |
| Nano Banana 2 | `gemini-3.1-flash-image-preview` | Fev/2026 | Pro-quality, text rendering, 4K, workflows complexos |
| Gemini 3 Pro Image | `gemini-3-pro-image` | 2026 | Máxima qualidade, text rendering perfeito |

### Pricing (Google AI Studio)
- **Input**: $0.30 / 1M tokens
- **Output (texto)**: $2.50 / 1M tokens
- **Output (imagem)**: $30.00 / 1M tokens → **$0.039 por imagem 1024x1024** (1290 tokens)
- Context window: 32.8K tokens (input) / 32.8K tokens (output)

## Setup

### API Key
```bash
# Google AI Studio (mais simples, uso pessoal/dev)
# https://aistudio.google.com/app/apikey
export GEMINI_API_KEY="sk-..."

# Vertex AI (enterprise, mais features e SLA)
gcloud auth application-default login
export GOOGLE_CLOUD_PROJECT="palmiros-ai"
```

### SDK Python
```bash
pip install google-genai pillow
```

### Verificação rápida
```bash
python -c "
from google import genai
client = genai.Client()
r = client.models.generate_content(
    model='gemini-2.5-flash-image',
    contents=['a banana wearing a lab coat, studio photo']
)
for p in r.candidates[0].content.parts:
    if p.inline_data: open('test.png','wb').write(p.inline_data.data)
print('OK')
"
```

## Workflow Padrão

```
1. DEFINIR OBJETIVO
   ├── Tipo: text-to-image, image edit, blend, variation
   ├── Uso: marketing, educativo, visualização, mockup
   └── Restrições: aspect ratio, resolução, estilo

2. PROMPT ENGINEERING
   → Ver references/prompting-patterns.md
   ├── Contexto + composição + estilo + detalhes técnicos
   ├── Negative prompts via descrição ("sem texto", "sem pessoas")
   └── Aspect ratio via image_config

3. GERAÇÃO
   → Ver references/api-usage.md
   ├── Single-shot (text-only) ou multi-modal (text + ref images)
   ├── Salvar output com metadata (prompt original, modelo, timestamp)
   └── Tracking de custo

4. REFINAMENTO (multi-turn)
   → Ver references/editing-workflows.md
   ├── Continue conversation com outputs anteriores
   ├── Edições localizadas ("change only the background")
   └── Consistency across edits

5. VALIDAÇÃO
   ├── Qualidade visual
   ├── Fidelidade ao prompt
   ├── Aspectos éticos (LGPD se envolve pessoas, CFM se clínico)
   └── Watermark SynthID (Google aplica automaticamente)
```

## Arquivos de Referência

- **`references/api-usage.md`** — Python SDK, REST API, curl, streaming, batch,
  integração com n8n. Exemplos reproduzíveis por padrão de uso.
- **`references/prompting-patterns.md`** — Estrutura de prompts eficazes,
  padrões de estilo (photorealistic, illustrated, infográfico, medical),
  controle de composição, aspect ratio, camera/lighting language.
- **`references/editing-workflows.md`** — Multi-turn editing, character
  consistency, image blending, variações, inpainting implícito, upscale.
- **`references/use-cases-medicos.md`** — Aplicações para Clínica Palmiros /
  Bella Derm: posts Instagram, infográficos educativos para pacientes,
  visualização de conceitos endócrinos (sem dados reais de pacientes),
  material para aulas/consultório. Compliance CFM e LGPD.

## Casos de Uso Típicos

```python
# 1. Post de marketing para clínica
prompt = """
Professional medical clinic photo, modern minimalist interior,
soft natural lighting through large windows, neutral palette
(sage green, warm white, brushed brass), sophisticated and welcoming,
no people visible, hero composition, 4:5 aspect ratio for Instagram feed
"""

# 2. Infográfico educativo (endocrinologia)
prompt = """
Minimalist educational illustration of the HPA axis
(hypothalamus, pituitary, adrenal glands),
clean vector style, labeled anatomical structures in Portuguese,
white background, brand colors #2C5F6F and #D4A574,
print-ready, 300 DPI equivalent
"""

# 3. Edit de foto existente (blend com ref)
# input: foto da clínica real + ref de estilo
prompt = "apply the warm golden-hour lighting from image 2 to image 1,
keep the architecture and furniture identical"
```

## Limitações Conhecidas

- **Texto em imagens**: Nano Banana v1 tem dificuldade com textos longos/complexos.
  Para texto crítico, usar Nano Banana 2 ou Imagen 4.
- **Fotorrealismo humano**: pode gerar artifacts em mãos, dentes, olhos.
  Edição iterativa corrige.
- **Watermark SynthID**: todas as imagens geradas têm watermark invisível
  (não afeta qualidade, mas rastreável como AI-generated).
- **Segurança**: filtros bloqueiam violência gráfica, NSFW, conteúdo com menores,
  celebridades por nome, marcas registradas em contexto hostil.
- **Aspect ratios**: nativos são 1:1, 4:5, 9:16, 16:9, 4:3, 3:4, 21:9, 3:2, 2:3.

## Ética e Compliance

### LGPD (se imagem envolve pessoa real)
- Se usar foto de paciente/funcionário como referência → consentimento LGPD Art. 7
- Imagens geradas de pessoas fictícias não precisam consentimento
- Nunca recriar rosto reconhecível de pessoa real sem autorização expressa

### CFM (conteúdo médico)
- Resolução CFM 1.974/2011 — publicidade médica:
  - Proibido antes/depois em procedimentos estéticos (mesmo que gerado por IA)
  - Permitido imagem educativa/ilustrativa genérica
  - Proibido sugerir resultados garantidos
- Marcar como "ilustração artística" ou "imagem ilustrativa" quando gerada por IA

### Copyright
- Não reproduzir obras protegidas (fotos, pinturas identificáveis, personagens)
- Estilos são livres ("pintura impressionista"), obras específicas não
  ("A Noite Estrelada de Van Gogh")

## Exemplos de Uso

- "Gera imagem hero para o site da Clínica Palmiros, estilo profissional"
- "Crie infográfico sobre eixo HPA para aula, estilo minimalista vetor"
- "Edite essa foto da clínica para aplicar iluminação golden hour"
- "Gera 4 variações desse post de Instagram em aspect 4:5"
- "Blend dessas duas imagens mantendo a composição da primeira"
- "Faz série de 10 posts Bella Derm com character consistency da mesma modelo fictícia"
- "Crie capa para apresentação sobre resistência à insulina, estilo TED"
- "Gera ícone de cada hormônio do sistema endócrino, mesmo estilo visual"

## Integração no Stack do Lucas

### Via n8n (palmiros.app.n8n.cloud)
Nodo HTTP Request → endpoint Google → parseia inline_data → salva em Drive/S3.
Útil para pipeline automatizado de posts sociais.

### Via AMYGDALA
Script Python em LXC 220 (Brain) que pega prompt do Obsidian vault
(Palmiros-Brain) e gera imagens para anexar a notas Claudian.

### Via Claudian plugin Obsidian
Comando custom que aciona Nano Banana e embed da imagem na nota atual.

### Via Home Assistant (automação criativa)
`shell_command.gen_image` aciona gerador e publica em `/config/www/` —
acessível via Cloudflare tunnel (ha.hapalmiros.com).
