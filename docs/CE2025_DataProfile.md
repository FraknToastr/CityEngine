# CE2025 Digital Twin – Source Workbook Summary

- Workbook: `Cadastre_and_PlanDesignCode_Overlays_and_TNGs.xlsx`

- Sheets: Cadastre, Neighbourhood_and_Corridor_Zone, Maximum_Building_Height__Metres, Maximum_Building_Height__Levels, Infrastructure_Zones, Capital_City_Zones, Capital_City_Subzones

- Main sheet (largest): **Cadastre**

## Heuristic Field Detection

- ID fields: ['OBJECTID', 'parcel', 'parcel_id']

- Zoning fields: []

- Overlay fields: []

- TNG fields: []

- Height fields: []

- Setback fields: []

- Heritage fields: []

- Active frontage fields: []

- Land-use fields: []

---

# Data Profile – Cadastre

- Rows: 7933
- Columns: 33

## Columns Overview

- **OBJECTID**: non-null=7933, unique=7933, sample=['1', '2', '3', '4', '5']

- **plan_t**: non-null=7931, unique=7, sample=['C', 'D', 'F', 'H', 'R']

- **plan_**: non-null=7931, unique=5452, sample=['10179', '12795', '12996', '14266', '14273']

- **parcel_t**: non-null=7163, unique=5, sample=['A', 'Q', 'F', 'S', 'T']

- **parcel**: non-null=7163, unique=974, sample=['10', '11', '8', '9', '12']

- **title_t**: non-null=7063, unique=3, sample=['CT', 'CR', 'CL']

- **volume**: non-null=7063, unique=1176, sample=['5288', '5099', '5838', '5893', '6234']

- **folio**: non-null=7063, unique=998, sample=['546', '524', '525', '684', '558']

- **qualifier**: non-null=69, unique=1, sample=['+titles']

- **date_from**: non-null=7554, unique=2011, sample=['2006-07-03 00:00:00', '1980-01-07 00:00:00', '2001-12-17 00:00:00', '1999-04-08 00:00:00', '1997-10-15 00:00:00']

- **parcel_id**: non-null=7931, unique=7817, sample=['C10179', 'C12795', 'C12996', 'C14266', 'C14273']

- **improved**: non-null=7933, unique=2, sample=['0', '1']

- **floor_level**: non-null=7165, unique=10, sample=['0', '1', '-1', '-0.5', '1.5']

- **accuracy_code**: non-null=7933, unique=3, sample=['7', '6', '2']

- **Shape_Length**: non-null=7933, unique=7922, sample=['112.0788536622734', '730.1502951240326', '161.1857136597846', '129.6494829295407', '100.3946014859114']

- **Shape_Area**: non-null=7933, unique=7920, sample=['783.7747231148022', '5279.93720127878', '1041.361234265725', '563.7833409509589', '624.2295264660478']

- **CCZ_id**: non-null=7816, unique=5, sample=['Z0908', 'Z0909', 'Z0905', 'Z0911', 'Z0302']

- **CCZ_name**: non-null=7816, unique=5, sample=['City Living', 'City Main Street', 'Capital City', 'City Riverbank', 'Adelaide Park Lands']

- **CCZ_value**: non-null=7816, unique=5, sample=['CL', 'CMS', 'CC', 'CR', 'APL']

- **CCSZ_id**: non-null=5137, unique=15, sample=['S3902', 'S2403', 'S4202', 'S5401', 'S0903']

- **CCSZ_name**: non-null=5137, unique=15, sample=['Medium-High Intensity', 'Hindley Street', 'North Adelaide Low Intensity', 'Rundle Mall', 'City High Street']

- **MBHM_id**: non-null=4998, unique=1, sample=['V0002']

- **MBHM_name**: non-null=4998, unique=1, sample=['Maximum Building Height (Metres)']

- **MBHM_value**: non-null=4998, unique=13, sample=['11', '9999', '22', '53', '14']

- **MBHL_id**: non-null=4790, unique=1, sample=['V0008']

- **MBHL_name**: non-null=4790, unique=1, sample=['Maximum Building Height (Levels)']

- **MBHL_value**: non-null=4790, unique=7, sample=['3', '2', '6', '4', '5']

- **IZ_id**: non-null=32, unique=1, sample=['Z0903']

- **IZ_name**: non-null=32, unique=1, sample=['Community Facilities']

- **IZ_value**: non-null=32, unique=1, sample=['CF']

- **NACZ_id**: non-null=75, unique=1, sample=['Z0601']

- **NACZ_name**: non-null=75, unique=1, sample=['Business Neighbourhood']

- **NACZ_value**: non-null=75, unique=1, sample=['BN']
