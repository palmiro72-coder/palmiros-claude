---
name: security-audit
description: "Auditoria de segurança para apps e infraestrutura. Identifica vulnerabilidades, hardening, Ghidra, pentest. Conformidade LGPD/HIPAA, OWASP Top 10."
---

# Security Audit — Skill de Segurança e Auditoria

Auditoria de segurança e proteção de infraestrutura com foco em ambientes
médicos e dados sensíveis de saúde.

## Escopo de Atuação

### 1. Infraestrutura
- Hardening de servidores Linux/Windows
- Auditoria de firewalls (pfSense/OPNsense)
- Segmentação de rede (VLANs)
- Segurança WiFi (WPA3, 802.1X)
- VPN e acesso remoto seguro
- Monitoramento e detecção de intrusão

### 2. Aplicações
- OWASP Top 10 (2025)
- Análise de código estático (SAST)
- Teste dinâmico (DAST)
- Segurança de APIs REST/GraphQL
- Autenticação e autorização
- Injeção, XSS, CSRF, SSRF

### 3. Engenharia Reversa
- Análise de binários com Ghidra
- Decompilação e análise de malware (defensiva)
- Análise de firmware de dispositivos médicos
- Protocolo de comunicação reversing
- Análise de tráfego criptografado

### 4. Compliance
- LGPD (Lei Geral de Proteção de Dados)
- CFM (dados médicos)
- HIPAA (se aplicável internacionalmente)
- PCI DSS (dados de pagamento)
- ISO 27001 / 27799 (saúde)

## OWASP Top 10 — Checklist

| # | Vulnerabilidade | Verificação |
|---|----------------|-------------|
| A01 | Broken Access Control | Testar escalação horizontal/vertical |
| A02 | Cryptographic Failures | Verificar TLS, hashing, armazenamento |
| A03 | Injection | SQL, NoSQL, OS, LDAP injection |
| A04 | Insecure Design | Threat modeling, princípios de segurança |
| A05 | Security Misconfiguration | Headers, defaults, permissões |
| A06 | Vulnerable Components | Dependências desatualizadas |
| A07 | Auth Failures | Brute force, session, credential stuffing |
| A08 | Data Integrity Failures | CI/CD, desserialização, updates |
| A09 | Logging Failures | Log injection, monitoramento insuficiente |
| A10 | SSRF | Server-side request forgery |

## Hardening Linux — Checklist Completo

### SSH
```bash
# /etc/ssh/sshd_config
Port 2222                           # Porta não-padrão
PermitRootLogin no                  # Sem root SSH
PasswordAuthentication no           # Apenas chaves
PubkeyAuthentication yes
MaxAuthTries 3
AllowUsers admin                    # Whitelist de usuários
ClientAliveInterval 300
ClientAliveCountMax 2
```

### Firewall (UFW)
```bash
ufw default deny incoming
ufw default allow outgoing
ufw allow from 10.0.10.0/24 to any port 22  # SSH apenas da VLAN corp
ufw allow 443/tcp                             # HTTPS
ufw enable
ufw logging on
```

### Fail2Ban
```ini
# /etc/fail2ban/jail.local
[sshd]
enabled = true
port = 2222
maxretry = 3
bantime = 3600
findtime = 600

[nginx-http-auth]
enabled = true
maxretry = 5
```

### Auditoria
```bash
# auditd - monitorar arquivos sensíveis
auditctl -w /etc/passwd -p wa -k identity
auditctl -w /etc/shadow -p wa -k identity
auditctl -w /etc/ssh/sshd_config -p wa -k sshd
auditctl -w /var/log/ -p wa -k logs
```

## Ghidra — Engenharia Reversa

### Workflow de Análise
```
1. IMPORTAÇÃO
   ├── Carregar binário
   ├── Auto-análise (CodeBrowser)
   └── Identificar formato (PE, ELF, ARM)

2. RECONHECIMENTO
   ├── Strings → identificar funcionalidades
   ├── Imports/Exports → dependências
   ├── Entry points → fluxo principal
   └── Cross-references → call graph

3. ANÁLISE
   ├── Decompiler view → pseudo-C
   ├── Renomear funções/variáveis
   ├── Anotar estruturas de dados
   ├── Identificar padrões (crypto, network, file I/O)
   └── Script Ghidra (Java/Python) para automação

4. DOCUMENTAÇÃO
   ├── Mapa de funções com descrições
   ├── Fluxo de dados sensíveis
   ├── Vulnerabilidades encontradas
   └── Relatório técnico
```

### Scripts Ghidra Úteis
```python
# Listar todas as strings com referências
from ghidra.program.util import DefinedDataIterator
for data in DefinedDataIterator.definedStrings(currentProgram):
    refs = getReferencesTo(data.getAddress())
    if len(refs) > 0:
        print(f"{data.getAddress()}: {data.getValue()} ({len(refs)} refs)")
```

## Análise de Tráfego de Rede

### Ferramentas
- **tcpdump**: Captura rápida em CLI
- **Wireshark/tshark**: Análise detalhada
- **Zeek (Bro)**: Análise de protocolo
- **Suricata**: IDS/IPS com regras ET

### Detecção de Anomalias
```bash
# Conexões suspeitas - tráfego para portas incomuns
tcpdump -i eth0 'tcp[tcpflags] & (tcp-syn) != 0 and not port 80 and not port 443'

# DNS queries suspeitas (exfiltração)
tcpdump -i eth0 port 53 -w dns_capture.pcap

# Tráfego lateral não autorizado entre VLANs
tcpdump -i vlan30 'src net 10.0.30.0/24 and dst net 10.0.10.0/24'
```

## LGPD para Dados Médicos

### Classificação de Dados
| Categoria | Exemplos | Proteção |
|-----------|----------|----------|
| Dados Pessoais | Nome, CPF, endereço | Consentimento + criptografia |
| Dados Sensíveis | Diagnóstico, exames, prontuário | Consentimento explícito + criptografia forte |
| Dados Anonimizados | Estatísticas agregadas | Liberado para pesquisa |

### Medidas Técnicas Obrigatórias
1. **Criptografia em repouso** (AES-256 para databases)
2. **Criptografia em trânsito** (TLS 1.3)
3. **Controle de acesso** (RBAC + MFA)
4. **Logs de acesso** imutáveis (append-only)
5. **Backup criptografado** com chaves segregadas
6. **Pseudoanonimização** para pesquisa
7. **Direito ao esquecimento** com workflow definido
8. **DPO** (Encarregado) designado

### Retenção de Dados Médicos
- Prontuário: **mínimo 20 anos** (CFM Resolução 1.821/2007)
- Dados de pagamento: **5 anos** (fiscal)
- Logs de acesso: **mínimo 6 meses** (Marco Civil)
- Imagens/exames: **20 anos** (vinculados ao prontuário)

## Criptografia Aplicada

### Padrões Recomendados
| Uso | Algoritmo | Tamanho |
|-----|-----------|---------|
| Simétrica (dados) | AES-256-GCM | 256 bits |
| Hash (senhas) | Argon2id | config tuned |
| Assinatura | Ed25519 | 256 bits |
| TLS | TLS 1.3 | - |
| Disco | LUKS2 + AES-XTS | 512 bits |
| Pós-quântica | CRYSTALS-Kyber / Dilithium | NIST Level 3+ |

## Relatório de Auditoria — Template

```
1. SUMÁRIO EXECUTIVO
   - Escopo da auditoria
   - Criticidade geral
   - Top 5 findings

2. METODOLOGIA
   - Ferramentas utilizadas
   - Escopo e limitações
   - Classificação de severidade

3. FINDINGS
   Para cada vulnerabilidade:
   ├── ID e título
   ├── Severidade (Critical/High/Medium/Low/Info)
   ├── CVSS score
   ├── Descrição técnica
   ├── Evidência (screenshot/log)
   ├── Impacto
   ├── Recomendação
   └── Referências (CVE, CWE)

4. RECOMENDAÇÕES PRIORIZADAS
   - Quick wins (< 1 semana)
   - Médio prazo (1-3 meses)
   - Longo prazo (3-12 meses)

5. CONCLUSÃO
```

## Exemplos de Uso

- "Faça uma auditoria de segurança da configuração do pfSense"
- "Analise este binário com Ghidra e identifique funções de rede"
- "Verifique compliance LGPD do sistema de prontuário"
- "Revise a configuração de SSL/TLS dos serviços expostos"
- "Monte um relatório de pentest da aplicação web da clínica"
- "Configure Suricata como IDS na rede da clínica"
- "Hardening do servidor Proxmox seguindo CIS Benchmark"
