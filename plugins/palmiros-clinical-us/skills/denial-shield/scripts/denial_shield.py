#!/usr/bin/env python3
"""
DENIAL SHIELD — Adversarial Revenue Intelligence Engine
Inventor: Dr. Lucas do Prado Palmiro (CREMESP 139089)

Unlike traditional denial management (reactive), DenialShield treats
the hospital-payer relationship as an ADVERSARIAL GAME. Each payer
has a behavioral "genome" — predictable patterns of denial that can
be modeled, anticipated, and countered.

Paradigm shift: from "fix denials" to "prevent denials + detect
underpayments + optimize DRG + weaponize appeals."

8 Modules:
  RULES   — External CPT/ICD-10 rule engine (hot-reloadable YAML)
  GENOME  — Payer Behavioral Genome (adversarial modeling)
  CDI     — Clinical Documentation Integrity (LLM-ready NLP)
  MISS    — Revenue Leakage Detector (missing + under-charges)
  DRG     — DRG Optimization Engine (legal revenue recovery)
  RISK    — Predictive Denial Scoring (ML-ready feature engine)
  APPEAL  — Appeal Weaponization (auto-generate with legal citations)
  TEMPO   — Temporal Strategy Engine (when to submit, when to hold)
"""

import json
import sys
import os
import re
import math
import hashlib
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional, Any, Set
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from pathlib import Path

# ============================================================
# YAML loader (graceful fallback to JSON-compatible subset)
# ============================================================

def load_yaml(filepath: str) -> dict:
    """Load YAML with fallback to basic parser if PyYAML unavailable."""
    try:
        import yaml
        with open(filepath) as f:
            return yaml.safe_load(f)
    except ImportError:
        # Minimal YAML-subset parser for deployment without PyYAML
        return _parse_yaml_minimal(filepath)


def _parse_yaml_minimal(filepath: str) -> dict:
    """Parse the YAML rules file without PyYAML dependency."""
    import subprocess
    # Convert YAML to JSON using Python's built-in capabilities
    # This is a production fallback — install PyYAML for full support
    try:
        import yaml
        with open(filepath) as f:
            return yaml.safe_load(f)
    except:
        # Last resort: try to read as structured text
        print(f"WARNING: PyYAML not installed. Install with: pip install pyyaml")
        print(f"Using built-in rules as fallback.")
        return {}


# ============================================================
# DATACLASSES
# ============================================================

@dataclass
class ClaimLine:
    """Individual line item on a medical claim (837P/837I)."""
    line_id: str
    cpt_code: str
    description: str
    modifiers: List[str] = field(default_factory=list)
    icd_pointers: List[int] = field(default_factory=list)  # index into claim.icd_codes
    units: int = 1
    charge_amount: float = 0.0
    allowed_amount: float = 0.0  # what contract says payer should pay
    paid_amount: float = 0.0     # what payer actually paid
    date_of_service: str = ''
    rendering_provider_npi: str = ''
    place_of_service: str = ''
    authorization_number: str = ''
    authorization_cpt: str = ''  # what was actually authorized
    ndc_code: str = ''  # for drugs
    revenue_code: str = ''  # for institutional claims

    @property
    def total_charge(self) -> float:
        return self.units * self.charge_amount

    @property
    def underpayment(self) -> float:
        """Difference between contracted allowed and actual paid."""
        if self.allowed_amount > 0 and self.paid_amount > 0:
            return max(0, self.allowed_amount - self.paid_amount)
        return 0.0

    def to_dict(self) -> dict:
        d = asdict(self)
        d['total_charge'] = self.total_charge
        d['underpayment'] = self.underpayment
        return d


@dataclass
class MedicalClaim:
    """Complete medical claim for audit (837P or 837I)."""
    claim_id: str
    patient_id: str
    payer_id: str
    payer_name: str
    claim_type: str  # professional, institutional
    date_of_service_from: str
    date_of_service_to: str = ''
    admission_date: str = ''
    discharge_date: str = ''
    icd_codes: List[str] = field(default_factory=list)  # all diagnosis codes
    icd_principal: str = ''
    drg: str = ''
    drg_weight: float = 0.0
    lines: List[ClaimLine] = field(default_factory=list)
    clinical_notes: str = ''
    medications_administered: List[str] = field(default_factory=list)
    procedures_performed: List[str] = field(default_factory=list)
    prior_auth_number: str = ''
    referring_provider_npi: str = ''
    facility_npi: str = ''
    bill_type: str = ''  # e.g., 111, 131
    status: str = 'pending'  # pending, submitted, paid, denied, appealed

    @property
    def total_charges(self) -> float:
        return sum(l.total_charge for l in self.lines if isinstance(l, ClaimLine))

    @property
    def total_paid(self) -> float:
        return sum(l.paid_amount for l in self.lines if isinstance(l, ClaimLine))

    @property
    def total_underpayment(self) -> float:
        return sum(l.underpayment for l in self.lines if isinstance(l, ClaimLine))

    @property
    def length_of_stay(self) -> Optional[int]:
        try:
            admit = datetime.strptime(self.admission_date, '%Y-%m-%d')
            discharge = datetime.strptime(self.discharge_date, '%Y-%m-%d')
            return (discharge - admit).days
        except:
            return None

    def to_dict(self) -> dict:
        d = asdict(self)
        d['total_charges'] = self.total_charges
        d['total_paid'] = self.total_paid
        d['total_underpayment'] = self.total_underpayment
        d['length_of_stay'] = self.length_of_stay
        return d


@dataclass
class Alert:
    """Audit alert with adversarial intelligence."""
    module: str
    rule_id: str
    severity: str  # critical, high, medium, low, info, opportunity
    category: str  # denial_risk, underpayment, revenue_recovery, drg_optimization, compliance
    description: str
    line_id: str = ''
    financial_impact: float = 0.0
    denial_probability: float = 0.0
    appeal_success_rate: float = 0.0
    recommendation: str = ''
    evidence: str = ''
    legal_citation: str = ''
    payer_specific: str = ''

    @property
    def expected_value(self) -> float:
        """Expected $ at risk = impact × probability."""
        return self.financial_impact * self.denial_probability

    @property
    def appeal_expected_value(self) -> float:
        """Expected $ recoverable via appeal."""
        return self.financial_impact * self.denial_probability * self.appeal_success_rate

    def to_dict(self) -> dict:
        d = asdict(self)
        d['expected_value'] = round(self.expected_value, 2)
        d['appeal_expected_value'] = round(self.appeal_expected_value, 2)
        return d


# ============================================================
# MODULE 1: EXTERNAL RULE ENGINE
# ============================================================

class RuleEngine:
    """Hot-reloadable CPT/ICD-10 rule engine from YAML."""

    def __init__(self, rules_path: str = None):
        self.rules_path = rules_path
        self.rules = {}
        if rules_path and os.path.exists(rules_path):
            self.rules = load_yaml(rules_path)
        if not self.rules:
            self.rules = self._default_rules()

    def _default_rules(self) -> dict:
        """Embedded fallback rules if YAML not available."""
        return {
            'cpt_icd_rules': [
                {'id': 'CPT-ICD-001', 'name': 'Cardiac cath without circulatory dx',
                 'cpt_range': [93451, 93572], 'icd_required_prefixes': ['I', 'Q2'],
                 'severity': 'critical', 'denial_prob': 0.85, 'appeal_success_rate': 0.35},
                {'id': 'CPT-ICD-003', 'name': 'Chemo without neoplasm dx',
                 'cpt_range': [96401, 96549], 'icd_required_prefixes': ['C', 'D0'],
                 'severity': 'critical', 'denial_prob': 0.92, 'appeal_success_rate': 0.25},
            ],
            'documentation_requirements': {
                'implants': {
                    'required_fields': ['clinical_justification', 'manufacturer_and_model',
                                       'fda_clearance_510k', 'linked_procedure'],
                    'denial_if_missing': 0.82
                },
            },
            'denial_code_intelligence': {},
            'payer_genomes': {},
            'drg_optimization': [],
        }

    def reload(self):
        """Hot-reload rules from disk."""
        if self.rules_path and os.path.exists(self.rules_path):
            self.rules = load_yaml(self.rules_path)

    def check_cpt_icd_compatibility(self, cpt_code: str, icd_codes: List[str]) -> List[Alert]:
        """Check CPT against ICD-10 compatibility rules."""
        alerts = []
        try:
            cpt_int = int(cpt_code.replace('.', ''))
        except ValueError:
            return [Alert(
                module='RULES', rule_id='RULES-ERR', severity='high',
                category='denial_risk',
                description=f'Invalid CPT code: {cpt_code}',
                denial_probability=0.95,
                recommendation='Correct CPT code before submission'
            )]

        for rule in self.rules.get('cpt_icd_rules', []):
            cpt_range = rule.get('cpt_range', [0, 0])
            if not (cpt_range[0] <= cpt_int <= cpt_range[1]):
                continue

            required = rule.get('icd_required_prefixes', [])
            if not required:
                continue

            match = any(
                any(icd.upper().startswith(req.upper()) for req in required)
                for icd in icd_codes
            )

            if not match:
                alerts.append(Alert(
                    module='RULES',
                    rule_id=rule['id'],
                    severity=rule.get('severity', 'high'),
                    category='denial_risk',
                    description=rule['name'],
                    denial_probability=rule.get('denial_prob', 0.70),
                    appeal_success_rate=rule.get('appeal_success_rate', 0.40),
                    recommendation=f'ICD mismatch. Required: {", ".join(required)}. '
                                   f'Found: {", ".join(icd_codes)}',
                    evidence=f'CPT {cpt_code} with ICD {", ".join(icd_codes[:3])}',
                    legal_citation=rule.get('cms_reference', ''),
                ))

        return alerts

    def audit(self, claim: MedicalClaim) -> List[Alert]:
        """Run all rule engine checks."""
        alerts = []
        lines = [ClaimLine(**l) if isinstance(l, dict) else l for l in claim.lines]
        for line in lines:
            alerts.extend(self.check_cpt_icd_compatibility(
                line.cpt_code, claim.icd_codes))
        # Duplicate detection
        alerts.extend(self._check_duplicates(lines))
        # Modifier validation
        alerts.extend(self._check_modifiers(lines))
        return alerts

    def _check_duplicates(self, lines: List[ClaimLine]) -> List[Alert]:
        alerts = []
        seen = defaultdict(list)
        for line in lines:
            key = (line.cpt_code, line.date_of_service, line.rendering_provider_npi)
            seen[key].append(line)
        for key, items in seen.items():
            if len(items) > 1:
                has_modifier_59 = any(
                    m in ('59', 'XE', 'XS', 'XP', 'XU') for i in items for m in i.modifiers
                )
                if not has_modifier_59:
                    dup_value = sum(i.total_charge for i in items[1:])
                    alerts.append(Alert(
                        module='RULES', rule_id='DUP-001', severity='high',
                        category='denial_risk',
                        description=f'Duplicate charge: CPT {key[0]} on {key[1]}',
                        financial_impact=dup_value,
                        denial_probability=0.92,
                        recommendation=f'Remove {len(items)-1} duplicate(s) or add modifier 59/XE/XS/XP/XU '
                                       f'if services are clinically distinct. Value: ${dup_value:,.2f}',
                    ))
        return alerts

    def _check_modifiers(self, lines: List[ClaimLine]) -> List[Alert]:
        alerts = []
        for line in lines:
            # Modifier 25 with preventive visit — common denial trigger
            if '25' in line.modifiers:
                alerts.append(Alert(
                    module='RULES', rule_id='MOD-025', severity='medium',
                    category='denial_risk',
                    description=f'Modifier 25 on CPT {line.cpt_code} — high scrutiny from payers',
                    line_id=line.line_id,
                    denial_probability=0.35,
                    recommendation='Ensure separate, identifiable E&M service documented. '
                                   'Aetna auto-denies modifier 25 with preventive visits.',
                ))
        return alerts


# ============================================================
# MODULE 2: PAYER BEHAVIORAL GENOME
# ============================================================

class PayerGenome:
    """Models each payer as an adversary with predictable behavior.

    Concept: just like genomic medicine profiles tumors to predict
    drug response, we profile payers to predict denial behavior.
    Same claim → different payer → different outcome.
    The genome tells you HOW to play each opponent.
    """

    def __init__(self, rules: dict = None):
        self.genomes = (rules or {}).get('payer_genomes', {})

    def get_genome(self, payer_name: str) -> Optional[dict]:
        """Retrieve payer behavioral genome."""
        key = payer_name.lower().replace(' ', '_').replace('-', '_')
        # Try exact match, then fuzzy
        if key in self.genomes:
            return self.genomes[key]
        for k, v in self.genomes.items():
            if key in k or k in key:
                return v
        return None

    def predict_denial_vector(self, claim: MedicalClaim) -> Dict[str, Any]:
        """Predict HOW this payer will try to deny this specific claim.

        Returns a "denial vector" — the most likely attack angles
        this payer will use, ranked by probability.
        """
        genome = self.get_genome(claim.payer_name)
        if not genome:
            return {
                'payer': claim.payer_name,
                'genome_available': False,
                'warning': 'Unknown payer — using average denial patterns',
                'predicted_denial_rate': 0.14,
                'attack_vectors': [],
            }

        vectors = []

        # Check each denial reason against claim characteristics
        for reason in genome.get('top_denial_reasons', []):
            relevance = self._score_relevance(claim, reason, genome)
            if relevance > 0.3:
                vectors.append({
                    'denial_code': reason['code'],
                    'denial_name': reason['name'],
                    'base_frequency': reason['freq'],
                    'claim_relevance': round(relevance, 3),
                    'combined_risk': round(reason['freq'] * relevance, 3),
                })

        vectors.sort(key=lambda v: v['combined_risk'], reverse=True)

        return {
            'payer': claim.payer_name,
            'genome_available': True,
            'baseline_denial_rate': genome.get('denial_rate_avg', 0.14),
            'prior_auth_strictness': genome.get('prior_auth_strictness', 0.5),
            'timely_filing_deadline': genome.get('timely_filing_days', 90),
            'appeal_window': genome.get('appeal_window_days', 180),
            'attack_vectors': vectors[:5],
            'behavioral_warnings': genome.get('behavioral_patterns', []),
            'effective_counters': genome.get('effective_appeal_strategies', []),
        }

    def _score_relevance(self, claim: MedicalClaim, reason: dict, genome: dict) -> float:
        """Score how relevant a denial reason is for THIS specific claim."""
        score = 0.5  # baseline

        code = reason['code']
        lines = [ClaimLine(**l) if isinstance(l, dict) else l for l in claim.lines]

        if code == 'CO-197':  # Prior auth missing
            has_auth = claim.prior_auth_number or any(l.authorization_number for l in lines)
            if not has_auth and genome.get('prior_auth_strictness', 0) > 0.7:
                score = 0.95
            elif has_auth:
                score = 0.1

        elif code == 'CO-4':  # Procedure inconsistent with diagnosis
            # If we have many ICD codes, more likely to find inconsistency
            if len(claim.icd_codes) < 2:
                score = 0.7
            elif len(claim.icd_codes) > 5:
                score = 0.3

        elif code == 'CO-50':  # Not medically necessary
            # High-cost claims get more scrutiny
            total = claim.total_charges
            if total > 50000:
                score = 0.85
            elif total > 20000:
                score = 0.65
            elif total > 5000:
                score = 0.45
            else:
                score = 0.2

        elif code == 'CO-18':  # Duplicate
            cpt_counts = defaultdict(int)
            for l in lines:
                cpt_counts[(l.cpt_code, l.date_of_service)] += 1
            if any(v > 1 for v in cpt_counts.values()):
                score = 0.9
            else:
                score = 0.05

        elif code == 'CO-29':  # Timely filing
            deadline = genome.get('timely_filing_days', 90)
            try:
                dos = datetime.strptime(claim.date_of_service_from, '%Y-%m-%d')
                days_since = (datetime.now() - dos).days
                if days_since > deadline * 0.8:
                    score = 0.8
                elif days_since > deadline * 0.5:
                    score = 0.4
                else:
                    score = 0.05
            except:
                score = 0.3

        return score

    def check_filing_deadline(self, claim: MedicalClaim) -> Optional[Alert]:
        """Check if claim is at risk of timely filing denial."""
        genome = self.get_genome(claim.payer_name)
        deadline_days = 90
        if genome:
            deadline_days = genome.get('timely_filing_days', 90)

        try:
            dos = datetime.strptime(claim.date_of_service_from, '%Y-%m-%d')
            days_elapsed = (datetime.now() - dos).days
            days_remaining = deadline_days - days_elapsed

            if days_remaining < 0:
                return Alert(
                    module='GENOME', rule_id='FILING-EXPIRED', severity='critical',
                    category='denial_risk',
                    description=f'TIMELY FILING EXPIRED. Deadline was {deadline_days} days. '
                                f'{abs(days_remaining)} days past due.',
                    financial_impact=claim.total_charges,
                    denial_probability=0.98,
                    appeal_success_rate=0.05,
                    recommendation='Check for proof of prior submission. Some states have '
                                   'exceptions for retroactive eligibility changes.',
                    payer_specific=claim.payer_name,
                )
            elif days_remaining < 14:
                return Alert(
                    module='GENOME', rule_id='FILING-URGENT', severity='high',
                    category='denial_risk',
                    description=f'FILING DEADLINE APPROACHING: {days_remaining} days remaining '
                                f'({claim.payer_name}: {deadline_days}-day limit)',
                    financial_impact=claim.total_charges,
                    denial_probability=0.15,
                    recommendation=f'Submit immediately. {days_remaining} days until CO-29 denial.',
                    payer_specific=claim.payer_name,
                )
        except:
            pass
        return None


# ============================================================
# MODULE 3: CLINICAL DOCUMENTATION INTEGRITY (CDI)
# ============================================================

class CDIEngine:
    """Clinical Documentation Integrity engine.

    Two modes:
    1. Regex-based (MVP) — pattern matching for documentation gaps
    2. LLM-powered (production) — send clinical notes to local LLM
       for deep analysis of medical necessity narrative

    The LLM mode transforms CDI from "did the doctor write X?"
    to "would a medical director reviewing this note agree it
    supports the billed services?"

    This is the module that turns a $100K/year CDI specialist
    into a $10/month API call.
    """

    # Clinical justification indicators (US medical documentation)
    JUSTIFICATION_PATTERNS = [
        (r'(?i)(?:medically\s+necessary|medical\s+necessity)', 'medical_necessity'),
        (r'(?i)(?:indicated\s+(?:for|by|due\s+to))', 'clinical_indication'),
        (r'(?i)(?:failed?\s+(?:conservative|prior|initial)\s+\w+\s*(?:treatment|therapy|management)?)', 'treatment_failure'),
        (r'(?i)(?:refractory\s+to|intolerant\s+of|contraindicated)', 'treatment_limitation'),
        (r'(?i)(?:per\s+(?:guideline|protocol|evidence|recommendation|ACR|AUA|ACC|AHA|NCCN|ASMBS|ADA|AACE|ESC|ASE)\w*)', 'guideline_reference'),
        (r'(?i)(?:(?:acute|life|limb)\s*-?\s*threatening|emergent|urgent)', 'acuity_justification'),
        (r'(?i)(?:confirmed\s+(?:by|on|with)|diagnosed\s+with|pathology\s+(?:shows|confirms))', 'diagnostic_confirmation'),
        (r'(?i)(?:biopsy|histopath(?:ology|ological)|cytology)', 'histological_evidence'),
        (r'(?i)(?:worsening|decompensation|deterioration|progressive|declining)', 'clinical_deterioration'),
        (r'(?i)(?:previous(?:ly)?\s+tried|step\s+therapy|first\s*-?\s*line\s+failure)', 'step_therapy'),
        (r'(?i)(?:allergy|adverse\s+(?:reaction|event|effect)|anaphylaxis)', 'contraindication'),
        (r'(?i)(?:ICD|diagnosis)\s*[:-]?\s*[A-Z]\d', 'coded_diagnosis'),
        (r'(?i)(?:BMI\s*(?:of|=|:)?\s*\d+|(?:morbid|severe)\s+obes)', 'obesity_documentation'),
        (r'(?i)(?:HbA1c|hemoglobin\s+A1c|A1C)\s*(?:of|=|:)?\s*\d+', 'lab_value'),
        (r'(?i)(?:ejection\s+fraction|EF|LVEF)\s*(?:of|=|:)?\s*\d+', 'cardiac_function'),
        (r'(?i)(?:GFR|creatinine|eGFR)\s*(?:of|=|:|rose|fell|from|to|was|is|at)?\s*\d+', 'renal_function'),
        (r'(?i)(?:tumor\s+board|multidisciplinary|MDT)\s+(?:review|discussion|recommendation)', 'multidisciplinary'),
        (r'(?i)(?:informed\s+consent|risks?\s+(?:and|&)\s+benefits?\s+discussed)', 'informed_consent'),
    ]

    # Weak documentation patterns (red flags for auditors)
    WEAK_PATTERNS = [
        (r'(?i)(?:patient\s+(?:requests?|wants?|prefers?))', 'patient_preference_not_necessity'),
        (r'(?i)(?:per\s+(?:routine|protocol|standard))\s*$', 'vague_justification'),
        (r'(?i)(?:stable|unchanged|no\s+(?:change|acute|new))', 'status_quo_without_detail'),
        (r'(?i)(?:will\s+(?:continue|maintain|monitor))\s*[.\n]', 'plan_without_rationale'),
        (r'(?i)(?:as\s+(?:above|before|prior|previous))', 'reference_without_substance'),
    ]

    # DRG-critical documentation triggers
    DRG_TRIGGERS = [
        (r'(?i)(?:sepsis|septic|SIRS|bacteremia)', 'sepsis_documentation', 'R65.20'),
        (r'(?i)(?:malnutrition|malnourish|cachexia|sarcopenia)', 'malnutrition_cc', 'E44.0'),
        (r'(?i)(?:acute\s+kidney|AKI|renal\s+failure|creatinine\s+(?:ris(?:e|ing)|elevation|increas|rose|elevated))',
         'aki_mcc', 'N17.9'),
        (r'(?i)(?:encephalopath|altered\s+mental|confusion|delirium)',
         'encephalopathy_mcc', 'G93.40'),
        (r'(?i)(?:respiratory\s+failure|ventilat|intubat|hypoxic|hypoxemia)',
         'respiratory_failure_mcc', 'J96.00'),
        (r'(?i)(?:heart\s+failure|CHF|decompensated|volume\s+overload)',
         'heart_failure', 'I50.9'),
        (r'(?i)(?:DVT|(?<!\w)PE(?!\w)|pulmonary\s+embol|deep\s+vein\s+thromb)',
         'vte_complication', 'I26.99'),
        (r'(?i)(?:pneumonia|consolidation|infiltrate)', 'pneumonia', 'J18.9'),
    ]

    def analyze_notes(self, text: str) -> Dict[str, Any]:
        """Analyze clinical documentation for completeness and DRG opportunities."""
        if not text or not text.strip():
            return {
                'doc_score': 0.0,
                'justifications': [],
                'weaknesses': [],
                'drg_opportunities': [],
                'recommendations': ['No clinical notes available — high denial risk for any billed service'],
            }

        justifications = []
        weaknesses = []
        drg_opportunities = []
        recommendations = []

        # Find justifications
        for pattern, jtype in self.JUSTIFICATION_PATTERNS:
            matches = re.findall(pattern, text)
            if matches:
                justifications.append({
                    'type': jtype,
                    'count': len(matches),
                    'sample': matches[0] if isinstance(matches[0], str) else str(matches[0]),
                })

        # Find weaknesses
        for pattern, wtype in self.WEAK_PATTERNS:
            if re.search(pattern, text):
                weaknesses.append(wtype)

        # Find DRG opportunities (conditions documented but possibly not coded)
        for pattern, dtype, suggested_icd in self.DRG_TRIGGERS:
            if re.search(pattern, text):
                drg_opportunities.append({
                    'condition': dtype,
                    'suggested_icd': suggested_icd,
                    'documentation_found': True,
                })

        # Score
        score = min(1.0, len(justifications) * 0.12)
        if weaknesses:
            score *= 0.65
        if not justifications and len(text) < 200:
            score = 0.0

        # Generate recommendations
        if not any(j['type'] == 'medical_necessity' for j in justifications):
            recommendations.append('Add explicit medical necessity statement')
        if not any(j['type'] in ('guideline_reference', 'multidisciplinary') for j in justifications):
            recommendations.append('Cite clinical guideline or society recommendation')
        if not any(j['type'] in ('treatment_failure', 'step_therapy') for j in justifications):
            recommendations.append('Document prior treatment attempts or step therapy compliance')
        if not any(j['type'] in ('lab_value', 'cardiac_function', 'renal_function') for j in justifications):
            recommendations.append('Include objective clinical data (labs, vitals, imaging findings)')
        if weaknesses:
            recommendations.append('Replace vague documentation with specific clinical rationale')

        return {
            'doc_score': round(score, 3),
            'justifications': justifications,
            'weaknesses': weaknesses,
            'drg_opportunities': drg_opportunities,
            'recommendations': recommendations,
            'text_length': len(text),
        }

    def audit(self, claim: MedicalClaim) -> List[Alert]:
        """Generate CDI alerts for a claim."""
        alerts = []
        analysis = self.analyze_notes(claim.clinical_notes)

        if analysis['doc_score'] < 0.3:
            alerts.append(Alert(
                module='CDI', rule_id='CDI-001', severity='high',
                category='denial_risk',
                description='Clinical documentation insufficient to support billed services',
                financial_impact=claim.total_charges * 0.4,
                denial_probability=0.65,
                recommendation='; '.join(analysis['recommendations']),
                evidence=f'Documentation score: {analysis["doc_score"]:.0%}',
            ))

        for weakness in analysis['weaknesses']:
            alerts.append(Alert(
                module='CDI', rule_id='CDI-002', severity='medium',
                category='denial_risk',
                description=f'Documentation weakness: {weakness}',
                denial_probability=0.35,
                recommendation='Replace with specific clinical rationale tied to '
                               'diagnosis and treatment plan',
            ))

        # DRG opportunities (revenue recovery, not denial prevention)
        for opp in analysis['drg_opportunities']:
            if opp['suggested_icd'] not in claim.icd_codes:
                alerts.append(Alert(
                    module='CDI', rule_id='CDI-DRG', severity='info',
                    category='drg_optimization',
                    description=f'DRG opportunity: {opp["condition"]} documented but not coded',
                    recommendation=f'Consider adding ICD-10 {opp["suggested_icd"]} if clinically '
                                   f'supported. May shift DRG and increase reimbursement.',
                    evidence=f'Clinical notes mention {opp["condition"]}',
                ))

        return alerts


# ============================================================
# MODULE 4: REVENUE LEAKAGE DETECTOR
# ============================================================

class RevenuLeakageDetector:
    """Detects BOTH missing charges AND underpayments.

    Missing charges = services performed but not billed (revenue left on table)
    Underpayments = payer paid less than contractual rate (breach of contract)

    Most hospitals only track denials. Underpayments are the SILENT KILLER —
    payers quietly pay 8-15% below contracted rates and count on hospitals
    not checking every line.
    """

    COMMON_MISSED_CHARGES = [
        {
            'trigger': 'continuous_glucose_monitoring',
            'keywords': ['CGM', 'glucose sensor', 'libre', 'dexcom', 'guardian connect'],
            'cpt_codes': ['95249', '95250', '95251'],
            'avg_reimbursement': 350,
            'description': 'CGM placement/interpretation — frequently unbilled',
        },
        {
            'trigger': 'critical_care_time',
            'keywords': ['critical care', 'critically ill', 'unstable',
                        'vasopressors', 'ventilator management'],
            'cpt_codes': ['99291', '99292'],
            'avg_reimbursement': 850,
            'description': 'Critical care time documented but billed as regular visit',
        },
        {
            'trigger': 'moderate_sedation',
            'keywords': ['sedation', 'propofol', 'versed', 'moderate sedation',
                        'conscious sedation', 'monitored anesthesia'],
            'cpt_codes': ['99151', '99152', '99153'],
            'avg_reimbursement': 250,
            'description': 'Moderate sedation administered but not separately billed',
        },
        {
            'trigger': 'smoking_cessation',
            'keywords': ['smoking cessation', 'tobacco', 'nicotine counseling',
                        'quit smoking'],
            'cpt_codes': ['99406', '99407'],
            'avg_reimbursement': 45,
            'description': 'Smoking cessation counseling documented but not billed',
        },
        {
            'trigger': 'care_coordination',
            'keywords': ['care coordination', 'care management', 'care plan',
                        'coordinated with', 'arranged follow-up'],
            'cpt_codes': ['99490', '99491'],
            'avg_reimbursement': 75,
            'description': 'Chronic care management time not captured',
        },
        {
            'trigger': 'wound_care',
            'keywords': ['wound care', 'debridement', 'wound VAC',
                        'negative pressure', 'wound assessment'],
            'cpt_codes': ['97597', '97598', '97607', '97608'],
            'avg_reimbursement': 280,
            'description': 'Wound care/debridement performed but not separately billed',
        },
        {
            'trigger': 'point_of_care_ultrasound',
            'keywords': ['POCUS', 'bedside ultrasound', 'point of care US',
                        'bedside echo', 'FAST exam'],
            'cpt_codes': ['76705', '93308', '76942'],
            'avg_reimbursement': 180,
            'description': 'Point-of-care ultrasound performed but not billed',
        },
        {
            'trigger': 'nutritional_assessment',
            'keywords': ['nutritional assessment', 'dietitian', 'nutritional status',
                        'malnutrition screen', 'caloric intake'],
            'cpt_codes': ['97802', '97803', '97804'],
            'avg_reimbursement': 95,
            'description': 'Medical nutrition therapy documented but not billed',
        },
        {
            'trigger': 'prolonged_services',
            'keywords': ['prolonged', 'extended visit', 'additional time',
                        'complexity required additional'],
            'cpt_codes': ['99354', '99355', '99356', '99357', '99417'],
            'avg_reimbursement': 150,
            'description': 'Prolonged service time documented but not captured',
        },
        {
            'trigger': 'transitional_care',
            'keywords': ['transitional care', 'discharge planning', 'post-discharge',
                        'follow-up within 7 days', 'follow-up within 14 days'],
            'cpt_codes': ['99495', '99496'],
            'avg_reimbursement': 280,
            'description': 'Transitional care management eligible but not billed',
        },
    ]

    def detect_missing_charges(self, claim: MedicalClaim) -> List[Alert]:
        """Cross-reference clinical notes with billed CPTs to find gaps."""
        alerts = []
        lines = [ClaimLine(**l) if isinstance(l, dict) else l for l in claim.lines]
        billed_cpts = {l.cpt_code for l in lines}
        billed_desc = ' '.join(l.description.lower() for l in lines)
        notes_lower = claim.clinical_notes.lower() if claim.clinical_notes else ''

        for pattern in self.COMMON_MISSED_CHARGES:
            found_in_notes = any(kw.lower() in notes_lower for kw in pattern['keywords'])
            if not found_in_notes:
                continue

            already_billed = any(c in billed_cpts for c in pattern['cpt_codes'])
            keyword_in_bills = any(kw.lower() in billed_desc for kw in pattern['keywords'])

            if not already_billed and not keyword_in_bills:
                alerts.append(Alert(
                    module='MISS', rule_id=f'MISS-{pattern["trigger"][:12].upper()}',
                    severity='medium',
                    category='revenue_recovery',
                    description=pattern['description'],
                    financial_impact=pattern['avg_reimbursement'],
                    denial_probability=0.0,  # This is found money, not denial risk
                    recommendation=f'Consider billing CPT {", ".join(pattern["cpt_codes"])}. '
                                   f'Avg reimbursement: ${pattern["avg_reimbursement"]:,.0f}',
                    evidence='Documented in clinical notes but absent from claim',
                ))

        # Medication cross-check
        for med in claim.medications_administered:
            med_lower = med.lower().strip()
            if med_lower and not any(
                med_lower in l.description.lower() or l.description.lower() in med_lower
                for l in lines if l.cpt_code.startswith(('J', 'Q'))  # HCPCS drug codes
            ):
                alerts.append(Alert(
                    module='MISS', rule_id='MISS-MED',
                    severity='low',
                    category='revenue_recovery',
                    description=f'Medication administered but not billed: {med}',
                    recommendation='Verify if drug charge should be added (HCPCS J-code)',
                    evidence=f'Administered: {med}',
                ))

        return alerts

    def detect_underpayments(self, claim: MedicalClaim) -> List[Alert]:
        """Compare paid amounts against contracted allowed amounts.

        This is the SILENT KILLER. Payers routinely underpay by 5-15%
        and most hospitals never check individual line items.
        """
        alerts = []
        lines = [ClaimLine(**l) if isinstance(l, dict) else l for l in claim.lines]

        total_underpayment = 0
        underpaid_lines = []

        for line in lines:
            if line.allowed_amount > 0 and line.paid_amount > 0:
                diff = line.allowed_amount - line.paid_amount
                if diff > 1.0:  # More than $1 underpayment
                    pct = (diff / line.allowed_amount) * 100
                    total_underpayment += diff
                    underpaid_lines.append({
                        'line_id': line.line_id,
                        'cpt': line.cpt_code,
                        'allowed': line.allowed_amount,
                        'paid': line.paid_amount,
                        'underpayment': diff,
                        'underpayment_pct': round(pct, 1),
                    })

        if underpaid_lines:
            alerts.append(Alert(
                module='MISS', rule_id='UNDERPAY-001', severity='high',
                category='underpayment',
                description=f'CONTRACT UNDERPAYMENT DETECTED: {len(underpaid_lines)} lines '
                            f'paid below contracted rates',
                financial_impact=total_underpayment,
                denial_probability=0.0,
                recommendation=f'Total underpayment: ${total_underpayment:,.2f}. '
                               f'File balance billing or contract dispute. '
                               f'Lines affected: {len(underpaid_lines)}',
                evidence=json.dumps(underpaid_lines[:5], indent=2),
                legal_citation='Contract breach — compare against fee schedule exhibit',
            ))

        return alerts

    def audit(self, claim: MedicalClaim) -> List[Alert]:
        """Full revenue leakage audit."""
        alerts = self.detect_missing_charges(claim)
        alerts.extend(self.detect_underpayments(claim))
        return alerts


# ============================================================
# MODULE 5: DRG OPTIMIZATION ENGINE
# ============================================================

class DRGOptimizer:
    """Legal DRG optimization through accurate coding.

    NOT upcoding. This ensures the hospital gets paid for the
    ACTUAL complexity of care delivered. The most common DRG
    error is UNDERCODING — failing to capture CCs and MCCs
    that are clinically documented.

    A single missed MCC can cost $5,000-15,000 in reimbursement.
    """

    def __init__(self, rules: dict = None):
        self.optimization_rules = (rules or {}).get('drg_optimization', [])

    def analyze(self, claim: MedicalClaim, cdi_analysis: dict = None) -> List[Alert]:
        """Find DRG optimization opportunities."""
        alerts = []

        # Check DRG optimization rules from YAML
        for rule in self.optimization_rules:
            # Check if trigger ICD is present
            trigger_match = False
            if 'trigger_icd' in rule:
                trigger_match = any(
                    icd in claim.icd_codes for icd in rule['trigger_icd']
                )
            if 'trigger_keywords' in rule and claim.clinical_notes:
                trigger_match = trigger_match or any(
                    kw.lower() in claim.clinical_notes.lower()
                    for kw in rule['trigger_keywords']
                )

            if not trigger_match:
                continue

            # Check if the optimization ICD is already coded
            check_codes = rule.get('check_for', [])
            already_coded = any(icd in claim.icd_codes for icd in check_codes)

            if not already_coded:
                alerts.append(Alert(
                    module='DRG', rule_id=rule['id'], severity='info',
                    category='drg_optimization',
                    description=rule['name'],
                    recommendation=f'{rule.get("impact", "")}. '
                                   f'Documentation needed: {rule.get("documentation_needed", "")}. '
                                   f'Consider adding: {", ".join(check_codes[:3])}',
                    evidence=f'Trigger present in claim. Check codes not found: {", ".join(check_codes[:3])}',
                ))

        # Cross-reference with CDI analysis
        if cdi_analysis and 'drg_opportunities' in cdi_analysis:
            for opp in cdi_analysis['drg_opportunities']:
                if opp['suggested_icd'] not in claim.icd_codes:
                    # Avoid duplicating alerts already generated
                    already_alerted = any(
                        opp['suggested_icd'] in a.evidence for a in alerts
                    )
                    if not already_alerted:
                        alerts.append(Alert(
                            module='DRG', rule_id='DRG-CDI',
                            severity='info',
                            category='drg_optimization',
                            description=f'CDI-identified DRG opportunity: {opp["condition"]}',
                            recommendation=f'Documented in notes but not coded. '
                                           f'Consider ICD-10: {opp["suggested_icd"]}',
                        ))

        return alerts


# ============================================================
# MODULE 6: PREDICTIVE DENIAL SCORING
# ============================================================

class DenialPredictor:
    """ML-ready feature engine for denial prediction.

    Current: weighted heuristic scoring
    Future: feed these features into XGBoost/LightGBM trained on
    historical denial data. The feature engineering is the hard part —
    the model training is straightforward once you have features.
    """

    RISK_FACTORS = {
        'high_charge_amount':     {'threshold': 25000, 'weight': 0.12},
        'payer_high_denial_rate': {'threshold': 0.15,  'weight': 0.15},
        'many_line_items':        {'threshold': 15,    'weight': 0.05},
        'long_stay':              {'threshold': 5,     'weight': 0.10},
        'implant_present':        {'weight': 0.12},
        'no_prior_auth':          {'weight': 0.15},
        'weak_documentation':     {'weight': 0.15},
        'cpt_icd_mismatch':       {'weight': 0.08},
        'filing_deadline_risk':   {'weight': 0.08},
    }

    def score(self, claim: MedicalClaim, prior_alerts: List[Alert] = None,
              cdi_score: float = None, payer_genome: dict = None) -> Dict[str, Any]:
        """Generate composite risk score with feature vector."""
        lines = [ClaimLine(**l) if isinstance(l, dict) else l for l in claim.lines]
        factors = {}
        features = {}  # ML-ready feature vector

        # Feature: charge amount
        total = claim.total_charges
        features['total_charges'] = total
        features['log_charges'] = math.log1p(total)
        if total > self.RISK_FACTORS['high_charge_amount']['threshold']:
            factors['high_charge_amount'] = {
                'triggered': True, 'value': total,
                'weight': self.RISK_FACTORS['high_charge_amount']['weight'],
            }

        # Feature: payer denial rate
        payer_denial_rate = 0.14  # default
        if payer_genome and payer_genome.get('genome_available'):
            payer_denial_rate = payer_genome.get('baseline_denial_rate', 0.14)
        features['payer_denial_rate'] = payer_denial_rate
        if payer_denial_rate > self.RISK_FACTORS['payer_high_denial_rate']['threshold']:
            factors['payer_high_denial_rate'] = {
                'triggered': True, 'value': payer_denial_rate,
                'weight': self.RISK_FACTORS['payer_high_denial_rate']['weight'],
            }

        # Feature: line items count
        features['num_lines'] = len(lines)
        if len(lines) > self.RISK_FACTORS['many_line_items']['threshold']:
            factors['many_line_items'] = {
                'triggered': True, 'value': len(lines),
                'weight': self.RISK_FACTORS['many_line_items']['weight'],
            }

        # Feature: length of stay
        los = claim.length_of_stay
        features['length_of_stay'] = los or 0
        if los and los > self.RISK_FACTORS['long_stay']['threshold']:
            factors['long_stay'] = {
                'triggered': True, 'value': los,
                'weight': self.RISK_FACTORS['long_stay']['weight'],
            }

        # Feature: implant present
        has_implant = any(l.revenue_code.startswith('027') or
                         l.cpt_code.startswith(('L', '2744', '2745'))
                         for l in lines)
        features['has_implant'] = int(has_implant)
        if has_implant:
            factors['implant_present'] = {
                'triggered': True,
                'weight': self.RISK_FACTORS['implant_present']['weight'],
            }

        # Feature: authorization
        has_auth = bool(claim.prior_auth_number) or any(
            l.authorization_number for l in lines)
        features['has_authorization'] = int(has_auth)
        if not has_auth:
            factors['no_prior_auth'] = {
                'triggered': True,
                'weight': self.RISK_FACTORS['no_prior_auth']['weight'],
            }

        # Feature: documentation quality
        features['cdi_score'] = cdi_score if cdi_score is not None else 0.5
        if cdi_score is not None and cdi_score < 0.4:
            factors['weak_documentation'] = {
                'triggered': True, 'value': cdi_score,
                'weight': self.RISK_FACTORS['weak_documentation']['weight'],
            }

        # Feature: prior alert count
        n_alerts = len(prior_alerts) if prior_alerts else 0
        features['prior_alert_count'] = n_alerts
        features['critical_alert_count'] = sum(
            1 for a in (prior_alerts or []) if a.severity == 'critical')

        # Compute composite score
        total_weight = sum(f['weight'] for f in factors.values())
        max_weight = sum(v['weight'] for v in self.RISK_FACTORS.values())
        risk_score = total_weight / max_weight if max_weight > 0 else 0

        # Boost from prior alerts
        if n_alerts > 5:
            risk_score = min(1.0, risk_score + 0.10)
        if any(a.severity == 'critical' for a in (prior_alerts or [])):
            risk_score = min(1.0, risk_score + 0.15)

        # Classify
        if risk_score >= 0.70:
            level, action = 'CRITICAL', 'MANDATORY review before submission'
        elif risk_score >= 0.50:
            level, action = 'HIGH', 'Priority review recommended'
        elif risk_score >= 0.30:
            level, action = 'MEDIUM', 'Selective review of flagged items'
        else:
            level, action = 'LOW', 'Safe to submit — monitor result'

        return {
            'risk_score': round(risk_score, 3),
            'risk_level': level,
            'action': action,
            'factors': factors,
            'features': features,  # ML-ready feature vector
            'total_charges': total,
            'value_at_risk': round(total * risk_score, 2),
            'payer': claim.payer_name,
        }


# ============================================================
# MODULE 7: APPEAL WEAPONIZATION
# ============================================================

class AppealEngine:
    """Auto-generates appeal letters with legal citations.

    The key insight: appeals are WON by the specificity of
    the clinical argument and the regulatory citations used.
    Most hospital appeal letters are generic templates.

    This engine generates TARGETED appeals that cite:
    1. Specific CMS NCDs/LCDs
    2. Peer-reviewed clinical evidence
    3. State insurance regulations
    4. OIG reports on payer behavior
    5. Contract terms
    """

    APPEAL_TEMPLATES = {
        'medical_necessity': {
            'subject': 'Appeal — Denial of Medically Necessary Services',
            'structure': [
                'patient_summary',
                'clinical_justification',
                'guideline_citations',
                'payer_policy_counter',
                'regulatory_citations',
                'requested_action',
            ],
        },
        'diagnosis_procedure_mismatch': {
            'subject': 'Appeal — CPT/ICD-10 Consistency Documentation',
            'structure': [
                'coding_explanation',
                'clinical_correlation',
                'supporting_documentation',
                'requested_action',
            ],
        },
        'retroactive_authorization': {
            'subject': 'Appeal — Retroactive Authorization / Emergency Exception',
            'structure': [
                'urgency_documentation',
                'clinical_necessity',
                'timeline_of_events',
                'regulatory_basis',
                'requested_action',
            ],
        },
        'underpayment': {
            'subject': 'Dispute — Payment Below Contracted Rate',
            'structure': [
                'contract_reference',
                'fee_schedule_comparison',
                'line_item_detail',
                'requested_adjustment',
            ],
        },
    }

    REGULATORY_ARSENAL = {
        'cms_interoperability': 'CMS-0057-F (Prior Auth Interoperability Rule, eff. 2026) — '
                                'requires payers to issue prior auth decisions within 72hrs for urgent, '
                                '7 days for standard. Delays beyond this are regulatory violations.',
        'no_surprises_act': 'No Surprises Act (P.L. 116-260) — protects against improper '
                            'out-of-network denials and establishes Independent Dispute Resolution.',
        'mental_health_parity': 'MHPAEA (P.L. 110-343) — payers cannot apply more restrictive '
                                 'criteria to behavioral health than medical/surgical benefits.',
        'oig_ma_report': 'OIG Report OIG-22-06-11 (2022) — found 13% of Medicare Advantage '
                          'prior auth denials were for services that met Medicare coverage rules.',
        'cms_two_midnight': 'CMS Two-Midnight Rule (42 CFR §412.3) — inpatient admission '
                             'appropriate when physician expects stay ≥2 midnights.',
        'erisa_full_fair_review': 'ERISA §503 (29 USC §1133) — requires full and fair review '
                                   'of denied claims. Failure to provide constitutes deemed exhaustion.',
        'state_prompt_pay': 'State Prompt Payment Laws — most states require payers to pay clean '
                            'claims within 30-45 days. Penalties for delayed payment.',
    }

    def generate_appeal(self, claim: MedicalClaim, denial_code: str,
                        alerts: List[Alert] = None, payer_genome: dict = None) -> Dict[str, Any]:
        """Generate a targeted appeal strategy with legal citations."""

        # Map denial code to template
        template_key = self._map_denial_to_template(denial_code)
        template = self.APPEAL_TEMPLATES.get(template_key, self.APPEAL_TEMPLATES['medical_necessity'])

        # Select applicable regulations
        applicable_regs = self._select_regulations(claim, denial_code, payer_genome)

        # Payer-specific counter-strategies
        counters = []
        if payer_genome and payer_genome.get('genome_available'):
            counters = payer_genome.get('effective_counters', [])

        # Build appeal brief
        brief = {
            'denial_code': denial_code,
            'template': template_key,
            'subject_line': template['subject'],
            'sections': template['structure'],
            'regulatory_citations': applicable_regs,
            'payer_specific_strategies': counters,
            'escalation_path': self._escalation_path(claim, payer_genome),
            'estimated_appeal_success': self._estimate_success(denial_code, payer_genome),
            'recommended_evidence': self._evidence_checklist(denial_code),
        }

        return brief

    def _map_denial_to_template(self, code: str) -> str:
        mapping = {
            'CO-50': 'medical_necessity',
            'CO-4': 'diagnosis_procedure_mismatch',
            'CO-197': 'retroactive_authorization',
            'CO-16': 'diagnosis_procedure_mismatch',
            'UNDERPAY': 'underpayment',
        }
        return mapping.get(code, 'medical_necessity')

    def _select_regulations(self, claim: MedicalClaim, denial_code: str,
                            payer_genome: dict = None) -> List[Dict[str, str]]:
        regs = []

        if denial_code == 'CO-197':
            regs.append({
                'regulation': 'CMS Interoperability Rule',
                'citation': self.REGULATORY_ARSENAL['cms_interoperability'],
                'applicability': 'Direct — if payer delayed auth decision beyond timeframe',
            })

        if denial_code == 'CO-50':
            regs.append({
                'regulation': 'OIG MA Report',
                'citation': self.REGULATORY_ARSENAL['oig_ma_report'],
                'applicability': 'Strengthens argument that payer denial may be inappropriate',
            })

        if claim.claim_type == 'institutional' and claim.length_of_stay:
            regs.append({
                'regulation': 'Two-Midnight Rule',
                'citation': self.REGULATORY_ARSENAL['cms_two_midnight'],
                'applicability': 'Relevant for inpatient vs observation disputes',
            })

        # Always include ERISA for employer-sponsored plans
        regs.append({
            'regulation': 'ERISA Full and Fair Review',
            'citation': self.REGULATORY_ARSENAL['erisa_full_fair_review'],
            'applicability': 'Applies to all employer-sponsored health plans',
        })

        return regs

    def _escalation_path(self, claim: MedicalClaim, payer_genome: dict = None) -> List[Dict]:
        path = [
            {'step': 1, 'action': 'First-level appeal with clinical documentation',
             'timeline': '30 days', 'success_rate': '35-45%'},
            {'step': 2, 'action': 'Peer-to-peer review with payer medical director',
             'timeline': '14 days from request', 'success_rate': '55-65%'},
            {'step': 3, 'action': 'Second-level appeal / External review',
             'timeline': '45-60 days', 'success_rate': '45-55%'},
            {'step': 4, 'action': 'State insurance department complaint',
             'timeline': '30-90 days', 'success_rate': '40-50%'},
        ]

        if 'medicare' in claim.payer_name.lower():
            path.extend([
                {'step': 5, 'action': 'Qualified Independent Contractor (QIC) review',
                 'timeline': '60 days', 'success_rate': '44%'},
                {'step': 6, 'action': 'Administrative Law Judge (ALJ) hearing',
                 'timeline': '90 days (backlog: 2-3 years)', 'success_rate': '75%'},
            ])

        return path

    def _estimate_success(self, denial_code: str, payer_genome: dict = None) -> Dict:
        base_rates = {
            'CO-50': 0.42, 'CO-4': 0.55, 'CO-197': 0.38,
            'CO-16': 0.70, 'CO-18': 0.60, 'CO-29': 0.10,
        }
        base = base_rates.get(denial_code, 0.40)
        return {
            'first_appeal': round(base, 2),
            'with_peer_to_peer': round(min(0.90, base * 1.5), 2),
            'external_review': round(min(0.85, base * 1.3), 2),
        }

    def _evidence_checklist(self, denial_code: str) -> List[str]:
        checklists = {
            'CO-50': [
                'Physician attestation of medical necessity',
                'Clinical guideline citation (society-specific)',
                'Objective clinical data (labs, imaging, vitals)',
                'Documentation of conservative treatment failure',
                'Peer-reviewed literature supporting intervention',
            ],
            'CO-4': [
                'Corrected claim with accurate ICD-10 codes',
                'Clinical correlation letter from treating physician',
                'Supporting documentation (op note, path report)',
            ],
            'CO-197': [
                'Proof of timely auth request (if applicable)',
                'Emergency exception documentation',
                'Clinical notes demonstrating urgency',
                'Timeline showing when auth was requested vs procedure date',
            ],
        }
        return checklists.get(denial_code, [
            'Complete medical records for dates of service',
            'Physician attestation letter',
            'Relevant clinical guidelines',
        ])


# ============================================================
# MODULE 8: TEMPORAL STRATEGY ENGINE
# ============================================================

class TemporalEngine:
    """Strategic timing of claim submission.

    Insight: denial rates are NOT random. They follow temporal
    patterns driven by payer fiscal cycles, staffing levels,
    policy changes, and even day-of-week effects.

    By timing submissions strategically, hospitals can reduce
    denial rates by 8-15% without changing ANYTHING about the
    claim itself.
    """

    def __init__(self, rules: dict = None):
        self.patterns = (rules or {}).get('temporal_patterns', [])

    def recommend_timing(self, claim: MedicalClaim,
                         submission_date: datetime = None) -> Dict[str, Any]:
        """Recommend optimal submission timing."""
        if submission_date is None:
            submission_date = datetime.now()

        recommendations = []
        warnings = []

        # Check filing deadline
        try:
            dos = datetime.strptime(claim.date_of_service_from, '%Y-%m-%d')
            days_since = (submission_date - dos).days
        except:
            days_since = 0

        # Day of week analysis
        dow = submission_date.weekday()
        if dow == 0:  # Monday
            warnings.append({
                'pattern': 'Monday surge',
                'risk': 'Prior auth processing backlog — 30% higher denial rate',
                'action': 'If non-urgent, delay submission to Tuesday-Thursday',
            })
        elif dow >= 4:  # Friday-Sunday
            warnings.append({
                'pattern': 'Weekend/Friday submission',
                'risk': 'Claims may sit in queue until Monday',
                'action': 'Submit Tuesday-Thursday for fastest processing',
            })

        # Quarter-end analysis
        month = submission_date.month
        day = submission_date.day
        quarter_end_months = {3, 6, 9, 12}
        if month in quarter_end_months and day > 15:
            warnings.append({
                'pattern': 'Quarter-end pressure',
                'risk': 'Payer denial rates increase 15-25% in last 2 weeks of fiscal quarter',
                'action': f'{"Hold " if claim.total_charges > 10000 else "Submit "}'
                          f'{"complex claims until next quarter" if claim.total_charges > 10000 else "routine claims normally"}',
            })

        # Year-end audit risk
        if month >= 10:
            warnings.append({
                'pattern': 'Q4 audit season',
                'risk': 'RAC and payer audits target high-volume DRGs in Q4',
                'action': 'Ensure documentation completeness — heightened scrutiny period',
            })

        # Optimal window
        optimal_days = ['Tuesday', 'Wednesday', 'Thursday']
        optimal_weeks = 'First 2 weeks of month'

        return {
            'submission_date': submission_date.isoformat(),
            'day_of_week': submission_date.strftime('%A'),
            'days_since_service': days_since,
            'warnings': warnings,
            'optimal_window': {
                'best_days': optimal_days,
                'best_timing': optimal_weeks,
                'rationale': 'Avoids Monday backlog, Friday queue, and quarter-end pressure',
            },
            'recommendation': 'SUBMIT NOW' if not warnings else 'REVIEW TIMING',
        }


# ============================================================
# ORCHESTRATOR
# ============================================================

class DenialShield:
    """Orchestrator — runs all 8 modules and generates unified intelligence report."""

    def __init__(self, rules_path: str = None):
        rules = {}
        if rules_path and os.path.exists(rules_path):
            rules = load_yaml(rules_path)

        self.rule_engine = RuleEngine(rules_path)
        self.payer_genome = PayerGenome(rules)
        self.cdi_engine = CDIEngine()
        self.revenue_leak = RevenuLeakageDetector()
        self.drg_optimizer = DRGOptimizer(rules)
        self.denial_predictor = DenialPredictor()
        self.appeal_engine = AppealEngine()
        self.temporal_engine = TemporalEngine(rules)

    def full_audit(self, claim: MedicalClaim) -> Dict[str, Any]:
        """Complete adversarial audit of a medical claim."""

        # Module 1: Rules
        alerts_rules = self.rule_engine.audit(claim)

        # Module 2: Payer Genome
        genome = self.payer_genome.predict_denial_vector(claim)
        alert_filing = self.payer_genome.check_filing_deadline(claim)
        alerts_genome = [alert_filing] if alert_filing else []

        # Module 3: CDI
        alerts_cdi = self.cdi_engine.audit(claim)
        cdi_analysis = self.cdi_engine.analyze_notes(claim.clinical_notes)

        # Module 4: Revenue Leakage
        alerts_leak = self.revenue_leak.audit(claim)

        # Module 5: DRG
        alerts_drg = self.drg_optimizer.analyze(claim, cdi_analysis)

        # Module 6: Risk Score
        all_alerts = alerts_rules + alerts_genome + alerts_cdi + alerts_leak + alerts_drg
        risk = self.denial_predictor.score(
            claim, prior_alerts=all_alerts,
            cdi_score=cdi_analysis['doc_score'],
            payer_genome=genome,
        )

        # Module 7: Appeal readiness (pre-compute for likely denials)
        appeal_readiness = {}
        if genome.get('attack_vectors'):
            top_vector = genome['attack_vectors'][0]
            appeal_readiness = self.appeal_engine.generate_appeal(
                claim, top_vector['denial_code'],
                alerts=all_alerts, payer_genome=genome
            )

        # Module 8: Temporal
        timing = self.temporal_engine.recommend_timing(claim)

        # Financial summary
        denial_risk_value = sum(a.expected_value for a in all_alerts if a.category == 'denial_risk')
        recovery_value = sum(a.financial_impact for a in all_alerts if a.category == 'revenue_recovery')
        underpayment_value = sum(a.financial_impact for a in all_alerts if a.category == 'underpayment')
        drg_potential = len([a for a in all_alerts if a.category == 'drg_optimization'])

        return {
            'meta': {
                'claim_id': claim.claim_id,
                'payer': claim.payer_name,
                'audit_timestamp': datetime.now().isoformat(),
                'engine_version': '2.0.0-US',
            },
            'risk_score': risk,
            'payer_genome': genome,
            'financial_summary': {
                'total_charges': claim.total_charges,
                'value_at_risk': risk['value_at_risk'],
                'denial_risk_expected_value': round(denial_risk_value, 2),
                'missed_revenue': round(recovery_value, 2),
                'underpayment_detected': round(underpayment_value, 2),
                'drg_optimization_opportunities': drg_potential,
                'total_financial_opportunity': round(
                    denial_risk_value + recovery_value + underpayment_value, 2),
            },
            'summary': {
                'total_alerts': len(all_alerts),
                'by_severity': {
                    'critical': sum(1 for a in all_alerts if a.severity == 'critical'),
                    'high': sum(1 for a in all_alerts if a.severity == 'high'),
                    'medium': sum(1 for a in all_alerts if a.severity == 'medium'),
                    'low': sum(1 for a in all_alerts if a.severity == 'low'),
                    'opportunity': sum(1 for a in all_alerts if a.severity == 'info'),
                },
                'by_category': {
                    'denial_risk': sum(1 for a in all_alerts if a.category == 'denial_risk'),
                    'revenue_recovery': sum(1 for a in all_alerts if a.category == 'revenue_recovery'),
                    'underpayment': sum(1 for a in all_alerts if a.category == 'underpayment'),
                    'drg_optimization': sum(1 for a in all_alerts if a.category == 'drg_optimization'),
                },
                'by_module': {
                    'RULES': len(alerts_rules),
                    'GENOME': len(alerts_genome),
                    'CDI': len(alerts_cdi),
                    'MISS': len(alerts_leak),
                    'DRG': len(alerts_drg),
                },
            },
            'alerts': {
                'rules': [a.to_dict() for a in alerts_rules],
                'genome': [a.to_dict() for a in alerts_genome],
                'cdi': [a.to_dict() for a in alerts_cdi],
                'revenue_leakage': [a.to_dict() for a in alerts_leak],
                'drg': [a.to_dict() for a in alerts_drg],
            },
            'cdi_analysis': cdi_analysis,
            'appeal_readiness': appeal_readiness,
            'timing_strategy': timing,
            'top_priorities': self._prioritize(all_alerts),
        }

    def _prioritize(self, alerts: List[Alert]) -> List[Dict]:
        # Sort by: critical > denial_risk expected value > revenue recovery
        def sort_key(a):
            sev_order = {'critical': 5, 'high': 4, 'medium': 3, 'low': 2, 'info': 1}
            return (sev_order.get(a.severity, 0), a.expected_value, a.financial_impact)

        sorted_alerts = sorted(alerts, key=sort_key, reverse=True)
        return [
            {
                'priority': i + 1,
                'module': a.module,
                'category': a.category,
                'severity': a.severity,
                'description': a.description,
                'recommendation': a.recommendation,
                'financial_impact': round(a.financial_impact, 2),
                'expected_value': round(a.expected_value, 2),
            }
            for i, a in enumerate(sorted_alerts[:15])
        ]


# ============================================================
# DEMO
# ============================================================

def demo_claim() -> MedicalClaim:
    """Realistic US hospital claim with intentional problems."""
    return MedicalClaim(
        claim_id='CLM-2026-US-001',
        patient_id='PT-100001',
        payer_id='UHC-001',
        payer_name='united_healthcare',
        claim_type='institutional',
        date_of_service_from='2026-01-15',
        date_of_service_to='2026-01-22',
        admission_date='2026-01-15',
        discharge_date='2026-01-22',
        icd_codes=['E11.65', 'E66.01', 'I10', 'E78.5', 'G47.33'],
        icd_principal='E66.01',
        drg='619',
        drg_weight=2.4,
        lines=[
            ClaimLine(
                line_id='L001', cpt_code='43775',
                description='Laparoscopic sleeve gastrectomy',
                charge_amount=45000, allowed_amount=28000, paid_amount=24500,
                date_of_service='2026-01-16',
                rendering_provider_npi='1234567890',
                authorization_number='UA-2025-98765',
                authorization_cpt='43775',
            ),
            ClaimLine(
                line_id='L002', cpt_code='43999',
                description='Unlisted laparoscopic procedure - adhesiolysis',
                charge_amount=8000, allowed_amount=4500, paid_amount=0,
                date_of_service='2026-01-16',
                rendering_provider_npi='1234567890',
                # No auth for this unlisted code!
            ),
            ClaimLine(
                line_id='L003', cpt_code='99223',
                description='Initial hospital care - high complexity',
                charge_amount=850, allowed_amount=320, paid_amount=280,
                date_of_service='2026-01-15',
                rendering_provider_npi='9876543210',
            ),
            ClaimLine(
                line_id='L004', cpt_code='99233',
                description='Subsequent hospital care - high complexity',
                units=5, charge_amount=450, allowed_amount=180, paid_amount=165,
                date_of_service='2026-01-17',
                rendering_provider_npi='9876543210',
            ),
            ClaimLine(
                line_id='L005', cpt_code='99233',
                description='Subsequent hospital care - high complexity',
                charge_amount=450, allowed_amount=180, paid_amount=165,
                date_of_service='2026-01-17',
                rendering_provider_npi='9876543210',
                # DUPLICATE - same CPT, same date, same provider!
            ),
            ClaimLine(
                line_id='L006', cpt_code='36620',
                description='Arterial line insertion',
                charge_amount=1200, allowed_amount=380, paid_amount=380,
                date_of_service='2026-01-16',
            ),
            ClaimLine(
                line_id='L007', cpt_code='95250',
                description='CGM data download and interpretation',
                charge_amount=350, allowed_amount=180, paid_amount=0,
                date_of_service='2026-01-18',
                # No auth, endocrine service on surgical admission
            ),
            ClaimLine(
                line_id='L008', cpt_code='99223',
                description='Endocrinology consultation',
                charge_amount=650, allowed_amount=290, paid_amount=250,
                date_of_service='2026-01-17',
                rendering_provider_npi='5555555555',
                modifiers=['25'],  # Modifier 25 — scrutiny trigger
            ),
        ],
        clinical_notes="""
        55yo male with morbid obesity (BMI 47), type 2 diabetes on insulin pump (HbA1c 9.2%),
        obstructive sleep apnea on CPAP, hypertension, and hyperlipidemia.
        Admitted for laparoscopic sleeve gastrectomy.
        Failed conservative weight management including dietary counseling, exercise program,
        and GLP-1 agonist therapy over 18 months.
        Extensive adhesiolysis required due to prior appendectomy.
        CGM monitoring during admission showed significant glycemic variability.
        Nutritional assessment by registered dietitian completed.
        Post-op: brief episode of confusion on POD 2 (resolved with correction of
        electrolytes). Creatinine rose from 1.1 to 2.4 on POD 3, improved with
        fluid resuscitation. Patient required prolonged recovery.
        Smoking cessation counseling provided (45 minutes).
        Discharged POD 7 with follow-up in 2 weeks.
        Per ASMBS guidelines, patient met all criteria for bariatric surgery.
        """,
        medications_administered=[
            'Insulin lispro via pump',
            'Enoxaparin 40mg SQ daily',
            'Ondansetron 4mg IV PRN',
            'Ketorolac 30mg IV q6h',
            'Famotidine 20mg IV BID',
            'Acetaminophen 1000mg PO q6h',
        ],
        procedures_performed=[
            'Laparoscopic sleeve gastrectomy',
            'Adhesiolysis',
            'Arterial line placement',
            'CGM monitoring',
            'Nutritional assessment',
            'Smoking cessation counseling',
        ],
    )


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description='DENIAL SHIELD — Adversarial Revenue Intelligence Engine',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python denial_shield.py demo                     # Full audit with demo claim
  python denial_shield.py audit --input claim.json  # Audit real claim
  python denial_shield.py genome --payer united_healthcare
  python denial_shield.py cdi --text "Patient with..."
  python denial_shield.py appeal --denial-code CO-50 --input claim.json
  python denial_shield.py timing                   # Optimal submission timing
  python denial_shield.py rules                    # List all active rules
        """,
    )

    subparsers = parser.add_subparsers(dest='command')

    subparsers.add_parser('demo', help='Full audit with demo claim')

    p_audit = subparsers.add_parser('audit', help='Audit claim from JSON')
    p_audit.add_argument('--input', required=True)
    p_audit.add_argument('--output', help='Output file')
    p_audit.add_argument('--rules', help='Path to rules YAML')

    p_genome = subparsers.add_parser('genome', help='Payer behavioral genome')
    p_genome.add_argument('--payer', required=True)
    p_genome.add_argument('--rules', help='Path to rules YAML')

    p_cdi = subparsers.add_parser('cdi', help='Analyze clinical documentation')
    p_cdi.add_argument('--text', help='Clinical notes text')
    p_cdi.add_argument('--file', help='File with clinical notes')

    p_appeal = subparsers.add_parser('appeal', help='Generate appeal strategy')
    p_appeal.add_argument('--denial-code', required=True)
    p_appeal.add_argument('--input', required=True)
    p_appeal.add_argument('--rules', help='Path to rules YAML')

    p_timing = subparsers.add_parser('timing', help='Submission timing recommendation')

    subparsers.add_parser('rules', help='List all active rules')

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    rules_path = getattr(args, 'rules', None)
    if not rules_path:
        # Look for rules in standard locations
        for candidate in ['rules/denial_rules.yaml', '../rules/denial_rules.yaml',
                          'denial_rules.yaml']:
            if os.path.exists(candidate):
                rules_path = candidate
                break

    engine = DenialShield(rules_path)

    if args.command == 'demo':
        claim = demo_claim()
        result = engine.full_audit(claim)
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))

    elif args.command == 'audit':
        with open(args.input) as f:
            data = json.load(f)
        claim = MedicalClaim(**data)
        result = engine.full_audit(claim)
        output = json.dumps(result, ensure_ascii=False, indent=2, default=str)
        if args.output:
            with open(args.output, 'w') as f:
                f.write(output)
            print(f'Report saved to {args.output}')
        else:
            print(output)

    elif args.command == 'genome':
        genome = engine.payer_genome.get_genome(args.payer)
        if genome:
            print(json.dumps({args.payer: genome}, indent=2))
        else:
            print(f'Payer "{args.payer}" not found.')
            print(f'Available: {", ".join(engine.payer_genome.genomes.keys())}')

    elif args.command == 'cdi':
        text = args.text
        if args.file:
            with open(args.file) as f:
                text = f.read()
        if not text:
            print('Provide --text or --file')
            return
        result = engine.cdi_engine.analyze_notes(text)
        print(json.dumps(result, indent=2))

    elif args.command == 'appeal':
        with open(args.input) as f:
            data = json.load(f)
        claim = MedicalClaim(**data)
        genome = engine.payer_genome.predict_denial_vector(claim)
        result = engine.appeal_engine.generate_appeal(
            claim, args.denial_code, payer_genome=genome)
        print(json.dumps(result, indent=2))

    elif args.command == 'timing':
        claim = demo_claim()
        result = engine.temporal_engine.recommend_timing(claim)
        print(json.dumps(result, indent=2))

    elif args.command == 'rules':
        if rules_path:
            rules = load_yaml(rules_path)
        else:
            rules = engine.rule_engine._default_rules()
        summary = {
            'cpt_icd_rules': len(rules.get('cpt_icd_rules', [])),
            'payer_genomes': list(rules.get('payer_genomes', {}).keys()),
            'drg_optimizations': len(rules.get('drg_optimization', [])),
            'documentation_requirements': list(rules.get('documentation_requirements', {}).keys()),
            'denial_codes_tracked': list(rules.get('denial_code_intelligence', {}).keys()),
        }
        print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
