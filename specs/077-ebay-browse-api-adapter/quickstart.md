# Quickstart: eBay Browse API Adapter

Run without credentials:

```sh
uv run --python python3.12 --extra dev veracrawl-ecommerce-official-api run-live \
  tests/fixtures/us-ecommerce-official-api-product-availability \
  --profile target \
  --out .veracrawl-test-runs/us-ecommerce-official-api-product-availability
```

Credentialed eBay run:

```sh
export EBAY_CLIENT_ID="..."
export EBAY_CLIENT_SECRET="..."
export EBAY_MARKETPLACE_ID="EBAY_US"
uv run --python python3.12 --extra dev veracrawl-ecommerce-official-api run-live \
  tests/fixtures/us-ecommerce-official-api-product-availability \
  --profile target \
  --out .veracrawl-real-runs/us-ecommerce-official-api-product-availability \
  --require-pass
```

An existing access token may be supplied with `EBAY_ACCESS_TOKEN` instead of
client credentials.

