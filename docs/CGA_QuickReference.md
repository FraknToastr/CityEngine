# 📌 CityEngine CGA Quick Reference

A one-page cheat sheet of **CGA essentials** — common errors, fixes, and a pre-flight checklist.  

---

## ✅ Checklist Before Compiling
- [ ] `StartRule` is defined and spelled correctly.  
- [ ] All `case` statements have an `else`.  
- [ ] File ends with a newline (avoid EOF errors).  
- [ ] Asset paths are **relative** to project (`assets/Trees/...`).  
- [ ] Required attributes exist in the dataset schema.  
- [ ] Use `report()` to confirm attributes load correctly.  
- [ ] Save `.cga` files inside the CityEngine workspace.  
- [ ] Test with a single shape before applying to full layer.  

---

## 🩺 Troubleshooting Common Errors

| Problem                         | Cause                                                                 | Fix                                                                 |
|---------------------------------|----------------------------------------------------------------------|---------------------------------------------------------------------|
| **Unexpected token }**          | Inline `setback` block with parameters in CE2025                     | Replace with `offset(-distance)` or restructure rule                 |
| **Unexpected token :**          | Used colon form `comp(top) : Rule`                                   | Must use braces → `comp(top) { Rule }`                              |
| **Unexpected end of file**      | Missing newline or unclosed `case` without `else`                    | Add final newline; ensure all `case` blocks have `else`              |
| **StartRule not found**         | No `StartRule` defined or misspelled                                 | Add `StartRule -->` as entry point                                   |
| **Asset not found in ResolveMap** | Wrong relative path, missing `.glb`, or misplaced folder             | Verify `assets/` folder structure; check file names and extensions   |
| **Rule won’t assign to layer**  | Attributes in `.cga` not in dataset schema                           | Add missing attributes in dataset or remove from CGA                 |
| **All shapes render white**     | Asset missing texture or `Unknown.glb` used                          | Check textures folder; confirm material references                   |

---

## 📝 Minimal Rule Example

```cga
// Attributes
attr FinalAsset = "assets/Trees/LowPoly/Unknown.glb"
attr height_m = 10
attr canopy_m = 6

// Start Rule
StartRule -->
    Tree

Tree -->
    case FinalAsset != "" :
        i(FinalAsset)
        s(canopy_m, height_m, canopy_m)
        report("tree.asset", FinalAsset)
    else :
        NIL
```

---

⚡ This page is designed to be a **grab-and-go reference** during development.  
