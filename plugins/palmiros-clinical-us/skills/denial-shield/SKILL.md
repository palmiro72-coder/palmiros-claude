---
name: denial-shield
description: "Adversarial Revenue Intelligence Engine for US healthcare. Treats hospital-payer relationship as an adversarial game — profiles payer behavioral 'genomes', predicts denial attack vectors, detects underpayments, optimizes DRG, auto-generates appeals with legal citations, and recommends optimal submission timing. Use whenever the user mentions: denial management, revenue cycle, claim denial, prior authorization, CPT/ICD coding, payer behavior, appeal letter, underpayment, DRG optimization, CDI clinical documentation, medical necessity, CARC/RARC codes, timely filing, modifier 25, CMS LCD NCD, Medicare Advantage denial, revenue leakage, charge capture, or any US healthcare billing/reimbursement topic. Also use for competitive analysis of US healthtech RCM companies."
---

# Denial Shield — Adversarial Revenue Intelligence Engine

## Paradigm Shift

Traditional denial management is **reactive**: claim denied → investigate → appeal.

Denial Shield is **adversarial**: profile the opponent → predict their moves → prevent denials before submission → detect underpayments → weaponize appeals.

Think of it like chess against the payer. The Payer Genome tells you their opening book.

## 8 Modules

| # | Module | What It Does | Category |
|---|--------|-------------|----------|
| 1 | **RULES** | CPT/ICD-10 compatibility from external YAML | Denial Prevention |
| 2 | **GENOME** | Payer behavioral profiling & denial prediction | Adversarial Intel |
| 3 | **CDI** | Clinical documentation integrity analysis | Denial Prevention |
| 4 | **MISS** | Missing charges + underpayment detection | Revenue Recovery |
| 5 | **DRG** | DRG optimization through accurate coding | Revenue Recovery |
| 6 | **RISK** | Predictive denial scoring (ML-ready features) | Prioritization |
| 7 | **APPEAL** | Auto-generate appeals with legal citations | Denial Recovery |
| 8 | **TEMPO** | Optimal submission timing strategy | Denial Prevention |

## Quick Start

```bash
cp -r /mnt/skills/user/denial-shield/scripts/* /home/claude/
cp -r /mnt/skills/user/denial-shield/rules/* /home/claude/

# Install PyYAML for external rules
pip install pyyaml --break-system-packages

# Demo with realistic US hospital claim
python /home/claude/denial_shield.py demo

# Payer genome analysis
python /home/claude/denial_shield.py genome --payer united_healthcare

# Clinical documentation analysis
python /home/claude/denial_shield.py cdi --text "55yo male with morbid obesity..."

# Appeal strategy for CO-50 denial
python /home/claude/denial_shield.py appeal --denial-code CO-50 --input claim.json

# Submission timing
python /home/claude/denial_shield.py timing
```

## Key Innovation: Payer Genome

Each payer has a behavioral "genome" — a fingerprint of:
- Baseline denial rate
- Top denial codes and frequencies
- High-risk CPT families
- Prior auth strictness score
- Timely filing deadline
- Temporal patterns (quarter-end spikes, Monday surges)
- Contract tactics (silent amendments, bundling without notice)
- Effective counter-strategies (peer-to-peer success rates, regulatory leverage)

The genome turns denial management from guessing to game theory.

## Key Innovation: Underpayment Detection

Most hospitals only track **denials** (paid $0). But payers also **underpay** — paying 8-15% below contracted rates on individual line items. This silent revenue loss often exceeds denial losses.

The MISS module compares `allowed_amount` vs `paid_amount` per line to detect contract breaches.

## Key Innovation: Appeal Weaponization

Appeals succeed based on specificity. The APPEAL module generates targeted strategies citing:
- CMS NCDs/LCDs
- OIG reports on payer behavior (OIG-22-06-11)
- CMS Interoperability Rule (CMS-0057-F)
- No Surprises Act provisions
- ERISA full-and-fair-review requirements
- State prompt payment laws

Plus payer-specific counter-strategies from the genome.

## Key Innovation: Temporal Strategy

Denial rates follow temporal patterns:
- Monday surge (+30% prior auth denials)
- Quarter-end spike (+15-25% denial rate)
- Q4 audit season (RAC targeting)
- Policy lag (30-60 day propagation delay)

TEMPO module recommends when to submit, when to hold, and when to escalate.

## External Rules (YAML)

All rules live in `rules/denial_rules.yaml` for hot-reload:
- CPT/ICD-10 incompatibility rules
- Payer genomes
- DRG optimization triggers
- Documentation requirements
- CARC/RARC denial code intelligence
- Temporal patterns

Hospital billing teams can update rules without touching code.

## Payers Profiled

6 payer genomes with behavioral fingerprints:
- United Healthcare, Anthem BCBS, Aetna, Cigna
- Medicare Traditional, Medicare Advantage

## Output Format

```json
{
  "risk_score": { "risk_score": 0.68, "risk_level": "HIGH" },
  "payer_genome": { "attack_vectors": [...], "behavioral_warnings": [...] },
  "financial_summary": {
    "total_charges": 85000,
    "value_at_risk": 57800,
    "missed_revenue": 1250,
    "underpayment_detected": 3600,
    "total_financial_opportunity": 62650
  },
  "appeal_readiness": { "regulatory_citations": [...], "escalation_path": [...] },
  "timing_strategy": { "recommendation": "REVIEW TIMING" }
}
```

## References

- `references/us_revenue_cycle.md` — US healthcare billing primer, regulatory landscape
- `rules/denial_rules.yaml` — All external rules (hot-reloadable)

## v3.0 Modules: Contract Compiler + Claim Digital Twin

### Contract Compiler (`scripts/contract_compiler.py`)

The missing foundation — converts payer contracts into executable pricing logic.

```bash
# Price a CPT code against compiled contract
python /home/claude/contract_compiler.py price --cpt 43775 --charge 45000

# Price inpatient DRG
python /home/claude/contract_compiler.py drg --drg 619 --charge 58750 --los 7

# Full variance analysis (expected vs paid)
python /home/claude/contract_compiler.py demo
```

Components:
- **PricingEngine** — calculates expected reimbursement per contract rules
- **VarianceEngine** — classifies every dollar of difference by root cause (15 variance types)
- **RecoveryPrioritizer** — ranks recovery opportunities by net expected value minus cost to pursue

Supports: fee schedule, % of Medicare, DRG-based, per diem (tiered), case rate, cost-plus, carve-outs, implant markup with caps, modifier adjustments, stop-loss, outlier, lesser-of, annual escalators.

### Claim Digital Twin (`scripts/claim_twin.py`)

Each claim has a "twin" with 4 layers:
1. **Clinical** — documentation quality, DRG opportunities, medical necessity score
2. **Regulatory** — auth status, CCI compliance, CMS coverage, guideline defensibility
3. **Economic** — expected vs optimized reimbursement, carve-outs, stop-loss
4. **Behavioral** — payer denial probability, attack vectors, appeal success rates

```bash
# Full twin analysis with strategy recommendation
python /home/claude/claim_twin.py demo

# Monte Carlo simulation across all strategies
python /home/claude/claim_twin.py simulate
```

The twin generates 3-5 submission strategies and recommends the optimal play:
- Submit as-is (baseline)
- Strengthen documentation first
- Optimize coding (DRG shift via CDI query)
- Pre-emptive peer-to-peer
- Full optimization package

Monte Carlo simulation (1000+ runs) produces probability distributions of payment outcomes for each strategy.

## Roadmap

- v3.1: 835/837 EDI parser for automated claim/remittance ingestion
- v3.2: FHIR R4 integration for EHR clinical data
- v3.3: Network Genome — cross-institutional payer behavior intelligence
- v4.0: ML model trained on historical denial data (XGBoost/LightGBM)
- v4.1: Automated appeal letter generation with local LLM
- v5.0: Multi-hospital Revenue Intelligence Platform (SaaS)
