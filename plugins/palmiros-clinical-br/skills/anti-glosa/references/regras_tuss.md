# Referência — Regras TUSS/CID e Padrões de Glosa

## 1. Estrutura do Código TUSS

A Terminologia Unificada da Saúde Suplementar (TUSS) organiza códigos em faixas:

| Faixa | Categoria | Risco de Glosa |
|-------|-----------|----------------|
| 10xxxxxx | Consultas | Baixo |
| 20xxxxxx | Procedimentos clínicos | Médio |
| 30xxxxxx | Procedimentos cirúrgicos | Alto |
| 40xxxxxx | Exames diagnósticos | Médio |
| 50xxxxxx | Terapias | Alto |
| 60xxxxxx | Materiais e medicamentos | Médio-Alto |
| 70xxxxxx | OPME | Muito Alto |
| 80xxxxxx | Taxas e diárias | Médio |
| 90xxxxxx | Pacotes | Médio |

## 2. Regras de Incompatibilidade CID × TUSS

### Princípio fundamental
Todo procedimento cobrado deve ter um CID compatível que justifique clinicamente
a sua realização. Incompatibilidade = glosa quase certa.

### Incompatibilidades críticas

1. **Cirurgia obstétrica** (TUSS 309xxxxx) sem CID capítulo O (gravidez/parto)
   - Glosa: ~85%
   - Exceção: CID O80-O84 para partos normais/cesáreas

2. **Cirurgia ortopédica** (TUSS 307xxxxx) sem CID M/S/T
   - Glosa: ~75%
   - Aceito: M (osteomuscular), S/T (trauma)

3. **Procedimento cardiovascular** (TUSS 304xxxxx) sem CID I/Q
   - Glosa: ~80%
   - Q21-Q28 aceito para cardiopatias congênitas

4. **Quimioterapia** (TUSS 503xxxxx) sem CID C/D0-D4
   - Glosa: ~90%
   - Mais rigoroso de todos

5. **Radioterapia** (TUSS 502xxxxx) sem CID C/D0
   - Glosa: ~90%

## 3. Documentação Obrigatória por Tipo

### OPME (Órteses, Próteses, Materiais Especiais)
Campos obrigatórios:
- Justificativa clínica detalhada
- Marca e fabricante
- Registro ANVISA
- Procedimento cirúrgico vinculado
- Quantidade utilizada vs. aberta

Sem esses campos: **85% de probabilidade de glosa**

### Medicamentos de Alto Custo
Campos obrigatórios:
- Indicação clínica com CID
- Falha terapêutica prévia documentada
- Referência a guideline/diretriz
- Dose e peso corporal (para imunobiológicos)

Sem esses campos: **75% de probabilidade de glosa**

### Uso Off-Label
Campos obrigatórios:
- Justificativa detalhada com literatura
- Referências bibliográficas
- Termo de consentimento
- Aprovação da comissão médica

Sem esses campos: **90% de probabilidade de glosa**

## 4. Padrões de Glosa por Operadora

### As 5 que mais glosam (em ordem)

1. **Notre Dame Intermédica** — taxa média 9%
   - Foco: OPME, alto custo, honorários
   - Auditoria agressiva em materiais > R$5k

2. **Amil** — taxa média 8%
   - Foco: OPME, diárias, taxas
   - Contesta permanência em UTI sistematicamente

3. **Unimed** (varia por regional) — taxa média 7%
   - Foco: exames repetidos, materiais, diárias
   - Paulistana mais rigorosa que interior

4. **SulAmérica** — taxa média 6%
   - Foco: materiais, honorários duplicados
   - Auditoria rigorosa em OPME > R$5k

5. **Bradesco Saúde** — taxa média 5%
   - Foco: pacotes, taxas de sala
   - Contesta itens cobrados fora de pacote

### Autogestões (CASSI, GEAP, Petrobras)
- Taxa média 4-5%
- Menos rigorosas em geral
- Exigem codificação TUSS precisa

## 5. Procedimentos que Mais Dão Prejuízo

### Top 10 por valor de glosa

1. Cirurgias com OPME de alto custo (bariátrica, ortopédica, cardíaca)
2. Internações prolongadas em UTI (> 7 dias)
3. Quimioterapia com imunobiológicos
4. Cirurgias robóticas
5. Transplantes
6. Procedimentos hemodinâmicos com stents
7. Neurocirurgias com neuronavegação
8. Cirurgias bariátricas
9. Terapias com medicamentos biológicos
10. Procedimentos de reprodução assistida

### Padrão comum
80% do valor de glosa vem de 20% dos procedimentos.
Esses 20% são quase sempre: OPME + alto custo + cirúrgicos complexos.

## 6. Causas Raiz de Glosa

| Causa | Frequência | Prevenível? |
|-------|------------|-------------|
| Documentação insuficiente | ~40% | Sim — NLP |
| Erro de codificação TUSS | ~30% | Sim — Motor regras |
| Regras contratuais | ~20% | Parcial — Base contratos |
| Falhas administrativas | ~10% | Sim — Automação |

### Insight fundamental
~70% das glosas são preveníveis com dados.
Documentação + codificação = 70% das causas.
Exatamente o que os módulos NLP + TUSS atacam.

## 7. Anatomia de uma Glosa Bem-Sucedida vs. Glosada

### Conta que NÃO será glosada:
- CID compatível com todos os procedimentos
- Senha de autorização válida e dentro do prazo
- OPME com justificativa, ANVISA e marca
- Prontuário com indicação clínica explícita
- Medicamentos de alto custo com guideline citado
- Sem duplicatas
- Itens dentro do pacote quando aplicável

### Conta que SERÁ glosada:
- CID genérico (ex: R69 — "causa desconhecida")
- Sem senha ou senha vencida
- OPME sem justificativa
- Prontuário com "conforme rotina" ou "a pedido"
- Medicamento caro sem falha prévia documentada
- Honorário duplicado
- Taxa cobrada fora do pacote
