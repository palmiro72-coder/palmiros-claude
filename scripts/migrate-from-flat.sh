#!/usr/bin/env bash
#
# migrate-from-flat.sh
# ====================
# Migra skills do layout flat (~/skills-palmiros/skills/<skill>/SKILL.md)
# para o layout de plugins (plugins/<plugin>/skills/<skill>/SKILL.md).
#
# Uso:
#   ./scripts/migrate-from-flat.sh /caminho/para/skills-palmiros [--copy|--symlink|--move]
#
# Default: --copy (mais seguro). --symlink mantém edição central no repo antigo.
# --move só depois de confirmar que tudo está versionado.
#
# Requisitos: bash 4+, rsync (para --copy), ln (para --symlink).
#
set -euo pipefail

SOURCE="${1:-$HOME/skills-palmiros}"
MODE="${2:---copy}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ ! -d "$SOURCE" ]]; then
  echo "ERRO: diretório de origem não encontrado: $SOURCE" >&2
  exit 1
fi

# Mapa: skill_name:plugin_destino (array paralelo, compatível com bash 3.2/macOS)
SKILL_MAP=(
  # Clinical BR
  conta-ambulatorial:palmiros-clinical-br
  anti-glosa:palmiros-clinical-br
  medical-reports:palmiros-clinical-br
  clinical-data-analysis:palmiros-clinical-br
  whatsapp-medical-bot:palmiros-clinical-br
  endo-derm-sales:palmiros-clinical-br

  # Clinical US
  denial-shield:palmiros-clinical-us

  # Research
  harmonia:palmiros-research
  patent-writer:palmiros-research
  mining:palmiros-research

  # Creative
  nano-banana:palmiros-creative

  # SecOps
  bug-bounty:palmiros-secops
  security-audit:palmiros-secops
  infra-devops:palmiros-secops
)

echo "==> Origem:  $SOURCE"
echo "==> Destino: $ROOT"
echo "==> Modo:    $MODE"
echo

# Localiza o diretório que contém os SKILL.md de cada skill
# Aceita ambos os layouts: ~/skills-palmiros/<skill>/SKILL.md
# e ~/skills-palmiros/skills/<skill>/SKILL.md
find_skill_dir() {
  local skill="$1"
  if [[ -f "$SOURCE/$skill/SKILL.md" ]]; then
    echo "$SOURCE/$skill"
  elif [[ -f "$SOURCE/skills/$skill/SKILL.md" ]]; then
    echo "$SOURCE/skills/$skill"
  else
    return 1
  fi
}

migrate_one() {
  local skill="$1" plugin="$2"
  local src dst
  src="$(find_skill_dir "$skill")" || {
    echo "  [skip] $skill — SKILL.md não encontrado em $SOURCE"
    return
  }
  dst="$ROOT/plugins/$plugin/skills/$skill"

  case "$MODE" in
    --copy)
      mkdir -p "$dst"
      rsync -a --delete "$src"/ "$dst"/
      echo "  [copy] $skill -> $plugin"
      ;;
    --symlink)
      mkdir -p "$(dirname "$dst")"
      [[ -e "$dst" ]] && rm -rf "$dst"
      ln -s "$src" "$dst"
      echo "  [link] $skill -> $plugin"
      ;;
    --move)
      mkdir -p "$(dirname "$dst")"
      [[ -e "$dst" ]] && rm -rf "$dst"
      mv "$src" "$dst"
      echo "  [move] $skill -> $plugin"
      ;;
    *)
      echo "ERRO: modo inválido: $MODE (use --copy, --symlink ou --move)" >&2
      exit 2
      ;;
  esac
}

for entry in "${SKILL_MAP[@]}"; do
  skill="${entry%%:*}"
  plugin="${entry##*:}"
  migrate_one "$skill" "$plugin"
done

echo
echo "==> Migração concluída. Validando estrutura..."
for plugin in palmiros-clinical-br palmiros-clinical-us palmiros-research palmiros-creative palmiros-secops; do
  count=$(find "$ROOT/plugins/$plugin/skills" -name SKILL.md 2>/dev/null | wc -l)
  printf "  %-26s %d skills\n" "$plugin" "$count"
done

echo
echo "==> Próximos passos:"
echo "  1) cd $ROOT && claude plugin validate ."
echo "  2) git init && git add . && git commit -m 'feat: initial marketplace'"
echo "  3) git remote add origin git@github.com:palmiro72-coder/palmiros-claude.git"
echo "  4) git push -u origin main"
echo "  5) Em qualquer máquina: /plugin marketplace add palmiro72-coder/palmiros-claude"
