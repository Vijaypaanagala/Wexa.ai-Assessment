# Phase 1 smoke checklist

- [ ] `pip install -r requirements.txt`
- [ ] `python scripts/run_all.py --dry-run` prints all 5 platforms
- [ ] `python scripts/bench.py --platform cognodb --dry-run` prints footprint stub
- [ ] `.env` is gitignored; `.env.example` has no secrets
- [ ] README resource parity table present
- [ ] Results JSON schema documented under `results/README.md`
