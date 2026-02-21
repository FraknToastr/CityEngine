# Taxonomy Fields That Improve Matching

For the current Forestree-to-CityEngine crosswalk, these taxonomy fields would improve match quality:

- `accepted_genus` + `accepted_species` (or one `accepted_scientific_name`)
  - Resolves synonym and spelling/noise issues before matching.
- `infraspecific_rank` + `infraspecific_name`
  - Preserves detail for `subsp.`, `var.`, and cultivar-level names.
- `hybrid_marker`, `hybrid_parent_1`, `hybrid_parent_2`
  - Improves handling of hybrid records (for example names with `x` or `×`).
- `taxon_id` + `accepted_taxon_id` (GBIF/APNI or your chosen authority)
  - Enables deterministic synonym resolution instead of string-only matching.
- `family`
  - Adds a useful fallback tier between species-level and genus-only matching.

## Hybrid Fields in Detail (with Examples)

Hybrid names are common in your source table and are a major source of missed exact matches when only `genus + species` is used as a free-text key.

Recommended hybrid fields:

- `hybrid_marker`
  - Store a normalized indicator such as `x` for any hybrid record.
  - Normalize all variants (`×`, `X`, `x`) to `x`.
- `hybrid_parent_1`
  - Store canonical parent taxon 1 (usually `Genus species`).
- `hybrid_parent_2`
  - Store canonical parent taxon 2 (usually `Genus species`).

Examples from current Forestree data:

| Input `genus` | Input `species` | Suggested `hybrid_marker` | Suggested `hybrid_parent_1` | Suggested `hybrid_parent_2` | Notes |
|---|---|---|---|---|---|
| `Platanus` | `x acerifolia` | `x` | `Platanus orientalis` | `Platanus occidentalis` | Interspecific hybrid notation with leading `x`. |
| `Callistemon` | `citrinus x viminalis` | `x` | `Callistemon citrinus` | `Callistemon viminalis` | Parent pair is already explicit in species text. |
| `Photinia` | `x fraseri` | `x` | `Photinia` (unknown parent species) | `Photinia` (unknown parent species) | Marker still helps even if parents are incomplete. |
| `Prunus` | `x blireana` | `x` | `Prunus` (optional if unknown) | `Prunus` (optional if unknown) | Keep marker even when parent lineage is not populated. |
| `Brachychiton` | `populneus x acerifolia 'Bella Pink'` | `x` | `Brachychiton populneus` | `Brachychiton acerifolius` | Cultivar can be split into a cultivar field separately. |

How these fields improve matching behavior:

- Build a normalized hybrid key (`genus + hybrid_marker + epithet`) so `x acerifolia`, `× acerifolia`, and `X acerifolia` resolve to one key.
- Use parent-pair fallback before genus fallback, for example:
  - Exact hybrid key match
  - Parent-pair match (`parent_1 + parent_2`)
  - Single-parent match
  - Genus-only fallback
- Keep hybrid records out of plain species-only matching buckets so they do not incorrectly map to non-hybrid assets.

Suggested normalization rules:

- Trim and collapse spaces in all taxonomy fields.
- Lowercase for token matching, preserve display case for output.
- Strip quotes around cultivar text and store cultivar separately when present.
- Treat `sp.` as unresolved species, not as a hybrid indicator.

## Current Tool Behavior

The latest toolbox currently matches using only:

- `common_name`
- `genus`
- `species`

So additional taxonomy fields will improve results only after a small matcher update.

## Existing Candidate Fields in Current Data

Your current Forestree schema does not include any more useful candidate fields.
