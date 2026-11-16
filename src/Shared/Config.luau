--!strict
-- WordEngine tunables. Each section is owned by one subsystem; games override with Config.set(path, value)
-- at startup (before WordEngineServer.start). Keep values here meaning-level, not game balance.

local Config = {}

-- [Speller] owned by Normalizer/Speller/Library/Modifiers
Config.Speller = {}
Config.Modifiers = {}

-- [AI] owned by Server/AI + Interpreter + Cache
Config.AI = {}
Config.Cache = {}

-- [Safety] owned by Server/Safety
Config.Safety = {}

-- [Visual] owned by Summon + Effects
Config.Visual = {
	Inset = 0.02, -- studs: touching parts are inset so faces never coincide (no z-fighting)
	DecalOffset = 0.01,
}

-- [Services] owned by Data/WordBook/Currency/Purchases/Analytics/Admin/UI
Config.Services = {}
Config.UI = {}

function Config.set(path: string, value: any)
	local node: any = Config
	local parts = string.split(path, ".")
	for i = 1, #parts - 1 do
		node = node[parts[i]]
		assert(type(node) == "table", "Config.set: bad path " .. path)
	end
	node[parts[#parts]] = value
end

return Config
