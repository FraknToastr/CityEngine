import pandas as pd
import os

def forestree_crosswalk_fullpath(forestree_path, crosswalk_path, output_path, style="LowPoly"):
    """
    Enrich Forestree dataset with baked-in full asset paths.
    Produces:
      - FinalAsset_LowPoly
      - FinalAsset_Realistic
      - FinalAsset_Schematic
    and a single FinalAsset column for the chosen style (default = LowPoly).
    """

    # Load
    forestree = pd.read_excel(forestree_path, sheet_name="Forestree")
    crosswalk = pd.read_csv(crosswalk_path)

    # Normalize
    forestree["genus"] = forestree["genus"].astype(str).str.strip().str.capitalize()
    forestree["species"] = forestree["species"].fillna("").astype(str).str.strip().str.capitalize()
    crosswalk["Genus"] = crosswalk["Genus"].astype(str).str.strip().str.capitalize()
    crosswalk["Species"] = crosswalk["Species"].astype(str).str.strip().str.capitalize()

    # Join key
    forestree["Key"] = forestree["genus"] + forestree["species"]
    crosswalk["Key"] = crosswalk["Genus"] + crosswalk["Species"]

    merged = forestree.merge(crosswalk[["Key", "asset_file", "Genus"]], on="Key", how="left")

    # Resolve base filename
    def pick_base(row):
        if pd.notna(row["asset_file"]) and str(row["asset_file"]).strip() != "":
            return os.path.basename(row["asset_file"]), "Species match"
        genus_match = crosswalk.loc[crosswalk["Genus"] == row["genus"]]
        if not genus_match.empty:
            return os.path.basename(genus_match.iloc[0]["asset_file"]), "Genus fallback"
        return "Unknown.glb", "Unknown"

    results = merged.apply(pick_base, axis=1)
    merged["base_file"] = results.apply(lambda x: x[0])
    merged["MatchType"] = results.apply(lambda x: x[1])

    # Build all three paths
    merged["FinalAsset_LowPoly"]   = "assets/Trees/LowPoly/"   + merged["base_file"]
    merged["FinalAsset_Realistic"] = "assets/Trees/Realistic/" + merged["base_file"]
    merged["FinalAsset_Schematic"] = "assets/Trees/Schematic/" + merged["base_file"]

    # Single column for chosen style
    style_map = {
        "LowPoly": "FinalAsset_LowPoly",
        "Realistic": "FinalAsset_Realistic",
        "Schematic": "FinalAsset_Schematic"
    }
    merged["FinalAsset"] = merged[style_map[style]]

    merged.drop(columns=["base_file"]).to_csv(output_path, index=False)

    print(f"✅ Saved enriched dataset to {output_path}")
    print(merged["MatchType"].value_counts())

if __name__ == "__main__":
    forestree_crosswalk_fullpath(
        r"E:\Work\City Engine\Forestree.xlsx",
        r"E:\Work\City Engine\Tree_CE2025_MasterCrosswalk_Schematic_Key.csv",
        r"E:\Work\City Engine\Forestree_WithAssets_FullPath.csv",
        style="LowPoly"
    )
