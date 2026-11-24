# Team guide: SR Fusion add-ins

Checked 24 Nov 2026. Facts below come from each repo's README, `.manifest`, and toolbar code on `main`, plus the Autodesk and GitHub pages linked at the bottom. This guide was not clicked through in a live Fusion window. Items that could not be confirmed are marked **unverified**.

## TL;DR

1. The four add-ins are public. Clone each repo into `%USERPROFILE%\projects\active\<repo>`.
2. Open **Command Prompt** (not PowerShell). Make a junction from Fusion's AddIns folder to the add-in folder inside the clone.
3. In Fusion, press **Shift+S**. Open the **Add-Ins** tab, tick **Run on Startup**, and click **Run**.
4. Buttons are in the **Design** workspace. Pin one with the three dots, then **Pin to Toolbar**.
5. To update a clone, double-click `pull.cmd` (or `git pull --ff-only`), then restart Fusion or Stop and Run the add-in.

## The add-ins

| Add-in | One line | Repo | Folder Fusion loads |
|---|---|---|---|
| SR Fastener | Places screws, nuts, and washers on hole edges and fills the BOM fields. | [sr-fastener](https://github.com/living-relation/sr-fastener) | `SRFastener` |
| SR BOM | Counts parts, fills part number, description, and material, and exports CSV and Excel. | [sr-bom](https://github.com/living-relation/sr-bom) | `SRBom` |
| SR Export | Exports STEP, F3D, STL, 3MF, IGES, SAT, and DXF in one click. | [sr-export](https://github.com/living-relation/sr-export) | `SRExport` |
| SR Drawing PDF | Makes a front, top, right, and isometric drawing of the active design and exports a PDF. | [sr-drawing-pdf](https://github.com/living-relation/sr-drawing-pdf) | `SRDrawingPDF` |

Each manifest `"type"` is `addin`. Each button name below is the command name the code registers.

### SR Fastener

- Button: **SR Fastener** (command id `srFastenerInsertCmd`).
- Design workspace, **SOLID** tab, **Insert** panel, on the panel face.
- Design workspace, **SOLID** tab, **SR Tools** panel (panel id `SRToolsPanel`), on the panel face. The add-in creates this panel on the SOLID tab when it is missing.
- **Add-ins** panel (panel id `SolidScriptsAddinsPanel`), in the drop-down. The README calls this **Utilities > Add-ins**. The code puts it on tab id `ToolsTab`.
- Full notes: [README](https://github.com/living-relation/sr-fastener/blob/main/README.md).

### SR BOM

- Button: **SR BOM** (command id `srBomCmd`).
- Panels: `SolidScriptsAddinsPanel` (README: **Utilities > Add-ins**), `SolidMakePanel` (README: **Make**), `InsertPanel` (README: **Insert**), and `SRToolsPanel` (panel name **SR Tools**).
- First pin (on the panel face) is set for **SR Tools** and **Add-ins**. **Insert** and **Make** get the command in the drop-down. Fusion keeps your later pin or unpin.
- If `SRToolsPanel` already exists, this add-in reuses it. If it does not, the code creates an **SR Tools** tab (tab id `SRToolsTab`) in the Design workspace and puts the **SR Tools** panel on that tab.
- Full notes: [README](https://github.com/living-relation/sr-bom/blob/main/README.md).

### SR Export

- Button: **SR Export** (command id `srExportCmd`).
- Same panels, same first-pin rules, and the same SR Tools tab-or-reuse rule as SR BOM.
- Full notes: [README](https://github.com/living-relation/sr-export/blob/main/README.md).

### SR Drawing PDF

- Button: **SR Drawing PDF** (command id `srDrawingPdfCmd`).
- Same panels, same first-pin rules, and the same SR Tools tab-or-reuse rule as SR BOM.
- Open a saved design before you click the button. The GitHub repo blurb still says "script". The manifest type is `addin`, and the README installs it as an add-in.
- The folder also contains a sheet editor (`sheet2d`). The README says that editor is not on this button yet.
- Full notes: [README](https://github.com/living-relation/sr-drawing-pdf/blob/main/README.md).

### Where SR Tools shows up

Whoever starts first creates the shared **SR Tools** panel:

- **SR Fastener** creates it on the **SOLID** tab.
- **SR BOM**, **SR Export**, and **SR Drawing PDF** reuse that panel if it is already there. If they start first, they create an **SR Tools** tab and put the panel on that tab.

SR Fastener puts its button on the face of **Insert** and **SR Tools** every time it starts. The other three only set the first pin, then leave your choice alone.

The code comment in SR BOM, SR Export, and SR Drawing PDF says `SolidScriptsAddinsPanel` is Utilities / Add-Ins, and that some Fusion builds put that panel under the **Manage** tab. Which tab you see is **unverified** here (no live Fusion window).

## Not add-ins

These two repos exist and are public. They are not Fusion add-ins, so there is nothing to junction.

- **[sr-cadlib](https://github.com/living-relation/sr-cadlib)** is a Python helper library for scripts that drive Fusion. Its README says it is not a Fusion add-in. There is no `.manifest` in the repo.
- **[sr-drawing-pack](https://github.com/living-relation/sr-drawing-pack)** is a research-stage drawing editor (title block, revision table, BOM). Its README says it is not ready for use. There is no `.manifest` and no add-in folder.

These six `sr-*` repos are the ones on [github.com/living-relation](https://github.com/living-relation) as of 24 Nov 2026.

## Access

All six repos are **public** (checked 24 Nov 2026). A public repo can be cloned without being added as a collaborator.

If a repo is made private later, you need access to the **living-relation** GitHub account before clone or Download ZIP will work. Ask Daniel for that access.

## Install with Git (Windows)

Use **Command Prompt**. `mklink` is a Command Prompt command. A normal window is enough. The READMEs say not to use "Run as administrator".

Git for Windows must already be installed. Check:

```
git --version
```

If that fails, use [Install without Git](#install-without-git) below.

1. Make the projects folder. If Command Prompt says it already exists, go to the next step.

```
mkdir "%USERPROFILE%\projects\active"
```

2. Go there.

```
cd /d "%USERPROFILE%\projects\active"
```

3. Clone each add-in you want. Skip a line if that folder is already there.

```
git clone https://github.com/living-relation/sr-fastener.git
```

```
git clone https://github.com/living-relation/sr-bom.git
```

```
git clone https://github.com/living-relation/sr-export.git
```

```
git clone https://github.com/living-relation/sr-drawing-pdf.git
```

4. Still in Command Prompt, make one junction per add-in. The link name must match the add-in folder. The target is that folder inside the clone, not the repo root. Each README uses this Fusion 360 AddIns path.

```
mklink /J "%APPDATA%\Autodesk\Autodesk Fusion 360\API\AddIns\SRFastener" "%USERPROFILE%\projects\active\sr-fastener\SRFastener"
```

```
mklink /J "%APPDATA%\Autodesk\Autodesk Fusion 360\API\AddIns\SRBom" "%USERPROFILE%\projects\active\sr-bom\SRBom"
```

```
mklink /J "%APPDATA%\Autodesk\Autodesk Fusion 360\API\AddIns\SRExport" "%USERPROFILE%\projects\active\sr-export\SRExport"
```

```
mklink /J "%APPDATA%\Autodesk\Autodesk Fusion 360\API\AddIns\SRDrawingPDF" "%USERPROFILE%\projects\active\sr-drawing-pdf\SRDrawingPDF"
```

If your clone lives in a different folder, change only the second path. It still has to end in `SRFastener`, `SRBom`, `SRExport`, or `SRDrawingPDF`.

Autodesk's current help also lists `%APPDATA%\Autodesk\Autodesk Fusion\API\AddIns` (no "360") as a folder Fusion searches. The API guide still lists the "Autodesk Fusion 360" path as a default search folder too. These READMEs use the Fusion 360 path. If Fusion does not list the add-in, make the same junction under the folder without "360". Which folder your installed Fusion reads first was **unverified** here.

## Install without Git

A ZIP copy does not follow `git pull`. You download a new ZIP when you want an update, replace the folder, then restart the add-in.

GitHub: open the repo, click **Code**, then **Download ZIP**. ([GitHub docs](https://docs.github.com/en/repositories/working-with-files/using-files/downloading-source-code-archives).)

1. Unzip. The top folder is named from the repo and the branch. For `main`, that is usually `sr-fastener-main`, `sr-bom-main`, `sr-export-main`, or `sr-drawing-pdf-main`. The exact zip-root name was not opened in this check, so confirm the folder you see.
2. Copy the inner add-in folder (the one that contains the `.manifest` file) into Fusion's AddIns folder. The copy's name must be the add-in folder name.

| Usual zip top folder | Copy this inner folder | Into AddIns as |
|---|---|---|
| `sr-fastener-main` | `SRFastener` | `SRFastener` |
| `sr-bom-main` | `SRBom` | `SRBom` |
| `sr-export-main` | `SRExport` | `SRExport` |
| `sr-drawing-pdf-main` | `SRDrawingPDF` | `SRDrawingPDF` |

Example destination:

`%APPDATA%\Autodesk\Autodesk Fusion 360\API\AddIns\SRFastener`

Copy that inner folder. Leave the repo root (README, `tests`, `tools`) out of AddIns. Fusion looks for the `.manifest` in the folder you place there.

## Turn the add-in on

Each manifest already sets `runOnStartup` to true. Still confirm the checkbox once.

1. Start Fusion.
2. Press **Shift+S**. Autodesk's shortcut list names this **Scripts and Add-ins**. The API guide names the dialog **Scripts and Add-Ins**.
3. Open the **Add-Ins** tab.
4. Select the add-in. The READMEs say the rows are **SR Fastener**, **SR BOM**, **SR Export**, and **SR Drawing PDF**. The folders are `SRFastener`, `SRBom`, `SRExport`, and `SRDrawingPDF`. The exact words in the list were **unverified** here. If you see the folder name, pick that row.
5. Tick **Run on Startup**.
6. Click **Run**.

A Dec 2025 Autodesk article describes a different screen: Utilities tab, **Add-ins**, then a filter named **run on startup**. If you see that screen, tick the add-in there. ([How to disable the automatic launch of a Fusion App/Add-ins](https://www.autodesk.com/support/technical/article/caas/sfdcarticles/sfdcarticles/How-to-disable-the-automatic-launch-of-a-Fusion-360-app.html).)

To load new code later: restart Fusion, or press **Shift+S**, open **Add-Ins**, click **Stop**, then **Run**. The API guide uses those button names.

## Update

Fusion does not check these add-ins for updates.

**Clone (keeps updating):** in that repo folder, double-click `pull.cmd`. It runs `git pull --ff-only` for that clone only, then tells you to restart the add-in. Or, in Command Prompt, one repo at a time:

```
cd /d "%USERPROFILE%\projects\active\sr-fastener"
```

```
git pull --ff-only
```

Repeat the `cd` and `git pull --ff-only` in `sr-bom`, `sr-export`, and `sr-drawing-pdf` if you installed them. Then restart Fusion, or Stop and Run each add-in.

**ZIP copy:** download a new ZIP, replace that add-in folder in AddIns, then Stop and Run. The old copy stays on disk until you replace it.

## Pin a button and set a shortcut

Open the **Design** workspace. Use the panel list in [The add-ins](#the-add-ins). Open the panel drop-down if the button is not already on the panel face.

Autodesk's help (10 Aug 2026) says:

1. Open the drop-down for that menu section.
2. Hover the command. Three dots appear to the right of the name.
3. Click the three dots.
4. Check **Pin to Toolbar**.

Uncheck **Pin to Toolbar** to take it back off the panel face. ([How to edit the toolbar in Autodesk Fusion](https://www.autodesk.com/support/technical/article/caas/sfdcarticles/sfdcarticles/How-to-edit-the-toolbar-in-Fusion-360.html).)

A 13 Nov 2024 Autodesk article says the same three-dot menu also has **Pin to Shortcuts** and **Change keyboard shortcut**. ([How to customize menus in Fusion](https://www.autodesk.com/support/technical/article/caas/sfdcarticles/sfdcarticles/How-to-customize-menus-in-Fusion-360.html).)

A 23 Jun 2026 Autodesk article spells the keyboard item **Change keyboard Shortcuts** (capital S). Steps there: hover, three dots, click that item, type the key, click **OK**. ([How to search and set custom shortcut commands](https://www.autodesk.com/support/technical/article/caas/sfdcarticles/sfdcarticles/How-to-set-the-custom-shortcut-to-various-commands-in-Fusion-360.html).)

Search names to type: `SR Fastener`, `SR BOM`, `SR Export`, `SR Drawing PDF`.

### S key

Autodesk's shortcut list calls **S** the **Model Toolbox**.

Get Started help:

1. Click the canvas.
2. Press **S**.
3. In the Search box, type the command name.
4. Place the pointer over the command and click **Add to Shortcuts**.

([Perform basic tasks](https://help.autodesk.com/cloudhelp/ENU/Fusion-GetStarted/files/GS-BASIC-OPERATIONS.htm).)

The 23 Jun 2026 shortcut article describes this differently: press **S**, type the command, hover until an **arrow** shows, then click the arrow. It does not use the words "Add to Shortcuts" or "pin". If you see an arrow, click that.

The word **Promote** is what the add-in code calls pinning (`isPromoted` in SR Fastener, `isPromotedByDefault` in the other three). A menu item named Promote was **not** found in the Autodesk pages above.

## Sources

- [Creating a Script or Add-In](https://help.autodesk.com/view/fusion360/ENU/?guid=GUID-9701BBA7-EC0E-4016-A9C8-964AA4838954) (dialog name, Add-Ins tab, Run on Startup, Run, Stop, both AddIns folder paths)
- [Python-specific API notes](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/PythonSpecific_UM.htm) (Run on Startup checkbox, Stop)
- [Fusion keyboard shortcuts reference](https://help.autodesk.com/view/fusion360/ENU/?guid=GUID-F0491540-0324-470A-B651-2238D0EFAC30) (Shift+S = Scripts and Add-ins, S = Model Toolbox)
- [Using Samples from GitHub](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/UsingSamplesFromGitHub_UM.htm) (AddIns folder without "360", Download ZIP)
- Toolbar, shortcuts, and startup articles linked in the sections above

## Unverified

- No live Fusion window was used. On-screen tab titles, the Add-Ins list label (spaced name vs folder name), and which AddIns folder your Fusion reads first were not clicked.
- Whether **Add-ins** sits under **Utilities** or **Manage** on your build. The code comment says both happen.
- A menu item named **Promote**. Autodesk's pages say **Pin to Toolbar**.
- The S-key control: **Add to Shortcuts** (Get Started) vs an **arrow** (23 Jun 2026 support article).
- The exact Download ZIP root folder name (`sr-fastener-main` and the others). GitHub names that folder from the repo and branch. The archives were not unzipped in this check.
- The keyboard-menu spelling: **Change keyboard shortcut** (13 Nov 2024) vs **Change keyboard Shortcuts** (23 Jun 2026).
