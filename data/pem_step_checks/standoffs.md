# PEM standoff model check (SO, SOS, BSO, BSOS)

Checked 2026-11-24 against the metric rows in `tools/pem_press.py` on branch `dan_cursor/pem-press-in-cadf` (commit `2882a0d`).
Pass means the measured number is within 0.05 mm of the catalog number. This report does not change the catalog.

## What was actually measured

An official STEP file was not downloaded. PennEngineering serves the model through TraceParts on catalog.pemnet.com. The STEP, IGES, and SAT buttons sit behind a form that requires an email, first name, last name, company, job title, city, postal code, and phone. That form was not filled in.

The same page draws the part without that form. The drawing file is a VRML mesh whose header says `VRML model created from Acis model`. It is the tessellation of the official ACIS solid. Each of the 40 parts below was read from that viewer.

The mesh has no millimeter unit. The viewer stretches the longest side of the part to exactly 2.0. Millimeters in the table use catalog length L as the ruler (the length the model was configured with). Hex size, body diameter, and thread major are then read on that scale. Overall length is checked the other way: set the hex across flats to catalog H, and read the length. Those two checks are the same proportion, shown both ways so each catalog number has a column.

cadquery, OCP, and FreeCAD were not used. They read STEP solids, and the only public official file is this mesh. The numbers below come from the mesh vertices (points that sit on the ACIS faces).

The mesh is sparse. Long faces only have vertices where the shape changes, so a short groove can be missing. What is there:

- One end is a hex cap about 0.50 mm thick. Across flats is H. Across corners follows a regular hex: the ratio of the two cross-section spans is 1.1544 to 1.1569 on every part, and a regular hex is 1.1547.
- The rest of the body is a round cylinder whose diameter is C.
- This is not a full-length hex body. The SO datasheet figure is a hex body with a short clinch shank. This ACIS mesh has a short hex cap and a long round body at diameter C. H, L, and C still land on the catalog numbers. A pass on H does not mean the hex runs the full length.
- Thru-hole parts (SO, SOS) are open at both ends. The opening diameter is the thread major. A ring near the ISO minor diameter sits just inside each end. There is no helix, so pitch cannot be measured.
- Blind parts (BSO, BSOS) are closed at the hex end. The hole starts at the round end and ends at a point. That hole is deeper than catalog F.
- No cylinder at the counterbore diameter B. No separate clinch shank shorter than the body.

Steel and stainless pairs (SO with SOS, BSO with BSOS) are separate meshes and measure the same to 0.001 mm. The mesh has no material.

Two lengths, 6 mm and 16 mm, cover each of the five metric thread codes in the standoff table (M3, 3.5M3, M3.5, M4, M5) and each of the four families.

The source URL is the viewer page. The mesh bytes come from a short-lived cache link under `/cache/Geomstore/` and that link changes every view, so the file is not stored in this repo. PEM does not offer that viewer file for redistribution. The repo check also rejects STEP, IGES, and SAT files.

## Results

Each cell is measured / catalog / delta / pass or fail.

Length uses catalog H as the ruler. Hex, C, and thread major use catalog L as the ruler. Blind depth is the hole from the open (round) end to the drill point, compared with catalog F. F is published as a minimum, not a single target.

| Part | Source | Hex across flats H | Body dia C | Thread major | Overall length L | Blind hole vs F | Pitch | Counterbore B | Hex cap thickness |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SO-M3-6ZI | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=so-m3-6zi | 4.800 / 4.800 / +0.000 / pass | 4.200 / 4.200 / +0.000 / pass | 3.000 / 3.000 / +0.000 / pass | 6.000 / 6.000 / -0.000 / pass | n/a (thru-hole) | not in mesh | not in mesh | 0.50 mm, no catalog value |
| SO-M3-16ZI | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=so-m3-16zi | 4.792 / 4.800 / -0.008 / pass | 4.193 / 4.200 / -0.007 / pass | 2.995 / 3.000 / -0.005 / pass | 16.027 / 16.000 / +0.027 / pass | n/a (thru-hole) | not in mesh | not in mesh | 0.50 mm, no catalog value |
| SO-3.5M3-6ZI | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=so-3-5m3-6zi | 6.403 / 6.400 / +0.003 / pass | 5.402 / 5.390 / +0.012 / pass | 3.001 / 3.000 / +0.001 / pass | 5.997 / 6.000 / -0.003 / pass | n/a (thru-hole) | not in mesh | not in mesh | 0.50 mm, no catalog value |
| SO-3.5M3-16ZI | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=so-3-5m3-16zi | 6.392 / 6.400 / -0.008 / pass | 5.393 / 5.390 / +0.003 / pass | 2.996 / 3.000 / -0.004 / pass | 16.020 / 16.000 / +0.020 / pass | n/a (thru-hole) | not in mesh | not in mesh | 0.50 mm, no catalog value |
| SO-M3.5-6ZI | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=so-m3-5-6zi | 6.403 / 6.400 / +0.003 / pass | 5.402 / 5.390 / +0.012 / pass | 3.482 / 3.500 / -0.018 / pass | 5.997 / 6.000 / -0.003 / pass | n/a (thru-hole) | not in mesh | not in mesh | 0.50 mm, no catalog value |
| SO-M3.5-16ZI | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=so-m3-5-16zi | 6.392 / 6.400 / -0.008 / pass | 5.393 / 5.390 / +0.003 / pass | 3.516 / 3.500 / +0.016 / pass | 16.020 / 16.000 / +0.020 / pass | n/a (thru-hole) | not in mesh | not in mesh | 0.50 mm, no catalog value |
| SO-M4-6ZI | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=so-m4-6zi | 7.897 / 7.900 / -0.003 / pass | 7.117 / 7.120 / -0.003 / pass | 3.998 / 4.000 / -0.002 / pass | 6.003 / 6.000 / +0.003 / pass | n/a (thru-hole) | not in mesh | not in mesh | 0.50 mm, no catalog value |
| SO-M4-16ZI | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=so-m4-16zi | 7.896 / 7.900 / -0.004 / pass | 7.116 / 7.120 / -0.004 / pass | 3.998 / 4.000 / -0.002 / pass | 16.008 / 16.000 / +0.008 / pass | n/a (thru-hole) | not in mesh | not in mesh | 0.50 mm, no catalog value |
| SO-M5-6ZI | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=so-m5-6zi | 7.897 / 7.900 / -0.003 / pass | 7.117 / 7.120 / -0.003 / pass | 4.998 / 5.000 / -0.002 / pass | 6.003 / 6.000 / +0.003 / pass | n/a (thru-hole) | not in mesh | not in mesh | 0.50 mm, no catalog value |
| SO-M5-16ZI | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=so-m5-16zi | 7.896 / 7.900 / -0.004 / pass | 7.116 / 7.120 / -0.004 / pass | 4.997 / 5.000 / -0.003 / pass | 16.008 / 16.000 / +0.008 / pass | n/a (thru-hole) | not in mesh | not in mesh | 0.50 mm, no catalog value |
| SOS-M3-6 | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=sos-m3-6 | 4.800 / 4.800 / +0.000 / pass | 4.200 / 4.200 / +0.000 / pass | 3.000 / 3.000 / +0.000 / pass | 6.000 / 6.000 / -0.000 / pass | n/a (thru-hole) | not in mesh | not in mesh | 0.50 mm, no catalog value |
| SOS-M3-16 | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=sos-m3-16 | 4.792 / 4.800 / -0.008 / pass | 4.193 / 4.200 / -0.007 / pass | 2.995 / 3.000 / -0.005 / pass | 16.027 / 16.000 / +0.027 / pass | n/a (thru-hole) | not in mesh | not in mesh | 0.50 mm, no catalog value |
| SOS-3.5M3-6 | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=sos-3-5m3-6 | 6.403 / 6.400 / +0.003 / pass | 5.402 / 5.390 / +0.012 / pass | 3.001 / 3.000 / +0.001 / pass | 5.997 / 6.000 / -0.003 / pass | n/a (thru-hole) | not in mesh | not in mesh | 0.50 mm, no catalog value |
| SOS-3.5M3-16 | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=sos-3-5m3-16 | 6.392 / 6.400 / -0.008 / pass | 5.393 / 5.390 / +0.003 / pass | 2.996 / 3.000 / -0.004 / pass | 16.020 / 16.000 / +0.020 / pass | n/a (thru-hole) | not in mesh | not in mesh | 0.50 mm, no catalog value |
| SOS-M3.5-6 | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=sos-m3-5-6 | 6.403 / 6.400 / +0.003 / pass | 5.402 / 5.390 / +0.012 / pass | 3.482 / 3.500 / -0.018 / pass | 5.997 / 6.000 / -0.003 / pass | n/a (thru-hole) | not in mesh | not in mesh | 0.50 mm, no catalog value |
| SOS-M3.5-16 | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=sos-m3-5-16 | 6.392 / 6.400 / -0.008 / pass | 5.393 / 5.390 / +0.003 / pass | 3.516 / 3.500 / +0.016 / pass | 16.020 / 16.000 / +0.020 / pass | n/a (thru-hole) | not in mesh | not in mesh | 0.50 mm, no catalog value |
| SOS-M4-6 | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=sos-m4-6 | 7.897 / 7.900 / -0.003 / pass | 7.117 / 7.120 / -0.003 / pass | 3.998 / 4.000 / -0.002 / pass | 6.003 / 6.000 / +0.003 / pass | n/a (thru-hole) | not in mesh | not in mesh | 0.50 mm, no catalog value |
| SOS-M4-16 | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=sos-m4-16 | 7.896 / 7.900 / -0.004 / pass | 7.116 / 7.120 / -0.004 / pass | 3.998 / 4.000 / -0.002 / pass | 16.008 / 16.000 / +0.008 / pass | n/a (thru-hole) | not in mesh | not in mesh | 0.50 mm, no catalog value |
| SOS-M5-6 | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=sos-m5-6 | 7.897 / 7.900 / -0.003 / pass | 7.117 / 7.120 / -0.003 / pass | 4.998 / 5.000 / -0.002 / pass | 6.003 / 6.000 / +0.003 / pass | n/a (thru-hole) | not in mesh | not in mesh | 0.50 mm, no catalog value |
| SOS-M5-16 | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=sos-m5-16 | 7.896 / 7.900 / -0.004 / pass | 7.116 / 7.120 / -0.004 / pass | 4.997 / 5.000 / -0.003 / pass | 16.008 / 16.000 / +0.008 / pass | n/a (thru-hole) | not in mesh | not in mesh | 0.50 mm, no catalog value |
| BSO-M3-6ZI | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=bso-m3-6zi | 4.800 / 4.800 / +0.000 / pass | 4.200 / 4.200 / +0.000 / pass | 3.000 / 3.000 / +0.000 / pass | 6.000 / 6.000 / -0.000 / pass | 5.29 / 3.2 / +2.09 / fail | not in mesh | not in mesh | 0.50 mm, no catalog value |
| BSO-M3-16ZI | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=bso-m3-16zi | 4.792 / 4.800 / -0.008 / pass | 4.193 / 4.200 / -0.007 / pass | 2.995 / 3.000 / -0.005 / pass | 16.027 / 16.000 / +0.027 / pass | 11.94 / 6.5 / +5.44 / fail | not in mesh | not in mesh | 0.50 mm, no catalog value |
| BSO-3.5M3-6ZI | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=bso-3-5m3-6zi | 6.403 / 6.400 / +0.003 / pass | 5.402 / 5.390 / +0.012 / pass | 3.001 / 3.000 / +0.001 / pass | 5.997 / 6.000 / -0.003 / pass | 5.29 / 3.2 / +2.09 / fail | not in mesh | not in mesh | 0.50 mm, no catalog value |
| BSO-3.5M3-16ZI | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=bso-3-5m3-16zi | 6.392 / 6.400 / -0.008 / pass | 5.393 / 5.390 / +0.003 / pass | 2.996 / 3.000 / -0.004 / pass | 16.020 / 16.000 / +0.020 / pass | 11.94 / 6.5 / +5.44 / fail | not in mesh | not in mesh | 0.50 mm, no catalog value |
| BSO-M3.5-6ZI | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=bso-m3-5-6zi | 6.403 / 6.400 / +0.003 / pass | 5.402 / 5.390 / +0.012 / pass | 3.482 / 3.500 / -0.018 / pass | 5.997 / 6.000 / -0.003 / pass | 5.39 / 3.2 / +2.19 / fail | not in mesh | not in mesh | 0.50 mm, no catalog value |
| BSO-M3.5-16ZI | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=bso-m3-5-16zi | 6.392 / 6.400 / -0.008 / pass | 5.393 / 5.390 / +0.003 / pass | 3.516 / 3.500 / +0.016 / pass | 16.020 / 16.000 / +0.020 / pass | 12.04 / 6.5 / +5.54 / fail | not in mesh | not in mesh | 0.50 mm, no catalog value |
| BSO-M4-6ZI | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=bso-m4-6zi | 7.897 / 7.900 / -0.003 / pass | 7.117 / 7.120 / -0.003 / pass | 3.998 / 4.000 / -0.002 / pass | 6.003 / 6.000 / +0.003 / pass | 5.51 / 3.2 / +2.31 / fail | not in mesh | not in mesh | 0.50 mm, no catalog value |
| BSO-M4-16ZI | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=bso-m4-16zi | 7.896 / 7.900 / -0.004 / pass | 7.116 / 7.120 / -0.004 / pass | 3.998 / 4.000 / -0.002 / pass | 16.008 / 16.000 / +0.008 / pass | 12.16 / 6.5 / +5.66 / fail | not in mesh | not in mesh | 0.50 mm, no catalog value |
| BSO-M5-6ZI | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=bso-m5-6zi | 7.897 / 7.900 / -0.003 / pass | 7.117 / 7.120 / -0.003 / pass | 4.998 / 5.000 / -0.002 / pass | 6.003 / 6.000 / +0.003 / pass | 5.76 / 3.2 / +2.56 / fail | not in mesh | not in mesh | 0.50 mm, no catalog value |
| BSO-M5-16ZI | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=bso-m5-16zi | 7.896 / 7.900 / -0.004 / pass | 7.116 / 7.120 / -0.004 / pass | 4.997 / 5.000 / -0.003 / pass | 16.008 / 16.000 / +0.008 / pass | 12.40 / 6.5 / +5.90 / fail | not in mesh | not in mesh | 0.50 mm, no catalog value |
| BSOS-M3-6 | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=bsos-m3-6 | 4.800 / 4.800 / +0.000 / pass | 4.200 / 4.200 / +0.000 / pass | 3.000 / 3.000 / +0.000 / pass | 6.000 / 6.000 / -0.000 / pass | 5.29 / 3.2 / +2.09 / fail | not in mesh | not in mesh | 0.50 mm, no catalog value |
| BSOS-M3-16 | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=bsos-m3-16 | 4.792 / 4.800 / -0.008 / pass | 4.193 / 4.200 / -0.007 / pass | 2.995 / 3.000 / -0.005 / pass | 16.027 / 16.000 / +0.027 / pass | 11.94 / 6.5 / +5.44 / fail | not in mesh | not in mesh | 0.50 mm, no catalog value |
| BSOS-3.5M3-6 | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=bsos-3-5m3-6 | 6.403 / 6.400 / +0.003 / pass | 5.402 / 5.390 / +0.012 / pass | 3.001 / 3.000 / +0.001 / pass | 5.997 / 6.000 / -0.003 / pass | 5.29 / 3.2 / +2.09 / fail | not in mesh | not in mesh | 0.50 mm, no catalog value |
| BSOS-3.5M3-16 | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=bsos-3-5m3-16 | 6.392 / 6.400 / -0.008 / pass | 5.393 / 5.390 / +0.003 / pass | 2.996 / 3.000 / -0.004 / pass | 16.020 / 16.000 / +0.020 / pass | 11.94 / 6.5 / +5.44 / fail | not in mesh | not in mesh | 0.50 mm, no catalog value |
| BSOS-M3.5-6 | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=bsos-m3-5-6 | 6.403 / 6.400 / +0.003 / pass | 5.402 / 5.390 / +0.012 / pass | 3.482 / 3.500 / -0.018 / pass | 5.997 / 6.000 / -0.003 / pass | 5.39 / 3.2 / +2.19 / fail | not in mesh | not in mesh | 0.50 mm, no catalog value |
| BSOS-M3.5-16 | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=bsos-m3-5-16 | 6.392 / 6.400 / -0.008 / pass | 5.393 / 5.390 / +0.003 / pass | 3.516 / 3.500 / +0.016 / pass | 16.020 / 16.000 / +0.020 / pass | 12.04 / 6.5 / +5.54 / fail | not in mesh | not in mesh | 0.50 mm, no catalog value |
| BSOS-M4-6 | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=bsos-m4-6 | 7.897 / 7.900 / -0.003 / pass | 7.117 / 7.120 / -0.003 / pass | 3.998 / 4.000 / -0.002 / pass | 6.003 / 6.000 / +0.003 / pass | 5.51 / 3.2 / +2.31 / fail | not in mesh | not in mesh | 0.50 mm, no catalog value |
| BSOS-M4-16 | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=bsos-m4-16 | 7.896 / 7.900 / -0.004 / pass | 7.116 / 7.120 / -0.004 / pass | 3.998 / 4.000 / -0.002 / pass | 16.008 / 16.000 / +0.008 / pass | 12.16 / 6.5 / +5.66 / fail | not in mesh | not in mesh | 0.50 mm, no catalog value |
| BSOS-M5-6 | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=bsos-m5-6 | 7.897 / 7.900 / -0.003 / pass | 7.117 / 7.120 / -0.003 / pass | 4.998 / 5.000 / -0.002 / pass | 6.003 / 6.000 / +0.003 / pass | 5.76 / 3.2 / +2.56 / fail | not in mesh | not in mesh | 0.50 mm, no catalog value |
| BSOS-M5-16 | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=bsos-m5-16 | 7.896 / 7.900 / -0.004 / pass | 7.116 / 7.120 / -0.004 / pass | 4.997 / 5.000 / -0.003 / pass | 16.008 / 16.000 / +0.008 / pass | 12.40 / 6.5 / +5.90 / fail | not in mesh | not in mesh | 0.50 mm, no catalog value |

Shank length is not a catalog field. `pem_press.py` stores C, not a shank length. In this mesh the diameter-C surface is the long round body (about L minus the 0.50 mm hex cap), not a short clinch pilot. Minimum sheet (1.00 mm, or 1.27 mm for M4 and M5) is a sheet limit, not a shank length, so it is not scored.

## Summary

- 40 official viewer meshes: two lengths (6 mm and 16 mm) for every metric thread in SO, SOS, BSO, and BSOS.
- Hex across flats, overall length, body diameter C, and thread major all pass within 0.05 mm.
- Thread pitch is not in the mesh.
- Counterbore B is not in the mesh.
- Hex cap thickness measures 0.50 mm on every part. The catalog does not publish a head thickness.
- All 20 blind holes fail a 0.05 mm match to F. The hole is deeper than the catalog minimum: about 5.3 to 5.8 mm on a 6 mm part (F is 3.2 mm) and about 11.9 to 12.4 mm on a 16 mm part (F is 6.5 mm). A deeper hole does not break a minimum. It is also not modeled at the F number.

## What could not be fetched

- **STEP, IGES, and SAT from catalog.pemnet.com.** The download calls TraceParts and returns no file until the registration form is submitted. Required fields are email, first name, last name, company, job title, city, postal code, and phone. The form was not submitted. Opening the download URL without the form returns an empty CAD settings object.
- **traceparts.com.** The search page returns HTTP 403.
- **KVT PARTcommunity and 3Dfindit** (the PEM SO/SOS and BSO/BSOS catalogs). Cloudflare blocks this network with "Sorry, you have been blocked" in Chrome. No file was downloaded.
- **Bossard Americas** product pages for these part numbers have no CAD file link.
- **McMaster-Carr** sells these PEM part numbers and states that it builds its own CAD. Those files are not official PEM models, so they were not used.
- **3D ContentCentral** lists a BSO family (catalog 6159) and the download button says login is required. No account was created.
- **Digi-Key, Mouser, Fastenal, and SnapEDA.** No public official PEM STEP link turned up for these metric standoffs.

Catalog letters, from the SO datasheet and `tools/pem_press.py`: H is hex across flats, C is the round clinch diameter, B is the counterbore (thru-hole only), L is length, F is the minimum blind thread depth. Thread major and pitch are the `d` and `pitch` fields.

