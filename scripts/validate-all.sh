#!/usr/bin/env bash
#
# validate-all.sh
# ===============
# Valida o marketplace e cada plugin individualmente.
# Roda localmente antes de commitar; também é usado pela CI.
#
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "==> Validating marketplace.json..."
if command -v claude >/dev/null 2>&1; then
  (cd "$ROOT" && claude plugin validate .)
else
  echo "  (claude CLI não encontrado — pulando validação CLI)"
fi

# Validação manual via jq (não depende do CLI)
if ! command -v jq >/dev/null 2>&1; then
  echo "ERRO: jq não instalado. Instale com: sudo apt install jq" >&2
  exit 1
fi

echo "==> Checking marketplace schema..."
jq -e '.name and .owner.name and (.plugins | length > 0)' \
  "$ROOT/.claude-plugin/marketplace.json" >/dev/null
echo "  ok"

echo "==> Checking each plugin manifest..."
fail=0
for dir in "$ROOT"/plugins/*/; do
  name=$(basename "$dir")
  manifest="$dir/.claude-plugin/plugin.json"
  if [[ ! -f "$manifest" ]]; then
    echo "  [FAIL] $name — plugin.json ausente"
    fail=1; continue
  fi
  if ! jq -e '.name and .version and .description' "$manifest" >/dev/null; then
    echo "  [FAIL] $name — campos obrigatórios ausentes"
    fail=1; continue
  fi
  # Conta skills com frontmatter válido (name + description)
  bad=0
  while IFS= read -r f; do
    if ! head -20 "$f" | grep -q '^name:' || ! head -20 "$f" | grep -q '^description:'; then
      echo "  [WARN] $name — $f sem frontmatter name/description"
      bad=$((bad+1))
    fi
  done < <(find "$dir/skills" -name SKILL.md 2>/dev/null)
  total=$(find "$dir/skills" -name SKILL.md 2>/dev/null | wc -l)
  echo "  [ok]   $name  ($total skills, $bad warnings)"
done

if [[ $fail -ne 0 ]]; then
  echo "==> FALHOU — corrija os erros acima."
  exit 1
fi
echo "==> Tudo certo."
