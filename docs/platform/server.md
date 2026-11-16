# Server platform findings (STEP 0)

Verified 2026-11-16 against the live Roblox Creator Docs and the Claude API reference. Where this
contradicts DESIGN.md, this file wins and the code follows it.

## HttpService
Source: https://create.roblox.com/docs/cloud-services/http-service (page last updated 2026-11-16)

- "Allow HTTP Requests" must be on (File > Experience Settings > Security), per game.
- 500 HTTP requests/min per server for normal (non-Open-Cloud) traffic. Our AI limiter is 60/min.
- Open Cloud **is** callable from HttpService for a listed subset of endpoints, including DataStore
  entries and MemoryStore sorted maps. There is a separate budget of 2,500 requests/min per server;
  going over it stalls requests for about 30 s ("Number of Open Cloud requests exceeded limit").
  Restrictions: only the `x-api-key` and `content-type` headers are allowed, `x-api-key` must be a
  Secret, there must be no `..` in path params, and only HTTPS on standard ports.
  **Decision (brief 4):** in-game Open Cloud sync is dropped. Promotion is done offline by
  `tools/promote.py`.

## Secrets Store
Source: https://create.roblox.com/docs/cloud-services/secrets

- Create one under Creator Dashboard > experience > Secrets: a name, a value and an allowed domain
  (wildcards are allowed). Limits: 500 secrets per experience, 1,024 chars each.
- `HttpService:GetSecret(name)` returns a Secret object. `print` shows `Secret(name)`, never the
  value. `AddPrefix` / `AddSuffix` are available, for example `"Bearer "`.
- A Secret can only be used in the URL or headers, never in the body.
- Secrets are available **only on live servers and in Team Test**. In local play-solo and in client
  scripts, the call errors with "Can't find secret with given key".
  Studio > Experience Settings > Security > Local Secrets can supply one locally. Without that, our
  server uses the **Mock provider**, which logs a loud warning.

## MemoryStore
Source: https://create.roblox.com/docs/cloud-services/memory-stores

| Limit | Value |
|---|---|
| Memory quota | 64 KB + 1.2 KB × users |
| Requests | 1000 + 120 × CCU units/min |
| Max value size | 32 KB |
| Max expiration | 45 days (3,888,000 s) |
| Sorted-map key | 128 chars |
| Throughput per partition | about 30k units/min |

We use one sorted map, `WordEngine_WordCacheHot_v1`. It holds:
- hot records (7-day TTL)
- `lock:<key>` de-dup locks (20 s)
- `spend:<YYYY-MM-DD>` daily-spend counters in micro-USD (2-day TTL)

## DataStore
Source: https://create.roblox.com/docs/cloud-services/data-stores/error-codes-and-limits

- Request limits are now **experience-level** and shared with Open Cloud:
  - read 300 + CCU × 40 per minute
  - write 300 + CCU × 20 per minute
  - list 300 + CCU × 2 per minute

  The older per-server figures (60 + players × 10) in DESIGN.md are out of date.
- Per-key throughput: read 25 MB/min, write 4 MB/min.
- Values can be up to 4,194,304 chars. Keys, store names and scope names can be up to 50 chars.
- Cache keys are `w1:<phrase>`, at most 43 chars. Unusual phrases are hashed to `#<16 hex>`.

## Open Cloud v2 (used by tools/promote.py)
Sources:
- https://create.roblox.com/docs/cloud/reference/features/storage
- https://create.roblox.com/docs/cloud/guides/data-stores

| Operation | Endpoint and notes |
|---|---|
| List entries | `GET /cloud/v2/universes/{u}/data-stores/{ds}/entries?maxPageSize=256&filter=id.startsWith("w1:")&pageToken=` returns only `path` / `id`. |
| Get one entry | `GET .../entries/{id}@latest`. `@` in an id selects a revision. Returns `{value, etag, ...}`. |
| Ordered data store | `GET /cloud/v2/universes/{u}/ordered-data-stores/{ods}/scopes/{scope}/entries?maxPageSize=100&orderBy=value desc` returns `orderedDataStoreEntries: [{path, value, id}]`. |

Scopes:
- `universe-datastores.objects:list` and `universe-datastores.objects:read`
- `universe.ordered-data-store.scope.entry:read`

**Proxy test (2026-11-16):** from the Claude Code environment, with no key:
- `GET .../universes/{10777140395,10777140284}/data-stores` returns 200 `{}`. Both universes have no
  data stores yet.
- Entry list on a missing store returns 404. `promote.py` treats this as empty.
- **Ordered-data-store reads return 403 "Scope not authorized".** The proxy credential lacks
  `universe.ordered-data-store.scope.entry:read`, so `WordEngine_Unknown_v1` and the play counters
  can't be read from here until that scope is added. `promote.py` warns and continues.

## TextService
Sources:
- https://create.roblox.com/docs/reference/engine/classes/TextService
- https://create.roblox.com/docs/reference/engine/classes/TextFilterResult
- https://create.roblox.com/docs/ui/text-filtering

`FilterStringAsync(text, fromUserId, Enum.TextFilterContext.PublicChat)` returns a
`TextFilterResult`. From it:
- `GetNonChatStringForBroadcastAsync()` is for text everyone sees.
- `GetNonChatStringForUserAsync(toUserId)` is for text one user sees.
- `GetChatForUserAsync` is deprecated.

Filtering is mandatory: experiences that skip it get removed. We fail closed (`""`) on error.
Studio filtering behaviour differs from live servers, so check it in Team Test.

## require-by-string
Source: https://create.roblox.com/docs/reference/engine/globals/LuaGlobals#require

`require` accepts a ModuleScript, an asset id or a **string path**:
- `./` resolves from `script.Parent`, `../` from `script.Parent.Parent`, `@self/` from `script`,
  and `@game/` from `game`.
- It does not wait for children to load.
- A DevForum thread reports a client-side bug.

We keep instance requires (`require(script.Parent.X)`) because the Lune test loader
(`tests/loader.luau`) emulates those.

## Claude API (Anthropic)
Source: the bundled claude-api reference (2026), https://docs.anthropic.com

- `POST https://api.anthropic.com/v1/messages` with headers `x-api-key`,
  `anthropic-version: 2026-10-21` and `content-type`.
- Model `claude-haiku-5-5` costs $0.10 / MTok input and $0.50 / MTok output. Cache reads cost 0.1×;
  5-minute cache writes cost 1.25×. The minimum cacheable prefix is 512 tokens.
- Forced `tool_choice` (`{type:"tool"}`) with `strict: true` is supported. If a 400 mentions
  `tool_choice`, we fall back automatically to `output_config.format` json_schema.
- We set `thinking: {type:"disabled"}` with effort `low`. Requests send no `temperature` and no
  prefill (both are rejected on this API version).
- `stop_reason: "refusal"` is handled: a batch is split, and a single refusal is cached as refused.
- `usage` returns `input_tokens`, `output_tokens`, `cache_creation_input_tokens` and
  `cache_read_input_tokens`. These feed the daily spend cap.
