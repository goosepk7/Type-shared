--!strict
-- Signature registry: hand-built blueprints for iconic words. Lookup order: result.id, synonymGroup, then the
-- last word of the id ("ice dragon" -> "dragon", recoloured by the result's own colours/element).

local Signatures = {}

local registry: { [string]: (any, any) -> () } = {}
local plans: { [string]: string } = {}

-- plan: the body plan this signature represents. Suffix matches ("ice dragon" -> "dragon") only apply when the
-- word's own body plan agrees, so "hot dog" (Food/Blob) never becomes a dog.
function Signatures.register(id: string, fn: (any, any) -> (), plan: string?)
	registry[string.lower(id)] = fn
	if plan then
		plans[string.lower(id)] = plan
	end
end

-- Optional uploaded-mesh backing for a signature (Open Cloud Model asset, loaded with InsertService:LoadAsset).
-- mesh = { assetId: number, scale: number?, offset: {x,y,z}?, keepRoles: {string}? }. The procedural blueprint is
-- always built first and stays as the fallback until the asset loads; faces, accents, materials and effects are
-- procedural parts and keep showing on top of the mesh (see Instantiate.attachMesh).
local meshes: { [string]: any } = {}
function Signatures.setMesh(id: string, mesh: any?)
	meshes[string.lower(id)] = mesh
end
function Signatures.mesh(id: string): any?
	return meshes[string.lower(id)]
end

function Signatures.get(id: string): ((any, any) -> ())?
	return registry[string.lower(id)]
end

function Signatures.has(id: string): boolean
	return registry[string.lower(id)] ~= nil
end

function Signatures.list(): { string }
	local out = {}
	for k in registry do
		table.insert(out, k)
	end
	table.sort(out)
	return out
end

function Signatures.find(r: any): (string?, ((any, any) -> ())?)
	local id = string.lower(tostring(r.id or ""))
	if registry[id] then
		return id, registry[id]
	end
	local g = r.synonymGroup and string.lower(r.synonymGroup)
	if g and registry[g] then
		return g, registry[g]
	end
	-- multi-word ids: last word, then a two-word suffix ("pirate ship" in "ghost pirate ship")
	local words = string.split(id, " ")
	local plan = r.visual and r.visual.bodyPlan
	local function ok(key: string): boolean
		-- plan may list alternatives: "Quadruped|Dragon"
		return registry[key] ~= nil and (plans[key] == nil or (plan ~= nil and string.find("|" .. plans[key] .. "|", "|" .. plan .. "|", 1, true) ~= nil))
	end
	if #words >= 3 then
		local two = words[#words - 1] .. " " .. words[#words]
		if ok(two) then
			return two, registry[two]
		end
	end
	if #words >= 2 then
		local last = words[#words]
		if ok(last) then
			return last, registry[last]
		end
	end
	return nil, nil
end

for _, child in script:GetChildren() do
	local mod = require(child) :: any
	if type(mod) == "table" then
		for id, entry in mod do
			if type(entry) == "function" then
				Signatures.register(id, entry)
			else
				Signatures.register(id, entry.build, entry.plan)
			end
		end
	end
end

return Signatures
