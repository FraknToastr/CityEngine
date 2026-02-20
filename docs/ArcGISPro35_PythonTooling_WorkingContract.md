# ArcGIS Pro 3.5+ Python/.pyt “Working Contract” (Josh ↔ ChatGPT)

**Purpose:** A consolidated, durable set of rules, patterns, and known pitfalls that have proven to work in our sessions for producing **ArcGIS Pro 3.5+ compatible** `.py` and `.pyt` tools (especially ArcPy toolboxes). This is written as an operating manual + implementation checklist.

**Scope:** ArcGIS Pro 3.5+ (ArcPy, Python toolbox `.pyt`, script tools `.py`). Windows-first, desktop geoprocessing focus.  
**Non-scope:** Server-side ArcGIS Enterprise/ArcGIS Server GP services deployment specifics (unless explicitly stated in a future update).

---

## 0) Compatibility baseline (ArcGIS Pro 3.5+)

### Python runtime expectations
- Assume **ArcGIS Pro 3.5** uses a fixed Python environment (Conda) with **ArcPy** available.
- Write Python that is compatible with:
  - Python 3.9-era syntax/features (safe in Pro 3.5)
  - No dependencies that require pip installs unless you explicitly state and the user confirms they exist in the Pro environment.
- Prefer standard library + ArcPy. If you use third-party libs (e.g., `pandas`), treat it as optional and fail gracefully.

### ArcPy/GP execution constraints
- Tools run inside the ArcGIS Pro geoprocessing framework:
  - Use `arcpy.AddMessage`, `arcpy.AddWarning`, `arcpy.AddError`.
  - Respect `arcpy.env` and scratch locations.
- Always design for **repeatable** runs and clear failure modes.

---

## 1) Hard invariants and contract rules from our sessions

### 1.1 No destructive “Output Workspace” behavior (GDB safety rule)
**Permanent rule:** *Never design tools such that deleting a tool, output parameter, or temporary workspace can cause ArcGIS Pro to delete a geodatabase.*

**Practices that follow this rule:**
- Do **not** create output parameters that point directly to a user-supplied folder/GDB that Pro might treat as “owned output.”
- Prefer:
  - a user-provided **Output Folder** (for reports / CSV / TXT / JSON outputs), and
  - internally managed scratch GDB paths (`arcpy.env.scratchGDB`) or a dedicated scratch folder under `%TEMP%` / `arcpy.env.scratchFolder`.
- When you create a GDB, do it in an explicitly tool-managed scratch area and **never** expose it as an output workspace parameter.

### 1.2 Secrets / authentication material handling
If authentication material appears (tokens, keys, passwords, auth headers, cookies, client secrets, etc.):
- **Do not repeat it back** verbatim.
- **Redact** if quoting is unavoidable.
- Recommend **revoking/rotating** the credential.
- Recommend storing secrets via:
  - ArcGIS Pro tool parameters marked as password/hidden where possible,
  - external secure stores (e.g., Windows Credential Manager, Key Vault),
  - or parameterized config files excluded from version control.

### 1.3 “Options A/B/C” convention when presenting multiple solutions
When you present multiple implementation options (A, B, C):
- Label them as **A, B, C** in the chat.
- The user can reply with only the letter to choose.
- **Inside each script**, include the option label + description as a comment for traceability, e.g.:
  - `# A) Minimal change — keep joins, filter latest statusdate`
- **Exception:** do not add such comments inside **DAX measures/statements** (Power BI may interpret comment as the measure name).  
  *(This exception does not apply to `.py` / `.pyt`.)*

### 1.4 FS (“Full Script”) convention
If the user says **FS**, provide the **entire full script** inline (not a patch diff), with all required context to run.

### 1.5 “Do not assume the user made a mistake”
If something looks off, do not assume user error. Prefer:
- detect the inconsistency,
- explain the implication,
- offer a minimal corrective path,
- and ask for confirmation **only if** it materially changes outputs.

*(When only one clear solution exists, provide a single best answer rather than forced A/B/C.)*

---

## 2) Production-grade `.pyt` structure (ArcGIS Pro 3.5 compatible)

### 2.1 Canonical `.pyt` skeleton (recommended baseline)
Use this structure for maximum compatibility and maintainability:

```python
# -*- coding: utf-8 -*-
# ArcGIS Pro 3.5+ compatible Python Toolbox (.pyt)

import arcpy
import os
import traceback
from datetime import datetime

class Toolbox(object):
    def __init__(self):
        self.label = "My Tools"
        self.alias = "mytools"
        self.tools = [MyTool]

class MyTool(object):
    def __init__(self):
        self.label = "My Tool"
        self.description = "Does a thing safely and repeatably."
        self.canRunInBackground = False  # safer default for many workflows

    def getParameterInfo(self):
        params = []

        p_in = arcpy.Parameter(
            displayName="Input Features",
            name="in_features",
            datatype="GPFeatureLayer",   # common: GPFeatureLayer, DEFeatureClass, GPString, GPFolder, DEFile
            parameterType="Required",
            direction="Input"
        )
        params.append(p_in)

        p_out_folder = arcpy.Parameter(
            displayName="Output Folder",
            name="out_folder",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input"
        )
        params.append(p_out_folder)

        return params

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        # Validate inputs here; keep it user-friendly.
        return

    def execute(self, parameters, messages):
        in_features = parameters[0].valueAsText
        out_folder = parameters[1].valueAsText

        try:
            arcpy.AddMessage(f"Start: {datetime.now().isoformat(timespec='seconds')}")
            # Work here...
            arcpy.AddMessage("Done.")

        except Exception:
            tb = traceback.format_exc()
            arcpy.AddError("Tool failed.")
            arcpy.AddError(tb)
            raise
```

**Why this works well in Pro 3.5+:**
- Avoids newer syntax features that might be risky.
- Uses explicit `datatype` strings that Pro understands.
- Uses `valueAsText` everywhere to avoid ArcObjects parameter coercion issues.
- Uses `traceback.format_exc()` so failures are diagnosable.

### 2.2 Parameter datatypes — avoid ArcObjects “Invalid input value for DataType”
A common failure mode (seen in our sessions) is:

> `ValueError: ParameterObject: Invalid input value for DataType property`

**Practices to prevent it:**
- Use **valid GP datatype strings**:
  - `GPFeatureLayer`, `DEFeatureClass`, `DETable`, `GPString`, `GPLong`, `GPDouble`, `GPBoolean`, `DEFolder`, `DEFile`, `GPValueTable`, etc.
- Don’t invent datatypes or pass Python types (like `str`) as the `datatype`.
- If you need “any spatial data,” do it as:
  - `GPFeatureLayer` for features,
  - `DETable` for non-spatial tables,
  - or separate parameters with clear constraints.
- Keep optional parameters with explicit defaults where Pro would otherwise supply `None` (see §3.4).

---

## 3) Robust execution patterns (repeatable, safe, debuggable)

### 3.1 Message logging (GP-friendly)
Prefer structured messages:
- `arcpy.AddMessage` for normal progress
- `arcpy.AddWarning` for recoverable issues
- `arcpy.AddError` before raising

Recommended practice:
- prefix messages with timestamps for long jobs
- print key resolved paths (input dataset, scratch, output folder)

### 3.2 Environment management
Use environment settings deliberately and locally:
- `arcpy.env.overwriteOutput = True` (only when you actually want it)
- Use `arcpy.EnvManager(...)` as a context manager to avoid contaminating the user’s session.

Example:

```python
with arcpy.EnvManager(overwriteOutput=True, workspace=arcpy.env.scratchGDB):
    # safe scratch work
    pass
```

### 3.3 Scratch workspaces (GDB safety compliant)
Preferred scratch hierarchy:
1. `arcpy.env.scratchGDB` for temporary feature classes/tables.
2. `arcpy.env.scratchFolder` for temp text/CSV/JSON outputs during processing.
3. A tool-managed subfolder under the user’s **Output Folder** for final deliverables:
   - e.g., `out_folder\reports`, `out_folder\logs`, `out_folder\exports`.

Never treat user folders as “temporary” unless you label them as such.

### 3.4 Optional numeric parameters must be defensive against `None`
Observed failure mode:

> `TypeError: float() argument must be a string or a real number, not 'NoneType'`

Practices:
- If a parameter is optional and numeric, either:
  - assign a default in `getParameterInfo()`, or
  - in `execute()`, apply:
    - `val = parameters[i].value` then `val = default if val is None else float(val)`
- In `updateMessages()`, warn if it is blank and what default will be used.

### 3.5 Progressor + cancellation support
For long loops:
- Use `arcpy.SetProgressor("step", ...)`, `arcpy.SetProgressorPosition()`.
- Periodically check for cancellation with `arcpy.env.isCancelled` if available, or break on GP cancellation errors.

### 3.6 Deterministic output naming
- Use safe, collision-resistant names in scratch:
  - include time-based suffix, or
  - `arcpy.CreateUniqueName()`
- Normalize names:
  - avoid spaces and punctuation that geodatabases reject.

---

## 4) Patterns we have validated in our sessions (known-good approaches)

### 4.1 Symbology color extraction — “LYR X export + CIM JSON parse”
**Checkpointed approach:** Export layer to `.lyrx`, parse the CIM JSON to reliably extract:
- RGB/HEX
- alpha/opacity/transparency
- stroke width
- unique-value fields/labels/values
- geometry type
- layer transparency

**Rationale:** ArcPy symbology wrappers can hide symbol layer details; CIM is more faithful.

**Implementation guidance:**
- Create `.lyrx` into scratch folder or output folder.
- Parse JSON safely with `json.load(...)`.
- Handle renderer variants:
  - `CIMUniqueValueRenderer`
  - `CIMSimpleRenderer`
- Expect symbol layers arrays (fills, strokes, etc.) and traverse defensively.

### 4.2 FeatureServer extraction (Power Query checkpoint exists)
We have a checkpoint for **Power Query (M)** extraction via:
- ObjectID list retrieval, chunked POST fetches to avoid URL length / 404.
This is not an ArcPy tool, but the **pattern is relevant** when you build ArcGIS Python tools that call REST:
- Use POST for large `objectIds` lists.
- Chunk requests.
- Avoid huge query string URLs.

### 4.3 CAD georeferencing scanner tooling
From our discussions:
- scanning folders can find tens of thousands of files
- PRJ discovery counts can be misleading if you only search specific patterns
- tool parameters that default to numeric thresholds must be robust against None (§3.4)

**Recommendation when scanning:**
- Use `os.walk` with explicit include filters and file extension normalization.
- Track counts by extension and report summary (found/used/skipped).

### 4.4 Two-step projection workflows (geographic transformations)
When doing chained reprojections:
- Always validate source spatial reference (WKID) before projecting.
- Use explicit geographic transformation strings exactly as ArcGIS names them.
- Prefer `arcpy.management.Project(...)` with:
  - `out_coor_system` set to a `SpatialReference`
  - `transform_method` set explicitly

**Best practice:** Log:
- input WKID/name,
- intermediate WKID/name,
- output WKID/name,
- transformation name(s) used.

---

## 5) Common pitfalls and how we avoid them

### 5.1 Silent schema mismatches / field name surprises
Practices:
- Always `ListFields` and confirm field existence before using it.
- For user-supplied layers, use `Describe` and `arcpy.Describe(...).shapeType`, `spatialReference`, etc.
- When outputting CSV, explicitly choose encoding (`utf-8-sig` is often a good default for Excel consumers).

### 5.2 “It ran but output is empty” issues
Typical causes:
- selection set is empty
- geometry type mismatch
- layer is a view with definition query
- spatial reference mismatch when doing spatial ops

Practices:
- Log counts:
  - `GetCount` on input
  - counts after key filters/steps
- In `updateMessages()`, warn if selection is empty.

### 5.3 Tool parameter UX
Keep parameters:
- minimal
- typed correctly
- with clear display names and help text
- ordered in an intuitive workflow order

Use `parameter.filter.list` where possible to constrain choices (e.g., geometry types).

### 5.4 Background processing
Default to `canRunInBackground = False` unless you’re confident the tool is background-safe.

---

## 6) Packaging and reproducibility rules

### 6.1 Versioning and checkpoints
When something “works,” treat it as a checkpoint:
- preserve the working file as-is
- make changes as additive and reversible
- maintain a brief “what changed” note

### 6.2 Deliverables
For `.pyt` toolboxes:
- keep single-file `.pyt` where possible for portability
- if multiple modules are needed, keep them in same folder and use relative imports carefully

Suggested folder layout:
```
MyToolbox/
  MyToolbox.pyt
  README.md
  LICENSE (optional)
  resources/ (optional)
```

---

## 7) Minimal QA checklist before you hand a tool to someone

### Functional checks
- [ ] Loads in ArcGIS Pro 3.5 without toolbox errors
- [ ] Parameters appear correctly and have sane defaults
- [ ] Optional parameters do not crash when blank
- [ ] Tool respects GDB safety rule (no risky output workspace behavior)
- [ ] Tool logs input/output paths and counts
- [ ] Tool fails with a readable stack trace if something breaks

### Data checks
- [ ] Input WKID validated (if projection/spatial ops)
- [ ] Geometry type validated (points/lines/polygons)
- [ ] Field existence validated before use

### Output checks
- [ ] Outputs are deterministic and do not silently overwrite unless intended
- [ ] Report/CSV encodings are Excel-friendly if needed
- [ ] Intermediate scratch data cleaned up if large (optional, but nice)

---

## 8) “House style” for code we produce together

### Error handling
- Catch broad exceptions at tool boundary (`execute`) only.
- Raise after logging traceback so GP shows the failure.

### Readability
- Avoid “magic numbers”; use named constants.
- Keep `execute()` readable; move heavy logic into helper functions.

### Performance
- Prefer data access cursors (`arcpy.da.SearchCursor`, `InsertCursor`, `UpdateCursor`) for attribute work.
- Avoid row-by-row geoprocessing calls when a GP tool can do it in bulk.

### ArcGIS Pro compatibility discipline
- Avoid relying on features introduced after Pro 3.5 unless explicitly confirmed.
- Keep dependencies minimal.

---

## 9) Session-derived checkpoints (for traceability)

These are known working checkpoints (as of our conversations) that inform design patterns:

- **SymbologyColorReporter.pyt**: LYR X export + CIM JSON parsing for robust symbology extraction (RGB/HEX, alpha, stroke width, unique values, geometry, layer transparency).
- **OSM Business & Services Extractor**: “MAX POINTS with AOI mode and centroid fallback” as a working checkpoint.
- **Power Query FeatureServer extractor**: ObjectID list + chunked POST fetch approach (pattern relevant for REST calls).
- **CAD georeferencing scanner**: optional numeric param defaulting to avoid `NoneType` conversion errors.

*(If you want, we can append links/paths to local files or repos — but only if you supply them in the current session.)*

---

## 10) How to update this contract
When we discover a new “always do X” or a new failure mode:
- Add a bullet under the most relevant section.
- Add a mini “checkpoint note” if it represents a stable working baseline.

---

### Appendix A — Quick reference: safe parameter datatypes (common)
- `GPFeatureLayer` — feature layer input
- `DEFeatureClass` — feature class dataset
- `DETable` — table dataset
- `DEFile` — file path
- `DEFolder` — folder path
- `GPString` — string
- `GPLong` — integer
- `GPDouble` — float
- `GPBoolean` — boolean
- `GPValueTable` — multi-row parameter table

*(Use ArcGIS Pro GP parameter docs for niche datatypes.)*
