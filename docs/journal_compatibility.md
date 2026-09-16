# Runtime journal compatibility

AXQ runtime journals are append-only evidence. Compatibility is implemented in the semantic
contract reader; historical databases and payloads are never rewritten merely to satisfy a newer
model shape.

`JournalRecord` dispatches decoding by `(record_type, semantic_schema_version)`. For
`SHADOW_RUNTIME_CYCLE`:

- V1 has two strict decoder-only shapes. The original shape omits `interaction_resolution_id` and
  preserves the identity calculated without it. A transitional shape explicitly contains
  `interaction_resolution_id` (including a persisted `null`) and preserves the identity calculated
  with that field. Dispatch selects between these shapes from the parsed payload keys before strict
  payload-model validation; neither shape permits unrelated extras.
- V2 is the current writer contract. Its identity includes interaction linkage.
- unknown versions fail closed;
- malformed payloads, envelope/payload version mismatches, semantic-ID mismatches, and corrupt
  content identities raise validation errors rather than being skipped.

Mixed V1/V2 rows retain append order and decode deterministically. The outer journal record and the
inner semantic payload keep their original IDs and bytes. There is no path that upgrades a V1 row in
place.

Runtime events may be appended before the reducer accepts them, so processing outcomes remain
separate immutable rows. Replay includes events with an `APPLIED` outcome and excludes rejected-only
events. An applied event remains replayable if a later duplicate attempt is recorded. Journals from
before outcome tracking remain compatible: when an event has no outcome rows, it is treated as a
legacy accepted event rather than silently discarded.

To validate an old artifact safely, open SQLite through a read-only URI or hash the file before and
after decoding. Never copy, delete, or rewrite the artifact as a compatibility workaround.
