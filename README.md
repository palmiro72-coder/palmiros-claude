# palmiros-claude

Marketplace privado de plugins do Claude Code para a operação Palmiros (Clínica Palmiros + Bella Derm) e projetos pessoais do Dr. Lucas Palmiro.

## Estrutura

```
palmiros-claude/
├── .claude-plugin/
│   └── marketplace.json          # registro de todos os plugins
├── plugins/
│   ├── palmiros-clinical-br/     # 6 skills — operações BR
│   ├── palmiros-clinical-us/     # 1 skill  — RCM US
│   ├── palmiros-research/        # 3 skills — harmonia, patente, mineração
│   ├── palmiros-creative/        # 1 skill  — Nano Banana
│   └── palmiros-secops/          # 3 skills — bug bounty, audit, infra
├── scripts/
│   ├── migrate-from-flat.sh      # importa de ~/skills-palmiros
│   └── validate-all.sh           # valida marketplace + plugins
└── .github/workflows/
    └── validate.yml              # CI
```

## Migração inicial (de `~/skills-palmiros`)

```bash
# 1) clone este repo (ou use direto a pasta gerada)
cd ~/palmiros-claude-marketplace

# 2) copie suas SKILL.md atuais para os plugins
./scripts/migrate-from-flat.sh ~/skills-palmiros --copy

# 3) valide
./scripts/validate-all.sh

# 4) versione e publique
git init && git add . && git commit -m 'feat: initial marketplace'
git remote add origin git@github.com:palmiro72-coder/palmiros-claude.git
git push -u origin main
```

Modos do migrate:
- `--copy` (default) — duplica os arquivos. Mais seguro, permite editar em paralelo.
- `--symlink` — liga; útil enquanto você ainda mantém `~/skills-palmiros` como fonte canônica.
- `--move` — só depois de confirmar que tudo está versionado em outro lugar.

## Uso em qualquer máquina

```bash
# adicionar o marketplace
/plugin marketplace add palmiro72-coder/palmiros-claude

# instalar tudo
/plugin install palmiros-clinical-br@palmiros-claude
/plugin install palmiros-clinical-us@palmiros-claude
/plugin install palmiros-research@palmiros-claude
/plugin install palmiros-creative@palmiros-claude
/plugin install palmiros-secops@palmiros-claude

# ou só o que faz sentido pra máquina (ex.: laptop da clínica)
/plugin install palmiros-clinical-br@palmiros-claude
```

Na recepção, no laptop da Bella Derm, no LXC 220 da AMYGDALA — em todos é o mesmo comando. Acabou o `link-to-claude-code.sh` por máquina.

## Versionamento

Cada plugin tem `version` em `plugin.json`. Suba a versão (semver) sempre que mudar uma skill. O Claude Code detecta atualizações pelo campo version.

```bash
# bump de patch num plugin
jq '.version = "1.0.1"' plugins/palmiros-clinical-br/.claude-plugin/plugin.json > /tmp/p.json \
  && mv /tmp/p.json plugins/palmiros-clinical-br/.claude-plugin/plugin.json
```

## Próximos incrementos sugeridos

1. **Hooks clínicos** — adicionar `hooks/hooks.json` em `palmiros-clinical-br` com PreToolUse que bloqueia `rm` em paths de prontuário e PostToolUse que loga toda chamada no AMYGDALA cortex-bridge.
2. **MCP integration** — declarar o MCP do Home Assistant em `palmiros-secops` via `.mcp.json`, evitando configurar a cada máquina.
3. **Subagents** — criar `agents/anti-glosa-auditor.md` em `palmiros-clinical-br` para delegação isolada de auditoria de contas, preservando o context window principal.

## Notas importantes

- Plugins são copiados para `~/.claude/plugins/cache/` na instalação. **Nada de referência relativa pra fora do diretório do plugin** (`../../shared`). Se precisar compartilhar entre plugins, use symlinks ou duplique.
- Nomes de plugin **devem ser kebab-case** — o sync com Claude.ai rejeita maiúsculas, espaços ou underscores.
- O campo `version` no `marketplace.json` (raiz) é decorativo hoje. Importa o `version` de cada `plugin.json`.
