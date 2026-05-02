# Contract: Normalization

- Raw HTML must normalize into deterministic text.
- `NormalizationManifest` must connect raw artifact, normalized artifact, anchor map, parser, transformation version, and digests.
- `AnchorMap` must contain `TextAnchor` refs.
- Empty normalized content is a typed non-success outcome.
- Missing raw artifact is a typed non-success outcome.
