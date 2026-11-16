# Agent rules for sr-fastener

- This repo is **public**. Never commit secrets, tokens, personal or machine paths, or vendor CAD
  files (STEP, f3d, SLDPRT, and the like). `tools/check.py` scans for these.
- Work on a branch and open a PR. Never commit to `main`. Delete the branch once it is merged.
- Run `python tools/check.py` before every push. CI runs the same check.
- Dimension data lives in `tools/build_catalog.py`. Every family must cite its source URL.
  Never invent values. If a value is not confirmed, mark it `TBD`.
- Regenerate `SRFastener/data/catalog.json` with `python tools/build_catalog.py`. Never edit it by hand.
- Part numbers follow the shop hardware codes (see README). Finishes are `18-8 SS` and `18-8 SS-BO`.
- No washers or nuts unless the owner asks for them.
- Do not write assembly instructions such as tightening torque or threadlocker notes.
- Live Fusion tests: take the machine's Fusion lock first, and never touch other people's open documents.
  The smoke test closes its own design without saving.
