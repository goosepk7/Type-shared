--!strict
-- Blueprint builder context. Plans and signatures describe geometry through this API in "design units"
-- (a Medium creature is ~5 units tall). Colours and materials are semantic KEYS ("primary", "skin", ...)
-- resolved later by Style, so one geometry serves both the Spectral and Solid looks.
--
-- Conventions: model faces -Z (Roblox LookVector), +Y up, +X is the summon's right. Feet rest on y = 0.
-- Mirrored helpers take a spec for the RIGHT side (+X) and add the left copy; "#" in names becomes R / L.

local Geom = require(script.Parent.Geom)
local Rng = require(script.Parent.Rng)

type Frame = Geom.Frame

export type PartSpec = {
	name: string?,
	shape: string, -- Block | Ball | Cylinder | Wedge | CornerWedge | Ellipsoid
	size: { number },
	cf: Frame,
	col: any?, -- colour key or {r,g,b}
	mat: string?, -- material key
	bone: string?,
	pri: number?, -- importance: 1 silhouette .. 5 fine detail (lower kept first under budget)
	pair: string?, -- parts sharing a pair id are kept or dropped together
	role: string?, -- "body","head","eye","pupil","shine","limb","wing","tail","spike","detail","core","shell","wheel","glow"
	tr: number?, -- transparency
	-- Sculpted look (docs/SUMMON.md "Sculpted meshes"). `mesh` is a piece id from Meshes/MeshAssets: Instantiate
	-- swaps the primitive for that MeshPart when the asset is loaded, placed in THIS part's box (Size + CFrame).
	-- false opts the part out of MeshMap's defaults. `meshL` is the piece for the mirrored (left) copy.
	-- `meshOf` names the lead part whose sculpt already contains this part (not built while that mesh shows).
	mesh: (string | boolean)?,
	meshL: string?,
	meshOf: any?,
	trail: boolean?, -- extremity: Spectral style may hang a Trail here
	glow: boolean?, -- emissive accent (Neon) in both styles
	noCore: boolean?, -- Spectral: never give this part an inner core
}

export type Part = PartSpec & { id: number }

export type Bone = { name: string, parent: string?, pos: { number } }

export type Builder = {
	parts: { Part },
	bones: { Bone },
	boneIndex: { [string]: Bone },
	rig: { [string]: any },
	sockets: { [string]: Frame },
	emitters: { any },
	lights: { any },
	rng: Rng.Rng,
	ctx: any,
	nextPair: number,
	[string]: any,
}

local Builder = {}
Builder.__index = Builder

function Builder.new(ctx: any, rng: Rng.Rng): Builder
	local self = setmetatable({
		parts = {},
		bones = {},
		boneIndex = {},
		rig = { legs = {}, arms = {}, wings = {}, tail = {}, spine = {}, wheels = {}, fins = {}, rotors = {}, sway = {}, orbit = {}, units = {} },
		sockets = {},
		emitters = {},
		lights = {},
		rng = rng,
		ctx = ctx,
		nextPair = 0,
	}, Builder)
	self:bone("Body", nil, 0, 0, 0)
	return self :: any
end

-- Joint pivot in model space (rotation is always identity so poses read as plain model-axis Euler angles).
function Builder.bone(self: Builder, name: string, parent: string?, x: number, y: number, z: number): string
	if self.boneIndex[name] then
		return name
	end
	if parent ~= nil and self.boneIndex[parent] == nil then
		parent = "Body"
	end
	local b = { name = name, parent = parent, pos = { x, y, z } }
	table.insert(self.bones, b)
	self.boneIndex[name] = b
	return name
end

-- Right-side bone plus its mirror. Name and parent may contain "#" (R / L).
function Builder.mirrorBone(self: Builder, name: string, parent: string?, x: number, y: number, z: number): (string, string)
	local r = self:bone((string.gsub(name, "#", "R")), parent and (string.gsub(parent, "#", "R")) or nil, x, y, z)
	local l = self:bone((string.gsub(name, "#", "L")), parent and (string.gsub(parent, "#", "L")) or nil, -x, y, z)
	return r, l
end

function Builder.newPair(self: Builder): string
	self.nextPair += 1
	return "p" .. self.nextPair
end

function Builder.part(self: Builder, spec: PartSpec): Part
	local p = spec :: any
	p.bone = p.bone or "Body"
	if self.boneIndex[p.bone] == nil then
		p.bone = "Body"
	end
	p.pri = p.pri or 2
	p.col = p.col or "primary"
	p.mat = p.mat or "skin"
	if p.shape == "Ball" then
		local d = math.min(p.size[1], p.size[2], p.size[3])
		p.size = { d, d, d }
	end
	p.id = #self.parts + 1
	p.name = p.name or (p.role or p.shape) .. p.id
	table.insert(self.parts, p)
	return p
end

-- Add the right-side spec and its mirror across x = 0. Returns (right, left).
function Builder.mirror(self: Builder, spec: PartSpec): (Part, Part)
	local pair = spec.pair or self:newPair()
	local r = table.clone(spec) :: any
	r.pair = pair
	r.name = spec.name and (string.gsub(spec.name, "#", "R")) or nil
	r.bone = spec.bone and (string.gsub(spec.bone, "#", "R")) or nil
	local l = table.clone(spec) :: any
	l.pair = pair
	l.name = spec.name and (string.gsub(spec.name, "#", "L")) or nil
	l.bone = spec.bone and (string.gsub(spec.bone, "#", "L")) or nil
	l.cf = Geom.mirrorX(spec.cf)
	l.size = table.clone(spec.size)
	l.mirrored = true
	if spec.meshL then
		l.mesh = spec.meshL
	end
	r.meshL, l.meshL = nil, nil
	return self:part(r), self:part(l)
end

-- Convenience shapes ---------------------------------------------------------------------------------------

function Builder.ell(self: Builder, sx: number, sy: number, sz: number, cf: Frame, o: { [string]: any }?): Part
	local s = table.clone(o or {}) :: any
	s.shape, s.size, s.cf = "Ellipsoid", { sx, sy, sz }, cf
	return self:part(s)
end

function Builder.block(self: Builder, sx: number, sy: number, sz: number, cf: Frame, o: { [string]: any }?): Part
	local s = table.clone(o or {}) :: any
	s.shape, s.size, s.cf = "Block", { sx, sy, sz }, cf
	return self:part(s)
end

function Builder.ball(self: Builder, d: number, cf: Frame, o: { [string]: any }?): Part
	local s = table.clone(o or {}) :: any
	s.shape, s.size, s.cf = "Ball", { d, d, d }, cf
	return self:part(s)
end

-- Cylinder along the frame's X axis.
function Builder.cyl(self: Builder, len: number, d: number, cf: Frame, o: { [string]: any }?): Part
	local s = table.clone(o or {}) :: any
	s.shape, s.size, s.cf = "Cylinder", { len, d, d }, cf
	return self:part(s)
end

function Builder.wedge(self: Builder, sx: number, sy: number, sz: number, cf: Frame, o: { [string]: any }?): Part
	local s = table.clone(o or {}) :: any
	s.shape, s.size, s.cf = "Wedge", { sx, sy, sz }, cf
	return self:part(s)
end

-- Elongated ellipsoid spanning a -> b (an organic tapered limb segment). `over` extends past both ends.
function Builder.limb(self: Builder, a: { number }, b: { number }, w: number, o: { [string]: any }?, over: number?): Part
	local f, len = Geom.between(a[1], a[2], a[3], b[1], b[2], b[3], "Y")
	local s = table.clone(o or {}) :: any
	local d = s.depth or w
	s.depth = nil
	s.shape, s.size, s.cf = "Ellipsoid", { w, len * (1 + (over or 0.18)), d }, f
	s.seg = "Y" -- local +Y runs from a to b (MeshMap picks tapered pieces by this)
	return self:part(s)
end

-- Cylinder spanning a -> b.
function Builder.rod(self: Builder, a: { number }, b: { number }, d: number, o: { [string]: any }?, over: number?): Part
	local f, len = Geom.between(a[1], a[2], a[3], b[1], b[2], b[3], "X")
	local s = table.clone(o or {}) :: any
	s.shape, s.size, s.cf = "Cylinder", { len + (over or 0), d, d }, f
	return self:part(s)
end

-- Block spanning a -> b (Y along the segment).
function Builder.beam(self: Builder, a: { number }, b: { number }, w: number, dpt: number, o: { [string]: any }?, over: number?): Part
	local f, len = Geom.between(a[1], a[2], a[3], b[1], b[2], b[3], "Y")
	local s = table.clone(o or {}) :: any
	s.shape, s.size, s.cf = "Block", { w, len + (over or 0), dpt }, f
	return self:part(s)
end

-- Mirrored variants of the helpers: pass the right-side frame.
function Builder.mell(self: Builder, sx: number, sy: number, sz: number, cf: Frame, o: { [string]: any }?): (Part, Part)
	local s = table.clone(o or {}) :: any
	s.shape, s.size, s.cf = "Ellipsoid", { sx, sy, sz }, cf
	return self:mirror(s)
end

function Builder.mblock(self: Builder, sx: number, sy: number, sz: number, cf: Frame, o: { [string]: any }?): (Part, Part)
	local s = table.clone(o or {}) :: any
	s.shape, s.size, s.cf = "Block", { sx, sy, sz }, cf
	return self:mirror(s)
end

function Builder.mball(self: Builder, d: number, cf: Frame, o: { [string]: any }?): (Part, Part)
	local s = table.clone(o or {}) :: any
	s.shape, s.size, s.cf = "Ball", { d, d, d }, cf
	return self:mirror(s)
end

function Builder.mcyl(self: Builder, len: number, d: number, cf: Frame, o: { [string]: any }?): (Part, Part)
	local s = table.clone(o or {}) :: any
	s.shape, s.size, s.cf = "Cylinder", { len, d, d }, cf
	return self:mirror(s)
end

function Builder.mwedge(self: Builder, sx: number, sy: number, sz: number, cf: Frame, o: { [string]: any }?): (Part, Part)
	local s = table.clone(o or {}) :: any
	s.shape, s.size, s.cf = "Wedge", { sx, sy, sz }, cf
	return self:mirror(s)
end

function Builder.mlimb(self: Builder, a: { number }, b: { number }, w: number, o: { [string]: any }?, over: number?): (Part, Part)
	local f, len = Geom.between(a[1], a[2], a[3], b[1], b[2], b[3], "Y")
	local s = table.clone(o or {}) :: any
	local d = s.depth or w
	s.depth = nil
	s.shape, s.size, s.cf = "Ellipsoid", { w, len * (1 + (over or 0.18)), d }, f
	s.seg = "Y"
	return self:mirror(s)
end

function Builder.mrod(self: Builder, a: { number }, b: { number }, d: number, o: { [string]: any }?): (Part, Part)
	local f, len = Geom.between(a[1], a[2], a[3], b[1], b[2], b[3], "X")
	local s = table.clone(o or {}) :: any
	s.shape, s.size, s.cf = "Cylinder", { len, d, d }, f
	return self:mirror(s)
end

function Builder.mbeam(self: Builder, a: { number }, b: { number }, w: number, dpt: number, o: { [string]: any }?): (Part, Part)
	local f, len = Geom.between(a[1], a[2], a[3], b[1], b[2], b[3], "Y")
	local s = table.clone(o or {}) :: any
	s.shape, s.size, s.cf = "Block", { w, len, dpt }, f
	return self:mirror(s)
end

-- Sculpt group: `lead` shows mesh piece `pieceId` (placed in the lead's own box, so it follows the lead through
-- scaling, the z-fighting fixer and animation) and `members` are primitives the sculpt already contains: they
-- stay in the blueprint as the fallback and are skipped by Instantiate while the lead's mesh shows.
function Builder.sculpt(self: Builder, lead: Part, pieceId: string, members: { Part }?): Part
	local l = lead :: any
	l.mesh = pieceId
	for _, m in members or {} do
		if m ~= lead then
			(m :: any).meshOf = lead
		end
	end
	return lead
end

-- Rig metadata for the animator ----------------------------------------------------------------------------

function Builder.addRig(self: Builder, list: string, entry: any)
	local l = self.rig[list]
	if l == nil then
		l = {}
		self.rig[list] = l
	end
	table.insert(l, entry)
end

function Builder.setRig(self: Builder, key: string, value: any)
	self.rig[key] = value
end

-- A named socket (model-space frame) for effects: "mouth", "hand", "muzzle", "core".
function Builder.socket(self: Builder, name: string, cf: Frame, bone: string?)
	self.sockets[name] = cf
	self.rig.socketBones = self.rig.socketBones or {}
	self.rig.socketBones[name] = bone or "Body"
end

-- Emitter request (Style decides whether it survives the budget and what it looks like).
function Builder.emit(self: Builder, preset: string, partName: string?, o: { [string]: any }?)
	local e = (o or {}) :: any
	e.preset = preset
	e.part = partName
	table.insert(self.emitters, e)
end

return Builder
