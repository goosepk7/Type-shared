--!strict
-- WordEngine tunables. Each section is owned by one subsystem; games override with Config.set(path, value)
-- at startup (before WordEngineServer.start). Keep values here meaning-level, not game balance.

local Config = {}

-- [Speller] owned by Normalizer/Speller/Library/Modifiers
Config.Speller = {
	CacheSize = 512, -- LRU of normalized input -> SpellResult (per client / per server)
	UnknownBelow = 0.6, -- Resolver.resolveLocal returns the Fallback blob below this confidence (DESIGN §5 bands)
	SilentAbove = 0.9, -- >= this: no "did you mean" chip
	-- max weighted edit cost accepted by fuzzy matching, by typed length (short words are stricter)
	FuzzyMaxCost = { 0, 0, 0.65, 1.05, 1.3, 1.6, 1.9, 2.1, 2.3, 2.5, 2.6, 2.8 }, -- index = length, last entry = longer
	PhoneticExtraCost = 1.6, -- phonetic matches may exceed the fuzzy threshold by this much
	FuzzyCandidates = 48, -- q-gram candidates scored with the full weighted distance
	MaxTokens = 10, -- phrase parser token cap; the rest become extras
	ExtraPenalty = 0.72, -- confidence multiplier per unplaced token
}
Config.Modifiers = {
	MaxModifiers = 6, -- applied per result (DESIGN §5a: at least 4 stack); extra ones are dropped
	MaxPowerDelta = 3, -- total |power| change from all modifiers + material
	MaxSpeedDelta = 3,
	MaxDurabilityDelta = 3,
	MaxSizeSteps = 3, -- net size steps (Tiny..Colossal)
	SizePowerPerStep = 0.5, -- bigger hits harder (counted inside MaxPowerDelta)
	MaxCount = 12, -- == Schema.Limits.MaxCount
	MaterialStatCap = 2, -- per-stat cap on a material's statHints
	MaxAccents = 8,
	ElementTint = 0.55, -- how far an element modifier pulls primary colour toward the element palette
	SecondaryElementTint = 0.3,
	MaterialTint = 0.85, -- material palette strength (0.5 when a Quality/State colour was also applied)
}

-- [AI] owned by Server/AI + Interpreter + Cache
Config.AI = {
	Enabled = true, -- static switch; the LIVE kill switch is the DataStore flag (see AI.setKillSwitch)
	Provider = "Anthropic", -- "Anthropic" | "OpenAICompatible" | "Mock" (Mock is automatic in Studio without a secret)
	SecretName = "ANTHROPIC_API_KEY", -- Secrets Store name, domain api.anthropic.com (start({aiSecretName}) overrides)
	MockInStudio = true, -- Studio play-solo has no Secrets: use the canned Mock provider (loud log line)
	Threshold = 0.8, -- library confidence below this asks the AI (DESIGN §5). 0.7-0.8 fuzzy hits are wrong ~1 in 3, so they get a second opinion
	InstantTimeout = 1.5, -- seconds interpretAsync may yield before returning its best guess
	BatchWindow = 0.12, -- seconds to gather queued words into one request
	MaxBatch = 8, -- words per request
	MaxConcurrent = 2, -- in-flight provider requests per server
	MaxRequestsPerMinute = 60, -- per server (HttpService allows 500/min for all non-Open-Cloud requests)
	MaxQueue = 64, -- pending words; beyond this new words skip AI
	MaxRetries = 2,
	BackoffBase = 1, -- seconds, doubled per retry (+ jitter); retry-after header wins when present
	BackoffMax = 8,
	NewPhrasePerMinute = 6, -- per player: NEW phrases that may reach the AI (separate from the typing limit)
	DailyBudgetUSD = 5, -- per game per UTC day, from returned token usage (MemoryStore counter)
	LockTTL = 20, -- seconds: cross-server per-phrase AI lock (MemoryStore)
	LockWait = 12, -- seconds a second server waits for the lock holder's result before trying itself
	LockPoll = 0.5,
	ControlStore = "WordEngine_Control_v1", -- DataStore with the live kill switch ({ aiEnabled = bool })
	ControlTopic = "WordEngineControl", -- MessagingService topic for instant kill-switch flips
	ControlPoll = 30, -- seconds between kill-switch polls
	Circuit = { FailureThreshold = 4, Cooldown = 20, MaxCooldown = 300, AuthCooldown = 900 },
	Anthropic = {
		Endpoint = "https://api.anthropic.com/v1/messages",
		Model = "claude-haiku-5-5",
		ApiVersion = "2026-10-21",
		Effort = "low",
		DisableThinking = true, -- Haiku 5.5 accepts thinking {type="disabled"} at effort high or below
		OutputMode = "tool", -- "tool": forced tool_choice + strict JSON-schema tool; "json_schema": output_config.format
		MaxTokensBase = 150,
		MaxTokensPerWord = 340,
	},
	OpenAICompatible = {
		Endpoint = "", -- e.g. a /v1/chat/completions URL; set Model too
		Model = "",
		MaxTokensBase = 150,
		MaxTokensPerWord = 340,
	},
	Mock = { Latency = 0.3 }, -- seconds; canned results so play-solo exercises the whole pipeline
	-- USD per million tokens (claude-haiku-5-5, prompts <= 100K tokens). Cache reads 0.1x, 5-min cache writes 1.25x.
	Pricing = { InputPerMTok = 0.10, OutputPerMTok = 0.50, CacheReadMultiplier = 0.1, CacheWriteMultiplier = 1.25 },
	FewShotIds = {
		"dragon", "tornado", "asteroid", "rubber duck", "shark", "fireball", "black hole", "cat", "sword", "tank",
		"cupcake", "phoenix", "robot", "volcano",
	},
	SpendRefreshInterval = 10, -- seconds between reads of the cross-server spend counter
}
Config.Cache = {
	Enabled = true,
	DataStoreName = "WordEngine_WordCache_v1", -- permanent cache (per game; tools/promote.py merges both games)
	UnknownStore = "WordEngine_Unknown_v1", -- OrderedDataStore: unknown/fallback phrases -> count (coverage report)
	PlaysOrderedStore = "WordEngine_AIWordPlays_v1", -- AI/cached phrase -> plays (promotion review)
	HotMapName = "WordEngine_WordCacheHot_v1", -- MemoryStore sorted map (hot cache + AI locks + spend counter)
	HotTTL = 7 * 24 * 3600, -- seconds (MemoryStore max is 45 days)
	HotRefreshAfter = 24 * 3600, -- re-set the hot item on a hit at most once a day
	LocalSize = 3000, -- per-server memory LRU entries
	NegativeTTL = 120, -- seconds a per-server "not in remote cache" memo lives
	FlushInterval = 30, -- play counts, unknown phrases, pending writes
	MaxFlushKeys = 20, -- DataStore writes per flush per kind
	WriteRetries = 3, -- immediate retries for a paid AI result before it goes to the retry queue
}

-- [Safety] owned by Server/Safety
Config.Safety = {
	MaxLength = 40, -- characters (Schema.Limits.MaxWord)
	RateCapacity = 6, -- typing limit: token bucket burst per player
	RateRefill = 2, -- tokens per second
	RepeatWindow = 8, -- seconds
	RepeatMax = 10, -- identical inputs inside the window before it is treated as spam
	SpamCooldown = 4, -- seconds of Fallback after spam is detected
	FilterCacheSeconds = 60,
	NetCapacity = 12, -- raw remote invocations per player (burst), checked before Safety
	NetRefill = 5,
}

-- [Visual] owned by Summon + Effects
Config.Visual = {
	Inset = 0.02, -- studs: touching parts are inset so faces never coincide (no z-fighting)
	DecalOffset = 0.01,
	-- Summon (src/Shared/Summon): per-summon budgets, DESIGN.md §8. Visible parts only (the invisible root is extra).
	SummonPartBudget = { Tiny = 8, Small = 12, Medium = 20, Large = 30, Huge = 40, Colossal = 40 },
	SummonSignatureBonus = 0.25, -- hand-built signature summons may use up to +25% parts
	SummonEmitterBudget = { Solid = 2, Spectral = 3 },
	SummonEffectBudget = { Solid = 2, Spectral = 3 }, -- looping Effects.play attachments (accents + material particles)
	SummonMaxParticleRate = 60, -- particles/sec per emitter
	SummonMaxTrails = 4,
	SummonMaxLights = 1,
	SummonHeight = { Tiny = 1.6, Small = 3, Medium = 5, Large = 8, Huge = 13, Colossal = 20 }, -- studs, before opts.scale
	SummonSpectralCoreScale = 0.6, -- inner Neon core size vs its ForceField shell (strictly inside)
	SummonSpectralHighlight = true, -- rim glow via Highlight (engine caps ~31 active Highlights per client)
	SummonFormationBudgetScale = 2, -- a formation may spend this many single-summon budgets in total
	SummonFormationMinParts = 5, -- each formation member keeps at least this many parts
	SummonAnimLodNear = 120, -- studs: full-rate animation inside this camera distance
	SummonAnimLodFar = 260, -- beyond this, update every 6th frame (between: every 2nd)
	SummonAnimCull = 600, -- beyond this, animation is paused

	-- Effects (src/Shared/Effects), owned by Effects. See docs/EFFECTS.md for what each budget means.
	Effects = {
		-- Ground-hugging layers (scorch decals, shockwave discs, pools) take rotating height slots so two
		-- overlapping ground layers never share a plane: y = ground + DecalOffset * slot, slot in 1..GroundSlots.
		GroundSlots = 24,
		ShellRatio = 1.25, -- nested glow shells: each radius >= previous * ShellRatio (never coincident)
		-- Quality tier per device class. Auto-degrade steps DOWN from this and back up to it, never above.
		DeviceTier = { Desktop = "High", Console = "High", Tablet = "Medium", Phone = "Medium" },
		Quality = "Auto", -- "Auto" | "Ultra" | "High" | "Medium" | "Low" (settings menus may force one)
		-- Hard budgets per tier for all live effects combined. particleScale multiplies every emitter Rate and
		-- burst count; detail gates optional layers (3 = everything, 1 = essentials only).
		Budgets = {
			Ultra = { maxEffects = 64, maxParts = 360, maxEmitters = 140, maxBeams = 64, maxTrails = 32, maxLights = 16, maxHighlights = 8, particleScale = 1.0, detail = 3, flipbooks = true },
			High = { maxEffects = 48, maxParts = 260, maxEmitters = 100, maxBeams = 48, maxTrails = 24, maxLights = 10, maxHighlights = 6, particleScale = 0.85, detail = 3, flipbooks = true },
			Medium = { maxEffects = 32, maxParts = 160, maxEmitters = 64, maxBeams = 28, maxTrails = 14, maxLights = 5, maxHighlights = 3, particleScale = 0.6, detail = 2, flipbooks = true },
			Low = { maxEffects = 18, maxParts = 80, maxEmitters = 32, maxBeams = 14, maxTrails = 6, maxLights = 2, maxHighlights = 0, particleScale = 0.35, detail = 1, flipbooks = false },
		},
		TierOrder = { "Low", "Medium", "High", "Ultra" },
		-- Priority 2+ (the local player's own casts) may exceed a budget by this factor; priority 0 (ambient,
		-- far away) is refused once any budget is past LowPriorityCutoff.
		PriorityOverflow = 1.25,
		LowPriorityCutoff = 0.7,
		-- Auto-degrade on low FPS (client): EMA of frame time with hysteresis.
		AutoDegrade = { Enabled = true, DowngradeFps = 40, CriticalFps = 24, UpgradeFps = 56, DowngradeAfter = 2.5, UpgradeAfter = 12, Smoothing = 0.1 },
		CullDistance = 450, -- studs from the camera; farther effects are skipped (the handle still works)
		MaxStatusesPerTarget = 4,
		PoolPrewarm = { Part = 24, Emitter = 24, Beam = 8, Light = 4 },
		PoolMaxIdle = { Part = 220, Emitter = 140, Beam = 48, Trail = 24, Light = 16, Highlight = 8 },
		AllowServer = false, -- Effects are client-side; on the server play() returns an inert handle unless true
	},
}

-- [Services] owned by Data/WordBook/Currency/Purchases/Analytics/Admin/UI
Config.Services = {
	Data = {
		StoreName = "WordEngine_Player_v1",
		KeyPrefix = "u_",
		AutosaveSeconds = 90, -- also refreshes the session lock timestamp
		LockStaleSeconds = 330, -- a lock untouched this long is dead (3 missed autosaves + slack)
		LockWaitSeconds = 12, -- after asking the holder to release, steal once this has passed
		RetryAttempts = 6,
		RetryBaseSeconds = 1,
		RetryMaxSeconds = 16,
		MinBudget = 2, -- keep this much request budget spare for releases/receipts
		WarnBytes = 3_000_000, -- DataStore value limit is 4,194,304 bytes
		ReceiptHistory = 64, -- purchase ids remembered per player for idempotency
		ReleaseTopic = "WordEngine_ReleaseLock",
	},
	WordBook = {
		MaxEntries = 1500, -- distinct words kept per player
		EvictBatch = 75, -- evict this many at once when over the cap
		UseBonusSeconds = 21_600, -- each use counts as 6h of recency when ranking for eviction
		MaxUseBonus = 30, -- uses beyond this don't protect further
	},
	Currency = {
		MaxBalance = 1_000_000_000_000,
		LedgerSize = 20, -- last N transactions kept per player for support
	},
	Purchases = {
		GamePassCacheSeconds = 600,
		ReceiptStoreName = "WordEngine_Receipts_v1", -- cross-check store for granted receipts
	},
	Analytics = {
		Enabled = true,
		RollupStoreName = "WordEngine_Analytics_v1",
		TopWordsStoreName = "WordEngine_TopWords_v1", -- OrderedDataStore, one per game namespace (scope)
		FlushSeconds = 120,
		MaxPendingWords = 400,
		TopWordsFlushPerCycle = 40, -- OrderedDataStore write budget is lower (30 + 5/player)
		UnknownStoreName = "WordEngine_Unknown_v1", -- OrderedDataStore: normalized unknown phrase -> count
		UnknownFlushPerCycle = 30,
		MaxPendingUnknown = 300,
	},
	Admin = {
		UserIds = {} :: { number }, -- add Roblox user ids; Studio owner is always admin in Studio
		GroupId = 0, -- optional: group rank gate
		MinGroupRank = 254,
		StoreName = "WordEngine_Admin_v1",
		AuditStoreName = "WordEngine_Audit_v1",
		Topic = "WordEngine_Admin",
		CommandPrefix = "/we",
		MaxActionsPerMinute = 30,
	},
}

Config.UI = {
	FontFamily = "rbxasset://fonts/families/BuilderSans.json",
	DisplayFamily = "rbxasset://fonts/families/BuilderExtended.json",
	MonoFamily = "rbxasset://fonts/families/BuilderMono.json",
	MinTouch = 48, -- px, every tappable target is at least this
	AutocompleteMinChars = 2,
	AutocompleteLimit = 4,
	DidYouMeanMin = 0.6, -- confidence band that shows the chip (DESIGN.md §5)
	DidYouMeanMax = 0.9,
	ToastSeconds = 3,
	ToastMax = 3,
	RevealSeconds = 2.2,
	HotbarSlotsMin = 3,
	HotbarSlotsMax = 5,
	ReducedMotion = false, -- settings panel toggles per player
}

function Config.set(path: string, value: any)
	local node: any = Config
	local parts = string.split(path, ".")
	for i = 1, #parts - 1 do
		node = node[parts[i]]
		assert(type(node) == "table", "Config.set: bad path " .. path)
	end
	node[parts[#parts]] = value
end

return Config
