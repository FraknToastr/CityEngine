# -*- coding: utf-8 -*-
# ArcGIS Pro 3.5+ Python Toolbox (.pyt)

import arcpy
import csv
import os
import re
import traceback
from collections import defaultdict
from datetime import datetime


STYLE_LIST = ["LowPoly", "Realistic", "Schematic", "Fan"]
STYLE_PRIORITY = ["LowPoly", "Realistic", "Schematic", "Fan"]
REQUIRED_FIELDS = ["common_name", "genus", "species"]
# Project-specific fallback preferences inferred from expected output behavior.
GENUS_FALLBACK_OVERRIDES = {"quercus": "QuercusRubra"}
GENUS_FORCE_UNKNOWN_FALLBACK = {"stump"}


def _collapse_spaces(value):
    text = "" if value is None else str(value)
    return " ".join(text.strip().split())


def _display_normalize(value):
    text = _collapse_spaces(value)
    if not text:
        return ""
    # Match prior workflow behavior where genus/species are capitalized.
    return text.capitalize()


def _tokenize(value):
    text = _collapse_spaces(value).lower()
    return re.sub(r"[^a-z0-9]+", "", text)


def _stem_genus(stem):
    match = re.match(r"^([A-Z][a-z]+)", stem)
    if match:
        return match.group(1)

    # Fallback for unexpected names that are not CamelCase.
    chars = []
    for index, char in enumerate(stem):
        if index > 0 and char.isupper():
            break
        chars.append(char)
    return "".join(chars) if chars else stem


def _normalize_value(value):
    if value is None:
        return ""
    if hasattr(value, "strftime"):
        try:
            return value.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return str(value)
    return str(value)


def _parse_filelist(filelist_path):
    """
    Build exact/genus lookup indexes from a CityEngine file list text file.
    Expected line formats include either:
      - Fan\\AbiesBalsamea.glb
      - C:\\...\\Vegetation\\LowPoly\\AbiesBalsamea.glb
    """
    base_to_styles = defaultdict(set)
    style_counts = {style: 0 for style in STYLE_LIST}
    style_lookup = {style.lower(): style for style in STYLE_LIST}

    with open(filelist_path, "r", encoding="utf-8-sig") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue

            parts = re.split(r"[\\/]+", line)
            if len(parts) < 2:
                continue

            filename = parts[-1]
            if not filename.lower().endswith(".glb"):
                continue

            style_name = None
            for part in reversed(parts[:-1]):
                style_name = style_lookup.get(part.lower())
                if style_name:
                    break

            if not style_name:
                continue

            stem = os.path.splitext(filename)[0]
            base_to_styles[stem].add(style_name)
            style_counts[style_name] += 1

    stems = sorted(base_to_styles.keys())

    # Species+genus exact lookup, tokenized.
    exact_key_to_stem = {}
    for stem in stems:
        token = _tokenize(stem)
        if token and token not in exact_key_to_stem:
            exact_key_to_stem[token] = stem

    # Genus fallback candidates by genus token.
    genus_to_candidates = defaultdict(list)
    for stem in stems:
        genus_token = _tokenize(_stem_genus(stem))
        if genus_token:
            genus_to_candidates[genus_token].append(stem)

    return base_to_styles, exact_key_to_stem, genus_to_candidates, style_counts


def _pick_species_style(stem, preferred_style, base_to_styles):
    styles = base_to_styles.get(stem, set())
    if preferred_style in styles:
        return preferred_style
    for style in STYLE_PRIORITY:
        if style in styles:
            return style
    return preferred_style


def _build_assets(stem):
    filename = "{0}.glb".format(stem)
    assets = {
        "LowPoly": "assets/Trees/LowPoly/{0}".format(filename),
        "Realistic": "assets/Trees/Realistic/{0}".format(filename),
        "Schematic": "assets/Trees/Schematic/{0}".format(filename),
        "Fan": "assets/Trees/Fan/{0}".format(filename),
    }
    return assets


def _validate_required_fields(in_table):
    field_names = [field.name for field in arcpy.ListFields(in_table)]
    lower_lookup = {name.lower(): name for name in field_names}
    missing = [name for name in REQUIRED_FIELDS if name not in lower_lookup]
    if missing:
        raise ValueError(
            "Input table is missing required field(s): {0}".format(", ".join(missing))
        )
    return lower_lookup


def _resolve_unknown_stem(exact_key_to_stem):
    return exact_key_to_stem.get("unknown", "Unknown")


def _resolve_summary_path(output_path):
    normalized = os.path.normpath(output_path)
    lower_normalized = normalized.lower()

    for workspace_ext in (".gdb", ".sde"):
        marker = lower_normalized.find(workspace_ext)
        if marker >= 0:
            workspace_path = normalized[: marker + len(workspace_ext)]
            dataset_part = normalized[marker + len(workspace_ext) :].strip("\\/")
            dataset_name = os.path.basename(dataset_part) if dataset_part else "output"
            base_name = os.path.splitext(dataset_name)[0] or "output"
            return workspace_path, base_name

    if os.path.isdir(normalized):
        return normalized, "output"

    folder_path = os.path.dirname(normalized) or os.getcwd()
    base_name = os.path.splitext(os.path.basename(normalized))[0] or "output"
    return folder_path, base_name


def _write_matchtype_summary(output_path, stats, row_count):
    report_folder, report_base = _resolve_summary_path(output_path)
    if not os.path.isdir(report_folder):
        os.makedirs(report_folder)

    report_name = "{0}_MatchTypeSummary.txt".format(report_base)
    report_path = os.path.join(report_folder, report_name)

    ordered_match_types = ["Species match", "Genus fallback", "Unknown"]
    lines = [
        "MatchType Summary Report",
        "Generated: {0}".format(datetime.now().isoformat(timespec="seconds")),
        "Output Target: {0}".format(output_path),
        "Rows Processed: {0}".format(row_count),
        "",
    ]

    for match_type in ordered_match_types:
        count = int(stats.get(match_type, 0))
        percent = (float(count) / float(row_count) * 100.0) if row_count else 0.0
        lines.append("{0}: {1} ({2:.2f}%)".format(match_type, count, percent))

    lines.append("")
    lines.append("Total MatchType Rows: {0}".format(sum(int(value) for value in stats.values())))

    try:
        with open(report_path, "w", encoding="utf-8") as handle:
            handle.write("\n".join(lines) + "\n")
        arcpy.AddMessage("MatchType summary report: {0}".format(report_path))
    except Exception as ex:
        fallback_folder = os.path.dirname(report_folder) or report_folder
        fallback_path = os.path.join(fallback_folder, report_name)
        with open(fallback_path, "w", encoding="utf-8") as handle:
            handle.write("\n".join(lines) + "\n")
        arcpy.AddWarning(
            "Could not write report in workspace. Wrote MatchType summary report to: {0}. Reason: {1}".format(
                fallback_path, ex
            )
        )


def _run_crosswalk(
    in_table, filelist_path, out_csv, default_style, species_asset_style, family_field=None
):
    base_to_styles, exact_key_to_stem, genus_to_candidates, style_counts = _parse_filelist(
        filelist_path
    )
    if not exact_key_to_stem:
        raise ValueError("No .glb assets were found in the provided file list.")

    lower_lookup = _validate_required_fields(in_table)
    common_name_field = lower_lookup["common_name"]
    genus_field = lower_lookup["genus"]
    species_field = lower_lookup["species"]
    family_field_name = None
    if family_field:
        family_field_name = lower_lookup.get(family_field.lower())
        if not family_field_name:
            arcpy.AddWarning(
                "Configured family field was not found and will be ignored: {0}".format(
                    family_field
                )
            )

    # Exclude unsupported field types from CSV output.
    source_fields = []
    for field in arcpy.ListFields(in_table):
        if field.type in ("Geometry", "Blob", "Raster"):
            continue
        source_fields.append(field.name)

    output_headers = source_fields + [
        "Key",
        "asset_file",
        "Genus",
        "MatchType",
        "FinalAsset_LowPoly",
        "FinalAsset_Realistic",
        "FinalAsset_Schematic",
        "FinalAsset_Fan",
        "FinalAsset",
    ]

    unknown_stem = _resolve_unknown_stem(exact_key_to_stem)
    folder = os.path.dirname(out_csv)
    if folder and not os.path.isdir(folder):
        os.makedirs(folder)

    arcpy.AddMessage("Start: {0}".format(datetime.now().isoformat(timespec="seconds")))
    arcpy.AddMessage("Input table: {0}".format(in_table))
    arcpy.AddMessage("File list: {0}".format(filelist_path))
    if family_field_name:
        arcpy.AddMessage("Family field mapping: {0}".format(family_field_name))
    arcpy.AddMessage(
        "Asset counts by style: {0}".format(
            ", ".join(
                "{0}={1}".format(style, style_counts.get(style, 0)) for style in STYLE_LIST
            )
        )
    )

    row_count = 0
    stats = {"Species match": 0, "Genus fallback": 0, "Unknown": 0}
    skipped_empty = 0

    with open(out_csv, "w", newline="", encoding="utf-8-sig") as out_handle:
        writer = csv.writer(out_handle)
        writer.writerow(output_headers)

        with arcpy.da.SearchCursor(in_table, source_fields) as cursor:
            for row in cursor:
                row_count += 1
                row_values = [_normalize_value(value) for value in row]
                row_dict = {source_fields[idx]: row_values[idx] for idx in range(len(source_fields))}

                common_name = _collapse_spaces(row_dict.get(common_name_field, ""))
                genus = _display_normalize(row_dict.get(genus_field, ""))
                species = _display_normalize(row_dict.get(species_field, ""))
                key_value = "{0}{1}".format(genus, species)

                if not genus and not species:
                    skipped_empty += 1

                # Keep normalized genus/species in the final output.
                row_dict[common_name_field] = common_name
                row_dict[genus_field] = genus
                row_dict[species_field] = species

                exact_token = _tokenize(key_value)
                chosen_stem = None
                asset_file = ""
                genus_out = ""
                match_type = "Unknown"

                if exact_token and exact_token in exact_key_to_stem:
                    chosen_stem = exact_key_to_stem[exact_token]
                    style_for_asset = _pick_species_style(
                        chosen_stem, species_asset_style, base_to_styles
                    )
                    asset_file = "ESRI.lib/assets/Webstyles/Vegetation/{0}/{1}.glb".format(
                        style_for_asset, chosen_stem
                    )
                    genus_out = genus
                    match_type = "Species match"
                else:
                    genus_token = _tokenize(genus)
                    if genus_token and genus_token in genus_to_candidates:
                        override = GENUS_FALLBACK_OVERRIDES.get(genus_token)
                        if genus_token in GENUS_FORCE_UNKNOWN_FALLBACK:
                            chosen_stem = unknown_stem
                        elif override and override in genus_to_candidates[genus_token]:
                            chosen_stem = override
                        else:
                            chosen_stem = genus_to_candidates[genus_token][0]
                        match_type = "Genus fallback"
                    else:
                        chosen_stem = unknown_stem
                        match_type = "Unknown"

                assets = _build_assets(chosen_stem)
                final_asset = assets[default_style]
                stats[match_type] += 1

                ordered_values = [row_dict.get(field, "") for field in source_fields]
                writer.writerow(
                    ordered_values
                    + [
                        key_value,
                        asset_file,
                        genus_out,
                        match_type,
                        assets["LowPoly"],
                        assets["Realistic"],
                        assets["Schematic"],
                        assets["Fan"],
                        final_asset,
                    ]
                )

    arcpy.AddMessage("Rows processed: {0}".format(row_count))
    arcpy.AddMessage("Species matches: {0}".format(stats["Species match"]))
    arcpy.AddMessage("Genus fallbacks: {0}".format(stats["Genus fallback"]))
    arcpy.AddMessage("Unknowns: {0}".format(stats["Unknown"]))
    if skipped_empty > 0:
        arcpy.AddWarning(
            "Rows with blank genus+species were assigned to Unknown: {0}".format(skipped_empty)
        )
    _write_matchtype_summary(out_csv, stats, row_count)
    arcpy.AddMessage("Output CSV: {0}".format(out_csv))


class Toolbox(object):
    def __init__(self):
        self.label = "Forestree City Engine Model Matcher"
        self.alias = "forestreecityenginemodelmatcher"
        self.tools = [ForestreeCityEngineModelMatcherTool]


class ForestreeCityEngineModelMatcherTool(object):
    def __init__(self):
        self.label = "Forestree City Engine Model Matcher"
        self.description = (
            "Takes a full Forestree table and a CityEngine tree file list, then outputs "
            "the final CSV with MatchType and FinalAsset paths."
        )
        self.canRunInBackground = False

    def getParameterInfo(self):
        p0 = arcpy.Parameter(
            displayName="Input Forestree Table",
            name="in_table",
            datatype="GPTableView",
            parameterType="Required",
            direction="Input",
        )

        p1 = arcpy.Parameter(
            displayName="CityEngine Tree File List (.txt)",
            name="filelist_path",
            datatype="DEFile",
            parameterType="Required",
            direction="Input",
        )

        p2 = arcpy.Parameter(
            displayName="Output Final CSV",
            name="out_csv",
            datatype="DEFile",
            parameterType="Required",
            direction="Output",
        )

        p3 = arcpy.Parameter(
            displayName="Default Style For FinalAsset",
            name="default_style",
            datatype="GPString",
            parameterType="Optional",
            direction="Input",
        )
        p3.filter.type = "ValueList"
        p3.filter.list = STYLE_LIST
        p3.value = "LowPoly"

        p4 = arcpy.Parameter(
            displayName="Style Used For Species-Match asset_file",
            name="species_asset_style",
            datatype="GPString",
            parameterType="Optional",
            direction="Input",
        )
        p4.filter.type = "ValueList"
        p4.filter.list = STYLE_LIST
        p4.value = "Schematic"

        p5 = arcpy.Parameter(
            displayName="Family Field (Optional)",
            name="family_field",
            datatype="Field",
            parameterType="Optional",
            direction="Input",
        )
        p5.parameterDependencies = [p0.name]

        return [p0, p1, p2, p3, p4, p5]

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        in_table = parameters[0].valueAsText
        if not in_table:
            return

        try:
            if parameters[5].altered:
                return
            lower_lookup = {field.name.lower(): field.name for field in arcpy.ListFields(in_table)}
            if "family" in lower_lookup:
                parameters[5].value = lower_lookup["family"]
        except Exception:
            pass

        return

    def updateMessages(self, parameters):
        in_table = parameters[0].valueAsText
        filelist_path = parameters[1].valueAsText
        out_csv = parameters[2].valueAsText

        if in_table:
            try:
                lower_lookup = {field.name.lower() for field in arcpy.ListFields(in_table)}
                missing = [name for name in REQUIRED_FIELDS if name not in lower_lookup]
                if missing:
                    parameters[0].setErrorMessage(
                        "Missing required field(s): {0}".format(", ".join(missing))
                    )
            except Exception:
                pass

        if filelist_path:
            if not filelist_path.lower().endswith(".txt"):
                parameters[1].setWarningMessage(
                    "Expected a .txt file list (tool will still attempt to read it)."
                )

        if out_csv and not out_csv.lower().endswith(".csv"):
            parameters[2].setErrorMessage("Output file must end with .csv")

        return

    def execute(self, parameters, messages):
        in_table = parameters[0].valueAsText
        filelist_path = parameters[1].valueAsText
        out_csv = parameters[2].valueAsText
        default_style = parameters[3].valueAsText or "LowPoly"
        species_asset_style = parameters[4].valueAsText or "Schematic"
        family_field = parameters[5].valueAsText

        try:
            _run_crosswalk(
                in_table=in_table,
                filelist_path=filelist_path,
                out_csv=out_csv,
                default_style=default_style,
                species_asset_style=species_asset_style,
                family_field=family_field,
            )
            arcpy.AddMessage("Completed successfully.")
        except Exception:
            arcpy.AddError("Tool failed.")
            arcpy.AddError(traceback.format_exc())
            raise
