# Screw, nut and washer types not in SR Fastener yet

Daniel approves new types automatically once their data is checked against McMaster-Carr or Fastenal. Names below are McMaster-Carr's category names
(mcmaster.com, checked 2026-11-16).

## Not built yet (next PRs, most common first)

| McMaster name | Standard | Metric / inch |
|---|---|---|
| Tapping Screws (self-tapping) | ISO 7049 / ISO 15482, ASME B18.6.4 | both |
| JIS Steel Flat Head Screws (cross-recessed countersunk) | JIS B 1111 | metric |
| Threaded Inserts (SPIROL heat-set) | maker datasheet | both |
| Cone-Tip Set Screws | ISO 4027, ASME B18.3 | both |
| Extended-Tip Set Screws (dog point) | ISO 4028, ASME B18.3 | both |
| Oval-Tip Set Screws | ASME B18.3 | inch (metric: no ISO standard) |
| Flanged Button Head Hex-Drive Screws | ISO 7380-2 | metric |
| Shoulder Screws | ISO 7379, ASME B18.3 | both |

## Nuts and washers left out on purpose

| McMaster name | Why |
|---|---|
| T-Slot Nuts for aluminum extrusion | McMaster sells them in zinc-plated steel only, sized by extrusion series, not in 18-8 or black oxide |
| Fender washers, DIN 9021 | McMaster's metric oversized washer (ISO 7093-1, already built as WOV) covers the same sizes |
| Extreme-Vibration-Resistant Wedge Lock Washers | Only 316 stainless, black-oxide 316 or zinc-flake steel, not 18-8 or alloy black oxide |
| Disc Springs (Belleville) | 302 stainless, 17-7 PH or steel, picked by load rating, not by screw size and finish |
| Serrated flange nut 1/2-20, wing nut 3/8-24 and 1/2-20 | McMaster's dimensions differ from the coarse-thread size, not added yet |

The work hub's Standard Components > Fasteners folder was not reachable live, so its list could not be rechecked.
