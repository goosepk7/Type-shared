--!strict
-- Tiny O(1) LRU cache (hash + doubly linked list).

local LRU = {}
LRU.__index = LRU

type Node = { key: string, value: any, prev: Node?, next: Node? }

export type LRU = typeof(setmetatable({} :: {
	capacity: number,
	size: number,
	map: { [string]: Node },
	head: Node?, -- most recent
	tail: Node?, -- least recent
	hits: number,
	misses: number,
}, LRU))

function LRU.new(capacity: number): LRU
	return setmetatable({
		capacity = math.max(1, capacity),
		size = 0,
		map = {},
		head = nil,
		tail = nil,
		hits = 0,
		misses = 0,
	}, LRU)
end

local function unlink(self: LRU, node: Node)
	if node.prev then
		node.prev.next = node.next
	else
		self.head = node.next
	end
	if node.next then
		node.next.prev = node.prev
	else
		self.tail = node.prev
	end
	node.prev, node.next = nil, nil
end

local function pushFront(self: LRU, node: Node)
	node.next = self.head
	node.prev = nil
	if self.head then
		self.head.prev = node
	end
	self.head = node
	if self.tail == nil then
		self.tail = node
	end
end

function LRU.get(self: LRU, key: string): any
	local node = self.map[key]
	if node == nil then
		self.misses += 1
		return nil
	end
	self.hits += 1
	if self.head ~= node then
		unlink(self, node)
		pushFront(self, node)
	end
	return node.value
end

function LRU.set(self: LRU, key: string, value: any)
	local node = self.map[key]
	if node then
		node.value = value
		if self.head ~= node then
			unlink(self, node)
			pushFront(self, node)
		end
		return
	end
	node = { key = key, value = value, prev = nil, next = nil }
	self.map[key] = node
	pushFront(self, node :: Node)
	self.size += 1
	while self.size > self.capacity do
		local t = self.tail
		if t == nil then
			break
		end
		unlink(self, t)
		self.map[t.key] = nil
		self.size -= 1
	end
end

function LRU.clear(self: LRU)
	table.clear(self.map)
	self.head, self.tail = nil, nil
	self.size = 0
end

return LRU
