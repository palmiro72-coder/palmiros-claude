---
name: infra-devops
description: "Gerencia infraestrutura Proxmox, pfSense, UniFi, Docker e Dell PowerEdge. Cria VLANs, VPNs, monitora com Grafana/Home Assistant. Hardening e automação."
---

# Infra DevOps — Skill de Infraestrutura e Operações

Gestão de infraestrutura homelab/clínica com foco em virtualização,
networking e monitoramento.

## Stack de Infraestrutura

### Hardware
- **Servidores**: Dell PowerEdge (rack/tower)
- **Networking**: Ubiquiti UniFi (switches, APs, gateways)
- **Storage**: NAS/SAN (ZFS preferred)

### Virtualização
- **Hypervisor**: Proxmox VE
- **Containers**: Docker / LXC
- **Orquestração**: Docker Compose / Portainer

### Networking & Segurança
- **Firewall**: pfSense / OPNsense
- **DNS**: Pi-hole / AdGuard Home / Unbound
- **VPN**: WireGuard / OpenVPN
- **Proxy reverso**: Nginx Proxy Manager / Traefik / Caddy
- **Certificados**: Let's Encrypt (ACME)
- **WiFi**: UniFi Controller

### Monitoramento
- **Métricas**: Grafana + Prometheus / InfluxDB
- **Logs**: Grafana Loki / Graylog
- **Alertas**: Grafana Alerting / Uptime Kuma
- **Automação**: Home Assistant
- **SNMP/IPMI**: Monitoramento de hardware

## Proxmox VE — Configurações Comuns

### VM Templates
```bash
# Criar template cloud-init Ubuntu
qm create 9000 --name ubuntu-template --memory 2048 --cores 2 \
  --net0 virtio,bridge=vmbr0 --scsihw virtio-scsi-single
qm set 9000 --scsi0 local-lvm:0,import-from=/path/to/ubuntu.img
qm set 9000 --ide2 local-lvm:cloudinit
qm set 9000 --boot order=scsi0
qm set 9000 --serial0 socket --vga serial0
qm template 9000
```

### Backup Strategy
```bash
# Backup agendado - vzdump
vzdump <vmid> --compress zstd --mode snapshot \
  --storage backup-storage --mailnotification always
```

### Clustering
- Quorum e fencing
- Migração live de VMs
- HA (High Availability) groups
- Ceph para storage distribuído

## UniFi — Configuração de Rede

### VLANs Recomendadas para Clínica
| VLAN ID | Nome | Subnet | Uso |
|---------|------|--------|-----|
| 1 | Management | 10.0.1.0/24 | Gerência de equipamentos |
| 10 | Corporativa | 10.0.10.0/24 | Workstations médicas |
| 20 | Servidores | 10.0.20.0/24 | Servidores e storage |
| 30 | IoT | 10.0.30.0/24 | Dispositivos IoT, câmeras |
| 40 | Guests | 10.0.40.0/24 | WiFi pacientes |
| 50 | VoIP | 10.0.50.0/24 | Telefonia IP |
| 99 | DMZ | 10.0.99.0/24 | Serviços expostos |

### WiFi SSIDs
- **Clinica-Corp**: VLAN 10, WPA3, 802.1X opcional
- **Clinica-IoT**: VLAN 30, WPA2, client isolation
- **Clinica-Guests**: VLAN 40, captive portal, bandwidth limit

## pfSense — Regras e Serviços

### Firewall Rules (princípios)
1. Default deny all
2. Permitir apenas tráfego necessário entre VLANs
3. IoT → Internet: sim; IoT → Corporativa: não
4. Guests: internet only, sem acesso à LAN
5. Log de todas as conexões bloqueadas

### Serviços Essenciais
- HAProxy / Nginx para reverse proxy
- Snort/Suricata para IDS/IPS
- OpenVPN / WireGuard para acesso remoto
- DHCP server por VLAN
- DNS resolver com DNSSEC

## Grafana — Dashboards

### Dashboard Infra
```
Painéis essenciais:
├── CPU / RAM / Disco de cada servidor
├── Temperatura dos servidores (IPMI)
├── Tráfego de rede por VLAN
├── Latência e packet loss (Smokeping)
├── Status de VMs e containers
├── Consumo elétrico (se UPS monitorado)
└── Alertas ativos
```

### Dashboard Clínica
```
Painéis de negócio:
├── Agendamentos do dia/semana
├── Tempo médio de espera
├── Taxa de no-show
├── Faturamento diário
├── Status dos equipamentos médicos
└── Ocupação de salas
```

## Home Assistant — Automações

### Automações para Clínica
- Iluminação automática por sala/horário
- HVAC controlado por ocupação
- Alerta de temperatura de equipamentos
- Controle de acesso (integração com fechaduras)
- Monitoramento de consumo energético
- Status de UPS/no-break

## Docker Compose — Serviços Comuns

```yaml
# Stack de monitoramento
services:
  grafana:
    image: grafana/grafana:latest
    ports: ["3000:3000"]
    volumes: ["grafana-data:/var/lib/grafana"]
  
  prometheus:
    image: prom/prometheus:latest
    ports: ["9090:9090"]
    volumes: ["./prometheus.yml:/etc/prometheus/prometheus.yml"]
  
  uptime-kuma:
    image: louislam/uptime-kuma:latest
    ports: ["3001:3001"]
    volumes: ["uptime-data:/app/data"]
  
  portainer:
    image: portainer/portainer-ce:latest
    ports: ["9443:9443"]
    volumes: ["/var/run/docker.sock:/var/run/docker.sock"]
```

## Segurança — Hardening Checklist

### Servidores
- [ ] SSH: key-only auth, porta não-padrão, fail2ban
- [ ] Firewall local (ufw/iptables)
- [ ] Updates automáticos de segurança
- [ ] Audit logging (auditd)
- [ ] Disk encryption (LUKS)
- [ ] SELinux/AppArmor ativo

### Rede
- [ ] Segmentação por VLANs
- [ ] IDS/IPS ativo (Suricata)
- [ ] DNS over TLS/HTTPS
- [ ] Certificados SSL válidos em todos os serviços
- [ ] WPA3 em todas as redes WiFi
- [ ] 802.1X para rede cabeada corporativa

### Backup
- [ ] Backup 3-2-1 (3 cópias, 2 mídias, 1 offsite)
- [ ] Backup criptografado
- [ ] Teste de restore mensal
- [ ] Retenção conforme LGPD (dados médicos)

## Fluxo de Uso

1. **Identificar** componente da infraestrutura
2. **Diagnosticar** estado atual (config, logs, métricas)
3. **Propor** solução ou otimização
4. **Gerar** scripts/configs necessários
5. **Documentar** mudanças e rollback plan
6. **Validar** com testes pós-implementação

## Exemplos de Uso

- "Configure VLANs no UniFi para separar rede médica, IoT e guests"
- "Crie um docker-compose para stack de monitoramento com Grafana + Prometheus"
- "Otimize a performance do Proxmox para as VMs de produção"
- "Configure WireGuard no pfSense para acesso remoto seguro"
- "Monte um dashboard no Grafana para monitorar os servidores Dell"
- "Automatize backup das VMs do Proxmox com retenção de 30 dias"
