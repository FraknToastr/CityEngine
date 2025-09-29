# 🏗️ CE2025.0 CGA Best Practices – Project Reference

This document summarises **best practices** for working with **CityEngine 2025.0 CGA rule files**, based on analysis of 208 example and tutorial files from Esri’s official distribution.

---

## 1. General Structure
- Always include a **Start Rule** – CE2025.0 enforces stricter parsing and rules will fail without it.
- Use **attributes** (`attr`) to parameterise values (heights, materials, booleans) instead of hardcoding.
- Group related rules logically with clear comments.

## 2. Imports & Utilities
- Use `import` for reusability, but CE2025.0 requires correct paths and naming.
- Keep **utility CGA files** (arrays, colors, CIM utils, etc.) in a shared folder and import them consistently.
- Avoid circular imports – CE2025.0 parser rejects them.

## 3. Geometry & Perimeters
- Use `setback`, `extrude`, and perimeter operators consistently for predictable envelopes.
- Leverage **orientation rules** (`edge`, `scope`, `alignScopeToAxes`) to control building massing.
- Validate geometry with reporting (`report`, `print`) to avoid unexpected results.

## 4. Streets & Lanes
- Modularise lane definitions (`Car_Lane.cga`, `Bike_Lane.cga`, etc.) and import into street templates.
- Keep **materials and lane markings** in separate files for easier swapping.
- Use **queries** (e.g., `Lane_Queries.cga`) for debugging attributes along networks.

## 5. Facades & Roofs
- Separate facade logic (`Facade_Textures.cga`, `gen_AdvancedFacade...`) from mass models.
- Always define **fallback materials** to avoid errors if textures are missing.
- Roofs should be modular (`flatroof.cga`, `brickroof.cga`) and parameter-driven.

## 6. Landscaping & Furniture
- Use distributors (`Plant_Distributor.cga`, `Row_Distributor.cga`) for controlled randomness.
- Keep **street furniture** (bollards, lamps, racks) as reusable CGA modules.
- Maintain scale consistency to avoid oversized elements.

## 7. Reporting & QA
- Use `report` to capture key metrics (GFA, site coverage, FSR, open space).
- Create dedicated reporting scripts (`reporting_01-04.cga`) for compliance checking.
- Use reports during iteration – they integrate well into dashboards.

## 8. Advanced Patterns
- Use **dynamic imports** (`dynamic_imports_01-05.cga`) cautiously; ensure all targets exist.
- Break large scripts into **perimeter / massing / facade / roof / landscape** components.
- When experimenting, use simplified placeholders (`simpleBuilding_01.cga`) before applying detailed rules.

## 9. Error Handling
- Always test new rules with **simple extrusions** before layering complexity.
- Include fallback cases (`Error.cga`) to catch unsupported geometry.
- Comment generously when using advanced CGA functions.

---

### ✅ Key Takeaways
- **Always define a Start Rule.**
- **Parameterise everything with attributes.**
- **Keep modules small and reusable.**
- **Use reports for QA and compliance.**
- **Organise scripts into categories:** Perimeter → Massing → Facade → Roof → Furniture → Landscaping.

---

This README is designed as a **living reference** for future City of Adelaide CGA rule development and can be extended with project-specific patterns (e.g., Plan & Design Code envelopes, heritage overlays, podium/tower setbacks).
