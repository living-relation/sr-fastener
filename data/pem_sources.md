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

CAD downloads are linked from those catalog pages (CAD supplier: PennEngineering). None could be fetched from this machine, so the 0.05 mm STEP check was not run.

Sizes left out, and why, are listed in `OMITTED` in `tools/pem_press.py`.
