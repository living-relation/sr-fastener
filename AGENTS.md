# Agent rules for sr-fastener

- This repo is **public**. Never commit secrets, tokens, personal or machine paths, or vendor CAD
  files (STEP, f3d, SLDPRT, and the like). `tools/check.py` scans for these.
- Work on a branch and open a PR. Never commit to `main`. Delete the branch once it is merged.
- Run `python tools/check.py` before every push. CI runs the same check.
- Dimension data lives in `tools/build_catalog.py`. Every family must cite its sources (dims, lengths, thread, alloy), and `tests/test_sources.py` must check at least one row per table.
  Never invent values. If a value is not confirmed, mark it `TBD`.
- Regenerate `SRFastener/data/catalog.json` with `python tools/build_catalog.py`. Never edit it by hand.
- Part numbers follow the shop hardware codes only (type code + size + length + finish; washers add the outside diameter, nuts carry only size and thread; see README). Never set the Fusion part number, component name or description to a McMaster or other vendor number; cite those only in `docs/SOURCES.md` as dimension sources. Finishes are `18-8 SS`, `18-8 SS-BO`, `ALLOY-BO` (alloy only where a cited maker sells that size; give the grade), and per type `STL`, `ZN`, `GR8` (inch), `CL10.9` (metric screws) and `CL10` (metric nuts) where McMaster sells that type in it. List combinations left off in `LEFT_OFF` in `tools/build_catalog.py`.
- Descriptions are `Type, size and thread, material`: capitalized words, no standards (ISO, ASME, DIN and the like) and no dimensions. Material names have no alloy numbers or acronyms. No wedge lock washers.
- Type names and codes come from McMaster-Carr's category names (screws: S + head letter + H; set screws: SS + tip letter).
- New screw, nut and washer types are pre-approved: add any missing type once its data is checked against McMaster-Carr or Fastenal and cited. List the ones not built yet in `docs/MISSING-SCREWS.md`.
- Do not write assembly instructions such as tightening torque or threadlocker notes.
- Live Fusion tests: take the machine's Fusion lock first, and never touch other people's open documents.
  The smoke test closes its own design without saving.
- This is the only agent rules file in the repo. Do not add a CLAUDE.md or any other agent file; put rules here.
