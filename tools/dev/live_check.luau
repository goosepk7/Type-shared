-- Live-server smoke test for WordEngine. Run: python3 tools/cloud_exec.py tools/dev/live_check.luau
-- Read-only: requires the engine already in the place, builds summons under a temp folder, destroys them.
local RS = game:GetService("ReplicatedStorage")
local WE = require(RS:WaitForChild("WordEngine", 10))
local out = { version = WE.VERSION, errors = {}, built = 0, parts = 0 }
local function try(label, fn)
	local ok, err = pcall(fn)
	if not ok then table.insert(out.errors, label .. ": " .. tostring(err)) end
	return ok
end
local phrases = { "dragon", "asteroid", "small tornado", "giant fire shark", "spaghetti dragon", "cheese tank",
	"glass shark", "bee wall", "tiny angry golden robot shark", "bees", "castle", "wizard", "fireball", "black hole",
	"angry toaster", "sleepy cat", "rocket powered snail", "zzqxv" }
local folder = Instance.new("Folder"); folder.Name = "WE_LiveCheck"; folder.Parent = workspace
out.words = {}
for _, p in phrases do
	try("resolve " .. p, function()
		local r = WE.Resolver.resolveLocal(p)
		table.insert(out.words, p .. " -> " .. r.canonical .. " [" .. r.source .. "]")
		for _, style in { "Solid", "Spectral" } do
			try("build " .. p .. " " .. style, function()
				local m = WE.Summon.build(r, { style = style, seed = 7 })
				m.Parent = folder
				out.built += 1
				out.parts += #m:GetDescendants()
				local a = WE.Summon.animate(m, r)
				a:play("Idle"); a:destroy()
			end)
		end
	end)
end
try("reactions", function()
	out.steam = WE.Reactions.get("Fire", "Ice").id
	out.matchup = WE.Reactions.matchup("Water", "Fire")
end)
try("effects", function()
	local h = WE.Effects.play("explosion_medium", { style = "Solid", element = "Fire", at = CFrame.new(0, 5, 0) })
	if h and h.stop then h:stop() end
end)
try("library", function()
	out.count = WE.Library.count()
	out.suggest = table.concat(WE.Suggest.prefix("dra", nil, 5), ",")
end)
folder:Destroy()
return out
