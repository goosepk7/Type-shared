-- Plain-language names reach the myth heroes: a player who has never heard "ophanim" can type "wheel of eyes".
return function(t)
	local Resolver = t.load("src/Shared/Resolver")
	local Summon = t.load("src/Shared/Summon")
	Summon.Heroes.setRequirePack(false)
	local CASES = {
		["snake woman"] = "lamia", ["bird woman"] = "harpy", ["giant worm"] = "sandworm", ["desert worm"] = "sandworm",
		["sea horse mount"] = "hippocampus", ["wheel of eyes"] = "ophanim", ["spider centaur"] = "spider centaur", ["half spider"] = "spider centaur", ["drider"] = "spider centaur", ["displacer beast"] = "phase panther",
		["goat sucker"] = "chupacabra", ["tentacle cat"] = "phase panther", ["cosmic horror"] = "eldritch horror",
		["crying beast"] = "squonk", ["giant squid monster"] = "kraken", ["fish lizard"] = "ichthyosaurus",
		["flying cloth"] = "ittan-momen", ["devil horse"] = "jersey devil", ["bug queen"] = "alien queen",
		["crocodile lion"] = "ammit", ["mask beast"] = "taotie", ["bee warrior"] = "bee knight",
	}
	t.test("brand monster names become our own creatures", function()
		for word, hero in { ["phase panther"] = "displacer beast", ["spider centaur"] = "drider" } do
			local r = Resolver.resolveLocal(word)
			t.eq(r.id, word, word .. " is a library word")
			local id = Summon.Heroes.find({ id = word, word = word, category = "Creature" })
			t.eq(id, hero, word .. " keeps its sculpted model")
		end
	end)
	t.test("everyday phrases resolve to the myth words and their hero models", function()
		for phrase, word in CASES do
			local r = Resolver.resolveLocal(phrase)
			t.eq(r.id, word, phrase .. " -> word")
		end
	end)
end
