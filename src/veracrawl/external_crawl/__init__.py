"""External (non-fixture) crawl runtime.

This package hosts the runtime that executes
:class:`~veracrawl.contracts.crawl_job.CrawlJobSpec` against real,
authorised web sources. It deliberately lives in its own subpackage
so the existing fixture-runtime modules (``runtime``, ``target_runtime``,
``source_runtime`` …) remain untouched.

Submodules:

* :mod:`veracrawl.external_crawl.url` — URL canonicalisation + the
  domain / scheme / private-network filter used by the frontier.
"""
