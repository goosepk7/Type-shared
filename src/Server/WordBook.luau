--!strict
-- WordBook: every word a player has cast, with counts and first/last use. Shared across both games.
--
--   WordBook.record(player, result)      -- call on CAST (not on preview); returns (entry, isNew)
--   WordBook.get(player)                 -- { WordBookEntry } newest first
--   WordBook.has(player, word) / entry(player, word) / count(player) / top(player, n)
--   WordBook.discovered:Connect(fn(player, entry))   -- first time a player casts a word (UI toast)
--
-- Storage: inside the session-locked profile (Data namespace "WordEngine", key `wordbook`), keyed by the
-- result's synonymGroup so "kitty" and "cat" share one page. Capped at Config.Services.WordBook.MaxEntries;
-- when full, the lowest-ranked batch is evicted, rank = lastUsed + min(uses, MaxUseBonus) * UseBonusSeconds
-- (LRU that protects favourites).
--
-- Per game in v1 (DESIGN.md §10, brief 4): no in-game cross-universe sync. WordBook.export/import and the
-- conflict-free union merge (max count, min first, max last, OR of game bits) are the seam for merging
-- books later (offline promotion tool or a future version).

local Data = require(script.Parent.Data)
local Env = Data.Env
local Signal = Data.Signal

export type WordBookEntry = {
	id: string, -- synonymGroup (page key)
	word: string, -- canonical last cast
	count: number,
	first: number, -- unix seconds
	last: number,
	element: string,
	category: string,
	games: number, -- bitmask: 1 = Wizard, 2 = Defend
}

-- stored compact: { w, n, f, l, e, c, g }
type Stored = { w: string, n: number, f: number, l: number, e: string, c: string, g: number }

local WordBook = {}
WordBook.discovered = Signal.new() :: Signal.Signal<any, WordBookEntry>
WordBook.recorded = Signal.new() :: Signal.Signal<any, WordBookEntry>

local GAME_BITS = { Wizard = 1, Defend = 2 }
local gameBit = 0

local function cfg()
	return Env.config().Services.WordBook
end

local function expand(id: string, s: Stored): WordBookEntry
	return { id = id, word = s.w or id, count = s.n or 0, first = s.f or 0, last = s.l or 0,
		element = s.e or "None", category = s.c or "Object", games = s.g or 0 }
end

local function book(player: any): any?
	local core = Data.get(player)
	return core and core.wordbook
end

local function keyOf(word: string): string
	return string.lower(string.sub(word, 1, 40))
end

-- Evict the lowest-ranked batch when over the cap. Pure; exported for tests.
function WordBook.evict(entries: { [string]: Stored }, maxEntries: number, batch: number, bonus: number, maxBonus: number): number
	local n = 0
	for _ in entries do
		n += 1
	end
	if n <= maxEntries then
		return 0
	end
	local ranked = {}
	for id, s in entries do
		table.insert(ranked, { id = id, score = (s.l or 0) + math.min(s.n or 0, maxBonus) * bonus })
	end
	table.sort(ranked, function(a, b)
		if a.score == b.score then
			return a.id < b.id
		end
		return a.score < b.score
	end)
	local remove = math.min(#ranked, (n - maxEntries) + batch)
	for i = 1, remove do
		entries[ranked[i].id] = nil
	end
	return remove
end

-- Union merge of two entry maps into `into` (mutated). Commutative, associative, idempotent.
function WordBook.merge(into: { [string]: Stored }, from: { [string]: Stored }): number
	local changed = 0
	for id, b in from do
		if type(b) == "table" then
			local a = into[id]
			if a == nil then
				into[id] = { w = b.w, n = b.n or 0, f = b.f or 0, l = b.l or 0, e = b.e, c = b.c, g = b.g or 0 }
				changed += 1
			else
				local before = a.n .. "|" .. a.f .. "|" .. a.l .. "|" .. (a.g or 0)
				a.n = math.max(a.n or 0, b.n or 0)
				local fa, fb = a.f or 0, b.f or 0
				a.f = if fa == 0 then fb elseif fb == 0 then fa else math.min(fa, fb)
				if (b.l or 0) > (a.l or 0) then
					a.l = b.l
					a.w, a.e, a.c = b.w or a.w, b.e or a.e, b.c or a.c
				end
				a.g = bit32.bor(a.g or 0, b.g or 0)
				if before ~= (a.n .. "|" .. a.f .. "|" .. a.l .. "|" .. a.g) then
					changed += 1
				end
			end
		end
	end
	return changed
end

function WordBook.setGame(name: string)
	gameBit = GAME_BITS[name] or 0
end

-- Record a cast. Returns (entry, isNew) or nil if the player's data isn't loaded.
function WordBook.record(player: any, result: any): (WordBookEntry?, boolean)
	if type(result) ~= "table" or result.source == "Fallback" then
		return nil, false
	end
	local id = keyOf(result.synonymGroup or result.id or "")
	if id == "" then
		return nil, false
	end
	local isNew = false
	local out: WordBookEntry? = nil
	Data.update(player, function(core)
		local wb = core.wordbook
		local now = math.floor(Env.now())
		local s: Stored? = wb.entries[id]
		if s == nil then
			isNew = true
			s = { w = result.id, n = 0, f = now, l = now, e = result.element, c = result.category, g = 0 }
			wb.entries[id] = s
		end
		local e = s :: Stored
		e.n += 1
		e.l = now
		e.w = result.id
		e.e = result.element or e.e
		e.c = result.category or e.c
		e.g = bit32.bor(e.g or 0, gameBit)
		wb.total = (wb.total or 0) + 1
		wb.dirty = true
		local c = cfg()
		if isNew then
			WordBook.evict(wb.entries, c.MaxEntries, c.EvictBatch, c.UseBonusSeconds, c.MaxUseBonus)
		end
		out = expand(id, e)
	end)
	if out then
		WordBook.recorded:Fire(player, out)
		if isNew then
			WordBook.discovered:Fire(player, out)
		end
	end
	return out, isNew
end

function WordBook.get(player: any): { WordBookEntry }
	local wb = book(player)
	local list = {}
	if not wb then
		return list
	end
	for id, s in wb.entries do
		table.insert(list, expand(id, s))
	end
	table.sort(list, function(a, b)
		if a.last == b.last then
			return a.id < b.id
		end
		return a.last > b.last
	end)
	return list
end

function WordBook.entry(player: any, word: string): WordBookEntry?
	local wb = book(player)
	local id = keyOf(word)
	local s = wb and wb.entries[id]
	return s and expand(id, s)
end

function WordBook.has(player: any, word: string): boolean
	return WordBook.entry(player, word) ~= nil
end

-- (distinct words, total casts)
function WordBook.count(player: any): (number, number)
	local wb = book(player)
	if not wb then
		return 0, 0
	end
	local n = 0
	for _ in wb.entries do
		n += 1
	end
	return n, wb.total or 0
end

function WordBook.top(player: any, limit: number?): { WordBookEntry }
	local list = WordBook.get(player)
	table.sort(list, function(a, b)
		if a.count == b.count then
			return a.last > b.last
		end
		return a.count > b.count
	end)
	local out = {}
	for i = 1, math.min(limit or 10, #list) do
		out[i] = list[i]
	end
	return out
end

---------------------------------------------------------------------------------------------------
-- Merge seam (v1: the word book is per game, DESIGN.md §10). Nothing here talks to another universe;
-- an offline tool (tools/promote.py) or a future version can move books between games with these.
---------------------------------------------------------------------------------------------------

-- Compact copy of the player's entries (the stored shape), safe to serialise.
function WordBook.export(player: any): { [string]: Stored }?
	local wb = book(player)
	return wb and Data.SessionStore.deepCopy(wb.entries)
end

-- Union-merge entries (e.g. another game's book) into the player's book. Returns entries changed.
function WordBook.import(player: any, entries: { [string]: Stored }): number
	if type(entries) ~= "table" then
		return 0
	end
	local changed = 0
	local c = cfg()
	Data.update(player, function(core)
		changed = WordBook.merge(core.wordbook.entries, entries)
		WordBook.evict(core.wordbook.entries, c.MaxEntries, c.EvictBatch, c.UseBonusSeconds, c.MaxUseBonus)
	end)
	return changed
end

local started = false
function WordBook.start(gameName: string?)
	if started then
		return
	end
	started = true
	if gameName then
		WordBook.setGame(gameName)
	end
end

function WordBook._reset()
	started = false
	gameBit = 0
	WordBook.discovered:DisconnectAll()
	WordBook.recorded:DisconnectAll()
end

return WordBook
