# PEM sources for press-in parts

The numbers in `tools/pem_press.py` were read from these PEM publications. The PDFs and STEP files are not in this repo (they are large and licensed, and pemnet.com also blocked a direct download with an empty CloudFront check).

| Datasheet | What it covers | URL |
|---|---|---|
| CL | Self-clinching nuts S, SS, CLS, CLSS. Metric table page 5, drawing page 4, materials page 9. | https://www.pemnet.com/wp-content/uploads/sites/2/2022/06/cldata.pdf |
| FH | Flush-head studs FH, FHS (page 5) and FH4 (page 6). Materials page 17. | https://www.pemnet.com/wp-content/uploads/sites/2/2022/06/fhdata.pdf |
| SO | Thru-hole standoffs SO, SOS (page 3) and blind standoffs BSO, BSOS (page 4). | https://www.pemnet.com/wp-content/uploads/sites/9/2023/10/sodata.pdf |
| ALA | Floating nuts AS and LAS. | https://www.pemnet.com/wp-content/uploads/sites/2/2022/06/aladata.pdf |

Catalog item pages used to confirm part numbers and the per-length blind depth F:

- https://catalog.pemnet.com/viewitems/nuts-types-s-ss-cls-clss-cla-sp/self-clinching-nuts-types-s-ss-cls-clss-sp-metric
- https://catalog.pemnet.com/en-us/item/nuts-types-s-ss-cls-clss-cla-sp/self-clinching-nuts-types-s-ss-cls-clss-sp-metric/clss-m5-1
- https://catalog.pemnet.com/item/flush-head-threaded-studs-types-fh-fha-fhs/lf-clinching-threaded-studs-type-fh-fhs-fha-metric/fhs-m5-12
- https://catalog.pemnet.com/viewitems/thru-hole-threaded-standoffs-types-so-soa-sos/ru-hole-threaded-standoffs-types-so-soa-sos-metric
- https://catalog.pemnet.com/viewitems/blind-threaded-standoffs-types-bso-bsoa-bsos/lind-threaded-standoffs-types-bso-bsoa-bsos-metric
- https://catalog.pemnet.com/viewitems/floating-self-clinching-fasteners-a4-as-ac/floating-self-clinching-fasteners-a4-as-ac-metric
- https://catalog.pemnet.com/item/floating-self-clinching-fasteners-a4-as-ac/floating-self-clinching-fasteners-a4-as-ac-metric/as-m3-1zi
- https://catalog.pemnet.com/item/floating-self-clinching-fasteners-a4-as-ac/floating-self-clinching-fasteners-a4-as-ac-metric/as-m5-1zi
- https://catalog.pemnet.com/en-us/item/all-metal-locking-thread-nuts-types-la4-lac-las/metal-locking-thread-nuts-types-la4-lac-las-metric/las-m5-1md

Sizes left out, and why, are listed in `OMITTED` in `tools/pem_press.py`.

## STEP checks

Official PennEngineering STEP models, built by TraceParts and served by the PEM catalog viewer. The files are not in this repo (the header reserves all rights, and `tools/check.py` rejects `.stp` files). The stable link for a part is `https://catalog.pemnet.com/cadviewer/ThreeDim?sn=<slug>`. A dot in the size is a hyphen in the slug.

Full tables: [data/pem_step_checks/fh.md](pem_step_checks/fh.md) and [data/pem_step_checks/nuts.md](pem_step_checks/nuts.md).

### Flush studs FH, FHS, FH4

18 files, one length per thread. Length, head diameter `H` and major diameter all pass within 0.05 mm (the measured deltas are under 0.001 mm). FH, FHS and FH4 of one thread are the same solid.

`S` in the datasheet is a **maximum** unthreaded length. The solid's plain barrel starts 0.65 mm to 1.23 mm before `S`. That is inside the maximum, so `S` was not changed. The head is modeled from the STEP profile: thickness `T = H/10`, full-round edge of radius `T/2`, then the collar, neck, undercut and barrel in the FH report.

| Part | STEP page | L | H | Major | Barrel start | S max |
|---|---|---:|---:|---:|---:|---:|
| FH-M2.5-10ZI | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=fh-m2-5-10zi | pass | pass | pass | 1.300 | 1.95 |
| FH-M3-10ZI | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=fh-m3-10zi | pass | pass | pass | 1.400 | 2.1 |
| FH-M3.5-10ZI | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=fh-m3-5-10zi | pass | pass | pass | 1.500 | 2.25 |
| FH-M4-10ZI | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=fh-m4-10zi | pass | pass | pass | 1.600 | 2.4 |
| FH-M5-12ZI | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=fh-m5-12zi | pass | pass | pass | 1.800 | 2.7 |
| FH-M6-12ZI | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=fh-m6-12zi | pass | pass | pass | 2.000 | 3.0 |
| FH-M8-15ZI | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=fh-m8-15zi | pass | pass | pass | 2.467 | 3.7 |
| FHS-M2.5-10 | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=fhs-m2-5-10 | pass | pass | pass | same as FH | same |
| FHS-M3-10 | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=fhs-m3-10 | pass | pass | pass | same as FH | same |
| FHS-M3.5-10 | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=fhs-m3-5-10 | pass | pass | pass | same as FH | same |
| FHS-M4-10 | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=fhs-m4-10 | pass | pass | pass | same as FH | same |
| FHS-M5-12 | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=fhs-m5-12 | pass | pass | pass | same as FH | same |
| FHS-M6-12 | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=fhs-m6-12 | pass | pass | pass | same as FH | same |
| FHS-M8-15 | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=fhs-m8-15 | pass | pass | pass | same as FH | same |
| FH4-M3-10 | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=fh4-m3-10 | pass | pass | pass | same as FH M3 | same |
| FH4-M4-10 | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=fh4-m4-10 | pass | pass | pass | same as FH M4 | same |
| FH4-M5-12 | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=fh4-m5-12 | pass | pass | pass | same as FH M5 | same |
| FH4-M6-12 | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=fh4-m6-12 | pass | pass | pass | same as FH M6 | same |

### Self-clinching nuts S, SS, CLS, CLSS

All 16 pass within 0.001 mm on E, C, A, T and the thread minor. Those body numbers were not changed.

| Part | STEP page | Result |
|---|---|---|
| S-M2.5-1ZI | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=s-m2-5-1zi | pass |
| S-M3-1ZI | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=s-m3-1zi | pass |
| S-M3.5-1ZI | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=s-m3-5-1zi | pass |
| S-M4-1ZI | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=s-m4-1zi | pass |
| S-M6-1ZI | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=s-m6-1zi | pass |
| S-M8-1ZI | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=s-m8-1zi | pass |
| S-M10-1ZI | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=s-m10-1zi | pass |
| SS-M5-1ZI | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=ss-m5-1zi | pass |
| CLS-M2.5-1 | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=cls-m2-5-1 | pass |
| CLS-M3-1 | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=cls-m3-1 | pass |
| CLS-M3.5-1 | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=cls-m3-5-1 | pass |
| CLS-M4-1 | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=cls-m4-1 | pass |
| CLS-M6-1 | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=cls-m6-1 | pass |
| CLS-M8-1 | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=cls-m8-1 | pass |
| CLS-M10-1 | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=cls-m10-1 | pass |
| CLSS-M5-1 | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=clss-m5-1 | pass |

### Floating nuts AS and LAS

E, C, A, T, D and the thread minor pass within 0.001 mm. Those body numbers were not changed.

The ALA drawing says: **Float – .015 in / 0.38 mm minimum, in all directions from center, .030 in / 0.76 mm total.** The intro says the part permits **a total of** .030 in / 0.76 mm of adjustment for a misaligned mating hole. So 0.76 mm is the full travel (the diametral gap) and 0.38 mm is the minimum shift from center toward each side. The model uses that gap. The STEP gap is wider or narrower and was not copied.

| Part | STEP page | STEP gap (mm) | Model gap |
|---|---|---:|---|
| AS-M3-1ZI and LAS-M3-1MD | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=as-m3-1zi | 0.655 | 0.76 total |
| AS-M4-1ZI and LAS-M4-1MD | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=as-m4-1zi | 0.825 | 0.76 total |
| AS-M5-1ZI and LAS-M5-1MD | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=as-m5-1zi | 0.915 | 0.76 total |
| AS-M6-2ZI and LAS-M6-2MD | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=as-m6-2zi | 1.152 | 0.76 total |

LAS uses the same body and the same gap as AS at that thread. Its STEP pages are `las-m3-1md`, `las-m4-1md`, `las-m5-1md` and `las-m6-2md` on the same viewer.

### Standoffs SO, SOS, BSO, BSOS

Forty viewer meshes (two lengths, 6 mm and 16 mm, for each metric thread). A STEP file was not saved: the download form asks for a name, company, and phone, and it was not filled in. The page still draws the part. The mesh header says it was made from the ACIS model. Hex across flats, length, body diameter C, and thread major all pass within 0.05 mm. The full table is [data/pem_step_checks/standoffs.md](pem_step_checks/standoffs.md).

**Blind depth.** Page SO-4 labels the column **F Min.** and the length chart **F Dimension Min.** F is a minimum full-thread depth. The viewer holes are deeper than F (about 5.3–5.8 mm on a 6 mm part where F is 3.2 mm, and about 11.9–12.4 mm on a 16 mm part where F is 6.5 mm). Deeper than the minimum is in spec. The model is cut to F, which meets the minimum. The measured depths are reference only. They are not catalog numbers.

**Hex length.** Pages SO-3 and SO-4 each show the same figure: dimension H is across the flats of a hex body that runs with length L, and C is a short clinch end. The product photo on those pages is a long hex with a short round end. The model keeps that full-length hex. The viewer mesh is different: a hex cap about 0.50 mm thick and a round body of diameter C for the rest of the length. That difference is open. It is not a change to the model.

**Pitch and counterbore B.** Page SO-3 gives the pitch in the thread column (M3 x 0.5, M3.5 x 0.6, M4 x 0.7, M5 x 0.8) and counterbore B in the metric table (M3 is 3.2 mm, 3.5M3 is 3.2 mm, M3.5 is 3.9 mm, M4 is 4.8 mm, M5 is 5.35 mm). The mesh has no helix and no counterbore cylinder, so those two datasheet numbers were not checked against it. Blind standoffs have no B column (page SO-4).

| Part family | Viewer page example | H, L, C, major | Blind vs F | Pitch | B |
|---|---|---|---|---|---|
| SO | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=so-m3-6zi | pass | thru-hole | datasheet only | datasheet only |
| SOS | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=sos-m3-6 | pass | thru-hole | datasheet only | datasheet only |
| BSO | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=bso-m3-6zi | pass | deeper than F min, model stays at F | datasheet only | no B on SO-4 |
| BSOS | https://catalog.pemnet.com/cadviewer/ThreeDim?sn=bsos-m3-6 | pass | deeper than F min, model stays at F | datasheet only | no B on SO-4 |

### Not downloaded

Bossard pages have no STEP link. traceparts.com returned HTTP 403. KVT and 3Dfindit were blocked. 3D ContentCentral asks for a login. No account was created. McMaster builds its own CAD, so those files were not used.
