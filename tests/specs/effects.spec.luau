-- Effects: pure modules (palettes, curves, pools, budgets, auto-degrade, catalogue, presets, assets) plus a
-- runtime smoke test that renders EVERY catalogue id in both styles against @lune/roblox Instances, checks
-- that nothing warns/errors/leaks, and runs a coplanar-face (z-fighting) checker on every visible part.
local fs = require("@lune/fs")
local serde = require("@lune/serde")
local roblox = require("@lune/roblox")

-- Faces closer than this along their normal with overlapping area are treated as z-fighting.
local PLANE_EPS = 0.002
local OVERLAP_MARGIN = 0.01

return function(t)
	-- Pure modules first (no Roblox globals needed) ------------------------------------------------------------
	local Palettes = t.load("src/Shared/Effects/Palettes")
	local Curves = t.load("src/Shared/Effects/Curves")
	local Pool = t.load("src/Shared/Effects/Pool")
	local Presets = t.load("src/Shared/Effects/Presets")
	local Assets = t.load("src/Shared/Effects/Assets")
	local Config = t.load("src/Shared/Config")
	local ECFG = Config.Visual.Effects
	local ELEMENTS = { "Fire", "Water", "Ice", "Lightning", "Earth", "Wind", "Nature", "Light", "Shadow", "Poison", "Metal", "Arcane", "None" }

	t.test("palettes: 5-stop hex ramps for every element in both styles, overrides and normalisation", function()
		for _, style in { "Spectral", "Solid" } do
			for _, e in ELEMENTS do
				local r = Palettes.ramp(e, style)
				t.eq(#r, 5, e .. " " .. style)
				for _, hex in r do
					t.ok(string.match(hex, "^#%x%x%x%x%x%x$") ~= nil, e .. " bad hex " .. tostring(hex))
				end
				t.ok(type(Palettes.elementFx(e).primary) == "string", e .. " elementFx")
			end
		end
		t.eq(Palettes.normalize("Nope"), "None")
		t.eq(Palettes.resolve("Fire", "Solid", "#FF0000")[3] ~= nil, true)
		local r, g, b = Palettes.toRGB("#FF8000")
		t.eq(Palettes.toHex(r, g, b), "#FF8000")
		t.eq(Palettes.lerp("#000000", "#FFFFFF", 0), "#000000")
	end)

	t.test("curves: easings hit their endpoints, envelope/flash stay in [0,1]", function()
		for _, name in { "linear", "inQuad", "outQuad", "outCubic", "inCubic", "outQuint", "outExpo", "inOutSine", "inOutCubic", "outBack", "outElastic" } do
			t.ok(math.abs(Curves[name](0)) < 1e-6, name .. "(0)")
			t.ok(math.abs(Curves[name](1) - 1) < 1e-6, name .. "(1)")
		end
		for i = 0, 40 do
			local x = i / 10
			local e = Curves.envelope(x, 4, 0.5, 1)
			t.ok(e >= 0 and e <= 1, "envelope " .. x)
			local f = Curves.flash(x / 4)
			t.ok(f >= 0 and f <= 1.0001, "flash " .. x)
		end
		-- golden-angle disc points stay inside the unit disc
		for i = 1, 30 do
			local x, y = Curves.disc(i, 30)
			t.ok(x * x + y * y <= 1.0001, "disc " .. i)
		end
	end)

	t.test("pool: acquire/release/reuse, double release ignored, maxIdle trims", function()
		local made, destroyed = 0, 0
		local p = Pool.new("x", function()
			made += 1
			return { n = made }
		end, nil, function()
			destroyed += 1
		end, 2)
		local a, b, c = p:acquire(), p:acquire(), p:acquire()
		t.eq(p:stats().inUse, 3)
		t.ok(p:release(a))
		t.ok(not p:release(a), "double release must return false")
		t.ok(not p:release({}), "foreign object must return false")
		p:release(b)
		p:release(c)
		t.eq(p:stats().inUse, 0)
		t.ok(p:stats().free <= 2, "maxIdle")
		t.eq(destroyed, 1)
		local d = p:acquire()
		t.ok(d == a or d == b or d == c, "reuses a parked object")
		t.eq(made, 3)
	end)

	t.test("budget: admits within limits, refuses over, thins particles near full, priorities", function()
		local b = Pool.budget(ECFG, "Low")
		local ok, scale = b:admit({ parts = 10 }, 1)
		t.ok(ok and scale == 1)
		for _ = 1, ECFG.Budgets.Low.maxEffects do
			b:commit({ parts = 1 })
		end
		t.ok(not (b:admit({ parts = 1 }, 1)), "over maxEffects refused")
		t.ok((b:admit({ parts = 1 }, 2)), "local player may overflow")
		local b2 = Pool.budget(ECFG, "Medium")
		b2:commit({ parts = ECFG.Budgets.Medium.maxParts - 5 })
		local ok2, s2 = b2:admit({ parts = 4 }, 1)
		t.ok(ok2 and s2 < 1 and s2 >= 0.4, "thinning " .. tostring(s2))
		t.ok(not (b2:admit({ parts = 10 }, 1)), "parts limit")
		t.ok((b2:admit({ lights = 999, highlights = 999 }, 1)), "lights/highlights never block")
		b2:refund({ parts = ECFG.Budgets.Medium.maxParts - 5 })
		t.eq(b2.usage.parts, 0)
		-- ambient effects are refused earlier than normal ones
		local b3 = Pool.budget(ECFG, "Low")
		for _ = 1, math.ceil(ECFG.Budgets.Low.maxEffects * ECFG.LowPriorityCutoff) do
			b3:commit({})
		end
		t.ok(not (b3:admit({}, 0)), "ambient refused at cutoff")
		t.ok((b3:admit({}, 1)), "normal still admitted")
		-- tiers are ordered: every limit grows from Low to Ultra
		for _, k in { "maxEffects", "maxParts", "maxEmitters", "maxBeams", "maxTrails", "maxLights" } do
			local prev = -1
			for _, tier in ECFG.TierOrder do
				t.ok(ECFG.Budgets[tier][k] >= prev, k .. " " .. tier)
				prev = ECFG.Budgets[tier][k]
			end
		end
	end)

	t.test("quality: device tiers, saved graphics level, FPS auto-degrade with hysteresis", function()
		t.eq(Pool.pickTier(ECFG, "Desktop", 0), ECFG.DeviceTier.Desktop)
		t.eq(Pool.pickTier(ECFG, "Phone", 0), ECFG.DeviceTier.Phone)
		t.eq(Pool.pickTier(ECFG, "Desktop", 2), "Low")
		t.eq(Pool.pickTier(ECFG, "Desktop", 10), "Ultra")
		local d = Pool.degrader(ECFG, "High")
		for _ = 1, 600 do
			d:step(1 / 60)
		end
		t.eq(d.tier, "High", "steady 60fps keeps tier")
		local changed = nil
		for _ = 1, 30 * 20 do
			changed = d:step(1 / 20) or changed
		end
		t.ok(d.tier == "Medium" or d.tier == "Low", "20fps degrades, got " .. d.tier)
		for _ = 1, 60 * 120 do
			d:step(1 / 60)
		end
		t.eq(d.tier, "High", "recovers up to the ceiling, never above")
		local slot = Pool.slots(3)
		t.eq(slot(), 1)
		t.eq(slot(), 2)
		t.eq(slot(), 3)
		t.eq(slot(), 1)
	end)

	t.test("presets: every texture exists in Assets, within engine caps", function()
		for tex in Presets.textures() do
			t.ok(Assets.has(tex), "preset texture missing from Assets: " .. tex)
		end
		for name, p in Presets.List do
			t.ok(type(p.tex) == "string", name .. " tex")
			if p.life then
				t.ok(p.life[2] <= 20 and p.life[1] <= p.life[2], name .. " life")
			end
			if p.fps then
				t.ok(p.fps[2] <= 30, name .. " fps above engine cap")
			end
			t.ok((p.rate or 0) <= 100, name .. " rate above mobile per-emitter cap")
		end
		-- every texture file referenced by Assets exists on disk
		for name, info in Assets.Textures do
			t.ok(fs.isFile("assets/textures/" .. info.file .. ".png"), "missing PNG for " .. name)
			local id = Assets.texture(name, true)
			t.ok(type(id) == "string", name)
		end
	end)

	-- Runtime: inject Roblox globals for the Effects modules only ----------------------------------------------
	local genv = getfenv(t.load)
	local injected = {}
	local function inject(k, v)
		if genv[k] == nil then
			injected[k] = true
			genv[k] = v
		end
	end
	for k, v in roblox do
		if type(k) == "string" and string.match(k, "^%u") then
			inject(k, v)
		end
	end
	local warnings = {}
	inject("task", require("@lune/task"))
	genv.warn = function(...)
		local parts = {}
		for i = 1, select("#", ...) do
			parts[i] = tostring((select(i, ...)))
		end
		table.insert(warnings, table.concat(parts, " "))
	end
	injected.warn = true

	-- methods @lune/roblox does not implement
	roblox.implementMethod("ParticleEmitter", "Emit", function() end)
	roblox.implementMethod("ParticleEmitter", "Clear", function() end)
	roblox.implementMethod("Trail", "Clear", function() end)
	local function modelParts(m)
		local out = {}
		for _, d in m:GetDescendants() do
			if d:IsA("BasePart") then
				table.insert(out, d)
			end
		end
		return out
	end
	roblox.implementMethod("Model", "GetPivot", function(m)
		local pp = m.PrimaryPart or modelParts(m)[1]
		return if pp then pp.CFrame else roblox.CFrame.new()
	end)
	roblox.implementMethod("Model", "GetBoundingBox", function(m)
		local lo, hi = nil, nil
		for _, p in modelParts(m) do
			local h = p.Size / 2
			local c = p.CFrame.Position
			lo = if lo then lo:Min(c - h) else c - h
			hi = if hi then hi:Max(c + h) else c + h
		end
		if not lo then
			return roblox.CFrame.new(), roblox.Vector3.new(0, 0, 0)
		end
		return roblox.CFrame.new((lo + hi) / 2), hi - lo
	end)

	local V3, CF = roblox.Vector3, roblox.CFrame
	local Effects = t.load("src/Shared/Effects")
	local Catalogue = Effects.Catalogue
	local Runtime = t.load("src/Shared/Effects/Runtime")

	local ws = roblox.Instance.new("Model")
	ws.Name = "Workspace"
	local container = roblox.Instance.new("Folder")
	container.Name = "WordEngineFX"
	container.Parent = ws
	local attachRoot = roblox.Instance.new("Part")
	attachRoot.Name = "AttachRoot"
	attachRoot.Transparency = 1
	attachRoot.Parent = ws

	-- target: a small 2-part character standing on the ground (y = 0)
	local target = roblox.Instance.new("Model")
	target.Name = "Dummy"
	local root = roblox.Instance.new("Part")
	root.Name = "HumanoidRootPart"
	root.Size = V3.new(2, 2, 1)
	root.CFrame = CF.new(6, 3, 4)
	root.Transparency = 1
	root.Parent = target
	local body = roblox.Instance.new("Part")
	body.Name = "Torso"
	body.Size = V3.new(2, 4, 1.2)
	body.CFrame = CF.new(6, 2, 4)
	body.Parent = target
	target.PrimaryPart = root
	target.Parent = ws

	Effects.init({
		workspace = ws,
		container = container,
		attachRoot = attachRoot,
		camera = V3.new(0, 20, -40),
		raycast = function(pos)
			return V3.new(pos.X, 0, pos.Z), V3.new(0, 1, 0)
		end,
		deviceClass = "Desktop",
		noConnect = true,
	})
	Effects.setQuality("Ultra")

	local function kindSet()
		local s = {}
		for _, k in Effects.Kinds do
			s[k] = fs.isFile("src/Shared/Effects/Kinds/" .. k .. ".luau")
		end
		return s
	end

	t.test("catalogue: validates, every kind has a renderer, every reaction has a vfx", function()
		local errs = Catalogue.validate(kindSet())
		t.ok(#errs == 0, table.concat(errs, "\n"))
		local R = t.load("src/Shared/Reactions")
		for _, r in R.all() do
			t.ok(Catalogue.has(r.vfx), r.id .. " vfx " .. r.vfx)
		end
		for _, s in R.Statuses do
			t.ok(Catalogue.has(Catalogue.statusId(s)), "status visual " .. s)
		end
		for _, k in R.materialOutcomes() do
			t.ok(Catalogue.has(R.materialOutcome(k).vfx), "material outcome vfx " .. k)
		end
		for _, fam in { "projectile.meteor", "beam.lightning", "impact.fire", "explosion.small", "explosion.medium", "explosion.huge", "aura.element", "shield.bubble", "wall.stone", "cloud.storm", "rain.local", "wave.water", "zone.tornado", "zone.vortex", "zone.blizzard", "zone.wildfire", "weather.rain", "spawn.materialize", "spawn.dissolve" } do
			t.ok(Catalogue.has(fam), "missing " .. fam)
		end
	end)

	t.test("catalogue: stable material/mood particle ids (summon builder + data/materials.json)", function()
		for _, id in { "anger_steam", "snore", "sweat_drops", "thruster", "glitch", "stars", "question_marks", "hearts", "music_notes", "drip_sauce", "sawdust", "sparkle", "bees", "crumbs", "goo_drip", "shards", "steam", "confetti", "smoke" } do
			t.ok(Catalogue.has(id), "stable id " .. id)
		end
		if fs.isFile("data/materials.json") then
			local raw = serde.decode("json", fs.readFile("data/materials.json"))
			for _, m in (raw.materials or raw) do
				for _, id in m.particles or {} do
					t.ok(Catalogue.has(id), tostring(m.id) .. " particle " .. id)
				end
			end
		end
	end)

	-- Z-fighting checker -----------------------------------------------------------------------------------
	local function visible(p): boolean
		-- @lune/roblox has no default for LocalTransparencyModifier until something sets it
		local ok, ltm = pcall(function()
			return p.LocalTransparencyModifier
		end)
		return p.Parent ~= nil and p.CFrame.Position.Y > -1000 and p.Transparency < 0.98 and (not ok or ltm < 0.98)
	end

	-- Planar faces of a part: { n, c, kind = "rect"|"circle", u, v, hu, hv | r }
	local function faces(p, out)
		local cf, s = p.CFrame, p.Size
		local decal = p:FindFirstChildOfClass("Decal")
		local mesh = p:FindFirstChildOfClass("SpecialMesh")
		local shape = p.Shape
		if decal then
			if decal.Transparency < 0.98 and decal.Texture ~= "" and p.CFrame.Position.Y > -1000 then
				table.insert(out, { p = p, n = cf.UpVector, c = cf.Position + cf.UpVector * s.Y / 2, kind = "rect", u = cf.RightVector, v = cf.LookVector, hu = s.X / 2, hv = s.Z / 2 })
			end
			return
		end
		if not visible(p) or mesh then
			return
		end
		if shape == Enum.PartType.Block then
			local axes = { { cf.RightVector, s.X, cf.UpVector, s.Y, cf.LookVector, s.Z }, { cf.UpVector, s.Y, cf.RightVector, s.X, cf.LookVector, s.Z }, { cf.LookVector, s.Z, cf.RightVector, s.X, cf.UpVector, s.Y } }
			for _, a in axes do
				for _, sign in { 1, -1 } do
					table.insert(out, { p = p, n = a[1] * sign, c = cf.Position + a[1] * sign * a[2] / 2, kind = "rect", u = a[3], v = a[5], hu = a[4] / 2, hv = a[6] / 2 })
				end
			end
		elseif shape == Enum.PartType.Cylinder then
			for _, sign in { 1, -1 } do
				table.insert(out, { p = p, n = cf.RightVector * sign, c = cf.Position + cf.RightVector * sign * s.X / 2, kind = "circle", r = math.min(s.Y, s.Z) / 2 })
			end
		end
	end

	local function radiusAlong(f, axis): number
		if f.kind == "circle" then
			return f.r
		end
		return f.hu * math.abs(f.u:Dot(axis)) + f.hv * math.abs(f.v:Dot(axis))
	end

	local function overlaps(a, b): boolean
		local d = b.c - a.c
		if a.kind == "circle" and b.kind == "circle" then
			return d.Magnitude < a.r + b.r - OVERLAP_MARGIN
		end
		local axes = {}
		for _, f in { a, b } do
			if f.kind == "rect" then
				table.insert(axes, f.u)
				table.insert(axes, f.v)
			end
		end
		for _, ax in axes do
			if math.abs(d:Dot(ax)) >= radiusAlong(a, ax) + radiusAlong(b, ax) - OVERLAP_MARGIN then
				return false
			end
		end
		return true
	end

	local function zfight(parts): { string }
		local fs_, balls, bad = {}, {}, {}
		for _, p in parts do
			if p:IsA("BasePart") then
				faces(p, fs_)
				if visible(p) and (p.Shape == Enum.PartType.Ball or p:FindFirstChildOfClass("SpecialMesh")) then
					table.insert(balls, p)
				end
			end
		end
		for _, f in fs_ do
			if f.n.Y > 0.9999 and math.abs(f.c.Y) < PLANE_EPS then
				table.insert(bad, f.p.Name .. " top face on the ground plane at y=" .. f.c.Y)
			end
		end
		for i = 1, #fs_ do
			local a = fs_[i]
			for j = i + 1, #fs_ do
				local b = fs_[j]
				if a.p ~= b.p and a.n:Dot(b.n) > 0.9999 and math.abs(a.n:Dot(b.c - a.c)) < PLANE_EPS and overlaps(a, b) then
					table.insert(bad, string.format("coplanar faces (%s, %s) at %s", a.p.Material.Name, b.p.Material.Name, tostring(a.c)))
				end
			end
		end
		for i = 1, #balls do
			for j = i + 1, #balls do
				local a, b = balls[i], balls[j]
				if (a.CFrame.Position - b.CFrame.Position).Magnitude < 1e-3 and (a.Size - b.Size).Magnitude < 1e-3 then
					table.insert(bad, "coincident spheres at " .. tostring(a.CFrame.Position))
				end
			end
		end
		return bad
	end

	t.test("z-fight checker catches coplanar faces (self-test)", function()
		local scratch = roblox.Instance.new("Folder")
		local a = roblox.Instance.new("Part")
		a.Parent = scratch
		a.Size = V3.new(4, 1, 4)
		a.CFrame = CF.new(0, 2, 0)
		local b = roblox.Instance.new("Part")
		b.Parent = scratch
		b.Size = V3.new(2, 1, 2)
		b.CFrame = CF.new(1, 2, 1)
		t.ok(#zfight({ a, b }) > 0, "same top plane must be flagged")
		b.CFrame = CF.new(0.5, 2.05, 0.5)
		t.eq(#zfight({ a, b }), 0, "offset faces are fine")
		local g = roblox.Instance.new("Part")
		g.Parent = scratch
		g.Size = V3.new(2, 1, 2)
		g.CFrame = CF.new(0, -0.5, 0)
		t.ok(#zfight({ g }) > 0, "top face on the ground plane must be flagged")
	end)

	local function idle(): boolean
		return Runtime.activeCount() == 0 and Runtime.coolingCount() == 0
	end

	local function leaks(): { string }
		local out = {}
		for name, st in Runtime.poolStats() do
			if st.inUse ~= 0 then
				table.insert(out, name .. " inUse=" .. st.inUse)
			end
		end
		local b = Runtime.budget()
		if b.effects ~= 0 then
			table.insert(out, "budget.effects=" .. b.effects)
		end
		for k, v in b.usage do
			if v ~= 0 then
				table.insert(out, "budget." .. k .. "=" .. v)
			end
		end
		return out
	end

	local function paramsFor(id, style)
		return {
			style = style,
			at = CF.new(0, 0, 0),
			from = V3.new(-14, 5, -10),
			to = V3.new(10, 0, 8),
			target = target,
			points = { V3.new(0, 3, 0), V3.new(5, 3, 3), V3.new(9, 3, -2) },
			targets = { target },
			seed = 7,
			priority = 2,
		}
	end

	local seenParts = 0
	-- Render every id in both styles: no warnings, no errors, z-fight free at sampled times, no leaks.
	for _, style in { "Spectral", "Solid" } do
		t.test("runtime: every catalogue id renders cleanly in " .. style .. " (no errors, leaks or z-fighting)", function()
			local problems = {}
			local ids = Catalogue.ids()
			seenParts = 0
			for _, id in ids do
				table.clear(warnings)
				local entry = Catalogue.get(id)
				local h = Effects.play(id, paramsFor(id, style))
				if not h._fx then
					table.insert(problems, id .. ": inert handle")
				end
				local tt, stopAt = 0, (if entry.loop or not entry.duration then 2.5 else math.huge)
				local zf = nil
				local dt = 1 / 30
				local steps = 0
				while not idle() and tt < 60 do
					Effects.step(dt)
					tt += dt
					steps += 1
					if zf == nil and steps % 4 == 1 and steps <= 120 then
						local descendants = container:GetDescendants()
						for _, d in descendants do
							if d:IsA("BasePart") and visible(d) then
								seenParts += 1
							end
						end
						local bad = zfight(descendants)
						if #bad > 0 then
							zf = bad[1] .. " (+" .. (#bad - 1) .. ")"
						end
					end
					if tt >= stopAt and h:isPlaying() then
						h:stop()
					end
					if Runtime.activeCount() == 0 then
						dt = 0.5 -- just flushing cooling emitters/trails
					end
				end
				if zf then
					table.insert(problems, id .. ": " .. zf)
				end
				if not idle() then
					table.insert(problems, id .. ": never finished")
				end
				if #warnings > 0 then
					table.insert(problems, id .. ": " .. warnings[1])
				end
				local lk = leaks()
				if #lk > 0 then
					table.insert(problems, id .. ": leak " .. table.concat(lk, ", "))
					Effects.clear()
				end
				if #problems >= 12 then
					break
				end
			end
			t.ok(#problems == 0, #problems .. " problems:\n  " .. table.concat(problems, "\n  "))
			print(("  [effects] %s: %d ids rendered, %d visible part samples checked for z-fighting"):format(style, #ids, seenParts))
			t.ok(seenParts > #ids, "sweep must actually render parts (" .. seenParts .. ")")
		end)
	end

	t.test("runtime: overlapping ground layers from concurrent effects never share a plane", function()
		table.clear(warnings)
		local hs = {}
		for _, id in { "explosion.medium", "explosion.medium", "shield.dome", "shield.dome", "impact.fire", "zone.runes", "burst.frost", "explosion.small", "zone.pool", "impact.earth" } do
			table.insert(hs, Effects.play(id, { at = CF.new(0, 0, 0), style = "Solid", priority = 2, seed = #hs }))
		end
		for _ = 1, 12 do
			Effects.step(1 / 30)
		end
		local bad = zfight(container:GetDescendants())
		t.ok(#bad == 0, table.concat(bad, "\n"))
		Effects.clear()
		t.eq(#warnings, 0, warnings[1])
	end)

	t.test("api: status refresh/cap, reaction by id, serialize round trip, unknown ids fall back", function()
		table.clear(warnings)
		local h1 = Effects.status(target, "Burn", 2)
		local h2 = Effects.status(target, "Burn", 5)
		t.ok(h1 == h2, "re-applying refreshes instead of stacking")
		local hs = { h1 }
		for _, s in { "Freeze", "Shock", "Poison", "Slow", "Stun" } do
			table.insert(hs, Effects.status(target, s, 3))
		end
		local live = 0
		for _, h in hs do
			if h:isPlaying() then
				live += 1
			end
		end
		t.ok(live <= ECFG.MaxStatusesPerTarget, "status cap " .. live)
		Effects.clearStatus(target)
		local r = Effects.reaction("Steam", { at = CF.new(0, 0, 0) })
		t.ok(r:isPlaying())
		local msg = Effects.serialize("impact.fire", { at = V3.new(1, 0, 1), f = function() end })
		t.eq(msg.f, nil)
		local h3 = Effects.playSerialized(msg)
		t.ok(h3:isPlaying())
		local h4 = Effects.play("totally.unknown", { at = CF.new() })
		t.ok(h4 ~= nil and #warnings == 1, "unknown id warns once and falls back")
		Effects.clear()
		for _ = 1, 50 do
			Effects.step(0.5)
		end
		t.eq(#leaks(), 0, table.concat(leaks(), ", "))
	end)

	-- restore the shared loader environment for later specs
	for k in injected do
		genv[k] = nil
	end
end
