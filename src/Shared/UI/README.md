# WordEngine UI kit

Mobile-first, premium dark-glass UI shared by **Typing Wizards** and **Type to Defend**. Client only; nothing touches
Roblox APIs at require time. Every tappable target is at least 48 px, every HUD lives in a safe-area aware
`ScreenGui` (`ScreenInsets = CoreUISafeInsets`), and every widget supports touch, mouse + keyboard and gamepad.

```lua
local WordEngine = require(game.ReplicatedStorage.WordEngine)
local UI = WordEngine.UI
```

| Module | What it is |
|---|---|
| `UI.Theme` | Tokens: colours, 12 element accent pairs, type scale (Builder Sans / Extended / Mono), spacing, radii, motion. `Theme.get()` returns Color3/Font/TweenInfo values; `Theme.element(element, fallbackHex)` returns the accent pair. |
| `UI.Kit` | Primitives: `Kit.screen`, `Kit.glass` (gradient glass + 1px stroke + layered shadow), `Kit.label`, `Kit.button`, `Kit.chip`, `Kit.tween`, `Kit.pop/press/shake`. Build new screens from these so they match. |
| `UI.TypingBox` | Word entry bar with autocomplete chips, one-tap "did you mean", busy and error states. |
| `UI.Hotbar` | 3-5 slots with element orb, charge pips ring, radial cooldown sweep, used-word greying. |
| `UI.Toast` | Stacked notifications (`info`, `success`, `warn`, `error`, `word`). |
| `UI.WordReveal` | The cast word punching onto the screen in element colours with tags and flavour text. |
| `UI.Settings` | Settings sheet (reduced motion, suggestions, did-you-mean, text size, music/effects sliders, summon style). |
| `UI.hud(opts)` | Convenience: typing box stacked above a hotbar on one HUD screen. |

## TypingBox

```lua
local box = UI.TypingBox.new({
  placeholder = "Type a spell...",   -- Wizard; Defend: "Type a defense..."
  submitLabel = "CAST",              -- Defend: "BUILD"
  wordBook = function() return myRecentWords end, -- ranks autocomplete (Suggest.prefix)
  autoResubmitCorrection = true,     -- accepting "did you mean" casts the corrected word
  chipSubmits = false,               -- tapping a suggestion completes the word; Enter/CAST submits
})
box.Submitted:Connect(function(text, meta)
  local result, info = WordEngine.Net.interpret(text)   -- yields <= ~1.5 s
  box:setResult(result)              -- shows the did-you-mean chip when correction confidence is 0.6..0.9
  info.upgraded:Connect(function(better) box:setResult(better) end)
end)
box.CorrectionAccepted:Connect(function(word, original) end)
box:setBusy(true/false)   box:error("Not enough mana")   box:setEnabled(false)   box:focus()
```

- Suggestions appear after `Config.UI.AutocompleteMinChars` (2) letters, from `Suggest.prefix(prefix, wordBook,
  limit)` (falls back to `Library.prefixSearch`). The first chip is highlighted: **Tab** accepts it.
- Keys: `/` or Enter focuses, Enter submits, Esc clears. Gamepad: **Y** focuses (console keyboard), the did-you-mean
  chip is auto-selected so one press confirms.
- The bar lifts above the on-screen keyboard on phones and tablets.

## Hotbar

```lua
local bar = UI.Hotbar.new({ slots = 5 })      -- 3..5 (Config.UI.HotbarSlotsMin/Max)
bar:setSlot(1, { word = "fireball", element = "Fire", charges = 3, maxCharges = 3 })
bar.Activated:Connect(function(i) ... end)    -- tap, keys 1-5, gamepad L1/R1 select + R2 activate
bar:cooldown(1, 4)          -- radial sweep + countdown, pops when ready
bar:setCharges(1, 2)        -- pips ring around the orb
bar:markUsed(1, true)       -- greyed + strike-through (Wizard no-repeat rule)
```

Typing Wizards: the 3-5 spell loadout; `markUsed` for words already used this match.
Type to Defend: backup defenses; put the cost in `subtitle` (`subtitle = "$120"`) and grey slots the team can't
afford with `markUsed(i, true)`.

The bar scales down on narrow phones (never below 0.7, so slots stay >= 53 px).

## Toast and WordReveal

```lua
UI.Toast.show("New word discovered: TORNADO", { kind = "word", element = "Wind", title = "Word book" })
UI.WordReveal.play(result)                               -- centre banner, auto-dismiss (~2.2 s)
UI.WordReveal.play(result, { caster = displayName })     -- show who cast it (pass a filtered/display name)
UI.WordReveal.play(result, { parent = frame, compact = true })  -- inside your own frame
```

WordReveal shows `result.canonical`, never the raw input, so it is safe to show to everyone (broadcast results with
`Schema.forBroadcast`). Secondary elements, mood, material and count appear as tags.

## Settings

```lua
local settings = UI.Settings.new({ values = savedValues })
settings:toggle()
settings.Changed:Connect(function(key, value, all) end)
```

Persistence is built in: the server (`Data.start`) creates `ReplicatedStorage.WordEngineSettings`. Fire it with the
full values table (debounce ~1 s); the server sanitises with `Settings.sanitize` (shared schema), stores it in the
player's profile and mirrors it to the `WE_Settings` player attribute (JSON) for restore on join. See
`testplace/Client` for the pattern. Text size and reduced motion apply live to every WordEngine widget.

## Look rules (keep the AAA bar)

- Build panels with `Kit.glass`; never use default grey frames or `AutoButtonColor`.
- Accent with the word's element (`Theme.element`). Brand violet/cyan only for neutral chrome.
- Spacing from `Theme.Space`, radii from `Theme.Radius`, text from `Theme.TypeScale` via `Kit.label`.
- Lines and strokes never overlap: highlights are inset 1 px, focus rings sit 3 px outside.
- Respect `Theme.reducedMotion` (Kit.tween does automatically).
