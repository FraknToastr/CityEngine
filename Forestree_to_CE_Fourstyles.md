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

## 2. Create Master Crosswalk (Schematic Key)

The crosswalk links **genus/species** names from Forestree to the available vegetation `.glb` assets in CityEngine.  

### Step 1. Generate file list of ESRI.lib vegetation assets
1. Open a Windows **CMD shell** and run:  

   ```cmd
   dir /S /B > filelist.txt
   ```

   - Run this inside:  
     ```
     E:\Work\City Engine\Default Workspace\ESRI.lib\assets\Webstyles\Vegetation
     ```
   - This creates a flat text file (`filelist.txt`) containing all `.glb` files and their paths.

2. Use **Power Query** in Excel to transform this list:
   - Split out folder and filename parts  
   - Normalize the filename into `Genus` and `Species` columns  
   - Create a simplified lookup table of vegetation assets

This became the **starting point** for the Master Crosswalk Schematic Key.

---

### Step 2. Initial Header Row (very simple)

```text
common_name, genus, species
```

**Example (start of process):**

| common_name   | genus      | species       |
|---------------|------------|---------------|
| River Red Gum | Eucalyptus | camaldulensis |
| Jacaranda     | Jacaranda  | mimosifolia   |
| London Plane  | Platanus   | x acerifolia  |

---

### Step 3. Add Join Key

- Create a new column `Key` in both datasets.  
- In Forestree:  
  ```
  Key = genus + species
  ```
  (capitalize + trim spaces)  
- In Crosswalk:  
  ```
  Key = Genus + Species
  ```
- This allows a **direct join** on scientific names, with fallback to genus if no exact species match.

---

### Step 4. Final Header Row (enriched)

```text
common_name, genus, species, Genus, Species, Model_type, MatchType, asset_file, Key
```

**Example (final version):**

| common_name   | genus      | species       | Genus      | Species       | Model_type | MatchType      | asset_file                                 | Key                     |
|---------------|------------|---------------|------------|---------------|------------|----------------|--------------------------------------------|-------------------------|
| River Red Gum | Eucalyptus | camaldulensis | Eucalyptus | Camaldulensis | Schematic  | Species match  | assets/Trees/Schematic/EucalyptusCam.glb   | EucalyptusCamaldulensis |
| Jacaranda     | Jacaranda  | mimosifolia   | Jacaranda  | Mimosifolia   | Schematic  | Species match  | assets/Trees/Schematic/JacarandaMim.glb    | JacarandaMimosifolia    |
| London Plane  | Platanus   | x acerifolia  | Platanus   | X acerifolia  | Schematic  | Genus fallback | assets/Trees/Schematic/PlatanusGeneric.glb | PlatanusX acerifolia    |
| Unknown Tree  |            |               |            |               | Schematic  | Unknown        | assets/Trees/Schematic/Unknown.glb         |                         |

This final CSV is the **MasterCrosswalk_Schematic_Key.csv**.

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
   assets/Trees/Schematic/
   assets/Trees/Fan/
   ```

---

## 4. Generate Four-Path CSV with Python

Use the included script **ForestreeFullPath.py** (or ArcGIS toolbox **ForestreeFullPath.pyt**).  

This creates:
- `FinalAsset_LowPoly`  
- `FinalAsset_Realistic`  
- `FinalAsset_Schematic`  
- `FinalAsset_Fan`  
- `FinalAsset` (chosen default style, e.g. LowPoly)  

Each column contains the **full baked path**:

```text
assets/Trees/LowPoly/EucalyptusCamaldulensis.glb
assets/Trees/Realistic/EucalyptusCamaldulensis.glb
assets/Trees/Schematic/EucalyptusCamaldulensis.glb
assets/Trees/Fan/EucalyptusCamaldulensis.glb
```

### Python Output Metrics
When the script runs, it prints summary statistics:  
- **Species+Genus match** — number of exact matches  
- **Genus only fallback** — number of genus-level matches  
- **Unknown** — trees with no matching asset, assigned `Unknown.glb`  

---

## 5. Create Forestree Feature Class (ArcGIS Pro)

1. Use the **XY to Table** tool in ArcGIS Pro:
   - Input: `Forestree_WithAssets_FullPath.csv`
   - X field: `lng`
   - Y field: `lat`
   - Coordinate System: **GCS_WGS_1984**

2. Use the **Project** tool to convert into **GDA2020 MGA Zone 54**:
   - Output CS: `GDA2020Z54`

3. Save the feature class into your CityEngine workspace geodatabase.

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

- **At the end:**  
  Enriched with join keys and asset mapping —  
  `common_name, genus, species, Genus, Species, Model_type, MatchType, asset_file, Key`.

---

## 📂 Repo Contents

- `ForestreeFullPath.py` – Python script  
- `ForestreeFullPath.pyt` – ArcGIS Python Toolbox  
- `Forestree_FullPath_PowerQuery.txt` – Power Query script  
- `TreeRule_Final_FullPath.cga` – CityEngine rule  
- `README.md` – this guide  
