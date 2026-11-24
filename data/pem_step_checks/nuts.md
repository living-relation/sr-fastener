# PEM STEP check: self-clinching nuts and floating nuts

Checked 2026-11-24. One official STEP model per thread size for each metric family in `tools/pem_press.py` on branch `dan_cursor/pem-press-in-cadf` (commit `2882a0d`):

- Self-clinching nuts S, SS, CLS, CLSS
- Floating nuts AS and LAS

Shank code **1** for every size that has it. AS and LAS at M6 are shank **2**, the only shank that table lists.

Pass means the absolute difference is **0.05 mm or less**.

## Where the files came from

Each file is the STEP model served by the PEM catalog for that part number. The catalog page names the CAD supplier as PennEngineering (PEM). TraceParts builds the file. The file header says the unit is the millimetre, and it carries this line:

`Copyright 2026 TraceParts S.A.S. All rights reserved.`

The viewer page shows a registration form. That form was not filled in, and no account was created. Asking the same viewer for a STEP file returned the model.

The stable source URL for a part is:

`https://catalog.pemnet.com/cadviewer/ThreeDim?sn=<slug>`

The slug is the part number in lower case. A dot in the size is a hyphen in the slug (`S-M2.5-1ZI` is `s-m2-5-1zi`, `S-M3.5-1ZI` is `s-m3-5-1zi`). The PEM product finder links to that viewer. Example product page: `https://www.pemnet.com/products/product-finder/s-m3-1zi/`.

The STEP bytes are not in this repo. The header reserves all rights to TraceParts, and `tools/check.py` rejects `.step` and `.stp` files in this public repo.

## How each solid was measured

OpenCascade (`OCP`, the kernel CadQuery uses) read each STEP file. The part axis is the axis of the round body. Diameters come from cylindrical faces and from cross-sections perpendicular to that axis.

- **E** is the largest outer cylinder (the flange or the nut body).
- **A** is the distance from the shank-side face of that cylinder to the shank end of the solid.
- **T** (T1 on AS, T2 on LAS) is the distance from that same face to the other end of the solid.
- **C** is the outer diameter at the free end of the shank. On S, SS, CLS and CLSS that end is a short cylinder. On AS and LAS it is the large end of a cone.
- **Thread minor** is the diameter of the plain bore. These models do not contain a helical thread, so there is no major-diameter surface to measure. The catalog stores the nominal major (`d`) and the pitch, not a separate minor. The minor below is the ISO basic minor from those two catalog numbers: `d - 1.082532 * pitch` (the ASME B1.13M basic minor the PEM page cites).
- **D** (AS and LAS only) is the retainer barrel, the long outer cylinder on the body side of the flange.
- **Float** (AS and LAS only) is the diametral gap between the captive nut and the retainer bore, measured on the straight part of that bore. The catalog value is `float_total` 0.76 mm (0.38 mm each way from center).

Every solid is 0.0003 mm to 0.0006 mm longer than catalog A + T. That extra is a sliver on the bounding box at the tip. The flange face itself sits on the catalog A station. The deltas below include the sliver.

S, SS, CLS and CLSS also carry a ring between the C pilot and the E body. Its diameter is exactly `(C + E) / 2`. That ring is not a column in `pem_press.py`, so it is not scored. AS and LAS have a similar ring under the flange. It is not scored either.

S and CLS of the same size measure the same. The two STEP files are not byte-for-byte copies.

## Self-clinching nuts S, SS, CLS, CLSS

All 16 pass every scored check. Thread major is not in the model (plain bore at the minor).

| Part | Source | E meas / cat | C meas / cat | A meas / cat | T meas / cat | Minor meas / ISO | Major | Result |
|---|---|---|---|---|---|---|---|---|
| S-M2.5-1ZI | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=s-m2-5-1zi | 6.350 / 6.35 | 4.200 / 4.2 | 0.9703 / 0.97 | 1.5003 / 1.5 | 2.0130 / 2.0129 | not modeled | PASS |
| S-M3-1ZI | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=s-m3-1zi | 6.350 / 6.35 | 4.200 / 4.2 | 0.9705 / 0.97 | 1.5005 / 1.5 | 2.4590 / 2.4587 | not modeled | PASS |
| S-M3.5-1ZI | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=s-m3-5-1zi | 7.110 / 7.11 | 4.730 / 4.73 | 0.9705 / 0.97 | 1.5005 / 1.5 | 2.8500 / 2.8505 | not modeled | PASS |
| S-M4-1ZI | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=s-m4-1zi | 7.870 / 7.87 | 5.380 / 5.38 | 0.9703 / 0.97 | 2.0003 / 2.0 | 3.2420 / 3.2422 | not modeled | PASS |
| S-M6-1ZI | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=s-m6-1zi | 11.180 / 11.18 | 8.730 / 8.73 | 1.3804 / 1.38 | 4.0804 / 4.08 | 4.9170 / 4.9175 | not modeled | PASS |
| S-M8-1ZI | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=s-m8-1zi | 12.700 / 12.7 | 10.470 / 10.47 | 1.3804 / 1.38 | 5.4704 / 5.47 | 6.6470 / 6.6468 | not modeled | PASS |
| S-M10-1ZI | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=s-m10-1zi | 17.350 / 17.35 | 13.970 / 13.97 | 2.2103 / 2.21 | 7.4803 / 7.48 | 8.3760 / 8.3762 | not modeled | PASS |
| SS-M5-1ZI | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=ss-m5-1zi | 8.640 / 8.64 | 6.330 / 6.33 | 0.9705 / 0.97 | 2.0005 / 2.0 | 4.1340 / 4.1340 | not modeled | PASS |
| CLS-M2.5-1 | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=cls-m2-5-1 | 6.350 / 6.35 | 4.200 / 4.2 | 0.9703 / 0.97 | 1.5003 / 1.5 | 2.0130 / 2.0129 | not modeled | PASS |
| CLS-M3-1 | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=cls-m3-1 | 6.350 / 6.35 | 4.200 / 4.2 | 0.9705 / 0.97 | 1.5005 / 1.5 | 2.4590 / 2.4587 | not modeled | PASS |
| CLS-M3.5-1 | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=cls-m3-5-1 | 7.110 / 7.11 | 4.730 / 4.73 | 0.9705 / 0.97 | 1.5005 / 1.5 | 2.8500 / 2.8505 | not modeled | PASS |
| CLS-M4-1 | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=cls-m4-1 | 7.870 / 7.87 | 5.380 / 5.38 | 0.9703 / 0.97 | 2.0003 / 2.0 | 3.2420 / 3.2422 | not modeled | PASS |
| CLS-M6-1 | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=cls-m6-1 | 11.180 / 11.18 | 8.730 / 8.73 | 1.3804 / 1.38 | 4.0804 / 4.08 | 4.9170 / 4.9175 | not modeled | PASS |
| CLS-M8-1 | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=cls-m8-1 | 12.700 / 12.7 | 10.470 / 10.47 | 1.3804 / 1.38 | 5.4704 / 5.47 | 6.6470 / 6.6468 | not modeled | PASS |
| CLS-M10-1 | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=cls-m10-1 | 17.350 / 17.35 | 13.970 / 13.97 | 2.2103 / 2.21 | 7.4803 / 7.48 | 8.3760 / 8.3762 | not modeled | PASS |
| CLSS-M5-1 | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=clss-m5-1 | 8.640 / 8.64 | 6.330 / 6.33 | 0.9705 / 0.97 | 2.0005 / 2.0 | 4.1340 / 4.1340 | not modeled | PASS |

Largest absolute delta on E, C, A, T or the minor for these 16 parts is **0.001 mm** (the tip sliver on A and T, and 0.0005 mm on the minor).

## Floating nuts AS and LAS

E, C, A, T and D pass on all 8. The thread minor passes. The thread major is not modeled. The float gap fails on all 8.

T in this table is T1 for AS and T2 for LAS, which is how `pem_press.py` stores them.

| Part | Source | E meas / cat | C meas / cat | A meas / cat | T meas / cat | D meas / cat | Minor meas / ISO | Result |
|---|---|---|---|---|---|---|---|---|
| AS-M3-1ZI | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=as-m3-1zi | 9.140 / 9.14 | 7.3504 / 7.35 | 0.9705 / 0.97 | 3.3105 / 3.31 | 7.370 / 7.37 | 2.4590 / 2.4587 | FAIL float |
| AS-M4-1ZI | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=as-m4-1zi | 11.180 / 11.18 | 9.3306 / 9.33 | 0.9704 / 0.97 | 3.3104 / 3.31 | 9.280 / 9.28 | 3.2420 / 3.2422 | FAIL float |
| AS-M5-1ZI | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=as-m5-1zi | 11.940 / 11.94 | 10.2910 / 10.29 | 0.9704 / 0.97 | 4.3204 / 4.32 | 10.290 / 10.29 | 4.1340 / 4.1340 | FAIL float |
| AS-M6-2ZI | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=as-m6-2zi | 15.240 / 15.24 | 13.0606 / 13.06 | 1.3803 / 1.38 | 5.3403 / 5.34 | 12.960 / 12.96 | 4.9170 / 4.9175 | FAIL float |
| LAS-M3-1MD | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=las-m3-1md | 9.140 / 9.14 | 7.3504 / 7.35 | 0.9705 / 0.97 | 4.8305 / 4.83 | 7.370 / 7.37 | 2.4590 / 2.4587 | FAIL float |
| LAS-M4-1MD | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=las-m4-1md | 11.180 / 11.18 | 9.3306 / 9.33 | 0.9704 / 0.97 | 5.3404 / 5.34 | 9.280 / 9.28 | 3.2420 / 3.2422 | FAIL float |
| LAS-M5-1MD | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=las-m5-1md | 11.940 / 11.94 | 10.2910 / 10.29 | 0.9704 / 0.97 | 6.8604 / 6.86 | 10.290 / 10.29 | 4.1340 / 4.1340 | FAIL float |
| LAS-M6-2MD | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=las-m6-2md | 15.240 / 15.24 | 13.0606 / 13.06 | 1.3803 / 1.38 | 7.8803 / 7.88 | 12.960 / 12.96 | 4.9170 / 4.9175 | FAIL float |

Largest absolute delta on E, C, A, T, D or the minor for these 8 parts is **0.001 mm**.

### Float gap (the only fail)

The captive nut and the retainer are one solid with a closed gap between them. The gap below is retainer bore minus nut body, on the straight capture length. LAS matches AS at the same thread size. Catalog `float_total` is 0.76 mm for every size.

| Part | Nut body dia | Retainer bore | Gap meas | Catalog | Delta | Result |
|---|---|---|---|---|---|---|
| AS-M3-1ZI and LAS-M3-1MD | 5.978 | 6.633 | 0.655 | 0.76 | -0.105 | FAIL |
| AS-M4-1ZI and LAS-M4-1MD | 7.527 | 8.352 | 0.825 | 0.76 | +0.065 | FAIL |
| AS-M5-1ZI and LAS-M5-1MD | 8.346 | 9.261 | 0.915 | 0.76 | +0.155 | FAIL |
| AS-M6-2ZI and LAS-M6-2MD | 10.512 | 11.664 | 1.152 | 0.76 | +0.392 | FAIL |

The gap grows with thread size. It is not the single 0.76 mm figure. M3 is also under the catalog's 0.38 mm per side (half of 0.655 is 0.328 mm).

## Summary

- **24 of 24** requested models were downloaded and measured. One shank code per thread size per family.
- **S, SS, CLS, CLSS (16 parts): PASS.** E, C, A, T and the thread minor all sit within 0.001 mm of the catalog (the minor is the ISO basic minor from catalog major and pitch).
- **AS, LAS (8 parts): E, C, A, T, D and the minor PASS. Float FAIL** by 0.065 mm to 0.392 mm.
- **Thread major is not in any of these models.** The bore is a plain cylinder at the minor diameter. Nothing to score against catalog `d`.

## What could not be stored or scored

- **STEP files are not in the repo.** Blocker: the file header says `Copyright 2026 TraceParts S.A.S. All rights reserved`, and `tools/check.py` rejects `.step` and `.stp` in this public repo. The source URL for each part is in the tables above.
- **Thread major diameter.** Blocker: the official solid has no helical thread and no major-diameter surface. The hole is the minor diameter only.
- **No other part in this set was missing.** The first request for `s-m2.5-1zi` returned "catalog element not found" because the catalog slug uses a hyphen (`s-m2-5-1zi`). The hyphen slug downloaded. The same is true for M3.5, CLS-M2.5 and CLS-M3.5.
