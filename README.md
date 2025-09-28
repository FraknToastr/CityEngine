# CGA Rules — Do’s and Don’ts (2025.0)

This guide is a quick-reference for writing **clean, compatible, and bug-free CGA rules** in CityEngine **2025.0**. It captures lessons learned from common errors and best practices.

---

## ✅ Do’s

- **Always declare the version at the top**
  ```cga
  version "2025.0"
  ```
  Ensures compatibility with the current syntax.

- **Use modern attribute annotations**
  ```cga
  @Range(min=5, max=200, restricted=false)
  attr BuildingHeight = 50
  ```
  🔹 Don’t use deprecated forms like `@Range(5,200)`.

- **Space-separate arguments** in functions like `setback()`  
  ```cga
  setback(2 2 0 0) Building
  ```
  (No commas allowed!)

- **Use `@StartRule` once per file**  
  ```cga
  @StartRule
  Lot -->
      Building
  ```

- **Organize with groups** (but only as comments/labels in newer versions)  
  ```cga
  # --- Podium Rules ---
  ```

- **Case conditions** with explicit comparisons:  
  ```cga
  case FrontEdge == 0 : setback(2 2 0 0) Building
  else : setback(0 0 0 0) Building
  ```

- **Check geometry orientation** using `scope` or `geometry` queries when needed, rather than assuming edges.

- **Keep modular**  
  - Separate podium, tower, roof into dedicated rules.  
  - Import helper CGA files carefully to avoid **import cycles**.

---

## ❌ Don’ts

- **Don’t use commas in numeric argument lists**
  ```cga
  setback(2, 2, 0, 0)   # ❌ Wrong
  setback(2 2 0 0)      # ✅ Correct
  ```

- **Don’t duplicate rule names**  
  Each rule name must be unique per file:
  ```cga
  # ❌ Duplicate
  CCSZ_color -->
  CCSZ_color -->
  ```

- **Don’t use HTML/JavaScript comment syntax**
  ```cga
  <!-- comment -->   # ❌ Wrong
  # comment          # ✅ Correct
  ```

- **Don’t assume functions exist in all versions**
  - `color(float,float,float)` ✅  
  - `color(str)` ❌ (not valid)  
  - Check the [CGA reference](https://doc.arcgis.com) for valid signatures.

- **Don’t import the same file into itself**  
  ```cga
  import "Parcel_Rules_01.cga"   # inside Parcel_Rules_01.cga ❌
  ```

- **Don’t leave rules unterminated**  
  Always complete rules with either:
  - another rule call,  
  - a shape operation (e.g. `extrude`, `offset`), or  
  - a geometry creation (e.g. `color`, `setupProjection`).

---

## ⚠️ Common Pitfalls & Fixes

| Error | Meaning | Fix |
|-------|---------|-----|
| `Unexpected token: ,` | Used commas in `setback()` or `extrude()` args | Replace commas with spaces |
| `Unexpected token: {` | Misplaced braces (CGA is not C/JS) | Remove braces, use `case` or nested rules |
| `Unexpected token: else` | Improper `else` without preceding `case` | Ensure `case ... else ...` pattern |
| `No such function: color(str)` | Wrong function signature | Use `color("#rrggbb")` or `color(r,g,b)` |
| `An import cycle was detected` | A file imported itself or circularly | Break imports into utility files |
| `Unknown rule: prt::generate failed` | No `@StartRule` or rule entry not found | Define `@StartRule` at top |

---

## 🧩 Recommended Workflow

1. **Start minimal**: write a small rule that only extrudes.  
2. **Add attributes**: height, setbacks, toggles.  
3. **Layer complexity**: podiums, towers, roofs.  
4. **Test imports carefully**: split zones, colors, and geometry into helper files.  
5. **Validate often**: errors cascade quickly — fix syntax immediately.  

---

## 📌 Example — Minimal Interactive Rule

```cga
version "2025.0"

@Range(min=5, max=200, restricted=false)
attr BuildingHeight = 50

@Range(min=0, max=10, restricted=false)
attr SetbackFront = 2

@StartRule
Lot -->
    setback(SetbackFront 0 0 0) Building

Building -->
    extrude(BuildingHeight)
    color("#88ccee")
```

---

🔗 **Reference**:  
- [Esri CGA Reference 2025.0](https://doc.arcgis.com/en/cityengine/latest/cga/cga-reference.htm)  
- [CGA Language Guide](https://doc.arcgis.com/en/cityengine/latest/cga/cga-language.htm)  
