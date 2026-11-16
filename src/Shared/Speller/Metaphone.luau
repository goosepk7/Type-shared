--!strict
-- Double Metaphone (Lawrence Philips, 2000). Line-by-line mirror of tools/metaphone.py: the build stores codes for
-- every library key and this module computes codes for player input, so the two MUST agree
-- (tests/specs/speller.spec.luau checks every library key). Only ASCII letters are used; max code length 4.

local Metaphone = {}

local MAX_LEN = 4
local VOWEL = { A = true, E = true, I = true, O = true, U = true, Y = true }

function Metaphone.encode(text: string, maxLen: number?): (string, string)
	local limit = maxLen or MAX_LEN
	local word = string.gsub(string.upper(text), "[^A-Z]", "")
	local length = #word
	if length == 0 then
		return "", ""
	end
	local last = length - 1
	local padded = word .. "     "
	local plen = #padded
	local pri: { string } = {}
	local sec: { string } = {}
	local priLen, secLen = 0, 0

	-- 0-based helpers to mirror the reference implementation
	local function get(i: number): string
		if i >= 0 and i < plen then
			return string.sub(padded, i + 1, i + 1)
		end
		return ""
	end
	local function at(start: number, n: number, ...: string): boolean
		if start < 0 or start >= plen then
			return false
		end
		local s = string.sub(padded, start + 1, start + n)
		for k = 1, select("#", ...) do
			if s == select(k, ...) then
				return true
			end
		end
		return false
	end
	local function vowel(i: number): boolean
		return i >= 0 and i < plen and VOWEL[string.sub(padded, i + 1, i + 1)] == true
	end
	local slavo = string.find(word, "W", 1, true) ~= nil
		or string.find(word, "K", 1, true) ~= nil
		or string.find(word, "CZ", 1, true) ~= nil
		or string.find(word, "WITZ", 1, true) ~= nil

	local function add(main: string, alt: string?)
		if alt == nil then
			if main ~= "" then
				table.insert(pri, main)
				table.insert(sec, main)
				priLen += #main
				secLen += #main
			end
			return
		end
		if main ~= "" then
			table.insert(pri, main)
			priLen += #main
		end
		if alt ~= "" then
			if string.sub(alt, 1, 1) ~= " " then
				table.insert(sec, alt)
				secLen += #alt
			end
		elseif main ~= "" and string.sub(main, 1, 1) ~= " " then
			table.insert(sec, main)
			secLen += #main
		end
	end

	local cur = 0
	if at(0, 2, "GN", "KN", "PN", "WR", "PS") then
		cur += 1
	end
	if get(0) == "X" then
		add("S")
		cur += 1
	end

	while priLen < limit or secLen < limit do
		if cur >= length then
			break
		end
		local ch = get(cur)
		if VOWEL[ch] then
			if cur == 0 then
				add("A")
			end
			cur += 1
		elseif ch == "B" then
			add("P")
			cur += if get(cur + 1) == "B" then 2 else 1
		elseif ch == "C" then
			if cur > 1 and not vowel(cur - 2) and at(cur - 1, 3, "ACH")
				and get(cur + 2) ~= "I" and (get(cur + 2) ~= "E" or at(cur - 2, 6, "BACHER", "MACHER"))
			then
				add("K")
				cur += 2
			elseif cur == 0 and at(cur, 6, "CAESAR") then
				add("S")
				cur += 2
			elseif at(cur, 4, "CHIA") then
				add("K")
				cur += 2
			elseif at(cur, 2, "CH") then
				if cur > 0 and at(cur, 4, "CHAE") then
					add("K", "X")
				elseif cur == 0 and (at(cur + 1, 5, "HARAC", "HARIS") or at(cur + 1, 3, "HOR", "HYM", "HIA", "HEM"))
					and not at(0, 5, "CHORE")
				then
					add("K")
				elseif (at(0, 4, "VAN ", "VON ") or at(0, 3, "SCH"))
					or at(cur - 2, 6, "ORCHES", "ARCHIT", "ORCHID")
					or at(cur + 2, 1, "T", "S")
					or ((at(cur - 1, 1, "A", "O", "U", "E") or cur == 0)
						and at(cur + 2, 1, "L", "R", "N", "M", "B", "H", "F", "V", "W", " "))
				then
					add("K")
				elseif cur > 0 then
					if at(0, 2, "MC") then
						add("K")
					else
						add("X", "K")
					end
				else
					add("X")
				end
				cur += 2
			elseif at(cur, 2, "CZ") and not at(cur - 2, 4, "WICZ") then
				add("S", "X")
				cur += 2
			elseif at(cur + 1, 3, "CIA") then
				add("X")
				cur += 3
			elseif at(cur, 2, "CC") and not (cur == 1 and get(0) == "M") then
				if at(cur + 2, 1, "I", "E", "H") and not at(cur + 2, 2, "HU") then
					if (cur == 1 and get(cur - 1) == "A") or at(cur - 1, 5, "UCCEE", "UCCES") then
						add("KS")
					else
						add("X")
					end
					cur += 3
				else
					add("K")
					cur += 2
				end
			elseif at(cur, 2, "CK", "CG", "CQ") then
				add("K")
				cur += 2
			elseif at(cur, 2, "CI", "CE", "CY") then
				if at(cur, 3, "CIO", "CIE", "CIA") then
					add("S", "X")
				else
					add("S")
				end
				cur += 2
			else
				add("K")
				if at(cur + 1, 2, " C", " Q", " G") then
					cur += 3
				elseif at(cur + 1, 1, "C", "K", "Q") and not at(cur + 1, 2, "CE", "CI") then
					cur += 2
				else
					cur += 1
				end
			end
		elseif ch == "D" then
			if at(cur, 2, "DG") then
				if at(cur + 2, 1, "I", "E", "Y") then
					add("J")
					cur += 3
				else
					add("TK")
					cur += 2
				end
			elseif at(cur, 2, "DT", "DD") then
				add("T")
				cur += 2
			else
				add("T")
				cur += 1
			end
		elseif ch == "F" then
			cur += if get(cur + 1) == "F" then 2 else 1
			add("F")
		elseif ch == "G" then
			if get(cur + 1) == "H" then
				if cur > 0 and not vowel(cur - 1) then
					add("K")
					cur += 2
				elseif cur == 0 then
					add(if get(cur + 2) == "I" then "J" else "K")
					cur += 2
				elseif (cur > 1 and at(cur - 2, 1, "B", "H", "D"))
					or (cur > 2 and at(cur - 3, 1, "B", "H", "D"))
					or (cur > 3 and at(cur - 4, 1, "B", "H"))
				then
					cur += 2
				else
					if cur > 2 and get(cur - 1) == "U" and at(cur - 3, 1, "C", "G", "L", "R", "T") then
						add("F")
					elseif cur > 0 and get(cur - 1) ~= "I" then
						add("K")
					end
					cur += 2
				end
			elseif get(cur + 1) == "N" then
				if cur == 1 and vowel(0) and not slavo then
					add("KN", "N")
				elseif not at(cur + 2, 2, "EY") and get(cur + 1) ~= "Y" and not slavo then
					add("N", "KN")
				else
					add("KN")
				end
				cur += 2
			elseif at(cur + 1, 2, "LI") and not slavo then
				add("KL", "L")
				cur += 2
			elseif cur == 0
				and (get(cur + 1) == "Y" or at(cur + 1, 2, "ES", "EP", "EB", "EL", "EY", "IB", "IL", "IN", "IE", "EI", "ER"))
			then
				add("K", "J")
				cur += 2
			elseif (at(cur + 1, 2, "ER") or get(cur + 1) == "Y")
				and not at(0, 6, "DANGER", "RANGER", "MANGER")
				and not at(cur - 1, 1, "E", "I")
				and not at(cur - 1, 3, "RGY", "OGY")
			then
				add("K", "J")
				cur += 2
			elseif at(cur + 1, 1, "E", "I", "Y") or at(cur - 1, 4, "AGGI", "OGGI") then
				if (at(0, 4, "VAN ", "VON ") or at(0, 3, "SCH")) or at(cur + 1, 2, "ET") then
					add("K")
				elseif at(cur + 1, 4, "IER ") then
					add("J")
				else
					add("J", "K")
				end
				cur += 2
			else
				cur += if get(cur + 1) == "G" then 2 else 1
				add("K")
			end
		elseif ch == "H" then
			if (cur == 0 or vowel(cur - 1)) and vowel(cur + 1) then
				add("H")
				cur += 2
			else
				cur += 1
			end
		elseif ch == "J" then
			if at(cur, 4, "JOSE") or at(0, 4, "SAN ") then
				if (cur == 0 and get(cur + 4) == " ") or at(0, 4, "SAN ") then
					add("H")
				else
					add("J", "H")
				end
				cur += 1
			else
				if cur == 0 and not at(cur, 4, "JOSE") then
					add("J", "A")
				elseif vowel(cur - 1) and not slavo and (get(cur + 1) == "A" or get(cur + 1) == "O") then
					add("J", "H")
				elseif cur == last then
					add("J", " ")
				elseif not at(cur + 1, 1, "L", "T", "K", "S", "N", "M", "B", "Z") and not at(cur - 1, 1, "S", "K", "L") then
					add("J")
				end
				cur += if get(cur + 1) == "J" then 2 else 1
			end
		elseif ch == "K" then
			cur += if get(cur + 1) == "K" then 2 else 1
			add("K")
		elseif ch == "L" then
			local spanish = false
			if get(cur + 1) == "L" then
				if (cur == length - 3 and at(cur - 1, 4, "ILLO", "ILLA", "ALLE"))
					or ((at(last - 1, 2, "AS", "OS") or at(last, 1, "A", "O")) and at(cur - 1, 4, "ALLE"))
				then
					add("L", " ")
					cur += 2
					spanish = true
				else
					cur += 2
				end
			else
				cur += 1
			end
			if not spanish then
				add("L")
			end
		elseif ch == "M" then
			if (at(cur - 1, 3, "UMB") and (cur + 1 == last or at(cur + 2, 2, "ER"))) or get(cur + 1) == "M" then
				cur += 2
			else
				cur += 1
			end
			add("M")
		elseif ch == "N" then
			cur += if get(cur + 1) == "N" then 2 else 1
			add("N")
		elseif ch == "P" then
			if get(cur + 1) == "H" then
				add("F")
				cur += 2
			else
				cur += if at(cur + 1, 1, "P", "B") then 2 else 1
				add("P")
			end
		elseif ch == "Q" then
			cur += if get(cur + 1) == "Q" then 2 else 1
			add("K")
		elseif ch == "R" then
			if cur == last and not slavo and at(cur - 2, 2, "IE") and not at(cur - 4, 2, "ME", "MA") then
				add("", "R")
			else
				add("R")
			end
			cur += if get(cur + 1) == "R" then 2 else 1
		elseif ch == "S" then
			if at(cur - 1, 3, "ISL", "YSL") then
				cur += 1
			elseif cur == 0 and at(cur, 5, "SUGAR") then
				add("X", "S")
				cur += 1
			elseif at(cur, 2, "SH") then
				if at(cur + 1, 4, "HEIM", "HOEK", "HOLM", "HOLZ") then
					add("S")
				else
					add("X")
				end
				cur += 2
			elseif at(cur, 3, "SIO", "SIA") or at(cur, 4, "SIAN") then
				if not slavo then
					add("S", "X")
				else
					add("S")
				end
				cur += 3
			elseif (cur == 0 and at(cur + 1, 1, "M", "N", "L", "W")) or at(cur + 1, 1, "Z") then
				add("S", "X")
				cur += if at(cur + 1, 1, "Z") then 2 else 1
			elseif at(cur, 2, "SC") then
				if get(cur + 2) == "H" then
					if at(cur + 3, 2, "OO", "ER", "EN", "UY", "ED", "EM") then
						if at(cur + 3, 2, "ER", "EN") then
							add("X", "SK")
						else
							add("SK")
						end
					else
						if cur == 0 and not vowel(3) and get(3) ~= "W" then
							add("X", "S")
						else
							add("X")
						end
					end
					cur += 3
				elseif at(cur + 2, 1, "I", "E", "Y") then
					add("S")
					cur += 3
				else
					add("SK")
					cur += 3
				end
			else
				if cur == last and at(cur - 2, 2, "AI", "OI") then
					add("", "S")
				else
					add("S")
				end
				cur += if at(cur + 1, 1, "S", "Z") then 2 else 1
			end
		elseif ch == "T" then
			if at(cur, 4, "TION") then
				add("X")
				cur += 3
			elseif at(cur, 3, "TIA", "TCH") then
				add("X")
				cur += 3
			elseif at(cur, 2, "TH") or at(cur, 3, "TTH") then
				if at(cur + 2, 2, "OM", "AM") or at(0, 4, "VAN ", "VON ") or at(0, 3, "SCH") then
					add("T")
				else
					add("0", "T")
				end
				cur += 2
			else
				cur += if at(cur + 1, 1, "T", "D") then 2 else 1
				add("T")
			end
		elseif ch == "V" then
			cur += if get(cur + 1) == "V" then 2 else 1
			add("F")
		elseif ch == "W" then
			if at(cur, 2, "WR") then
				add("R")
				cur += 2
			else
				if cur == 0 and (vowel(cur + 1) or at(cur, 2, "WH")) then
					if vowel(cur + 1) then
						add("A", "F")
					else
						add("A")
					end
				end
				if (cur == last and vowel(cur - 1)) or at(cur - 1, 5, "EWSKI", "EWSKY", "OWSKI", "OWSKY") or at(0, 3, "SCH") then
					add("", "F")
					cur += 1
				elseif at(cur, 4, "WICZ", "WITZ") then
					add("TS", "FX")
					cur += 4
				else
					cur += 1
				end
			end
		elseif ch == "X" then
			if not (cur == last and (at(cur - 3, 3, "IAU", "EAU") or at(cur - 2, 2, "AU", "OU"))) then
				add("KS")
			end
			cur += if at(cur + 1, 1, "C", "X") then 2 else 1
		elseif ch == "Z" then
			if get(cur + 1) == "H" then
				add("J")
				cur += 2
			else
				if at(cur + 1, 2, "ZO", "ZI", "ZA") or (slavo and cur > 0 and get(cur - 1) ~= "T") then
					add("S", "TS")
				else
					add("S")
				end
				cur += if get(cur + 1) == "Z" then 2 else 1
			end
		else
			cur += 1
		end
	end

	local p = string.sub(table.concat(pri), 1, limit)
	local s = string.sub(table.concat(sec), 1, limit)
	return p, s
end

-- "PRI" or "PRI/ALT" exactly as the build stores it.
function Metaphone.code(text: string): string
	local p, s = Metaphone.encode(text)
	if p == "" and s == "" then
		return ""
	end
	return if p == s then p else p .. "/" .. s
end

return Metaphone
