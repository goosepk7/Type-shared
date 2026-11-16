--!strict
-- Deterministic PRNG (xorshift32 with a splitmix-style string hash for seeding). Pure integer math via bit32,
-- so the same seed gives the same sequence on every Roblox client, server and under Lune.

export type Rng = {
	state: number,
	next: (self: Rng) -> number,
	range: (self: Rng, lo: number, hi: number) -> number,
	int: (self: Rng, lo: number, hi: number) -> number,
	chance: (self: Rng, p: number) -> boolean,
	pick: <T>(self: Rng, list: { T }) -> T,
	jitter: (self: Rng, v: number, amount: number) -> number,
}

local Rng = {}
Rng.__index = Rng

-- FNV-1a 32-bit
function Rng.hash(s: string): number
	local h = 2166136261
	for i = 1, #s do
		h = bit32.bxor(h, string.byte(s, i))
		-- multiply by 16777619 mod 2^32 without float overflow: split into 16-bit halves
		local lo = bit32.band(h, 0xFFFF)
		local hi = bit32.rshift(h, 16)
		h = bit32.band(lo * 16777619 + bit32.lshift(bit32.band(hi * 16777619, 0xFFFF), 16), 0xFFFFFFFF)
	end
	return h
end

function Rng.new(seed: number | string): Rng
	local s: number
	if type(seed) == "string" then
		s = Rng.hash(seed)
	else
		s = bit32.band(math.floor(math.abs(seed :: number)) % 4294967296, 0xFFFFFFFF)
		s = bit32.bxor(s, 0x9E3779B9)
	end
	if s == 0 then
		s = 0x6D2B79F5
	end
	local self = setmetatable({ state = s }, Rng) :: any
	-- warm up
	for _ = 1, 4 do
		self:next()
	end
	return self
end

-- uniform [0, 1)
function Rng.next(self: Rng): number
	local x = self.state
	x = bit32.bxor(x, bit32.lshift(x, 13))
	x = bit32.bxor(x, bit32.rshift(x, 17))
	x = bit32.bxor(x, bit32.lshift(x, 5))
	self.state = x
	return x / 4294967296
end

function Rng.range(self: Rng, lo: number, hi: number): number
	return lo + (hi - lo) * self:next()
end

function Rng.int(self: Rng, lo: number, hi: number): number
	return math.min(hi, lo + math.floor(self:next() * (hi - lo + 1)))
end

function Rng.chance(self: Rng, p: number): boolean
	return self:next() < p
end

function Rng.pick<T>(self: Rng, list: { T }): T
	return list[self:int(1, #list)]
end

function Rng.jitter(self: Rng, v: number, amount: number): number
	return v * (1 + (self:next() * 2 - 1) * amount)
end

return Rng
