# Contract: Publication Gates

`PublicationReport` records pass and fail publication outcomes.

Pass requires:

- evidence coverage pass
- evidence packet and evidence manifest refs
- accepted verification decision
- accepted review decision
- allow publication policy
- privacy lifecycle refs
- replay bundle ref
- command record refs
- event cursor refs
- outbox refs
- output manifest ref
- published output ref

Fail or needs-review outcomes must include `failure_report_refs` or
`missing_ref_fields` and must not create output manifest refs.

Direct candidate publication is forbidden. A candidate can be referenced by a
published output only through evidence, verification, review, policy, privacy, and
replay gates.
