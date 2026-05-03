#!/usr/bin/env python3
"""
CONTRACT COMPILER — Reimbursement Kernel
Part of DENIAL SHIELD v3.0 — Revenue Intelligence Platform
Inventor: Dr. Lucas do Prado Palmiro

The missing foundation. Without this, everything else is cosmetic.

A hospital contract with a payer is a 200-page PDF filled with
nested conditional logic: base rates, fee schedules, carve-outs,
stop-losses, outlier provisions, per-diem tiers, case rate bundles,
implant markups, modifier rules, escalators, and exceptions to
exceptions.

The Contract Compiler converts that PDF into executable pricing
logic — a function that takes a claim and returns exactly what
the payer SHOULD pay, down to the penny.

Then the Variance Engine compares expected vs actual and classifies
every dollar of difference by root cause.

This is the "canonical layer of financial truth" that was identified
as the #1 technical weakness.

Architecture:
  ContractModel      — Represents a compiled payer contract
  ReimbursementRule  — Individual pricing rule (fee schedule, DRG, etc.)
  PricingEngine      — Calculates expected reimbursement per claim
  VarianceEngine     — Classifies differences between expected and paid
  RecoveryPrioritizer — Ranks recovery opportunities by ROI
"""

import json
import math
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from collections import defaultdict
from enum import Enum


# ============================================================
# ENUMS
# ============================================================

class PricingMethod(Enum):
    """How a contract prices a service category."""
    FEE_SCHEDULE = "fee_schedule"          # Fixed $ per CPT
    PCT_OF_MEDICARE = "pct_of_medicare"    # X% of Medicare fee schedule
    DRG_BASED = "drg_based"               # Base rate × DRG weight
    PER_DIEM = "per_diem"                 # $ per day, often tiered
    CASE_RATE = "case_rate"               # Flat rate per case/episode
    COST_PLUS = "cost_plus"               # Hospital cost + X% markup
    CARVE_OUT = "carve_out"               # Specific items priced separately
    LESSER_OF = "lesser_of"               # Min(charges, contracted rate)
    PERCENT_OF_CHARGES = "pct_of_charges" # X% of billed charges
    CAPITATION = "capitation"             # Fixed PMPM, not per-claim


class VarianceType(Enum):
    """Root cause classification for payment variance."""
    CORRECT_PAYMENT = "correct_payment"
    WRONG_FEE_SCHEDULE = "wrong_fee_schedule"
    WRONG_DRG = "wrong_drg_assignment"
    BUNDLING_ERROR = "incorrect_bundling"
    MODIFIER_IGNORED = "modifier_not_applied"
    CARVE_OUT_MISSED = "carve_out_not_honored"
    STOP_LOSS_NOT_PAID = "stop_loss_threshold_not_applied"
    OUTLIER_NOT_PAID = "outlier_payment_missing"
    ESCALATOR_NOT_APPLIED = "annual_escalator_missing"
    IMPLANT_UNDERPAID = "implant_markup_not_applied"
    COB_ERROR = "coordination_of_benefits_error"
    TIMELY_PENALTY_OWED = "prompt_pay_penalty_due"
    ZERO_BALANCE_ERROR = "premature_zero_balance"
    PARTIAL_DENIAL_HIDDEN = "medical_necessity_as_underpayment"
    UNKNOWN = "unknown_variance"


# ============================================================
# DATACLASSES
# ============================================================

@dataclass
class MedicareRate:
    """Medicare fee schedule rate for a CPT code."""
    cpt_code: str
    facility_rate: float        # Hospital/facility rate
    non_facility_rate: float    # Office rate
    global_rate: float          # Combined
    rvu_work: float = 0.0
    rvu_pe: float = 0.0
    rvu_mp: float = 0.0
    conversion_factor: float = 33.29  # 2026 CMS CF
    locality: str = '00'       # National
    effective_date: str = '2026-01-01'

    @property
    def total_rvu(self) -> float:
        return self.rvu_work + self.rvu_pe + self.rvu_mp


@dataclass
class ReimbursementRule:
    """Single pricing rule within a contract."""
    rule_id: str
    description: str
    pricing_method: str  # PricingMethod value
    service_category: str  # inpatient, outpatient, emergency, professional, etc.
    cpt_range: Optional[Tuple[int, int]] = None
    revenue_code_range: Optional[Tuple[str, str]] = None
    drg_range: Optional[Tuple[int, int]] = None

    # Fee schedule pricing
    fee_schedule: Dict[str, float] = field(default_factory=dict)  # CPT → $

    # Percent of Medicare
    medicare_pct: float = 1.0  # e.g., 1.15 = 115% of Medicare

    # DRG pricing
    drg_base_rate: float = 0.0
    drg_weights: Dict[str, float] = field(default_factory=dict)  # DRG → weight

    # Per diem
    per_diem_rates: Dict[str, float] = field(default_factory=dict)  # tier → $/day
    per_diem_tiers: List[Dict] = field(default_factory=list)
    # e.g., [{"days": "1-3", "rate": 5000}, {"days": "4-7", "rate": 3500}, {"days": "8+", "rate": 2000}]

    # Case rate
    case_rate: float = 0.0

    # Cost plus
    cost_plus_pct: float = 0.0  # e.g., 0.10 = cost + 10%

    # Carve-outs (items priced separately from base)
    carve_out_categories: List[str] = field(default_factory=list)
    # e.g., ["implants", "blood_products", "high_cost_drugs"]

    # Implant/device pricing
    implant_markup_pct: float = 0.0      # e.g., 0.15 = cost + 15%
    implant_cap: float = 0.0             # max reimbursement per device

    # Modifier adjustments
    modifier_adjustments: Dict[str, float] = field(default_factory=dict)
    # e.g., {"50": 1.5, "80": 0.85, "26": 0.40, "TC": 0.60}

    # Stop loss / outlier
    stop_loss_threshold: float = 0.0     # $ above which stop-loss kicks in
    stop_loss_pct: float = 0.80          # hospital pays X%, payer pays rest
    outlier_threshold_multiple: float = 3.0  # e.g., 3× geometric mean LOS

    # Lesser of
    lesser_of_enabled: bool = True       # min(charges, contracted)

    # Escalator
    escalator_pct: float = 0.0           # annual increase (e.g., 0.03 = 3%)
    escalator_base_date: str = ''        # when escalator starts
    escalator_index: str = ''            # CPI-U, Medicare update, etc.

    # Effective dates
    effective_from: str = ''
    effective_to: str = ''

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ContractModel:
    """Compiled payer contract — executable pricing logic."""
    contract_id: str
    hospital_id: str
    payer_id: str
    payer_name: str
    effective_from: str
    effective_to: str
    rules: List[ReimbursementRule] = field(default_factory=list)
    global_lesser_of: bool = True
    prompt_pay_days: int = 30
    prompt_pay_penalty_pct: float = 0.01  # 1% per month late
    timely_filing_days: int = 90
    appeal_window_days: int = 180
    notes: str = ''

    def get_applicable_rule(self, service_category: str,
                            cpt_code: str = None,
                            drg: str = None) -> Optional[ReimbursementRule]:
        """Find the most specific applicable rule for a service."""
        best_rule = None
        best_specificity = -1

        for rule in self.rules:
            if rule.service_category != service_category:
                continue

            specificity = 0

            # Check CPT range match
            if cpt_code and rule.cpt_range:
                try:
                    cpt_int = int(cpt_code.replace('.', ''))
                    if rule.cpt_range[0] <= cpt_int <= rule.cpt_range[1]:
                        specificity += 2
                    else:
                        continue
                except ValueError:
                    pass

            # Check DRG range match
            if drg and rule.drg_range:
                try:
                    drg_int = int(drg)
                    if rule.drg_range[0] <= drg_int <= rule.drg_range[1]:
                        specificity += 2
                    else:
                        continue
                except ValueError:
                    pass

            # Check fee schedule has specific CPT
            if cpt_code and cpt_code in rule.fee_schedule:
                specificity += 3

            # Default category match
            specificity += 1

            if specificity > best_specificity:
                best_specificity = specificity
                best_rule = rule

        return best_rule

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class VarianceResult:
    """Payment variance analysis result for a single line or claim."""
    line_id: str = ''
    claim_id: str = ''
    cpt_code: str = ''
    description: str = ''
    billed_amount: float = 0.0
    expected_amount: float = 0.0
    paid_amount: float = 0.0
    variance: float = 0.0          # expected - paid (positive = underpaid)
    variance_pct: float = 0.0
    variance_type: str = ''
    root_cause: str = ''
    recoverable: bool = False
    recovery_probability: float = 0.0
    recovery_method: str = ''      # appeal, balance_bill, contract_dispute, renegotiation
    evidence_needed: List[str] = field(default_factory=list)
    deadline: str = ''             # when recovery window closes
    priority_score: float = 0.0    # value × probability × urgency

    @property
    def expected_recovery(self) -> float:
        return self.variance * self.recovery_probability if self.recoverable else 0.0

    def to_dict(self) -> dict:
        d = asdict(self)
        d['expected_recovery'] = round(self.expected_recovery, 2)
        return d


# ============================================================
# MEDICARE FEE SCHEDULE (subset for demo — production loads full CMS file)
# ============================================================

MEDICARE_RATES_2026 = {
    # Surgery
    '43775': MedicareRate('43775', 6842.00, 0, 6842.00, 32.17, 48.92, 4.81),   # Sleeve gastrectomy
    '43644': MedicareRate('43644', 7520.00, 0, 7520.00, 35.33, 53.71, 5.28),   # Gastric bypass
    '27447': MedicareRate('27447', 5480.00, 0, 5480.00, 25.74, 39.14, 3.85),   # Total knee
    '27130': MedicareRate('27130', 5920.00, 0, 5920.00, 27.81, 42.29, 4.16),   # Total hip
    # E&M
    '99223': MedicareRate('99223', 316.00, 316.00, 316.00, 3.86, 4.28, 0.37),  # Initial hosp high
    '99233': MedicareRate('99233', 178.00, 178.00, 178.00, 2.00, 2.44, 0.21),  # Subsequent high
    '99291': MedicareRate('99291', 452.00, 452.00, 452.00, 4.50, 5.80, 0.48),  # Critical care 1st hr
    '99292': MedicareRate('99292', 218.00, 218.00, 218.00, 2.20, 2.80, 0.23),  # Critical care addl
    # Procedures
    '36620': MedicareRate('36620', 380.00, 280.00, 380.00, 1.80, 2.70, 0.27),  # Arterial line
    '95250': MedicareRate('95250', 175.00, 175.00, 175.00, 0.90, 1.40, 0.12),  # CGM download
    # Consults
    '99254': MedicareRate('99254', 286.00, 286.00, 286.00, 3.50, 3.90, 0.34),  # Inpt consult high
    '99255': MedicareRate('99255', 356.00, 356.00, 356.00, 4.38, 4.84, 0.42),  # Inpt consult highest
}

# DRG weights (subset — production loads full MS-DRG table)
DRG_WEIGHTS_2026 = {
    '619': {'description': 'O.R. procedures for obesity w/o CC/MCC', 'weight': 2.0431, 'gmlos': 2.1, 'amlos': 2.8},
    '620': {'description': 'O.R. procedures for obesity w CC', 'weight': 2.4192, 'gmlos': 3.0, 'amlos': 4.1},
    '621': {'description': 'O.R. procedures for obesity w MCC', 'weight': 3.1847, 'gmlos': 4.5, 'amlos': 6.8},
    '470': {'description': 'Major hip/knee joint replacement w/o MCC', 'weight': 1.7394, 'gmlos': 2.0, 'amlos': 3.0},
    '469': {'description': 'Major hip/knee joint replacement w MCC', 'weight': 2.8176, 'gmlos': 4.5, 'amlos': 7.2},
    '871': {'description': 'Sepsis w/o MV >96 hours w MCC', 'weight': 1.8878, 'gmlos': 5.4, 'amlos': 7.2},
    '872': {'description': 'Sepsis w/o MV >96 hours w/o MCC', 'weight': 1.1892, 'gmlos': 3.6, 'amlos': 4.7},
    '193': {'description': 'Simple pneumonia & pleurisy w MCC', 'weight': 1.1738, 'gmlos': 4.4, 'amlos': 5.6},
    '194': {'description': 'Simple pneumonia & pleurisy w CC', 'weight': 0.8270, 'gmlos': 3.2, 'amlos': 4.0},
    '195': {'description': 'Simple pneumonia & pleurisy w/o CC/MCC', 'weight': 0.6072, 'gmlos': 2.4, 'amlos': 3.0},
    '682': {'description': 'Renal failure w MCC', 'weight': 1.4590, 'gmlos': 4.3, 'amlos': 5.6},
}


# ============================================================
# PRICING ENGINE
# ============================================================

class PricingEngine:
    """Calculates expected reimbursement from compiled contract.

    This is the "canonical layer of financial truth."
    Every dollar the hospital expects to receive flows through here.
    """

    def __init__(self, contract: ContractModel,
                 medicare_rates: Dict[str, MedicareRate] = None,
                 drg_weights: Dict[str, dict] = None):
        self.contract = contract
        self.medicare = medicare_rates or MEDICARE_RATES_2026
        self.drg_weights = drg_weights or DRG_WEIGHTS_2026

    def price_line(self, cpt_code: str, charge_amount: float,
                   service_category: str = 'outpatient',
                   modifiers: List[str] = None,
                   units: int = 1,
                   cost: float = 0.0) -> Dict[str, Any]:
        """Calculate expected reimbursement for a single line item."""

        rule = self.contract.get_applicable_rule(service_category, cpt_code=cpt_code)
        if not rule:
            return {
                'cpt_code': cpt_code,
                'method': 'no_rule_found',
                'expected': 0.0,
                'explanation': f'No contract rule found for {cpt_code} in {service_category}',
            }

        method = rule.pricing_method
        expected = 0.0
        explanation = ''

        if method == PricingMethod.FEE_SCHEDULE.value:
            rate = rule.fee_schedule.get(cpt_code, 0.0)
            expected = rate * units
            explanation = f'Fee schedule: ${rate:.2f} × {units} units'

        elif method == PricingMethod.PCT_OF_MEDICARE.value:
            medicare_rate = self.medicare.get(cpt_code)
            if medicare_rate:
                base = medicare_rate.facility_rate
                expected = base * rule.medicare_pct * units
                explanation = (f'{rule.medicare_pct:.0%} of Medicare '
                               f'(${base:.2f} × {rule.medicare_pct} × {units})')
            else:
                expected = charge_amount * 0.5  # fallback estimate
                explanation = f'Medicare rate not found — estimated at 50% of charges'

        elif method == PricingMethod.CASE_RATE.value:
            expected = rule.case_rate
            explanation = f'Case rate: ${rule.case_rate:,.2f}'

        elif method == PricingMethod.COST_PLUS.value:
            if cost > 0:
                expected = cost * (1 + rule.cost_plus_pct)
                explanation = f'Cost + {rule.cost_plus_pct:.0%}: ${cost:.2f} × {1+rule.cost_plus_pct:.2f}'
            else:
                expected = charge_amount * 0.6  # fallback
                explanation = 'Cost plus — cost not provided, estimated'

        elif method == PricingMethod.PERCENT_OF_CHARGES.value:
            pct = rule.medicare_pct  # reusing field for charge pct
            expected = charge_amount * pct
            explanation = f'{pct:.0%} of charges: ${charge_amount:,.2f} × {pct}'

        elif method == PricingMethod.CARVE_OUT.value:
            if cost > 0 and rule.implant_markup_pct > 0:
                expected = cost * (1 + rule.implant_markup_pct)
                if rule.implant_cap > 0:
                    expected = min(expected, rule.implant_cap)
                explanation = (f'Carve-out: cost ${cost:,.2f} + '
                               f'{rule.implant_markup_pct:.0%} markup'
                               f'{f" (capped at ${rule.implant_cap:,.0f})" if rule.implant_cap else ""}')
            else:
                expected = charge_amount * 0.7
                explanation = 'Carve-out — cost not provided, estimated'

        # Apply modifier adjustments
        if modifiers and rule.modifier_adjustments:
            for mod in modifiers:
                if mod in rule.modifier_adjustments:
                    factor = rule.modifier_adjustments[mod]
                    expected *= factor
                    explanation += f' | Modifier {mod}: ×{factor}'

        # Apply lesser-of
        if rule.lesser_of_enabled or self.contract.global_lesser_of:
            if expected > charge_amount:
                explanation += f' | Lesser-of applied (charges ${charge_amount:,.2f} < expected)'
                expected = charge_amount

        # Apply escalator
        if rule.escalator_pct > 0 and rule.escalator_base_date:
            years = self._years_since(rule.escalator_base_date)
            if years > 0:
                factor = (1 + rule.escalator_pct) ** years
                expected *= factor
                explanation += f' | Escalator: {rule.escalator_pct:.1%}/yr × {years}yr = ×{factor:.3f}'

        return {
            'cpt_code': cpt_code,
            'method': method,
            'rule_id': rule.rule_id,
            'expected': round(expected, 2),
            'charge_amount': charge_amount,
            'units': units,
            'explanation': explanation,
        }

    def price_inpatient(self, drg: str, charge_amount: float,
                        los: int = 1) -> Dict[str, Any]:
        """Calculate expected reimbursement for inpatient DRG-based claim."""
        rule = self.contract.get_applicable_rule('inpatient', drg=drg)
        if not rule:
            return {
                'drg': drg, 'method': 'no_rule_found',
                'expected': 0.0,
                'explanation': 'No inpatient rule found'
            }

        method = rule.pricing_method
        expected = 0.0
        explanation = ''

        if method == PricingMethod.DRG_BASED.value:
            drg_info = self.drg_weights.get(drg, {})
            weight = rule.drg_weights.get(drg, drg_info.get('weight', 1.0))
            base = rule.drg_base_rate
            expected = base * weight
            explanation = f'DRG {drg}: base ${base:,.2f} × weight {weight:.4f}'

            # Outlier check
            gmlos = drg_info.get('gmlos', 3.0)
            if los > gmlos * rule.outlier_threshold_multiple:
                outlier_days = los - gmlos
                outlier_per_day = base * 0.15  # typical outlier per diem
                outlier_payment = outlier_days * outlier_per_day
                expected += outlier_payment
                explanation += (f' | OUTLIER: {outlier_days:.0f} excess days × '
                                f'${outlier_per_day:,.0f}/day = +${outlier_payment:,.0f}')

        elif method == PricingMethod.PER_DIEM.value:
            if rule.per_diem_tiers:
                expected = self._calculate_tiered_per_diem(rule.per_diem_tiers, los)
                explanation = f'Per diem tiered: {los} days'
            else:
                rate = list(rule.per_diem_rates.values())[0] if rule.per_diem_rates else 2500
                expected = rate * los
                explanation = f'Per diem flat: ${rate:,.2f} × {los} days'

        elif method == PricingMethod.CASE_RATE.value:
            expected = rule.case_rate
            explanation = f'Case rate: ${rule.case_rate:,.2f}'

        elif method == PricingMethod.PCT_OF_CHARGES.value:
            pct = rule.medicare_pct
            expected = charge_amount * pct
            explanation = f'{pct:.0%} of charges'

        # Stop-loss
        if rule.stop_loss_threshold > 0 and charge_amount > rule.stop_loss_threshold:
            excess = charge_amount - rule.stop_loss_threshold
            stop_loss_payment = excess * rule.stop_loss_pct
            if expected < rule.stop_loss_threshold + stop_loss_payment:
                expected = rule.stop_loss_threshold + stop_loss_payment
                explanation += (f' | STOP-LOSS at ${rule.stop_loss_threshold:,.0f}: '
                                f'{rule.stop_loss_pct:.0%} of ${excess:,.0f} excess')

        # Lesser of
        if self.contract.global_lesser_of and expected > charge_amount:
            expected = charge_amount
            explanation += ' | Lesser-of applied'

        # Escalator
        if rule.escalator_pct > 0 and rule.escalator_base_date:
            years = self._years_since(rule.escalator_base_date)
            if years > 0:
                factor = (1 + rule.escalator_pct) ** years
                expected *= factor
                explanation += f' | Escalator ×{factor:.3f}'

        return {
            'drg': drg,
            'method': method,
            'rule_id': rule.rule_id,
            'expected': round(expected, 2),
            'charge_amount': charge_amount,
            'los': los,
            'explanation': explanation,
        }

    def _calculate_tiered_per_diem(self, tiers: List[Dict], los: int) -> float:
        """Calculate per diem with tiered rates."""
        total = 0.0
        days_remaining = los

        for tier in sorted(tiers, key=lambda t: int(t.get('days', '1').split('-')[0])):
            days_spec = tier['days']
            rate = tier['rate']

            if '+' in days_spec:
                # "8+" — all remaining days
                total += days_remaining * rate
                break
            elif '-' in days_spec:
                start, end = map(int, days_spec.split('-'))
                tier_days = min(days_remaining, end - start + 1)
                total += tier_days * rate
                days_remaining -= tier_days
            else:
                # Single day
                if days_remaining > 0:
                    total += rate
                    days_remaining -= 1

            if days_remaining <= 0:
                break

        return total

    def _years_since(self, date_str: str) -> float:
        try:
            base = datetime.strptime(date_str, '%Y-%m-%d')
            return (datetime.now() - base).days / 365.25
        except:
            return 0.0


# ============================================================
# VARIANCE ENGINE
# ============================================================

class VarianceEngine:
    """Classifies every dollar of difference by root cause.

    This is where the system transitions from "detecting problems"
    to "liquidating claims." Each variance gets a root cause,
    recovery probability, optimal recovery method, and deadline.
    """

    def __init__(self, contract: ContractModel, pricing: PricingEngine):
        self.contract = contract
        self.pricing = pricing

    def analyze_line(self, cpt_code: str, charge_amount: float,
                     paid_amount: float, allowed_amount: float = 0.0,
                     service_category: str = 'outpatient',
                     modifiers: List[str] = None,
                     units: int = 1, cost: float = 0.0,
                     line_id: str = '', description: str = '',
                     date_of_service: str = '',
                     carc_codes: List[str] = None) -> VarianceResult:
        """Analyze a single line item for payment variance."""

        # Calculate expected
        pricing = self.pricing.price_line(
            cpt_code, charge_amount, service_category,
            modifiers, units, cost)
        expected = pricing['expected']

        # Calculate variance
        actual = paid_amount
        if actual <= 0 and allowed_amount > 0:
            actual = allowed_amount  # use allowed if no payment yet

        variance = expected - actual
        variance_pct = (variance / expected * 100) if expected > 0 else 0

        # Classify variance
        vtype, root_cause, recoverable, recovery_prob, recovery_method = \
            self._classify_variance(
                expected, actual, charge_amount, allowed_amount,
                cpt_code, modifiers, carc_codes, pricing)

        # Calculate deadline
        deadline = self._calculate_deadline(date_of_service)

        # Evidence needed
        evidence = self._evidence_checklist(vtype, root_cause)

        # Priority score: value × probability × urgency
        days_left = 0
        try:
            dl = datetime.strptime(deadline, '%Y-%m-%d')
            days_left = max(1, (dl - datetime.now()).days)
        except:
            days_left = 180

        urgency = max(0.1, 1.0 - (days_left / 365))
        priority = abs(variance) * recovery_prob * urgency

        return VarianceResult(
            line_id=line_id,
            cpt_code=cpt_code,
            description=description,
            billed_amount=charge_amount,
            expected_amount=expected,
            paid_amount=paid_amount,
            variance=round(variance, 2),
            variance_pct=round(variance_pct, 2),
            variance_type=vtype,
            root_cause=root_cause,
            recoverable=recoverable,
            recovery_probability=round(recovery_prob, 3),
            recovery_method=recovery_method,
            evidence_needed=evidence,
            deadline=deadline,
            priority_score=round(priority, 2),
        )

    def analyze_inpatient(self, drg: str, charge_amount: float,
                          paid_amount: float, los: int = 1,
                          claim_id: str = '',
                          date_of_service: str = '') -> VarianceResult:
        """Analyze inpatient DRG-based payment variance."""
        pricing = self.pricing.price_inpatient(drg, charge_amount, los)
        expected = pricing['expected']
        variance = expected - paid_amount
        variance_pct = (variance / expected * 100) if expected > 0 else 0

        # DRG-specific classification
        if abs(variance) < 50:
            vtype = VarianceType.CORRECT_PAYMENT.value
            root_cause = 'Payment matches expected DRG reimbursement'
            recoverable = False
            recovery_prob = 0.0
            method = ''
        elif variance > 0:
            # Underpaid
            if variance > expected * 0.3:
                vtype = VarianceType.WRONG_DRG.value
                root_cause = f'Possible DRG downgrade. Expected DRG {drg} payment not matched.'
                recoverable = True
                recovery_prob = 0.55
                method = 'contract_dispute'
            elif 'STOP-LOSS' in pricing.get('explanation', ''):
                vtype = VarianceType.STOP_LOSS_NOT_PAID.value
                root_cause = 'Stop-loss threshold reached but excess not paid'
                recoverable = True
                recovery_prob = 0.70
                method = 'contract_dispute'
            elif 'OUTLIER' in pricing.get('explanation', ''):
                vtype = VarianceType.OUTLIER_NOT_PAID.value
                root_cause = 'Outlier days qualify for additional payment'
                recoverable = True
                recovery_prob = 0.60
                method = 'appeal'
            elif 'Escalator' in pricing.get('explanation', ''):
                vtype = VarianceType.ESCALATOR_NOT_APPLIED.value
                root_cause = 'Annual escalator not reflected in payment'
                recoverable = True
                recovery_prob = 0.80
                method = 'contract_dispute'
            else:
                vtype = VarianceType.WRONG_FEE_SCHEDULE.value
                root_cause = 'Payment below contracted DRG rate'
                recoverable = True
                recovery_prob = 0.65
                method = 'balance_bill'
        else:
            vtype = VarianceType.CORRECT_PAYMENT.value
            root_cause = 'Overpayment or lesser-of applied'
            recoverable = False
            recovery_prob = 0.0
            method = ''

        deadline = self._calculate_deadline(date_of_service)
        evidence = self._evidence_checklist(vtype, root_cause)

        return VarianceResult(
            claim_id=claim_id,
            cpt_code=f'DRG-{drg}',
            description=pricing.get('explanation', ''),
            billed_amount=charge_amount,
            expected_amount=expected,
            paid_amount=paid_amount,
            variance=round(variance, 2),
            variance_pct=round(variance_pct, 2),
            variance_type=vtype,
            root_cause=root_cause,
            recoverable=recoverable,
            recovery_probability=round(recovery_prob, 3),
            recovery_method=method,
            evidence_needed=evidence,
            deadline=deadline,
        )

    def _classify_variance(self, expected: float, actual: float,
                           charge: float, allowed: float,
                           cpt: str, modifiers: List[str],
                           carcs: List[str], pricing: dict
                           ) -> Tuple[str, str, bool, float, str]:
        """Classify variance by root cause with recovery parameters."""

        variance = expected - actual

        if abs(variance) < 1.0:
            return (VarianceType.CORRECT_PAYMENT.value,
                    'Payment matches contract', False, 0.0, '')

        if actual <= 0:
            # Full denial — different from underpayment
            return (VarianceType.PARTIAL_DENIAL_HIDDEN.value,
                    'Zero payment — may be denial disguised as adjudication',
                    True, 0.45, 'appeal')

        if variance < 0:
            # Overpayment — flag but don't pursue (payer may recoup)
            return (VarianceType.CORRECT_PAYMENT.value,
                    f'Overpayment of ${abs(variance):.2f} — monitor for recoupment',
                    False, 0.0, '')

        # Underpayment analysis
        pct = (variance / expected) if expected > 0 else 0

        # Check for modifier issues
        if modifiers and pct > 0.1:
            explanation = pricing.get('explanation', '')
            if 'Modifier' not in explanation:
                return (VarianceType.MODIFIER_IGNORED.value,
                        f'Modifier {", ".join(modifiers)} may not have been applied',
                        True, 0.65, 'appeal')

        # Check for escalator
        if 'Escalator' in pricing.get('explanation', ''):
            return (VarianceType.ESCALATOR_NOT_APPLIED.value,
                    'Annual rate escalator not reflected in payment',
                    True, 0.80, 'contract_dispute')

        # General underpayment
        if pct > 0.25:
            return (VarianceType.WRONG_FEE_SCHEDULE.value,
                    f'Significant underpayment: {pct:.0%} below contracted rate',
                    True, 0.60, 'contract_dispute')
        elif pct > 0.05:
            return (VarianceType.WRONG_FEE_SCHEDULE.value,
                    f'Moderate underpayment: {pct:.0%} below contracted rate',
                    True, 0.55, 'balance_bill')
        else:
            return (VarianceType.CORRECT_PAYMENT.value,
                    f'Minor variance: {pct:.1%} — within tolerance',
                    False, 0.0, '')

    def _calculate_deadline(self, dos: str) -> str:
        """Calculate recovery deadline based on contract terms."""
        try:
            dt = datetime.strptime(dos, '%Y-%m-%d')
            deadline = dt + timedelta(days=self.contract.appeal_window_days)
            return deadline.strftime('%Y-%m-%d')
        except:
            return (datetime.now() + timedelta(days=180)).strftime('%Y-%m-%d')

    def _evidence_checklist(self, vtype: str, root_cause: str) -> List[str]:
        """Evidence needed for recovery based on variance type."""
        checklists = {
            VarianceType.WRONG_FEE_SCHEDULE.value: [
                'Contract fee schedule exhibit (relevant section)',
                'Remittance advice (835/EOB) showing paid amount',
                'Claim submission record (837)',
            ],
            VarianceType.WRONG_DRG.value: [
                'DRG assignment worksheet',
                'Clinical documentation supporting DRG',
                'Contract DRG rate table',
            ],
            VarianceType.MODIFIER_IGNORED.value: [
                'Operative report documenting distinct services',
                'Medical record supporting modifier use',
                'CCI edit reference showing modifier override',
            ],
            VarianceType.ESCALATOR_NOT_APPLIED.value: [
                'Contract escalator clause (with effective date)',
                'CPI-U or relevant index data',
                'Prior year payment records showing old rate',
            ],
            VarianceType.STOP_LOSS_NOT_PAID.value: [
                'Contract stop-loss/outlier provision',
                'Itemized bill showing total charges above threshold',
                'Clinical justification for extended stay/services',
            ],
            VarianceType.IMPLANT_UNDERPAID.value: [
                'Invoice/cost documentation for device',
                'Contract carve-out/implant provision',
                'FDA clearance documentation',
            ],
        }
        return checklists.get(vtype, [
            'Contract terms for applicable service',
            'Remittance/EOB',
            'Supporting clinical documentation',
        ])


# ============================================================
# RECOVERY PRIORITIZER
# ============================================================

class RecoveryPrioritizer:
    """Ranks recovery opportunities by ROI.

    Not all underpayments are worth pursuing. A $50 variance
    with 30% recovery probability costs more to pursue than
    the expected return. A $5,000 variance with 80% probability
    and 30 days until deadline is urgent.

    The prioritizer factors: value, probability, urgency, and
    operational cost (estimated staff time to pursue).
    """

    COST_PER_RECOVERY_ACTION = {
        'appeal': 118.0,           # Average cost to work an appeal
        'balance_bill': 45.0,      # Cost to generate and send balance bill
        'contract_dispute': 250.0, # Cost for formal contract dispute
        'renegotiation': 0.0,      # No per-claim cost (batch process)
    }

    def prioritize(self, variances: List[VarianceResult]) -> List[Dict[str, Any]]:
        """Rank recovery opportunities by net expected value."""
        opportunities = []

        for v in variances:
            if not v.recoverable or v.variance <= 0:
                continue

            cost = self.COST_PER_RECOVERY_ACTION.get(v.recovery_method, 100.0)
            gross_expected = v.variance * v.recovery_probability
            net_expected = gross_expected - cost

            if net_expected <= 0:
                continue  # Not worth pursuing

            # Calculate urgency
            days_left = 180
            try:
                dl = datetime.strptime(v.deadline, '%Y-%m-%d')
                days_left = max(1, (dl - datetime.now()).days)
            except:
                pass

            urgency = 'critical' if days_left < 30 else \
                      'high' if days_left < 60 else \
                      'medium' if days_left < 120 else 'low'

            # ROI
            roi = (net_expected / cost) if cost > 0 else float('inf')

            opportunities.append({
                'line_id': v.line_id or v.claim_id,
                'cpt_code': v.cpt_code,
                'variance': v.variance,
                'variance_type': v.variance_type,
                'recovery_method': v.recovery_method,
                'recovery_probability': v.recovery_probability,
                'gross_expected_recovery': round(gross_expected, 2),
                'cost_to_pursue': cost,
                'net_expected_recovery': round(net_expected, 2),
                'roi': round(roi, 2),
                'deadline': v.deadline,
                'days_remaining': days_left,
                'urgency': urgency,
                'evidence_needed': v.evidence_needed,
            })

        # Sort by net expected recovery (highest first), then urgency
        urgency_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        opportunities.sort(
            key=lambda x: (-x['net_expected_recovery'],
                           urgency_order.get(x['urgency'], 4)))

        return opportunities

    def summary(self, opportunities: List[Dict]) -> Dict[str, Any]:
        """Aggregate recovery summary."""
        if not opportunities:
            return {'total_opportunities': 0, 'total_recoverable': 0}

        total_variance = sum(o['variance'] for o in opportunities)
        total_gross = sum(o['gross_expected_recovery'] for o in opportunities)
        total_cost = sum(o['cost_to_pursue'] for o in opportunities)
        total_net = sum(o['net_expected_recovery'] for o in opportunities)

        by_method = defaultdict(lambda: {'count': 0, 'value': 0, 'net': 0})
        for o in opportunities:
            m = o['recovery_method']
            by_method[m]['count'] += 1
            by_method[m]['value'] += o['variance']
            by_method[m]['net'] += o['net_expected_recovery']

        by_urgency = defaultdict(lambda: {'count': 0, 'value': 0})
        for o in opportunities:
            u = o['urgency']
            by_urgency[u]['count'] += 1
            by_urgency[u]['value'] += o['variance']

        return {
            'total_opportunities': len(opportunities),
            'total_variance': round(total_variance, 2),
            'total_gross_recovery': round(total_gross, 2),
            'total_cost_to_pursue': round(total_cost, 2),
            'total_net_recovery': round(total_net, 2),
            'aggregate_roi': round(total_net / total_cost, 2) if total_cost > 0 else 0,
            'by_recovery_method': dict(by_method),
            'by_urgency': dict(by_urgency),
        }


# ============================================================
# DEMO CONTRACT
# ============================================================

def demo_contract() -> ContractModel:
    """Realistic hospital-UHC contract for demo."""
    return ContractModel(
        contract_id='CTR-UHC-2025-001',
        hospital_id='HOSP-EINSTEIN-001',
        payer_id='UHC-001',
        payer_name='United Healthcare',
        effective_from='2025-01-01',
        effective_to='2027-12-31',
        prompt_pay_days=30,
        prompt_pay_penalty_pct=0.01,
        timely_filing_days=90,
        appeal_window_days=180,
        rules=[
            # Inpatient: DRG-based at 120% of Medicare
            ReimbursementRule(
                rule_id='IP-DRG-001',
                description='Inpatient DRG — 120% of Medicare base rate',
                pricing_method=PricingMethod.DRG_BASED.value,
                service_category='inpatient',
                drg_base_rate=7200.00,  # Hospital-specific base rate
                drg_weights={},  # Uses standard CMS weights
                stop_loss_threshold=150000,
                stop_loss_pct=0.80,
                outlier_threshold_multiple=3.0,
                escalator_pct=0.025,
                escalator_base_date='2025-01-01',
                escalator_index='CPI-U + 0.5%',
                lesser_of_enabled=True,
            ),
            # Outpatient surgery: 130% of Medicare
            ReimbursementRule(
                rule_id='OP-SURG-001',
                description='Outpatient surgery — 130% of Medicare',
                pricing_method=PricingMethod.PCT_OF_MEDICARE.value,
                service_category='outpatient',
                cpt_range=(10000, 69999),
                medicare_pct=1.30,
                modifier_adjustments={
                    '50': 1.50, '80': 0.85, '26': 0.40, 'TC': 0.60,
                    '59': 1.0, 'XE': 1.0, 'XS': 1.0,
                },
                escalator_pct=0.03,
                escalator_base_date='2025-01-01',
            ),
            # E&M: 140% of Medicare
            ReimbursementRule(
                rule_id='EM-001',
                description='E&M services — 140% of Medicare',
                pricing_method=PricingMethod.PCT_OF_MEDICARE.value,
                service_category='professional',
                cpt_range=(99201, 99499),
                medicare_pct=1.40,
                escalator_pct=0.025,
                escalator_base_date='2025-01-01',
            ),
            # Implants: Cost + 15%, cap $25K
            ReimbursementRule(
                rule_id='IMPL-001',
                description='Implants/devices — cost + 15%, cap $25K',
                pricing_method=PricingMethod.CARVE_OUT.value,
                service_category='implant',
                implant_markup_pct=0.15,
                implant_cap=25000,
                carve_out_categories=['implants', 'devices'],
            ),
            # Lab: 110% of Medicare
            ReimbursementRule(
                rule_id='LAB-001',
                description='Laboratory — 110% of Medicare',
                pricing_method=PricingMethod.PCT_OF_MEDICARE.value,
                service_category='laboratory',
                cpt_range=(80000, 89999),
                medicare_pct=1.10,
            ),
            # Procedures: 125% of Medicare
            ReimbursementRule(
                rule_id='PROC-001',
                description='Procedures — 125% of Medicare',
                pricing_method=PricingMethod.PCT_OF_MEDICARE.value,
                service_category='outpatient',
                cpt_range=(90000, 99199),
                medicare_pct=1.25,
            ),
        ],
    )


def demo_variance_analysis():
    """Run variance analysis on demo claim vs demo contract."""
    contract = demo_contract()
    pricing = PricingEngine(contract)
    variance = VarianceEngine(contract, pricing)
    prioritizer = RecoveryPrioritizer()

    # Simulate line items with actual payments (some underpaid)
    lines = [
        {'cpt': '43775', 'charge': 45000, 'paid': 7800, 'allowed': 8895,
         'category': 'outpatient', 'modifiers': [], 'units': 1,
         'line_id': 'L001', 'desc': 'Lap sleeve gastrectomy',
         'dos': '2026-01-16'},
        {'cpt': '99223', 'charge': 850, 'paid': 280, 'allowed': 320,
         'category': 'professional', 'modifiers': [], 'units': 1,
         'line_id': 'L003', 'desc': 'Initial hospital care high',
         'dos': '2026-01-15'},
        {'cpt': '99233', 'charge': 450, 'paid': 165, 'allowed': 180,
         'category': 'professional', 'modifiers': [], 'units': 1,
         'line_id': 'L004', 'desc': 'Subsequent hosp care high',
         'dos': '2026-01-17'},
        {'cpt': '36620', 'charge': 1200, 'paid': 380, 'allowed': 380,
         'category': 'outpatient', 'modifiers': [], 'units': 1,
         'line_id': 'L006', 'desc': 'Arterial line insertion',
         'dos': '2026-01-16'},
        {'cpt': '95250', 'charge': 350, 'paid': 0, 'allowed': 180,
         'category': 'outpatient', 'modifiers': [], 'units': 1,
         'line_id': 'L007', 'desc': 'CGM download/interpretation',
         'dos': '2026-01-18'},
        {'cpt': '99223', 'charge': 650, 'paid': 250, 'allowed': 290,
         'category': 'professional', 'modifiers': ['25'], 'units': 1,
         'line_id': 'L008', 'desc': 'Endocrinology consult',
         'dos': '2026-01-17'},
    ]

    # Inpatient DRG
    drg_result = variance.analyze_inpatient(
        drg='619', charge_amount=58750, paid_amount=13500,
        los=7, claim_id='CLM-2026-US-001', date_of_service='2026-01-15')

    # Line-level analysis
    line_results = []
    for line in lines:
        result = variance.analyze_line(
            cpt_code=line['cpt'],
            charge_amount=line['charge'],
            paid_amount=line['paid'],
            allowed_amount=line['allowed'],
            service_category=line['category'],
            modifiers=line.get('modifiers', []),
            units=line.get('units', 1),
            line_id=line['line_id'],
            description=line['desc'],
            date_of_service=line['dos'],
        )
        line_results.append(result)

    # Prioritize recovery
    all_results = [drg_result] + line_results
    opportunities = prioritizer.prioritize(all_results)
    summary = prioritizer.summary(opportunities)

    return {
        'contract': {
            'id': contract.contract_id,
            'payer': contract.payer_name,
            'effective': f'{contract.effective_from} to {contract.effective_to}',
        },
        'drg_analysis': drg_result.to_dict(),
        'line_analysis': [r.to_dict() for r in line_results],
        'recovery_opportunities': opportunities,
        'recovery_summary': summary,
    }


# ============================================================
# CLI
# ============================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='CONTRACT COMPILER — Reimbursement Kernel')
    subparsers = parser.add_subparsers(dest='command')

    subparsers.add_parser('demo', help='Full variance analysis with demo data')

    p_price = subparsers.add_parser('price', help='Price a single CPT code')
    p_price.add_argument('--cpt', required=True)
    p_price.add_argument('--charge', type=float, required=True)
    p_price.add_argument('--category', default='outpatient')

    p_drg = subparsers.add_parser('drg', help='Price inpatient DRG')
    p_drg.add_argument('--drg', required=True)
    p_drg.add_argument('--charge', type=float, required=True)
    p_drg.add_argument('--los', type=int, default=3)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == 'demo':
        result = demo_variance_analysis()
        print(json.dumps(result, indent=2, default=str))

    elif args.command == 'price':
        contract = demo_contract()
        engine = PricingEngine(contract)
        result = engine.price_line(
            args.cpt, args.charge, args.category)
        print(json.dumps(result, indent=2))

    elif args.command == 'drg':
        contract = demo_contract()
        engine = PricingEngine(contract)
        result = engine.price_inpatient(args.drg, args.charge, args.los)
        print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
