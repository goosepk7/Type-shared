--!strict
-- Minimal pure-Luau signal (no BindableEvent, runs under Lune). Handlers run in order, each in pcall.

export type Connection = { Connected: boolean, Disconnect: (self: Connection) -> () }
export type Signal<T...> = {
	Connect: (self: Signal<T...>, fn: (T...) -> ()) -> Connection,
	Fire: (self: Signal<T...>, T...) -> (),
	Once: (self: Signal<T...>, fn: (T...) -> ()) -> Connection,
	DisconnectAll: (self: Signal<T...>) -> (),
}

local Signal = {}
Signal.__index = Signal

function Signal.new<T...>(): Signal<T...>
	return setmetatable({ _handlers = {} }, Signal) :: any
end

function Signal:Connect(fn)
	local conn
	conn = {
		Connected = true,
		Disconnect = function(c)
			if not c.Connected then
				return
			end
			c.Connected = false
			local i = table.find(self._handlers, conn)
			if i then
				table.remove(self._handlers, i)
			end
		end,
		_fn = fn,
	}
	table.insert(self._handlers, conn)
	return conn
end

function Signal:Once(fn)
	local conn
	conn = self:Connect(function(...)
		conn:Disconnect()
		fn(...)
	end)
	return conn
end

function Signal:Fire(...)
	for _, c in table.clone(self._handlers) do
		if c.Connected then
			local ok, err = pcall(c._fn, ...)
			if not ok then
				local w = (warn :: any) or print
				w("[WordEngine] signal handler error: " .. tostring(err))
			end
		end
	end
end

function Signal:DisconnectAll()
	for _, c in self._handlers do
		c.Connected = false
	end
	table.clear(self._handlers)
end

return Signal
