# -*- coding: utf-8 -*-
# ArcGIS Pro 3.5+ Python Toolbox (.pyt)

import arcpy
import base64
import csv
import os
import re
import traceback
from collections import defaultdict
from datetime import datetime


STYLE_LIST = ["LowPoly", "Realistic", "Schematic", "Fan"]
STYLE_PRIORITY = ["LowPoly", "Realistic", "Schematic", "Fan"]
MODEL_LIST_FILENAME = "City Engine Tree Model List.txt"
TREE_DATA_WITH_PATHS_FILENAME = "Tree Data with CE Model Paths.csv"
TREE_RULE_FILENAME = "TreeRule_Final_FullPath.cga"
# Embedded bytes for CGA/TreeRule_Final_FullPath.cga
TREE_RULE_FINAL_FULLPATH_B64 = """
Ly8gLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0KLy8gVHJlZVJ1bGVfRmluYWxfRnVsbFBhdGguY2dhCi8vIFVzZXMgZnVsbCBwYXRoIEZpbmFsQXNzZXQgYmFrZWQgaW50byBDU1YKLy8gLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0KCmF0dHIgRmluYWxBc3NldCA9ICJhc3NldHMvVHJlZXMvTG93UG9seS9Vbmtub3duLmdsYiIKYXR0ciBoZWlnaHRfbSAgID0gMAphdHRyIGNhbm9weV9tICAgPSAwCgpUcmVlIC0tPgogICAgY2FzZSBGaW5hbEFzc2V0ICE9ICIiIDoKICAgICAgICBJbnNlcnRUcmVlKEZpbmFsQXNzZXQpCiAgICBlbHNlIDoKICAgICAgICBOSUwKCkluc2VydFRyZWUocGF0aCkgLS0+CiAgICBjYXNlIChjYW5vcHlfbSA+IDAgJiYgaGVpZ2h0X20gPiAwKSA6CiAgICAgICAgV2l0aERpbWVuc2lvbnMocGF0aCkKICAgIGVsc2UgOgogICAgICAgIFdpdGhSYW5kb20ocGF0aCkKCldpdGhEaW1lbnNpb25zKHBhdGgpIC0tPgogICAgaShwYXRoKQogICAgcyhjYW5vcHlfbSwgaGVpZ2h0X20sIGNhbm9weV9tKQoKV2l0aFJhbmRvbShwYXRoKSAtLT4KICAgIGkocGF0aCkKICAgIHMocmFuZCgyLDEwKSwgcmFuZCg1LDIwKSwgcmFuZCgyLDEwKSkK
""".strip()

# (key, display label, fallback field name when parameter is empty)
FIELD_CONFIG = [
    ("common_name", "Common Name Field", "common_name"),
    ("genus", "Genus Field", "genus"),
    ("species", "Species Field", "species"),
]

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


def _get_embedded_tree_rule_bytes():
    return base64.b64decode(TREE_RULE_FINAL_FULLPATH_B64)


def _get_default_project_folder():
    try:
        project = arcpy.mp.ArcGISProject("CURRENT")
        home_folder = project.homeFolder
        if home_folder:
            normalized = os.path.normpath(home_folder)
            if not os.path.isdir(normalized):
                os.makedirs(normalized)
            return normalized
    except Exception:
        pass

    workspace = arcpy.env.workspace
    if workspace:
        normalized_workspace = os.path.normpath(workspace)
        if normalized_workspace.lower().endswith(".gdb"):
            candidate = os.path.dirname(normalized_workspace)
            if candidate and os.path.isdir(candidate):
                return candidate
        if os.path.isdir(normalized_workspace):
            return normalized_workspace

    return os.getcwd()


def _generate_vegetation_filelist(vegetation_folder):
    folder = os.path.normpath(vegetation_folder)
    if not os.path.isdir(folder):
        raise ValueError("Vegetation folder does not exist: {0}".format(folder))

    project_folder = _get_default_project_folder()
    output_path = os.path.join(project_folder, MODEL_LIST_FILENAME)
    lines = []
    style_counts = {}
    missing_styles = []

    for style in STYLE_LIST:
        style_folder = os.path.join(folder, style)
        count = 0

        if not os.path.isdir(style_folder):
            missing_styles.append(style)
            style_counts[style] = 0
            continue

        for root, _, filenames in os.walk(style_folder):
            for filename in sorted(filenames):
                file_path = os.path.join(root, filename)
                if os.path.isfile(file_path):
                    lines.append(file_path)
                    count += 1

        style_counts[style] = count

    lines.sort(key=lambda value: value.lower())
    with open(output_path, "w", encoding="utf-8") as handle:
        for line in lines:
            handle.write("{0}\n".format(line))

    return output_path, style_counts, missing_styles, len(lines)


def _normalize_field_token(field_name):
    token = _collapse_spaces(field_name)
    if not token:
        return ""
    token = token.strip('"')
    if "." in token:
        token = token.split(".")[-1]
    return token


def _resolve_field_name(lower_lookup, configured_name, fallback_name):
    configured_token = _normalize_field_token(configured_name)
    if configured_token:
        return lower_lookup.get(configured_token.lower())

    if fallback_name:
        return lower_lookup.get(fallback_name.lower())

    return None


def _first_non_empty(row_dict, field_names):
    for field_name in field_names:
        if not field_name:
            continue
        value = _collapse_spaces(row_dict.get(field_name, ""))
        if value:
            return value
    return ""


def _split_scientific_name(value):
    text = _collapse_spaces(value)
    if not text:
        return "", ""

    # Strip cultivar text in single quotes for key generation.
    text = re.sub(r"'[^']*'", "", text)
    text = _collapse_spaces(text)
    if not text:
        return "", ""

    parts = text.split(" ")
    genus = parts[0]
    species = " ".join(parts[1:]) if len(parts) > 1 else ""
    return genus, species


def _strip_hybrid_prefix(species_value):
    value = _collapse_spaces(species_value)
    if not value:
        return ""
    return re.sub(r"^(x|X|×)\s+", "", value).strip()


def _extract_species_epithet(parent_value, genus_value):
    text = _collapse_spaces(parent_value)
    if not text:
        return ""

    parts = text.split(" ")
    if genus_value and parts and parts[0].lower() == genus_value.lower():
        parts = parts[1:]

    return _collapse_spaces(" ".join(parts))


def _build_exact_tokens(
    genus,
    species,
    accepted_scientific_name,
    infraspecific_rank,
    infraspecific_name,
    hybrid_marker,
    hybrid_parent_1,
    hybrid_parent_2,
):
    tokens = []

    def add_key(genus_part, species_part):
        key_value = "{0}{1}".format(_display_normalize(genus_part), _display_normalize(species_part))
        token = _tokenize(key_value)
        if token and token not in tokens:
            tokens.append(token)

    species_base = _collapse_spaces(species)
    if genus or species_base:
        add_key(genus, species_base)

    if species_base and infraspecific_name:
        if infraspecific_rank:
            add_key(genus, "{0} {1} {2}".format(species_base, infraspecific_rank, infraspecific_name))
        else:
            add_key(genus, "{0} {1}".format(species_base, infraspecific_name))

    if accepted_scientific_name:
        sci_genus, sci_species = _split_scientific_name(accepted_scientific_name)
        if sci_genus or sci_species:
            add_key(sci_genus or genus, sci_species)

    if species_base and hybrid_marker:
        stripped = _strip_hybrid_prefix(species_base)
        if stripped:
            add_key(genus, "x {0}".format(stripped))
            add_key(genus, stripped)

    parent_1_species = _extract_species_epithet(hybrid_parent_1, genus)
    parent_2_species = _extract_species_epithet(hybrid_parent_2, genus)
    if parent_1_species and parent_2_species:
        add_key(genus, "{0} x {1}".format(parent_1_species, parent_2_species))

    return tokens


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
    in_table,
    filelist_path,
    out_csv,
    default_style,
    species_asset_style,
    configured_fields,
):
    base_to_styles, exact_key_to_stem, genus_to_candidates, style_counts = _parse_filelist(
        filelist_path
    )
    if not exact_key_to_stem:
        raise ValueError("No .glb assets were found in the provided file list.")

    table_fields = [field.name for field in arcpy.ListFields(in_table)]
    lower_lookup = {name.lower(): name for name in table_fields}

    resolved_fields = {}
    unresolved_configured = []
    for field_key, _, fallback_name in FIELD_CONFIG:
        configured_name = configured_fields.get(field_key)
        resolved_name = _resolve_field_name(lower_lookup, configured_name, fallback_name)
        resolved_fields[field_key] = resolved_name
        if configured_name and not resolved_name:
            unresolved_configured.append(configured_name)

    if unresolved_configured:
        arcpy.AddWarning(
            "Configured field(s) were not found and will be ignored: {0}".format(
                ", ".join(sorted(set(unresolved_configured)))
            )
        )

    common_name_field = resolved_fields["common_name"]
    genus_field = resolved_fields["genus"]
    species_field = resolved_fields["species"]
    # Non-mapped supplemental taxonomy fields are still used when present with default names.
    accepted_genus_field = lower_lookup.get("accepted_genus")
    accepted_species_field = lower_lookup.get("accepted_species")
    accepted_scientific_name_field = lower_lookup.get("accepted_scientific_name")
    infraspecific_rank_field = lower_lookup.get("infraspecific_rank")
    infraspecific_name_field = lower_lookup.get("infraspecific_name")
    hybrid_marker_field = lower_lookup.get("hybrid_marker")
    hybrid_parent_1_field = lower_lookup.get("hybrid_parent_1")
    hybrid_parent_2_field = lower_lookup.get("hybrid_parent_2")

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
    arcpy.AddMessage(
        "Asset counts by style: {0}".format(
            ", ".join(
                "{0}={1}".format(style, style_counts.get(style, 0)) for style in STYLE_LIST
            )
        )
    )

    for field_key, _, _ in FIELD_CONFIG:
        arcpy.AddMessage(
            "Field mapping {0}: {1}".format(field_key, resolved_fields.get(field_key) or "<none>")
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

                common_name = _collapse_spaces(_first_non_empty(row_dict, [common_name_field]))

                genus_raw = _first_non_empty(row_dict, [accepted_genus_field, genus_field])
                species_raw = _first_non_empty(row_dict, [accepted_species_field, species_field])
                accepted_scientific_name = _first_non_empty(
                    row_dict, [accepted_scientific_name_field]
                )

                if accepted_scientific_name and (not genus_raw or not species_raw):
                    sci_genus, sci_species = _split_scientific_name(accepted_scientific_name)
                    if not genus_raw and sci_genus:
                        genus_raw = sci_genus
                    if not species_raw and sci_species:
                        species_raw = sci_species

                infraspecific_rank = _first_non_empty(row_dict, [infraspecific_rank_field])
                infraspecific_name = _first_non_empty(row_dict, [infraspecific_name_field])
                hybrid_marker = _first_non_empty(row_dict, [hybrid_marker_field])
                hybrid_parent_1 = _first_non_empty(row_dict, [hybrid_parent_1_field])
                hybrid_parent_2 = _first_non_empty(row_dict, [hybrid_parent_2_field])

                genus = _display_normalize(genus_raw)
                species = _display_normalize(species_raw)

                species_for_key = species
                if species and infraspecific_name:
                    if infraspecific_rank:
                        species_for_key = _display_normalize(
                            "{0} {1} {2}".format(species, infraspecific_rank, infraspecific_name)
                        )
                    else:
                        species_for_key = _display_normalize(
                            "{0} {1}".format(species, infraspecific_name)
                        )

                key_value = "{0}{1}".format(genus, species_for_key)

                if not genus and not species_for_key:
                    skipped_empty += 1

                # Keep normalized core matching fields in the final output when present.
                if common_name_field:
                    row_dict[common_name_field] = common_name
                if genus_field:
                    row_dict[genus_field] = genus
                if species_field:
                    row_dict[species_field] = species

                exact_tokens = _build_exact_tokens(
                    genus=genus,
                    species=species,
                    accepted_scientific_name=accepted_scientific_name,
                    infraspecific_rank=infraspecific_rank,
                    infraspecific_name=infraspecific_name,
                    hybrid_marker=hybrid_marker,
                    hybrid_parent_1=hybrid_parent_1,
                    hybrid_parent_2=hybrid_parent_2,
                )

                chosen_stem = None
                asset_file = ""
                genus_out = ""
                match_type = "Unknown"

                for exact_token in exact_tokens:
                    if exact_token in exact_key_to_stem:
                        chosen_stem = exact_key_to_stem[exact_token]
                        style_for_asset = _pick_species_style(
                            chosen_stem, species_asset_style, base_to_styles
                        )
                        asset_file = "ESRI.lib/assets/Webstyles/Vegetation/{0}/{1}.glb".format(
                            style_for_asset, chosen_stem
                        )
                        genus_out = genus
                        match_type = "Species match"
                        break

                if not chosen_stem:
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
        self.label = "City Engine"
        self.alias = "cityengine"
        self.tools = [
            GenerateVegetationFileListTool,
            ForestreeCityEngineModelMatcherOptionalTaxonomyFieldsTool,
            XYTableToPointTool,
            CopyTreeRuleToWorkspaceTool,
        ]


class ForestreeCityEngineModelMatcherOptionalTaxonomyFieldsTool(object):
    def __init__(self):
        self.label = "02 Add CE Model Paths to your tree data"
        self.description = (
            "Crosswalks a tree table to CityEngine assets. Core and GBIF/APNI-style taxonomy "
            "field parameters are optional and can be mapped per dataset."
        )
        self.canRunInBackground = False

    def getParameterInfo(self):
        p0 = arcpy.Parameter(
            displayName="Input Tree Table",
            name="in_table",
            datatype="GPTableView",
            parameterType="Required",
            direction="Input",
        )

        p1 = arcpy.Parameter(
            displayName="City Engine Tree Model List (.txt)",
            name="filelist_path",
            datatype="DEFile",
            parameterType="Required",
            direction="Input",
        )
        p1.filter.list = ["txt"]

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

        field_params = []
        for field_key, display_label, _ in FIELD_CONFIG:
            field_param = arcpy.Parameter(
                displayName=display_label,
                name="{0}_field".format(field_key),
                datatype="Field",
                parameterType="Optional",
                direction="Input",
            )
            field_param.parameterDependencies = [p0.name]
            field_param.category = "Optional Field Mapping"
            field_params.append(field_param)

        return [p0, p1, p2, p3, p4] + field_params

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        if not parameters[1].altered and not parameters[1].valueAsText:
            default_filelist = os.path.join(_get_default_project_folder(), MODEL_LIST_FILENAME)
            if os.path.isfile(default_filelist):
                parameters[1].value = default_filelist

        if not parameters[2].altered and not parameters[2].valueAsText:
            parameters[2].value = os.path.join(
                _get_default_project_folder(), TREE_DATA_WITH_PATHS_FILENAME
            )

        in_table = parameters[0].valueAsText
        if not in_table:
            return

        try:
            lower_lookup = {field.name.lower(): field.name for field in arcpy.ListFields(in_table)}
            for offset, (_, _, fallback_name) in enumerate(FIELD_CONFIG):
                field_param = parameters[5 + offset]
                if field_param.altered:
                    continue
                if fallback_name.lower() in lower_lookup:
                    field_param.value = lower_lookup[fallback_name.lower()]
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
                genus_set = bool(parameters[6].valueAsText or "genus" in lower_lookup)
                species_set = bool(parameters[7].valueAsText or "species" in lower_lookup)
                if not (genus_set and species_set):
                    parameters[0].setWarningMessage(
                        "Genus/species field mapping is incomplete; many rows may resolve to Unknown."
                    )
            except Exception:
                pass

        if filelist_path and not filelist_path.lower().endswith(".txt"):
            parameters[1].setWarningMessage(
                "Expected {0} (tool will still attempt to read it).".format(
                    MODEL_LIST_FILENAME
                )
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

        configured_fields = {}
        for offset, (field_key, _, _) in enumerate(FIELD_CONFIG):
            configured_fields[field_key] = parameters[5 + offset].valueAsText

        try:
            _run_crosswalk(
                in_table=in_table,
                filelist_path=filelist_path,
                out_csv=out_csv,
                default_style=default_style,
                species_asset_style=species_asset_style,
                configured_fields=configured_fields,
            )
            arcpy.AddMessage("Completed successfully.")
        except Exception:
            arcpy.AddError("Tool failed.")
            arcpy.AddError(traceback.format_exc())
            raise


class GenerateVegetationFileListTool(object):
    def __init__(self):
        self.label = "01 Make CE Tree Model Catalog"
        self.description = (
            "Start at your CityEngine workspace folder, then open "
            "ESRI.lib/assets/Webstyles/Vegetation and select the Vegetation folder. "
            "The tool writes City Engine Tree Model List.txt to the default ArcGIS Pro project folder, "
            "containing all files found under LowPoly, "
            "Realistic, Schematic, and Fan."
        )
        self.canRunInBackground = False

    def getParameterInfo(self):
        p0 = arcpy.Parameter(
            displayName=(
                "Vegetation Folder "
                "(from CityEngine workspace -> ESRI.lib\\assets\\Webstyles\\Vegetation)"
            ),
            name="vegetation_folder",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input",
        )
        return [p0]

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        vegetation_folder = parameters[0].valueAsText
        if not vegetation_folder:
            return

        folder_name = os.path.basename(os.path.normpath(vegetation_folder)).lower()
        if folder_name != "vegetation":
            parameters[0].setWarningMessage(
                "Start at your CityEngine workspace folder, then select: "
                "ESRI.lib\\assets\\Webstyles\\Vegetation"
            )
            return

        missing_styles = []
        for style in STYLE_LIST:
            style_folder = os.path.join(vegetation_folder, style)
            if not os.path.isdir(style_folder):
                missing_styles.append(style)

        if missing_styles:
            parameters[0].setWarningMessage(
                "Missing expected style folder(s): {0}".format(", ".join(missing_styles))
            )

        return

    def execute(self, parameters, messages):
        vegetation_folder = parameters[0].valueAsText

        try:
            output_path, style_counts, missing_styles, total_count = _generate_vegetation_filelist(
                vegetation_folder
            )
            arcpy.AddMessage("Generated file list: {0}".format(output_path))
            arcpy.AddMessage("Total files listed: {0}".format(total_count))
            arcpy.AddMessage(
                "Files by style: {0}".format(
                    ", ".join(
                        "{0}={1}".format(style, style_counts.get(style, 0)) for style in STYLE_LIST
                    )
                )
            )
            if missing_styles:
                arcpy.AddWarning(
                    "Style folder(s) not found and skipped: {0}".format(
                        ", ".join(missing_styles)
                    )
                )
        except Exception:
            arcpy.AddError("Tool failed.")
            arcpy.AddError(traceback.format_exc())
            raise


class XYTableToPointTool(object):
    def __init__(self):
        self.label = "03 Tree XY's to Points"
        self.description = (
            "Creates a point feature class from an input table using X/Y coordinate fields."
        )
        self.canRunInBackground = False

    def getParameterInfo(self):
        p0 = arcpy.Parameter(
            displayName="Input Table",
            name="in_table",
            datatype="GPTableView",
            parameterType="Required",
            direction="Input",
        )

        p1 = arcpy.Parameter(
            displayName="Output Point Feature Class",
            name="out_feature_class",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output",
        )

        p2 = arcpy.Parameter(
            displayName="X Field",
            name="x_field",
            datatype="Field",
            parameterType="Required",
            direction="Input",
        )
        p2.parameterDependencies = [p0.name]

        p3 = arcpy.Parameter(
            displayName="Y Field",
            name="y_field",
            datatype="Field",
            parameterType="Required",
            direction="Input",
        )
        p3.parameterDependencies = [p0.name]

        p4 = arcpy.Parameter(
            displayName="Z Field (Optional)",
            name="z_field",
            datatype="Field",
            parameterType="Optional",
            direction="Input",
        )
        p4.parameterDependencies = [p0.name]

        p5 = arcpy.Parameter(
            displayName="Coordinate System (Optional)",
            name="coordinate_system",
            datatype="GPSpatialReference",
            parameterType="Optional",
            direction="Input",
        )

        return [p0, p1, p2, p3, p4, p5]

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        if not parameters[0].altered and not parameters[0].valueAsText:
            default_input = os.path.join(
                _get_default_project_folder(), TREE_DATA_WITH_PATHS_FILENAME
            )
            if os.path.isfile(default_input):
                parameters[0].value = default_input

        in_table = parameters[0].valueAsText
        if not in_table:
            return

        try:
            lookup = {field.name.lower(): field.name for field in arcpy.ListFields(in_table)}
            if not parameters[2].altered:
                for candidate in ("x", "lon", "lng", "longitude"):
                    if candidate in lookup:
                        parameters[2].value = lookup[candidate]
                        break
            if not parameters[3].altered:
                for candidate in ("y", "lat", "latitude"):
                    if candidate in lookup:
                        parameters[3].value = lookup[candidate]
                        break
        except Exception:
            pass

        return

    def updateMessages(self, parameters):
        in_table = parameters[0].valueAsText
        x_field = parameters[2].valueAsText
        y_field = parameters[3].valueAsText

        if x_field and y_field and x_field == y_field:
            parameters[3].setErrorMessage("Y Field must be different from X Field.")

        if in_table:
            try:
                type_lookup = {field.name: field.type for field in arcpy.ListFields(in_table)}
                numeric_types = {
                    "Double",
                    "Single",
                    "Integer",
                    "SmallInteger",
                    "BigInteger",
                }
                if x_field and type_lookup.get(x_field) not in numeric_types:
                    parameters[2].setWarningMessage(
                        "X Field is not numeric ({0}).".format(type_lookup.get(x_field))
                    )
                if y_field and type_lookup.get(y_field) not in numeric_types:
                    parameters[3].setWarningMessage(
                        "Y Field is not numeric ({0}).".format(type_lookup.get(y_field))
                    )
            except Exception:
                pass

        return

    def execute(self, parameters, messages):
        in_table = parameters[0].valueAsText
        out_feature_class = parameters[1].valueAsText
        x_field = parameters[2].valueAsText
        y_field = parameters[3].valueAsText
        z_field = parameters[4].valueAsText or ""
        coordinate_system = parameters[5].value

        try:
            arcpy.management.XYTableToPoint(
                in_table,
                out_feature_class,
                x_field,
                y_field,
                z_field,
                coordinate_system,
            )
            arcpy.AddMessage("Created point feature class: {0}".format(out_feature_class))
        except Exception:
            arcpy.AddError("Tool failed.")
            arcpy.AddError(traceback.format_exc())
            raise


class CopyTreeRuleToWorkspaceTool(object):
    def __init__(self):
        self.label = "04 Copy Tree Rule to CE Workspace"
        self.description = (
            "Select your CityEngine workspace Rules folder. "
            "The tool writes an embedded copy of TreeRule_Final_FullPath.cga into that folder."
        )
        self.canRunInBackground = False

    def getParameterInfo(self):
        p0 = arcpy.Parameter(
            displayName="Your CE Project's Rules folder",
            name="rules_folder",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input",
        )
        return [p0]

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        rules_folder = parameters[0].valueAsText
        if not rules_folder:
            return

        folder_name = os.path.basename(os.path.normpath(rules_folder)).lower()
        if folder_name not in ("rules", "rule"):
            parameters[0].setWarningMessage(
                "Select your CityEngine Rules folder in the workspace."
            )

        return

    def execute(self, parameters, messages):
        rules_folder = parameters[0].valueAsText

        try:
            rule_bytes = _get_embedded_tree_rule_bytes()
            destination_path = os.path.join(rules_folder, TREE_RULE_FILENAME)
            existed = os.path.isfile(destination_path)

            # Write embedded bytes directly so rule formatting and encoding stay unchanged.
            with open(destination_path, "wb") as handle:
                handle.write(rule_bytes)

            if existed:
                arcpy.AddMessage("Replaced existing embedded rule: {0}".format(destination_path))
            else:
                arcpy.AddMessage("Copied embedded rule: {0}".format(destination_path))
        except Exception:
            arcpy.AddError("Tool failed.")
            arcpy.AddError(traceback.format_exc())
            raise
