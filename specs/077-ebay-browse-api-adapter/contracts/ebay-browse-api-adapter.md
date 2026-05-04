# Contract: eBay Browse API Adapter

The adapter implements `EcommerceOfficialApiAdapterPort.fetch_product`.

Input:

- `fixture_id`
- `EcommerceOfficialApiTargetSpec(platform="ebay")`

Output:

- `EcommerceOfficialApiFetchOutcome`
- On success: credential grant/audit refs and `EcommerceOfficialApiResponse`
- On non-success: credential grant/audit refs, typed failure, diagnostics

Forbidden:

- returning product fields without Browse API response bytes;
- using LLM output as source evidence;
- storing eBay-native state in VeraCrawl core;
- bypassing eBay access controls.

