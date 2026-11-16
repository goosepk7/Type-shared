# Roblox VFX platform notes (Effects)

These notes explain why `src/Shared/Effects` is built the way it is. They were checked against the Roblox Creator Docs in November 2026. Where a fact comes from the DevForum rather than the docs, it says so.

## Sources

- ParticleEmitter API: https://create.roblox.com/docs/reference/engine/classes/ParticleEmitter
- Particle emitters guide: https://create.roblox.com/docs/effects/particle-emitters
- Beam API: https://create.roblox.com/docs/reference/engine/classes/Beam
- Trail API: https://create.roblox.com/docs/reference/engine/classes/Trail
- Highlight API: https://create.roblox.com/docs/reference/engine/classes/Highlight
- Highlighting guide: https://create.roblox.com/docs/effects/highlighting
- Performance guide: https://create.roblox.com/docs/performance-optimization/improve
- Material enum: https://create.roblox.com/docs/reference/engine/enums/Material
- BloomEffect: https://create.roblox.com/docs/reference/engine/classes/BloomEffect
- Open Cloud Assets API (`POST https://apis.roblox.com/assets/v1/assets`, then poll `/assets/v1/operations/{id}`): https://create.roblox.com/docs/cloud/reference/features/assets
- DevForum, neon glow and bloom (community and staff posts; not official docs):
  - https://devforum.roblox.com/t/unified-neon-and-bloom-poll/180359
  - https://devforum.roblox.com/t/neon-parts-dont-glow-is-not-the-rendering/3276740
  - https://devforum.roblox.com/t/improvements-for-the-neon-material/38173

## Findings and how the code uses them

| Platform fact | What Effects does |
|---|---|
| Flipbooks: `FlipbookLayout` Grid2x2/4x4/8x8 on square textures up to 1024 px. The framerate is capped at 30. | Smoke and flame are 1024 px 4x4 sheets. Presets keep fps at or below 30 (spec-enforced). Low tier turns flipbooks off. |
| Emission is capped at 400 particles/s per emitter (about 100 on mobile). Particle lifetime is capped at 20 s. | Preset `rate` is at most 100 and `life` at most 20 (spec-enforced). Rain uses several low-rate emitters on a grid around the camera, not one dense emitter. |
| `ParticleEmitter.Shape`/`ShapeStyle`/`ShapeInOut` only apply when the emitter is parented to a BasePart. | Area emitters get an invisible pooled "carrier" part sized to the area. |
| `Emit(n)` emits a burst even while `Enabled = false`. | Bursts are pooled emitters with `rate = 0` plus `:emit(n)`. Released emitters stay parented until their particles die (the cooling list). |
| `Beam.ZOffset` layers overlapping beams. `CurveSize0/1` bend along the attachment's RightVector. | Layered beams (core and glow) get distinct ZOffsets. Arcing beams orient attachments so the curve is vertical. |
| Highlights: at most 255 at once. The first one costs up to about 1 ms of GPU on mobile. Avoid frequent Adornee/parent churn. | Highlights are pooled and enabled/disabled rather than created. Budgets allow 0 (Low) to 8 (Ultra). They are optional, so an effect never fails for lack of one. |
| Pool instances; keep purely visual effects on the client. | Everything is pooled. `Effects.play` on the server is inert unless `AllowServer` is set; the server sends `Effects.serialize(...)` to clients. |
| Disable CanCollide/CanTouch/CanQuery and CastShadow on decorative parts. Shadows are skipped below graphics quality 4. | Every pooled part is anchored, massless, non-colliding, non-queryable and casts no shadow. |
| `BasePart.LocalTransparencyModifier` is a client-only multiplier that never replicates. | Spawn materialize/dissolve fades the summon with it, so the replicated `Transparency` set by the summon builder is untouched. |
| Neon glow strength depends on graphics quality and the place's Bloom (DevForum; behaviour changed over time). | Spectral never relies on neon bloom alone. Every glowing body also has a ForceField or translucent shell, additive particles (`LightEmission` 1) and, budget permitting, a PointLight. It reads as glowing at any quality level. |
| Co-planar surfaces z-fight; the engine has no depth bias for parts. | Ground slots (`DecalOffset * slot`, 24 slots), shell ratio of at least 1.25, buried bottoms, unequal lengths for crossed parts, and a 7% scale-up for stacked identical effects. The spec checks every effect in both styles. |
| Open Cloud `Image` asset upload returns an image id usable directly as `rbxassetid://` once moderation approves it. | `assets/textures/upload.py` uploads idempotently (sha1) and writes `AssetIds.luau`. Until an id exists, `Assets.texture` falls back to a built-in `rbxasset://textures/particles/*` texture. |

## Uncertain or unverified

- **Built-in fallback paths.** The `rbxasset://textures/particles/...` paths (sparkles_main, fire_main, smoke_main, ...) are long-standing engine content but are not documented as a stable API. They are only used until the uploaded ids clear moderation.
- **Moderation.** All 30 uploaded textures were in the "Reviewing" moderation state at hand-off.
- **No live render check.** The Lune tests check geometry, budgets and leaks, not pixels. A Studio pass on a phone is still needed to judge look and feel.
