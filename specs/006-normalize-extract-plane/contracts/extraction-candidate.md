# Contract: Extraction Candidate

- Every candidate field value must have a field anchor ref.
- Candidates must reference an extraction strategy.
- Candidates must reference normalized documents.
- Candidates must not create `PublishedOutput` or `OutputManifest`.
- Candidate failures must be replay-visible.
