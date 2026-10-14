# P1b field and transformation ledger

Engineering extraction: 2026-10-14 UTC. Exact pinned revision `4199850a6af49665db0080fa2bb9ef751750a406`.
Namespace `tcgdex_repository`; policy `tcgdex_two_artifacts_es_en_v1`; extractor `pinned_ts_literals_v1`.

Only the listed minimum licensed metadata is retained. Source AST/originals are transient.
Byte spans are UTF-8 zero-based half-open offsets in the original Git blobs.

| Artifact | Structural field | Bytes [start,end) | Transform / permitted use |
| --- | --- | --- | --- |
| `data/Sword & Shield/Darkness Ablaze.ts` | `id` | [104,111) | External reference only; never canonical identity |
| `data/Sword & Shield/Darkness Ablaze.ts` | `name.es` | [185,210) | Exact language literal; short catalog display/evidence, never identity |
| `data/Sword & Shield/Darkness Ablaze.ts` | `name.en` | [129,146) | Exact language literal; short catalog display/evidence, never identity |
| `data/Sword & Shield/Darkness Ablaze.ts` | `releaseDate` | [387,399) | Calendar date declaration; no regional or launch guarantee |
| `data/Sword & Shield/Darkness Ablaze/136.ts` | `name.es` | [166,174) | Exact language literal; short catalog display/evidence, never identity |
| `data/Sword & Shield/Darkness Ablaze/136.ts` | `name.en` | [133,141) | Exact language literal; short catalog display/evidence, never identity |
| `data/Sword & Shield/Darkness Ablaze/136.ts` | `set` | [313,316) | Declared Set identifier, validated against exact approved import; no execution |
| `data/Sword & Shield/Darkness Ablaze/136.ts` | `$parent_import` | [59,79) | Exact declared `../Darkness Ablaze` import, line 2; links root `set` identifier on line 19 to the approved set path without execution |

Card number `136` is the exact approved filename stem. Card external ID is the
explicit `${set.id}-${stem}` transform `swsh3-136`. Parent import is exactly
`../Darkness Ablaze`, resolved structurally to the approved set path without
loading or executing it. ES and EN are exact keys; no fallback is permitted.

All variants, other languages, counts, third-party IDs, artwork URLs, descriptions,
attacks/effects, illustrator, prices, stock and `updated` are excluded. `variant`
remains `unknown`; release date on the card and provider update remain null.

## Reviewed integrity lock

| Artifact | Bytes | Git blob SHA-1 | Content SHA-256 | Acquisition completed UTC |
| --- | --- | --- | --- | --- |
| `data/Sword & Shield/Darkness Ablaze.ts` | 536 | `db48bc4a054b3b1c5bd2b6956257f20ba251c79c` | `4bed34217397bcfeee8925868b50816051022d1bbdb60b63eac702ae6f6bd70a` | `2026-10-14T17:53:08.304471Z` |
| `data/Sword & Shield/Darkness Ablaze/136.ts` | 2028 | `6db89c69b56552fa4e09f26e0e90d14e97466411` | `bd5ab2a350fe4b453d468f8b89aa904d26b4b57c4c2d62d330111a28a92a4be6` | `2026-10-14T17:53:08.594654Z` |
| `LICENSE` | 1063 | `c67ded0d5f0abc77b4fbdbfd37312f2a88de1b55` | `12e7dd2d018848b9997d0226c4632f01da86ec4bf6ebe0c8b19953d5e5eeb6ff` | `2026-10-14T17:53:08.862701Z` |
| `README.md` | 6809 | `77bc8108c2cdb54c663e1fdf8c4502ac65f88734` | `82ab33624f52569fd3b45991d90c840e8b7d77969a1b5d52071a6782cd791de5` | `2026-10-14T17:53:09.118954Z` |

Projection SHA-256: `53100248a987378fb3ca2273b7ec219747b876b515f57087faf6becdd0caa479`.
Canonical whole-bundle SHA-256: `3b43e1a78c117ef1ecb5cf200a4b2fc7e57af8fd29e3fcf29b06f4291ae58085`.

Whole-bundle canonicalization uses UTF-8, sorted JSON keys, no ASCII escaping and
separators comma/colon without spaces. Git SHA-1 hashes `blob <byte length>\0`
plus original bytes; SHA-256 hashes original bytes only. The bundle lock includes
policy/extractor, four artifact locks, both engineering times, MIT notice and
projection; a self-declared digest or Python object grants no authority.

The source database MIT declaration is retained as one short sentence with the
full license in the installed package and fixture. The README lock identifies the
consulted licensing artifact; its remaining contents are excluded. Covered copies,
local retention, minimal fixture publication and metadata history are authorized
by the P1b Orchestrator contract with the complete notice. MIT grants no separate
trademark/artwork/third-party data rights. No REST permission is inferred.

Acquisition is the per-artifact engineering completion above; aggregate acquisition
and declared capture are the last completed artifact time. Import time is stored
separately by storage. Reimport cannot advance acquisition/capture. Verification
establishes equality with the reviewed local package, not independent producer
authentication, physical card truth, live provider health, full catalog coverage
or product absence. QA must contrast originals independently before final approval.

See [request ledger](P1B_REQUEST_LEDGER.json), [bundle contract](../data-contracts/PINNED_REPOSITORY_BUNDLE_V1.md),
and [MIT notice](../../src/card_market_tracker/pinned_repository/MIT_NOTICE.txt).
