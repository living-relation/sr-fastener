# Agent rules for sr-fastener

- This repo is **public**. Never commit secrets, tokens, personal or machine paths, or vendor CAD
  files (STEP, f3d, SLDPRT, and the like). `tools/check.py` scans for these.
- Work on a branch and open a PR. Never commit to `main`. Delete the branch once it is merged.
- Run `python tools/check.py` before every push. CI runs the same check.
- Dimension data lives in `tools/build_catalog.py`. Every family must cite its sources (dims, lengths, thread, alloy), and `tests/test_sources.py` must check at least one row per table.
  Never invent values. If a value is not confirmed, mark it `TBD`.
- Regenerate `SRFastener/data/catalog.json` with `python tools/build_catalog.py`. Never edit it by hand.
- Part numbers follow the shop hardware codes (see README). Finishes are `18-8 SS`, `18-8 SS-BO` and `ALLOY-BO` (alloy only where a cited maker sells that size; give the grade).
- Type names and codes come from McMaster-Carr's category names (screws: S + head letter + H; set screws: SS + tip letter).
- New screw, nut and washer types are pre-approved: add any missing type once its data is checked against McMaster-Carr or Fastenal and cited. List the ones not built yet in `docs/MISSING-SCREWS.md`.
- Do not write assembly instructions such as tightening torque or threadlocker notes.
- Live Fusion tests: take the machine's Fusion lock first, and never touch other people's open documents.
  The smoke test closes its own design without saving.
