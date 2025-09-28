# CityEngine CGA Rule Package – Adelaide Digital Twin

This repository contains a modular set of **CGA rule files** for use in CityEngine.  
The rules are aligned with the **South Australian Planning and Design Code (PDA Act)** and the **City of Adelaide (Adelaide City Council)** overlays.

---

## 📂 File Overview

### 1. `00_config.cga`
Shared constants used across rules:
- Floor heights: `FLOOR_HEIGHT_RES=3.2`, `FLOOR_HEIGHT_COM=3.6`, `FLOOR_HEIGHT_MIX=3.4`
- Podium & streetwall: `PODIUM_SETBACK=3`, `STREETWALL_MIN=8`, `STREETWALL_MAX=24`
- Site coverage: `MAX_SITE_COVERAGE_RES=0.70`, `COM=0.90`, `MIX=0.85`

---

### 2. `10_parcel_attribs.cga`
Handles parcel-level attributes:
- Reads SAPPA overlay fields (`CCZNAME`, `CCSZNAME`, `NACZNAME`, `IZNAME`, `MBHMVALUE`, `MBHLVALUE`)
- Converts text values safely to numbers
- Resolves **maximum building height** from metres and levels (`getMaxHeight`)
- Returns zone name, subzone name, etc.

---

### 3. `20_envelope.cga`
Defines the **podium + tower building envelopes**:
- `Envelope(maxH, floorH, coverage)`  
- Splits building into podium and tower using `split(y)`
- Operations written **one per line**:  
  ```cga
  color("#cfcfcf")
  extrude(10)
  ```
- No chained `-->` after extrude/setback

---

### 4. `30_landuse.cga`
Maps parcels to envelopes based on **zone and subzone**:
- **StartRule = LandUseLot**
- Detects zone family using substring tests:
  - Capital City Zone → Subfamilies (*Central Core, Main Street, Boulevard, Frame*)  
  - Corridor / Neighbourhood → Residential envelope  
  - Infrastructure → Simple extrusion
- Uses `find(string, substring) >= 0` to avoid “Unexpected token: s”

---

### 5. `40_heritage.cga`
Overrides rules for **heritage sites**:
- `HeritageWrap(baseMaxH)` selects one of:
  - State heritage → extrude 2 floors, apply style
  - Local heritage → extrude 3 floors, apply style
  - Adjacent heritage → 2m setback then fallback to land use
  - Else → LandUseLot
- Each operation on **separate lines**:
  ```cga
  extrude(12)
  HeritageStyle
  ```

---

### 6. `99_main.cga`
Project entry point:
- **The only @StartRule in the project**:  
  ```cga
  @StartRule
  Lot -->
      her.HeritageWrap(att.getMaxHeight(att.FLOOR_HEIGHT_RES))
  ```
- Imports all other modules

---

## 🚀 Usage

1. Copy all `.cga` files into your CityEngine project’s `/rules` folder.
2. In the Inspector, assign the rule file:  
   - **Rule File**: `99_main.cga`  
   - **Start Rule**: `Lot`
3. Apply to parcel shapes to generate envelopes.

---

## 🔑 Lessons Learned / Best Practices

- **No stray characters**: especially `s` after imports.  
- **Every operation on its own line** (no chaining with `-->`).  
- **Imports must match filenames** exactly.  
- **ASCII identifiers only** (avoid `Façade`, use `Facade`).  
- `split(y)` should use integer sizes, not decimals.  
- Only `99_main.cga` should define the project’s `@StartRule`.  
- Use functions (`getMaxHeight`) to resolve attribute logic cleanly.

---

## 📄 Example Rule Flow

```text
99_main.cga
 └── Lot (@StartRule)
       │
       ▼
       HeritageWrap(...)   [40_heritage.cga]
          ├─ HeritageState → extrude + HeritageStyle
          ├─ HeritageLocal → extrude + HeritageStyle
          ├─ HeritageAdjacent → setback + LandUseLot
          └─ else → LandUseLot   [30_landuse.cga]
                                └─ Envelopes [20_envelope.cga]
```

---

## 📝 Notes
- Constants in `00_config.cga` can be tuned to match new policy settings.  
- `10_parcel_attribs.cga` ensures compatibility with SAPPA overlays.  
- `20_envelope.cga` and `30_landuse.cga` form the backbone of the **City of Adelaide digital twin zoning logic**.  
- `40_heritage.cga` ensures heritage rules override zoning envelopes correctly.

---
