--!strict
-- Theme: design tokens for the WordEngine UI kit. Hex/number data is pure; Roblox values (Color3, Font,
-- TweenInfo) are built lazily by Theme.get() so the module is safe to require anywhere.
--
-- Look: dark translucent glass, crisp 1px light strokes, soft layered shadows, element-coloured accents.

local Theme = {}

Theme.Hex = {
	Ink = "#070A10", -- deepest background / shadow
	Glass = "#111827", -- panel base (used at GlassTransparency)
	GlassHi = "#1D2638", -- gradient top of panels
	GlassLo = "#0C111C", -- gradient bottom
	Raised = "#243048", -- buttons on glass
	RaisedHi = "#2F3D5C",
	Stroke = "#FFFFFF", -- used at StrokeTransparency
	Text = "#F4F7FB",
	TextDim = "#B3BDCE",
	TextMute = "#6E7A90",
	Brand = "#8B6CFF", -- WordEngine violet
	Brand2 = "#38D6F5", -- cyan partner for brand gradients
	Success = "#3DDC97",
	Warn = "#FFB547",
	Danger = "#FF5C7A",
}

-- Element accents: primary (bright) + deep (gradient end). Tuned for contrast on dark glass.
Theme.ElementHex = {
	Fire = { "#FF7A2F", "#D7261E" },
	Water = { "#3BA7FF", "#1747C9" },
	Ice = { "#A6ECFF", "#4FA9E6" },
	Lightning = { "#FFE14D", "#F59E0B" },
	Earth = { "#C99A5B", "#7A4E26" },
	Wind = { "#A8F5D2", "#3FB58C" },
	Nature = { "#6BE36B", "#1F9D4C" },
	Light = { "#FFF4C2", "#FFC94D" },
	Shadow = { "#A78BFA", "#4C1D95" },
	Poison = { "#B5F23D", "#5E9E14" },
	Metal = { "#D3DCE6", "#7B8A9C" },
	Arcane = { "#F07BFF", "#8B2BE2" },
	None = { "#D5DCE6", "#8A96A8" },
}

Theme.Space = { xxs = 2, xs = 4, sm = 8, md = 12, lg = 16, xl = 24, xxl = 32, xxxl = 48 }
Theme.Radius = { sm = 8, md = 12, lg = 16, xl = 22 }
Theme.TypeScale = { caption = 13, label = 15, body = 17, title = 22, headline = 30, display = 52, hero = 84 }
Theme.GlassTransparency = 0.16
Theme.StrokeTransparency = 0.86
Theme.StrokeStrongTransparency = 0.7
Theme.MinTouch = 48
Theme.Motion = { fast = 0.12, base = 0.2, slow = 0.35, reveal = 0.55 }
Theme.Z = { hud = 10, chips = 20, panel = 40, toast = 60, reveal = 80, modal = 100 }

-- Per-player multipliers set by the Settings panel.
Theme.textScale = 1
Theme.reducedMotion = false

local built: any = nil

local function hex(h: string): Color3
	return Color3.fromHex(h)
end

-- Roblox-typed tokens (Color3 / Font / TweenInfo). Cached.
function Theme.get(): any
	if built then
		return built
	end
	local cfg: any = nil
	pcall(function()
		cfg = (require(script.Parent.Parent.Config) :: any).UI
	end)
	local family = (cfg and cfg.FontFamily) or "rbxasset://fonts/families/BuilderSans.json"
	local display = (cfg and cfg.DisplayFamily) or "rbxasset://fonts/families/BuilderExtended.json"
	local mono = (cfg and cfg.MonoFamily) or "rbxasset://fonts/families/BuilderMono.json"
	local W = Enum.FontWeight
	local C: { [string]: Color3 } = {}
	for k, v in Theme.Hex do
		C[k] = hex(v)
	end
	local E: { [string]: { Color3 } } = {}
	for k, v in Theme.ElementHex do
		E[k] = { hex(v[1]), hex(v[2]) }
	end
	built = {
		Color = C,
		Element = E,
		Font = {
			Regular = Font.new(family, W.Regular),
			Medium = Font.new(family, W.Medium),
			Semi = Font.new(family, W.SemiBold),
			Bold = Font.new(family, W.Bold),
			Heavy = Font.new(family, W.ExtraBold),
			Display = Font.new(display, W.Heavy),
			DisplayBold = Font.new(display, W.Bold),
			Mono = Font.new(mono, W.Medium),
		},
		Tween = {
			fast = TweenInfo.new(Theme.Motion.fast, Enum.EasingStyle.Quint, Enum.EasingDirection.Out),
			base = TweenInfo.new(Theme.Motion.base, Enum.EasingStyle.Quint, Enum.EasingDirection.Out),
			slow = TweenInfo.new(Theme.Motion.slow, Enum.EasingStyle.Quint, Enum.EasingDirection.Out),
			punch = TweenInfo.new(Theme.Motion.reveal, Enum.EasingStyle.Back, Enum.EasingDirection.Out),
			spring = TweenInfo.new(0.42, Enum.EasingStyle.Back, Enum.EasingDirection.Out),
			linear = function(t: number): TweenInfo
				return TweenInfo.new(t, Enum.EasingStyle.Linear)
			end,
		},
	}
	return built
end

-- Element accent pair; falls back to the result's own colours, then None.
function Theme.element(element: string?, fallbackHex: string?): (Color3, Color3)
	local T = Theme.get()
	local pair = element and T.Element[element]
	if pair and element ~= "None" then
		return pair[1], pair[2]
	end
	if fallbackHex then
		local ok, c = pcall(Color3.fromHex, fallbackHex)
		if ok then
			return c, c:Lerp(Color3.new(0, 0, 0), 0.45)
		end
	end
	return T.Element.None[1], T.Element.None[2]
end

function Theme.textSize(token: string): number
	return math.floor((Theme.TypeScale[token] or 17) * Theme.textScale + 0.5)
end

return Theme
