# Binary Bounty — Foso Defensável na Era Pós-Mythos

Enquanto web bounty vira commodity AI, binary bounty continua **humano-dominado**. LLMs são péssimos em exploitation sob mitigations modernas. Este é o espaço onde Ghidra + instinto + paciência rendem 6 dígitos por chain funcional.

## Por que binary resiste à IA

- Exploitation requer **heap grooming**, **gadget finding**, **timing preciso de race windows**.
- Mitigations modernas (ASLR, CET/IBT, PAC, MTE, shadow stack, CFG) exigem raciocínio sobre estado de runtime que LLM não modela bem.
- **Reliability** é critério de avaliação — exploit precisa funcionar em 80%+ das vezes.
- Reversing em código otimizado com SIMD/intrínsecas cerebrais confunde LLM puro.

Resultado: o bar de entrada é alto, mas o upside também.

## Plataformas e pagamentos

| Programa | Alvo | Tier máximo |
|----------|------|-------------|
| Apple Security Bounty | iOS/macOS, Secure Enclave, iCloud | Até $2M (kernel zero-click) |
| Samsung Mobile Security | Galaxy, Tizen, Bixby, Knox | Até $1M (lockscreen bypass remoto) |
| Google VRP | Android, Chrome, ChromeOS | Até $1M-$1.5M (Android full chain) |
| Microsoft Bug Bounty | Windows, Hyper-V, Azure | Até $250k-$500k (hypervisor escape) |
| ZDI (Zero Day Initiative) | Enterprise software, IoT | $5k-$250k+ (tiered by target) |
| Pwn2Own Vancouver/Tokyo/Automotive | Rotativo (browsers, servers, vehicles) | $500k+ por chain |
| Meta Bug Bounty | WhatsApp, FB, Instagram, Oculus | Até $300k (RCE em Oculus/Quest) |
| Kraken, Immunefi (crypto) | Smart contracts, wallets | Até $10M (protocol critical) |

**Observação**: pagamento varia conforme categorias (pre-auth vs post-auth, user interaction vs zero-click, chain vs single bug).

## Targets de alto ROI (2026+)

### Hardened, mas ainda tratáveis
- **Chrome renderer → sandbox escape**: Sandbox bugs em libs de parser (V8, PDFium, libwebp)
- **iOS Safari → kernel**: WebKit sempre tem gadgets; conversão para IOKit/kernel é arte
- **Android System Server**: escalation para system_server (UID 1000) com privilégios massivos
- **Hypervisors**: Hyper-V, KVM, VMware ESXi — bugs raros mas payouts enormes
- **Secure boot chains**: UEFI bugs, TPM, Secure Enclave
- **Smart lock / smart home firmware**: bar de mitigations menor, bounties reais via ZDI

### Sweet spots de menor concorrência
- **Printer firmware** (HP, Canon) — Pwn2Own categoria com menos gente
- **NAS appliances** (Synology, QNAP) — bugs recorrentes em mgmt UI + chains para RCE
- **SOHO routers** (TP-Link, D-Link, Asus) — ZDI paga bem
- **IoT wearables** e **drones**

## Workflow Ghidra + AI Assistants

### Setup
```bash
# Ghidra (free, NSA)
# Download: https://ghidra-sre.org/

# Plugins essenciais
# - Ghidrathon: Python 3 scripting dentro do Ghidra
# - GhidraMCP: interface MCP Ghidra ↔ LLM (permite Claude ler decompile)
# - BinDiff: comparar binaries (diff de patches = encontrar N-day)
# - Dragondance: coverage-guided reversing
```

### Pipeline híbrido
```
1. TRIAGE (passivo)
   ├── Listar funções exportadas / symbols interessantes
   ├── String references: "admin", "debug", "root", "priv"
   ├── Cross-references de funções de parsing (entry points)
   └── Bindiff com versão anterior (se houver) → funções modificadas = candidatos

2. DECOMPILE + AI ANNOTATION
   ├── GhidraMCP: exportar decompile de funções suspeitas
   ├── Claude: "analise este decompile buscando memory safety issues"
   ├── Humano: valida sanidade da análise (decompile != source)
   └── Foco em: tamanhos não-checked, ponteiros user-controlled, integer math

3. FUZZING ALVO-ESPECÍFICO
   ├── Identificar entry point (network handler, file parser)
   ├── Harness: AFL++, libFuzzer, honggfuzz
   ├── Coverage-guided → encontrar crashes
   └── Minimize + deduplicate crashes

4. TRIAGE DE CRASHES
   ├── Classificar: null deref, SIGSEGV write/read, SIGFPE, abort
   ├── Priorizar: write primitives, type confusion, UAF > null derefs
   └── Avaliar: com ASLR/PAC/CET quebrados, isso vira RCE?

5. EXPLOITATION
   ├── Heap grooming (estudar allocator do alvo: ptmalloc/scudo/iOS kalloc)
   ├── Info leak first (sempre) → quebra ASLR
   ├── Construir write primitive confiável
   ├── ROP/JOP chain ou data-only se CET ativo
   ├── Executar código / alterar estado sensível
   └── Cleanup / recover (para exploit continuável, não só crash)

6. RELIABILITY ENGINEERING
   ├── Rodar exploit 1000x → medir % sucesso
   ├── Ajustar race windows, spray counts, timing
   ├── ZDI/Pwn2Own exigem ≥80% reliability
   └── Documentar edge cases (versão do kernel, config)

7. REPORT
   ├── Writeup técnico: root cause + primitives + chain
   ├── PoC build + instructions (docker reprod preferido)
   ├── Video do exploit rodando
   └── Mitigation sugerida (patch diff, arquitetura)
```

## Classes de bugs (por impacto)

### Memory Corruption
- **Heap overflow / OOB write** — ainda o clássico; grooming define reliability
- **Use-after-free** — plataformas com refcount bugs (C++ com std::shared_ptr mal usado)
- **Type confusion** — comum em JIT engines (V8, JSC, SpiderMonkey)
- **Integer overflow → insufficient allocation** → OOB
- **Double free** — menos útil com hardened heaps, mas vive em firmware

### Race Conditions
- **Signal handlers** não async-signal-safe
- **TOCTOU** em kernel syscalls (check + use em lugares diferentes)
- **Setuid race** — clássico Linux
- **Filesystem races** via symlinks em /tmp

### Logic Bugs (sem memory corruption)
- **Privilege escalation** via confused deputy
- **Authentication bypass** em bootloader / secure boot
- **Downgrade attacks** em update mechanisms
- **Cryptographic misuse** (IV reuse, nonce collision, weak randomness)

## Mitigations modernas — o que quebrar e como

### ASLR (Address Space Layout Randomization)
- **Quebra via info leak**: sempre a primeira primitiva
- Em Android/iOS, leak de ponteiro libc = base ASLR

### Stack canaries
- Geralmente canário por função; overflow precisa preservar ou vazar

### DEP / W^X / NX
- Elimina shellcode direto; força ROP/JOP

### CET / IBT (Intel Control-flow Enforcement)
- Shadow stack protege RET
- IBT exige landing pad (endbr64) em destinos indirect call
- **Bypass**: data-only attacks, COP, ou gadgets em código IBT-compatible

### PAC (Pointer Authentication — ARM64, iOS/macOS Apple Silicon)
- Ponteiros assinados com chave secret
- **Bypass**: signing oracle, re-signing via controlled PAC context, ou atacar dados não-PAC

### MTE (Memory Tagging Extension — ARM)
- Tags em alocações detectam OOB
- **Bypass**: prob de colisão 1/16 = 6.25% ainda bypassable em spray

### SMAP / SMEP (kernel)
- Impede acesso direto de kernel a userspace
- **Bypass**: kernel ROP, data-only via reused structures

### Shadow stack (Windows CET, Linux)
- Cópia separada de returns em página protected
- **Bypass**: não atacar RETs; usar indirect calls

## Heap Grooming básico

Grooming = deixar heap em estado previsível para que bug caia em alocação conhecida.

### Padrões por alocator
- **ptmalloc (glibc)**: tcache, fastbins, unsorted bin — explore size classes
- **jemalloc (Firefox/FreeBSD)**: arenas separadas por size
- **scudo (Android/hardened Linux)**: quarantine + randomization
- **iOS kalloc**: zones por size, strict free list verification
- **Windows LFH (Low-Fragmentation Heap)**: buckets por size

### Técnica geral
1. Vazar info sobre allocator state (chunks, freelists)
2. Preencher heap com objeto-controlado (spray)
3. Liberar buracos para alocação do alvo
4. Trigger bug → overwrite vai cair em spray-object
5. Escalate (fake vtable, corrupt length, etc.)

## Ferramentas essenciais

### Análise estática
- **Ghidra** — gratuito, plugin ecosystem forte
- **IDA Pro + Hex-Rays** — gold standard, $$$$ mas produtividade
- **Binary Ninja** — moderno, boa API Python
- **BinDiff** — patch diffing

### Análise dinâmica
- **gdb + gef/pwndbg/peda** — exploit dev Linux
- **x64dbg** — Windows
- **LLDB** — macOS/iOS
- **Frida** — dynamic instrumentation (iOS/Android)
- **QEMU** — emulação de firmware, MIPS/ARM

### Fuzzing
- **AFL++** — coverage-guided, feature-rich
- **libFuzzer** — in-process, para libs com API clara
- **honggfuzz** — robusto, paraleliza bem
- **syzkaller** — syscall fuzzing (Linux/Android kernel)
- **WinAFL** — Windows binaries

### Exploit dev
- **pwntools** (Python) — biblioteca de facto
- **ROPgadget / ropper** — gadget finding
- **one_gadget** — magic RCE em libc Linux

## Recursos de aprendizado

### Literatura fundamental
- **Hacking: The Art of Exploitation** (Jon Erickson) — baseline
- **A Bug Hunter's Diary** (Tobias Klein)
- **The Shellcoder's Handbook** (2ª ed)
- **iOS Hacker's Handbook**, **Android Hacker's Handbook**
- **Windows Internals** (Russinovich) — para Windows kernel

### Labs
- **pwn.college** (ASU) — currículum completo, gratuito
- **Nightmare** (guyinatuxedo) — CTF pwn writeups progressivo
- **HackTheBox Pro Labs** — Offshore, APT para escalation prática
- **SANS SEC660 / SEC760** — treinamento pago de elite

### Writeups de referência
- **Google Project Zero blog** — técnicas de ponta
- **Synacktiv research** — bugs em Pwn2Own
- **Trail of Bits blog** — bugs + ferramentas
- **Saar Amar (iOS)**, **Ian Beer (iOS kernel)**, **Gynvael (diverse)**

### Comunidades
- **CTFTime.org** — CTFs pwn para prática contínua
- **r/netsec** — curated
- **Twitter/X**: @i41nbeer, @Saaramar, @GynvaelEn, @_qaz_qaz, @marcograss

## Ghidra + Claude MCP workflow (exemplo)

```python
# Usando GhidraMCP (hipotético) — LLM pode ler decompile via MCP
# Workflow:

# 1. Claude analisa decompile de função suspeita
claude_prompt = """
Analise este decompile do Ghidra:

[decompile]
undefined8 parse_packet(char *data, size_t len) {
    char buf[256];
    size_t copy_len = *(uint32_t*)data;
    memcpy(buf, data + 4, copy_len);
    ...
}
[/decompile]

Identifique:
1. Vulnerabilidade (se houver)
2. Condições de trigger
3. Mitigations que bloqueiam exploit (assumindo ASLR+stack canary+DEP ativos)
4. Primitivas necessárias (info leak? write primitive?)
5. Probabilidade de ser exploitable em target hardened: baixa/média/alta
"""
# → Claude retorna análise; você valida no binário real
```

## Anti-patterns específicos de binary bounty

- ❌ Reportar crash sem demonstrar exploitabilidade → marked "not a security bug"
- ❌ Exploit que só funciona em debug build / sem mitigations
- ❌ Submitter para ZDI exclusivo algo já vendido em outro broker → ban permanente
- ❌ Testar em dispositivos de outras pessoas sem consentimento (ataque a iCloud de celebs virou caso federal)
- ❌ Não baixar symbols públicos quando disponíveis (Windows PDB, iOS kernel cache) — análise vira trabalho desnecessário
- ❌ Ficar em bug que não escala → timebox, passar pra próximo target
