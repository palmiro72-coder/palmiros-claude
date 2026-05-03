#!/usr/bin/env python3
"""
CLAIM DIGITAL TWIN — Strategic Claim Simulation Engine
Part of DENIAL SHIELD v3.0 — Revenue Intelligence Platform
Inventor: Dr. Lucas do Prado Palmiro

A claim is not a document. It's a financial asset with:
  - A defensible value (what the contract says)
  - A risk profile (how the payer will react)
  - A set of strategies (how to maximize net reimbursement)
  - A decision tree (what to do when, based on outcomes)

The Digital Twin creates a simulation of each claim across
multiple submission strategies and recommends the optimal play.

"Make the CFO feel that each claim is a derivative with
 price, risk, and hedge."

Architecture:
  ClaimTwin        — The digital twin with 4 layers
  StrategyEngine   — Generates and evaluates submission strategies
  SimulationEngine — Monte Carlo simulation of outcomes
  DecisionEngine   — Recommends optimal action
"""

import json
import math
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from collections import defaultdict


# ============================================================
# THE FOUR LAYERS
# ============================================================

@dataclass
class ClinicalLayer:
    """Layer 1: What was actually documented and performed."""
    diagnoses: List[str] = field(default_factory=list)      # ICD-10 codes
    procedures: List[str] = field(default_factory=list)      # CPT codes
    documentation_score: float = 0.5                         # CDI score (0-1)
    documentation_gaps: List[str] = field(default_factory=list)
    drg_opportunities: List[Dict] = field(default_factory=list)
    clinical_narrative_strength: float = 0.5  # How well does narrative support billing?
    objective_data_present: bool = False      # Labs, imaging, vitals documented?
    guideline_cited: bool = False             # Society guideline referenced?
    treatment_failure_documented: bool = False
    informed_consent_present: bool = False

    @property
    def medical_necessity_score(self) -> float:
        """Composite score for medical necessity defensibility."""
        score = self.documentation_score * 0.4
        if self.objective_data_present:
            score += 0.15
        if self.guideline_cited:
            score += 0.20
        if self.treatment_failure_documented:
            score += 0.15
        if self.informed_consent_present:
            score += 0.10
        return min(1.0, score)


@dataclass
class RegulatoryLayer:
    """Layer 2: What is defensible by guideline, policy, and contract."""
    cms_coverage: bool = True                  # Covered by Medicare NCD/LCD?
    lcd_reference: str = ''                     # Specific LCD citation
    ncd_reference: str = ''                     # Specific NCD citation
    prior_auth_obtained: bool = False
    prior_auth_valid: bool = False              # Not expired?
    prior_auth_matches_procedure: bool = False  # Auth CPT = billed CPT?
    in_network: bool = True
    contract_covers_service: bool = True
    modifier_compliant: bool = True
    cci_edits_clear: bool = True               # No bundling violations
    two_midnight_met: bool = True              # For inpatient
    state_mandate_applies: bool = False
    applicable_regulations: List[str] = field(default_factory=list)

    @property
    def regulatory_strength(self) -> float:
        """How defensible is this claim from a regulatory perspective?"""
        factors = [
            self.cms_coverage,
            self.prior_auth_obtained,
            self.prior_auth_valid,
            self.prior_auth_matches_procedure,
            self.contract_covers_service,
            self.modifier_compliant,
            self.cci_edits_clear,
            self.two_midnight_met,
        ]
        return sum(factors) / len(factors)


@dataclass
class EconomicLayer:
    """Layer 3: What should be paid in each scenario."""
    billed_charges: float = 0.0
    expected_reimbursement: float = 0.0        # Contract compiler output
    expected_patient_responsibility: float = 0.0
    drg_base_payment: float = 0.0
    drg_with_optimization: float = 0.0         # If missed CC/MCCs added
    carve_out_value: float = 0.0               # Devices/implants carved out
    stop_loss_eligible: bool = False
    stop_loss_additional: float = 0.0
    outlier_eligible: bool = False
    outlier_additional: float = 0.0
    total_optimized_value: float = 0.0         # Best-case with all optimizations

    @property
    def optimization_delta(self) -> float:
        """Additional revenue if all optimizations applied."""
        return self.total_optimized_value - self.expected_reimbursement


@dataclass
class BehavioralLayer:
    """Layer 4: How the payer will likely react."""
    payer_name: str = ''
    payer_denial_rate: float = 0.14
    predicted_denial_probability: float = 0.0
    primary_attack_vector: str = ''            # Most likely denial code
    secondary_attack_vectors: List[str] = field(default_factory=list)
    appeal_success_probability: float = 0.40
    peer_to_peer_success_probability: float = 0.60
    expected_days_to_payment: int = 45
    temporal_risk_factor: float = 1.0          # Quarter-end spike, etc.
    payer_specific_warnings: List[str] = field(default_factory=list)


@dataclass
class ClaimTwin:
    """The Digital Twin — 4 layers combined."""
    claim_id: str
    clinical: ClinicalLayer
    regulatory: RegulatoryLayer
    economic: EconomicLayer
    behavioral: BehavioralLayer

    @property
    def composite_value(self) -> float:
        """Expected value accounting for all risk factors."""
        base = self.economic.expected_reimbursement
        denial_risk = self.behavioral.predicted_denial_probability
        appeal_recovery = denial_risk * self.behavioral.appeal_success_probability
        net_risk = denial_risk - appeal_recovery
        return base * (1 - net_risk)

    @property
    def optimized_value(self) -> float:
        """Value with all legal optimizations applied."""
        base = self.economic.total_optimized_value or self.economic.expected_reimbursement
        denial_risk = max(0, self.behavioral.predicted_denial_probability - 0.15)
        # Optimizations typically reduce denial risk by ~15% (better documentation)
        return base * (1 - denial_risk)

    def to_dict(self) -> dict:
        d = {
            'claim_id': self.claim_id,
            'clinical': asdict(self.clinical),
            'regulatory': asdict(self.regulatory),
            'economic': asdict(self.economic),
            'behavioral': asdict(self.behavioral),
            'composite_value': round(self.composite_value, 2),
            'optimized_value': round(self.optimized_value, 2),
            'optimization_uplift': round(self.optimized_value - self.composite_value, 2),
        }
        d['clinical']['medical_necessity_score'] = round(
            self.clinical.medical_necessity_score, 3)
        d['regulatory']['regulatory_strength'] = round(
            self.regulatory.regulatory_strength, 3)
        d['economic']['optimization_delta'] = round(
            self.economic.optimization_delta, 2)
        return d


# ============================================================
# STRATEGY ENGINE
# ============================================================

@dataclass
class SubmissionStrategy:
    """A specific strategy for submitting/handling a claim."""
    strategy_id: str
    name: str
    description: str
    actions: List[str]               # What to do
    estimated_denial_prob: float      # New denial probability if strategy applied
    estimated_reimbursement: float    # Expected payment
    estimated_time_to_payment: int    # Days
    cost_to_implement: float          # Staff time, opportunity cost
    risk_level: str                   # low, medium, high
    net_expected_value: float = 0.0   # Reimbursement × (1-denial) - cost

    def to_dict(self) -> dict:
        return asdict(self)


class StrategyEngine:
    """Generates submission strategies for a claim twin."""

    def generate_strategies(self, twin: ClaimTwin) -> List[SubmissionStrategy]:
        """Generate 3-5 strategies ranked by expected value."""
        strategies = []

        base_reimb = twin.economic.expected_reimbursement
        base_denial = twin.behavioral.predicted_denial_probability
        base_ev = base_reimb * (1 - base_denial)

        # Strategy 1: Submit as-is (baseline)
        strategies.append(SubmissionStrategy(
            strategy_id='S1-BASELINE',
            name='Submit as-is',
            description='Submit current claim without modifications',
            actions=['Submit claim through normal channel'],
            estimated_denial_prob=base_denial,
            estimated_reimbursement=base_reimb,
            estimated_time_to_payment=twin.behavioral.expected_days_to_payment,
            cost_to_implement=0,
            risk_level='medium' if base_denial < 0.3 else 'high',
            net_expected_value=round(base_ev, 2),
        ))

        # Strategy 2: Strengthen documentation, then submit
        if twin.clinical.documentation_score < 0.7:
            doc_actions = []
            improved_denial = base_denial

            if not twin.clinical.guideline_cited:
                doc_actions.append('Add clinical guideline citation to medical record')
                improved_denial *= 0.75

            if not twin.clinical.treatment_failure_documented:
                doc_actions.append('Document prior treatment failure/step therapy')
                improved_denial *= 0.80

            if not twin.clinical.objective_data_present:
                doc_actions.append('Add objective clinical data (labs, imaging results)')
                improved_denial *= 0.85

            if twin.clinical.documentation_gaps:
                for gap in twin.clinical.documentation_gaps[:3]:
                    doc_actions.append(f'Address documentation gap: {gap}')
                improved_denial *= 0.85

            improved_ev = base_reimb * (1 - improved_denial) - 50
            strategies.append(SubmissionStrategy(
                strategy_id='S2-DOC-STRENGTHEN',
                name='Strengthen documentation first',
                description='Request addendum/clarification before submission',
                actions=doc_actions,
                estimated_denial_prob=round(improved_denial, 3),
                estimated_reimbursement=base_reimb,
                estimated_time_to_payment=twin.behavioral.expected_days_to_payment + 3,
                cost_to_implement=50,  # CDI specialist time
                risk_level='low',
                net_expected_value=round(improved_ev, 2),
            ))

        # Strategy 3: Optimize coding (DRG shift)
        if twin.clinical.drg_opportunities:
            optimized_reimb = twin.economic.total_optimized_value or base_reimb * 1.15
            coding_actions = []
            for opp in twin.clinical.drg_opportunities[:3]:
                coding_actions.append(
                    f'Query physician for {opp.get("condition", "condition")} '
                    f'— potential ICD: {opp.get("suggested_icd", "?")}')

            coding_denial = base_denial * 0.9  # Better coding slightly reduces denial
            coding_ev = optimized_reimb * (1 - coding_denial) - 75
            strategies.append(SubmissionStrategy(
                strategy_id='S3-OPTIMIZE-CODING',
                name='Optimize coding before submission',
                description='CDI query for missed CC/MCC — potential DRG upgrade',
                actions=coding_actions,
                estimated_denial_prob=round(coding_denial, 3),
                estimated_reimbursement=round(optimized_reimb, 2),
                estimated_time_to_payment=twin.behavioral.expected_days_to_payment + 5,
                cost_to_implement=75,
                risk_level='low',
                net_expected_value=round(coding_ev, 2),
            ))

        # Strategy 4: Pre-emptive peer-to-peer
        if base_denial > 0.4 and base_reimb > 5000:
            p2p_denial = base_denial * 0.4  # P2P reduces denial by ~60%
            p2p_ev = base_reimb * (1 - p2p_denial) - 200
            strategies.append(SubmissionStrategy(
                strategy_id='S4-PREEMPTIVE-P2P',
                name='Pre-emptive peer-to-peer',
                description='Request physician peer-to-peer BEFORE submission '
                            'to establish medical necessity on record',
                actions=[
                    'Schedule peer-to-peer with payer medical director',
                    'Prepare clinical summary with guideline citations',
                    'Document peer-to-peer outcome for appeal record',
                ],
                estimated_denial_prob=round(p2p_denial, 3),
                estimated_reimbursement=base_reimb,
                estimated_time_to_payment=twin.behavioral.expected_days_to_payment + 14,
                cost_to_implement=200,
                risk_level='low',
                net_expected_value=round(p2p_ev, 2),
            ))

        # Strategy 5: Combined optimization + documentation
        if twin.clinical.drg_opportunities and twin.clinical.documentation_score < 0.7:
            combined_reimb = twin.economic.total_optimized_value or base_reimb * 1.15
            combined_denial = base_denial * 0.6
            combined_ev = combined_reimb * (1 - combined_denial) - 125

            strategies.append(SubmissionStrategy(
                strategy_id='S5-FULL-OPTIMIZATION',
                name='Full optimization package',
                description='Documentation strengthening + coding optimization + '
                            'payer-specific positioning',
                actions=[
                    'CDI query for all identified CC/MCC opportunities',
                    'Request physician addendum for documentation gaps',
                    'Add guideline citations and objective clinical data',
                    'Position claim language for known payer audit criteria',
                    'Pre-prepare appeal package (just in case)',
                ],
                estimated_denial_prob=round(combined_denial, 3),
                estimated_reimbursement=round(combined_reimb, 2),
                estimated_time_to_payment=twin.behavioral.expected_days_to_payment + 7,
                cost_to_implement=125,
                risk_level='low',
                net_expected_value=round(combined_ev, 2),
            ))

        # Sort by net expected value
        strategies.sort(key=lambda s: -s.net_expected_value)
        return strategies


# ============================================================
# SIMULATION ENGINE
# ============================================================

class SimulationEngine:
    """Monte Carlo simulation of claim outcomes.

    Runs N simulations of each strategy to generate
    probability distributions of payment outcomes.
    """

    def simulate(self, twin: ClaimTwin, strategy: SubmissionStrategy,
                 n_simulations: int = 1000, seed: int = 42) -> Dict[str, Any]:
        """Run Monte Carlo simulation for a strategy."""
        random.seed(seed)
        outcomes = []

        for _ in range(n_simulations):
            # Simulate denial decision
            denied = random.random() < strategy.estimated_denial_prob

            if denied:
                # Simulate appeal
                appealed = random.random() < 0.85  # 85% of denials are appealed
                if appealed:
                    appeal_success = random.random() < twin.behavioral.appeal_success_probability
                    if appeal_success:
                        # Partial recovery common on appeal
                        recovery_pct = random.uniform(0.6, 1.0)
                        payment = strategy.estimated_reimbursement * recovery_pct
                        days = strategy.estimated_time_to_payment + random.randint(30, 120)
                    else:
                        # External review
                        ext_review = random.random() < 0.45
                        if ext_review:
                            payment = strategy.estimated_reimbursement * random.uniform(0.7, 1.0)
                            days = strategy.estimated_time_to_payment + random.randint(90, 270)
                        else:
                            payment = 0
                            days = strategy.estimated_time_to_payment + 180
                else:
                    payment = 0
                    days = strategy.estimated_time_to_payment + 30
            else:
                # Paid — but possibly underpaid
                underpay_prob = 0.15  # 15% chance of underpayment even when "paid"
                if random.random() < underpay_prob:
                    payment = strategy.estimated_reimbursement * random.uniform(0.85, 0.98)
                else:
                    payment = strategy.estimated_reimbursement
                days = strategy.estimated_time_to_payment + random.randint(-10, 15)

            outcomes.append({
                'payment': round(payment, 2),
                'days_to_payment': max(0, days),
                'denied': denied,
            })

        # Analyze distribution
        payments = [o['payment'] for o in outcomes]
        days_list = [o['days_to_payment'] for o in outcomes]

        payments.sort()
        n = len(payments)

        return {
            'strategy': strategy.strategy_id,
            'n_simulations': n_simulations,
            'payment_distribution': {
                'mean': round(sum(payments) / n, 2),
                'median': round(payments[n // 2], 2),
                'p5': round(payments[int(n * 0.05)], 2),   # 5th percentile (worst case)
                'p25': round(payments[int(n * 0.25)], 2),
                'p75': round(payments[int(n * 0.75)], 2),
                'p95': round(payments[int(n * 0.95)], 2),   # 95th percentile (best case)
                'zero_payment_rate': round(sum(1 for p in payments if p == 0) / n, 3),
            },
            'days_distribution': {
                'mean': round(sum(days_list) / n, 1),
                'median': days_list[n // 2],
                'p95': days_list[int(n * 0.95)],
            },
            'denial_rate_observed': round(sum(1 for o in outcomes if o['denied']) / n, 3),
            'cost_adjusted_mean': round(sum(payments) / n - strategy.cost_to_implement, 2),
        }


# ============================================================
# DECISION ENGINE
# ============================================================

class DecisionEngine:
    """Recommends optimal action with natural language explanation."""

    def recommend(self, twin: ClaimTwin,
                  strategies: List[SubmissionStrategy],
                  simulations: Dict[str, Dict] = None) -> Dict[str, Any]:
        """Generate final recommendation."""

        if not strategies:
            return {'recommendation': 'No strategies available'}

        best = strategies[0]  # Already sorted by net EV

        # Calculate uplift from optimization
        baseline = next((s for s in strategies if s.strategy_id == 'S1-BASELINE'), strategies[-1])
        uplift = best.net_expected_value - baseline.net_expected_value
        uplift_pct = (uplift / baseline.net_expected_value * 100) if baseline.net_expected_value > 0 else 0

        # Decision rationale
        if best.strategy_id == 'S1-BASELINE':
            rationale = ('Submit as-is. The claim is well-positioned and optimization '
                         'cost exceeds expected benefit.')
        elif uplift < 100:
            rationale = (f'Marginal benefit from optimization (${uplift:,.0f}). '
                         f'Submit as-is unless time permits the {best.name} approach.')
        else:
            rationale = (f'OPTIMIZE before submission. {best.name} yields '
                         f'${uplift:,.0f} additional expected value ({uplift_pct:.0f}% uplift) '
                         f'for ${best.cost_to_implement:,.0f} investment.')

        # Simulation summary
        sim_data = None
        if simulations and best.strategy_id in simulations:
            sim = simulations[best.strategy_id]
            sim_data = {
                'expected_payment': sim['payment_distribution']['mean'],
                'worst_case_5pct': sim['payment_distribution']['p5'],
                'best_case_95pct': sim['payment_distribution']['p95'],
                'zero_payment_risk': sim['payment_distribution']['zero_payment_rate'],
                'expected_days': sim['days_distribution']['mean'],
            }

        return {
            'recommended_strategy': best.strategy_id,
            'recommended_name': best.name,
            'recommended_actions': best.actions,
            'rationale': rationale,
            'financial_comparison': {
                'baseline_ev': baseline.net_expected_value,
                'optimized_ev': best.net_expected_value,
                'uplift': round(uplift, 2),
                'uplift_pct': round(uplift_pct, 1),
                'investment_required': best.cost_to_implement,
                'roi': round(uplift / best.cost_to_implement, 1) if best.cost_to_implement > 0 else float('inf'),
            },
            'risk_comparison': {
                'baseline_denial_prob': baseline.estimated_denial_prob,
                'optimized_denial_prob': best.estimated_denial_prob,
                'denial_reduction': round(baseline.estimated_denial_prob - best.estimated_denial_prob, 3),
            },
            'simulation': sim_data,
            'all_strategies': [s.to_dict() for s in strategies],
        }


# ============================================================
# DEMO
# ============================================================

def demo_twin() -> ClaimTwin:
    """Create a realistic claim twin for demo."""
    return ClaimTwin(
        claim_id='CLM-2026-US-001',
        clinical=ClinicalLayer(
            diagnoses=['E66.01', 'E11.65', 'I10', 'E78.5', 'G47.33'],
            procedures=['43775', '99223', '99233', '36620', '95250'],
            documentation_score=0.48,
            documentation_gaps=[
                'Medical necessity statement missing',
                'Step therapy compliance not explicitly documented',
                'BMI measurement not in current note (referenced from history)',
            ],
            drg_opportunities=[
                {'condition': 'aki_mcc', 'suggested_icd': 'N17.9',
                 'impact': 'DRG 619→621, +$8,200'},
                {'condition': 'encephalopathy_mcc', 'suggested_icd': 'G93.40',
                 'impact': 'DRG 619→621, +$8,200'},
            ],
            clinical_narrative_strength=0.55,
            objective_data_present=True,    # HbA1c, BMI, creatinine documented
            guideline_cited=True,           # ASMBS guidelines mentioned
            treatment_failure_documented=True,  # Failed conservative management
            informed_consent_present=False,
        ),
        regulatory=RegulatoryLayer(
            cms_coverage=True,
            ncd_reference='NCD 100.1 (Bariatric Surgery)',
            prior_auth_obtained=True,
            prior_auth_valid=True,
            prior_auth_matches_procedure=True,
            in_network=True,
            contract_covers_service=True,
            modifier_compliant=True,
            cci_edits_clear=True,
            two_midnight_met=True,
            applicable_regulations=[
                'CMS NCD 100.1',
                'ASMBS Clinical Practice Guidelines 2022',
            ],
        ),
        economic=EconomicLayer(
            billed_charges=58750,
            expected_reimbursement=14720,  # DRG 619 at contract rate
            expected_patient_responsibility=2500,
            drg_base_payment=14720,
            drg_with_optimization=22920,   # If AKI/encephalopathy coded → DRG 621
            carve_out_value=0,
            stop_loss_eligible=False,
            outlier_eligible=False,
            total_optimized_value=22920,
        ),
        behavioral=BehavioralLayer(
            payer_name='united_healthcare',
            payer_denial_rate=0.17,
            predicted_denial_probability=0.28,
            primary_attack_vector='CO-50',
            secondary_attack_vectors=['CO-4', 'CO-197'],
            appeal_success_probability=0.55,
            peer_to_peer_success_probability=0.62,
            expected_days_to_payment=45,
            temporal_risk_factor=1.0,
            payer_specific_warnings=[
                'UHC underpays E&M codes systematically 8-12%',
                'Bariatric claims require BMI in current note (not just history)',
            ],
        ),
    )


def main():
    import argparse
    parser = argparse.ArgumentParser(description='CLAIM DIGITAL TWIN')
    subparsers = parser.add_subparsers(dest='command')
    subparsers.add_parser('demo', help='Full twin analysis with demo claim')
    subparsers.add_parser('simulate', help='Monte Carlo simulation')

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    twin = demo_twin()
    strategy_engine = StrategyEngine()
    simulation_engine = SimulationEngine()
    decision_engine = DecisionEngine()

    strategies = strategy_engine.generate_strategies(twin)

    if args.command == 'demo':
        # Run simulations for top 3 strategies
        simulations = {}
        for s in strategies[:3]:
            simulations[s.strategy_id] = simulation_engine.simulate(twin, s)

        recommendation = decision_engine.recommend(twin, strategies, simulations)

        result = {
            'twin': twin.to_dict(),
            'recommendation': recommendation,
            'simulations': simulations,
        }
        print(json.dumps(result, indent=2, default=str))

    elif args.command == 'simulate':
        for s in strategies:
            sim = simulation_engine.simulate(twin, s, n_simulations=5000)
            print(f'\n=== {s.name} ===')
            print(f'  Expected payment: ${sim["payment_distribution"]["mean"]:,.0f}')
            print(f'  Worst case (5%):  ${sim["payment_distribution"]["p5"]:,.0f}')
            print(f'  Best case (95%):  ${sim["payment_distribution"]["p95"]:,.0f}')
            print(f'  Zero-payment:     {sim["payment_distribution"]["zero_payment_rate"]:.1%}')
            print(f'  Avg days:         {sim["days_distribution"]["mean"]:.0f}')
            print(f'  Cost-adjusted:    ${sim["cost_adjusted_mean"]:,.0f}')


if __name__ == '__main__':
    main()
