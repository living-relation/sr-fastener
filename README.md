# SR Fastener

A Fusion add-in that places screws, set screws, nuts and washers. Pick a type, size, length and material, click
the hole edges, and SR Fastener builds the part, puts it on the hole with a rigid joint, and fills in the
BOM part number, description and material. One insert can place a screw with any number of nuts and washers
on both sides of every picked hole.

Team install and toolbar buttons for every SR Fusion add-in: [docs/TEAM-FUSION-ADDINS.md](docs/TEAM-FUSION-ADDINS.md).

![SR Fastener button in the Insert panel](docs/screenshots/button.png)

![SR Fastener dialog](docs/screenshots/dialog.png) ![SR Fastener dialog for a nut](docs/screenshots/dialog-nut.png)

## How this add-in is installed

**SR Fastener is junctioned straight to the repo clone**, so a `git pull` updates what Fusion loads. Fusion's AddIns entry must be named exactly `SRFastener` and must point at the `SRFastener` folder inside this repo, not the repo root.

Fusion does not pick up new code until the add-in restarts: restart Fusion, or press **Shift+S**, open **Add-Ins**, and **Stop** then **Run**.

To update, double-click `pull.cmd` in the repo folder. It runs `git pull --ff-only` on this clone only, then reminds you to restart the add-in. Nothing updates on its own: Fusion does not check add-ins for updates, so pull, then restart the add-in.

To create the junction, open a normal Command Prompt (not Run as administrator). `mklink /J` does not need elevation. Both paths below are absolute, so no `cd` is required. Run:

```
mklink /J "%APPDATA%\Autodesk\Autodesk Fusion 360\API\AddIns\SRFastener" "<path-to-this-clone>\SRFastener"
```

Replace `<path-to-this-clone>` with this repo's clone path on that PC. The active-folder path differs per PC.

## What it does

- **Toolbar button** "SR Fastener" on more than one panel: by default the Design workspace Solid tab **Insert**
  panel, an **SR Tools** panel on the Solid tab, and Utilities > Add-ins. The panel list is configurable (see
  [Where the buttons go](#where-the-buttons-go)).
- **Dialog:** Units, Part (screws, nuts or washers), Type, Size, Length (screws only), Material, hole selection,
  "Match size to first hole" (on every time the dialog opens), "Flip direction", "Cosmetic thread" (screws
  only), "Stack nuts/washers", a Hole line (size, tapped or not, what is already in it), a Warnings line and a
  read-only BOM preview.
- **Placing:** pick one or more circular hole edges (the top edge of a hole or of a countersink).
  Each screw is centred on the hole, points into the material, and gets a rigid joint to the hole edge.
- **Nuts and washers alone:** pick Nuts or Washers as the Part and pick the hole edge on the side where the
  part goes (bottom edge of a through hole for a nut on the thread end). Parts placed on the same edge stack
  on top of the ones already there.
- **Stack:** tick "Stack nuts/washers" to get a small table with **+**, **−**, **Up** and **Down** buttons.
  Each row has Side (near = the picked edge, under the screw head; far = the other end of the hole), Part
  (nut or washer), Type, the matching size, and Material. **+** adds a row, **−** removes the highlighted row
  (or the newest one if none is highlighted), Up and Down reorder. Each side stacks from the part outward, top
  row first. The table grows and shrinks with the rows (the dialog window keeps its height and scrolls).
  Insert places the screw and the whole stack on every picked hole. The rows are remembered for next time.
- **One component per part number:** the same screw used twice is two occurrences of one component, so
  the BOM counts quantity.
- **BOM fields:** part number, description and Fusion material are set on the component.

The geometry is generated from `SRFastener/data/catalog.json` on your PC. Each part becomes a normal component
inside the design you are working in: nothing is read from or written to a cloud library, the Standard
Components project or any shared folder. To use the tool on another PC, install it from GitHub (see
[Install](#install)).

## Sizing, warnings and matching materials

- **Screws** take their size from the first picked hole: the hole's thread if it is tapped (a Fusion thread
  feature or a Hole feature set to Tapped), otherwise a clearance or tap-drill fit to its diameter.
- **Nuts and washers** take their size from the screw first, whether the screw is in the dialog or already in
  the hole. Only with no screw do they size from the hole. They never size from other nuts or washers. Stack
  rows only offer types that come in the screw's size.
- **Warnings** (shown live and again after Insert): a nut or washer that does not match the screw's size or
  thread (the warning says "inch and metric" when the unit systems differ), a screw that does not match a tapped hole's thread, a screw bigger than a plain hole, two screws in
  one hole, and mixed materials.
- **Mixed materials:** if the new parts' materials differ from each other or from parts already in the hole,
  Insert asks: Yes switches the new parts to the screw's material where that material is sold, No inserts them
  as picked, Cancel goes back to the dialog. Press-in parts are left out of this check, whether the new part
  is a PEM or a PEM is already in the hole.

## Screw types

Names and codes follow McMaster-Carr's category names (checked on mcmaster.com 2026-11-16).

| Type (McMaster name) | Code | Standard | Sizes |
|---|---|---|---|
| Socket head screw, metric | SSH | ISO 4762 | M2 to M16 |
| Button head hex-drive screw, metric | SBH | ISO 7380-1 | M3 to M16 |
| Hex-drive flat head screw 90 deg, metric | SFH | ISO 10642 | M3 to M20 |
| Low-profile socket head screw, metric | SLH | DIN 7984 | M3 to M16 |
| Hex head bolt, fully threaded, metric | HHB | ISO 4017 | M3 to M16 |
| Flat-tip set screw, metric | SSF | ISO 4026 | M3 to M12 |
| Cup-tip set screw, metric | SSC | ISO 4029 | M3 to M12 |
| Pan head Phillips screw, metric | SPH | ISO 7045 | M2 to M10 |
| Cheese head slotted screw, metric | SCH | ISO 1207 | M2 to M10 |
| Socket head screw, inch | SSH | ASME B18.3 | #2 to 1/2, UNC and UNF |
| Button head hex-drive screw, inch | SBH | ASME B18.3 | #2 to 1/2, UNC and UNF |
| Hex-drive flat head screw 82 deg, inch | SFH | ASME B18.3 | #2 to 1/2, UNC and UNF |
| Low-profile socket head screw, inch | SLH | ASME B18.3 | #4 to 1/2 UNC, #8 to 1/2 UNF |
| Hex head bolt, inch | HHB | ASME B18.2.1 | 1/4 to 1/2 |
| Flat-tip set screw, inch | SSF | ASME B18.3 | #2 to 1/2, UNC and UNF |
| Cup-tip set screw, inch | SSC | ASME B18.3 | #2 to 1/2, UNC and UNF |
| Cone-tip set screw, metric | SSN | ISO 4027 | M2 to M12 |
| Cone-tip set screw, inch | SSN | ASME B18.3 | #2 to 1/2 UNC, #10 to 3/8 UNF |
| Extended-tip set screw, metric | SSE | ISO 4028 | M3 to M12 |
| Extended-tip set screw, inch | SSE | ASME B18.3 (half dog) | #2 to 1/2 UNC, #10 to 3/8 UNF |
| Oval-tip set screw, inch | SSO | ASME B18.3 | #4, #6, #8, #10-32, 1/4, 3/8 |
| Flanged button head hex-drive screw, metric | SBF | ISO 7380-2 | M3 to M10 |
| Phillips rounded head sheet metal screw, inch | STP | ASME B18.6.3 head | #2 to #12 |
| Phillips rounded head sheet metal screw, metric | STP | ISO 7049 | M2.2, M2.9, M3.5, M4.2, M4.8, M5.5 |

Button head M3 also includes 4 mm and 5 mm. Those two lengths are on the WASI ISO 7380-1 length grid.
ISO 7380-1:2011 starts M3 at 6 mm, and that is still the first length for every larger button head.

The newer types (SSN, SSE, SSO, SBF, STP) have no alloy black oxide. Their lengths are exactly the lengths
McMaster stocks. Short inch set screws that Holo-Krome's key engagement tables do not cover use the size's
standard socket depth, cut back where needed to leave a quarter diameter of metal above the point (listed in
[docs/SOURCES.md](docs/SOURCES.md)). Sheet metal screws get no cosmetic thread (Fusion has no tapping-screw thread), and the inch
tip is drawn one diameter long (its length is not in the sources). Cone and extended tips start at the thread
root, as the standards specify.

Every family cites its sources in the catalog (dimensions, lengths, thread length and alloy availability
separately), and `tests/test_sources.py` checks rows against them. See [docs/SOURCES.md](docs/SOURCES.md).

What is modeled from the tables: head diameter and height, socket size and depth (set screws use the
shallower socket the standard gives for their shortest lengths), countersink angle (90 deg metric, 82 deg
inch), button and pan crowns (crown radius or side height from the table), slot width and depth, flat-tip and cup-tip
diameters (the cup recess shape itself is not dimensioned in the standards and is drawn as a 118 deg cone), thread pitch, and the threaded length (partly threaded screws get a cosmetic thread of the
tabled length from the tip; shorter ones are threaded to the head).

## Nuts and washers

Names and codes follow McMaster-Carr's category names. Dimensions are what McMaster lists for its 18-8
stainless stock, cross-checked with the standard or a maker data sheet (see [docs/SOURCES.md](docs/SOURCES.md)).
Every size comes in 18-8 SS and 18-8 SS-BO (black oxide uses the same dimensions as plain 18-8). Other
materials per type are listed under [Materials](#materials).

| Type (McMaster name) | Code | Standard | Sizes |
|---|---|---|---|
| Hex nut, metric | NHX | DIN 934 | M3 to M20 |
| Regular hex nut, metric | NHR | ISO 4032 | M2, M5 to M20 (not M3, M4) |
| Thin-profile hex nut, metric | NTH | DIN 439 B | M3 to M16 |
| Nylon-insert locknut, metric | NNL | DIN 985 | M3 to M20 |
| Thin-profile nylon-insert locknut, metric | NTN | ISO 10511 | M3 to M20 |
| Flange nut, metric | NFL | ISO 4161 (M5 to M12), McMaster (M3, M4) | M3 to M12 |
| Serrated flange nut, metric | NSF | ISO 4161 / DIN 6923 | M3 to M12 |
| General purpose washer, metric | WGP | ISO 7089 | M3 to M20 |
| Oversized washer, metric | WOV | ISO 7093-1 | M3 to M20 |
| Split lock washer, metric | WSL | DIN 127 B | M2 to M20 |
| External-tooth lock washer, metric | WTE | DIN 6797 A | M3 to M20 |
| Internal-tooth lock washer, metric | WTI | DIN 6797 J | M3 to M10 |
| Hex nut, inch | NHX | ASME B18.2.2 | #2 to 1/2, UNC and UNF |
| Thin-profile hex nut, inch | NTH | ASME B18.2.2 (jam) | 1/4 to 1/2, UNC and UNF |
| Nylon-insert locknut, inch | NNL | IFI 100/107 | #2 to 1/2 UNC, #6 to 1/2 UNF |
| SAE washer, inch | WSA | ASME B18.21.1 (SAE) | #2 to 1/2 |
| USS washer, inch | WUS | USS | 1/4 to 1/2 |
| Split lock washer, inch | WSL | ASME B18.21.1 | #2 to 1/2 |
| Flange nut, inch | NFL | inch flange | #4 to 1/2 UNC, #10 to 1/2 UNF |
| Serrated flange nut, inch | NSF | inch serrated flange | #6 to 1/2 UNC, #10 to 3/8 UNF |
| Top-lock distorted-thread locknut, metric | NTL | metric top-lock | M4 to M16 |
| Top-lock distorted-thread locknut, inch | NTL | inch top-lock | #6 to 1/2 UNC, #10 to 1/2 UNF |
| Thin-profile nylon-insert locknut, inch | NTN | inch thin nylon-insert | #4 to 1/2 UNC, #10 to 1/2 UNF |
| Coupling nut, metric | NCP | DIN 6334 | M3 to M20 |
| Coupling nut, inch | NCP | inch coupling | #4 to 1/2 UNC, #10 to 1/2 UNF |
| Cap nut, metric | NCA | DIN 1587 | M3 to M20 |
| Cap nut, inch | NCA | inch cap | #6 to 1/2 UNC, #10 to 1/2 UNF |
| Wing nut, metric | NWG | DIN 315 | M3 to M20 |
| Wing nut, inch | NWG | Style 1 | #6 to 1/2 UNC, #10 to 5/16 UNF |
| Square nut, metric | NSQ | DIN 557 | M5 to M16 |
| Square nut, inch | NSQ | ASME B18.2.2 | #2 to 1/2 UNC, #10 to 3/8 UNF |
| Thick washer, metric | WTK | DIN 7349 | M3 to M20 |
| External-tooth lock washer, inch | WTE | ASME B18.21.1 | #2 to 1/2 |
| Internal-tooth lock washer, inch | WTI | ASME B18.21.1 | #4 to 1/2 |
| Oversized washer, inch | WOV | inch fender | #6 to 3/8 |

Alloy steel black oxide is not offered for nuts and washers. Nut part numbers carry only the screw size and
thread: `NHX-M5-0.8 18-8 SS`, `NHX-1/4-20 GR8`. Washer part numbers carry the screw size and the outside
diameter: `WGP-M5 x 10 18-8 SS`, `WSA-1/4 x 0.625 ZN`. Descriptions have no dimensions or standards, e.g.
`Split Lock Washer, M6, 18-8 Stainless Steel`.

Simplified in the model: nut bores are the nominal diameter (no cosmetic thread), the nylon insert is drawn as
part of the hex, the top-lock distortion is not drawn, flange serrations and lock-washer teeth are not drawn,
cap nuts are a hex with a half-sphere dome and a blind bore, wing nuts are a round base with a flat wing plate, and the split-washer gap is as wide as the
washer is thick and flat (not helical).

Where McMaster and the standard differ, McMaster wins and the difference is listed in SOURCES.md, e.g. McMaster's
metric hex nuts are DIN 934. ISO 4032 style 1 is the regular hex nut: M3 and M4 match DIN 934, and the other
common sizes are taller (narrower at M10 and M12). Its 1/4 USS washer is
0.750 in OD (Brighton-Best's B18.21.1 table says 0.734).

![Live test: washers and nuts stacked on screws and holes](docs/screenshots/nuts-washers.png)

## Materials

| Code | Description words | Fusion material (custom, named) | Copied from | Appearance |
|---|---|---|---|---|
| `18-8 SS` | 18-8 Stainless Steel | Stainless Steel | Stainless Steel AISI 304 | Stainless Steel - Satin |
| `18-8 SS-BO` | 18-8 Stainless Steel Black Oxide | Stainless Steel Black Oxide | Stainless Steel AISI 304 | Coating - Black Oxide |
| `ALLOY-BO` | Alloy Steel Black Oxide | Alloy Steel Black Oxide | a quenched-and-tempered Fusion steel for the grade | Coating - Black Oxide |
| `STL` | Plain Steel | Plain Steel | Steel | Steel - Satin |
| `ZN` | Zinc Plated Steel | Zinc Plated | Steel | Steel - Galvanized (Small) |
| `GR8` (inch only) | GR-8 Steel | Grade 8 Steel | Steel AISI 4340 350A QT | Steel - Satin |
| `CL10.9` (metric screws) | CL-10.9 Steel | Class 10.9 Steel | Steel AISI 4340 350A QT | Steel - Satin |
| `CL10` (metric nuts) | CL-10 Steel | Class 10 Steel | Steel | Steel - Satin |

The Fusion material is a named copy made in the design the first time it is used, so the material name has no
alloy numbers or other codes. `STL`, `ZN`, `GR8`, `CL10.9` and `CL10` are made-up codes, like `ALLOY-BO`.

Which types get which extra materials was checked against McMaster-Carr's category filters (2026-11-17). Combinations
McMaster does not sell are left off on purpose (for example Grade 8 socket screws, Class 10.9 set screws,
classes on washers, and Class 10.9 nuts, which are sold as Class 10); the full list and the source pages are in
[docs/SOURCES.md](docs/SOURCES.md). Whether every size of a type is stocked in every material was not checked.

`ALLOY-BO` is offered only for sizes a maker sells in alloy steel black oxide; the Material list shows the
grade, e.g. `Alloy Steel Black Oxide (Class 12.9)`.

## Part numbers

These follow the shop's basic hardware codes, which end with the finish:

- `SSH-M3-0.5 x 10 18-8 SS`
- `SBH-M4-0.7 x 12 18-8 SS-BO`
- `SSH-1/4-20 x 1.5 18-8 SS`
- `SFH-8-32 x 0.5 18-8 SS-BO`
- `SBH-10-32 x 0.5 ALLOY-BO` (UNF)
- `SSH-M5-0.8 x 16 ALLOY-BO`
- `HHB-1/4-20 x 1 GR8`, `SSH-M6-1 x 20 CL10.9`, `SSH-M5-0.8 x 16 ZN`
- nuts: `NHX-M6-1 18-8 SS` (size and thread only); washers: `WGP-M6 x 12 18-8 SS` (screw size x outside diameter)

Descriptions are `Type, size and thread, material` with capitalized words and no standards or dimensions,
e.g. `Socket Head Screw, M4 x 0.7, 18-8 Stainless Steel`. Grade and class finishes use the short form in the
description only, e.g. `Hex Head Bolt, 1/4-20, GR-8 Steel` and `Socket Head Screw, M6 x 1, CL-10.9 Steel`; the
Fusion material name stays spelled out (`Grade 8 Steel`, `Class 10.9 Steel`, `Class 10 Steel`).

Codes: screws are S + head letter + H, which is the shop's existing SSH/SBH/SFH/SLH pattern; the external hex
is a hex head bolt, HHB (Daniel's name; McMaster sells it as Hex Head Screws);
set screws are SS + tip letter (SSF flat-tip, SSC cup-tip, SSN cone-tip, SSE extended-tip, SSO oval-tip);
SBF is a flanged button head and STP a Phillips rounded head sheet metal (tapping) screw.
Nuts are N + two letters (NHX hex, NTH thin-profile, NNL nylon-insert locknut, NFL flange, NSF serrated
flange, NTL top-lock, NTN thin nylon-insert locknut, NCP coupling, NCA cap, NWG wing, NSQ square); washers are
W + two letters (WGP general purpose, WSA SAE, WUS USS, WOV oversized, WSL split lock, WTE/WTI external/internal
tooth lock, WTK thick).
Codes not in the shop list yet: `HHB` (named by Daniel), `SSC`, `SSF`, `SPH`, `SCH`, `SSN`, `SSE`, `SSO`, `SBF`, `STP`, all the nut and washer codes, and the finishes `ALLOY-BO`, `STL`, `ZN`, `GR8`, `CL10.9` and `CL10`.
The Fusion part number, component name and description always use this smart scheme, never a
McMaster or other vendor number. McMaster catalog numbers stay in [docs/SOURCES.md](docs/SOURCES.md)
as the dimension source only.

## Install

1. Clone this repo and keep the folder on disk.
2. Create the AddIns junction as described in [How this add-in is installed](#how-this-add-in-is-installed). Do not copy the folder into AddIns; a copy will not follow `git pull`.
3. In Fusion, press **Shift+S**, open the **Add-Ins** tab, select **SR Fastener**, tick **Run on Startup**, and click **Run**. After a later `git pull`, restart the add-in the same way (**Stop**, then **Run**) or restart Fusion.
4. The button shows up in the Insert panel, the SR Tools panel and Utilities > Add-ins.

Settings (last type, size, length, material and stack rows) are saved in `%APPDATA%\SRFastener\settings.json`.

To share it with the team, each person clones `https://github.com/living-relation/sr-fastener` and creates the
`SRFastener` junction as above; `git pull` and Stop/Run the add-in to update.

## Where the buttons go

The **SR Fastener** button can show on any number of Fusion toolbar panels at once. By default it is on:

- the Design workspace SOLID tab **Insert** panel (on the panel face)
- the **SR Tools** panel (the add-in creates this panel on the SOLID tab, on the panel face)
- **Utilities > Add-ins** (in the drop-down)

Make is not in the default list. You can add it with panel id `SolidMakePanel`, or add any other Fusion toolbar panel.

To change where it shows, copy [panels.example.json](panels.example.json) to `%APPDATA%\SRFastener\panels.json`, edit it, then Stop and Run the add-in (or restart Fusion). If that file is missing, unreadable, or lists nothing valid, the defaults above are used.

| Key | Meaning |
|---|---|
| `panel` | Fusion toolbar panel id, e.g. `InsertPanel`, `SolidCreatePanel`, `SolidScriptsAddinsPanel`, or a new id such as `SRToolsPanel` |
| `workspace` | workspace id, default `FusionSolidEnvironment` (Design) |
| `tab` | tab id used to create a new panel, default `SolidTab` |
| `name` | name shown for a panel the add-in creates |
| `create` | `true` to create the panel if it does not exist |
| `promote` | `true` to show the button on the panel face, not only in its drop-down |

An entry can also be just the panel id as a string. Bad entries are skipped and listed in a message when the add-in
starts. On stop the add-in removes every button it added, the command, and any panel it created that is left
empty (other SR add-ins can share the SR Tools panel).

## Press-in (PEM)

Pick **Press-in**, then a PEM type (self-clinching nut, flush-head stud, standoff or floating nut), size and length or shank. One PEM goes in one hole, as its own component. The BOM part number is the PEM designation, for example `FHS-M5-12` or `S-M4-1ZI`. The description stays `Type, size and thread, material`.

The same stack box adds the mating part. A clinch nut, floating nut or standoff takes a screw of the same thread. A thru standoff takes one screw on each end. A blind standoff takes one screw on the open end, no longer than the blind thread depth. A flush stud takes a nut, and a washer, of the same thread on the stud. A different thread is refused.

The mounting hole size, hole tolerance and minimum sheet thickness are shown in the dialog when you pick a size. They are also saved as design user parameters and part attributes. They are not written into the BOM description.

Warnings: hole off the PEM size, sheet thinner than the minimum (and thicker than the maximum where PEM gives a range), centerline-to-edge under the minimum, and sheet harder than the family's maximum. Type a sheet thickness, an edge distance and a hardness (HRB) to see them; a picked hole fills the first two when it can.

Dimension sources are in [data/pem_sources.md](data/pem_sources.md).

## Known gaps (TBD)

- **Stocked lengths and vendor part numbers:** McMaster-Carr pages need a browser that runs scripts, so they
  could not be read; lengths come from the standards' preferred-length tables (or a maker's maximum length)
  where cited, and are marked unverified in [docs/SOURCES.md](docs/SOURCES.md) where not. Vendor part numbers are `TBD`.
- **Screw, nut and washer types not yet in the tool:** see [docs/MISSING-SCREWS.md](docs/MISSING-SCREWS.md).
- **Stacking under a screw already placed:** a washer added after its screw does not push the screw up; put
  the washer in the stack with the screw, or place it first.
- **Thread detail:** threads are cosmetic (Fusion thread feature), not modelled.
- **Phillips recess:** shown as two crossed slots sized from ISO 7045 (`m` and mean gauge penetration); the
  true ISO 4757 wing shape is not modeled. Cheese head sides are straight (ISO 1207 allows up to 5 deg taper).
- **Dialog test:** the dialog was driven live in Fusion from a script (the same events a click fires:
  hole picks, the stack buttons and row dropdowns, the material prompt and Insert); not clicked by hand.

## Development

```
python tools/build_catalog.py   # regenerate SRFastener/data/catalog.json
python tools/check.py           # repo safety scan + catalog freshness + unit tests
```

`dev/fusion_smoke.py` is a live test that runs inside Fusion (through a Python bridge or the Scripts
dialog). It opens a new design, cuts a plate with 41 holes, places every type in every finish (alloy black
oxide in each family that offers it, a UNF screw, cup, cone, extended and oval tip set screws, the pan and cheese heads, flanged button heads, sheet metal screws, and partly threaded screws),
checks the part number, description, material, appearance, position, tip depth, joint, reuse, toolbar
button, and that partial cosmetic threads have the tabled length and start at the tip. A second plate with
17 holes gets every nut and washer type, stacked under screw heads and on the thread end, and checks the seat
height of each stacked part, its direction, thickness, outside size and joint. Then it closes the design
without saving.

`dev/fusion_stack_smoke.py` is a second live test for sizing and stacks: a plate with a clearance hole, a
tapped hole and a small plain hole; it checks tapped-hole detection, sizing from the hole and from the screw,
far-side placement, a four-part stack, the warnings, nut-alone and washer-alone inserts and the materials.

![Live test plate: one screw of each type](docs/screenshots/test-plate.png)

## Rules for this repo

This repo is public. Keep secrets, machine paths and vendor CAD files out of it. See [AGENTS.md](AGENTS.md).
