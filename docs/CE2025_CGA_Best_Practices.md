# CityEngine CGA Best Practices – Categorised by Version

This document collects lessons, rules, and debugging notes from working with **CGA rule files** in different versions of **CityEngine**.  
It is structured by **version number** so you can quickly check which syntax and behaviours apply.

---

## ✅ General CGA Best Practices (All Versions)

- Always define a **`StartRule`** — required entry point.
- Keep **braces `{ }`** clean and consistent. Avoid inline one-liners that combine multiple braces/blocks.
- Provide **fallback cases** for missing or invalid attributes.
- Use `report("AttributeName", value)` liberally for debugging.
- Save `.cga` files directly inside CE to avoid encoding/BOM issues.
- Use **clear, descriptive rule names** (e.g., `TreeRule_Final`, `BuildingMassing`).
- Keep a **single StartRule** entry point per CGA file.
- Define all user-controllable parameters with `attr` at the top, with **default values** to prevent compilation errors.
- Use meaningful names (`height_m`, `canopy_m`, `style`) instead of generic ones.
- Always provide `else` fallbacks in `case` statements to avoid empty geometry.
- Reference assets with **relative paths** to ensure portability.
- Encapsulate `i(path)` inside helper rules/functions for clarity (e.g., `InsertTree(path)`).
- Use a **default/unknown asset** as a visual placeholder when no match is found.
- Tie scaling (`s(x,y,z)`) to attributes or data fields when possible; randomize within realistic ranges if data is missing.
- Use **debug colors** or primitive geometry during development to validate rule flow.
- Keep CGA rules **modular** — separate tree rules, building rules, and utilities.
- Store assets in structured subfolders (`/assets/Trees/LowPoly/`).
- Version control CGA files with meaningful names (`TreeRule_v2.cga`).

---

## 🚀 Performance Optimization Best Practices

- **Use Levels of Detail (LOD):** Provide simplified models for far distances, detailed models only when close.
- **Proxy geometry:** Replace high-poly assets with low-poly or schematic proxies for faster navigation and previews.
- **Batch complexity:** Avoid generating thousands of unique complex geometries at once. Use shared assets when possible.
- **Reduce texture load:** Use common/shared materials, compress textures, and limit the number of unique texture files.
- **Randomization with care:** Apply variation sparingly — e.g., random colors, rotation, and scale — but avoid unique mesh generation if unnecessary.
- **Cull invisible geometry:** Do not generate faces or volumes that will never be seen (e.g., underground volumes, backsides hidden by podiums).
- **Optimize rule structure:** Simplify long chains of case/if logic; consolidate repeated patterns into helper rules.
- **Use reporting:** Track how many geometries and assets are being instantiated to avoid exceeding memory limits.

### Example: LOD Switching Rule
```cga
attr LOD = "Low"

Tree -->
    case LOD == "Low" :
        i("assets/Trees/LowPoly/EucalyptusCamaldulensis.glb")
    case LOD == "Med" :
        i("assets/Trees/Crosswalk/EucalyptusCamaldulensis.glb")
    case LOD == "High" :
        i("assets/Trees/Realistic/EucalyptusCamaldulensis.glb")
    else :
        i("assets/Trees/Fan/EucalyptusCamaldulensis.glb")
```

### Example: Proxy Usage
```cga
Building -->
    case LOD == "Low" :
        extrude(10) color("#cccccc")    // simple proxy mass
    else :
        DetailedBuilding

DetailedBuilding -->
    extrude(10)
    comp(f) { front : Facade | side : Wall | top : Roof }
```

---

## 🩺 Troubleshooting Common Errors

| Problem                         | Cause                                                                 | Fix                                                                 |
|---------------------------------|----------------------------------------------------------------------|---------------------------------------------------------------------|
| **Unexpected token }**          | Inline `setback` block with parameters in CE2025                     | Replace with `offset(-distance)` or restructure rule                 |
| **Unexpected token :**          | Used colon form `comp(top) : Rule`                                   | Must use braces → `comp(top) { Rule }`                              |
| **Unexpected end of file**      | File missing newline at end, or unclosed `case` without `else`        | Add final newline; ensure all `case` blocks have `else`              |
| **StartRule not found**         | No `StartRule` defined or misspelled                                 | Add `StartRule -->` as entry point                                   |
| **Asset not found in ResolveMap** | Wrong relative path, missing `.glb` file, or misplaced assets folder | Verify `assets/` folder structure; check file names and extensions   |
| **Rule won’t assign to layer**  | Attributes referenced in `.cga` not in layer schema                  | Add missing attributes in dataset or remove from CGA                 |
| **All shapes render white**     | Asset missing texture or default `Unknown.glb` used                   | Check textures folder, ensure correct material paths                 |

---

## 📋 Checklist Before Compiling

- ✅ Ensure `StartRule` is defined and spelled correctly.
- ✅ Verify all `case` statements end with an `else` branch.
- ✅ Confirm there’s a newline at the end of the file.
- ✅ Make sure all asset paths are **relative** to the project folder.
- ✅ Check that required attributes exist in the source dataset schema.
- ✅ Test rule with a simple geometry before applying to a full layer.
- ✅ Use `report()` to confirm attribute values are being read correctly.
- ✅ Save `.cga` file inside CityEngine workspace (not external editor with BOM issues).

---

## 🏗️ CityEngine 2024.x

- **`setback` syntax** is more permissive:
  - Both `{ remainder : Rule }` and simple `setback(distance) Rule` forms generally work.
  - Safer for passing parameters to rules.
- Debugging is simpler: “Unexpected token” errors usually indicate a real brace mismatch.
- Podium + tower rules can be written with `setback` directly.

**Example (CE2024 podium/tower):**
```cga
TopShape(h) -->
    setback(5) { remainder : Tower(h) }
```

---

## 🏙️ CityEngine 2025.0

- **`setback` syntax is stricter**:
  - Inline braces with parameters often cause `Unexpected token }` or `Unexpected token Rule`.
  - Recommended to **replace `setback` with `offset(-distance)`** when creating towers above podiums.
- **`comp()` must always use braces**:
  - Valid: `comp(top) { TopShape }`
  - Invalid: `comp(top) : TopShape`
- End-of-file errors (`Unexpected end of file`) are often due to:
  - Trailing spaces without newline
  - Unclosed `case` without `else`
- **Attribute Binding**: CE2025 blocks rule assignment if attributes referenced in the `.cga` don’t exist in the layer schema.

**Example (CE2025 safe podium/tower):**
```cga
PodiumTower -->
    extrude(15)
    color("#ff0000")
    comp(top) { TowerTop }

TowerTop -->
    offset(-5)
    extrude(45)
    color("#0000ff")
```

---

## 🌳 Special Parcels: Adelaide Park Lands

- Parcels with **0 metres and 0 levels** → always extrude **1m flat** and colour **forest green (#228B22)**.
- Excluded from podium/tower rules unless explicitly required by planning code.

---

## 📏 Height Envelope Rules (Test 7 series)

### Attributes
- `MaxMetres_value_dbl` → preferred when present.
- `MaxLevels_value_dbl` → used if metres missing/disabled.
- `UseMetres` toggle:
  - `1` → force metres
  - `0` → force levels
  - `-1` → auto (prefer metres, else levels)

### Caps
- **9999 metres** → capped to **120m** (colour = **magenta #ff00ff**).

### Colour Mapping
From **MaxHeights.xlsx**:

- **Metres values:** 8.5, 11, 14, 15, 18, 22, 28, 29, 34, 36, 43, 53, 120 (cap)
- **Levels values:** 1, 2, 3, 4, 5, 6, 14

Each assigned a unique colour.

### Reporting
- `report("HeightSource", "...")` outputs classification in Inspector:
  - `Metres`, `Levels`, `Parklands (1m)`, or `Fallback`.

---

## 📌 Reference Example Rules (Esri Samples, CE2025)

- `towers_podiums_setbacks.cga`
- `towers_podiums_setbacks_02.cga` ← **most stable, recommended**
- `towers_podiums_simple.cga`

Use these as templates for complex podium + tower scenarios.

---

## ⚠️ Debugging Summary (CE2025)

- **Unexpected token }** → usually inline `setback` block with parameters. Replace with `offset`.
- **Unexpected token :** → caused by colon-form `comp`. Must use braces.
- **Unexpected end of file** → file missing newline or `else`.
- **Rule won’t assign** → attribute mismatch in layer schema.

---
