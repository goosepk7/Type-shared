--!strict
-- LocalStore: an in-memory stand-in for DataStore / OrderedDataStore with the same call shapes.
-- Used (1) by unit tests, with failure injection, and (2) automatically in Studio when "Enable Studio
-- Access to API Services" is off, so the test place still runs. Values are deep-copied on every read and
-- write to mimic serialisation (shared references between caller and store would hide bugs).

local LocalStore = {}
LocalStore.__index = LocalStore

local function copy(v: any, depth: number?): any
	local d = depth or 0
	assert(d < 64, "LocalStore: value too deep")
	local t = type(v)
	if t == "table" then
		local out = {}
		for k, x in v do
			assert(type(k) == "string" or type(k) == "number", "LocalStore: bad key type " .. type(k))
			out[k] = copy(x, d + 1)
		end
		return out
	elseif t == "function" or t == "userdata" or t == "thread" then
		error("104: Cannot store " .. t .. " in data store")
	end
	return v
end
LocalStore.copy = copy

export type LocalStore = typeof(setmetatable(
	{} :: {
		name: string,
		ordered: boolean,
		data: { [string]: any },
		userIds: { [string]: { number } },
		versions: { [string]: number },
		calls: { [string]: number },
		failures: { [string]: number }, -- op -> remaining forced failures
		failError: string,
		beforeUpdate: ((key: string) -> ())?, -- hook to simulate a concurrent writer
	},
	LocalStore
))

function LocalStore.new(name: string?, ordered: boolean?): LocalStore
	return setmetatable({
		name = name or "local",
		ordered = ordered == true,
		data = {},
		userIds = {},
		versions = {},
		calls = {},
		failures = {},
		failError = "502: simulated transient failure",
		beforeUpdate = nil,
	}, LocalStore) :: any
end

function LocalStore.failNext(self: LocalStore, op: string, n: number, err: string?)
	self.failures[op] = n
	if err then
		self.failError = err
	end
end

function LocalStore._op(self: LocalStore, op: string)
	self.calls[op] = (self.calls[op] or 0) + 1
	local f = self.failures[op]
	if f and f > 0 then
		self.failures[op] = f - 1
		error(self.failError)
	end
end

function LocalStore.GetAsync(self: LocalStore, key: string): (any, any)
	self:_op("GetAsync")
	return copy(self.data[key]), { Version = tostring(self.versions[key] or 0) }
end

function LocalStore.SetAsync(self: LocalStore, key: string, value: any, userIds: { number }?)
	self:_op("SetAsync")
	self.data[key] = copy(value)
	self.versions[key] = (self.versions[key] or 0) + 1
	if userIds then
		self.userIds[key] = table.clone(userIds)
	end
	return tostring(self.versions[key])
end

function LocalStore.UpdateAsync(self: LocalStore, key: string, transform: (any, any) -> (any, any?, any?)): (any, any)
	self:_op("UpdateAsync")
	if self.beforeUpdate then
		self.beforeUpdate(key)
	end
	local new, userIds = transform(copy(self.data[key]), { Version = tostring(self.versions[key] or 0) })
	if new == nil then
		return nil, nil -- cancelled: nothing written
	end
	self.data[key] = copy(new)
	self.versions[key] = (self.versions[key] or 0) + 1
	if type(userIds) == "table" then
		self.userIds[key] = table.clone(userIds)
	end
	return copy(new), { Version = tostring(self.versions[key]) }
end

function LocalStore.IncrementAsync(self: LocalStore, key: string, delta: number?): number
	self:_op("IncrementAsync")
	local v = (tonumber(self.data[key]) or 0) + (delta or 1)
	if self.ordered then
		v = math.floor(v)
	end
	self.data[key] = v
	return v
end

function LocalStore.RemoveAsync(self: LocalStore, key: string): any
	self:_op("RemoveAsync")
	local old = self.data[key]
	self.data[key] = nil
	return copy(old)
end

-- OrderedDataStore:GetSortedAsync(ascending, pageSize) -> pages with :GetCurrentPage()
function LocalStore.GetSortedAsync(self: LocalStore, ascending: boolean, pageSize: number): any
	self:_op("GetSortedAsync")
	local rows = {}
	for k, v in self.data do
		if type(v) == "number" then
			table.insert(rows, { key = k, value = v })
		end
	end
	table.sort(rows, function(a, b)
		if a.value == b.value then
			return a.key < b.key
		end
		if ascending then
			return a.value < b.value
		end
		return a.value > b.value
	end)
	local page = {}
	for i = 1, math.min(pageSize, #rows) do
		page[i] = rows[i]
	end
	return {
		IsFinished = true,
		GetCurrentPage = function()
			return page
		end,
		AdvanceToNextPageAsync = function() end,
	}
end

-- A DataStoreService look-alike that hands out LocalStores and a configurable budget.
function LocalStore.service(): any
	local svc = { stores = {}, budget = 1000 :: number }
	function svc:GetDataStore(name: string, scope: string?)
		local id = name .. "/" .. (scope or "global")
		self.stores[id] = self.stores[id] or LocalStore.new(id, false)
		return self.stores[id]
	end
	function svc:GetOrderedDataStore(name: string, scope: string?)
		local id = "ordered:" .. name .. "/" .. (scope or "global")
		self.stores[id] = self.stores[id] or LocalStore.new(id, true)
		return self.stores[id]
	end
	function svc:GetRequestBudgetForRequestType(_t: any): number
		return self.budget
	end
	return svc
end

return LocalStore
