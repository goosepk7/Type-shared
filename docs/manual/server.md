# Manual steps: WordEngine server (for Bruce)

There are two games:

| Game | Universe | Place |
|---|---|---|
| Type to Defend | 10777140395 | 109889925586054 |
| Typing Wizards | 10777140284 | 117303085664849 |

Do steps 1–2 in **each** game.

## 1. Anthropic API key secret (done 2026-11-16)
1. Go to Creator Dashboard > the experience > **Secrets** > Create Secret.
2. Use these values:
   - Name: `ANTHROPIC_API_KEY`
   - Secret: the `sk-ant-...` key. Use one key per game so they can be revoked separately.
   - Domain: `api.anthropic.com`
3. The server reads it only with `HttpService:GetSecret`. It is never logged and never sent to
   clients.

## 2. Allow HTTP requests
In Studio, go to File > Experience Settings > Security and turn on **Allow HTTP Requests**, then
publish.

## 3. Studio play-solo
- Secrets don't exist in local play-solo, so the server uses the **Mock AI**. The Output window shows
  `*** MOCK AI PROVIDER ACTIVE ***`, and mock words say "[MOCK] Studio stand-in for real AI.".
- Mock results are never promoted.
- To test the real AI in Studio, either add a Local Secret (Experience Settings > Security > Local
  Secrets) or use Team Test.

## 4. Cost controls
All of these are in `src/Shared/Config.luau`, under `Config.AI`.

| Setting | Default | What it does |
|---|---|---|
| `DailyBudgetUSD` | 5 | Hard cap per game per UTC day, across all servers (MemoryStore counter). When it's reached, new words fall back to the library guess until midnight UTC. |
| `NewPhrasePerMinute` | 6 | New phrases each player may send to the AI per minute. |
| `Enabled` | — | Turns the AI on or off at startup. |

**Live kill switch** (from the server console in a live server, or from an admin command):

```lua
local AI = require(game.ServerScriptService.WordEngineServer.AI)
AI.setEnabled(false, yourUserId) -- all servers stop calling the AI within seconds
AI.setEnabled(true, yourUserId)  -- turn it back on
print(AI.status())               -- provider, todayUsd, budget, circuit, queue
```

This stores the flag in DataStore `WordEngine_Control_v1` and broadcasts it with MessagingService.
Servers also re-poll it every 30 s.

## 5. Team Test live check (do once per game)
1. In Studio, choose Test > Team Test, start a server and join it.
2. Type **50 phrases that are not in the library**, such as "glitter hamster", "lava toaster" or
   "sleepy comet".
3. In the server console, run:
   ```lua
   local S = require(game.ServerScriptService.WordEngineServer)
   local st = S.stats() ; print(st.aiCalls, st.cacheHitRate, st.avgCostPerAiPhrase, st.todayUsd, st.avgAiLatencyMs)
   ```
4. Check the results:
   - `aiCalls` (HTTP requests) should be at most 50; batching may make it lower. `aiResults` should be
     50, which means each phrase was sent once.
   - Type the same 50 again. `aiCalls` must not rise, and `st.cache.hits` should rise by 50.
     `cacheHitRate` should be about 0.5.
   - `avgCostPerAiPhrase` is the average cost per phrase. Expect about $0.0002–0.0006 when the
     prompt cache is warm.
   - `todayUsd` is the spend counted across all servers.
5. Open a second Team Test server and type the same phrases. It should show **zero** new AI calls,
   because the results come from MemoryStore and DataStore.

## 6. Promoting AI words into the library (`tools/promote.py`)
1. Get an Open Cloud API key (Creator Dashboard > Open Cloud > API Keys).
   - Add both universes.
   - Scopes: `universe-datastores.objects:list`, `universe-datastores.objects:read` and
     `universe.ordered-data-store.scope.entry:read`.
   - Inside the Claude Code environment no key is needed for data stores, because the proxy
     authenticates them. However, the proxy credential is **missing the ordered-data-store scope**,
     so add that scope to the proxy key, or run with your own key.
2. Run it. Locally, first set `export ROBLOX_OPEN_CLOUD_KEY=...`. The key is only read from this
   environment variable.
   ```
   python3 tools/promote.py                          # pulls both games, writes data/promotion/{candidates.json,report.md}
   python3 tools/promote.py --min-plays 25 --write   # also writes data/words/promoted_NN.jsonl
   python3 tools/promote.py --approve my_list.txt --write
   ```
3. Review `report.md`. It covers:
   - popular new phrases
   - conflicts between the games
   - fallback phrases that the library still doesn't cover
4. Run `python3 tools/validate.py` and `python3 tools/build_library.py`.

## 7. Blocklist
`data/blocklist.txt` and `src/Server/BlocklistData.luau` hold **hashes only**. To add a word, hash it
with Lune and append the line, choosing `exact1` or `contains1`:

```lua
-- in a Lune script loaded with tests/loader.luau, or pasted into the Studio command bar:
local B = require(game.ServerScriptService.WordEngineServer.Blocklist)
print(B.hash(B.skeleton("theword", 1)), B.hash(B.skeleton("theword", 2)))
```

Lines are `<set> <hash>`. The sets are `exact1`/`exact2` (the whole token) and
`contains1`/`contains2` (a substring). Put `1` hashes in the `*1` sets and `2` hashes in the
`*2` sets, following the existing file.

Never commit the plain word. For an urgent ban in a live game, use the Admin ban tools, which call
`Safety.addBlocked` at runtime.
