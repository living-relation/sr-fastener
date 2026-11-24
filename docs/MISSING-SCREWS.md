# Screw, nut and washer types not in SR Fastener yet

Daniel approves new types automatically once their data is checked against McMaster-Carr or Fastenal. Names below are McMaster-Carr's category names
(mcmaster.com, checked 2026-11-16).

## Not built yet

| McMaster name | Why not yet |
|---|---|
| Phillips Flat Head Screws for Sheet Metal (inch and metric) | McMaster's head height switches between undercut and standard by length, and the threads per inch change within a size, so each length needs its own head data |
| JIS Flat Head Screws (cross-recessed countersunk) | McMaster sells only M4 to M6 in 18-8; no checked source yet for the JIS B 1111 cross recess size |
| Heat-Set Inserts for Plastic | a new kind of part (sits inside a hole, no head), needs its own placement rule |
| Shoulder Screws, 18-8 hex drive | McMaster lists several thread lengths per shoulder size; needs a full scrape plus Holo-Krome Table 12 socket depths |
| Flanged Button Head Hex-Drive Screws, inch | no standard for the flange thickness and socket, and McMaster's head and flange sizes change with length |
| Phillips Rounded Head Screws for Sheet Metal, No. 0, 1, 5, 7, 14 and M3.9 | outside ASME B18.6.3 Table 18 or ISO 7049, so no recess source |

## Nuts and washers left out on purpose

| McMaster name | Why |
|---|---|
| T-Slot Nuts for aluminum extrusion | McMaster sells them in zinc-plated steel only, sized by extrusion series, not in 18-8 or black oxide |
| Fender washers, DIN 9021 | McMaster's metric oversized washer (ISO 7093-1, already built as WOV) covers the same sizes |
| Extreme-Vibration-Resistant Wedge Lock Washers | Only 316 stainless, black-oxide 316 or zinc-flake steel, not 18-8 or alloy black oxide |
| Disc Springs (Belleville) | 302 stainless, 17-7 PH or steel, picked by load rating, not by screw size and finish |
| Serrated flange nut 1/2-20, wing nut 3/8-24 and 1/2-20 | McMaster's dimensions differ from the coarse-thread size, not added yet |

The work hub's Standard Components > Fasteners folder was not reachable live, so its list could not be rechecked.

## Lengths and parts checked and left out

| Part | Why it is not in the catalog |
|---|---|
| ISO 10642 M3 x 5 flat head | ISO 10642:2004 Table 1 starts every size at 8 mm. A shop listing of M3 x 5 uses a 6 mm head, not the 6.72 mm theoretical head already in the catalog. |
| ISO 7045 M3 x 35 pan head | ISO 7045:2011 Table 1 gives M3 lengths through 30 mm, which are already offered. 35 mm starts at M3.5. |
| Female-female M3 hex standoffs, 6 mm and 8 mm | PEM SO and BSO include M3 at 6 mm and 8 mm, but those are self-clinching standoffs, not two female threads. No one datasheet gave both lengths with across-flats, thread depth and a material that fits the finish list. |
