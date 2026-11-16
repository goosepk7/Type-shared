--!strict
-- MeshLibrary: sculpted MeshPart pieces (tools/meshgen, data/mesh_assets.json -> Meshes/MeshAssets.luau).
-- Shared by the Summon builder and by games built on WordEngine (Type-defend's enemy Kit uses the same API).
--
-- SERVER   MeshLibrary.start(filter?, { priority = { "core_", "prop_" } }?) loads the manifest entries with
--          InsertService:LoadAsset (MeshLibrary.MAX_PARALLEL at a time, retries with backoff), renames each
--          MeshPart to its pieceId, stamps NativeSize / Origin / Kind attributes and parents the templates to
--          ReplicatedStorage[MeshLibrary.FolderName]. It returns at once and may be called again for more ids.
-- CLIENT   never loads assets (start/preload only watch the folder): templates are picked up from the
--          replicated folder on demand and as they arrive.
-- OFFLINE  tools and tests register stand-in templates with MeshLibrary.register().
--
--   MeshLibrary.get(pieceId, size, cframe, color?, material?) -> MeshPart?
--       clone of a "box" piece resized to `size` (a MeshPart scales its mesh to its Size, exactly like the
--       primitive Part it replaces). nil when the piece is not loaded: callers fall back.
--   MeshLibrary.place(pieceId, frame, scale, color?, material?) -> MeshPart?
--       "anchor" / "unit" pieces authored in anchor units: Size = native size * scale and
--       CFrame = frame * (origin * scale). `scale` is a number or (addition) a Vector3 for per-axis scale.
--   MeshLibrary.fit(pieceId, size, cframe, color?, material?) -> MeshPart?            (addition)
--       put any piece in a primitive's box: "box" pieces fill it (same as get); "unit" pieces are authored in
--       the box's unit frame and may reach outside it (Size = native * size, CFrame = cframe * (origin * size)).
--   MeshLibrary.has(pieceId) / MeshLibrary.info(pieceId) -> { size, origin, kind }?
--   MeshLibrary.record(pieceId) -> manifest record? (addition; available whether or not the asset is loaded)
--   MeshLibrary.ready() -> { isReady: () -> boolean, Wait: () -> (), Connect: (fn) -> () }
--   MeshLibrary.register(pieceId, template, info?) / clear() / setDisabled(on)
--   MeshLibrary.live() -> boolean    (addition) false offline, where nothing can ever load
--   MeshLibrary.addAssets(records)   (addition) merge extra manifest records (a game's own pieces) before start
--   MeshLibrary.setRuntime(rt)       (addition) inject Roblox datatypes (tests under Lune's @lune/roblox)
--
-- Every clone is CanCollide/CanQuery/CanTouch off and Massless. Verified on a live server
-- (tools/meshgen/README.md): LoadAsset works for group-owned assets, 1 glTF unit = 1 stud, vertex colours
-- (baked AO) survive import, the importer turns the mesh 180 degrees about Y (the exporter pre-compensates).

local MeshLibrary = {}

export type Info = { size: Vector3, origin: Vector3, kind: string }
export type Ready = { isReady: () -> boolean, Wait: () -> (), Connect: (fn: () -> ()) -> () }

MeshLibrary.FolderName = "WE_Meshes"
local templates: { [string]: BasePart? } = {}
local infos: { [string]: Info } = {}
local readyFlag = false
local waiters: { () -> () } = {}
local started = false
local disabled = false
local folderHooked = false
local lastFolderTry = -math.huge
local extra: { [string]: any } = {}
local manifest: { [string]: any }? = nil

local RT: any = nil
function MeshLibrary.setRuntime(rt: any)
	RT = rt
end
local function V3(): any
	return if RT then RT.Vector3 else Vector3
end
local function CF(): any
	return if RT then RT.CFrame else CFrame
end

local function v3(t: any): Vector3
	if type(t) == "table" then
		return V3().new(tonumber(t[1]) or 0, tonumber(t[2]) or 0, tonumber(t[3]) or 0)
	end
	if t ~= nil and type(t) ~= "number" then
		return t
	end
	return V3().new(0, 0, 0)
end

local function loadManifest(): { [string]: any }
	if manifest == nil then
		local ok, data = pcall(function(): any
			return (require :: any)((script :: any).Parent.MeshAssets)
		end)
		local m: { [string]: any } = {}
		if ok and type(data) == "table" then
			for id, rec in data do
				m[id] = rec
			end
		end
		for id, rec in extra do
			m[id] = rec
		end
		manifest = m
	end
	return manifest :: { [string]: any }
end

-- Merge extra manifest records ({ [pieceId] = { assetId, size, origin, tris, kind } }). Call before start().
function MeshLibrary.addAssets(records: { [string]: any })
	for id, rec in records do
		extra[id] = rec
		if manifest then
			manifest[id] = rec
		end
	end
end

function MeshLibrary.record(pieceId: string): any?
	return loadManifest()[pieceId]
end

local function markReady()
	if readyFlag then
		return
	end
	readyFlag = true
	local list = waiters
	waiters = {}
	for _, fn in list do
		task.spawn(fn)
	end
end

-- Register a template (server loader, client folder watcher, offline tools). The template is never
-- parented by this call. info falls back to the template's attributes, then to the manifest record.
function MeshLibrary.register(pieceId: string, template: BasePart, info: { size: any?, origin: any?, kind: string? }?)
	templates[pieceId] = template
	local rec = loadManifest()[pieceId]
	local function attr(name: string): any
		local ok, v = pcall(function(): any
			return template:GetAttribute(name)
		end)
		return if ok then v else nil
	end
	local size = if info and info.size then v3(info.size) else (attr("NativeSize") or (if rec then v3(rec.size) else template.Size))
	local origin = if info and info.origin then v3(info.origin) else (attr("Origin") or (if rec then v3(rec.origin) else v3(nil)))
	local kind = (info and info.kind) or attr("Kind") or (rec and rec.kind) or "box"
	infos[pieceId] = { size = size, origin = origin, kind = kind }
end

-- Forget everything (tests / the offline renderer's "before" pass).
function MeshLibrary.clear()
	templates = {}
	infos = {}
end

-- Turn mesh use off entirely (fallback to primitive parts everywhere); used for A/B renders.
function MeshLibrary.setDisabled(on: boolean)
	disabled = on
end

local function gameAny(): any
	return game
end

local function isLive(): boolean
	return typeof(gameAny()) == "Instance"
end

-- true inside a running Roblox DataModel (false under Lune and other offline tools: nothing will ever load).
function MeshLibrary.live(): boolean
	return isLive()
end

local function hookFolder()
	if folderHooked or not isLive() then
		return
	end
	local now = os.clock()
	if now - lastFolderTry < 1 then
		return
	end
	lastFolderTry = now
	local ok, folder = pcall(function(): Instance?
		return gameAny():GetService("ReplicatedStorage"):FindFirstChild(MeshLibrary.FolderName)
	end)
	if not ok or not folder then
		return
	end
	folderHooked = true
	local function add(c: Instance)
		if c:IsA("BasePart") and templates[c.Name] == nil then
			MeshLibrary.register(c.Name, c)
		end
	end
	for _, c in folder:GetChildren() do
		add(c)
	end
	folder.ChildAdded:Connect(add)
	if folder:GetAttribute("Ready") then
		markReady()
	else
		folder:GetAttributeChangedSignal("Ready"):Connect(function()
			if folder:GetAttribute("Ready") then
				markReady()
			end
		end)
	end
end

function MeshLibrary.has(pieceId: string): boolean
	if disabled then
		return false
	end
	if templates[pieceId] == nil then
		hookFolder()
	end
	return templates[pieceId] ~= nil
end

function MeshLibrary.info(pieceId: string): Info?
	if not MeshLibrary.has(pieceId) then
		return nil
	end
	return infos[pieceId]
end

local function clone(pieceId: string, size: Vector3, cf: CFrame, color: Color3?, material: Enum.Material?): BasePart?
	if not MeshLibrary.has(pieceId) then
		return nil
	end
	local t = templates[pieceId] :: BasePart
	local ok, p = pcall(function(): Instance?
		return t:Clone()
	end)
	if not ok or not p then
		return nil
	end
	local part = p :: BasePart
	part.Name = pieceId
	part.Size = size
	part.CFrame = cf
	if color then
		part.Color = color
	end
	if material then
		part.Material = material
	end
	part.Anchored = false
	part.CanCollide = false
	part.CanQuery = false
	part.CanTouch = false
	part.Massless = true
	part:SetAttribute("MeshPiece", pieceId)
	return part
end

function MeshLibrary.get(pieceId: string, size: Vector3, cframe: CFrame, color: Color3?, material: Enum.Material?): BasePart?
	return clone(pieceId, size, cframe, color, material)
end

function MeshLibrary.place(pieceId: string, frame: CFrame, scale: number | Vector3, color: Color3?, material: Enum.Material?): BasePart?
	local info = MeshLibrary.info(pieceId)
	if not info then
		return nil
	end
	local s: any = scale
	return clone(pieceId, info.size * s, frame * CF().new(info.origin * s), color, material)
end

function MeshLibrary.fit(pieceId: string, size: Vector3, cframe: CFrame, color: Color3?, material: Enum.Material?): BasePart?
	local info = MeshLibrary.info(pieceId)
	if not info then
		return nil
	end
	if info.kind == "unit" then
		return clone(pieceId, info.size * size, cframe * CF().new(info.origin * size), color, material)
	end
	return clone(pieceId, size, cframe, color, material)
end

function MeshLibrary.ready(): Ready
	return {
		isReady = function()
			hookFolder()
			return readyFlag
		end,
		Wait = function()
			hookFolder()
			if readyFlag then
				return
			end
			local th = coroutine.running()
			table.insert(waiters, function()
				task.spawn(th)
			end)
			coroutine.yield()
		end,
		Connect = function(fn: () -> ())
			hookFolder()
			if readyFlag then
				task.spawn(fn)
			else
				table.insert(waiters, fn)
			end
		end,
	}
end

-- Parallel InsertService loads. 12 made a cold load of ~700 pieces take about 40 s; games may raise or lower it.
MeshLibrary.MAX_PARALLEL = 24

local function isServer(): boolean
	if not isLive() then
		return false
	end
	local ok, v = pcall(function(): boolean
		return gameAny():GetService("RunService"):IsServer()
	end)
	return ok and v == true
end

local requested: { [string]: boolean } = {}
local queue: { string } = {}
local pending = 0
local failed = 0
local running = 0
local loadFolder: any = nil

local function finishOne()
	pending -= 1
	if pending <= 0 and loadFolder then
		loadFolder:SetAttribute("Failed", failed)
		loadFolder:SetAttribute("Ready", true)
		if failed > 0 then
			warn(("[MeshLibrary] %d pieces failed to load (parts fallback)"):format(failed))
		end
		markReady()
	end
end

local function loadOne(id: string)
	local rec = loadManifest()[id]
	local InsertService = gameAny():GetService("InsertService")
	local mesh: BasePart? = nil
	for attempt = 1, 4 do
		local ok, model = pcall(function(): Instance?
			return InsertService:LoadAsset(rec.assetId)
		end)
		if ok and model then
			for _, d in model:GetDescendants() do
				if d:IsA("MeshPart") then
					mesh = d
					break
				end
			end
			if mesh then
				(mesh :: BasePart).Parent = nil
			end
			model:Destroy()
			break
		end
		task.wait(0.5 * 2 ^ attempt)
	end
	if mesh then
		local m = mesh :: BasePart
		m.Name = id
		m.Anchored = true
		m.CanCollide = false
		m.CanQuery = false
		m.CanTouch = false
		m.CastShadow = true
		m:SetAttribute("NativeSize", v3(rec.size))
		m:SetAttribute("Origin", v3(rec.origin))
		m:SetAttribute("Kind", rec.kind or "box")
		m:SetAttribute("Tris", rec.tris)
		MeshLibrary.register(id, m, rec)
		m.Parent = loadFolder
	else
		failed += 1
	end
end

local function pump()
	while running < math.max(1, MeshLibrary.MAX_PARALLEL) and #queue > 0 do
		local id = table.remove(queue, 1) :: string
		running += 1
		task.spawn(function()
			local ok, err = pcall(loadOne, id)
			if not ok then
				failed += 1
				warn("[MeshLibrary] " .. id .. ": " .. tostring(err))
			end
			running -= 1
			finishOne()
			pump()
		end)
	end
end

export type StartOptions = {
	-- load order: id prefixes, earlier first ({ "core_", "prop_" }), or a function (lower number loads first).
	-- Ids that match nothing load last, alphabetically.
	priority: ({ string } | (id: string, record: any) -> number)?,
}

-- SERVER ONLY: load manifest pieces (all, or those `filter(id, record)` accepts) into
-- ReplicatedStorage[FolderName]. Call it again at any time to add more ids (a different filter, or after
-- addAssets); ready() is true only while nothing is pending. On a client this never loads anything: it only
-- watches the replicated folder. Returns at once; ready():Wait() yields until the pieces are in.
function MeshLibrary.start(filter: ((string, any) -> boolean)?, opts: StartOptions?)
	if not isLive() then
		return
	end
	if not isServer() then
		hookFolder()
		return
	end
	started = true
	if loadFolder == nil then
		local RS = gameAny():GetService("ReplicatedStorage")
		local folder = RS:FindFirstChild(MeshLibrary.FolderName) or Instance.new("Folder")
		folder.Name = MeshLibrary.FolderName
		folder.Parent = RS
		loadFolder = folder
		folderHooked = true
	end
	local data = loadManifest()
	local ids: { string } = {}
	for id, rec in data do
		if not requested[id] and type(rec) == "table" and rec.assetId and (filter == nil or filter(id, rec)) then
			table.insert(ids, id)
		end
	end
	if #ids == 0 then
		if pending <= 0 then
			loadFolder:SetAttribute("Ready", true)
			markReady()
		end
		return
	end
	local prio = opts and opts.priority
	local function rankOf(id: string): number
		if type(prio) == "function" then
			return tonumber(prio(id, data[id])) or math.huge
		elseif type(prio) == "table" then
			for i, prefix in prio do
				if string.sub(id, 1, #prefix) == prefix then
					return i
				end
			end
		end
		return math.huge
	end
	local ranks: { [string]: number } = {}
	for _, id in ids do
		ranks[id] = rankOf(id)
	end
	table.sort(ids, function(a, b)
		if ranks[a] ~= ranks[b] then
			return ranks[a] < ranks[b]
		end
		return a < b
	end)
	readyFlag = false
	loadFolder:SetAttribute("Ready", false)
	for _, id in ids do
		requested[id] = true
		pending += 1
		table.insert(queue, id)
	end
	pump()
end

-- Same as start (kept for callers that used the old non-yielding entry point). Safe on a client: no-op there
-- apart from watching the replicated folder.
function MeshLibrary.preload(filter: ((string, any) -> boolean)?, opts: StartOptions?)
	MeshLibrary.start(filter, opts)
end

-- All manifest records ({ [pieceId] = { assetId, size, origin, tris, kind } }), including addAssets ones.
function MeshLibrary.records(): { [string]: any }
	return loadManifest()
end

return MeshLibrary
