# Results

- `published/` — committed per-platform JSON + `summary.csv` + `matrix.json` (runner schema v1)
- `runs/` — local live benchmark outputs (gitignored)

Rebuild published artifacts:

```powershell
python scripts\build_results.py
python scripts\aggregate_results.py
python scripts\plot_results.py
```

Replace any `published/<platform>.json` with a live `results/runs/*.json` file of the same schema, then re-run aggregate + plot.
