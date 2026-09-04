# Clonality Hematology Agent (ClonoMind)

> **Domain:** Hematopathology, Molecular Diagnostics & Clinical Decision Support (BIOMED-2 / EuroClonality)  
> **Reference Standards:** WHO 5th Edition Classification of Haematolymphoid Tumours (2022) / ICC (2022), EuroClonality / BIOMED-2 Guidelines, CAP / CLSI / ISO 15189 Quality Standards

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![CI/CD](https://img.shields.io/badge/CI%2FCD-Passing-brightgreen.svg)

</div>

---

## 📖 Overview & Clinical Purpose

**Clonality Hematology Agent** (ClonoMind) is an enterprise clinical decision support and analytical multi-agent system designed for hematopathology laboratories. It analyzes B-cell and T-cell receptor gene rearrangement clonality assays (capillary electrophoresis fragment analysis and next-generation sequencing), distinguishing true monoclonal expansions from polyclonal reactive backgrounds in accordance with **EuroClonality / BIOMED-2** criteria and **WHO 5th Edition / ICC (2022)** hematolymphoid classifications.

The system incorporates:
- Multi-target assessment across immunoglobulin loci (**IGH**, **IGK**, **IGL**) and T-cell receptor loci (**TCRB**, **TCRG**, **TCRD**).
- Automated capillary electrophoresis peak-to-background ratio analysis, Gaussian distribution fit, and duplicate-tube peak reproducibility confirmation.
- Minimal Residual Disease (**MRD**) sensitivity tracking and clonal evolution profiling.
- Air-gapped **Zero-PHI Outbound Guards** blocking PHI/PII leakage (HIPAA Safe Harbor).
- Tamper-evident **HMAC-SHA256 audit trails** ensuring chain-of-custody compliance under CAP and ISO 15189 regulations.

---

## 🔬 Clinical Diagnostic Standards & Formulas

### 1. EuroClonality / BIOMED-2 Monoclonality Criteria

A peak in capillary fragment analysis is designated as clonal when it satisfies standard height and ratio criteria relative to the polyclonal background and duplicate PCR reactions:

```
Peak Ratio (R_peak) = H_dominant / H_polyclonal_background

Duplicate Peak Delta (Delta_dup) = |H_dominant_A - H_dominant_B| / max(H_dominant_A, H_dominant_B)
```

```
+-------------------------------------------------------------------------------------------+
|                           EuroClonality BIOMED-2 Diagnostic Matrix                       |
+-------------------+-----------------+---------------------------+-------------------------+
| Target Locus      | Tube / Primer   | Target Size Range (bp)    | Interpretation Threshold|
+-------------------+-----------------+---------------------------+-------------------------+
| IGH (VH-JH)       | Tube A (FR1-JH) | 310 - 360 bp              | Peak Ratio > 2.5x bkgd  |
| IGH (VH-JH)       | Tube B (FR2-JH) | 250 - 295 bp              | Peak Ratio > 2.5x bkgd  |
| IGH (VH-JH)       | Tube C (FR3-JH) | 100 - 170 bp              | Peak Ratio > 2.5x bkgd  |
| IGK (Vk-Jk / Kde) | Tube A (Vk-Jk)  | 120 - 160, 190 - 210 bp   | Peak Ratio > 2.0x bkgd  |
| IGK (Vk-Kde)      | Tube B (Vk-Kde) | 210 - 250, 270 - 300 bp   | Peak Ratio > 2.0x bkgd  |
| TCRG (Vg-Jg)      | Tube A (Vg1-8)  | 160 - 255 bp              | Dominant / subdominant  |
| TCRG (Vg-Jg)      | Tube B (Vg9/11) | 80 - 130 bp               | Dominant / subdominant  |
| TCRB (Vb-Jb)      | Tube A, B, C    | 240 - 285, 170 - 210 bp   | Distinct reproducible   |
+-------------------+-----------------+---------------------------+-------------------------+
```

### 2. Clinical Urgency & Triage Categorization

```
+--------------------------+---------------------+------------------------------------------+
| Urgency Tier             | Integrity Status    | Clinical Action / Protocol               |
+--------------------------+---------------------+------------------------------------------+
| ROUTINE                  | VALIDATED_OPTIMAL   | Gaussian polyclonal distribution; report |
| ELEVATED_RISK            | DISCORDANT_ANOMALY  | Equivocal / oligoclonal; reflex test     |
| CRITICAL_STAT_PANIC      | RECALIBRATION_REQ   | High dominant clone with STAT priority;  |
|                          |                     | immediate verbal pathology escalation    |
+--------------------------+---------------------+------------------------------------------+
```

---

## ⚙️ Multi-Agent Architecture

```
                 +-----------------------------------+
                 |        SystemTaskPayload          |
                 | (Sample / Assay Measurements)     |
                 +-----------------+-----------------+
                                   |
                         [ Zero-PHI Guard ]
                                   |
                                   v
                 +-----------------------------------+
                 |         SystemSupervisor          |
                 +--------+-----------------+--------+
                          |                 |
         +----------------+                 +----------------+
         |                                                   |
         v                                                   v
+------------------------+  +------------------------+  +------------------------+
|   InvariantQCWorker    |  | SafetyEscalationWorker |  |ProtocolConformanceWrkr |
|  - Primary peak metric |  |  - STAT alert triggers |  |  - Discordance triage  |
|  - Baseline calibration|  |  - Urgent escalations  |  |  - Anomaly flags       |
+-----------+------------+  +-----------+------------+  +-----------+------------+
            |                           |                           |
            +---------------------------+---------------------------+
                                        |
                                        v
                    +---------------------------------------+
                    |    ConsensusDossier & Audit Logger    |
                    | (HMAC-SHA256 Cryptographic Integrity) |
                    +---------------------------------------+
```

- **InvariantQCWorker:** Analyzes capillary electrophoresis peak ratios, baseline signal-to-noise thresholds, and reagent calibration indices.
- **SafetyEscalationWorker:** Monitors STAT clinical alerts, high-burden clonal emergence, and urgent specimen escalations.
- **ProtocolConformanceWorker:** Validates nomenclature consistency, biomarker concordance, and identifies discordant anomalies requiring reflex testing.
- **SystemSupervisor:** Synthesizes multi-worker evidence into an executive `ConsensusDossier` and writes cryptographically signed HMAC audit blocks.

---

## 💻 CLI Quickstart & Usage

The application provides a command-line interface via `cli.py` for audit analysis, query processing, verification, and high-throughput batch CSV processing.

### 1. Single Assay Case Evaluation (`audit`)
```bash
python cli.py audit --task-id CASE-IGH-001 --target SYNTH-PT-BCELL-01 --primary 28.5 --secondary 14.2 --critical --status DISCORDANT
```

### 2. Supervisory Query (`chat`)
```bash
python cli.py chat Explain the EuroClonality BIOMED-2 criteria for IGH clonal evaluation
```

### 3. Cryptographic Audit Trail Verification (`verify-audit`)
```bash
python cli.py verify-audit
```

### 4. High-Throughput Batch Processing (`batch`)
Execute batch evaluation on specimen datasets:
```bash
python cli.py batch -i sample.csv -o results.csv
```

### Batch CSV Schema Reference

| Column Header | Type | Description | Example |
|:--------------|:-----|:------------|:--------|
| `case_id` / `task_id` | String | Unique specimen / accession identifier | `CASE-IGH-001` |
| `patient_synthetic_id` / `target_identifier` | String | De-identified synthetic patient key (Zero-PHI compliant) | `SYNTH-PT-BCELL-01` |
| `metric_primary` / `primary_metric` | Float | Dominant peak height / fragment ratio ($R_{peak}$) | `28.6` |
| `metric_secondary` / `secondary_metric` | Float | Background noise level / duplicate variance ($\%$) | `14.5` |
| `is_stat` / `is_critical_flag` | Boolean | STAT priority escalation flag | `True` |
| `status_flag` / `status_descriptor` | String | Clinical phenotype / initial finding | `DISCORDANT_MONOCLONAL` |

---

## 🛡️ Security, Governance & Verification

- **Zero-PHI Interception:** Regex patterns intercept Medical Record Numbers (MRN), Social Security Numbers (SSN), patient names, and dates of birth.
- **Cryptographic Audit Trail:** Chained HMAC-SHA256 signatures link each audit decision with actor identification and hash verification.
- **Air-Gapped LLM Adapter:** Compatible with local, offline reasoning endpoints without data egress.

### Running Test Suite
Execute the automated test suite:
```bash
python -m pytest -p no:zarr -v
```

### Running Batch Smoke Verification
Verify end-to-end batch evaluation:
```bash
python cli.py batch -i sample.csv -o out_smoke.csv
python -c "import os; assert os.path.getsize('out_smoke.csv') > 0; print('Smoke verification succeeded.')"
```

---

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
