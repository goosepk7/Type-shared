--!strict
-- WordEngineServer facade. DESIGN §4.
--
--   local WordEngineServer = require(ServerScriptService.WordEngineServer)
--   WordEngineServer.start({ game = "Wizard", aiSecretName = "WORDENGINE_AI_KEY", remotes = true })
--   local result, handle = WordEngineServer.Interpreter.interpretAsync(player, "flaming toaster")
--
-- Child modules load lazily (WordEngineServer.WordBook, .Admin, ...), like the Shared facade.

local Runtime = require(script.Runtime)

local WordEngineServer = {}

export type StartOptions = {
	game: string?, -- "Wizard" | "Defend" (analytics namespace)
	aiSecretName: string?, -- Secrets Store name of the Claude API key (default "ANTHROPIC_API_KEY")
	remotes: boolean?, -- create ReplicatedStorage.WordEngineRemotes (default true)
}

local started = false
local loaded: { [string]: any } = {}

setmetatable(WordEngineServer, {
	__index = function(_, key: string)
		local cached = loaded[key]
		if cached ~= nil then
			return cached
		end
		local child = script:FindFirstChild(key)
		if child == nil then
			error(("WordEngineServer has no module %q"):format(tostring(key)), 2)
		end
		local mod = require(child :: any)
		loaded[key] = mod
		return mod
	end,
})

local function try(label: string, fn: () -> ())
	local ok, err = pcall(fn)
	if not ok then
		Runtime.log("warn", label .. " failed: " .. tostring(err))
	end
end

-- Idempotent. Call once from a server Script after any Config.set overrides.
function WordEngineServer.start(options: StartOptions?)
	if started then
		return WordEngineServer
	end
	started = true
	local opts: StartOptions = options or {}
	WordEngineServer.gameName = opts.game or "Unknown"

	-- Services agent modules (each idempotent, optional).
	for _, name in { "Data", "WordBook", "Currency", "Purchases", "Analytics", "Admin" } do
		if script:FindFirstChild(name) then
			try(name .. ".start", function()
				local mod = (WordEngineServer :: any)[name]
				if type(mod.start) == "function" then
					if name == "Analytics" or name == "WordBook" then
						mod.start(opts.game)
					else
						mod.start()
					end
				end
			end)
		end
	end

	local Safety = (WordEngineServer :: any).Safety
	local Cache = (WordEngineServer :: any).Cache
	local AI = (WordEngineServer :: any).AI
	local Interpreter = (WordEngineServer :: any).Interpreter

	try("Safety.init", Safety.init)
	try("Cache.init", function()
		Cache.init()
		Cache.startLoop()
	end)
	try("AI.init", function()
		AI.init({ secretName = opts.aiSecretName })
		AI.startLoops() -- live kill switch + cross-server spend counter
	end)
	try("Interpreter.init", Interpreter.init)

	local Players = Runtime.service("Players")
	Players.PlayerRemoving:Connect(function(player: any)
		Interpreter.forget(player)
	end)

	try("BindToClose", function()
		(game :: any):BindToClose(function()
			pcall(Cache.flushAll)
			pcall(AI.Cost.flush)
		end)
	end)

	if opts.remotes ~= false then
		try("Net.setupServer", function()
			local Net = Runtime.sharedModule("Net")
			local sc = Runtime.config().Safety or {}
			Net.setupServer(function(player: any, text: string)
				return Interpreter.interpretAsync(player, text)
			end, { capacity = sc.NetCapacity, refill = sc.NetRefill })
		end)
	end
	return WordEngineServer
end

function WordEngineServer.stats(): { [string]: any }
	return (WordEngineServer :: any).Interpreter.stats()
end

return WordEngineServer
