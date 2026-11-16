--!strict
-- Shared response classification for provider adapters.

local Common = {}

export type Usage = { input: number, output: number, cacheRead: number, cacheWrite: number }
export type Parsed = {
	ok: boolean,
	text: string?,
	data: any?, -- already-parsed output (tool_use input)
	usage: Usage,
	retryable: boolean,
	auth: boolean,
	refusal: boolean,
	truncated: boolean,
	retryAfter: number?,
	err: string,
}

function Common.empty(err: string): Parsed
	return {
		ok = false, text = nil, data = nil, usage = { input = 0, output = 0, cacheRead = 0, cacheWrite = 0 },
		retryable = false, auth = false, refusal = false, truncated = false, retryAfter = nil, err = err,
	}
end

local function header(headers: any, name: string): string?
	if type(headers) ~= "table" then
		return nil
	end
	local lower = string.lower(name)
	for k, v in headers do
		if type(k) == "string" and string.lower(k) == lower then
			return tostring(v)
		end
	end
	return nil
end

-- Classify a non-2xx status. Returns a Parsed with ok=false.
function Common.httpError(response: any): Parsed
	local code = tonumber(response and response.StatusCode) or 0
	local p = Common.empty("HTTP " .. code)
	p.auth = code == 401 or code == 403
	p.retryable = code == 408 or code == 409 or code == 425 or code == 429 or code >= 500 or code == 0
	local ra = tonumber(header(response and response.Headers, "retry-after"))
	if ra then
		p.retryAfter = math.clamp(ra, 0, 60)
	end
	return p
end

return Common
