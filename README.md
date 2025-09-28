# Adelaide Digital Twin – CGA Rule Development Notes

This document is a **working knowledge base** for developing CGA rules in CityEngine for the City of Adelaide Digital Twin.  
It summarises all **mistakes, fixes, corrections, and lessons learned** across previous iterations so that future work can build from a clean foundation.

---

## 🎯 Current Focus

We are developing a **single rule file**:  
`01_Parcel_Rules.cga`  

This rule handles **height extrusions** and **colouring by subzone** for parcels in the cadastre. It connects directly to attribute fields from the Planning and Design Code overlays.

---

## 📂 Current Script: 01_Parcel_Rules.cga

Key behaviour:

- **Height resolution**  
  - If `CCZ_value == "APL"` (Adelaide Park Lands) → extrude **1m**.  
  - Else if `MBHM_value == 9999` → extrude **DummyHeightCap** (Inspector parameter, default 150m).  
  - Else if `MBHM_value > 0` → extrude that value (metres).  
  - Else if `MBHL_value > 0` → extrude `MBHL_value * LevelHeight`.  
  - Else → `DefaultHeight` (Inspector parameter, default 10m).

- **Colour resolution**  
  - If `CCSZ_name` matches a recognised **Capital City Subzone**, apply a **hard-coded colour**.  
  - Else → grey (`#cccccc`).  
  - Zones are **not** used for colouring (simplified approach).

---

## 🛑 Common Mistakes Made

These are the pitfalls we’ve encountered and corrected:

1. **Attribute mismatches**  
   - CityEngine only auto-maps `attr` if the names **exactly match** GIS field names (case, underscores).  
   - Fixed by aligning to lowercase/underscore field names (e.g. `MBHM_value`, `CCZ_value`, `CCSZ_name`).

2. **Functions in CGA**  
   - Tried defining helper functions (`getZoneColor()`, `getSubzoneColor()`) → ❌ invalid.  
   - CGA doesn’t support custom functions.  
   - ✅ Fixed by using inline `case` statements directly inside rule attributes.

3. **Mid-file `attr` declarations**  
   - Adding `attr` after rules → ❌ caused `Unexpected token: attr`.  
   - ✅ All `attr` declarations must be at the very top of the file.

4. **Version mismatches**  
   - Used `version "2022.1"` → ⚠ warnings in CityEngine 2025.  
   - ✅ Now always set `version "2025.0"`.

5. **Over-complicated colour toggles**  
   - Tried zone/subzone toggles and auto-modes. Too complex and error-prone.  
   - ✅ Simplified: colour **only by subzone**, else grey.

6. **Park Lands handling**  
   - Originally left uncontrolled → extruded absurd heights.  
   - ✅ Rule hard-coded: `CCZ_value == "APL"` → 1m.

7. **Dummy height values**  
   - Parcels with `MBHM_value == 9999` stretched infinitely.  
   - ✅ Added Inspector parameter `DummyHeightCap` (default 150m).

---

## ✅ Current Best Practices

- **Use inline `case` statements** for height and colour.  
- **Keep rules simple** — avoid toggles unless strictly necessary.  
- **Map only by subzone names** (zone colours removed for clarity).  
- **Default everything to grey** unless a subzone explicitly matches.  
- **Always declare all `attr` fields first** and align exactly with GIS schema.  
- **Cap dummy heights** with a parameter.  
- **Special case Park Lands** to 1m extrusion.  
- **Use `version "2025.0"`** to match current CityEngine.  

---

## 📊 Current Rule Flow

```text
01_Parcel_Rules.cga
 └── Lot (@StartRule)
       │
       ▼
       colour(getColor)   ← by CCSZ_name, else grey
       extrude(getExtrusion)
