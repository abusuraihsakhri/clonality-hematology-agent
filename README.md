# Clonality Hematology Agent

A small Python research utility for deterministic review rules around clonality-assay metadata and workflow flags.

The current numeric thresholds are **compatibility defaults from the original project**. They are not validated EuroClonality/BIOMED-2 diagnostic cutoffs, and this repository should not be used to diagnose clonality or direct patient care. EuroClonality guidance emphasizes pattern-based interpretation, reproducibility, assay validation, and integration with morphologic, immunophenotypic, and clinical findings rather than fixed quantitative cutoffs.

## Features

- Single-record and CSV batch rule review.
- Canonical installable Python package and CLI.
- Optional FastAPI interface.
- Process-local HMAC-SHA256 audit trail in the legacy compatibility path.
- Heuristic identifier screening for common identifier patterns.
- Browser interface that runs the canonical Python rules client-side with Pyodide.
- Light/dark theme and responsive compact layout.

## Use

Requires Python 3.10 or newer.

```bash
python -m pip install -e .
clonality-hematology-engine audit --case-id CASE-001 --primary 15 --secondary 5 --status NORMAL
clonality-hematology-engine batch -i sample.csv -o results.csv
```

For the optional API:

```bash
python -m pip install -e ".[server]"
clonality-hematology-engine serve
```

The legacy `cli.py` and `clono_mind.py` entry points remain for compatibility, but new work should use the `clonality_hematology_agent` package.

## Browser application

The `web/` interface loads Pyodide and executes the package's Python rule engine in the browser. Case inputs are not submitted to an application server. The browser still downloads the Pyodide runtime from jsDelivr on first load.

GitHub Pages deployment is automated through `.github/workflows/pages.yml`. The verified live URL is added here after deployment is confirmed.

## Security and data handling

The legacy identifier guard is a **heuristic pattern screen**, not a complete PHI detector or a HIPAA Safe Harbor implementation. Do not rely on it as a de-identification control.

The audit trail uses an HMAC key from `AUDIT_SECRET_KEY` when provided. If the variable is absent, a random process-local key is generated. The verifier recomputes each HMAC and checks chain linkage.

No API keys or external model providers are required. Non-mock model-provider names fail closed rather than silently falling back.

## Testing

```bash
python -m pip install -e ".[server,dev]"
python -m pytest -q
python -m compileall -q clonality_hematology_agent agents clono_mind.py enrichment.py cli.py
node --check web/app.js
python -m pip_audit
```

CI runs on Python 3.10, 3.11, and 3.12.

## Scientific context

The rule engine is intentionally not presented as a clinical interpretation algorithm. For the interpretation and reporting framework used in Ig/TCR clonality testing, see:

- Langerak AW, et al. *EuroClonality/BIOMED-2 guidelines for interpretation and reporting of Ig/TCR clonality testing in suspected lymphoproliferations.* Leukemia. 2012;26:2159-2171. doi:10.1038/leu.2012.246

## Technology

Python, optional FastAPI/Pydantic/Uvicorn, vanilla HTML/CSS/JavaScript, and Pyodide for browser-side Python execution.

## License

MIT. See [LICENSE](LICENSE).
