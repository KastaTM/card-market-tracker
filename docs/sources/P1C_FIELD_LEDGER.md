# P1c field, acquisition and rights ledger

Source: `tcgdex/cards-database`, R1 `af57972e8f784c2507ab9e573c99bf02ae2e5e42`.
Only the P1c allowlist is retained. Exact literals and explicit Set import/reference
are parsed without executing upstream code. UTF8 spans are zero-based half-open.

| Artifact | Field | Bytes | Permitted transformation/use |
| --- | --- | --- | --- |
| `data/Sword & Shield/Darkness Ablaze.ts` | `id` | [104,111) | Exact ES/EN literal/relation; metadata evidence, never canonical identity |
| `data/Sword & Shield/Darkness Ablaze.ts` | `name.es` | [185,210) | Exact ES/EN literal/relation; metadata evidence, never canonical identity |
| `data/Sword & Shield/Darkness Ablaze.ts` | `name.en` | [129,146) | Exact ES/EN literal/relation; metadata evidence, never canonical identity |
| `data/Sword & Shield/Darkness Ablaze.ts` | `releaseDate` | [387,399) | Exact ES/EN literal/relation; metadata evidence, never canonical identity |
| `data/Sword & Shield/Darkness Ablaze/136.ts` | `name.es` | [166,174) | Exact ES/EN literal/relation; metadata evidence, never canonical identity |
| `data/Sword & Shield/Darkness Ablaze/136.ts` | `name.en` | [133,141) | Exact ES/EN literal/relation; metadata evidence, never canonical identity |
| `data/Sword & Shield/Darkness Ablaze/136.ts` | `set` | [313,316) | Exact ES/EN literal/relation; metadata evidence, never canonical identity |
| `data/Sword & Shield/Darkness Ablaze/136.ts` | `$parent_import` | [59,79) | Exact ES/EN literal/relation; metadata evidence, never canonical identity |

Card number is exact filename stem `136`; external ID is `${set.id}-${stem}`.
Release date is a declared calendar date without region/launch guarantee. Set
acceptance requires curated coherent bindings. Cards retain unknown_variant;
no UUID, printing, variant or promotion is inferred. Excluded: artwork/logos,
other languages, effects/descriptions/attacks, illustrator, counts, updated,
market IDs, prices/stock and arbitrary extras.

Permission is the pinned LICENSE/full MIT notice plus README's short database MIT
declaration, retained under the Orchestrator's explicit contract. The full notice
is unchanged in [MIT_NOTICE](../../src/card_market_tracker/pinned_repository/MIT_NOTICE.txt).
No separate trademark/artwork/third-party grant is inferred. Local history and
minimum fixture publication require that complete notice; no REST grant exists.

| Artifact | Bytes | Git blob SHA1 | Content SHA256 | Acquisition finished UTC |
| --- | --- | --- | --- | --- |
| `data/Sword & Shield/Darkness Ablaze.ts` | 536 | `db48bc4a054b3b1c5bd2b6956257f20ba251c79c` | `4bed34217397bcfeee8925868b50816051022d1bbdb60b63eac702ae6f6bd70a` | `2026-10-18T12:18:49.654621Z` |
| `data/Sword & Shield/Darkness Ablaze/136.ts` | 2028 | `6db89c69b56552fa4e09f26e0e90d14e97466411` | `bd5ab2a350fe4b453d468f8b89aa904d26b4b57c4c2d62d330111a28a92a4be6` | `2026-10-18T12:18:49.912617Z` |
| `LICENSE` | 1063 | `c67ded0d5f0abc77b4fbdbfd37312f2a88de1b55` | `12e7dd2d018848b9997d0226c4632f01da86ec4bf6ebe0c8b19953d5e5eeb6ff` | `2026-10-18T12:18:50.149341Z` |
| `README.md` | 6809 | `77bc8108c2cdb54c663e1fdf8c4502ac65f88734` | `82ab33624f52569fd3b45991d90c840e8b7d77969a1b5d52071a6782cd791de5` | `2026-10-18T12:18:50.379756Z` |

R1 aggregate acquired_at/captured_at is final necessary read completion:
`2026-10-18T12:18:50.379756Z`. Per-artifact UTC times are actual engineering read
observations, not commit dates or provider-authenticated stamps. R0 remains at
`2026-10-14T17:53:09.118954Z`; import time is separate and replays cannot redate it.
R1 canonical bundle SHA256 is
`e3b6ec38358a8fc089e65a365fe2f5566459df441e67c3e8ad51b3b5352b50c0`;
projection SHA256 is unchanged
`53100248a987378fb3ca2273b7ec219747b876b515f57087faf6becdd0caa479`.
Canonical UTF8 JSON is sorted keys, ensure_ascii=False, compact comma/colon.
Git SHA1 includes `blob <size>\0`; content SHA256 covers original bytes.

Independent QA (2026-10-18T12:20:23.695769Z) used a separate stdlib byte lexer,
regex/context and direct slices without production imports. Independent REVIEWER
(12:21:54.170321Z) used own regex/byte extraction. Both recomputed all four byte
locks, eight spans, exact projection, parent relation and full MIT plus the README
sentence, then independently confirmed canonical R0/R1 hashes. They reused the
engineering originals; neither claimed a separate fetch or provider timestamp.
Their pre-freeze source review is separate from final exact-candidate review.

All four original TS/LICENSE/README buffers were temporary; source originals were
deleted at 12:22:33.662193Z after both contrasts and reviewer verified no raw files
remain. Only minimum package, MIT, lock/spans and this evidence remain in Git.
[Request ledger](P1C_REQUEST_LEDGER.json) records four sequential content requests,
zero redirects/retries and zero metadata calls of total budget12/content8/metadata4.
No further source request is needed for offline CI/runtime. Four real unit
comparisons must yield no_discoveries and zero events; positive novelty is synthetic.
