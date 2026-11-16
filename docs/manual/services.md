# Manual setup: services (do these once per game)

Do these in **both** Typing Wizards and Type to Defend unless noted.

## 1. Data stores in Studio

1. Open the place in Studio, then **File > Experience Settings > Security**.
2. Turn on **Enable Studio Access to API Services** (needed for real DataStores while testing). Without it the engine
   logs a warning and uses an in-memory store, so nothing persists.
3. Turn on **Allow HTTP Requests** (the AI provider needs it).
4. Publish the place at least once so DataStores exist for the universe.

## 2. Admins

Edit `Config.Services.Admin.UserIds` in `src/Shared/Config.luau` (or call `Config.set("Services.Admin.UserIds",
{ 123, 456 })` before `WordEngineServer.start`). The experience owner is admin automatically; in Studio everyone is.
Optional: set `GroupId` + `MinGroupRank` to use a group rank instead.

Chat commands (type in chat): `/we test giant fire shark`, `/we ban <phrase>`, `/we unban <phrase>`,
`/we force <phrase> {json}`, `/we retag <id> {json}`, `/we cache <phrase>`, `/we cachelist [prefix]`,
`/we cacheedit <phrase> {json}`, `/we cacheretag <phrase> {json}`, `/we cachedelete <phrase>`, `/we ai off`,
`/we ai on`, `/we ai` (spend vs cap), `/we stats`, `/we unknown`, `/we history`, `/we audit`.
Every action is audit-logged in DataStore `WordEngine_Audit_v1` (one key per UTC day).

## 3. Developer products and game passes

1. Creator Dashboard > your experience > **Monetization > Developer Products** > Create. Note each product id.
2. **Monetization > Passes** > Create. Note each pass id.
3. In the game's server script, before `WordEngineServer.start(...)`:

```lua
local S = require(game.ServerScriptService.WordEngineServer)
S.Currency.define("Gems", { initial = 0 })
S.Purchases.registerCurrencyProduct(1234567890, "Gems", 100)   -- product id from step 1
S.Purchases.registerGamePass(987654321, function(player) player:SetAttribute("VIP", true) end)
```

Do **not** set `MarketplaceService.ProcessReceipt` anywhere else; the engine owns it.

## 4. Secrets (AI key)

Creator Dashboard > experience > **Secrets** > Create Secret, name as configured (`Config.AI.SecretName`), domain
`api.anthropic.com`. For local play-solo testing add the same name under **File > Experience Settings > Security >
Local Secrets**. In-game cross-universe sync is not used (brief 4), so no Open Cloud key is needed in-game. The
offline `tools/promote.py` uses an Open Cloud API key from an environment variable with
`universe-datastores.objects:read` (+ `list`) on both universes.

## 5. Analytics

Creator Dashboard > experience > **Analytics** shows `WordInterpreted`, `WordCast`, `DidYouMean`, `Purchase` custom
events and economy events automatically. Our own rollups live in DataStores (`WordEngine_Analytics_v1`,
`WordEngine_TopWords_v1`, `WordEngine_Unknown_v1`); view them with `/we stats`, `/we history`, `/we unknown`.

## 6. Test place

`rojo build test.project.json -o WordEngineTest.rbxlx` (or `rojo serve test.project.json` + the Rojo plugin), open it,
publish to a place (so DataStores work), then Play. Type any word; both summon styles appear side by side.
