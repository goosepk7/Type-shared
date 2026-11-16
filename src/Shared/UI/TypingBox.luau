--!strict
-- TypingBox: the word-entry bar shared by both games.
--
--   local box = UI.TypingBox.new({ parent = hud, placeholder = "Type a spell...", submitLabel = "CAST" })
--   box.Submitted:Connect(function(text, meta) local r = WordEngine.Net.interpret(text); box:setResult(r) end)
--   box.CorrectionAccepted:Connect(function(word, original) ... end)
--
-- * Autocomplete chips from Suggest.prefix(prefix, wordBook, limit) once Config.UI.AutocompleteMinChars
--   letters are typed (falls back to Library.prefixSearch). Tap or Tab completes the last word.
-- * "Did you mean" chip (one tap) when a WordResult's correction confidence is in the 0.6..0.9 band,
--   plus up to 3 alternative chips; accepting re-submits the corrected word (configurable).
-- * Mobile first: 56px bar, 48px+ targets, lifts above the on-screen keyboard, safe-area aware parent.
-- * Keyboard: "/" or Enter focuses, Enter submits, Tab accepts the highlighted chip, Esc clears.
--   Gamepad: ButtonY focuses (opens the console keyboard); chips are Selectable for D-pad navigation.

local Theme = require(script.Parent.Theme)
local Kit = require(script.Parent.Kit)
local Signal = require(script.Parent.Signal)

local TypingBox = {}
TypingBox.__index = TypingBox

export type Options = {
	parent: Instance?,
	placeholder: string?,
	submitLabel: string?,
	accent: Color3?,
	position: UDim2?,
	anchor: Vector2?,
	width: number?, -- max width in px (scales down to fit phones)
	suggest: ((prefix: string, limit: number) -> { string })?,
	wordBook: ({ string } | () -> { string })?,
	autoResubmitCorrection: boolean?,
	chipSubmits: boolean?, -- tapping an autocomplete chip also submits (default: false)
	keepFocus: boolean?, -- refocus after submit (default: true on keyboard devices, false on touch)
	maxLength: number?,
	zIndex: number?,
	clearOnSubmit: boolean?, -- default true
}

local function uiCfg(): any
	local ok, c = pcall(function()
		return (require(script.Parent.Parent.Config) :: any).UI
	end)
	return if ok and c then c else {}
end

local function engine(): any?
	local ok, e = pcall(function()
		return require(script.Parent.Parent) :: any
	end)
	return if ok then e else nil
end

local function defaultSuggest(wordBook: any): (string, number) -> { string }
	return function(prefix: string, limit: number): { string }
		local e = engine()
		if not e then
			return {}
		end
		local book = if type(wordBook) == "function" then wordBook() else wordBook
		local ok, list = pcall(function()
			return e.Suggest.prefix(prefix, book or {}, limit)
		end)
		if ok and type(list) == "table" then
			return list
		end
		ok, list = pcall(function()
			return e.Library.prefixSearch(prefix, limit)
		end)
		return if ok and type(list) == "table" then list else {}
	end
end

local function trim(s: string): string
	return (string.match(s, "^%s*(.-)%s*$") or "")
end

local function lastToken(s: string): (string, string)
	local head, tail = string.match(s, "^(.-)(%S*)$")
	return head or "", tail or s
end

function TypingBox.new(opts: Options?): any
	local o: Options = opts or {}
	local T = Theme.get()
	local cfg = uiCfg()
	local UIS = game:GetService("UserInputService")
	local accent = o.accent or T.Color.Brand
	local z = o.zIndex or Theme.Z.hud
	local maxLen = o.maxLength or 40
	local touch = UIS.TouchEnabled and not UIS.KeyboardEnabled

	local self: any = setmetatable({}, TypingBox)
	self.Submitted = Signal.new() -- (text, meta { fromCorrection: boolean?, fromChip: boolean? })
	self.CorrectionAccepted = Signal.new() -- (word, original)
	self.Changed = Signal.new() -- (text)
	self._conns = {}
	self._suggestions = {} :: { string }
	self._enabled = true
	self._suggest = o.suggest or defaultSuggest(o.wordBook)
	self._accent = accent
	self._keepFocus = if o.keepFocus == nil then not touch else o.keepFocus
	self._opts = o

	local width = o.width or 620
	local root: Frame = Kit.new("Frame", {
		Name = "WordEngineTypingBox",
		BackgroundTransparency = 1,
		AnchorPoint = o.anchor or Vector2.new(0.5, 1),
		Position = o.position or UDim2.new(0.5, 0, 1, -112),
		Size = UDim2.new(1, -32, 0, 0),
		AutomaticSize = Enum.AutomaticSize.Y,
		ZIndex = z,
	}, {
		Kit.new("UISizeConstraint", { MaxSize = Vector2.new(width, math.huge) }),
		Kit.list(Enum.FillDirection.Vertical, Theme.Space.sm, Enum.HorizontalAlignment.Center, Enum.VerticalAlignment.Bottom),
	})
	self.root = root
	self._basePos = root.Position

	-- Row 1: did-you-mean
	local dym: Frame = Kit.new("Frame", {
		Name = "DidYouMean",
		BackgroundTransparency = 1,
		Size = UDim2.new(1, 0, 0, Theme.MinTouch),
		Visible = false,
		LayoutOrder = 1,
		ZIndex = z + 2,
		Parent = root,
	}, { Kit.list(Enum.FillDirection.Horizontal, Theme.Space.sm, Enum.HorizontalAlignment.Center, Enum.VerticalAlignment.Center) })
	self._dym = dym

	-- Row 2: autocomplete chips (horizontal scroller)
	local chips: ScrollingFrame = Kit.new("ScrollingFrame", {
		Name = "Suggestions",
		BackgroundTransparency = 1,
		BorderSizePixel = 0,
		Size = UDim2.new(1, 0, 0, Theme.MinTouch),
		CanvasSize = UDim2.new(),
		AutomaticCanvasSize = Enum.AutomaticSize.X,
		ScrollingDirection = Enum.ScrollingDirection.X,
		ScrollBarThickness = 0,
		ElasticBehavior = Enum.ElasticBehavior.Always,
		Visible = false,
		LayoutOrder = 2,
		ZIndex = z + 2,
		Selectable = false,
		Parent = root,
	}, { Kit.list(Enum.FillDirection.Horizontal, Theme.Space.sm, Enum.HorizontalAlignment.Center, Enum.VerticalAlignment.Center) })
	self._chips = chips

	-- Row 3: the bar
	local barRoot, bar = Kit.glass({ Name = "Bar", Size = UDim2.new(1, 0, 0, 60), Radius = Theme.Radius.xl, ZIndex = z, Accent = accent })
	barRoot.LayoutOrder = 3
	barRoot.Parent = root
	self._barRoot = barRoot
	self._barStroke = (barRoot:FindFirstChild("Panel") :: Frame):FindFirstChildOfClass("UIStroke")
	Kit.padding(6, 6).Parent = bar

	-- caret glyph on the left: a small element-coloured diamond, tinted by the last cast
	local glyph: Frame = Kit.new("Frame", {
		Name = "Glyph",
		AnchorPoint = Vector2.new(0, 0.5),
		Position = UDim2.new(0, 14, 0.5, 0),
		Size = UDim2.fromOffset(12, 12),
		Rotation = 45,
		BackgroundColor3 = Color3.new(1, 1, 1),
		BorderSizePixel = 0,
		ZIndex = z + 3,
		Parent = bar,
	}, { Kit.corner(3), Kit.gradient(accent, accent:Lerp(Color3.new(0, 0, 0), 0.4), 45) })
	self._glyph = glyph

	local submitW = 104
	local box: TextBox = Kit.new("TextBox", {
		Name = "Input",
		BackgroundTransparency = 1,
		ClearTextOnFocus = false,
		MultiLine = false,
		Text = "",
		PlaceholderText = o.placeholder or "Type anything...",
		PlaceholderColor3 = T.Color.TextMute,
		TextColor3 = T.Color.Text,
		FontFace = T.Font.Semi,
		TextSize = Theme.textSize("title"),
		TextXAlignment = Enum.TextXAlignment.Left,
		TextTruncate = Enum.TextTruncate.None,
		ClipsDescendants = true,
		Position = UDim2.fromOffset(36, 0),
		Size = UDim2.new(1, -(36 + submitW + 8), 1, 0),
		ZIndex = z + 3,
		Selectable = true,
		Parent = bar,
	})
	box:SetAttribute("TypeToken", "title")
	self.box = box

	local counter = Kit.label({
		Name = "Counter", Text = "", Size = "caption", Font = T.Font.Mono, Color = T.Color.TextMute,
		XAlign = Enum.TextXAlignment.Right, AutomaticSize = Enum.AutomaticSize.None,
		AnchorPoint = Vector2.new(1, 0.5), Position = UDim2.new(1, -(submitW + 14), 0.5, 0),
		FrameSize = UDim2.fromOffset(44, 20), ZIndex = z + 3, Parent = bar,
	})
	self._counter = counter

	local submit = Kit.button({
		Name = "Submit",
		Text = o.submitLabel or "CAST",
		Style = "Primary",
		Accent = accent,
		AnchorPoint = Vector2.new(1, 0.5),
		Position = UDim2.fromScale(1, 0.5),
		Size = UDim2.fromOffset(submitW, Theme.MinTouch),
		ZIndex = z + 3,
		Parent = bar,
		OnActivated = function()
			self:submit()
		end,
	})
	self._submit = submit

	-- input hygiene: single line, length cap, no control characters
	table.insert(self._conns, box:GetPropertyChangedSignal("Text"):Connect(function()
		local t = box.Text
		local clean = string.gsub(t, "[%c]", "")
		if utf8.len(clean) and (utf8.len(clean) :: number) > maxLen then
			clean = string.sub(clean, 1, (utf8.offset(clean, maxLen + 1) or (#clean + 1)) - 1)
		end
		if clean ~= t then
			box.Text = clean
			return
		end
		local n = utf8.len(clean) or #clean
		counter.Text = if n >= maxLen - 10 then (n .. "/" .. maxLen) else ""
		counter.TextColor3 = if n >= maxLen then T.Color.Warn else T.Color.TextMute
		self:_hideCorrection()
		self:_scheduleSuggest()
		self.Changed:Fire(clean)
	end))

	table.insert(self._conns, box.FocusLost:Connect(function(enterPressed: boolean)
		Kit.tween(self._barStroke, T.Tween.fast, { Transparency = Theme.StrokeTransparency, Color = Color3.new(1, 1, 1) })
		if enterPressed then
			self:submit()
		end
	end))
	table.insert(self._conns, box.Focused:Connect(function()
		Kit.tween(self._barStroke, T.Tween.fast, { Transparency = 0.35, Color = accent })
	end))
	pcall(function()
		table.insert(self._conns, (box :: any).ReturnPressedFromOnScreenKeyboard:Connect(function()
			self:submit()
		end))
	end)

	-- keyboard + gamepad shortcuts
	table.insert(self._conns, UIS.InputBegan:Connect(function(input: InputObject, processed: boolean)
		if not self._enabled then
			return
		end
		local kc = input.KeyCode
		if box:IsFocused() then
			if kc == Enum.KeyCode.Tab then
				self:acceptSuggestion(1)
			elseif kc == Enum.KeyCode.Escape then
				box.Text = ""
			end
			return
		end
		if processed or UIS:GetFocusedTextBox() then
			return
		end
		if kc == Enum.KeyCode.Slash or kc == Enum.KeyCode.Return or kc == Enum.KeyCode.ButtonY then
			task.defer(function()
				self:focus()
			end)
		end
	end))

	-- lift above the on-screen keyboard (phones/tablets)
	local function onKeyboard()
		local visible = UIS.OnScreenKeyboardVisible
		local lift = 0
		if visible then
			local cam = workspace.CurrentCamera
			local vh = cam and cam.ViewportSize.Y or 0
			local kbTop = UIS.OnScreenKeyboardPosition.Y
			if kbTop > 0 and vh > 0 then
				lift = math.max(0, vh - kbTop - 100)
			end
		end
		Kit.tween(root, T.Tween.base, { Position = self._basePos - UDim2.fromOffset(0, lift) })
	end
	pcall(function()
		table.insert(self._conns, UIS:GetPropertyChangedSignal("OnScreenKeyboardVisible"):Connect(onKeyboard))
	end)

	root.Parent = o.parent or Kit.screen("WordEngineHUD", 10)
	return self
end

function TypingBox:focus()
	if self._enabled then
		self.box:CaptureFocus()
	end
end

function TypingBox:release()
	self.box:ReleaseFocus(false)
end

function TypingBox:setText(text: string)
	self.box.Text = text
	self.box.CursorPosition = #text + 1
end

function TypingBox:setEnabled(enabled: boolean)
	self._enabled = enabled
	self.box.TextEditable = enabled
	self._submit.Active = enabled
	self._submit.BackgroundTransparency = if enabled then 0 else 0.5
	if not enabled then
		self:release()
	end
end

function TypingBox:setAccent(color: Color3)
	self._accent = color
	local g = self._glyph:FindFirstChildOfClass("UIGradient")
	if g then
		g.Color = ColorSequence.new(color, color:Lerp(Color3.new(0, 0, 0), 0.4))
	end
	Kit.pop(self._glyph, 1.6)
end

-- Busy state while the server resolves: the bar's stroke breathes in the accent colour.
function TypingBox:setBusy(busy: boolean)
	self._busy = busy
	local stroke: UIStroke = self._barStroke
	if busy then
		task.spawn(function()
			local T = Theme.get()
			while self._busy and stroke.Parent do
				Kit.tween(stroke, TweenInfo.new(0.45, Enum.EasingStyle.Sine), { Transparency = 0.2, Color = self._accent })
				task.wait(0.45)
				Kit.tween(stroke, TweenInfo.new(0.45, Enum.EasingStyle.Sine), { Transparency = 0.7 })
				task.wait(0.45)
			end
			Kit.tween(stroke, T.Tween.fast, { Transparency = Theme.StrokeTransparency, Color = Color3.new(1, 1, 1) })
		end)
	end
end

function TypingBox:error(message: string?)
	Kit.shake(self._barRoot)
	local T = Theme.get()
	local stroke: UIStroke = self._barStroke
	stroke.Color = T.Color.Danger
	stroke.Transparency = 0.1
	Kit.tween(stroke, T.Tween.slow, { Transparency = Theme.StrokeTransparency, Color = Color3.new(1, 1, 1) })
	if message then
		self.box.PlaceholderText = message
	end
end

function TypingBox:submit(textOverride: string?, meta: { [string]: any }?)
	if not self._enabled then
		return
	end
	local text = trim(textOverride or self.box.Text)
	if text == "" then
		self:error()
		return
	end
	self:_clearSuggestions()
	self:_hideCorrection()
	if self._opts.clearOnSubmit ~= false then
		self.box.Text = ""
	end
	Kit.press(self._submit)
	self.Submitted:Fire(text, meta or {})
	if self._keepFocus then
		task.defer(function()
			self:focus()
		end)
	end
end

-- Autocomplete ---------------------------------------------------------------------------------------

function TypingBox:_scheduleSuggest()
	self._suggestToken = (self._suggestToken or 0) + 1
	local token = self._suggestToken
	task.delay(0.06, function()
		if token ~= self._suggestToken then
			return
		end
		self:_refreshSuggestions()
	end)
end

function TypingBox:_clearSuggestions()
	for _, c in self._chips:GetChildren() do
		if c:IsA("GuiObject") then
			c:Destroy()
		end
	end
	self._chips.Visible = false
	self._suggestions = {}
end

function TypingBox:_refreshSuggestions()
	local cfg = uiCfg()
	local minChars = cfg.AutocompleteMinChars or 2
	local _, tail = lastToken(string.lower(self.box.Text))
	if #tail < minChars then
		self:_clearSuggestions()
		return
	end
	local ok, list = pcall(self._suggest, tail, cfg.AutocompleteLimit or 4)
	if not ok or type(list) ~= "table" then
		list = {}
	end
	-- drop exact echo of what's typed
	local filtered = {}
	for _, w in list do
		if type(w) == "string" and w ~= tail and #filtered < (cfg.AutocompleteLimit or 4) then
			table.insert(filtered, w)
		end
	end
	local same = #filtered == #self._suggestions
	if same then
		for i, w in filtered do
			if self._suggestions[i] ~= w then
				same = false
				break
			end
		end
	end
	if same then
		return
	end
	self:_clearSuggestions()
	self._suggestions = filtered
	if #filtered == 0 then
		return
	end
	self._chips.Visible = true
	for i, w in filtered do
		local chip = Kit.chip({
			Name = "Suggestion" .. i,
			Text = w,
			Strong = i == 1, -- Tab target
			Accent = self._accent,
			LayoutOrder = i,
			ZIndex = Theme.Z.chips,
			Parent = self._chips,
			OnActivated = function()
				self:acceptSuggestion(i)
			end,
		})
		Kit.pop(chip, 0.85)
	end
end

function TypingBox:acceptSuggestion(index: number)
	local w = self._suggestions[index]
	if not w then
		return
	end
	local head = lastToken(self.box.Text)
	local text = head .. w
	if self._opts.chipSubmits then
		self:submit(text, { fromChip = true })
	else
		self:setText(text .. " ")
		self:_clearSuggestions()
		self:focus()
	end
end

-- Did you mean ---------------------------------------------------------------------------------------

function TypingBox:_hideCorrection()
	if not self._dym.Visible then
		return
	end
	for _, c in self._dym:GetChildren() do
		if c:IsA("GuiObject") then
			c:Destroy()
		end
	end
	self._dym.Visible = false
end

-- Feed the WordResult back in; shows the one-tap correction chip when the confidence is in the band.
function TypingBox:setResult(result: any)
	if type(result) ~= "table" then
		return
	end
	local Th = Theme.get()
	local accent = Theme.element(result.element, result.visual and result.visual.primaryColour)
	self:setAccent(accent)
	local c = result.correction
	local cfg = uiCfg()
	local lo, hi = cfg.DidYouMeanMin or 0.6, cfg.DidYouMeanMax or 0.9
	local conf = if c then (c.confidence or result.confidence) else 1
	if not c or conf < lo or conf >= hi or type(c.to) ~= "string" or c.to == "" then
		return
	end
	self:_hideCorrection()
	local original = c.from
	local dym = self._dym
	dym.Visible = true
	local primary = Kit.chip({
		Name = "Accept",
		Prefix = "Did you mean",
		Text = c.to .. "?",
		Strong = true,
		Accent = accent,
		LayoutOrder = 1,
		ZIndex = Theme.Z.chips + 1,
		Parent = dym,
		OnActivated = function()
			self:_acceptCorrection(c.to, original)
		end,
	})
	Kit.pop(primary, 0.7)
	for i, alt in c.alternatives or {} do
		if i > 3 then
			break
		end
		Kit.chip({
			Name = "Alt" .. i,
			Text = alt,
			LayoutOrder = 1 + i,
			ZIndex = Theme.Z.chips + 1,
			Accent = Th.Color.TextDim,
			Parent = dym,
			OnActivated = function()
				self:_acceptCorrection(alt, original)
			end,
		})
	end
	local token = {}
	self._dymToken = token
	task.delay(7, function()
		if self._dymToken == token then
			self:_hideCorrection()
		end
	end)
	-- gamepad: put selection on the accept chip so one press confirms
	local GuiService = game:GetService("GuiService")
	local UIS = game:GetService("UserInputService")
	if UIS.GamepadEnabled and not UIS.TouchEnabled then
		GuiService.SelectedObject = primary
	end
end

function TypingBox:_acceptCorrection(word: string, original: string?)
	self:_hideCorrection()
	self.CorrectionAccepted:Fire(word, original)
	if self._opts.autoResubmitCorrection ~= false then
		self:submit(word, { fromCorrection = true })
	else
		self:setText(word)
	end
end

function TypingBox:destroy()
	for _, c in self._conns do
		c:Disconnect()
	end
	self.Submitted:Destroy()
	self.CorrectionAccepted:Destroy()
	self.Changed:Destroy()
	self.root:Destroy()
end

return TypingBox
