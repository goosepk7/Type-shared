--!strict
-- WordEngine UI kit (client). See README.md in this folder.
-- Lazy: each widget module loads on first access, nothing touches Roblox APIs at require time.

local UI = {}

local loaded: { [string]: any } = {}
local root = script

setmetatable(UI, {
	__index = function(_, key: string)
		local cached = loaded[key]
		if cached ~= nil then
			return cached
		end
		local child = root:FindFirstChild(key)
		if child == nil then
			error(("WordEngine.UI has no module %q"):format(tostring(key)), 2)
		end
		local mod = require(child :: any)
		loaded[key] = mod
		return mod
	end,
})

-- Convenience: the standard HUD (typing box above a hotbar) wired with toasts. Returns { box, hotbar, screen }.
function UI.hud(opts: { slots: number?, placeholder: string?, submitLabel: string? }?): { [string]: any }
	local o = opts or {}
	local Kit = (UI :: any).Kit
	local screen = Kit.screen("WordEngineHUD", 10)
	local hotbar = (UI :: any).Hotbar.new({ parent = screen, slots = o.slots or 4 })
	local box = (UI :: any).TypingBox.new({
		parent = screen,
		placeholder = o.placeholder,
		submitLabel = o.submitLabel,
		position = UDim2.new(0.5, 0, 1, -(hotbar.root.Size.Y.Offset + 28)),
	})
	return { box = box, hotbar = hotbar, screen = screen }
end

return UI
