# Effects textures: regenerate and upload

The textures are generated procedurally and deterministically, so they never need hand edits.

```
python3 assets/textures/generate.py                 # writes assets/textures/*.png (Pillow + numpy)
python3 assets/textures/upload.py --group 685727405 # uploads new/changed PNGs, writes src/Shared/Effects/AssetIds.luau
```

How `upload.py` works:

- **API key.** It reads an Open Cloud API key with `asset:write` from `$ROBLOX_API_KEY`, or relies on a proxy that injects the credentials.
- **Idempotent.** It is keyed by the PNG's sha1 in `assets/textures/ids.json`. Unchanged files are skipped; a changed file gets a new asset.
- **Output.** It regenerates `AssetIds.luau`. `Assets.luau` reads it and falls back to built-in textures for anything missing.

## Textures

There are 30 textures. Every one was uploaded and was in the "Reviewing" moderation state at hand-off; `assets/textures/ids.json` holds the ids.

| Kind | Textures |
|---|---|
| Glow and energy | glow, glow_core, spark, star, burst, ring, swirl, beam_lightning, beam_energy |
| Ground decals | shadow, scorch, crack, frost, rune_circle |
| Flipbooks (1024 px, 4x4) | runes_4x4, smoke_4x4, flame_4x4 |
| Particles | raindrop, bubble, snowflake, shard, leaf, petal, heart, arrow_down, plus, music_note, zzz, question, pixel |

## Notes

- **Moderation.** Check it in Creator Hub > Development Items > Images (group-owned). `ids.json` records the state at upload time only; re-running `upload.py` does not refresh it.
- **Stray asset.** A test upload left a stray Decal asset, 83245574984127. It is harmless and can be archived.
