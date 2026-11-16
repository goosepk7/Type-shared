--!strict
-- Suggest: client-side autocomplete, no server round trip.
--   Suggest.prefix(prefix, wordBook?, limit?) -> { string }
-- Ranking: the player's word book first (in the order given, i.e. the caller's recency/play order), then library
-- words by signature + popularity (Library.prefixSearch). Multi-word input completes the LAST word and keeps the
-- typed modifiers in front ("giant sha" -> "giant shark").

local Library = require(script.Parent.Library)
local Modifiers = require(script.Parent.Modifiers)

local Suggest = {}

local DEFAULT_LIMIT = 4

local function clean(s: string): string
	s = string.lower(s)
	s = string.gsub(s, "^%s+", "")
	s = string.gsub(s, "%s+", " ")
	return s
end

function Suggest.prefix(prefix: string, wordBook: { string }?, limit: number?): { string }
	local n = math.clamp(math.floor(limit or DEFAULT_LIMIT), 1, 20)
	if type(prefix) ~= "string" then
		return {}
	end
	local p = clean(prefix)
	if p == "" then
		return {}
	end
	local out: { string } = {}
	local seen: { [string]: boolean } = {}
	local function push(s: string)
		if not seen[s] and #out < n then
			seen[s] = true
			table.insert(out, s)
		end
	end
	if wordBook then
		local plen = #p
		for _, w in wordBook do
			if type(w) == "string" then
				local lw = string.lower(w)
				if #lw > plen and string.sub(lw, 1, plen) == p then
					push(lw)
					if #out >= n then
						return out
					end
				end
			end
		end
	end
	for _, k in Library.prefixSearch(p, n) do
		push(k)
	end
	-- "giant sha" -> keep the modifiers, complete the last word
	if #out < n then
		local head, last = string.match(p, "^(.* )(%S+)$")
		if head and last and #last >= 1 then
			local allMods = true
			for w in string.gmatch(head, "%S+") do
				if Modifiers.lookup(w) == nil and Modifiers.Fillers[w] == nil and Library.lookupMaterial(w) == nil then
					allMods = false
					break
				end
			end
			if allMods then
				for _, k in Library.prefixSearch(last, n) do
					push(head .. k)
				end
			end
		end
	end
	return out
end

return Suggest
