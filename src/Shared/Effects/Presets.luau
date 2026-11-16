--!strict
-- ParticleEmitter presets (pure data). The runtime turns a preset + element ramp + style + scale into a
-- configured, pooled emitter. Sizes/speeds are in studs at scale 1; Rate is per second at particleScale 1.
--
-- Field reference (all optional unless noted):
--   tex (required)  texture name in Assets.Textures
--   flip            ParticleFlipbookMode name for flipbook textures: "OneShot" | "Loop" | "PingPong" | "Random"
--   fps             {min,max} flipbook framerate (engine cap 30)
--   life            {min,max} seconds (engine caps at 20)
--   size            number or {{t,v},...} NumberSequence keypoints (studs)
--   trans           {{t,v},...} transparency keypoints
--   squash          {{t,v},...} Squash keypoints (stretch along velocity/screen-up)
--   speed           {min,max} studs/s
--   spread          {x,y} degrees
--   dir             EmissionDirection NormalId name (default "Top")
--   accel           {x,y,z}, drag number
--   rot, rotSpeed   {min,max} degrees
--   colour          ramp stops ({1,3,5} or {{t,idx},...});  hex {"#..",..} fixed colours;  smoke = true uses the
--                   style's smoke tint
--   emission        {spectral, solid} LightEmission; influence {spectral, solid} LightInfluence
--   brightness      number
--   orient          ParticleOrientation name
--   shape           "Box"|"Sphere"|"Cylinder"|"Disc" (needs an area carrier), shapeStyle, shapeInOut
--   rate            default Rate (0 = burst-only via :emit(n))
--   zoffset, locked, velInherit

export type Preset = { [string]: any }

local P: { [string]: Preset } = {}

-- Glows and flashes -----------------------------------------------------------------------------------------
P.glow = {
	tex = "glow", life = { 0.25, 0.4 }, size = { { 0, 2 }, { 1, 3.2 } }, trans = { { 0, 0.25 }, { 1, 1 } },
	speed = { 0, 0 }, rate = 0, colour = { 2, 3 }, emission = { 1, 1 }, influence = { 0, 0 }, zoffset = 0.5,
}
P.flash = {
	tex = "burst", life = { 0.14, 0.22 }, size = { { 0, 1 }, { 0.25, 7 }, { 1, 9 } }, trans = { { 0, 0 }, { 0.5, 0.35 }, { 1, 1 } },
	speed = { 0, 0 }, rate = 0, rot = { 0, 360 }, colour = { 1, 2 }, emission = { 1, 1 }, influence = { 0, 0 }, zoffset = 1,
	brightness = 2,
}
P.coreGlow = {
	tex = "glow_core", life = { 0.3, 0.3 }, size = 3, trans = { { 0, 0.35 }, { 0.5, 0.45 }, { 1, 0.35 } },
	speed = { 0, 0 }, rate = 6, colour = { 1, 2 }, emission = { 1, 0.9 }, influence = { 0, 0 }, locked = true, zoffset = 0.3,
}
P.ring = { -- flat shockwave ring lying on the ground (VelocityPerpendicular with an upward velocity)
	tex = "ring", life = { 0.55, 0.55 }, size = { { 0, 0.5 }, { 1, 12 } }, trans = { { 0, 0.1 }, { 0.6, 0.55 }, { 1, 1 } },
	speed = { 0.01, 0.01 }, spread = { 0, 0 }, rate = 0, orient = "VelocityPerpendicular", colour = { 1, 3 },
	emission = { 1, 0.7 }, influence = { 0, 0.3 },
}
P.ringAir = { -- camera-facing ring for mid-air bursts
	tex = "ring", life = { 0.35, 0.35 }, size = { { 0, 0.5 }, { 1, 9 } }, trans = { { 0, 0.15 }, { 1, 1 } },
	speed = { 0, 0 }, rate = 0, colour = { 1, 2 }, emission = { 1, 1 }, influence = { 0, 0 }, zoffset = 0.8,
}

-- Fire ------------------------------------------------------------------------------------------------------
P.fire = {
	tex = "flame_4x4", flip = "OneShot", life = { 0.55, 0.9 }, size = { { 0, 1.1 }, { 0.35, 1.7 }, { 1, 0.5 } },
	trans = { { 0, 0.7 }, { 0.12, 0.1 }, { 0.7, 0.35 }, { 1, 1 } }, speed = { 2.5, 5 }, spread = { 14, 14 },
	accel = { 0, 5, 0 }, rot = { -12, 12 }, rotSpeed = { -25, 25 }, colour = { { 0, 1 }, { 0.3, 2 }, { 0.7, 3 }, { 1, 4 } },
	emission = { 1, 0.85 }, influence = { 0, 0 }, rate = 20, brightness = 1.5,
}
P.embers = {
	tex = "glow", life = { 1, 2.2 }, size = { { 0, 0.16 }, { 0.8, 0.1 }, { 1, 0 } }, trans = { { 0, 0 }, { 0.5, 0.2 }, { 1, 1 } },
	speed = { 2, 6 }, spread = { 40, 40 }, accel = { 0, 6, 0 }, drag = 1.2, colour = { 2, 3, 4 }, emission = { 1, 1 },
	influence = { 0, 0 }, rate = 8, brightness = 2,
}
P.sparks = {
	tex = "spark", orient = "VelocityParallel", life = { 0.3, 0.7 }, size = { { 0, 0.22 }, { 1, 0 } },
	squash = { { 0, 1.5 }, { 1, 0.5 } }, trans = { { 0, 0 }, { 1, 0.3 } }, speed = { 18, 38 }, spread = { 180, 180 },
	accel = { 0, -40, 0 }, drag = 2.5, colour = { 1, 2, 3 }, emission = { 1, 1 }, influence = { 0, 0 }, rate = 0, brightness = 2,
}
P.smoke = {
	tex = "smoke_4x4", flip = "OneShot", life = { 1.8, 3 }, size = { { 0, 1.4 }, { 1, 4.4 } },
	trans = { { 0, 1 }, { 0.12, 0.5 }, { 0.6, 0.7 }, { 1, 1 } }, speed = { 1.5, 3 }, spread = { 25, 25 },
	accel = { 0, 2.5, 0 }, drag = 0.6, rot = { 0, 360 }, rotSpeed = { -20, 20 }, smoke = true,
	emission = { 0.15, 0 }, influence = { 0.4, 1 }, rate = 6, zoffset = -0.5,
}
P.steam = {
	tex = "smoke_4x4", flip = "OneShot", life = { 1.6, 2.6 }, size = { { 0, 1.5 }, { 1, 5 } },
	trans = { { 0, 1 }, { 0.15, 0.45 }, { 1, 1 } }, speed = { 2, 5 }, spread = { 40, 40 }, accel = { 0, 3, 0 },
	drag = 0.8, rot = { 0, 360 }, rotSpeed = { -15, 15 }, hex = { "#FFFFFF", "#E6EEF2" }, emission = { 0.3, 0.1 },
	influence = { 0.3, 1 }, rate = 10,
}

-- Water / ice -----------------------------------------------------------------------------------------------
P.splash = {
	tex = "raindrop", orient = "VelocityParallel", life = { 0.4, 0.75 }, size = { { 0, 0.35 }, { 1, 0.15 } },
	trans = { { 0, 0.1 }, { 1, 0.8 } }, speed = { 10, 20 }, spread = { 55, 55 }, accel = { 0, -50, 0 },
	colour = { 1, 2, 3 }, emission = { 0.8, 0.2 }, influence = { 0.2, 1 }, rate = 0,
}
P.droplets = {
	tex = "bubble", life = { 0.4, 0.8 }, size = { { 0, 0.25 }, { 1, 0.1 } }, trans = { { 0, 0.1 }, { 1, 1 } },
	speed = { 8, 16 }, spread = { 180, 180 }, accel = { 0, -40, 0 }, colour = { 1, 2 }, emission = { 0.8, 0.3 },
	influence = { 0.2, 1 }, rate = 0,
}
P.bubbles = {
	tex = "bubble", life = { 1, 2 }, size = { { 0, 0.2 }, { 0.8, 0.4 }, { 1, 0.45 } }, trans = { { 0, 0.2 }, { 0.85, 0.3 }, { 1, 1 } },
	speed = { 1, 3 }, spread = { 40, 40 }, accel = { 0, 3, 0 }, drag = 1, colour = { 1, 2 }, emission = { 0.7, 0.2 },
	influence = { 0.2, 1 }, rate = 6,
}
P.mist = {
	tex = "glow", life = { 2, 3.2 }, size = { { 0, 3 }, { 1, 5.5 } }, trans = { { 0, 1 }, { 0.3, 0.82 }, { 1, 1 } },
	speed = { 0.3, 1 }, spread = { 180, 180 }, colour = { 2, 3 }, emission = { 0.5, 0 }, influence = { 0.2, 1 }, rate = 5, zoffset = -1,
}
P.frostMist = {
	tex = "smoke_4x4", flip = "OneShot", life = { 1.2, 2 }, size = { { 0, 1 }, { 1, 3 } }, trans = { { 0, 1 }, { 0.2, 0.6 }, { 1, 1 } },
	speed = { 0.5, 1.5 }, spread = { 180, 180 }, accel = { 0, -0.8, 0 }, rot = { 0, 360 }, rotSpeed = { -10, 10 },
	colour = { 1, 2 }, emission = { 0.6, 0.15 }, influence = { 0.2, 1 }, rate = 6,
}
P.snow = {
	tex = "snowflake", life = { 2, 3.5 }, size = { { 0, 0.22 }, { 1, 0.16 } }, trans = { { 0, 1 }, { 0.1, 0 }, { 0.85, 0 }, { 1, 1 } },
	speed = { 1, 3 }, spread = { 180, 180 }, accel = { 0, -3, 0 }, drag = 0.6, rot = { 0, 360 }, rotSpeed = { -90, 90 },
	colour = { 1, 2 }, emission = { 0.6, 0.1 }, influence = { 0.3, 1 }, rate = 10,
}
P.iceShards = {
	tex = "shard", orient = "VelocityParallel", life = { 0.4, 0.8 }, size = { { 0, 0.7 }, { 1, 0.2 } },
	trans = { { 0, 0 }, { 0.8, 0.2 }, { 1, 1 } }, speed = { 16, 30 }, spread = { 180, 180 }, accel = { 0, -30, 0 },
	drag = 1, colour = { 1, 2, 3 }, emission = { 0.9, 0.35 }, influence = { 0.1, 0.8 }, rate = 0,
}
P.rain = {
	tex = "raindrop", orient = "VelocityParallel", dir = "Bottom", life = { 0.6, 0.9 }, size = 0.55,
	squash = { { 0, 1 }, { 1, 1 } }, trans = { { 0, 0.35 }, { 1, 0.55 } }, speed = { 55, 70 }, spread = { 3, 3 },
	hex = { "#D9ECFF", "#A9CBEA" }, emission = { 0.4, 0.1 }, influence = { 0.4, 1 }, rate = 40,
	shape = "Box", shapeStyle = "Volume",
}

-- Electric --------------------------------------------------------------------------------------------------
P.electric = {
	tex = "star", life = { 0.05, 0.12 }, size = { { 0, 0.6 }, { 1, 1.3 } }, trans = { { 0, 0 }, { 1, 0.6 } },
	speed = { 0, 0 }, rot = { 0, 360 }, colour = { 1, 2 }, emission = { 1, 1 }, influence = { 0, 0 }, rate = 22, brightness = 3,
	shape = "Sphere", shapeStyle = "Surface",
}
P.motes = {
	tex = "glow", life = { 1, 2 }, size = { { 0, 0.16 }, { 0.5, 0.22 }, { 1, 0 } }, trans = { { 0, 0.2 }, { 1, 0.6 } },
	speed = { 0.4, 1.5 }, spread = { 180, 180 }, accel = { 0, 0.6, 0 }, drag = 1, colour = { 1, 2, 3 },
	emission = { 1, 1 }, influence = { 0, 0 }, rate = 8, brightness = 2,
}

-- Earth -----------------------------------------------------------------------------------------------------
P.dust = {
	tex = "smoke_4x4", flip = "OneShot", life = { 1, 2 }, size = { { 0, 1 }, { 1, 3.6 } }, trans = { { 0, 1 }, { 0.1, 0.45 }, { 1, 1 } },
	speed = { 4, 8 }, spread = { 80, 80 }, accel = { 0, -1.5, 0 }, drag = 2, rot = { 0, 360 }, rotSpeed = { -20, 20 },
	colour = { 2, 3 }, emission = { 0.4, 0 }, influence = { 0.3, 1 }, rate = 0,
}
P.dustRing = { -- ground dust pushed outward from a ring (needs a Disc carrier)
	tex = "smoke_4x4", flip = "OneShot", life = { 0.8, 1.4 }, size = { { 0, 1.4 }, { 1, 4 } }, trans = { { 0, 1 }, { 0.1, 0.4 }, { 1, 1 } },
	speed = { 12, 20 }, drag = 4, accel = { 0, 1, 0 }, rot = { 0, 360 }, rotSpeed = { -30, 30 }, colour = { 2, 3 },
	smokeMix = 0.5, emission = { 0.25, 0 }, influence = { 0.4, 1 }, rate = 0, shape = "Disc", shapeStyle = "Surface",
	shapeInOut = "Outward",
}
P.pebbles = {
	tex = "shard", life = { 0.5, 0.9 }, size = { { 0, 0.4 }, { 1, 0.3 } }, trans = { { 0, 0 }, { 0.85, 0 }, { 1, 1 } },
	speed = { 14, 26 }, spread = { 60, 60 }, accel = { 0, -60, 0 }, rot = { 0, 360 }, rotSpeed = { -400, 400 },
	colour = { 3, 4, 5 }, emission = { 0.5, 0 }, influence = { 0.4, 1 }, rate = 0,
}

-- Wind / nature ---------------------------------------------------------------------------------------------
P.windStreaks = {
	tex = "swirl", life = { 0.4, 0.7 }, size = { { 0, 1.8 }, { 1, 3.4 } }, trans = { { 0, 1 }, { 0.25, 0.55 }, { 1, 1 } },
	speed = { 2, 6 }, spread = { 180, 180 }, rot = { 0, 360 }, rotSpeed = { 220, 420 }, colour = { 1, 2 },
	emission = { 0.7, 0.2 }, influence = { 0.2, 1 }, rate = 10,
}
P.leaves = {
	tex = "leaf", life = { 1, 1.8 }, size = { { 0, 0.45 }, { 1, 0.35 } }, trans = { { 0, 0 }, { 0.8, 0 }, { 1, 1 } },
	speed = { 8, 16 }, spread = { 180, 180 }, accel = { 0, -6, 0 }, drag = 2, rot = { 0, 360 }, rotSpeed = { -200, 200 },
	colour = { 2, 3, 4 }, emission = { 0.5, 0 }, influence = { 0.3, 1 }, rate = 0,
}
P.leavesDrift = {
	tex = "leaf", life = { 2, 3 }, size = 0.35, trans = { { 0, 1 }, { 0.1, 0 }, { 0.85, 0 }, { 1, 1 } }, speed = { 3, 6 },
	spread = { 180, 180 }, accel = { 0, -1, 0 }, drag = 0.5, rot = { 0, 360 }, rotSpeed = { -160, 160 },
	hex = { "#B7D86A", "#7FAF3D", "#D9B04A" }, emission = { 0.3, 0 }, influence = { 0.4, 1 }, rate = 4,
}
P.petals = {
	tex = "petal", life = { 1.6, 2.6 }, size = 0.3, trans = { { 0, 1 }, { 0.1, 0 }, { 0.85, 0 }, { 1, 1 } }, speed = { 2, 5 },
	spread = { 180, 180 }, accel = { 0, -1.2, 0 }, drag = 0.6, rot = { 0, 360 }, rotSpeed = { -150, 150 },
	hex = { "#FFD1E8", "#FF9CC9", "#FFFFFF" }, emission = { 0.4, 0 }, influence = { 0.3, 1 }, rate = 6,
}
P.pollen = {
	tex = "glow", life = { 1.5, 3 }, size = { { 0, 0.12 }, { 0.5, 0.18 }, { 1, 0 } }, trans = { { 0, 0.3 }, { 1, 0.7 } },
	speed = { 0.5, 1.5 }, spread = { 180, 180 }, accel = { 0, 0.3, 0 }, drag = 1, hex = { "#FFF3A0", "#FFD84A" },
	emission = { 1, 0.6 }, influence = { 0, 0.5 }, rate = 10,
}

-- Light / shadow / arcane -----------------------------------------------------------------------------------
P.stars = {
	tex = "star", life = { 0.4, 0.9 }, size = { { 0, 0.55 }, { 1, 0 } }, trans = { { 0, 0 }, { 1, 0.2 } }, speed = { 4, 10 },
	spread = { 180, 180 }, drag = 2, rot = { 0, 360 }, rotSpeed = { -120, 120 }, colour = { 1, 2, 3 }, emission = { 1, 1 },
	influence = { 0, 0 }, rate = 0, brightness = 2,
}
P.wisps = {
	tex = "smoke_4x4", flip = "OneShot", life = { 1, 1.6 }, size = { { 0, 1.2 }, { 1, 2.8 } }, trans = { { 0, 1 }, { 0.2, 0.35 }, { 1, 1 } },
	speed = { 1, 2 }, spread = { 180, 180 }, accel = { 0, 1.5, 0 }, rot = { 0, 360 }, rotSpeed = { -40, 40 },
	colour = { 4, 5 }, emission = { 0.15, 0 }, influence = { 0.2, 1 }, rate = 8, zoffset = -0.4,
}
P.darkMotes = {
	tex = "glow", life = { 0.8, 1.6 }, size = { { 0, 0.2 }, { 1, 0 } }, trans = { { 0, 0.1 }, { 1, 0.5 } }, speed = { 1, 3 },
	spread = { 180, 180 }, drag = 1.5, colour = { 1, 2 }, emission = { 1, 0.6 }, influence = { 0, 0.5 }, rate = 6,
}
P.runes = {
	tex = "runes_4x4", flip = "Random", fps = { 0, 0 }, life = { 1, 1.6 }, size = { { 0, 0.45 }, { 1, 0.65 } },
	trans = { { 0, 1 }, { 0.2, 0.1 }, { 0.8, 0.2 }, { 1, 1 } }, speed = { 1, 2 }, spread = { 180, 180 }, accel = { 0, 1.5, 0 },
	drag = 1, orient = "FacingCameraWorldUp", colour = { 2, 3 }, emission = { 1, 0.8 }, influence = { 0, 0.2 }, rate = 6, brightness = 2,
}
P.glitter = {
	tex = "star", life = { 0.6, 1.1 }, size = { { 0, 0.35 }, { 1, 0 } }, trans = { { 0, 0 }, { 1, 0.3 } }, speed = { 3, 7 },
	spread = { 180, 180 }, drag = 1.5, accel = { 0, -2, 0 }, rot = { 0, 360 }, rotSpeed = { -200, 200 },
	hex = { "#FFFFFF", "#FFB3F0", "#B3E5FF", "#FFF3A0" }, emission = { 1, 1 }, influence = { 0, 0 }, rate = 0,
}

-- Poison / metal --------------------------------------------------------------------------------------------
P.toxicBubbles = {
	tex = "bubble", life = { 0.8, 1.6 }, size = { { 0, 0.25 }, { 0.85, 0.5 }, { 1, 0.6 } }, trans = { { 0, 0.15 }, { 0.85, 0.25 }, { 1, 1 } },
	speed = { 1, 2.5 }, spread = { 30, 30 }, accel = { 0, 2.5, 0 }, drag = 1, colour = { 2, 3 }, emission = { 0.8, 0.3 },
	influence = { 0.1, 0.8 }, rate = 8,
}
P.toxicGas = {
	tex = "smoke_4x4", flip = "OneShot", life = { 1.6, 2.8 }, size = { { 0, 1.6 }, { 1, 4.5 } }, trans = { { 0, 1 }, { 0.2, 0.55 }, { 1, 1 } },
	speed = { 0.8, 2 }, spread = { 180, 180 }, accel = { 0, 0.4, 0 }, drag = 0.4, rot = { 0, 360 }, rotSpeed = { -15, 15 },
	colour = { 2, 3, 4 }, emission = { 0.35, 0.05 }, influence = { 0.3, 1 }, rate = 6,
}
P.toxicSplash = {
	tex = "bubble", life = { 0.4, 0.8 }, size = { { 0, 0.35 }, { 1, 0.1 } }, trans = { { 0, 0 }, { 1, 1 } }, speed = { 8, 16 },
	spread = { 70, 70 }, accel = { 0, -40, 0 }, colour = { 2, 3 }, emission = { 0.9, 0.3 }, influence = { 0.1, 0.8 }, rate = 0,
}
P.metalSparks = {
	tex = "spark", orient = "VelocityParallel", life = { 0.25, 0.55 }, size = { { 0, 0.18 }, { 1, 0 } },
	squash = { { 0, 2 }, { 1, 0.5 } }, speed = { 24, 44 }, spread = { 70, 70 }, accel = { 0, -60, 0 }, drag = 1.5,
	hex = { "#FFFFFF", "#FFD08A", "#FF7A2E" }, emission = { 1, 1 }, influence = { 0, 0 }, rate = 0, brightness = 3,
}
P.glints = {
	tex = "star", life = { 0.2, 0.4 }, size = { { 0, 0 }, { 0.5, 0.5 }, { 1, 0 } }, speed = { 0, 0 }, rot = { 0, 90 },
	colour = { 1, 2 }, emission = { 1, 1 }, influence = { 0, 0 }, rate = 5, brightness = 2, shape = "Sphere", shapeStyle = "Surface",
}

-- Status icons ----------------------------------------------------------------------------------------------
P.plusUp = {
	tex = "plus", life = { 1, 1.5 }, size = { { 0, 0 }, { 0.2, 0.35 }, { 1, 0.25 } }, trans = { { 0, 0 }, { 0.7, 0.1 }, { 1, 1 } },
	speed = { 2, 3.5 }, spread = { 25, 25 }, drag = 0.5, colour = { 1, 2 }, emission = { 1, 0.7 }, influence = { 0, 0.3 }, rate = 3,
}
P.hearts = {
	tex = "heart", life = { 1, 1.6 }, size = { { 0, 0 }, { 0.2, 0.4 }, { 1, 0.3 } }, trans = { { 0, 0 }, { 0.7, 0.1 }, { 1, 1 } },
	speed = { 2, 3.5 }, spread = { 30, 30 }, drag = 0.6, rot = { -15, 15 }, hex = { "#FF7FB6", "#FF4F93" }, emission = { 1, 0.6 },
	influence = { 0, 0.3 }, rate = 3,
}
P.arrowsDown = {
	tex = "arrow_down", dir = "Bottom", life = { 0.7, 1 }, size = 0.35, trans = { { 0, 1 }, { 0.2, 0.1 }, { 1, 1 } },
	speed = { 2, 3 }, spread = { 10, 10 }, colour = { 2, 3 }, emission = { 1, 0.5 }, influence = { 0, 0.4 }, rate = 3,
	orient = "FacingCameraWorldUp",
}
P.drips = {
	tex = "raindrop", orient = "VelocityParallel", dir = "Bottom", life = { 0.4, 0.6 }, size = 0.3, trans = { { 0, 0.2 }, { 1, 0.6 } },
	speed = { 2, 4 }, spread = { 5, 5 }, accel = { 0, -30, 0 }, colour = { 1, 2 }, emission = { 0.5, 0.1 }, influence = { 0.3, 1 },
	rate = 6, shape = "Box", shapeStyle = "Volume",
}

-- Material / mood particles ---------------------------------------------------------------------------------
P.halo = { -- flat glowing ring locked above a head (refreshed continuously, so it never pops)
	tex = "ring", orient = "VelocityPerpendicular", life = { 0.6, 0.6 }, size = 1.6, trans = { { 0, 1 }, { 0.2, 0.15 }, { 0.8, 0.15 }, { 1, 1 } },
	speed = { 0.01, 0.01 }, spread = { 0, 0 }, colour = { 1, 2 }, emission = { 1, 1 }, influence = { 0, 0 }, rate = 5, locked = true, brightness = 2,
}
P.notes = {
	tex = "music_note", life = { 1.4, 2 }, size = { { 0, 0 }, { 0.15, 0.45 }, { 1, 0.35 } }, trans = { { 0, 0 }, { 0.75, 0.1 }, { 1, 1 } },
	speed = { 1.5, 2.5 }, spread = { 35, 35 }, rot = { -20, 20 }, rotSpeed = { -30, 30 }, hex = { "#FFFFFF", "#BDE3FF" }, emission = { 1, 0.4 },
	influence = { 0, 0.5 }, rate = 2, orient = "FacingCameraWorldUp",
}
P.zzz = {
	tex = "zzz", life = { 1.8, 2.4 }, size = { { 0, 0.2 }, { 1, 0.7 } }, trans = { { 0, 1 }, { 0.15, 0.1 }, { 0.8, 0.2 }, { 1, 1 } },
	speed = { 1, 1.6 }, spread = { 15, 15 }, accel = { 0.6, 0, 0 }, hex = { "#FFFFFF", "#CFE0FF" }, emission = { 0.9, 0.3 }, influence = { 0, 0.6 },
	rate = 0.7, orient = "FacingCameraWorldUp",
}
P.questions = {
	tex = "question", life = { 1.2, 1.8 }, size = { { 0, 0 }, { 0.2, 0.5 }, { 1, 0.4 } }, trans = { { 0, 0 }, { 0.75, 0.1 }, { 1, 1 } },
	speed = { 1, 2 }, spread = { 40, 40 }, rot = { -25, 25 }, rotSpeed = { -40, 40 }, hex = { "#FFFFFF", "#FFE58A" }, emission = { 1, 0.4 },
	influence = { 0, 0.5 }, rate = 1.5, orient = "FacingCameraWorldUp",
}
P.pixels = {
	tex = "pixel", life = { 0.15, 0.35 }, size = { { 0, 0.25 }, { 1, 0.15 } }, trans = { { 0, 0 }, { 1, 0.3 } }, speed = { 0, 1 },
	spread = { 180, 180 }, hex = { "#00FFFF", "#FF00FF", "#FFFFFF" }, emission = { 1, 1 }, influence = { 0, 0 }, rate = 0,
	shape = "Box", shapeStyle = "Volume",
}
P.confetti = {
	tex = "pixel", life = { 1.2, 2 }, size = 0.22, squash = { { 0, 0.6 }, { 0.5, -0.6 }, { 1, 0.6 } }, trans = { { 0, 0 }, { 0.85, 0 }, { 1, 1 } },
	speed = { 8, 14 }, spread = { 50, 50 }, accel = { 0, -14, 0 }, drag = 2, rot = { 0, 360 }, rotSpeed = { -400, 400 },
	hex = { "#FF4F6D", "#FFC93C", "#3CD3FF", "#7CFF6B", "#C77DFF" }, emission = { 0.6, 0.2 }, influence = { 0.3, 0.8 }, rate = 0,
}
P.sprinkles = {
	tex = "pixel", life = { 0.8, 1.2 }, size = 0.12, squash = { { 0, 2 }, { 1, 2 } }, trans = { { 0, 0 }, { 0.85, 0 }, { 1, 1 } },
	speed = { 0.5, 2 }, spread = { 180, 180 }, accel = { 0, -12, 0 }, rot = { 0, 360 }, hex = { "#FF6FAE", "#FFE15A", "#6FD6FF", "#8CFF7A", "#FFFFFF" },
	emission = { 0.4, 0 }, influence = { 0.3, 1 }, rate = 3, shape = "Box", shapeStyle = "Volume",
}
P.flakes = { -- falling bits (sawdust, crumbs, sand): coloured per use
	tex = "shard", life = { 0.8, 1.3 }, size = { { 0, 0.14 }, { 1, 0.1 } }, trans = { { 0, 0 }, { 0.85, 0 }, { 1, 1 } }, speed = { 0.2, 1 },
	spread = { 180, 180 }, accel = { 0, -14, 0 }, rot = { 0, 360 }, rotSpeed = { -300, 300 }, colour = { 2, 3 }, emission = { 0.2, 0 },
	influence = { 0.5, 1 }, rate = 3, shape = "Box", shapeStyle = "Volume",
}
P.fluff = {
	tex = "glow", life = { 2, 3 }, size = { { 0, 0.15 }, { 0.5, 0.3 }, { 1, 0.2 } }, trans = { { 0, 1 }, { 0.2, 0.3 }, { 1, 1 } }, speed = { 0.3, 1 },
	spread = { 180, 180 }, accel = { 0, 0.4, 0 }, drag = 1, hex = { "#FFFFFF", "#F2EEF8" }, emission = { 0.5, 0 }, influence = { 0.3, 1 }, rate = 2,
}
P.feathers = {
	tex = "leaf", life = { 2.2, 3.2 }, size = 0.4, trans = { { 0, 1 }, { 0.1, 0 }, { 0.85, 0 }, { 1, 1 } }, speed = { 0.5, 1.5 },
	spread = { 180, 180 }, accel = { 0, -1.2, 0 }, drag = 1, rot = { 0, 360 }, rotSpeed = { -90, 90 }, hex = { "#FFFFFF", "#EDE8E0" },
	emission = { 0.4, 0 }, influence = { 0.4, 1 }, rate = 1,
}
P.coins = {
	tex = "star", life = { 0.6, 1 }, size = { { 0, 0 }, { 0.3, 0.35 }, { 1, 0 } }, speed = { 1, 3 }, spread = { 180, 180 }, accel = { 0, -4, 0 },
	rot = { 0, 90 }, rotSpeed = { -200, 200 }, hex = { "#FFF6C2", "#FFD54A", "#E0A21B" }, emission = { 1, 0.8 }, influence = { 0, 0.3 }, rate = 3,
	brightness = 2,
}

local Presets = {}
Presets.List = P

function Presets.get(name: string): Preset?
	return P[name]
end

--- Every texture name used by any preset (for catalogue/asset validation).
function Presets.textures(): { [string]: boolean }
	local out = {}
	for _, p in P do
		out[p.tex] = true
	end
	return out
end

return Presets
