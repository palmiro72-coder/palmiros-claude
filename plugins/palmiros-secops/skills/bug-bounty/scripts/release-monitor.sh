#!/usr/bin/env bash
# release-monitor.sh — monitora releases de repos públicos do target para
# capturar janela de novelty premium (24-72h após release nova).
# Uso: ./release-monitor.sh <target-name>
# Lê $TARGET_DIR/repos-to-monitor.txt (formato: owner/repo, um por linha).
# Grava estado em $TARGET_DIR/recon/last-releases.json para comparar runs.
# Ideal rodar via cron 4x/dia.

set -euo pipefail

BOUNTY_ROOT="${BOUNTY_ROOT:-$HOME/bounty}"
TARGET="${1:-}"

if [[ -z "$TARGET" ]]; then
    echo "Uso: $0 <target-name>" >&2
    exit 1
fi

TARGET_DIR="$BOUNTY_ROOT/$TARGET"
[[ -d "$TARGET_DIR" ]] || { echo "Target não existe: $TARGET_DIR" >&2; exit 1; }

REPOS_FILE="$TARGET_DIR/repos-to-monitor.txt"
STATE_FILE="$TARGET_DIR/recon/last-releases.json"
NOTIFY_LOG="$TARGET_DIR/recon/release-notifications.log"

[[ -f "$REPOS_FILE" ]] || { echo "Crie $REPOS_FILE com 1 repo por linha (owner/repo)" >&2; exit 1; }
mkdir -p "$TARGET_DIR/recon"
touch "$STATE_FILE" "$NOTIFY_LOG"

# Carregar estado anterior (map de repo → last release tag)
declare -A LAST_SEEN
if [[ -s "$STATE_FILE" ]]; then
    while IFS='=' read -r repo tag; do
        [[ -n "$repo" ]] && LAST_SEEN["$repo"]="$tag"
    done < <(jq -r 'to_entries | .[] | "\(.key)=\(.value)"' "$STATE_FILE" 2>/dev/null || true)
fi

# Token GitHub opcional (evita rate limit)
AUTH_HEADER=""
if [[ -n "${GITHUB_TOKEN:-}" ]]; then
    AUTH_HEADER="Authorization: token $GITHUB_TOKEN"
fi

declare -A NEW_STATE
NEW_RELEASES=0

while IFS= read -r repo; do
    # Ignorar comentários e linhas vazias
    repo=$(echo "$repo" | awk '{$1=$1}1' | sed 's/#.*//')
    [[ -z "$repo" ]] && continue

    # GitHub API: latest release
    if [[ -n "$AUTH_HEADER" ]]; then
        RESP=$(curl -s -H "$AUTH_HEADER" -H "Accept: application/vnd.github+json" \
            "https://api.github.com/repos/$repo/releases/latest" 2>/dev/null || echo "")
    else
        RESP=$(curl -s -H "Accept: application/vnd.github+json" \
            "https://api.github.com/repos/$repo/releases/latest" 2>/dev/null || echo "")
    fi

    TAG=$(echo "$RESP" | jq -r '.tag_name // empty' 2>/dev/null || echo "")
    NAME=$(echo "$RESP" | jq -r '.name // empty' 2>/dev/null || echo "")
    URL=$(echo "$RESP" | jq -r '.html_url // empty' 2>/dev/null || echo "")
    DATE=$(echo "$RESP" | jq -r '.published_at // empty' 2>/dev/null || echo "")

    if [[ -z "$TAG" ]]; then
        echo "  [skip] $repo — sem release ou erro de API"
        continue
    fi

    NEW_STATE["$repo"]="$TAG"

    LAST="${LAST_SEEN[$repo]:-}"
    if [[ "$LAST" != "$TAG" ]]; then
        NEW_RELEASES=$((NEW_RELEASES + 1))
        NOW=$(date -u +%FT%TZ)
        MSG="[$NOW] NEW RELEASE: $repo $TAG (\"$NAME\") published $DATE → $URL"
        echo "$MSG"
        echo "$MSG" >> "$NOTIFY_LOG"

        # Opcional: notificar via webhook se NOTIFY_WEBHOOK setado
        if [[ -n "${NOTIFY_WEBHOOK:-}" ]]; then
            curl -s -X POST -H "Content-Type: application/json" \
                -d "{\"text\":\"🎯 $repo — nova release $TAG. Janela de novelty premium: 24-72h. $URL\"}" \
                "$NOTIFY_WEBHOOK" >/dev/null 2>&1 || true
        fi
    else
        echo "  [=] $repo @ $TAG (sem mudança)"
    fi
done < "$REPOS_FILE"

# Persistir novo estado
{
    echo "{"
    FIRST=1
    for repo in "${!NEW_STATE[@]}"; do
        [[ $FIRST -eq 0 ]] && echo ","
        FIRST=0
        printf '  "%s": "%s"' "$repo" "${NEW_STATE[$repo]}"
    done
    echo ""
    echo "}"
} > "$STATE_FILE"

echo ""
echo "=== Monitor concluído ==="
echo "Novas releases: $NEW_RELEASES"
echo "Log: $NOTIFY_LOG"
echo ""
echo "Sugestão de cron (a cada 6h):"
echo "  0 */6 * * * $HOME/.claude/skills/bug-bounty/scripts/release-monitor.sh $TARGET"
