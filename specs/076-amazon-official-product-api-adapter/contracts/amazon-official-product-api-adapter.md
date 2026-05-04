# Contract: Amazon Official Product API Adapter

The adapter implements `EcommerceOfficialApiAdapterPort.fetch_product`.

Input:

- `fixture_id`
- `EcommerceOfficialApiTargetSpec(platform="amazon")`

Output:

- `EcommerceOfficialApiFetchOutcome`
- On success: credential grant/audit refs and `EcommerceOfficialApiResponse`
- On non-success: credential grant/audit refs, typed failure, diagnostics

Forbidden:

- returning product fields without official API response bytes;
- using LLM output as source evidence;
- storing Amazon SDK-native state in VeraCrawl core;
- fetching outside manifest `allowed_origin`;
- bypassing access controls.

