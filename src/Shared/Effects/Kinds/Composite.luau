--!nonstrict
-- Composite: plays catalogue layers with delays/offsets/element overrides (reactions, material reactions).
-- Layers inherit at/from/to/target/style/colour/priority from the parent params; scale multiplies.
-- Looping layers (zones, clouds, auras) last for the composite's duration and stop with it; one-shot layers
-- (explosions, impacts) are detached and always play to their natural end.

local Catalogue = require(script.Parent.Parent.Catalogue)

return function(fx)
	local params = fx.params
	local layers = fx.entry.layers or {}
	local base = fx:at()
	for _, layer in layers do
		local function start()
			if fx.stopping then
				return
			end
			local at = base
			if layer.off then
				at = base * CFrame.new(layer.off[1] * fx.scale, layer.off[2] * fx.scale, layer.off[3] * fx.scale)
			end
			local p = {
				at = at,
				from = params.from,
				to = params.to,
				target = params.target,
				points = params.points,
				targets = params.targets,
				element = layer.el or params.element,
				colour = layer.colour or params.colour,
				scale = fx.scale * (layer.s or 1),
				style = fx.style,
				priority = params.priority,
				radius = params.radius and params.radius * (layer.s or 1) or nil,
			}
			local entry = Catalogue.get(layer.id)
			local looping = entry ~= nil and entry.loop == true
			if layer.dur then
				p.duration = layer.dur
			elseif looping then
				p.duration = math.max(0.2, (fx.duration or 4) - (layer.d or 0))
			end
			fx:child(layer.id, p)
			if not looping then
				table.remove(fx.children) -- one-shot: let it finish on its own
			end
		end
		if (layer.d or 0) <= 0 then
			start()
		else
			fx:after(layer.d, start)
		end
	end
	-- the composite itself owns no instances; it ends when its duration ends (children follow via stop())
	fx.fadeOut = 0
end
