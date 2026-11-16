--!strict
-- Tiny client-side signal (no BindableEvent allocations, handlers in pcall, safe disconnect while firing).
local Signal = {}
Signal.__index = Signal

export type Connection = { Connected: boolean, Disconnect: (Connection) -> () }

function Signal.new(): any
	return setmetatable({ _h = {} }, Signal)
end

function Signal:Connect(fn: (...any) -> ()): Connection
	local c: any = { Connected = true, _fn = fn }
	local handlers = self._h
	function c.Disconnect(conn: any)
		conn.Connected = false
		local i = table.find(handlers, conn)
		if i then
			table.remove(handlers, i)
		end
	end
	table.insert(handlers, c)
	return c
end

function Signal:Once(fn: (...any) -> ()): Connection
	local c: any
	c = self:Connect(function(...)
		c:Disconnect()
		fn(...)
	end)
	return c
end

function Signal:Fire(...: any)
	for _, c in table.clone(self._h) do
		if c.Connected then
			local ok, err = pcall(c._fn, ...)
			if not ok then
				warn("[WordEngine.UI] " .. tostring(err))
			end
		end
	end
end

function Signal:Destroy()
	for _, c in self._h do
		c.Connected = false
	end
	table.clear(self._h)
end

return Signal
