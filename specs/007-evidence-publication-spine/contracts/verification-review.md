# Contract: Verification And Review

`VerificationDecision` remains the canonical verification aggregate. This feature
adds deterministic review records after verification.

`ReviewDecision` must include:

- run ref
- verification decision ref
- evidence packet ref
- accept/reject/review/conflict decision
- reviewer or authority ref
- policy decision refs
- rationale refs

Publication pass requires accepted verification and accepted review. Reject,
review, or conflict blocks publication and must be visible in the publication
report.
