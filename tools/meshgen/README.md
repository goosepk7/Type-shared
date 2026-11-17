# meshgen: sculpted mesh pieces

Shared toolkit (ported from Type-defend `tools/meshgen`, same function signatures) that sculpts mesh pieces in
Python, exports them as `.glb`, uploads them to the group as Model assets and records the ids. The runtime side is
`src/Shared/Meshes/MeshLibrary.luau` + the generated `src/Shared/Meshes/MeshAssets.luau`.

```
python3 tools/meshgen/build.py [--only a,b] [--jobs n] [--no-ao]   # catalogue -> out/*.glb + out/manifest.json
python3 tools/meshgen/preview.py sheet.png [--only a,b] [--set summon] [--match text] [--views 2]
python3 tools/meshgen/upload.py [--dry] [--only a,b] [--max n]      # new / changed pieces only (hash keyed)
python3 tools/meshgen/upload.py --sync                              # rewrite MeshAssets.luau from the JSON
python3 tools/meshgen/upload.py --import <other MeshAssets.json>    # adopt records of identical pieces
lune run tools/meshgen/export_refs                                  # refs.json: reference blueprints for sculptors
```

`out/` is git-ignored (rebuild is deterministic: the 134 Type-defend pieces rebuild byte-identical, which is how
their asset ids were adopted without a second upload). Every upload is appended to `uploads.log`
(time, piece, asset id, hash, triangles). `data/mesh_assets.json` is the source of truth; `MeshAssets.luau` is
generated from it so nothing decodes JSON at runtime.

## Pipeline

SDF (numpy, `sdf.py`) -> marching cubes -> Taubin smoothing -> quadric decimation to the piece's triangle budget
-> normals from the SDF gradient -> ambient occlusion baked into greyscale `COLOR_0` -> `.glb`, pre-rotated 180
degrees about Y because the Roblox importer rotates it back. 1 glTF unit = 1 stud. Vertex colour multiplies
`MeshPart.Color`, so one piece takes any palette colour and material. `InsertService:LoadAsset` returns
Model > Model > MeshPart for group-owned assets.

Hard-surface and thin pieces skip the SDF: `direct.py` builds exact low-poly geometry with authored normals
(`rounded_box`, `lathe`, `bevel_cylinder`, `revolve`, `blade`, `deform`, `merge`, `moved`). A catalogue function
may return an SDF or a `direct` mesh.

## Catalogue

`catalogue/__init__.py`: `piece(id, region, tris=1200, fit=None, kind=None, note="", res=120, smooth=6,
pivot="center", mirror=False, set=None)`. `mirror` and `set` are additions to the Type-defend signature:
`mirror=True` also emits the x-mirrored twin `<id>_l`; `set` is filled in by the loader ("td": body, features,
face; "summon": s_organic, s_heads, s_hard, s_hero).

`lead=(sx, sy, sz)` (third addition, unit pieces only): the sculpt is authored in the lead primitive's local
frame in studs, at the reference lead size, so its normals keep true proportions; the manifest size / origin are
divided by `lead`. `catalogue/refs.py` (`Group.local`, `Group.region_local`) converts a model-space sculpt.
Hero sets: `s_dragon.py` (full and compact dragon), `s_trex.py`, `s_canine.py` (wolf), `s_fx.py` (shark, tornado,
asteroid, blaze, accretion disc, `s_noodle_wrap` material wrap).
Round 4 sets: `s_knight.py` (also the shared helpers `_def`, `_ext`), `s_wizard.py`, `s_golem.py`, `s_robot.py`,
`s_horse.py` (horse family, unicorn), `s_octo.py` (kraken, octopus; pieces authored in the lead's local frame),
and the directly built hard-surface sets `s_castle.py` (helpers `cube`, `local`, `_unit`), `s_ship.py` (SDF hull,
direct stern castle and sail sheets), `s_tank.py` (`prism`, `drum`), `s_wing.py` (feather leaves; ids listed in
`catalogue.NO_AO` skip the ambient occlusion bake). `export_refs.luau` takes key arguments and writes only those
reference blueprints (`"sig:kraken"`, `"eagle@1"`); a full re-export would move every existing sculpt.

`upload.py --adopt <MeshAssets.json> ...` takes another repository's record (asset id, size, origin, tris, hash) for
every piece id both manifests list, marks it `"source": "adopted"` and never uploads that id from the local build
again (the local glb of a "td" piece is our higher-triangle build and is only used by the offline renderer). The
uploader takes a lock file: two overlapping runs once uploaded 22 pieces twice (`uploads_orphans.tsv` lists the
unreferenced duplicates).

`export_refs.luau` with arguments re-exports only those keys (`lune run tools/meshgen/export_refs "sig:dragon@1"`)
and keeps every other entry of `refs.json`: a full re-export moves each existing sculpt by whatever the generators
changed since, so do it on purpose only. `sig:dragon@1` / `@0` are the low-detail dragon layouts
(`Summon.blueprint(..., { detail = n })`, a tooling option).

Kinds:

| kind | authored in | placed by |
| --- | --- | --- |
| `box` | any units; the mesh is fitted to `fit` | `MeshLibrary.get/fit`: MeshPart.Size = the part's Size |
| `anchor` | anchor units (head radius ...); native size + origin recorded | `MeshLibrary.place(id, frame, scale)` |
| `unit` (new) | the unit frame of the primitive it replaces (its box is [-0.5, 0.5]^3) | `MeshLibrary.fit`: Size = native * part Size, CFrame = part CFrame * (origin * part Size) |

The manifest also records `set` and `flat` (the box faces a piece touches with a planar face, from
`mesher.flat_faces`), used by the z-fighting notes in docs/SUMMON.md.

## Summon piece frames

A summon piece stands in for one primitive of the builder and uses that primitive's frame:

* Ellipsoid / Ball / Block: the part's box, +Y up, -Z front for upright parts.
* Limb segments (`Builder.limb`, `seg = "Y"`): +Y runs from the thick root end to the thin end.
* Cylinder: axis X. Wedge: fills the WedgePart triangle.
* Asymmetric pieces have a `_l` twin for the mirrored copy (`MeshMap.Left`).
* Head and body sculpts are `unit` pieces: the lead ellipsoid is the unit sphere and stays untouched where the
  builder puts eyes and mouths; snout, chest and haunch primitives are modelled in at the positions the generator
  gives them (measured in `refs.json`), and those primitives are listed as the sculpt's members (`B:sculpt`).

Budgets (phone): bevel blocks and cylinders 240-320 triangles, small bits (teeth, claws, feathers) 140-300,
limbs and tails about 300, hero hard-surface pieces 250-700, heads 600-1300, bodies 1000-1500.

## Runtime API (`src/Shared/Meshes/MeshLibrary.luau`)

Same as the Type-defend module: `register, clear, setDisabled, has, info, get, place, ready, start`.
Additions: `fit(pieceId, size, cframe, color?, material?)`, `preload(filter?)` (never yields), `start(filter?)`,
`record(pieceId)`, `addAssets(records)`, `live()`, `setRuntime(rt)` (Lune tests), `FolderName`; `place` accepts a
Vector3 scale; `info()` includes `kind`. The manifest is the sibling module `MeshAssets` (not a JSON string).
