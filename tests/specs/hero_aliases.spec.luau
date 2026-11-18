-- Plain-language names reach the myth heroes: a player who has never heard "ophanim" can type "wheel of eyes".
return function(t)
	local Resolver = t.load("src/Shared/Resolver")
	local Summon = t.load("src/Shared/Summon")
	Summon.Heroes.setRequirePack(false)
	local CASES = {
		["snake woman"] = "lamia", ["bird woman"] = "harpy", ["giant worm"] = "sandworm", ["desert worm"] = "sandworm",
		["sea horse mount"] = "hippocampus", ["wheel of eyes"] = "ophanim", ["spider centaur"] = "drider",
		["goat sucker"] = "chupacabra", ["tentacle cat"] = "displacer beast", ["cosmic horror"] = "eldritch horror",
		["crying beast"] = "squonk", ["giant squid monster"] = "kraken", ["fish lizard"] = "ichthyosaurus",
		["flying cloth"] = "ittan-momen", ["devil horse"] = "jersey devil", ["bug queen"] = "alien queen",
		["crocodile lion"] = "ammit", ["mask beast"] = "taotie", ["bee warrior"] = "bee knight",
	}
	t.test("everyday phrases resolve to the myth words and their hero models", function()
		for phrase, word in CASES do
			local r = Resolver.resolveLocal(phrase)
			t.eq(r.id, word, phrase .. " -> word")
		end
	end)
end
