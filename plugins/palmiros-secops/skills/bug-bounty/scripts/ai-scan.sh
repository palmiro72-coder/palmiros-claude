#!/usr/bin/env bash
# ai-scan.sh — roda semgrep + claude-cli em source-code/ e dumpa em ai-analysis/
# Uso: ./ai-scan.sh <target-name> <language>
#   language: java | python | node | go | c | generic

set -euo pipefail

BOUNTY_ROOT="${BOUNTY_ROOT:-$HOME/bounty}"
TARGET="${1:-}"
LANG="${2:-generic}"

if [[ -z "$TARGET" ]]; then
    echo "Uso: $0 <target-name> <language>" >&2
    echo "Linguagens: java, python, node, go, c, generic" >&2
    exit 1
fi

TARGET_DIR="$BOUNTY_ROOT/$TARGET"
[[ -d "$TARGET_DIR" ]] || { echo "Target não existe: $TARGET_DIR" >&2; exit 1; }
cd "$TARGET_DIR"

SRC_DIR="source-code"
[[ -d "$SRC_DIR" ]] || { echo "source-code/ vazio. Clone repos primeiro." >&2; exit 1; }
[[ -n "$(ls -A "$SRC_DIR" 2>/dev/null)" ]] || { echo "source-code/ vazio." >&2; exit 1; }

# Checar ai_policy
AI_POLICY=$(grep -i '^# ai_policy:' scope.txt | sed 's/.*: *//' | awk '{print $1}' || echo "unknown")
if [[ "$AI_POLICY" == "banned" ]]; then
    echo "⚠ ai_policy=banned para este programa. Abortando." >&2
    echo "Se tem certeza, edite scope.txt." >&2
    exit 1
fi

mkdir -p ai-analysis
TIMESTAMP=$(date -u +%Y%m%d-%H%M%S)
RUN_DIR="ai-analysis/run-$TIMESTAMP-$LANG"
mkdir -p "$RUN_DIR"

echo "=== AI scan: target=$TARGET, lang=$LANG ==="
echo "Output: $RUN_DIR"
echo ""

# 1. Semgrep (sempre roda — baseline estático)
if command -v semgrep >/dev/null 2>&1; then
    echo "[1/3] semgrep..."
    semgrep --config=auto --json --output="$RUN_DIR/semgrep.json" "$SRC_DIR" 2>"$RUN_DIR/semgrep.log" || true
    semgrep --config=auto --output="$RUN_DIR/semgrep.txt" "$SRC_DIR" 2>>"$RUN_DIR/semgrep.log" || true
    SEMGREP_COUNT=$(grep -c '^' "$RUN_DIR/semgrep.txt" 2>/dev/null || echo 0)
    echo "  → $SEMGREP_COUNT linhas em semgrep.txt"
else
    echo "[1/3] semgrep não instalado — pulando"
fi

# 2. Claude-cli (se instalado e ai_policy permite)
PROMPT_FILE=""
case "$LANG" in
    java)    PROMPT_FILE="ai-prompts/java-spring.md" ;;
    python)  PROMPT_FILE="ai-prompts/python-django.md" ;;
    node)    PROMPT_FILE="ai-prompts/node-express.md" ;;
    go)      PROMPT_FILE="ai-prompts/go.md" ;;
    c)       PROMPT_FILE="ai-prompts/c-cpp.md" ;;
    generic) PROMPT_FILE="ai-prompts/generic.md" ;;
    *) echo "Linguagem desconhecida: $LANG" >&2; exit 1 ;;
esac

if command -v claude >/dev/null 2>&1; then
    echo "[2/3] claude-cli análise ($LANG)..."

    # Prompt inline (idealmente externalizado)
    PROMPT=$(cat <<'EOF'
Você é um security researcher revisando o código em ./source-code/.
Analise buscando vulnerabilidades EXPLOITABLE, não code smells.

Formato de saída em Markdown:

## Top candidatos (max 10)

| # | Arquivo:linha | Classe | CWE | Evidência (trecho curto) | Exploit hipótese |
|---|---------------|--------|-----|--------------------------|------------------|

Regras:
- Só inclua candidatos com probabilidade >40% de exploit real
- Cite arquivo e linha SEMPRE
- CWE específico (nunca CWE-20 ou CWE-200 genérico)
- Priorize: auth bypass > RCE > SQLi > SSRF > IDOR > XSS
- Se ambiguidade alta, marque com [?] e justifique

## Áreas que merecem revisão manual profunda
- Liste 3-5 áreas onde você suspeitou mas não conseguiu concluir

## Cross-references sugeridas
- Se o código referencia services externos (microsserviços), aponte qual é
  candidato a cross-service invariant violation
EOF
)

    claude -p "$PROMPT" \
           --allowedTools "Read,Glob,Grep,Bash(ls:*),Bash(find:*),Bash(wc:*),Bash(head:*),Bash(tail:*)" \
           > "$RUN_DIR/claude-findings.md" 2>"$RUN_DIR/claude.log" || true

    if [[ -s "$RUN_DIR/claude-findings.md" ]]; then
        echo "  → claude-findings.md gerado ($(wc -l < "$RUN_DIR/claude-findings.md") linhas)"
    else
        echo "  ⚠ claude-findings.md vazio — ver claude.log"
    fi
else
    echo "[2/3] claude-cli não instalado — pulando"
    echo "Instale: npm install -g @anthropic-ai/claude-code"
fi

# 3. Trufflehog em git history (se for repo git)
echo "[3/3] trufflehog (secrets)..."
find "$SRC_DIR" -maxdepth 2 -name '.git' -type d | while read -r gitdir; do
    repo_dir=$(dirname "$gitdir")
    repo_name=$(basename "$repo_dir")
    if command -v trufflehog >/dev/null 2>&1; then
        trufflehog git "file://$repo_dir" --json > "$RUN_DIR/trufflehog-$repo_name.json" 2>/dev/null || true
    else
        # fallback: docker
        docker run --rm -v "$repo_dir:/repo" trufflesecurity/trufflehog:latest \
            git file:///repo --json > "$RUN_DIR/trufflehog-$repo_name.json" 2>/dev/null || true
    fi
done
echo "  → ver $RUN_DIR/trufflehog-*.json"

# Resumo
echo ""
echo "=== Scan concluído ==="
echo "Próximos passos:"
echo "  1. Abra $RUN_DIR/claude-findings.md"
echo "  2. Filtrar false positives (humano)"
echo "  3. Salvar achados validados em ai-analysis/triaged.md"
echo "  4. Validar no target real antes de report"
