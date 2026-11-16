--!strict
-- Safety: per-player rate limiting + spam detection, the hashed blocklist, keyboard-mash detection
-- and TextService filtering (DESIGN §9). Every function here is total: no errors escape, and when
-- filtering fails we fail CLOSED (empty string / "hashed"), never open.

local Runtime = require(script.Parent.Runtime)
local Blocklist = require(script.Parent.Blocklist)

local Safety = {}

export type CheckReason = "Ok" | "Empty" | "RateLimited" | "Spam" | "Blocked"
export type Check = { ok: boolean, reason: CheckReason, text: string, normalized: string }

type PlayerState = {
	tokens: number,
	last: number,
	recent: { { text: string, t: number } },
	spamUntil: number,
	aiTimes: { number },
}

local states: { [number]: PlayerState } = {}
local filterCache: { [string]: { value: string, t: number } } = {}
local filterCacheCount = 0

local function cfg(): any
	local c = Runtime.config()
	return (c and c.Safety) or {}
end

local function userIdOf(player: any): number
	local ok, id = pcall(function()
		return player.UserId
	end)
	return if ok and type(id) == "number" then id else 0
end

local function stateFor(player: any): PlayerState
	local id = userIdOf(player)
	local s = states[id]
	if not s then
		s = { tokens = cfg().RateCapacity or 6, last = Runtime.clock(), recent = {}, spamUntil = 0, aiTimes = {} }
		states[id] = s
	end
	return s
end

-- Fallback normalizer used when Shared.Normalizer is unavailable: lowercase, strip punctuation,
-- collapse whitespace, 3+ repeated letters -> 2.
function Safety.basicNormalize(text: string): string
	local s = string.lower(text)
	s = string.gsub(s, "[%c%p]", " ")
	s = string.gsub(s, "%s+", " ")
	s = string.match(s, "^%s*(.-)%s*$") or ""
	s = string.gsub(s, "(%a)%1%1+", "%1%1")
	return s
end

function Safety.normalize(text: string): string
	local N = Runtime.sharedModule("Normalizer")
	if N and N.normalize then
		local ok, out = pcall(N.normalize, text)
		if ok and type(out) == "string" then
			return out
		end
	end
	return Safety.basicNormalize(text)
end

-- Truncate to MaxLength characters on a UTF-8 boundary; invalid UTF-8 becomes "".
function Safety.clampText(text: any): string
	if type(text) ~= "string" then
		return ""
	end
	if utf8.len(text) == nil then
		return ""
	end
	local max = cfg().MaxLength or 40
	if (utf8.len(text) :: number) > max then
		local cut = utf8.offset(text, max + 1)
		text = string.sub(text, 1, (cut or (#text + 1)) - 1)
	end
	return text
end

function Safety.isBlocked(text: string): boolean
	local ok, blocked = pcall(Blocklist.isBlocked, text)
	if not ok then
		return false
	end
	if blocked then
		return true
	end
	-- also check the Normalizer's view (number words, etc.)
	local ok2, blocked2 = pcall(Blocklist.isBlocked, Safety.normalize(text))
	return ok2 and blocked2 == true
end

-- Runtime ban hooks (Admin persists them).
function Safety.addBlocked(word: string)
	pcall(Blocklist.add, word)
end
function Safety.removeBlocked(word: string)
	pcall(Blocklist.remove, word)
end

-- Keyboard mash ("asdfgh", "qwrtzp"): skip the AI for these, it would only produce noise and cost.
function Safety.looksLikeMash(normalized: string): boolean
	local letters = string.gsub(normalized, "[^a-z]", "")
	if #letters < 5 then
		return false
	end
	local vowels = #(string.gsub(letters, "[^aeiouy]", ""))
	if vowels == 0 or vowels / #letters < 0.1 then
		return true
	end
	-- 7+ consonants in a row never happens in English ("catchphrase" peaks at 6)
	if string.find(letters, "[^aeiouy][^aeiouy][^aeiouy][^aeiouy][^aeiouy][^aeiouy][^aeiouy]") then
		return true
	end
	return false
end

-- Rate limit + spam + blocklist. Consumes one token.
function Safety.check(player: any, rawText: any): Check
	local c = cfg()
	local text = Safety.clampText(rawText)
	local normalized = Safety.normalize(text)
	if normalized == "" then
		return { ok = false, reason = "Empty", text = text, normalized = normalized }
	end
	local s = stateFor(player)
	local now = Runtime.clock()
	-- token bucket
	local cap = c.RateCapacity or 6
	s.tokens = math.min(cap, s.tokens + (now - s.last) * (c.RateRefill or 2))
	s.last = now
	if now < s.spamUntil then
		return { ok = false, reason = "Spam", text = text, normalized = normalized }
	end
	if s.tokens < 1 then
		return { ok = false, reason = "RateLimited", text = text, normalized = normalized }
	end
	s.tokens -= 1
	-- repeat detection
	local window = c.RepeatWindow or 8
	local kept = {}
	local same = 0
	for _, r in s.recent do
		if now - r.t <= window then
			table.insert(kept, r)
			if r.text == normalized then
				same += 1
			end
		end
	end
	table.insert(kept, { text = normalized, t = now })
	while #kept > 32 do
		table.remove(kept, 1)
	end
	s.recent = kept
	if same + 1 > (c.RepeatMax or 10) then
		s.spamUntil = now + (c.SpamCooldown or 4)
		return { ok = false, reason = "Spam", text = text, normalized = normalized }
	end
	if Safety.isBlocked(text) then
		return { ok = false, reason = "Blocked", text = text, normalized = normalized }
	end
	return { ok = true, reason = "Ok", text = text, normalized = normalized }
end

-- Per-player NEW-phrase limit (phrases that would reach the AI), sliding minute. Separate from the
-- typing limit in Safety.check. Returns true and records when allowed.
function Safety.allowNewPhrase(player: any): boolean
	local limit = 6
	local c = Runtime.config()
	if c and c.AI and c.AI.NewPhrasePerMinute then
		limit = c.AI.NewPhrasePerMinute
	end
	local s = stateFor(player)
	local now = Runtime.clock()
	local kept = {}
	for _, t in s.aiTimes do
		if now - t < 60 then
			table.insert(kept, t)
		end
	end
	s.aiTimes = kept
	if #kept >= limit then
		return false
	end
	table.insert(kept, now)
	return true
end

function Safety.forget(player: any)
	states[userIdOf(player)] = nil
end

-- Filtered text that contains '#' where the source had none was hashed (fully or partly).
function Safety.isHashed(original: string, filtered: string): boolean
	if filtered == "" and original ~= "" then
		return true
	end
	return string.find(filtered, "#", 1, true) ~= nil and string.find(original, "#", 1, true) == nil
end

local function cacheGet(key: string): string?
	local e = filterCache[key]
	if e and Runtime.clock() - e.t < (cfg().FilterCacheSeconds or 60) then
		return e.value
	end
	return nil
end

local function cachePut(key: string, value: string)
	if filterCacheCount > 1000 then
		table.clear(filterCache)
		filterCacheCount = 0
	end
	if filterCache[key] == nil then
		filterCacheCount += 1
	end
	filterCache[key] = { value = value, t = Runtime.clock() }
end

local function filterResult(player: any, text: string): any
	local TextService = Runtime.service("TextService")
	local lastErr
	for attempt = 1, 2 do
		local ok, result = pcall(function()
			return TextService:FilterStringAsync(text, userIdOf(player), Runtime.filterContext())
		end)
		if ok and result then
			return result
		end
		lastErr = result
		if attempt == 1 then
			Runtime.task().wait(0.2)
		end
	end
	Runtime.warnOnce("filterfail", "TextService filtering failed: " .. tostring(lastErr))
	return nil
end

-- Text visible to everyone in the server (TextFilterResult:GetNonChatStringForBroadcastAsync).
-- Returns "" if filtering is unavailable (fail closed).
function Safety.filterForBroadcast(player: any, text: string): string
	if type(text) ~= "string" or text == "" then
		return ""
	end
	local key = "b:" .. userIdOf(player) .. ":" .. text
	local hit = cacheGet(key)
	if hit then
		return hit
	end
	local result = filterResult(player, text)
	if not result then
		return ""
	end
	local ok, out = pcall(function()
		return result:GetNonChatStringForBroadcastAsync()
	end)
	if not ok or type(out) ~= "string" then
		return ""
	end
	cachePut(key, out)
	return out
end

-- Text shown to one specific user (TextFilterResult:GetNonChatStringForUserAsync).
function Safety.filterForUser(player: any, text: string, toPlayer: any): string
	if type(text) ~= "string" or text == "" then
		return ""
	end
	local toId = userIdOf(toPlayer)
	local key = "u:" .. userIdOf(player) .. ":" .. toId .. ":" .. text
	local hit = cacheGet(key)
	if hit then
		return hit
	end
	local result = filterResult(player, text)
	if not result then
		return ""
	end
	local ok, out = pcall(function()
		return result:GetNonChatStringForUserAsync(toId)
	end)
	if not ok or type(out) ~= "string" then
		return ""
	end
	cachePut(key, out)
	return out
end

function Safety.init()
	table.clear(states)
	table.clear(filterCache)
	filterCacheCount = 0
end

return Safety
