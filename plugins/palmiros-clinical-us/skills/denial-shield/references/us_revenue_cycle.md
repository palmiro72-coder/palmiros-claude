# US Healthcare Revenue Cycle — Reference Guide

## 1. Why This Is a $10B+ Problem

US hospitals lose an estimated $262 billion annually to denied claims.
The average denial rate across commercial payers is 10-17%.
The average cost to rework a denied claim is $25-118 per claim.
Only 35-40% of denied claims are ever appealed.
Of those appealed, 50-65% are overturned.

The math: most denials are preventable, and most that slip through are winnable.
Hospitals just don't have the tooling to fight at scale.

## 2. Claim Lifecycle

```
Patient encounter
    → Charge capture (CPT/HCPCS codes assigned)
    → Coding review (ICD-10-CM diagnoses assigned)
    → Prior authorization verification
    → Claim scrubbing (edit checks)
    → Claim submission (837P or 837I)
    → Payer adjudication (5-45 days)
        → Paid (full or partial)
        → Denied (with CARC/RARC codes)
            → Appeal (if viable)
            → Write-off (if not)
```

Denial Shield intervenes at TWO points:
1. **Pre-submission** — catch errors before they become denials
2. **Post-adjudication** — detect underpayments and weaponize appeals

## 3. Coding System Hierarchy

### CPT (Current Procedural Terminology)
- Published by AMA
- 5-digit numeric codes for procedures/services
- Categories: E&M (99xxx), Surgery (1xxxx-6xxxx), Radiology (7xxxx), Path/Lab (8xxxx)

### ICD-10-CM (Diagnosis Codes)
- Published by WHO, US clinical modification by CMS
- Format: letter + digits (A00.0 - Z99.9)
- Required on every claim to justify medical necessity

### HCPCS (Healthcare Common Procedure Coding System)
- Level I = CPT codes
- Level II = alphanumeric (A0000-V9999) for drugs, DME, supplies

### DRG (Diagnosis Related Groups)
- Used for Medicare inpatient reimbursement
- Groups diagnoses/procedures into ~750 categories
- Each DRG has a weight → multiplied by hospital base rate → payment
- CC (Complication/Comorbidity) and MCC (Major CC) shift DRG higher

## 4. Payer Denial Taxonomy (CARC/RARC)

### CARC (Claim Adjustment Reason Codes)
Top denial codes by frequency:

| Code | Reason | Frequency | Preventable? |
|------|--------|-----------|-------------|
| CO-4 | Procedure not consistent with diagnosis | 25% | Yes — coding review |
| CO-50 | Not medically necessary | 20% | Yes — documentation |
| CO-197 | Prior auth missing | 18% | Yes — auth tracking |
| CO-16 | Missing information | 12% | Yes — scrubbing |
| CO-29 | Timely filing exceeded | 8% | Yes — submission tracking |
| CO-18 | Duplicate claim | 7% | Yes — duplicate detection |
| CO-97 | Already included in another procedure | 5% | Partially — CCI edits |

### Group Codes
- CO = Contractual Obligation (payer responsibility)
- PR = Patient Responsibility (patient owes)
- OA = Other Adjustment
- CR = Correction/Reversal

## 5. Regulatory Weapons

### CMS Interoperability Rule (CMS-0057-F, effective 2026)
- Payers MUST respond to prior auth within 72hrs (urgent) / 7 days (standard)
- Payers MUST provide specific denial reasons
- Applies to Medicare Advantage, Medicaid, CHIP, QHP

### No Surprises Act (P.L. 116-260)
- Protects against surprise out-of-network billing
- Independent Dispute Resolution (IDR) for payment disputes
- Qualifying Payment Amount (QPA) standard

### ERISA §503 (Employee Retirement Income Security Act)
- Requires "full and fair review" of denied claims
- Failure to comply = "deemed exhaustion" (patient can go directly to court)
- Applies to employer-sponsored health plans

### OIG Report OIG-22-06-11 (2022)
- Found 13% of Medicare Advantage prior auth denials were inappropriate
- Found 18% of MA payment denials were for claims that met Medicare rules
- Powerful citation in MA plan appeals

### Two-Midnight Rule (42 CFR §412.3)
- Inpatient admission appropriate when physician expects stay ≥ 2 midnights
- Common battleground: payers downcode to observation

### Mental Health Parity Act (MHPAEA)
- Payers cannot apply stricter criteria to mental health than medical
- Powerful for behavioral health denial appeals

## 6. Game Theory: The Hospital-Payer Dynamic

The payer has incentives to:
- Deny borderline claims (saves money)
- Delay payment (time value of money)
- Underpay silently (most hospitals don't check line items)
- Change policies quietly (via provider manual updates)
- Use third-party review companies (Evicore, AIM, Carelon) as shields

The hospital's counter-moves:
- Pre-submission scrubbing (prevent easy denials)
- Payer-specific documentation (give them what they audit)
- Strategic submission timing (avoid quarter-end pressure)
- Aggressive appeal with legal citations (raise the cost of denying)
- Underpayment detection (call out contract breaches)
- Peer-to-peer escalation (bypass automated denials)

## 7. DRG Optimization (Legal)

### The Difference Between Upcoding and Accurate Coding

**Upcoding** (illegal): Assigning codes for services not performed or
conditions not present. This is fraud.

**Accurate coding** (mandatory): Capturing ALL documented conditions
that affect care complexity. Failure to code documented conditions
is UNDERCODING — it shortchanges the hospital.

### Common Undercoding Patterns

1. **Malnutrition** — documented by dietitian but not coded → adds CC
2. **Acute kidney injury** — creatinine spike documented but not coded → adds MCC
3. **Encephalopathy** — "confusion" documented but not coded → adds MCC
4. **Sepsis** — meeting criteria but coded as simple infection → massive DRG shift
5. **Respiratory failure** — on supplemental O2 but not coded → adds MCC
6. **Diabetes with complications** — coded as "uncontrolled" instead of specific complication

### Financial Impact

A single missed MCC can shift DRG reimbursement by $5,000-15,000.
A systematic CDI program recovers $1,500-3,000 per case reviewed.

## 8. The $50B Underpayment Problem

Most hospitals focus on denials ($0 payments).
But underpayments (partial payments below contract) are often larger in aggregate.

Common underpayment patterns:
- E&M codes underpaid by 8-12%
- Implant reimbursement below cost
- Bundling professional + technical components without notice
- Applying wrong fee schedule (out-of-network rates on in-network claims)
- Ignoring contract escalators (annual rate increases not applied)

Detection requires comparing EVERY line item's `paid_amount` against
the contractual `allowed_amount`. Most hospitals don't do this.

## 9. Competitive Landscape (US Revenue Cycle AI)

| Company | Focus | Annual Revenue |
|---------|-------|---------------|
| Optum (UHG) | Full RCM + analytics | $20B+ |
| R1 RCM | End-to-end RCM | $2B+ |
| Waystar | Claim management | $800M+ |
| AKASA | AI-powered RCM | $100M+ (startup) |
| Olive AI | AI automation | Shut down 2023 |
| Infinx | Prior auth AI | $50M+ |
| Valer | Denial prevention AI | <$10M (early) |

Gap in market: most tools are REACTIVE (manage denials after they happen).
Very few do ADVERSARIAL PREDICTION (model payer behavior to prevent denials).
None combine all 8 modules in a single engine.
