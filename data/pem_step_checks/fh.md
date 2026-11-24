# PEM flush-head studs: STEP check (FH, FHS, FH4)

Official PennEngineering STEP models, one length per metric thread, measured with OpenCascade (the OCP Python bindings). Units in every file are millimetres. Pass means the measured value is within 0.05 mm of the value stored in `tools/pem_press.py`.

The solid is the TraceParts model served by the PEM catalog viewer. The file header names TraceParts and the supplier PennEngineering. The viewer page shows a user form. No form was filled in. A STEP AP203 download for that part still came back.

STEP files are not in this repo. The header says all rights reserved, and `tools/check.py` rejects `.stp` and `.step` files. The source link below is the stable CAD page for that part. The temporary download link expires.

M10 is not in the metric FH table (`OMITTED` in `tools/pem_press.py`: the table stops at M8). Nothing was fetched for M10. FH4 is M3, M4, M5 and M6 only.

FH, FHS and FH4 of the same thread measured as the same solid. Material differs in the catalog. The CAD shape does not. Head, collar and undercut sit at the head end, so they do not depend on the one length chosen here. Only that length was checked. A longer stud was not measured.

## Catalog comparison

`L` is overall length of the solid. `H` is the largest head diameter (crest of the round edge). `Major` is the long plain cylinder after the undercut. The model has no helical thread, so this is the blank diameter, not a thread crest and root.

`Unthreaded` is the distance from the flush face to the start of that long cylinder. The catalog value is `S`, and the datasheet calls `S` a maximum. The solid has no shoulder at `S`.

Head thickness, collar and undercut have no number in `tools/pem_press.py`. They are in the modeling table. They are not a pass or fail.

| Part | Source | L | cat L | | Head dia | cat H | | Major | cat major | | Unthreaded | cat S max | |
|---|---|---:|---:|---|---:|---:|---|---:|---:|---|---:|---:|---|
| FH-M2.5-10ZI | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=fh-m2-5-10zi | 10.000 | 10 | pass | 4.100 | 4.1 | pass | 2.500 | 2.5 | pass | 1.300 | 1.95 | fail |
| FH-M3-10ZI | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=fh-m3-10zi | 10.000 | 10 | pass | 4.600 | 4.6 | pass | 3.000 | 3.0 | pass | 1.400 | 2.1 | fail |
| FH-M3.5-10ZI | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=fh-m3-5-10zi | 10.000 | 10 | pass | 5.300 | 5.3 | pass | 3.500 | 3.5 | pass | 1.500 | 2.25 | fail |
| FH-M4-10ZI | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=fh-m4-10zi | 10.000 | 10 | pass | 5.900 | 5.9 | pass | 4.000 | 4.0 | pass | 1.600 | 2.4 | fail |
| FH-M5-12ZI | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=fh-m5-12zi | 12.000 | 12 | pass | 6.500 | 6.5 | pass | 5.000 | 5.0 | pass | 1.800 | 2.7 | fail |
| FH-M6-12ZI | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=fh-m6-12zi | 12.000 | 12 | pass | 8.200 | 8.2 | pass | 6.000 | 6.0 | pass | 2.000 | 3.0 | fail |
| FH-M8-15ZI | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=fh-m8-15zi | 15.000 | 15 | pass | 9.600 | 9.6 | pass | 8.000 | 8.0 | pass | 2.467 | 3.7 | fail |
| FHS-M2.5-10 | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=fhs-m2-5-10 | 10.000 | 10 | pass | 4.100 | 4.1 | pass | 2.500 | 2.5 | pass | 1.300 | 1.95 | fail |
| FHS-M3-10 | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=fhs-m3-10 | 10.000 | 10 | pass | 4.600 | 4.6 | pass | 3.000 | 3.0 | pass | 1.400 | 2.1 | fail |
| FHS-M3.5-10 | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=fhs-m3-5-10 | 10.000 | 10 | pass | 5.300 | 5.3 | pass | 3.500 | 3.5 | pass | 1.500 | 2.25 | fail |
| FHS-M4-10 | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=fhs-m4-10 | 10.000 | 10 | pass | 5.900 | 5.9 | pass | 4.000 | 4.0 | pass | 1.600 | 2.4 | fail |
| FHS-M5-12 | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=fhs-m5-12 | 12.000 | 12 | pass | 6.500 | 6.5 | pass | 5.000 | 5.0 | pass | 1.800 | 2.7 | fail |
| FHS-M6-12 | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=fhs-m6-12 | 12.000 | 12 | pass | 8.200 | 8.2 | pass | 6.000 | 6.0 | pass | 2.000 | 3.0 | fail |
| FHS-M8-15 | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=fhs-m8-15 | 15.000 | 15 | pass | 9.600 | 9.6 | pass | 8.000 | 8.0 | pass | 2.467 | 3.7 | fail |
| FH4-M3-10 | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=fh4-m3-10 | 10.000 | 10 | pass | 4.600 | 4.6 | pass | 3.000 | 3.0 | pass | 1.400 | 2.1 | fail |
| FH4-M4-10 | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=fh4-m4-10 | 10.000 | 10 | pass | 5.900 | 5.9 | pass | 4.000 | 4.0 | pass | 1.600 | 2.4 | fail |
| FH4-M5-12 | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=fh4-m5-12 | 12.000 | 12 | pass | 6.500 | 6.5 | pass | 5.000 | 5.0 | pass | 1.800 | 2.7 | fail |
| FH4-M6-12 | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=fh4-m6-12 | 12.000 | 12 | pass | 8.200 | 8.2 | pass | 6.000 | 6.0 | pass | 2.000 | 3.0 | fail |

`S` fails on every part. The model’s unthreaded length is 0.65 mm to 1.23 mm shorter than `S` max. Length, head diameter and major diameter pass on every part. The raw head crest sits under 0.00002 mm above `H` (torus math in the file). Rounded to 0.001 mm it is `H`.

Same shape for the FHS and FH4 rows as the FH row of that thread. Same pass and fail.

## Head thickness and profile

Same profile on every thread. Sizes change. The shape does not.

From the flush face to the tip:

1. Head. Thickness `T = H / 10`. The edge is a full round of radius `T / 2`, so the crest `H` is at mid-thickness. Each flat face is diameter `H - T`.
2. Collar. A smooth cylinder, not separate rib teeth. Diameter is the shank diameter below. Length is `T / 2`.
3. Neck. A short cylinder at the major diameter.
4. Undercut. Cone flanks at 63.43 degrees from the axis (`arctan 2`), with a round bottom. Minimum diameter and axial length are below.
5. Barrel. Plain cylinder at the major diameter (no helix) out to a 45 degree chamfer. The end face also has a conical recess: 60 degrees from the axis (included angle 120 degrees). Its reference radius is 0.075 times the major diameter.

| Thread | Head thickness | Edge radius | Flat face dia | Collar dia | Collar length | Neck length | Undercut min dia | Undercut length | Barrel starts at |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| M2.5 | 0.410 | 0.205 | 3.690 | 3.485 | 0.205 | 0.498 | 2.233 | 0.188 | 1.300 |
| M3 | 0.460 | 0.230 | 4.140 | 3.910 | 0.230 | 0.485 | 2.680 | 0.225 | 1.400 |
| M3.5 | 0.530 | 0.265 | 4.770 | 4.505 | 0.265 | 0.443 | 3.127 | 0.263 | 1.500 |
| M4 | 0.590 | 0.295 | 5.310 | 5.015 | 0.295 | 0.415 | 3.573 | 0.300 | 1.600 |
| M5 | 0.650 | 0.325 | 5.850 | 5.525 | 0.325 | 0.450 | 4.467 | 0.375 | 1.800 |
| M6 | 0.820 | 0.410 | 7.380 | 6.970 | 0.410 | 0.320 | 5.360 | 0.450 | 2.000 |
| M8 | 0.960 | 0.480 | 8.640 | 8.160 | 0.480 | 0.427 | 7.146 | 0.600 | 2.467 |

Numbers are millimetres, rounded to 0.001. Collar diameter and undercut minimum are the exact cylinder and torus sizes in the STEP, rounded. FH4 uses the M3, M4, M5 and M6 rows. It has no M2.5, M3.5 or M8 row in the catalog.

To model one stud: revolve that stack, then set the barrel so the overall length is the length code. Put the 45 degree chamfer and the tip recess on the free end. Do not add a helix unless you want a cosmetic thread. The official solid does not have one.

## Summary

- 18 official STEP files, every metric FH and FHS thread from M2.5 to M8, and every FH4 thread from M3 to M6. One length each.
- Length, head diameter `H` and major diameter all pass 0.05 mm.
- `S` fails on every part. The solid’s unthreaded length is shorter than `S` max, and nothing in the solid sits at `S`.
- Head thickness is `H / 10` with a full-round edge. That number is not in the catalog. The modeling table is the one to build from.
- FH, FHS and FH4 share one solid per thread.

## What is missing

- M10. Not in the metric table. No part to download.
- A helical thread. The official solid is a plain major-diameter cylinder, so thread root and pitch cannot be measured from it.
- A feature at `S` max. Compared anyway. It fails the 0.05 mm check.
- STEP files in the repo. TraceParts marks the file all rights reserved, and this repo rejects vendor CAD. Links above are the source.
