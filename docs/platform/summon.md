# Summon builder: Roblox platform notes

Research behind `src/Shared/Summon` (DESIGN.md §8), checked against the Roblox Creator Docs in November 2026.
Each heading lists the source URLs and then what we built because of it.

## Procedural parts beat EditableMesh for summons

Source: https://create.roblox.com/docs/reference/engine/classes/EditableMesh.md

What the docs say:
- **Limits.** An EditableMesh can hold at most 60,000 vertices and 20,000 triangles. A quad counts as two
  triangles.
- **Memory.** The docs call editable assets "expensive for memory usage". Clients have strict budgets, while the
  server, Studio and plugins have no memory limit.
- **Off by default.** Published games block EditableMesh until the creator turns on **Enable Mesh / Image APIs**.
  The setting is in the Creator Dashboard under Configure → Settings, or in Studio under Experience Settings →
  Security, and the creator must accept the Terms of Use to enable it.
- **FixedSize.** A mesh loaded from an existing asset is fixed-size by default. You can edit vertex positions and
  attributes but not add or remove vertices or faces. Pass `{FixedSize = false}` to `CreateEditableMeshAsync` to
  allow that.
- **Ownership.** `CreateEditableMeshAsync` only loads assets owned by the game owner, the Studio user or the
  player, or explicitly shared with them. Group assets count if the user's role can edit them.
- **Display.** `AssetService:CreateMeshPartAsync` creates a MeshPart that shows the mesh, and
  `MeshPart:ApplyMesh` attaches a mesh to an existing MeshPart. After a geometry edit you must call them again to
  update collision.

What we built:
- **Primitives only.** Summons are built from Parts: Block, Ball, Cylinder, Wedge, and an ellipsoid made from a
  Block with a `SpecialMesh` of type Sphere. This needs no setting or opt-in, costs no per-client mesh memory,
  replicates nothing new, and is easy to budget, at 8–40 parts per summon.
- **EditableMesh is held back.** We would only use it for later hero sculpts, and only behind the opt-in.

## Uploaded meshes for signature summons (Open Cloud)

Source: https://create.roblox.com/docs/cloud/guides/usage-assets

What the docs say:
- **Model assets** accept `.fbx`, `.gltf`, `.glb`, `.rbxm` and `.rbxmx`, and are uploaded as packages.
- **Mesh assets** accept only Roblox-sourced mesh data, downloaded from Asset Delivery.
- **Size.** Each create or update call is limited to 20 MB.
- **Updates.** Only `.fbx` content can be updated, and each update creates a new version.
- **Polling.** A create call returns `operations/{id}`. Poll `GET https://apis.roblox.com/assets/v1/operations/{id}`
  until `done` is true, then read `assetId`.
- **Upload from this container.** The Type to Defend thread found that `.glb` → Model upload works from this
  container. The proxy injects the API key, so send the header `x-api-key: dummy` and set the creator to the
  group. They load the result at runtime with `InsertService:LoadAsset`
  (https://create.roblox.com/docs/reference/engine/classes/InsertService).

What we built:
- **Register a mesh with a signature.** Call
  `Summon.registerSignature(id, fn, { plan, mesh = { assetId, scale?, offset?, keepRoles? } })`, or
  `Summon.setSignatureMesh(id, mesh)` to add one later.
- **What the blueprint carries.** The blueprint gets `meshAsset`, and the procedural build is always made first.
  It is the fallback until the mesh loads, and the face, accents, material details and effects stay procedural on
  top of the mesh.
- **What `Instantiate.attachMesh` does:**
  - loads the asset;
  - scales it to the procedural height;
  - welds it to the `Body` bone;
  - hides the procedural body parts, keeping the roles eye, mouth, brow, lid, blush, gem, glow, light, hat and
    held, any role listed in `keepRoles`, and accent parts.
- **Safe failure.** If the load fails, nothing changes.
- **Not verified.** We have not checked in a live server that `LoadAsset` works on the client for group-owned
  assets. Call it on the server, or use assets the place owns.

## Animating rigs without Humanoids

Sources:
- https://create.roblox.com/docs/reference/engine/classes/Motor6D.md
- https://create.roblox.com/docs/reference/engine/classes/AnimationController
- https://create.roblox.com/docs/reference/engine/classes/RunService

What the docs say:
- **When Transform applies.** Changes to `Motor6D.Transform` are batched "after RunService.PreSimulation,
  immediately before physics steps".
- **Animator overwrites it.** The Animator usually writes Transform every frame, between PreAnimation and
  PreSimulation.
- **No replication.** Transform is not replicated.
- **Non-humanoid rigs.** An AnimationController with an Animator child plays animations on models that have no
  Humanoid.

What we built:
- **Writing Transform.** `Summon.Animator` writes Transform from one shared `RunService.PreSimulation`
  connection. That runs after the Animator has written, so procedural motion wins, and it runs on clients only.
- **LOD.** Distance LOD uses `Config.Visual.SummonAnimLodNear`, `SummonAnimLodFar` and `SummonAnimCull` (120,
  260 and 600 studs): every frame when near, every 2nd frame when mid-range, every 6th frame when far, and paused
  past the cull distance.
- **Optional keyframes.** Each model also gets an AnimationController and Animator, so authored animations can
  still be layered on.
- **Bones.** Bones are invisible 0.05-stud parts chained by Motor6D. Visible parts are welded to their bone with a
  fixed `Weld.C0`.

## Highlight, Trail, ParticleEmitter, PointLight, CollisionGroup

Sources:
- https://create.roblox.com/docs/reference/engine/classes/Highlight
- https://create.roblox.com/docs/reference/engine/classes/Trail
- https://create.roblox.com/docs/reference/engine/classes/ParticleEmitter
- https://create.roblox.com/docs/workspace/collisions

What we built and why:
- **Highlight.** A client renders only about 31 Highlights at once, so we use one per Spectral summon and none
  for Solid summons. It can be turned off with `SummonSpectralHighlight`.
- **Trail.** Each trail uses two attachments across the longest axis of the part. There are at most
  `SummonMaxTrails` (4) per summon.
- **ParticleEmitter.** Emitters use the built-in textures (`rbxasset://textures/particles/*`), so nothing has to
  be uploaded. Limits:
  - `SummonEmitterBudget` (2 in Solid, 3 in Spectral);
  - `SummonMaxParticleRate` (60/s each);
  - `opts.budget.maxParticles` caps the total.
- **Looping accent and material effects.** These use the shared Effects library (`Effects.play(id, {target,
  style, element})`), which pools them and does distance culling. They are capped at `SummonEffectBudget` and
  stopped when the model is destroyed.
- **Collision.** Every visible part has CanCollide, CanTouch and CanQuery set to false and is Massless. The
  invisible Root keeps CanQuery for targeting. For collision groups, pass `opts.collisionGroup` or call
  `Instantiate.setCollisionGroupHook(fn)`.

## Z-fighting

There is no engine fix for z-fighting. Coplanar faces flicker. Our rule is that no two visible faces may coincide.

How we enforce it:
- **Checker (`Overlap.check`).** It finds:
  - coplanar polygons with an overlapping area above 1e-4 within 0.005 studs, on Block, Wedge and Cylinder caps;
  - coincident quadric shells (Ball, Ellipsoid);
  - coaxial Cylinder sides.
- **Fixer.** After the plan is scaled, the fixer nudges the less important part by `Config.Visual.Inset` (0.02),
  with a step that varies per pass so chains of thin plates settle.
- **Tests.** `tests/specs/summon_zfight.spec.luau` requires zero violations across:
  - all 60 body plans × 6 sizes × 2 styles × 50 seeds;
  - every signature;
  - 300 library entries;
  - 240 material, mood and accent phrases.

## Open uncertainties

- **CornerWedge orientation.** It is assumed and not used.
- **`LoadAsset` on the client for group-owned mesh assets.** This is untested in a live server.
- **Effects library ids.** Material particle ids that the Effects catalogue does not have (for example `flies`
  before it existed) fall back to `sparkle`. This is by design.
