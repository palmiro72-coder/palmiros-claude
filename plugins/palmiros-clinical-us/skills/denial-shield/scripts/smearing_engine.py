#!/usr/bin/env python3
"""
SMEARING ENGINE — Systematic Variance Detection
Part of DENIAL SHIELD v4.0 — Revenue Intelligence Platform
Inventor: Dr. Lucas do Prado Palmiro

The most dangerous payer tactic isn't a $50K denial.
It's 10,000 claims each underpaid by $5-50 — hidden inside
normal adjudication flow, below the threshold of human reaction.

"Denial hurts. Underpayment FEELS like flow."

The Smearing Engine detects what no human auditor can:
statistical drift in payment patterns that reveals SYSTEMATIC
underpayment — not errors, but strategy.

Architecture:
  PaymentStream     — Time-series of payments by payer × service family
  DriftDetector     — Statistical change-point detection on allowed amounts
  SmearingAnalyzer  — Aggregates micro-variances into material patterns
  ZeroBalanceHunter — Reopens "closed" accounts with contractual variance
  BundlingRadar     — Detects opaque/proprietary bundling not matching CCI
  RecoveryBatch     — Groups micro-variances into batch recovery actions

Key insight: the signal is NOT "this claim was underpaid."
The signal is: "in this payer × service family × window, the mean
delta shifted -3.8% over 9 weeks with no valid contract change."
"""

import json
import math
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from collections import defaultdict
from enum import Enum


# ============================================================
# DATACLASSES
# ============================================================

@dataclass
class PaymentObservation:
    """Single payment observation for time-series analysis."""
    claim_id: str
    payer_id: str
    payer_name: str
    service_family: str        # E&M, surgery, imaging, lab, DME, etc.
    cpt_code: str
    drg: str = ''
    modifier: str = ''
    specialty: str = ''
    facility_id: str = ''
    date_of_service: str = ''
    date_paid: str = ''
    billed_amount: float = 0.0
    expected_amount: float = 0.0  # From Contract Compiler
    allowed_amount: float = 0.0   # What payer says is allowed
    paid_amount: float = 0.0      # What payer actually paid
    carc_codes: List[str] = field(default_factory=list)
    rarc_codes: List[str] = field(default_factory=list)
    account_status: str = ''      # open, closed, zero_balance
    adjustment_reason: str = ''

    @property
    def variance_vs_expected(self) -> float:
        """Difference between contract-expected and actual paid."""
        return self.expected_amount - self.paid_amount

    @property
    def variance_pct(self) -> float:
        if self.expected_amount > 0:
            return (self.variance_vs_expected / self.expected_amount) * 100
        return 0.0

    @property
    def allowed_vs_expected(self) -> float:
        """Difference between allowed (payer's number) and expected (contract)."""
        return self.expected_amount - self.allowed_amount

    def to_dict(self) -> dict:
        d = asdict(self)
        d['variance_vs_expected'] = round(self.variance_vs_expected, 2)
        d['variance_pct'] = round(self.variance_pct, 2)
        d['allowed_vs_expected'] = round(self.allowed_vs_expected, 2)
        return d


class SmearingType(Enum):
    """Classification of smearing pattern."""
    ALLOWED_AMOUNT_DRIFT = "allowed_amount_drift"
    SILENT_DOWNCODE = "silent_downcode"
    OPAQUE_BUNDLING = "opaque_bundling"
    ZERO_BALANCE_BURIAL = "zero_balance_burial"
    THRESHOLD_FRAGMENTATION = "threshold_fragmentation"
    FEE_SCHEDULE_VERSION_MISMATCH = "fee_schedule_version_mismatch"
    MODIFIER_SUPPRESSION = "modifier_suppression"
    ESCALATOR_OMISSION = "escalator_omission"


@dataclass
class SmearingPattern:
    """Detected systematic underpayment pattern."""
    pattern_id: str
    smearing_type: str
    payer_name: str
    service_family: str
    description: str
    window_weeks: int               # Detection window
    num_claims_affected: int
    total_variance: float           # Aggregate underpayment
    mean_variance_per_claim: float
    variance_trend: str             # stable, worsening, improving
    statistical_significance: float # p-value or confidence
    is_material: bool               # Above materiality threshold
    evidence: Dict[str, Any] = field(default_factory=dict)
    recovery_strategy: str = ''
    estimated_recovery: float = 0.0
    batch_appealable: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ZeroBalanceCase:
    """Account closed at zero balance but with contractual variance."""
    claim_id: str
    payer_name: str
    closed_date: str
    total_billed: float
    total_expected: float
    total_paid: float
    variance: float
    closure_reason: str
    days_since_closure: int
    reopenable: bool
    reopen_deadline: str
    evidence: str = ''

    def to_dict(self) -> dict:
        return asdict(self)


# ============================================================
# DRIFT DETECTOR
# ============================================================

class DriftDetector:
    """Statistical change-point detection on payment streams.

    Uses CUSUM (Cumulative Sum) algorithm — designed for detecting
    small persistent shifts in process mean. Perfect for smearing
    because smearing IS a small persistent shift.

    Alternative: Bayesian Online Change Point Detection for
    production deployment with streaming data.
    """

    def __init__(self, sensitivity: float = 0.5, threshold: float = 4.0):
        self.sensitivity = sensitivity  # δ: minimum shift to detect
        self.threshold = threshold       # h: decision threshold

    def cusum(self, values: List[float],
              target_mean: float = None) -> Dict[str, Any]:
        """Run CUSUM change-point detection.

        Args:
            values: time-ordered sequence of observations
            target_mean: expected mean (from contract). If None, uses first 25% as baseline.

        Returns:
            Dict with change points, current status, and drift magnitude.
        """
        if len(values) < 10:
            return {
                'change_detected': False,
                'message': 'Insufficient data (need ≥10 observations)',
                'n_observations': len(values),
            }

        # Establish baseline
        if target_mean is None:
            baseline_n = max(5, len(values) // 4)
            target_mean = sum(values[:baseline_n]) / baseline_n

        # Calculate standard deviation from baseline
        baseline = values[:max(5, len(values) // 4)]
        if len(baseline) < 2:
            return {'change_detected': False, 'message': 'Insufficient baseline'}
        mean_b = sum(baseline) / len(baseline)
        std_b = math.sqrt(sum((x - mean_b) ** 2 for x in baseline) / (len(baseline) - 1))
        if std_b == 0:
            std_b = abs(target_mean) * 0.01 or 1.0  # Prevent division by zero

        # Normalize
        k = self.sensitivity / 2  # allowance
        h = self.threshold

        # CUSUM statistics
        s_pos = [0.0]  # Detect upward shift (overpayment — less common)
        s_neg = [0.0]  # Detect downward shift (underpayment — the signal)
        change_points = []

        for i, x in enumerate(values):
            z = (x - target_mean) / std_b  # standardized
            s_pos.append(max(0, s_pos[-1] + z - k))
            s_neg.append(max(0, s_neg[-1] - z - k))

            if s_neg[-1] > h:
                change_points.append({
                    'index': i,
                    'direction': 'downward',
                    'magnitude': s_neg[-1],
                    'value': x,
                })
                s_neg[-1] = 0  # Reset after detection

            if s_pos[-1] > h:
                change_points.append({
                    'index': i,
                    'direction': 'upward',
                    'magnitude': s_pos[-1],
                    'value': x,
                })
                s_pos[-1] = 0

        # Current drift status
        current_mean = sum(values[-min(10, len(values)):]) / min(10, len(values))
        drift_pct = ((current_mean - target_mean) / target_mean * 100) if target_mean != 0 else 0

        return {
            'change_detected': len(change_points) > 0,
            'change_points': change_points,
            'n_observations': len(values),
            'target_mean': round(target_mean, 2),
            'current_mean': round(current_mean, 2),
            'drift_pct': round(drift_pct, 2),
            'drift_direction': 'underpayment' if drift_pct < -1 else
                               'overpayment' if drift_pct > 1 else 'stable',
            'cusum_neg_current': round(s_neg[-1], 3),
            'cusum_pos_current': round(s_pos[-1], 3),
            'std_baseline': round(std_b, 2),
        }

    def detect_trend(self, values: List[float]) -> str:
        """Simple trend detection: worsening, stable, or improving."""
        if len(values) < 6:
            return 'insufficient_data'

        n = len(values)
        first_half = sum(values[:n//2]) / (n//2)
        second_half = sum(values[n//2:]) / (n - n//2)

        diff_pct = ((second_half - first_half) / abs(first_half) * 100) if first_half != 0 else 0

        if diff_pct < -3:
            return 'worsening'
        elif diff_pct > 3:
            return 'improving'
        return 'stable'


# ============================================================
# SMEARING ANALYZER
# ============================================================

class SmearingAnalyzer:
    """Core engine: aggregates micro-variances into material patterns.

    Groups claims by payer × service_family × time_window and
    applies statistical tests to detect systematic underpayment.
    """

    def __init__(self, materiality_threshold: float = 1000.0,
                 min_claims_for_pattern: int = 5,
                 window_weeks: int = 8):
        self.materiality = materiality_threshold
        self.min_claims = min_claims_for_pattern
        self.window_weeks = window_weeks
        self.drift_detector = DriftDetector()

    def analyze(self, observations: List[PaymentObservation]) -> List[SmearingPattern]:
        """Detect smearing patterns across all observations."""
        patterns = []

        # Group by payer × service family
        groups = defaultdict(list)
        for obs in observations:
            key = (obs.payer_name, obs.service_family)
            groups[key].append(obs)

        for (payer, family), claims in groups.items():
            if len(claims) < self.min_claims:
                continue

            # Sort by date
            claims.sort(key=lambda c: c.date_of_service or c.date_paid or '')

            # === Allowed Amount Drift ===
            drift_pattern = self._detect_allowed_drift(payer, family, claims)
            if drift_pattern:
                patterns.append(drift_pattern)

            # === Silent Downcode ===
            downcode_pattern = self._detect_silent_downcode(payer, family, claims)
            if downcode_pattern:
                patterns.append(downcode_pattern)

            # === Opaque Bundling ===
            bundling_pattern = self._detect_opaque_bundling(payer, family, claims)
            if bundling_pattern:
                patterns.append(bundling_pattern)

            # === Threshold Fragmentation ===
            frag_pattern = self._detect_threshold_fragmentation(payer, family, claims)
            if frag_pattern:
                patterns.append(frag_pattern)

            # === Modifier Suppression ===
            mod_pattern = self._detect_modifier_suppression(payer, family, claims)
            if mod_pattern:
                patterns.append(mod_pattern)

            # === Escalator Omission ===
            esc_pattern = self._detect_escalator_omission(payer, family, claims)
            if esc_pattern:
                patterns.append(esc_pattern)

        # Sort by total variance (biggest smearing first)
        patterns.sort(key=lambda p: -abs(p.total_variance))
        return patterns

    def _detect_allowed_drift(self, payer: str, family: str,
                               claims: List[PaymentObservation]) -> Optional[SmearingPattern]:
        """Detect gradual drift in allowed amounts vs contract expected."""
        # Extract variance percentages as time series
        variances = [c.variance_pct for c in claims if c.expected_amount > 0]
        if len(variances) < self.min_claims:
            return None

        # Run CUSUM
        result = self.drift_detector.cusum(variances, target_mean=0.0)

        if not result.get('change_detected') and abs(result.get('drift_pct', 0)) < 2:
            return None

        total_var = sum(c.variance_vs_expected for c in claims)
        if abs(total_var) < self.materiality:
            return None

        trend = self.drift_detector.detect_trend(variances)

        return SmearingPattern(
            pattern_id=f'SMEAR-DRIFT-{payer[:6]}-{family[:6]}'.upper(),
            smearing_type=SmearingType.ALLOWED_AMOUNT_DRIFT.value,
            payer_name=payer,
            service_family=family,
            description=(f'Systematic allowed amount drift: {result["drift_pct"]:+.1f}% '
                         f'over {len(claims)} claims. '
                         f'Expected mean: ${result["target_mean"]:,.0f}, '
                         f'Current mean: ${result["current_mean"]:,.0f}'),
            window_weeks=self.window_weeks,
            num_claims_affected=len(claims),
            total_variance=round(total_var, 2),
            mean_variance_per_claim=round(total_var / len(claims), 2),
            variance_trend=trend,
            statistical_significance=0.95 if result['change_detected'] else 0.70,
            is_material=abs(total_var) >= self.materiality,
            evidence={
                'cusum_result': result,
                'sample_claims': [c.claim_id for c in claims[:5]],
            },
            recovery_strategy='batch_contract_dispute',
            estimated_recovery=round(abs(total_var) * 0.60, 2),
            batch_appealable=True,
        )

    def _detect_silent_downcode(self, payer: str, family: str,
                                 claims: List[PaymentObservation]) -> Optional[SmearingPattern]:
        """Detect when payer consistently pays at a lower service level."""
        downcoded = [c for c in claims
                     if c.variance_pct > 15  # Paid 15%+ below expected
                     and 'CO-4' not in c.carc_codes  # Not flagged as coding error
                     and c.paid_amount > 0]  # Was actually "paid" (not denied)

        if len(downcoded) < self.min_claims:
            return None

        total_var = sum(c.variance_vs_expected for c in downcoded)
        if abs(total_var) < self.materiality:
            return None

        # Check if downcode rate is abnormal
        downcode_rate = len(downcoded) / len(claims)
        if downcode_rate < 0.15:  # Less than 15% — might be noise
            return None

        return SmearingPattern(
            pattern_id=f'SMEAR-DCODE-{payer[:6]}-{family[:6]}'.upper(),
            smearing_type=SmearingType.SILENT_DOWNCODE.value,
            payer_name=payer,
            service_family=family,
            description=(f'Silent downcoding: {len(downcoded)}/{len(claims)} claims '
                         f'({downcode_rate:.0%}) paid 15%+ below expected with no denial code. '
                         f'Appears as "paid" but at systematically lower level.'),
            window_weeks=self.window_weeks,
            num_claims_affected=len(downcoded),
            total_variance=round(total_var, 2),
            mean_variance_per_claim=round(total_var / len(downcoded), 2),
            variance_trend=self.drift_detector.detect_trend(
                [c.variance_pct for c in downcoded]),
            statistical_significance=0.90,
            is_material=True,
            evidence={
                'downcode_rate': round(downcode_rate, 3),
                'sample_claims': [c.claim_id for c in downcoded[:5]],
                'typical_variance': round(
                    sum(c.variance_pct for c in downcoded) / len(downcoded), 1),
            },
            recovery_strategy='batch_appeal_with_contract_citation',
            estimated_recovery=round(abs(total_var) * 0.55, 2),
            batch_appealable=True,
        )

    def _detect_opaque_bundling(self, payer: str, family: str,
                                 claims: List[PaymentObservation]) -> Optional[SmearingPattern]:
        """Detect proprietary bundling not matching CMS CCI edits."""
        bundled = [c for c in claims if 'CO-97' in c.carc_codes]

        if len(bundled) < 3:
            return None

        total_var = sum(c.billed_amount for c in bundled)  # Full billed = lost
        if total_var < self.materiality:
            return None

        # Check for opaque RARC (no specific explanation)
        opaque = [c for c in bundled
                  if not c.rarc_codes or 'N95' in c.rarc_codes]
        opacity_rate = len(opaque) / len(bundled) if bundled else 0

        return SmearingPattern(
            pattern_id=f'SMEAR-BNDL-{payer[:6]}-{family[:6]}'.upper(),
            smearing_type=SmearingType.OPAQUE_BUNDLING.value,
            payer_name=payer,
            service_family=family,
            description=(f'Opaque bundling: {len(bundled)} claims denied with CO-97 '
                         f'(included in another procedure). {opacity_rate:.0%} have no '
                         f'specific bundling explanation. May use proprietary edits '
                         f'not matching CMS CCI.'),
            window_weeks=self.window_weeks,
            num_claims_affected=len(bundled),
            total_variance=round(total_var, 2),
            mean_variance_per_claim=round(total_var / len(bundled), 2),
            variance_trend='stable',
            statistical_significance=0.85,
            is_material=True,
            evidence={
                'opacity_rate': round(opacity_rate, 3),
                'co97_claims': len(bundled),
                'sample_claims': [c.claim_id for c in bundled[:5]],
            },
            recovery_strategy='cci_comparison_appeal',
            estimated_recovery=round(total_var * 0.45, 2),
            batch_appealable=True,
        )

    def _detect_threshold_fragmentation(self, payer: str, family: str,
                                          claims: List[PaymentObservation]) -> Optional[SmearingPattern]:
        """Detect when individual variances cluster just below appeal threshold.

        If a payer knows the hospital's appeal threshold is $200,
        they can systematically underpay by $150-190 per claim.
        No single claim triggers review. Aggregate loss is massive.
        """
        APPEAL_THRESHOLD = 200.0  # Typical hospital threshold for manual appeal

        micro_variances = [c for c in claims
                          if 0 < c.variance_vs_expected < APPEAL_THRESHOLD
                          and c.paid_amount > 0]

        if len(micro_variances) < self.min_claims * 2:
            return None

        total = sum(c.variance_vs_expected for c in micro_variances)
        if total < self.materiality:
            return None

        # Statistical test: are variances clustered below threshold?
        # If uniformly distributed, we'd expect even spread.
        # If clustered near threshold, it's strategic.
        near_threshold = [c for c in micro_variances
                         if c.variance_vs_expected > APPEAL_THRESHOLD * 0.5]
        clustering_ratio = len(near_threshold) / len(micro_variances) if micro_variances else 0

        return SmearingPattern(
            pattern_id=f'SMEAR-FRAG-{payer[:6]}-{family[:6]}'.upper(),
            smearing_type=SmearingType.THRESHOLD_FRAGMENTATION.value,
            payer_name=payer,
            service_family=family,
            description=(f'Threshold fragmentation: {len(micro_variances)} claims with '
                         f'variances between $1-${APPEAL_THRESHOLD:.0f} (below appeal threshold). '
                         f'Aggregate loss: ${total:,.0f}. {clustering_ratio:.0%} cluster in '
                         f'upper half — possible strategic pricing below reaction threshold.'),
            window_weeks=self.window_weeks,
            num_claims_affected=len(micro_variances),
            total_variance=round(total, 2),
            mean_variance_per_claim=round(total / len(micro_variances), 2),
            variance_trend='stable',
            statistical_significance=0.80 if clustering_ratio > 0.6 else 0.60,
            is_material=True,
            evidence={
                'appeal_threshold': APPEAL_THRESHOLD,
                'clustering_ratio': round(clustering_ratio, 3),
                'mean_variance': round(total / len(micro_variances), 2),
                'total_claims': len(claims),
                'micro_claims': len(micro_variances),
            },
            recovery_strategy='batch_balance_bill',
            estimated_recovery=round(total * 0.70, 2),
            batch_appealable=True,
        )

    def _detect_modifier_suppression(self, payer: str, family: str,
                                       claims: List[PaymentObservation]) -> Optional[SmearingPattern]:
        """Detect when modifier adjustments are silently ignored."""
        with_modifiers = [c for c in claims if c.modifier and c.modifier.strip()]
        if len(with_modifiers) < 3:
            return None

        # Compare: claims with modifier that have same variance pattern
        # as claims without — suggests modifier not being applied
        underpaid_with_mod = [c for c in with_modifiers if c.variance_pct > 10]
        if len(underpaid_with_mod) < 3:
            return None

        total = sum(c.variance_vs_expected for c in underpaid_with_mod)
        if abs(total) < self.materiality:
            return None

        return SmearingPattern(
            pattern_id=f'SMEAR-MOD-{payer[:6]}-{family[:6]}'.upper(),
            smearing_type=SmearingType.MODIFIER_SUPPRESSION.value,
            payer_name=payer,
            service_family=family,
            description=(f'Modifier suppression: {len(underpaid_with_mod)} claims with '
                         f'modifiers underpaid by 10%+. Modifier adjustments may not '
                         f'be applied to contracted rates.'),
            window_weeks=self.window_weeks,
            num_claims_affected=len(underpaid_with_mod),
            total_variance=round(total, 2),
            mean_variance_per_claim=round(total / len(underpaid_with_mod), 2),
            variance_trend='stable',
            statistical_significance=0.75,
            is_material=abs(total) >= self.materiality,
            evidence={
                'modifiers_affected': list(set(c.modifier for c in underpaid_with_mod)),
                'sample_claims': [c.claim_id for c in underpaid_with_mod[:5]],
            },
            recovery_strategy='modifier_appeal_with_contract_exhibit',
            estimated_recovery=round(abs(total) * 0.65, 2),
            batch_appealable=True,
        )

    def _detect_escalator_omission(self, payer: str, family: str,
                                     claims: List[PaymentObservation]) -> Optional[SmearingPattern]:
        """Detect when annual rate escalators haven't been applied."""
        # If we see a sudden drop in payment ratio at year boundary, escalator was missed
        by_year = defaultdict(list)
        for c in claims:
            try:
                year = c.date_of_service[:4] if c.date_of_service else c.date_paid[:4]
                by_year[year].append(c)
            except:
                pass

        if len(by_year) < 2:
            return None

        years = sorted(by_year.keys())
        year_means = {}
        for y in years:
            ratios = [c.paid_amount / c.expected_amount
                      for c in by_year[y]
                      if c.expected_amount > 0 and c.paid_amount > 0]
            if ratios:
                year_means[y] = sum(ratios) / len(ratios)

        if len(year_means) < 2:
            return None

        # Check if payment ratio dropped or stayed flat when it should have increased
        years_sorted = sorted(year_means.keys())
        latest = year_means[years_sorted[-1]]
        previous = year_means[years_sorted[-2]]

        if latest <= previous and latest < 0.98:  # Not improving and below 98%
            total_claims = sum(len(by_year[y]) for y in years_sorted[-2:])
            total_var = sum(
                c.variance_vs_expected
                for y in years_sorted[-2:]
                for c in by_year[y]
            )

            if abs(total_var) < self.materiality:
                return None

            return SmearingPattern(
                pattern_id=f'SMEAR-ESC-{payer[:6]}-{family[:6]}'.upper(),
                smearing_type=SmearingType.ESCALATOR_OMISSION.value,
                payer_name=payer,
                service_family=family,
                description=(f'Possible escalator omission: payment ratio {latest:.1%} '
                             f'in {years_sorted[-1]} vs {previous:.1%} in {years_sorted[-2]}. '
                             f'If contract has annual escalator, it may not have been applied.'),
                window_weeks=52,
                num_claims_affected=total_claims,
                total_variance=round(total_var, 2),
                mean_variance_per_claim=round(total_var / total_claims, 2) if total_claims else 0,
                variance_trend='worsening',
                statistical_significance=0.85,
                is_material=abs(total_var) >= self.materiality,
                evidence={
                    'payment_ratios_by_year': {k: round(v, 4) for k, v in year_means.items()},
                    'years_analyzed': years_sorted,
                },
                recovery_strategy='contract_escalator_dispute',
                estimated_recovery=round(abs(total_var) * 0.80, 2),
                batch_appealable=True,
            )

        return None


# ============================================================
# ZERO BALANCE HUNTER
# ============================================================

class ZeroBalanceHunter:
    """Reopens "closed" accounts that were paid below contract.

    The deadliest smearing tactic: account gets paid, posted,
    and closed. Everyone moves on. But the payment was $200
    less than contract. Multiply by 5,000 accounts = $1M lost.

    Zero-balance review is the ONLY way to catch this.
    """

    def __init__(self, reopen_window_days: int = 365,
                 minimum_variance: float = 25.0):
        self.reopen_window = reopen_window_days
        self.min_variance = minimum_variance

    def hunt(self, observations: List[PaymentObservation]) -> List[ZeroBalanceCase]:
        """Find closed accounts with contractual variance."""
        cases = []

        for obs in observations:
            if obs.account_status != 'zero_balance':
                continue

            variance = obs.variance_vs_expected
            if variance < self.min_variance:
                continue

            # Calculate days since closure
            days_since = 0
            try:
                closed = datetime.strptime(obs.date_paid, '%Y-%m-%d')
                days_since = (datetime.now() - closed).days
            except:
                days_since = 30  # assume recent

            reopenable = days_since < self.reopen_window

            cases.append(ZeroBalanceCase(
                claim_id=obs.claim_id,
                payer_name=obs.payer_name,
                closed_date=obs.date_paid,
                total_billed=obs.billed_amount,
                total_expected=obs.expected_amount,
                total_paid=obs.paid_amount,
                variance=round(variance, 2),
                closure_reason='paid_and_posted',
                days_since_closure=days_since,
                reopenable=reopenable,
                reopen_deadline=(
                    datetime.strptime(obs.date_paid, '%Y-%m-%d') +
                    timedelta(days=self.reopen_window)
                ).strftime('%Y-%m-%d') if obs.date_paid else '',
                evidence=f'Expected ${obs.expected_amount:,.2f}, '
                         f'paid ${obs.paid_amount:,.2f}, '
                         f'variance ${variance:,.2f} ({obs.variance_pct:.1f}%)',
            ))

        # Sort by variance (biggest money first), then urgency
        cases.sort(key=lambda c: (-c.variance, -c.days_since_closure))
        return cases


# ============================================================
# RECOVERY BATCH GENERATOR
# ============================================================

class RecoveryBatchGenerator:
    """Groups micro-variances into batch recovery actions.

    Individual $50 underpayments aren't worth pursuing.
    But 200 of them from the same payer with the same pattern?
    That's a $10,000 batch contract dispute with evidence of
    systematic breach.
    """

    def generate_batches(self, patterns: List[SmearingPattern],
                         zero_balance_cases: List[ZeroBalanceCase] = None
                         ) -> List[Dict[str, Any]]:
        """Create actionable recovery batches."""
        batches = []

        # Group patterns by payer and recovery strategy
        by_payer_strategy = defaultdict(list)
        for p in patterns:
            if p.is_material and p.batch_appealable:
                by_payer_strategy[(p.payer_name, p.recovery_strategy)].append(p)

        for (payer, strategy), group_patterns in by_payer_strategy.items():
            total_variance = sum(p.total_variance for p in group_patterns)
            total_recovery = sum(p.estimated_recovery for p in group_patterns)
            total_claims = sum(p.num_claims_affected for p in group_patterns)

            batches.append({
                'batch_id': f'BATCH-{payer[:6]}-{strategy[:8]}'.upper(),
                'payer': payer,
                'recovery_strategy': strategy,
                'patterns': [p.pattern_id for p in group_patterns],
                'smearing_types': list(set(p.smearing_type for p in group_patterns)),
                'total_claims': total_claims,
                'total_variance': round(total_variance, 2),
                'estimated_recovery': round(total_recovery, 2),
                'evidence_strength': 'strong' if all(
                    p.statistical_significance > 0.80 for p in group_patterns
                ) else 'moderate',
                'recommended_action': self._recommend_action(strategy, total_variance),
            })

        # Add zero-balance batch
        if zero_balance_cases:
            reopenable = [c for c in zero_balance_cases if c.reopenable]
            if reopenable:
                total_zb_var = sum(c.variance for c in reopenable)
                batches.append({
                    'batch_id': f'BATCH-ZB-REOPEN',
                    'payer': 'multiple',
                    'recovery_strategy': 'zero_balance_reopen',
                    'patterns': [],
                    'smearing_types': [SmearingType.ZERO_BALANCE_BURIAL.value],
                    'total_claims': len(reopenable),
                    'total_variance': round(total_zb_var, 2),
                    'estimated_recovery': round(total_zb_var * 0.50, 2),
                    'evidence_strength': 'strong',
                    'recommended_action': f'Reopen {len(reopenable)} zero-balance accounts. '
                                          f'Total variance: ${total_zb_var:,.0f}',
                })

        batches.sort(key=lambda b: -b['estimated_recovery'])
        return batches

    def _recommend_action(self, strategy: str, total: float) -> str:
        actions = {
            'batch_contract_dispute': (
                f'File formal contract dispute citing systematic underpayment '
                f'of ${total:,.0f}. Attach variance analysis as evidence of '
                f'pattern. Request contract compliance review.'),
            'batch_appeal_with_contract_citation': (
                f'Batch appeal ${total:,.0f} in silent downcoding. Cite specific '
                f'contract fee schedule exhibits for each service family.'),
            'cci_comparison_appeal': (
                f'Challenge proprietary bundling edits. Compare payer bundling '
                f'decisions against CMS CCI edits. Cite NCCI Policy Manual '
                f'for each disputed code pair.'),
            'batch_balance_bill': (
                f'Batch balance bill for ${total:,.0f} in micro-underpayments. '
                f'Group by CPT family for efficiency.'),
            'modifier_appeal_with_contract_exhibit': (
                f'Appeal modifier-related underpayments citing contract modifier '
                f'adjustment tables. Request payer explain calculation methodology.'),
            'contract_escalator_dispute': (
                f'Formal contract dispute for ${total:,.0f}: annual escalator '
                f'not applied. Cite escalator clause with effective date. '
                f'Request retroactive adjustment.'),
        }
        return actions.get(strategy, f'Pursue recovery of ${total:,.0f}')


# ============================================================
# DEMO
# ============================================================

def generate_demo_observations() -> List[PaymentObservation]:
    """Generate realistic payment stream with embedded smearing patterns."""
    import random
    random.seed(42)

    observations = []
    claim_counter = 0

    # Pattern 1: UHC E&M allowed amount drift (-3.5% over 8 weeks)
    for week in range(12):
        for _ in range(random.randint(8, 15)):
            claim_counter += 1
            expected = 316.0 * 1.40  # 140% of Medicare 99223
            drift = 1.0 - (week * 0.004 if week > 3 else 0)  # Drift starts week 4
            paid = expected * drift * random.uniform(0.97, 1.03)

            observations.append(PaymentObservation(
                claim_id=f'CLM-EM-{claim_counter:04d}',
                payer_id='UHC', payer_name='united_healthcare',
                service_family='E&M', cpt_code='99223',
                specialty='hospitalist',
                date_of_service=f'2026-{1 + week // 4:02d}-{(week % 4) * 7 + 1:02d}',
                date_paid=f'2026-{1 + week // 4 + 1:02d}-{(week % 4) * 7 + 1:02d}',
                billed_amount=850, expected_amount=expected,
                allowed_amount=paid * 1.02, paid_amount=round(paid, 2),
            ))

    # Pattern 2: Aetna silent downcoding on surgery (pays 15-25% below)
    for i in range(25):
        claim_counter += 1
        expected = 6842 * 1.30  # 130% of Medicare for 43775
        downcode = random.choice([True, True, True, False])  # 75% downcoded
        if downcode:
            paid = expected * random.uniform(0.72, 0.85)
        else:
            paid = expected * random.uniform(0.97, 1.02)

        observations.append(PaymentObservation(
            claim_id=f'CLM-SURG-{claim_counter:04d}',
            payer_id='AETNA', payer_name='aetna',
            service_family='surgery', cpt_code='43775',
            specialty='bariatric',
            date_of_service=f'2026-{1 + i // 10:02d}-{(i % 10) * 3 + 1:02d}',
            date_paid=f'2026-{2 + i // 10:02d}-{(i % 10) * 3 + 1:02d}',
            billed_amount=45000, expected_amount=expected,
            allowed_amount=paid, paid_amount=round(paid, 2),
            account_status='zero_balance' if random.random() < 0.6 else 'open',
        ))

    # Pattern 3: Cigna threshold fragmentation ($50-180 per claim)
    for i in range(80):
        claim_counter += 1
        expected = 178 * 1.40  # 140% Medicare for 99233
        underpay = random.uniform(50, 180)  # Below $200 appeal threshold
        paid = expected - underpay

        observations.append(PaymentObservation(
            claim_id=f'CLM-FRAG-{claim_counter:04d}',
            payer_id='CIGNA', payer_name='cigna',
            service_family='E&M', cpt_code='99233',
            date_of_service=f'2026-{1 + i // 30:02d}-{(i % 30) + 1:02d}',
            date_paid=f'2026-{2 + i // 30:02d}-{(i % 30) + 1:02d}',
            billed_amount=450, expected_amount=expected,
            allowed_amount=paid, paid_amount=round(paid, 2),
        ))

    # Pattern 4: Anthem opaque bundling
    for i in range(12):
        claim_counter += 1
        observations.append(PaymentObservation(
            claim_id=f'CLM-BNDL-{claim_counter:04d}',
            payer_id='ANTHEM', payer_name='anthem_bcbs',
            service_family='procedures', cpt_code='36620',
            date_of_service=f'2026-01-{i * 2 + 1:02d}',
            date_paid=f'2026-02-{i * 2 + 1:02d}',
            billed_amount=1200, expected_amount=475,
            allowed_amount=0, paid_amount=0,
            carc_codes=['CO-97'],
            rarc_codes=['N95'] if random.random() < 0.7 else ['N362'],
            adjustment_reason='Included in another procedure',
        ))

    return observations


def main():
    import argparse
    parser = argparse.ArgumentParser(description='SMEARING ENGINE')
    subparsers = parser.add_subparsers(dest='command')
    subparsers.add_parser('demo', help='Full smearing analysis with demo data')
    subparsers.add_parser('summary', help='Executive summary only')

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    observations = generate_demo_observations()
    analyzer = SmearingAnalyzer()
    zb_hunter = ZeroBalanceHunter()
    batch_gen = RecoveryBatchGenerator()

    patterns = analyzer.analyze(observations)
    zb_cases = zb_hunter.hunt(observations)
    batches = batch_gen.generate_batches(patterns, zb_cases)

    if args.command == 'demo':
        result = {
            'meta': {
                'total_observations': len(observations),
                'analysis_date': datetime.now().isoformat(),
                'engine_version': '4.0.0',
            },
            'patterns_detected': [p.to_dict() for p in patterns],
            'zero_balance_cases': {
                'total': len(zb_cases),
                'reopenable': len([c for c in zb_cases if c.reopenable]),
                'total_variance': round(sum(c.variance for c in zb_cases), 2),
                'cases': [c.to_dict() for c in zb_cases[:10]],
            },
            'recovery_batches': batches,
            'executive_summary': {
                'total_smearing_detected': round(
                    sum(p.total_variance for p in patterns), 2),
                'total_recoverable': round(
                    sum(p.estimated_recovery for p in patterns), 2),
                'total_zero_balance': round(
                    sum(c.variance for c in zb_cases if c.reopenable), 2),
                'num_patterns': len(patterns),
                'num_batches': len(batches),
                'payers_affected': list(set(p.payer_name for p in patterns)),
            },
        }
        print(json.dumps(result, indent=2, default=str))

    elif args.command == 'summary':
        total_smear = sum(p.total_variance for p in patterns)
        total_recovery = sum(p.estimated_recovery for p in patterns)
        total_zb = sum(c.variance for c in zb_cases if c.reopenable)

        print('\n═════════════════════════════════════════════════════')
        print('  SMEARING ENGINE — EXECUTIVE SUMMARY')
        print('═════════════════════════════════════════════════════')
        print(f'  Observations analyzed: {len(observations)}')
        print(f'  Patterns detected:     {len(patterns)}')
        print()
        print(f'  TOTAL SMEARING:        ${total_smear:>12,.2f}')
        print(f'  ESTIMATED RECOVERY:    ${total_recovery:>12,.2f}')
        print(f'  ZERO-BALANCE BURIED:   ${total_zb:>12,.2f}')
        print(f'  COMBINED OPPORTUNITY:  ${total_smear + total_zb:>12,.2f}')
        print()
        print('  PATTERNS:')
        for p in patterns:
            print(f'  [{p.smearing_type[:20]:20s}] {p.payer_name:20s} '
                  f'${p.total_variance:>10,.0f}  ({p.num_claims_affected} claims)  '
                  f'trend: {p.variance_trend}')
        print()
        print('  RECOVERY BATCHES:')
        for b in batches:
            print(f'  {b["batch_id"]:30s} ${b["total_variance"]:>10,.0f} → '
                  f'est recovery ${b["estimated_recovery"]:>10,.0f}  '
                  f'({b["total_claims"]} claims)')
        print('═════════════════════════════════════════════════════')


if __name__ == '__main__':
    main()
