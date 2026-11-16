# MANUAL_STEPS.md: things only Bruce can do

Everything else is automated. Detail for each step lives in `docs/manual/` (linked below).

| Game | Universe | Place |
|---|---|---|
| Type to Defend | 10777140395 | 109889925586054 |
| Typing Wizards | 10777140284 | 117303085664849 |

## Checklist

| # | Step | Where | Status |
|---|---|---|---|
| 1 | Add secret `ANTHROPIC_API_KEY` (domain `api.anthropic.com`), one key per game | Creator Dashboard > experience > Secrets | Done 2026-11-16 |
| 2 | Turn on **Allow HTTP Requests** | Studio > File > Experience Settings > Security | Done 2026-11-16 |
| 3 | Turn on **Enable Studio Access to API Services** in both games, so DataStores work in Studio | Studio > File > Experience Settings > Security | Done 2026-11-16 |
| 4 | Admins: the owner of the group that owns each game (rank 255) is admin automatically. Add extra admins with `Config.Services.Admin.UserIds` | `src/Shared/Config.luau` | Automatic |
| 5 | Create developer products and game passes when each game needs them, and send Claude the ids | Creator Dashboard > Monetization | Per game thread |
| 6 | Add the scope `universe.ordered-data-store.scope.entry:read` (both universes) to the Open Cloud key used by the Claude environment, so the promotion tool can read play counts and the unknown-word log | Creator Dashboard > Open Cloud > API Keys | To do (optional) |
| 7 | Check the 30 effect textures cleared moderation (group 685727405); until then built-in textures are used | Creator Hub > Development Items > Images | Check later |
| 8 | Team Test live check: type 50 new phrases, confirm each is sent to the AI once and is free the second time | `docs/manual/server.md` §5 | After games are published |
| 9 | Optional: add `ANTHROPIC_API_KEY` as a **Local Secret** to test the real AI in Studio play-solo (otherwise a loud mock is used) | Studio > Experience Settings > Security > Local Secrets | Optional |

## Notes

- **Cost controls.** Daily AI spend cap ($5 per game per UTC day by default), a per-player new-phrase limit and a live
  kill switch (`/we ai off`). See `docs/manual/server.md` §4.
- **Admin chat commands.** `/we test <phrase>`, `/we ban <phrase>`, `/we cache <phrase>`, `/we ai`, `/we stats`,
  `/we unknown` and more. See `docs/manual/services.md` §2.
- **Promoting AI-learned words into the shared library.** `python3 tools/promote.py`. See `docs/manual/server.md` §6.
- **Test place.** `rojo build test.project.json -o WordEngineTest.rbxlx`, open it and press Play: type any word and see
  it in both styles side by side. See `docs/manual/services.md` §6.
- **Effects textures.** Regenerate/upload with `assets/textures/generate.py` and `upload.py`. See `docs/manual/vfx.md`.
