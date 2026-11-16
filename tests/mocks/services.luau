-- Shared mocks for the services specs (Data, WordBook, Currency, Purchases).
-- Fake clock: wait() advances time instantly; spawn() runs synchronously.
local Mocks = {}

function Mocks.setup(t)
	local Env = t.load("src/Server/Data/Env")
	local Config = t.load("src/Shared/Config")
	local LocalStore = t.load("src/Server/Data/LocalStore")
	local clock = { now = 1_700_000_000, mono = 0 }
	local logs = {}
	local dss = LocalStore.service()
	local guidN = 0
	local serde = require("@lune/serde")
	local httpJson = {
		JSONEncode = function(_, v) return serde.encode("json", v) end,
		JSONDecode = function(_, v) return serde.decode("json", v) end,
		GetSecret = function() error("Can't find secret with given key") end,
	}
	local env = {
		services = { DataStoreService = dss, HttpService = httpJson },
		now = function()
			return clock.now
		end,
		clock = function()
			return clock.mono
		end,
		wait = function(s)
			clock.now += s
			clock.mono += s
		end,
		spawn = function(fn, ...)
			fn(...)
		end,
		jobId = "server-A",
		placeId = 1,
		gameId = 1,
		isStudio = false,
		config = Config,
		guid = function()
			guidN += 1
			return "g" .. guidN
		end,
		log = function(level, msg)
			table.insert(logs, level .. ": " .. msg)
		end,
	}
	Env.set(env)
	return {
		Env = Env,
		env = env,
		Config = Config,
		LocalStore = LocalStore,
		dss = dss,
		clock = clock,
		logs = logs,
	}
end

function Mocks.player(userId)
	local p = { UserId = userId, Name = "Player" .. userId, Parent = "Players", kicked = nil }
	function p:Kick(msg)
		self.kicked = msg
		self.Parent = nil
	end
	return p
end

return Mocks
