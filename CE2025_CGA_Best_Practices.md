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
