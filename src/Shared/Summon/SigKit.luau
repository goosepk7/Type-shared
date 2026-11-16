--!strict
-- Shared helpers for hand-built signatures (Signatures/*). Not a child of Signatures, so the registry never
-- mistakes these helpers for signature builders.
--
-- A signature starts from a tuned generic body (base: plan generator with forced kind/traits/proportions) and then
-- adds the hero details that make the word iconic, placed on anchors measured from what was built (eyes, head
-- top, mouth, body bounds). Everything goes through Builder, so budget, styles, materials, accents and the
-- z-fighting fixer apply exactly as for plans.

local Geom = require(script.Parent.Geom)
local Accents = require(script.Parent.Accents)

local Kit = {}
Kit.at = Geom.at
Kit.rad = math.rad

local plansMod: any = nil
local function plans(): any
	if plansMod == nil then
		plansMod = require(script.Parent.Plans) :: any
	end
	return plansMod
end

-- Build the generic body for `plan` with forced traits and kind; returns anchors.
function Kit.base(B: any, ctx: any, plan: string, kind: string?, traits: { [string]: any }?): any
	for k, v in traits or {} do
		ctx.traits[k] = v
	end
	ctx.kind = kind
	local gen = plans()[plan]
	gen(B, ctx)
	return Accents._anchors(B)
end

function Kit.anchors(B: any): any
	return Accents._anchors(B)
end

function Kit.find(B: any, name: string): any
	for _, p in B.parts do
		if p.name == name then
			return p
		end
	end
	return nil
end

function Kit.findRole(B: any, role: string): { any }
	local out = {}
	for _, p in B.parts do
		if p.role == role then
			table.insert(out, p)
		end
	end
	return out
end

-- Scale every part and bone about the origin (proportion tweaks after a base build).
function Kit.scaleParts(B: any, names: { [string]: boolean }?, k: number)
	for _, p in B.parts do
		if names == nil or names[p.name] then
			p.size = { p.size[1] * k, p.size[2] * k, p.size[3] * k }
		end
	end
end

return Kit
