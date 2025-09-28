# Adelaide Digital Twin – CityEngine CGA Rules

This repository contains a complete set of **CGA rule files** for building a 3D Digital Twin of the City of Adelaide in Esri CityEngine. These rules are aligned with the **South Australian Planning and Design Code (PDI Act)** and are designed to map parcels, zones, and subzones into extruded massings that reflect planning constraints.

---

## 📂 File Overview

### 01_Parcel_Rules.cga
- Handles **parcel-level attributes** from the cadastre.
- Reads Planning & Design Code overlay fields (e.g. `CCZ_value`, `CCSZ_name`, `MBHM_value`, `MBHL_value`).
- Resolves **extrusion height**:
  - If `MBHM_value == 9999` → apply Inspector parameter `DummyHeightCap` (default 150m).
  - Else if `MBHM_value > 0` → use that value in metres.
  - Else if `MBHL_value > 0` → multiply by `LevelHeight` (default 3.5m).
  - Else → fallback to `DefaultHeight` (default 10m).
  - Special case: if `CCZ_value == "APL"` (Adelaide Park Lands), extrusion is fixed to **1m**.
- Applies **colour mapping** by `CCSZ_name` (Capital City Subzones):
  - *Adelaide Aquatic Centre* → `#4DB6AC`  
  - *City Frame* → `#80CBC4`  
  - *Cultural Institutions* → `#9575CD`  
  - *City High Street* → `#AED581`  
  - *Entertainment* → `#F06292`  
  - *East Terrace* → `#64B5F6`  
  - *Gouger and Grote Street* → `#BA68C8`  
  - *Health* → `#81C784`  
  - *Hindley Street* → `#FF8A65`  
  - *Innovation* → `#4FC3F7`  
  - *Medium-High Intensity* → `#FFF176`  
  - *Melbourne Street West* → `#A1887F`  
  - *North Adelaide Low Intensity* → `#90A4AE`  
  - *Rundle Mall* → `#F48FB1`  
  - *Rundle Street* → `#81D4FA`  
  - Else → grey (`#cccccc`).

---

## 🚀 Usage

1. Place the `.cga` files in your CityEngine project’s `/rules` folder.
2. Assign `01_Parcel_Rules.cga` as the rule file in the Inspector.
3. Ensure your cadastre feature class has the required attribute fields exactly matching:
   - `CCSZ_name`
   - `CCZ_value`
   - `NACZ_value`
   - `IZ_value`
   - `MBHM_value`
   - `MBHL_value`
4. Apply the rule to parcel geometries to generate extrusions.

---

## 📝 Best Practices and Lessons Learned

- **Exact attribute matching**: CGA `attr` names must exactly match GIS field names (case and underscores).
- **Dummy values**: Handle placeholders (`9999`) using a parameterised cap (`DummyHeightCap`).
- **Park Lands handling**: All parcels with `CCZ_value == "APL"` are extruded to **1m**, regardless of overlay values.
- **Colour simplicity**: Colours are hard-coded by subzone. All non-subzoned parcels default to grey.
- **Functions**: Avoid defining custom functions like `getZoneColor()`; instead inline logic in `case` statements.
- **Syntax safety**:
  - Every operation on its own line (e.g. `extrude(10)` not chained).
  - No stray characters after rule definitions.
  - Use ASCII identifiers only (avoid special characters like `ç`).
- **Modularisation** (if extended):
  - Keep attribute handling separate (`10_parcel_attribs.cga`).
  - Envelope generation (`20_envelope.cga`).
  - Zone/subzone-based logic (`30_landuse.cga`).
  - Heritage overrides (`40_heritage.cga`).
  - Main entry point (`99_main.cga`).

---

## 🔮 Next Steps

- Extend colour mapping to include **all zones and overlays** from the Planning & Design Code.
- Add optional Inspector toggles for **neutral greyscale view** vs **subzone colouring**.
- Integrate with `40_heritage.cga` to apply heritage overrides (State, Local, Adjacent).
- Expand modular rules into the recommended package (`00_config.cga`, `10_parcel_attribs.cga`, etc.) for reusability and clarity.

---

## 📄 Example Rule Flow

```text
01_Parcel_Rules.cga
 └── Lot (@StartRule)
       │
       ▼
       colour(getColor)
       extrude(getExtrusion)
