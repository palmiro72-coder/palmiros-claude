#!/usr/bin/env python3
"""
ANTIGLOSA — Motor de Auditoria Preditiva Hospitalar
Inventor: Dr. Lucas do Prado Palmiro (CREMESP 139089)
Hospital Israelita Albert Einstein / UNIFESP-EPM

Módulos:
  TUSS  — Motor de Regras TUSS/CID (consistência)
  NLP   — Extrator de Justificativas Clínicas
  MISS  — Detector de Cobranças Perdidas
  RISK  — Scoring de Risco de Glosa por Conta
"""

import json
import sys
import argparse
import re
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional, Any
from collections import defaultdict
from dataclasses import dataclass, field, asdict

# ============================================================
# CONSTANTES E TABELAS DE REGRAS
# ============================================================

# Classificação de capítulos CID-10
CID_CHAPTERS = {
    'E': 'endócrinas_nutricionais_metabólicas',
    'C': 'neoplasias',
    'D': 'sangue_imunidade',
    'I': 'circulatório',
    'J': 'respiratório',
    'K': 'digestivo',
    'M': 'osteomuscular',
    'N': 'geniturinário',
    'G': 'sistema_nervoso',
    'H': 'olho_ouvido',
    'L': 'pele',
    'O': 'gravidez_parto',
    'S': 'traumatismos',
    'T': 'traumatismos_envenenamentos',
    'Z': 'fatores_saude',
    'R': 'sintomas_sinais',
    'F': 'transtornos_mentais',
    'A': 'infecciosas_parasitárias',
    'B': 'infecciosas_parasitárias',
    'P': 'perinatais',
    'Q': 'malformações_congênitas',
    'U': 'códigos_especiais',
    'V': 'causas_externas',
    'W': 'causas_externas',
    'X': 'causas_externas',
    'Y': 'causas_externas',
}

# Grupos TUSS por faixa de código
TUSS_GROUPS = {
    (10101012, 10199019): 'consultas',
    (20101015, 20999999): 'procedimentos_clínicos',
    (30101018, 30999999): 'procedimentos_cirúrgicos',
    (40101010, 40999999): 'exames_diagnósticos',
    (50101017, 50999999): 'terapias',
    (60101013, 60999999): 'materiais_medicamentos',
    (70101016, 70999999): 'órteses_próteses_materiais',
    (80101019, 80999999): 'taxas_diárias',
    (90101012, 90999999): 'pacotes',
}

# Regras de incompatibilidade TUSS/CID
INCOMPATIBILITY_RULES = [
    {
        'id': 'INC-001',
        'name': 'Procedimento obstétrico sem CID obstétrico',
        'tuss_range': (30901016, 30999999),
        'cid_required': ['O'],
        'severity': 'alta',
        'glosa_prob': 0.85,
    },
    {
        'id': 'INC-002',
        'name': 'Cirurgia ortopédica sem CID traumatológico/osteomuscular',
        'tuss_range': (30701016, 30799999),
        'cid_required': ['M', 'S', 'T'],
        'severity': 'alta',
        'glosa_prob': 0.75,
    },
    {
        'id': 'INC-003',
        'name': 'Procedimento cardiovascular sem CID circulatório',
        'tuss_range': (30401014, 30499999),
        'cid_required': ['I', 'Q'],
        'severity': 'alta',
        'glosa_prob': 0.80,
    },
    {
        'id': 'INC-004',
        'name': 'Procedimento neurológico sem CID neurológico',
        'tuss_range': (30201012, 30299999),
        'cid_required': ['G', 'C71', 'I6'],
        'severity': 'média',
        'glosa_prob': 0.65,
    },
    {
        'id': 'INC-005',
        'name': 'Exame endócrino sem CID endócrino',
        'tuss_range': (40301010, 40399999),
        'cid_required': ['E'],
        'severity': 'baixa',
        'glosa_prob': 0.30,
    },
    {
        'id': 'INC-006',
        'name': 'Quimioterapia sem CID neoplásico',
        'tuss_range': (50301012, 50399999),
        'cid_required': ['C', 'D0', 'D1', 'D2', 'D3', 'D4'],
        'severity': 'alta',
        'glosa_prob': 0.90,
    },
    {
        'id': 'INC-007',
        'name': 'Radioterapia sem CID neoplásico',
        'tuss_range': (50201019, 50299999),
        'cid_required': ['C', 'D0'],
        'severity': 'alta',
        'glosa_prob': 0.90,
    },
    {
        'id': 'INC-008',
        'name': 'OPME sem justificativa vinculada a procedimento cirúrgico',
        'tuss_range': (70101016, 70999999),
        'requires_linked_surgical': True,
        'severity': 'alta',
        'glosa_prob': 0.70,
    },
    {
        'id': 'INC-009',
        'name': 'Diária UTI sem CID de gravidade compatível',
        'tuss_range': (80101019, 80199999),
        'severity': 'média',
        'glosa_prob': 0.55,
    },
    {
        'id': 'INC-010',
        'name': 'Honorário duplicado para mesmo procedimento/data',
        'check_type': 'duplicate_fee',
        'severity': 'alta',
        'glosa_prob': 0.95,
    },
]

# Regras de documentação obrigatória por tipo de material/medicamento
DOCUMENTATION_RULES = {
    'opme': {
        'required_fields': [
            'justificativa_clínica',
            'marca_fabricante',
            'registro_anvisa',
            'procedimento_vinculado',
        ],
        'glosa_if_missing': 0.85,
    },
    'alto_custo': {
        'required_fields': [
            'indicação_clínica',
            'falha_terapêutica_prévia',
            'referência_guideline',
            'cid_principal',
        ],
        'glosa_if_missing': 0.75,
    },
    'off_label': {
        'required_fields': [
            'justificativa_detalhada',
            'referências_literatura',
            'termo_consentimento',
            'aprovação_comissão',
        ],
        'glosa_if_missing': 0.90,
    },
    'imunobiológico': {
        'required_fields': [
            'indicação_aprovada_anvisa',
            'peso_corporal',
            'dose_calculada',
            'ciclo_tratamento',
        ],
        'glosa_if_missing': 0.80,
    },
}

# Operadoras com padrões conhecidos de glosa
OPERATOR_PROFILES = {
    'amil': {
        'taxa_glosa_média': 0.08,
        'foco_glosa': ['opme', 'diárias', 'taxas'],
        'exige_senha_previa': True,
        'prazo_senha_dias': 30,
        'observações': 'Frequente contestação de permanência em UTI',
    },
    'sulamerica': {
        'taxa_glosa_média': 0.06,
        'foco_glosa': ['materiais', 'honorários_duplicados'],
        'exige_senha_previa': True,
        'prazo_senha_dias': 60,
        'observações': 'Auditoria rigorosa em OPME acima de R$5k',
    },
    'bradesco_saude': {
        'taxa_glosa_média': 0.05,
        'foco_glosa': ['pacotes', 'taxas_sala'],
        'exige_senha_previa': True,
        'prazo_senha_dias': 45,
        'observações': 'Contestação frequente de itens fora de pacote',
    },
    'unimed': {
        'taxa_glosa_média': 0.07,
        'foco_glosa': ['exames_repetidos', 'materiais', 'diárias'],
        'exige_senha_previa': True,
        'prazo_senha_dias': 30,
        'observações': 'Varia por regional. Unimed Paulistana mais rigorosa.',
    },
    'notre_dame_intermedica': {
        'taxa_glosa_média': 0.09,
        'foco_glosa': ['opme', 'alto_custo', 'honorários'],
        'exige_senha_previa': True,
        'prazo_senha_dias': 30,
        'observações': 'Alto índice de glosa em materiais de alto custo',
    },
    'cassi': {
        'taxa_glosa_média': 0.04,
        'foco_glosa': ['codificação_tuss'],
        'exige_senha_previa': False,
        'prazo_senha_dias': None,
        'observações': 'Menos rigorosa, porém exige codificação precisa',
    },
    'geap': {
        'taxa_glosa_média': 0.05,
        'foco_glosa': ['diárias', 'taxas'],
        'exige_senha_previa': True,
        'prazo_senha_dias': 60,
        'observações': 'Autogestão — padrão mais previsível',
    },
}

# Padrões de cobrança frequentemente perdidos
COMMON_MISSING_CHARGES = [
    {
        'trigger': 'monitorização_contínua_glicose',
        'keywords': ['CGM', 'sensor glicose', 'libre', 'dexcom', 'guardian'],
        'tuss_codes': ['40302180', '40302199'],
        'description': 'Monitorização contínua de glicose — frequentemente não faturada',
    },
    {
        'trigger': 'avaliação_nutricional',
        'keywords': ['nutricionista', 'avaliação nutricional', 'dieta', 'IMC', 'bioimpedância'],
        'tuss_codes': ['20104014', '20104022'],
        'description': 'Avaliação e acompanhamento nutricional registrados mas não faturados',
    },
    {
        'trigger': 'telemonitoramento',
        'keywords': ['telemonitor', 'monitoramento remoto', 'teleconsulta', 'telemedicina'],
        'tuss_codes': ['10101039', '10101047'],
        'description': 'Atendimento de telemedicina realizado mas cobrado como consulta presencial',
    },
    {
        'trigger': 'bomba_infusão',
        'keywords': ['bomba de infusão', 'infusão contínua', 'PCA', 'bomba insulina'],
        'tuss_codes': ['80040177'],
        'description': 'Uso de bomba de infusão registrado sem taxa correspondente',
    },
    {
        'trigger': 'oxigenoterapia',
        'keywords': ['O2', 'oxigênio', 'cateter nasal', 'máscara O2', 'nebulização'],
        'tuss_codes': ['20104090', '80040088'],
        'description': 'Oxigenoterapia ou nebulização sem cobrança de taxa/material',
    },
    {
        'trigger': 'curativo_complexo',
        'keywords': ['curativo', 'desbridamento', 'VAC', 'terapia pressão negativa'],
        'tuss_codes': ['30911010', '30911028'],
        'description': 'Curativo especial ou terapia por pressão negativa sem cobrança completa',
    },
    {
        'trigger': 'fisioterapia',
        'keywords': ['fisioterapia', 'mobilização', 'exercícios', 'reabilitação'],
        'tuss_codes': ['50000470', '50000489'],
        'description': 'Sessões de fisioterapia registradas no prontuário mas não faturadas',
    },
    {
        'trigger': 'interconsulta',
        'keywords': ['interconsulta', 'parecer', 'avaliação especialista'],
        'tuss_codes': ['10102019'],
        'description': 'Interconsulta médica realizada sem cobrança de honorário',
    },
    {
        'trigger': 'sedação',
        'keywords': ['sedação', 'propofol', 'midazolam', 'anestesia local'],
        'tuss_codes': ['30901010', '20104120'],
        'description': 'Sedação para procedimento sem cobrança separada',
    },
    {
        'trigger': 'ecografia_beira_leito',
        'keywords': ['POCUS', 'ultrassom beira leito', 'USG point-of-care', 'ecografia'],
        'tuss_codes': ['40901114', '40901122'],
        'description': 'Ecografia à beira leito realizada mas não registrada no faturamento',
    },
]


# ============================================================
# DATACLASSES
# ============================================================

@dataclass
class ContaItem:
    """Item individual de uma conta hospitalar."""
    id: str
    tipo: str  # procedimento, material, medicamento, taxa, diária, honorário
    codigo_tuss: str
    descricao: str
    quantidade: int = 1
    valor_unitario: float = 0.0
    data: str = ''  # YYYY-MM-DD
    hora: str = ''  # HH:MM
    medico_executante: str = ''
    cid_vinculado: str = ''
    senha_autorizacao: str = ''
    data_senha: str = ''
    justificativa: str = ''
    registro_anvisa: str = ''
    marca: str = ''
    lote: str = ''

    @property
    def valor_total(self) -> float:
        return self.quantidade * self.valor_unitario

    def to_dict(self) -> dict:
        d = asdict(self)
        d['valor_total'] = self.valor_total
        return d


@dataclass
class ContaHospitalar:
    """Conta hospitalar completa para auditoria."""
    id_conta: str
    paciente_id: str
    data_internacao: str
    data_alta: str = ''
    cid_principal: str = ''
    cids_secundarios: list = field(default_factory=list)
    operadora: str = ''
    tipo_atendimento: str = ''  # internação, ambulatorial, pronto_socorro
    itens: list = field(default_factory=list)  # List[ContaItem]
    prontuario_texto: str = ''  # texto livre do prontuário
    prescricoes: list = field(default_factory=list)  # medicações prescritas
    procedimentos_realizados: list = field(default_factory=list)  # do prontuário

    @property
    def valor_total(self) -> float:
        return sum(item.valor_total for item in self.itens if isinstance(item, ContaItem))

    def to_dict(self) -> dict:
        d = asdict(self)
        d['valor_total'] = self.valor_total
        return d


@dataclass
class Alerta:
    """Alerta de auditoria."""
    modulo: str  # TUSS, NLP, MISS, RISK
    regra_id: str
    severidade: str  # crítica, alta, média, baixa, info
    descricao: str
    item_id: str = ''
    valor_impacto: float = 0.0
    probabilidade_glosa: float = 0.0
    recomendacao: str = ''
    evidencia: str = ''

    @property
    def score(self) -> float:
        """Score composto = probabilidade × impacto."""
        sev_weights = {'crítica': 1.0, 'alta': 0.8, 'média': 0.5, 'baixa': 0.3, 'info': 0.1}
        return self.probabilidade_glosa * self.valor_impacto * sev_weights.get(self.severidade, 0.5)

    def to_dict(self) -> dict:
        d = asdict(self)
        d['score'] = self.score
        return d


# ============================================================
# MÓDULO 1: MOTOR DE REGRAS TUSS/CID
# ============================================================

class MotorTUSS:
    """Verifica consistência TUSS/CID e regras contratuais."""

    def __init__(self, rules: list = None):
        self.rules = rules or INCOMPATIBILITY_RULES
        self.doc_rules = DOCUMENTATION_RULES

    def get_tuss_group(self, codigo: str) -> Optional[str]:
        """Identifica o grupo TUSS de um código."""
        try:
            code_int = int(codigo.replace('.', ''))
        except ValueError:
            return None
        for (low, high), group in TUSS_GROUPS.items():
            if low <= code_int <= high:
                return group
        return None

    def check_cid_compatibility(self, item: ContaItem, cid_principal: str,
                                 cids_secundarios: list) -> List[Alerta]:
        """Verifica se o CID é compatível com o procedimento TUSS."""
        alertas = []
        all_cids = [cid_principal] + (cids_secundarios or [])

        try:
            code_int = int(item.codigo_tuss.replace('.', ''))
        except ValueError:
            alertas.append(Alerta(
                modulo='TUSS',
                regra_id='TUSS-ERR',
                severidade='alta',
                descricao=f'Código TUSS inválido: {item.codigo_tuss}',
                item_id=item.id,
                valor_impacto=item.valor_total,
                probabilidade_glosa=0.95,
                recomendacao='Corrigir código TUSS antes do envio',
            ))
            return alertas

        for rule in self.rules:
            if 'check_type' in rule:
                continue  # handled separately

            tuss_range = rule.get('tuss_range', (0, 0))
            if not (tuss_range[0] <= code_int <= tuss_range[1]):
                continue

            if 'requires_linked_surgical' in rule:
                if not item.justificativa and not any(
                    'cirurg' in c.lower() for c in [item.descricao]
                ):
                    alertas.append(Alerta(
                        modulo='TUSS',
                        regra_id=rule['id'],
                        severidade=rule['severity'],
                        descricao=rule['name'],
                        item_id=item.id,
                        valor_impacto=item.valor_total,
                        probabilidade_glosa=rule['glosa_prob'],
                        recomendacao='Vincular OPME ao procedimento cirúrgico com justificativa clínica',
                        evidencia=f'TUSS {item.codigo_tuss} sem procedimento cirúrgico vinculado',
                    ))
                continue

            cid_required = rule.get('cid_required', [])
            if cid_required:
                match = False
                for cid in all_cids:
                    for req in cid_required:
                        if cid.upper().startswith(req.upper()):
                            match = True
                            break
                    if match:
                        break

                if not match:
                    alertas.append(Alerta(
                        modulo='TUSS',
                        regra_id=rule['id'],
                        severidade=rule['severity'],
                        descricao=rule['name'],
                        item_id=item.id,
                        valor_impacto=item.valor_total,
                        probabilidade_glosa=rule['glosa_prob'],
                        recomendacao=f'CID incompatível. Esperado: {", ".join(cid_required)}. '
                                     f'Encontrado: {", ".join(all_cids)}',
                        evidencia=f'TUSS {item.codigo_tuss} com CID {cid_principal}',
                    ))

        return alertas

    def check_duplicates(self, itens: List[ContaItem]) -> List[Alerta]:
        """Detecta cobranças duplicadas (mesmo código, data, médico)."""
        alertas = []
        seen = defaultdict(list)

        for item in itens:
            key = (item.codigo_tuss, item.data, item.medico_executante)
            seen[key].append(item)

        for key, items in seen.items():
            if len(items) > 1:
                total_dup = sum(i.valor_total for i in items[1:])
                alertas.append(Alerta(
                    modulo='TUSS',
                    regra_id='INC-010',
                    severidade='alta',
                    descricao=f'Cobrança duplicada: {items[0].descricao} em {items[0].data}',
                    item_id=items[0].id,
                    valor_impacto=total_dup,
                    probabilidade_glosa=0.95,
                    recomendacao=f'Remover {len(items)-1} duplicata(s). Valor duplicado: R${total_dup:,.2f}',
                    evidencia=f'{len(items)}x TUSS {key[0]} em {key[1]} por {key[2]}',
                ))

        return alertas

    def check_documentation(self, item: ContaItem) -> List[Alerta]:
        """Verifica documentação obrigatória por tipo de item."""
        alertas = []
        group = self.get_tuss_group(item.codigo_tuss)

        # Determinar tipo de documentação necessária
        doc_type = None
        if group == 'órteses_próteses_materiais':
            doc_type = 'opme'
        elif item.valor_unitario > 5000:
            doc_type = 'alto_custo'

        if doc_type and doc_type in self.doc_rules:
            rules = self.doc_rules[doc_type]
            missing = []

            for field_name in rules['required_fields']:
                # Mapear campos obrigatórios para atributos do item
                field_map = {
                    'justificativa_clínica': item.justificativa,
                    'marca_fabricante': item.marca,
                    'registro_anvisa': item.registro_anvisa,
                    'procedimento_vinculado': item.justificativa,
                    'indicação_clínica': item.justificativa,
                    'falha_terapêutica_prévia': item.justificativa,
                    'referência_guideline': item.justificativa,
                    'cid_principal': item.cid_vinculado,
                }
                value = field_map.get(field_name, '')
                if not value or value.strip() == '':
                    missing.append(field_name)

            if missing:
                alertas.append(Alerta(
                    modulo='TUSS',
                    regra_id=f'DOC-{doc_type.upper()}',
                    severidade='alta',
                    descricao=f'Documentação incompleta para {doc_type}: {", ".join(missing)}',
                    item_id=item.id,
                    valor_impacto=item.valor_total,
                    probabilidade_glosa=rules['glosa_if_missing'],
                    recomendacao=f'Completar campos obrigatórios antes do envio: {", ".join(missing)}',
                    evidencia=f'Item {item.descricao} (R${item.valor_total:,.2f}) sem {len(missing)} campos',
                ))

        return alertas

    def check_authorization(self, item: ContaItem, operadora: str) -> List[Alerta]:
        """Verifica senhas e autorizações prévias."""
        alertas = []
        op_profile = OPERATOR_PROFILES.get(operadora.lower().replace(' ', '_'), {})

        if op_profile.get('exige_senha_previa') and not item.senha_autorizacao:
            group = self.get_tuss_group(item.codigo_tuss)
            if group in ('procedimentos_cirúrgicos', 'exames_diagnósticos',
                        'terapias', 'órteses_próteses_materiais'):
                alertas.append(Alerta(
                    modulo='TUSS',
                    regra_id='AUTH-001',
                    severidade='alta',
                    descricao=f'Sem autorização prévia para {item.descricao}',
                    item_id=item.id,
                    valor_impacto=item.valor_total,
                    probabilidade_glosa=0.80,
                    recomendacao=f'Obter senha de autorização da {operadora} antes do envio',
                    evidencia=f'Operadora {operadora} exige senha para {group}',
                ))

        # Verificar validade da senha
        if item.senha_autorizacao and item.data_senha and item.data:
            try:
                dt_senha = datetime.strptime(item.data_senha, '%Y-%m-%d')
                dt_proc = datetime.strptime(item.data, '%Y-%m-%d')
                prazo = op_profile.get('prazo_senha_dias', 30)
                if prazo and (dt_proc - dt_senha).days > prazo:
                    alertas.append(Alerta(
                        modulo='TUSS',
                        regra_id='AUTH-002',
                        severidade='alta',
                        descricao=f'Senha vencida para {item.descricao}',
                        item_id=item.id,
                        valor_impacto=item.valor_total,
                        probabilidade_glosa=0.90,
                        recomendacao=f'Senha expirada ({(dt_proc - dt_senha).days} dias). '
                                     f'Prazo {operadora}: {prazo} dias. Renovar antes do envio.',
                        evidencia=f'Senha: {item.data_senha}, Procedimento: {item.data}',
                    ))
            except ValueError:
                pass

        return alertas

    def audit(self, conta: ContaHospitalar) -> List[Alerta]:
        """Executa auditoria completa de regras TUSS/CID."""
        alertas = []

        for item in conta.itens:
            if isinstance(item, dict):
                item = ContaItem(**item)
            alertas.extend(self.check_cid_compatibility(
                item, conta.cid_principal, conta.cids_secundarios))
            alertas.extend(self.check_documentation(item))
            alertas.extend(self.check_authorization(item, conta.operadora))

        alertas.extend(self.check_duplicates(
            [ContaItem(**i) if isinstance(i, dict) else i for i in conta.itens]))

        return alertas


# ============================================================
# MÓDULO 2: NLP — EXTRATOR DE JUSTIFICATIVAS CLÍNICAS
# ============================================================

class ExtractorNLP:
    """Analisa texto de prontuário para extrair e validar justificativas clínicas.

    Versão MVP: regex-based pattern matching.
    Versão produção: integrar com LLM local (Llama/Mistral no Proxmox).
    """

    # Padrões que indicam justificativa clínica presente
    JUSTIFICATION_PATTERNS = [
        (r'(?i)indicad[oa]\s+\w+', 'indicação_clínica'),
        (r'(?i)necessidade\s+(?:de\s+)?(?:clínica|terapêutica|cirúrgica|acompanhamento|tratamento)', 'necessidade_clínica'),
        (r'(?i)falha\s+(?:terapêutica|ao?\s+tratamento)', 'falha_terapêutica'),
        (r'(?i)refratári[oa]\s+a', 'refratariedade'),
        (r'(?i)(?:guideline|diretriz|protocolo)\s+\w+', 'referência_guideline'),
        (r'(?i)(?:risco\s+)?(?:vital|morte|óbito|emergência|urgência)', 'urgência_clínica'),
        (r'(?i)(?:comprov(?:ado|ada)|confirm(?:ado|ada)|diagnóstico\s+de)', 'confirmação_diagnóstica'),
        (r'(?i)(?:biópsia|anatomopatológico|histopatológico)', 'evidência_histológica'),
        (r'(?i)(?:piora\s+clínica|deterioração|agravamento)', 'deterioração_clínica'),
        (r'(?i)(?:tentativ[oa]\s+prévi[oa]|já\s+tent(?:ou|ado))', 'tratamento_prévio'),
        (r'(?i)(?:contraindicad[oa]|intolerância|alergia\s+a)', 'contraindicação'),
        (r'(?i)(?:CID|código|classificação)\s*[:-]?\s*[A-Z]\d', 'codificação_presente'),
        (r'(?i)portador[oa]?\s+de\s+\w+', 'condição_documentada'),
        (r'(?i)(?:obesidade|DM[12]|HAS|dislipidemia|hipotireoidismo|hipertireoidismo)', 'diagnóstico_explícito'),
        (r'(?i)IMC\s*(?:=|de|:)?\s*\d+', 'parâmetro_clínico'),
        (r'(?i)(?:há|por|desde)\s+\d+\s+(?:anos?|meses?|dias?)', 'tempo_evolução'),
        (r'(?i)(?:grau\s+(?:I{1,3}|[123])|estágio|estadiamento)', 'classificação_gravidade'),
    ]

    # Padrões de documentação fraca/insuficiente
    WEAK_DOCUMENTATION = [
        (r'(?i)(?:a\s+pedido|solicitado\s+pelo?\s+paciente)', 'pedido_paciente_sem_justificativa'),
        (r'(?i)(?:conforme\s+rotina|protocolo\s+padrão)', 'justificativa_genérica'),
        (r'(?i)(?:idem|mesma\s+conduta|sem\s+alterações)', 'documentação_preguiçosa'),
        (r'(?i)(?:mantido|mantida|manter)\s*$', 'conduta_sem_detalhamento'),
    ]

    # Termos que exigem justificativa detalhada
    HIGH_COST_TRIGGERS = [
        (r'(?i)(?:rituximab|trastuzumab|bevacizumab|pembrolizumab|nivolumab)', 'imunobiológico_oncológico'),
        (r'(?i)(?:adalimumab|infliximab|etanercept|secukinumab)', 'imunobiológico_reumatológico'),
        (r'(?i)(?:insulina\s+bomba|CSII|sensor\s+glicose|CGM)', 'tecnologia_diabetes'),
        (r'(?i)(?:prótese|stent|válvula|marcapasso|desfibrilador)', 'dispositivo_implantável'),
        (r'(?i)(?:robótica|navegação|neuronavegação)', 'tecnologia_cirúrgica'),
        (r'(?i)(?:hemodiálise|diálise|ECMO|CRRT)', 'suporte_avançado'),
    ]

    def analyze_text(self, texto: str) -> Dict[str, Any]:
        """Analisa texto do prontuário e retorna perfil de documentação."""
        if not texto:
            return {
                'score_documentacao': 0,
                'justificativas_encontradas': [],
                'fraquezas': ['prontuário vazio'],
                'alto_custo_detectado': [],
                'recomendacoes': ['Documentar indicação clínica, diagnóstico e plano terapêutico'],
            }

        justificativas = []
        fraquezas = []
        alto_custo = []

        # Buscar justificativas
        for pattern, tipo in self.JUSTIFICATION_PATTERNS:
            matches = re.findall(pattern, texto)
            if matches:
                justificativas.append({
                    'tipo': tipo,
                    'ocorrências': len(matches),
                    'trecho': matches[0] if isinstance(matches[0], str) else matches[0],
                })

        # Buscar fraquezas
        for pattern, tipo in self.WEAK_DOCUMENTATION:
            if re.search(pattern, texto):
                fraquezas.append(tipo)

        # Buscar itens de alto custo
        for pattern, tipo in self.HIGH_COST_TRIGGERS:
            if re.search(pattern, texto):
                alto_custo.append(tipo)

        # Calcular score de documentação (0-1)
        score = min(1.0, len(justificativas) * 0.15)
        if fraquezas:
            score *= 0.6
        if alto_custo and len(justificativas) < 2:
            score *= 0.5

        # Gerar recomendações
        recomendacoes = []
        if not justificativas:
            recomendacoes.append('Adicionar justificativa clínica explícita')
        if alto_custo:
            for ac in alto_custo:
                recomendacoes.append(f'Documentar indicação detalhada para {ac}')
            if 'falha_terapêutica' not in [j['tipo'] for j in justificativas]:
                recomendacoes.append('Registrar falha terapêutica prévia ou primeira linha')
            if 'referência_guideline' not in [j['tipo'] for j in justificativas]:
                recomendacoes.append('Citar guideline ou diretriz que suporta a indicação')
        if fraquezas:
            recomendacoes.append('Substituir termos vagos por justificativa clínica específica')

        return {
            'score_documentacao': round(score, 3),
            'justificativas_encontradas': justificativas,
            'fraquezas': fraquezas,
            'alto_custo_detectado': alto_custo,
            'recomendacoes': recomendacoes,
            'comprimento_texto': len(texto),
            'num_linhas': texto.count('\n') + 1,
        }

    def audit(self, conta: ContaHospitalar) -> List[Alerta]:
        """Audita prontuário via NLP."""
        alertas = []
        analise = self.analyze_text(conta.prontuario_texto)

        if analise['score_documentacao'] < 0.3:
            alertas.append(Alerta(
                modulo='NLP',
                regra_id='NLP-001',
                severidade='alta',
                descricao='Documentação clínica insuficiente para suportar cobrança',
                valor_impacto=conta.valor_total * 0.4,
                probabilidade_glosa=0.65,
                recomendacao='; '.join(analise['recomendacoes']),
                evidencia=f'Score documentação: {analise["score_documentacao"]:.1%}',
            ))

        for fraqueza in analise['fraquezas']:
            alertas.append(Alerta(
                modulo='NLP',
                regra_id='NLP-002',
                severidade='média',
                descricao=f'Documentação fraca detectada: {fraqueza}',
                probabilidade_glosa=0.40,
                recomendacao='Substituir por justificativa clínica específica',
                evidencia=f'Padrão detectado: {fraqueza}',
            ))

        for ac in analise['alto_custo_detectado']:
            if analise['score_documentacao'] < 0.5:
                alertas.append(Alerta(
                    modulo='NLP',
                    regra_id='NLP-003',
                    severidade='crítica',
                    descricao=f'Item de alto custo ({ac}) sem documentação adequada',
                    probabilidade_glosa=0.80,
                    recomendacao=f'Documentar indicação, falha prévia e guideline para {ac}',
                    evidencia=f'Alto custo: {ac}, Score doc: {analise["score_documentacao"]:.1%}',
                ))

        return alertas


# ============================================================
# MÓDULO 3: DETECTOR DE COBRANÇAS PERDIDAS
# ============================================================

class MissingChargesDetector:
    """Detecta procedimentos realizados mas não faturados."""

    def __init__(self, patterns: list = None):
        self.patterns = patterns or COMMON_MISSING_CHARGES

    def scan_prontuario(self, texto: str, itens_cobrados: List[ContaItem]) -> List[Alerta]:
        """Cruza prontuário com itens cobrados para encontrar gaps."""
        alertas = []
        codigos_cobrados = {item.codigo_tuss for item in itens_cobrados}
        descricoes_cobradas = ' '.join(item.descricao.lower() for item in itens_cobrados)

        texto_lower = texto.lower()

        for pattern in self.patterns:
            # Verificar se o prontuário menciona o procedimento
            found_in_prontuario = any(kw.lower() in texto_lower for kw in pattern['keywords'])

            if not found_in_prontuario:
                continue

            # Verificar se já foi cobrado
            already_charged = any(code in codigos_cobrados for code in pattern['tuss_codes'])
            keyword_in_charges = any(kw.lower() in descricoes_cobradas for kw in pattern['keywords'])

            if not already_charged and not keyword_in_charges:
                alertas.append(Alerta(
                    modulo='MISS',
                    regra_id=f'MISS-{pattern["trigger"].upper()[:8]}',
                    severidade='média',
                    descricao=pattern['description'],
                    probabilidade_glosa=0.0,  # não é glosa, é receita perdida
                    recomendacao=f'Considerar cobrança de TUSS {", ".join(pattern["tuss_codes"])}',
                    evidencia=f'Mencionado no prontuário mas ausente na conta',
                ))

        return alertas

    def check_prescricao_vs_cobranca(self, prescricoes: list,
                                       itens_cobrados: List[ContaItem]) -> List[Alerta]:
        """Verifica se medicações prescritas foram cobradas."""
        alertas = []
        cobradas = {item.descricao.lower().strip() for item in itens_cobrados
                   if item.tipo in ('medicamento', 'material')}

        for presc in prescricoes:
            presc_lower = presc.lower().strip()
            if presc_lower and not any(presc_lower in c or c in presc_lower for c in cobradas):
                alertas.append(Alerta(
                    modulo='MISS',
                    regra_id='MISS-PRESC',
                    severidade='baixa',
                    descricao=f'Medicação prescrita não encontrada na conta: {presc}',
                    recomendacao='Verificar se a medicação foi administrada e incluir na cobrança',
                    evidencia=f'Prescrição: {presc}',
                ))

        return alertas

    def audit(self, conta: ContaHospitalar) -> List[Alerta]:
        """Executa detecção de cobranças perdidas."""
        alertas = []
        itens = [ContaItem(**i) if isinstance(i, dict) else i for i in conta.itens]

        if conta.prontuario_texto:
            alertas.extend(self.scan_prontuario(conta.prontuario_texto, itens))

        if conta.prescricoes:
            alertas.extend(self.check_prescricao_vs_cobranca(conta.prescricoes, itens))

        return alertas


# ============================================================
# MÓDULO 4: RISK SCORING
# ============================================================

class RiskScorer:
    """Calcula score de risco de glosa por conta e por item."""

    # Fatores de risco e seus pesos
    RISK_FACTORS = {
        'valor_alto': {
            'threshold': 10000,
            'weight': 0.20,
            'description': 'Valor total da conta acima do threshold',
        },
        'operadora_rigorosa': {
            'threshold_taxa': 0.07,
            'weight': 0.15,
            'description': 'Operadora com taxa de glosa acima da média',
        },
        'muitos_itens': {
            'threshold': 20,
            'weight': 0.10,
            'description': 'Conta com muitos itens (complexidade)',
        },
        'internacao_longa': {
            'threshold_dias': 7,
            'weight': 0.15,
            'description': 'Internação acima de 7 dias',
        },
        'opme_presente': {
            'weight': 0.15,
            'description': 'Conta contém OPME',
        },
        'sem_autorizacao': {
            'weight': 0.10,
            'description': 'Itens sem senha de autorização',
        },
        'documentacao_fraca': {
            'weight': 0.15,
            'description': 'Score de documentação NLP baixo',
        },
    }

    def __init__(self, historical_data: dict = None):
        self.historical_data = historical_data or {}

    def score_conta(self, conta: ContaHospitalar,
                    alertas_previos: List[Alerta] = None,
                    nlp_score: float = None) -> Dict[str, Any]:
        """Calcula risk score composto para a conta."""
        itens = [ContaItem(**i) if isinstance(i, dict) else i for i in conta.itens]
        factors = {}

        # Fator 1: Valor alto
        valor_total = sum(i.valor_total for i in itens)
        if valor_total > self.RISK_FACTORS['valor_alto']['threshold']:
            factors['valor_alto'] = {
                'triggered': True,
                'value': valor_total,
                'contribution': self.RISK_FACTORS['valor_alto']['weight'],
            }

        # Fator 2: Operadora rigorosa
        op_profile = OPERATOR_PROFILES.get(
            conta.operadora.lower().replace(' ', '_'), {})
        taxa_op = op_profile.get('taxa_glosa_média', 0.05)
        if taxa_op > self.RISK_FACTORS['operadora_rigorosa']['threshold_taxa']:
            factors['operadora_rigorosa'] = {
                'triggered': True,
                'value': taxa_op,
                'contribution': self.RISK_FACTORS['operadora_rigorosa']['weight'],
            }

        # Fator 3: Muitos itens
        if len(itens) > self.RISK_FACTORS['muitos_itens']['threshold']:
            factors['muitos_itens'] = {
                'triggered': True,
                'value': len(itens),
                'contribution': self.RISK_FACTORS['muitos_itens']['weight'],
            }

        # Fator 4: Internação longa
        try:
            dt_in = datetime.strptime(conta.data_internacao, '%Y-%m-%d')
            dt_out = datetime.strptime(conta.data_alta, '%Y-%m-%d') if conta.data_alta else datetime.now()
            dias = (dt_out - dt_in).days
            if dias > self.RISK_FACTORS['internacao_longa']['threshold_dias']:
                factors['internacao_longa'] = {
                    'triggered': True,
                    'value': dias,
                    'contribution': self.RISK_FACTORS['internacao_longa']['weight'],
                }
        except (ValueError, TypeError):
            pass

        # Fator 5: OPME presente
        has_opme = any(
            self._is_opme(i.codigo_tuss) for i in itens
        )
        if has_opme:
            factors['opme_presente'] = {
                'triggered': True,
                'contribution': self.RISK_FACTORS['opme_presente']['weight'],
            }

        # Fator 6: Itens sem autorização
        sem_auth = sum(1 for i in itens if not i.senha_autorizacao
                       and self._requires_auth(i.codigo_tuss))
        if sem_auth > 0:
            factors['sem_autorizacao'] = {
                'triggered': True,
                'value': sem_auth,
                'contribution': self.RISK_FACTORS['sem_autorizacao']['weight'],
            }

        # Fator 7: Documentação fraca
        if nlp_score is not None and nlp_score < 0.5:
            factors['documentacao_fraca'] = {
                'triggered': True,
                'value': nlp_score,
                'contribution': self.RISK_FACTORS['documentacao_fraca']['weight'],
            }

        # Calcular score composto
        total_weight = sum(f['contribution'] for f in factors.values())
        max_possible = sum(v['weight'] for v in self.RISK_FACTORS.values())
        risk_score = total_weight / max_possible if max_possible > 0 else 0

        # Ajustar pelo histórico de alertas
        if alertas_previos:
            alerta_boost = min(0.2, len(alertas_previos) * 0.03)
            risk_score = min(1.0, risk_score + alerta_boost)

        # Classificação
        if risk_score >= 0.7:
            risk_level = 'CRÍTICO'
            action = 'REVISÃO OBRIGATÓRIA antes do envio'
        elif risk_score >= 0.5:
            risk_level = 'ALTO'
            action = 'Revisão recomendada — prioridade alta'
        elif risk_score >= 0.3:
            risk_level = 'MÉDIO'
            action = 'Revisão seletiva de itens sinalizados'
        else:
            risk_level = 'BAIXO'
            action = 'Envio seguro — monitorar resultado'

        return {
            'risk_score': round(risk_score, 3),
            'risk_level': risk_level,
            'action': action,
            'factors': factors,
            'valor_total_conta': valor_total,
            'valor_em_risco': round(valor_total * risk_score, 2),
            'operadora': conta.operadora,
            'num_alertas_previos': len(alertas_previos) if alertas_previos else 0,
        }

    def _is_opme(self, codigo: str) -> bool:
        try:
            code_int = int(codigo.replace('.', ''))
            return 70101016 <= code_int <= 70999999
        except ValueError:
            return False

    def _requires_auth(self, codigo: str) -> bool:
        try:
            code_int = int(codigo.replace('.', ''))
            return code_int >= 30000000  # cirúrgicos, exames, terapias
        except ValueError:
            return False


# ============================================================
# ORQUESTRADOR PRINCIPAL
# ============================================================

class AntiGlosa:
    """Orquestrador: roda todos os módulos e gera relatório unificado."""

    def __init__(self):
        self.motor_tuss = MotorTUSS()
        self.extractor_nlp = ExtractorNLP()
        self.missing_charges = MissingChargesDetector()
        self.risk_scorer = RiskScorer()

    def audit_full(self, conta: ContaHospitalar) -> Dict[str, Any]:
        """Auditoria completa de uma conta hospitalar."""

        # Módulo 1: TUSS/CID
        alertas_tuss = self.motor_tuss.audit(conta)

        # Módulo 2: NLP
        alertas_nlp = self.extractor_nlp.audit(conta)
        analise_nlp = self.extractor_nlp.analyze_text(conta.prontuario_texto)

        # Módulo 3: Missing Charges
        alertas_miss = self.missing_charges.audit(conta)

        # Módulo 4: Risk Score
        all_alertas = alertas_tuss + alertas_nlp + alertas_miss
        risk = self.risk_scorer.score_conta(
            conta,
            alertas_previos=all_alertas,
            nlp_score=analise_nlp['score_documentacao'],
        )

        # Compilar resultado
        resultado = {
            'meta': {
                'conta_id': conta.id_conta,
                'paciente_id': conta.paciente_id,
                'operadora': conta.operadora,
                'data_auditoria': datetime.now().isoformat(),
                'versao_engine': '1.0.0',
            },
            'risk_score': risk,
            'resumo': {
                'total_alertas': len(all_alertas),
                'por_severidade': {
                    'crítica': sum(1 for a in all_alertas if a.severidade == 'crítica'),
                    'alta': sum(1 for a in all_alertas if a.severidade == 'alta'),
                    'média': sum(1 for a in all_alertas if a.severidade == 'média'),
                    'baixa': sum(1 for a in all_alertas if a.severidade == 'baixa'),
                },
                'por_modulo': {
                    'TUSS': len(alertas_tuss),
                    'NLP': len(alertas_nlp),
                    'MISS': len(alertas_miss),
                },
                'valor_total_conta': conta.valor_total,
                'valor_em_risco': risk['valor_em_risco'],
                'cobranças_perdidas': len(alertas_miss),
            },
            'alertas': {
                'tuss': [a.to_dict() for a in alertas_tuss],
                'nlp': [a.to_dict() for a in alertas_nlp],
                'missing': [a.to_dict() for a in alertas_miss],
            },
            'analise_nlp': analise_nlp,
            'recomendacoes_prioritarias': self._prioritize(all_alertas),
        }

        return resultado

    def _prioritize(self, alertas: List[Alerta]) -> List[Dict]:
        """Ordena alertas por score (impacto × probabilidade)."""
        sorted_alertas = sorted(alertas, key=lambda a: a.score, reverse=True)
        return [
            {
                'prioridade': i + 1,
                'modulo': a.modulo,
                'severidade': a.severidade,
                'descricao': a.descricao,
                'recomendacao': a.recomendacao,
                'score': round(a.score, 2),
            }
            for i, a in enumerate(sorted_alertas[:10])  # Top 10
        ]


# ============================================================
# CLI
# ============================================================

def demo_account() -> ContaHospitalar:
    """Gera conta demo para teste do sistema."""
    return ContaHospitalar(
        id_conta='DEMO-2026-001',
        paciente_id='PAC-000001',
        data_internacao='2026-02-20',
        data_alta='2026-03-01',
        cid_principal='E11.9',  # DM2
        cids_secundarios=['E78.5', 'I10', 'E66.0'],
        operadora='amil',
        tipo_atendimento='internação',
        itens=[
            ContaItem(
                id='IT-001', tipo='procedimento', codigo_tuss='30901016',
                descricao='Cirurgia bariátrica por videolaparoscopia',
                valor_unitario=15000, data='2026-02-22',
                medico_executante='Dr. Silva', cid_vinculado='E66.0',
                senha_autorizacao='AUTH-12345', data_senha='2026-01-10',
            ),
            ContaItem(
                id='IT-002', tipo='material', codigo_tuss='70301016',
                descricao='Grampeador linear cortante',
                quantidade=3, valor_unitario=2500, data='2026-02-22',
                # Sem justificativa, sem registro ANVISA
            ),
            ContaItem(
                id='IT-003', tipo='medicamento', codigo_tuss='60301016',
                descricao='Enoxaparina 40mg',
                quantidade=10, valor_unitario=85, data='2026-02-22',
            ),
            ContaItem(
                id='IT-004', tipo='diária', codigo_tuss='80101019',
                descricao='Diária de UTI',
                quantidade=3, valor_unitario=4500, data='2026-02-22',
            ),
            ContaItem(
                id='IT-005', tipo='honorário', codigo_tuss='10101012',
                descricao='Consulta endocrinologia',
                valor_unitario=350, data='2026-02-21',
                medico_executante='Dr. Palmiro',
            ),
            ContaItem(
                id='IT-006', tipo='honorário', codigo_tuss='10101012',
                descricao='Consulta endocrinologia',
                valor_unitario=350, data='2026-02-21',
                medico_executante='Dr. Palmiro',  # DUPLICADO!
            ),
            ContaItem(
                id='IT-007', tipo='taxa', codigo_tuss='80040177',
                descricao='Taxa de sala cirúrgica',
                valor_unitario=3200, data='2026-02-22',
            ),
            ContaItem(
                id='IT-008', tipo='exame', codigo_tuss='40301010',
                descricao='TSH ultrassensível',
                valor_unitario=45, data='2026-02-21',
            ),
            ContaItem(
                id='IT-009', tipo='exame', codigo_tuss='40301010',
                descricao='TSH ultrassensível',
                valor_unitario=45, data='2026-02-23',  # Repetido 2 dias depois
            ),
        ],
        prontuario_texto="""
        Paciente feminina, 45 anos, portadora de DM2 há 12 anos, obesidade grau III (IMC 42),
        HAS e dislipidemia. Indicada cirurgia bariátrica por videolaparoscopia.
        Monitorização contínua de glicose com sensor CGM durante internação.
        Avaliação nutricional pré-operatória realizada.
        Fisioterapia respiratória no pós-operatório.
        Mantida enoxaparina profilática.
        Evolução satisfatória. Alta com orientações.
        Necessidade de acompanhamento nutricional ambulatorial.
        Conforme rotina do serviço, manter seguimento endocrinológico.
        """,
        prescricoes=[
            'Enoxaparina 40mg SC 1x/dia',
            'Omeprazol 40mg IV 1x/dia',
            'Dipirona 1g IV 6/6h SN',
            'Ondansetrona 4mg IV 8/8h SN',
            'Insulina NPH conforme glicemia capilar',
        ],
        procedimentos_realizados=[
            'Cirurgia bariátrica sleeve',
            'Monitorização CGM',
            'Avaliação nutricional',
            'Fisioterapia respiratória',
        ],
    )


def main():
    parser = argparse.ArgumentParser(
        description='ANTIGLOSA — Motor de Auditoria Preditiva Hospitalar',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  # Rodar demo com conta simulada
  python antiglosa.py demo

  # Auditar conta de arquivo JSON
  python antiglosa.py audit --input conta.json

  # Apenas motor TUSS
  python antiglosa.py tuss --input conta.json

  # Apenas NLP do prontuário
  python antiglosa.py nlp --text "Paciente com DM2, indicado insulina bomba..."

  # Verificar perfil de operadora
  python antiglosa.py operadora --nome amil

  # Listar regras ativas
  python antiglosa.py regras
        """,
    )

    subparsers = parser.add_subparsers(dest='command')

    # Demo
    subparsers.add_parser('demo', help='Rodar auditoria completa com conta demo')

    # Audit
    p_audit = subparsers.add_parser('audit', help='Auditar conta de arquivo JSON')
    p_audit.add_argument('--input', required=True, help='Arquivo JSON da conta')
    p_audit.add_argument('--output', help='Arquivo de saída (default: stdout)')

    # TUSS only
    p_tuss = subparsers.add_parser('tuss', help='Apenas motor de regras TUSS')
    p_tuss.add_argument('--input', required=True, help='Arquivo JSON da conta')

    # NLP only
    p_nlp = subparsers.add_parser('nlp', help='Analisar texto de prontuário')
    p_nlp.add_argument('--text', help='Texto direto')
    p_nlp.add_argument('--file', help='Arquivo com texto do prontuário')

    # Operadora
    p_op = subparsers.add_parser('operadora', help='Perfil de operadora')
    p_op.add_argument('--nome', required=True, help='Nome da operadora')

    # Regras
    subparsers.add_parser('regras', help='Listar todas as regras ativas')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    engine = AntiGlosa()

    if args.command == 'demo':
        conta = demo_account()
        resultado = engine.audit_full(conta)
        print(json.dumps(resultado, ensure_ascii=False, indent=2, default=str))

    elif args.command == 'audit':
        with open(args.input) as f:
            data = json.load(f)
        conta = ContaHospitalar(**data)
        resultado = engine.audit_full(conta)
        output = json.dumps(resultado, ensure_ascii=False, indent=2, default=str)
        if args.output:
            with open(args.output, 'w') as f:
                f.write(output)
            print(f'Relatório salvo em {args.output}')
        else:
            print(output)

    elif args.command == 'tuss':
        with open(args.input) as f:
            data = json.load(f)
        conta = ContaHospitalar(**data)
        alertas = engine.motor_tuss.audit(conta)
        for a in alertas:
            print(json.dumps(a.to_dict(), ensure_ascii=False, indent=2, default=str))

    elif args.command == 'nlp':
        texto = args.text
        if args.file:
            with open(args.file) as f:
                texto = f.read()
        if not texto:
            print('Forneça --text ou --file')
            return
        resultado = engine.extractor_nlp.analyze_text(texto)
        print(json.dumps(resultado, ensure_ascii=False, indent=2, default=str))

    elif args.command == 'operadora':
        nome = args.nome.lower().replace(' ', '_')
        profile = OPERATOR_PROFILES.get(nome)
        if profile:
            print(json.dumps({nome: profile}, ensure_ascii=False, indent=2))
        else:
            print(f'Operadora "{args.nome}" não encontrada.')
            print(f'Disponíveis: {", ".join(OPERATOR_PROFILES.keys())}')

    elif args.command == 'regras':
        print(json.dumps({
            'incompatibilidade_tuss_cid': [
                {'id': r['id'], 'nome': r['name'], 'severidade': r['severity']}
                for r in INCOMPATIBILITY_RULES
            ],
            'documentacao_obrigatoria': {
                k: v['required_fields'] for k, v in DOCUMENTATION_RULES.items()
            },
            'operadoras_monitoradas': list(OPERATOR_PROFILES.keys()),
            'cobranças_perdidas_detectáveis': [p['trigger'] for p in COMMON_MISSING_CHARGES],
        }, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
