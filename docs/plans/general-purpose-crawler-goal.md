# Goal — Evolve VeraCrawl into a General-Purpose AI Web Crawler

> Intended use: feed this file to `/goal`.
> Verified against repo state on 2026-05-13.
> One known deviation from the original draft: §4 wording adjusted because
> `ArtifactStorePort` already exists at `src/veracrawl/ports/artifact_store.py`
> (text-only `write/read` shape). The task is to **extend** the existing port,
> not to create a new one — see §4 for the revised contract.

---

你是一位資深 Python backend / distributed crawler / AI agent runtime engineer。請接手 GitHub repo `m24927605/veracrawl`，目標是把 VeraCrawl 從目前的 target-architecture / fixture-driven crawler spine，演進成可實際使用的「通用型 AI 網站爬蟲工具」。

請先閱讀以下文件與程式碼，不要只根據 README 下判斷：

- `README.md`
- `pyproject.toml`
- `docs/02-production-architecture.md`
- `docs/07-data-contracts.md`
- `docs/08-build-roadmap.md`
- `docs/10-target-implementation-design.md`
- `docs/11-target-testing-and-acceptance.md`
- `src/veracrawl/fetch/`
- `src/veracrawl/adapters/network/`
- `src/veracrawl/adapters/sources/`
- `src/veracrawl/normalize/`
- `src/veracrawl/extract/`
- `src/veracrawl/evidence/`
- `src/veracrawl/verify/`
- `src/veracrawl/publish/`
- `src/veracrawl/cli/`
- `tests/contract/`
- `tests/unit/`
- `tests/integration/`
- `tests/fixtures/`

目前 VeraCrawl 已有良好的 contract-first architecture、HTTP adapter、source acquisition lineage、normalization、candidate/evidence/publication gate、replay-oriented reports。但它仍偏 fixture/runtime-gate runner，不是完整通用 crawler app。請你的工作重點放在「讓它可以實際對任意授權網站執行 crawl job」，同時保留現有 evidence-first、policy-bounded、replayable 的核心設計。

## 核心目標

### 1. 建立真正可用的 External Crawl Job Runtime

- 目前 CLI 多半吃 `tests/fixtures`。
- 新增可以從 YAML / JSON job spec 啟動真實 crawl 的 runtime。
- 支援使用者指定 seed URLs、allowed domains、crawl depth、page limit、rate limit、adapter types、output schema、artifact output location。
- 不要破壞現有 fixture runners。
- 新 CLI 建議命名：
  - `veracrawl-crawl run <job_spec.yaml> --out <run_dir>`
  - 或整合到現有 CLI，但要保持清楚邊界。

### 2. 建立通用 CrawlJobSpec contract

請新增或擴充 contract，例如：

```yaml
CrawlJobSpec:
  id: string
  project_id: string
  objective: string
  seed_urls: list[string]
  allowed_domains: list[string]
  denied_domains: list[string]
  max_depth: int
  max_pages: int
  max_runtime_seconds: int
  per_origin_concurrency: int
  rate_limit:
    requests_per_minute: int
    crawl_delay_seconds: float | null
  source_adapters:
    - http
    - sitemap
    - rss
    - document
    - browser_snapshot
  robots_policy: obey | warn | deny_without_robots
  private_network_policy: deny
  artifact_policy:
    store_raw_html: bool
    store_headers: bool
    store_screenshots: bool
    store_documents: bool
  extraction:
    mode: none | deterministic | llm_assisted
    schema_ref: string | null
    exploratory_schema_allowed: bool
  output:
    format: jsonl | json
    include_raw_refs: bool
    include_evidence: bool
```

必須有 Pydantic validation。
必須拒絕危險預設，例如：

- empty `allowed_domains` 不可默默允許整個網路
- private network 預設 deny
- robots 預設 obey
- browser 預設 disabled，除非 job spec 明確允許
- page limit / runtime limit 必須有上限

### 3. 建立真正的 ExternalSourceRunner

新增 runtime，將 job spec 轉成：

- objective
- approved crawl plan
- frontier items
- network requests
- fetch attempts
- snapshots
- normalized documents
- evidence-bearing outputs

請盡量重用現有：

- `fetch.network_acquisition`
- `adapters.network.stdlib_http.StdlibHttpSourceAdapter`
- `normalize.pipeline`
- `extract.candidates`
- `evidence.coverage`
- `publish.gates`

但不要讓新的 production-ish crawl runtime 依賴 `tests/fixtures` 的 manifest。

### 4. 擴充 artifact store（既有 port 已存在，需擴充支援 bytes）

> 註：`src/veracrawl/ports/artifact_store.py` 已存在，目前 `ArtifactStorePort`
> 只支援 text-only 的 `write` / `read`。請**擴充**這個既有 port（或新增姊妹
> port），加入 bytes/binary API，並提供 filesystem implementation。
> 不要刪掉現有 `write` / `read`，以維持 fixture runtime 的回溯相容性。

請至少擴充至以下介面：

```python
class ArtifactStorePort(Protocol):
    # existing — keep for fixture-runtime backward compat
    def write(self, *, artifact_id: str, artifact_type: ArtifactType,
              producer_service: OwnerService, source_ref: Ref,
              content: str,
              privacy_classification: PrivacyClassification = ...) -> RuntimeArtifactRef: ...
    def read(self, artifact_ref: Ref) -> str | None: ...

    # new
    def put_bytes(self, artifact_ref: str, data: bytes, *,
                  content_type: str, metadata: dict[str, str]) -> ArtifactWriteResult: ...
    def put_text(self, artifact_ref: str, text: str, *,
                 content_type: str, metadata: dict[str, str]) -> ArtifactWriteResult: ...
    def get_bytes(self, artifact_ref: str) -> bytes: ...
    def exists(self, artifact_ref: str) -> bool: ...
```

並提供至少一個 filesystem implementation。

Filesystem layout 建議：

```
.veracrawl-runs/<run_id>/
  artifacts/
    raw-html/
    documents/
    normalized/
    screenshots/
    metadata/
  reports/
  events/
  outputs/
```

每個 artifact 必須有：

- content hash
- content type
- source URL
- created timestamp
- privacy classification
- replay ref

### 5. HTTP crawling 必須可以抓真實外部網站

使用現有 `StdlibHttpSourceAdapter`，但整理 production-ish factory：

- 注入 robots port
- 注入 rate limiter
- 注入 conditional cache
- 注入 cookie jar
- 注入 egress allowlist
- 注入 private network denial
- 注入 timeout / size budget
- 支援 redirect lineage

不要繞過現有 policy gate。不要允許 SSRF。不要允許預設抓 private network。不要忽略 robots。

### 6. Sitemap / RSS / document adapters 要支援 remote source

目前 `adapters/sources/structured_runtime.py` 偏本地 fixture parser。
請新增外部來源 adapter：

- `RemoteSitemapAdapter`
- `RemoteRSSAdapter`
- `RemoteDocumentAdapter`
- `RemoteFileImportAdapter`（可後續做）

Remote sitemap / RSS 應：

- 先透過 HTTP acquisition 抓取原始 XML
- 保存 raw artifact
- parse discovered URLs
- 產生 `discovered_url_refs`
- 不直接把 URL 塞進 frontier，必須經過 allowed domain / robots / budget policy

Remote document adapter 應至少支援：

- PDF download
- text/plain
- HTML document
- application/json metadata
- PDF / document text extraction

建立 document normalization pipeline：

- `normalize_document_artifact`
- PDF text extraction 可先用 PyMuPDF 或 pypdf；若 dependency 不想立即加入，先做 port + optional adapter。
- 支援 page-level anchors：page number、character offsets、text hash、raw artifact ref。
- 如果 PDF 無法抽文字，回傳 `needs_review`，不要假裝成功。
- OCR 可以設計 interface，但第一版可以標成 not implemented。

### 7. General extraction runtime

目前 `extract/candidates.py` 是 demo schema：title / summary / link_count。
請保留 demo extractor，但新增通用 extractor interface：

```python
class ExtractorPort(Protocol):
    def extract(self, request: ExtractionRequest) -> ExtractionCandidate | ExtractionResult: ...
```

第一版支援：

- deterministic metadata extractor
- link extractor
- document metadata extractor
- optional LLM-assisted extractor behind model provider port

LLM-assisted extraction 必須：

- structured output
- evidence anchors required
- missing anchor → `needs_review`
- LLM response 不可直接成為 source evidence
- raw prompt/response retention 受 policy 控制

### 8. AI crawler behavior

目標是「AI-assisted」，不是 uncontrolled autonomous crawler。
請建立 AI planner / site understanding adapter boundary：

- AI 可以 propose crawl plan
- AI 可以 recommend frontier prioritization
- AI 可以 propose extraction strategy
- AI 不可直接 mutate frontier durable state
- AI 不可 publish output
- AI 不可 bypass policy
- 所有 AI tool call / model call 必須有 trace / replay refs

第一版可以做 native deterministic planner，並留 model provider adapter。
不需要立刻接真實 LLM，但 contract 與 boundary 要可以接。

### 9. Frontier scheduler

建立真實 frontier loop：

- seed URL enqueue
- depth tracking
- canonical URL dedup
- visited set
- discovered link filtering
- max pages
- max depth
- per-origin rate budget
- retry/backoff
- terminal stop reason

每個 frontier transition 都要有 event。
每個 skipped URL 要有 skip reason，例如：

- `outside_allowed_domain`
- `robots_denied`
- `depth_exceeded`
- `duplicate`
- `budget_exceeded`
- `unsupported_scheme`
- `private_network_denied`

### 10. Replay report

每次 crawl run 完成後輸出：

- `reports/run_report.json`
- `reports/replay_report.json`
- `outputs/documents.jsonl`
- `outputs/links.jsonl`
- `outputs/extraction_candidates.jsonl`
- `outputs/evidence_packets.jsonl`

`run_report` 至少包含：

- run id
- job spec hash
- seed urls
- pages fetched
- pages skipped
- artifacts written
- extraction candidates
- evidence packets
- failures
- policy denials
- replay completeness result

### 11. Test strategy

不要只寫 happy path。必須新增 tests：

**Contract tests:**

- `CrawlJobSpec` validation
- `ArtifactStorePort` contract（涵蓋新舊兩組 API）
- External crawl report contracts
- Remote adapter contracts

**Unit tests:**

- allowed domain filtering
- private network denial
- canonical URL dedup
- frontier depth
- artifact write/read hash check
- document text anchor generation
- publication gate still rejects candidate without evidence

**Integration tests:**

- local static site crawl
- local sitemap crawl
- local RSS crawl
- local PDF/document crawl
- redirect lineage
- robots denied
- duplicate URL suppression
- missing artifact failure
- replay gap failure

所有 tests 必須預設不打外網。
外網測試要標記 `@pytest.mark.live`，並且預設 skip。

### 12. Backward compatibility

不要刪掉現有 fixture runners。不要破壞：

- `veracrawl-contracts validate`
- `veracrawl-runtime`
- `veracrawl-live-http`
- `veracrawl-structured-source`
- 現有 tests

新 runtime 應該是 additive。

### 13. Implementation constraints

- Python 3.11+
- 遵守目前 pyproject 的 mypy strict / ruff
- Pydantic v2
- 核心 domain 不可 import concrete adapters
- concrete adapters 必須放在 `adapters` package
- ports/interfaces 放 `ports` package
- runtime owner services 不可直接依賴 framework-native LLM / browser / DB objects
- 不要把 fixture-only assumptions 帶進 external crawl runtime

### 14. Acceptance criteria

完成後，以下指令必須通過：

```bash
uv run --python python3.12 --extra dev ruff check src tests
uv run --python python3.12 --extra dev mypy src
uv run --python python3.12 --extra dev pytest tests/contract tests/unit tests/integration
uv run --python python3.12 --extra dev veracrawl-contracts validate --format json
```

新增一個可執行 local crawl demo：

```bash
uv run --python python3.12 --extra dev veracrawl-crawl run \
  examples/crawl/static-site-job.yaml \
  --out .veracrawl-runs/static-site-demo
```

Demo 必須產生：

- raw artifacts
- normalized documents
- discovered links
- evidence anchors or evidence-ready candidates
- run report
- replay report

> 註：`examples/` 目錄與 `.veracrawl-runs/` 目錄目前皆不存在，需在實作中建立。

## 建議第一個實作順序

請按照以下順序做，不要一開始改太大：

**Phase 1:**

- `CrawlJobSpec` contract
- `FilesystemArtifactStore`（含新的 bytes API）
- External crawl CLI skeleton
- local static site integration fixture

**Phase 2:**

- HTTP external crawl loop
- frontier scheduler
- allowed domain / depth / max pages / dedup
- raw HTML artifact persistence
- normalized document output

**Phase 3:**

- remote sitemap / RSS adapter
- document/PDF artifact handling
- page/span anchors

**Phase 4:**

- extraction runtime interface
- metadata extractor
- evidence packet generation
- replay report

**Phase 5:**

- AI planner / LLM extractor adapter boundary
- model call trace
- tool call trace
- policy-bounded AI recommendations

## 請在完成後輸出

- 變更摘要
- 新增檔案清單
- 修改檔案清單
- 如何執行 demo
- 測試結果
- 尚未完成的 production gaps
- 後續建議

## 重要原則

- Raw artifacts must be real, not only refs.
- Candidates are not published outputs.
- Every extracted field must trace back to source evidence.
- LLM output cannot be source evidence.
- Policy denial must be visible, not silently bypassed.
- Replay gaps must fail or `needs_review`.
- Fixture runtime must remain intact.
- External crawl runtime must be bounded, safe, and auditable.
