# Platform notes: services layer (Data, WordBook, Currency, Purchases, Analytics, Admin, UI)

Checked against create.roblox.com on 2026-11-16. Each finding lists what the code does about it.

## DataStores

Source: [Error codes and limits](https://create.roblox.com/docs/cloud-services/data-stores/error-codes-and-limits),
[DataStoreService](https://create.roblox.com/docs/reference/engine/classes/DataStoreService),
[GlobalDataStore:UpdateAsync](https://create.roblox.com/docs/reference/engine/classes/GlobalDataStore),
[DataStore:ListKeysAsync](https://create.roblox.com/docs/reference/engine/classes/DataStore).

| Limit | Value | Our handling |
|---|---|---|
| Per-server read / write (standard) | 60 + 40 x players per minute each | `Data/Queue` waits on `GetRequestBudgetForRequestType` before every call |
| Per-server ordered write | 30 + 5 x players / min | Analytics flushes at most `TopWordsFlushPerCycle` / `UnknownFlushPerCycle` ordered writes per 120 s, Low priority |
| Experience-wide (all servers + Open Cloud) | read 300 + 40 x CCU, write 300 + 20 x CCU / min | Analytics and Admin use Low/Normal priority so player saves win |
| Per-key throughput | 25 MB/min read, 4 MB/min write | Autosave 90 s per player, staggered (one save per tick) |
| Queue | 30 requests per queue, errors 301-306 when full | treated as transient: exponential backoff |
| Value size | 4,194,304 bytes | word book capped at 1,500 entries (~100 KB); `WarnBytes` |
| Key / store name | 50 chars | keys are `u_<userId>`, phrases are capped at 40 chars |
| Storage | 500 MB + 1 MB x lifetime users | negligible for our record sizes |

- **New:** `DataStoreService:SetRateLimitForRequestType(type, base, perPlayer)` lets a server lower its own limits.
  Not used yet; a good lever if analytics ever crowds player saves.
- Studio "Run" uses separate (lower) static limits. Studio without "Enable Studio Access to API Services" fails every
  call with a permanent error: `Data.start()` detects that and switches to the in-memory `LocalStore` (logged).
- `UpdateAsync` transforms may run more than once and must not yield; ours are pure. Returning `nil` cancels the write,
  which is how a session that lost its lock refuses to overwrite newer data. The transform may return `userIds`
  (GDPR association), which we pass.
- [DataModel:BindToClose](https://create.roblox.com/docs/reference/engine/classes/DataModel): the server waits
  30 s for bound functions. `Data` releases every session in parallel with a 24 s deadline.

### Session locking design (ProfileStore-style)

Record: `{ format, meta = { created, updated, saves, lock = { job, session, place, t } }, ns = { [name] = { v, d } } }`.

1. Load = `UpdateAsync`: take the lock if free, ours, or stale (`LockStaleSeconds` 330 = 3 missed autosaves + slack).
2. Fresh lock held elsewhere: publish a release request (MessagingService `WordEngine_ReleaseLock`); the holder
   saves + releases + kicks ("You joined another server"). After `LockWaitSeconds` (12 s) we steal.
3. Every save is `UpdateAsync` that first checks `lock.session == mine`. A stolen session never writes; it ends and the
   player is kicked with a rejoin message. Stealing is therefore safe for integrity (at most the holder's unsaved
   last seconds are lost, the same trade-off ProfileService makes).
4. Load failure after retries -> the player is kicked ("nothing was lost") rather than playing on a blank profile that
   could later overwrite the real one.
5. Namespaces: games register their own `{ template, version, migrations }`. Migrations run in order
   (`migrations[n]` upgrades n-1 -> n). Data written by a newer version is frozen (read-only) for the session, a
   failing migration also freezes the namespace, and namespaces this server doesn't know are carried through untouched.

## Developer products and game passes

Source: [Developer products](https://create.roblox.com/docs/production/monetization/developer-products),
[MarketplaceService](https://create.roblox.com/docs/reference/engine/classes/MarketplaceService),
[Passes](https://create.roblox.com/docs/production/monetization/passes).

- Only one `ProcessReceipt` callback per experience ("This can only be done once by one server-side script").
  `Purchases.start()` owns it; games register handlers with `Purchases.registerProduct`.
- Return `PurchaseGranted` only once items are granted; `NotProcessedYet` makes Roblox redeliver, e.g. "next time
  the user joins". Never grant from `PromptProductPurchaseFinished`.
- Idempotency is our job. Design: grant + record `PurchaseId` in the same synchronous profile update (handlers may not
  yield; a yielding handler is rejected), then `saveAsync`; only a successful save returns `PurchaseGranted`. The
  session lock makes check-then-grant single-writer. A ring of 64 ids per player plus a global
  `WordEngine_Receipts_v1` store (written after grant) catch redeliveries.
- Passes: the docs show `UserOwnsGamePassAsync` on join (pcall) and `PromptGamePassPurchaseFinished` for in-session
  buys, and say nothing about caching. We cache positives for the session (ownership never goes away mid-session),
  negatives for `GamePassCacheSeconds` (600 s), keep the last known value on API errors, and flip the cache on
  `PromptGamePassPurchaseFinished(wasPurchased = true)`.

## HttpService, Open Cloud and Secrets (cross-game sharing)

Source: [HTTP service](https://create.roblox.com/docs/cloud-services/http-service),
[Secrets stores](https://create.roblox.com/docs/cloud-services/secrets),
[Open Cloud data stores](https://create.roblox.com/docs/cloud/guides/data-stores),
[Data and memory stores API](https://create.roblox.com/docs/cloud/reference/features/storage).

- **Feasible:** game servers can now call a subset of Open Cloud endpoints through `HttpService`, including v2 data
  store entries (Get/Create/Update/Delete/Increment/List, with or without scope), ordered data stores and memory
  stores. The `x-api-key` header must be a `Secret` (`HttpService:GetSecret`); only `x-api-key` and `content-type`
  headers are allowed; `..` is not allowed in path segments. 2,500 Open Cloud requests/min per server (separate
  from the 500/min HTTP budget). Open Cloud data store traffic shares the target universe's experience-wide limits.
- Update Data Store Entry (PATCH) supports `allowMissing=true` and an `etag` for optimistic concurrency; partial
  update is unsupported (users/attributes are cleared if omitted).
- Secrets are only available in live servers and Team Test; local play-solo needs Local Secrets
  (File > Experience Settings > Security). Secrets cannot go in a request body.
- **Decision (brief 4, DESIGN.md §10):** in-game cross-universe word-book sync is dropped. The word book is per game in
  v1. `WordBook.export/import` + a conflict-free union merge (max count, min first, max last, OR of game bits) are the
  seam for a later merge. Cross-game sharing of words is an offline promotion pipeline (`tools/promote.py`, Open Cloud
  key from env vars). Stores it reads from this layer: `WordEngine_Unknown_v1` (ordered, global scope, phrase -> count),
  `WordEngine_TopWords_v1` (ordered, scope = game), `WordEngine_Analytics_v1` (key `<Game>/<YYYY-MM-DD>`).

## AnalyticsService

Source: [AnalyticsService](https://create.roblox.com/docs/reference/engine/classes/AnalyticsService),
[Custom events](https://create.roblox.com/docs/production/analytics/custom-events),
[Economy events](https://create.roblox.com/docs/production/analytics/economy-events).

- `LogCustomEvent(player, eventName, value?, customFields?)`. Event names have a much tighter cardinality limit than
  custom fields, so we use a fixed set (`WordInterpreted`, `WordCast`, `DidYouMean`, `Purchase`) and put variety in
  `CustomField01..03` (limit: 8,000 unique combinations per experience). Source x Element x Category = 975 combos.
  Words themselves are never event names or fields (unbounded); they go to our OrderedDataStore rollup.
- `LogEconomyEvent(player, flowType, currency, amount, endingBalance, transactionType, sku, fields?)`: max 5
  currencies, 20 transaction types, 100 SKUs per experience. `Currency` emits these; keep currency count <= 5.
- Our rollup (all servers): daily counters (words, fallback, cache hits, AI calls, AI cost, AI latency, tokens,
  did-you-mean shown/accepted, purchases) add-merged with `UpdateAsync`; most-typed words and unknown phrases in
  ordered stores. Unknown phrases are logged only when Safety did not refuse them and they are letters/spaces/hyphens
  only (no digits, so no phone numbers or codes).

## UI platform

- [ScreenGui](https://create.roblox.com/docs/reference/engine/classes/ScreenGui): `ScreenInsets = CoreUISafeInsets`
  keeps HUD clear of notches and the Roblox top bar; `ClipToDeviceSafeArea` defaults to true;
  `SafeAreaCompatibility = FullscreenExtension` (default) auto-extends full-screen frames (our modal scrim).
  [GuiService.TopbarInset](https://create.roblox.com/docs/reference/engine/classes/GuiService) is available if a
  widget must align with the top bar.
- [TextBox](https://create.roblox.com/docs/reference/engine/classes/TextBox): `FocusLost(enterPressed)` plus
  `ReturnPressedFromOnScreenKeyboard` on mobile/console; `ClearTextOnFocus = false`; `ShowNativeInput` exists.
  [UserInputService](https://create.roblox.com/docs/reference/engine/classes/UserInputService)
  `OnScreenKeyboardVisible/Position/Size` let the typing bar lift above the keyboard.
- [UIDragDetector](https://create.roblox.com/docs/reference/engine/classes/UIDragDetector): `DragStyle =
  TranslateLine`, `BoundingUI`, `DragContinue/DragEnd` events; used for the settings sliders (tap-to-jump and D-pad
  stepping added for accessibility).
- [Font](https://create.roblox.com/docs/reference/engine/datatypes/Font): bundled families include Builder Sans,
  Builder Extended and Builder Mono (`rbxasset://fonts/families/*.json`), used via `Font.new(family, weight)`; no
  asset upload needed.
- [UIStroke](https://create.roblox.com/docs/reference/engine/classes/UIStroke) (`ApplyStrokeMode`, `LineJoinMode`,
  `BorderStrokePosition`, `StrokeSizingMode`), `UICorner`, `UIGradient` (Transparency sequences give the radial
  cooldown sweep without images).
- [TextChatCommand](https://create.roblox.com/docs/reference/engine/classes/TextChatCommand): `Triggered` fires on the
  sending client and the server, and the command text is not replicated to other users: safe for `/we` admin
  commands (validated server-side anyway).
