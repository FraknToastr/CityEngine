# 🌳 CityEngine Tree Workflow

This repo documents the workflow for preparing **Forestree** data for use in **ArcGIS CityEngine**.  
The process ensures that every tree record is linked to a valid `.glb` tree model in **ESRI.lib** (or copied locally), and that CityEngine rules can reference them directly.

---

## 1. Export Forestree Data

1. In **ArcGIS Pro**, open the **Forestree** point feature class or table.  
2. Export the attribute table to **Excel (.xlsx)**.  
   - Sheet name: `Forestree`  
   - Ensure key columns are included:
     - `id`, `asset_id`, `common_name`, `genus`, `species`, `dbh`, `canopy_m`, `height_m`, `lng`, `lat`, etc.

---

## 2. Create the Crosswalk with Key (AI Assisted)

The **Crosswalk with Key** is the lookup table that links **genus/species** names from Forestree to the available vegetation `.glb` assets in CityEngine.  
This step is partly manual (generating and transforming a file list) and partly automated (AI-assisted name matching).

---

### Step 1. Generate raw file list from ESRI.lib

Run this in a Windows CMD shell inside the ESRI.lib vegetation folder:

```cmd
dir /S /B > filelist.txt
```

Example `filelist.txt` output:

```
E:\Work\City Engine\Default Workspace\ESRI.lib\assets\Webstyles\Vegetation\LowPoly\EucalyptusCamaldulensis.glb
E:\Work\City Engine\Default Workspace\ESRI.lib\assets\Webstyles\Vegetation\Realistic\JacarandaMimosifolia.glb
E:\Work\City Engine\Default Workspace\ESRI.lib\assets\Webstyles\Vegetation\Fan\PlatanusGeneric.glb
```

---

### Step 2. Transform file list with Power Query

Import `filelist.txt` into Excel/Power BI with **Power Query** and transform it:

- Split the path by `\` delimiter.  
- Keep only the folder name (model type) and filename.  
- Remove the `.glb` extension.  
- Rename headers.

The result is **CE2025_Esri.lib_assets.txt** with headers:

```text
Model_type, Filename
```

Example:

| Model_type | Filename                |
|------------|-------------------------|
| LowPoly    | EucalyptusCamaldulensis |
| Realistic  | JacarandaMimosifolia    |
| Fan        | PlatanusGeneric         |

---

### Step 3. Prepare Forestree input

From Step 1, export Forestree attributes to **Forestree.xlsx** (sheet `Forestree`).  

Header row:

```text
id, asset_id, common_name, genus, species, dbh, canopy_m, height_m, lng, lat, ...
```

---

### Step 4. AI-Assisted Crosswalk Creation

Provide both files to the AI:  
- **Forestree.xlsx**  
- **CE2025_Esri.lib_assets.txt**

The AI will:  
- Normalize names (capitalize, trim).  
- Create a **Key** in both datasets:  
  - Forestree: `Key = genus + species`  
  - Assets: `Key = Genus + Species`  
- Match on **species+genus**, fall back to **genus only**, or flag as **Unknown**.  

---

### Step 5. Output Crosswalk with Key

The AI outputs **Tree_CE2025_MasterCrosswalk_withKey.csv** with headers:

```text
common_name, genus, species, Genus, Species, MatchType, asset_file, Key
```

Example:

| common_name   | genus      | species       | Genus      | Species       | MatchType      | asset_file                              | Key                     |
|---------------|------------|---------------|------------|---------------|----------------|-----------------------------------------|-------------------------|
| River Red Gum | Eucalyptus | camaldulensis | Eucalyptus | Camaldulensis | Species match  | assets/Trees/LowPoly/EucalyptusCam.glb  | EucalyptusCamaldulensis |
| Jacaranda     | Jacaranda  | mimosifolia   | Jacaranda  | Mimosifolia   | Species match  | assets/Trees/Realistic/JacarandaMim.glb | JacarandaMimosifolia    |
| London Plane  | Platanus   | x acerifolia  | Platanus   | X acerifolia  | Genus fallback | assets/Trees/Fan/PlatanusGeneric.glb    | PlatanusX acerifolia    |
| Unknown Tree  |            |               |            |               | Unknown        | assets/Trees/LowPoly/Unknown.glb        |                         |

---

## 3. Move `.glb` Files from ESRI.lib

1. Copy vegetation `.glb` assets out of your CityEngine installation:  

   ```
   <workspace>\ESRI.lib\assets\Webstyles\Vegetation
   ```

2. Place them into your project under:

   ```
   CityEngine_Tour/assets/Trees/
   ```

3. Maintain four subfolders:
   ```
   assets/Trees/LowPoly/
   assets/Trees/Realistic/
   assets/Trees/Crosswalk/
   assets/Trees/Fan/
   ```

---

## 4. Generate Four-Path CSV with Python

Use the included script **ForestreeFullPath.py** (or ArcGIS toolbox **ForestreeFullPath.pyt**).  

This creates:
- `FinalAsset_LowPoly`  
- `FinalAsset_Realistic`  
- `FinalAsset_Crosswalk`  
- `FinalAsset_Fan`  
- `FinalAsset` (chosen default style, e.g. LowPoly)  

Each column contains the **full baked path**.

### Python Output Metrics
When the script runs, it prints summary statistics:  
- **Species+Genus match** — number of exact matches  
- **Genus only fallback** — number of genus-level matches  
- **Unknown** — trees with no matching asset, assigned `Unknown.glb`  

---

## 5. Create Forestree Feature Class (ArcGIS Pro)

1. Use the **XY Table to Point** tool in ArcGIS Pro:
   - Input: `Forestree_WithAssets_FullPath.csv`
   - X field: `lng`
   - Y field: `lat`
   - Coordinate System: **GDA2020 MGA Zone 54** (set in the *Environment* tab)

2. Save the feature class into your CityEngine workspace geodatabase.  
   - Projection is already applied in this step — no need to run the Project tool separately.

---

## 6. CityEngine Rule

Attach the `TreeRule_Final_FullPath.cga` rule to the imported feature class.  

- **Accurate scaling:**  
  - If `height_m` and `canopy_m` > 0, the tree is scaled to those real-world values.  
  - This produces trees with the correct *relative* size compared to one another.

- **Fallback scaling:**  
  - If `height_m` or `canopy_m` is missing or 0, a **random size** is chosen within a realistic range (e.g. canopy 2–10 m, height 5–20 m).  
  - This prevents blank or tiny trees, while still keeping visual variety.

- **Unknown trees:**  
  - If a species/genus cannot be matched in the Crosswalk, it defaults to **`Unknown.glb`**.  
  - `Unknown.glb` is deliberately **white**, so these trees stand out visually in CityEngine.  
  - This provides a quick diagnostic for gaps in the crosswalk or missing assets.

---

## 7. Summary of Crosswalk Iteration

- **At the start:**  
  Header was minimal — `common_name, genus, species`.  

- **At the end (AI output):**  
  Enriched with join keys and asset mapping —  
  `common_name, genus, species, Genus, Species, MatchType, asset_file, Key`.

---

## 📂 Repo Contents

- `ForestreeFullPath.py` – Python script  
- `ForestreeFullPath.pyt` – ArcGIS Python Toolbox  
- `Forestree_FullPath_PowerQuery.txt` – Power Query script  
- `TreeRule_Final_FullPath.cga` – CityEngine rule  
- `README.md` – this guide  
