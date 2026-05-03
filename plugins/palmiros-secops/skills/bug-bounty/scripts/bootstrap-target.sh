#!/usr/bin/env bash
# bootstrap-target.sh — cria estrutura padrão de um novo alvo de bug bounty
# Uso: ./bootstrap-target.sh <target-name> [platform] [ai-policy]
#   target-name: slug curto (ex: acme, stark-bank)
#   platform: hackerone|bugcrowd|intigriti|yeswehack|bughunt|hackaflag|synack|zdi (default: hackerone)
#   ai-policy: allowed|disclosure_required|banned (default: banned — default conservador)

set -euo pipefail

BOUNTY_ROOT="${BOUNTY_ROOT:-$HOME/bounty}"
TARGET="${1:-}"
PLATFORM="${2:-hackerone}"
AI_POLICY="${3:-banned}"

if [[ -z "$TARGET" ]]; then
    echo "Uso: $0 <target-name> [platform] [ai-policy]" >&2
    echo "Ex: $0 acme hackerone disclosure_required" >&2
    exit 1
fi

# Validar ai_policy
case "$AI_POLICY" in
    allowed|disclosure_required|banned) ;;
    *) echo "ai-policy inválido. Use: allowed, disclosure_required, banned" >&2; exit 1 ;;
esac

TARGET_DIR="$BOUNTY_ROOT/$TARGET"

if [[ -d "$TARGET_DIR" ]]; then
    echo "Target já existe: $TARGET_DIR" >&2
    exit 1
fi

mkdir -p "$TARGET_DIR"/{recon,source-code,ai-analysis,fuzz,nuclei,burp,findings,reports/submitted,reports/drafts}

# scope.txt template
cat > "$TARGET_DIR/scope.txt" <<EOF
# Target: $TARGET
# Platform: $PLATFORM
# Created: $(date -u +%Y-%m-%dT%H:%M:%SZ)
# Last updated: $(date -u +%Y-%m-%dT%H:%M:%SZ)
# ai_policy: $AI_POLICY

in_scope:
  # *.${TARGET}.com
  # api.${TARGET}.com

out_of_scope:
  # marketing.${TARGET}.com
  # third-party SSO

test_accounts:
  # user1@example.com / senha (low-priv)
  # user2@example.com / senha (high-priv)

notes:
  # Observações específicas do programa (rate limits, headers, etc.)
EOF

# repos-to-monitor.txt para release-monitor.sh
touch "$TARGET_DIR/repos-to-monitor.txt"

# README com checklist inicial
cat > "$TARGET_DIR/README.md" <<EOF
# $TARGET — Bug Bounty Workspace

**Platform:** $PLATFORM
**AI Policy:** $AI_POLICY
**Started:** $(date -u +%Y-%m-%d)

## Checklist inicial
- [ ] Ler programa inteiro (policy, scope, rewards, rules)
- [ ] Preencher \`scope.txt\` com domínios in/out
- [ ] Criar test accounts se programa fornece
- [ ] Identificar repos públicos → adicionar em \`repos-to-monitor.txt\`
- [ ] Rodar \`recon.sh $TARGET\` (recon passiva + ativa)
- [ ] Clonar source-code público em \`source-code/\`
- [ ] Rodar \`ai-scan.sh $TARGET <lang>\` (análise estática + LLM)
- [ ] Triar achados → \`ai-analysis/triaged.md\`
- [ ] Validar top candidates no target real

## Estrutura
\`\`\`
$TARGET/
├── scope.txt                  # in-scope + ai_policy
├── repos-to-monitor.txt       # repos para release-monitor.sh
├── recon/                     # saída de recon
├── source-code/               # repos clonados
├── ai-analysis/               # outputs de LLM/semgrep/codeql
├── fuzz/                      # resultados ffuf/feroxbuster
├── nuclei/                    # scan logs
├── burp/                      # Burp project files
├── findings/                  # 1 md por bug validado
└── reports/
    ├── drafts/                # em construção
    └── submitted/             # enviados
\`\`\`
EOF

echo "✓ Target '$TARGET' criado em $TARGET_DIR"
echo "  Platform: $PLATFORM"
echo "  AI Policy: $AI_POLICY"
echo ""
echo "Próximos passos:"
echo "  1. Edite $TARGET_DIR/scope.txt com os domínios in/out"
echo "  2. ./recon.sh $TARGET"
