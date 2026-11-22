---
trace: en-cod-lru
annotator: claude-draft
status: draft
concepts: [LRU cache, doubly linked list, hash map, node, capacity, sentinel, dict, OrderedDict]
topics:
- [node, prev, head, tail, sentinel, front]
- [dict, hash map, key, lookup]
- [capacity, cache, recency]
- [value, None, sentinel value]
---
[[planning]]We need answer. Need design LRU cache in Python get/put O(1) without OrderedDict. Explain data structures. Likely provide class using dict + doubly linked list. Need code. Need maybe mention thread safety? Not required. Need show sentinel nodes, Node class. [[development]]Implement capacity positive. get: if key not in map return -1 (or None). Move to front. put: if exists update and move; else create; if over capacity remove tail; add front. Need explain hash map provides O(1) key lookup; doubly linked list maintains recency order with O(1) node removal/insertion. Dict maps key to node, not value. Need mention why not single linked list: need remove arbitrary node on access/update without predecessor; doubly linked allows prev. Sentinel head/tail simplify edge cases. O(1) average due to dict. Space O(capacity). Could include code. Need maybe if capacity 0? Handle. Let's craft robust.

[[planning]]Need maybe test? Not necessary but can include usage.

[[development]]Need be careful: Python dict insertion order not used? We don't rely on it. Using dict as hash map only. Node prev/next. Order: head.next most recently used, tail.prev least recently used. _add_front and _remove methods. On get move to front. put existing update value and move front. New if capacity 0 return; create node insert dict and front; if len > capacity remove LRU: node = tail.prev; remove; del cache[node.key].

Need maybe use type hints. Need maybe "average O(1)" due to hash collisions worst-case but standard.

Need explain "without OrderedDict". Good.

[[planning]]Need answer with code and explanation. Desired oververbosity 5, not too lengthy. [[verification]]Ensure no hidden issue: get returns -1 as common LeetCode. If value None allowed? Use sentinel? get existing with value None should return None not -1? Common use integer. Could mention adjust sentinel. Maybe better implement get returns None if missing? Prompt says LRU cache get/put, no return spec. Use -1 standard. We can say return -1 for missing. Or use Optional. Need design. Let's craft.

[[development]]Code:

class _Node:
    __slots__ = ("key","value","prev","next")
    def __init__(self, key=None, value=None):
        self.key=key
        self.value=value
        self.prev=None
        self.next=None

class LRUCache:
    def __init__(self, capacity: int):
       if capacity < 0: raise ValueError
       self.capacity=capacity
       self.cache={}
       self.head=_Node()
       self.tail=_Node()
       self.head.next=self.tail
       self.tail.prev=self.head

    def _remove(self, node):
       p=node.prev; n=node.next
       p.next=n; n.prev=p
       node.prev=node.next=None

    def _add_to_front(self,node):
       node.prev=self.head
       node.next=self.head.next
       self.head.next.prev=node
       self.head.next=node

    def _move_to_front(self,node):
       self._remove(node); self._add_to_front(node)

    def get(self, key):
       node=self.cache.get(key)
       if node is None: return -1
       self._move_to_front(node)
       return node.value

    def put(self,key,value):
       if self.capacity == 0: return
       node=self.cache.get(key)
       if node is not None:
          node.value=value
          self._move_to_front(node)
          return
       new=_Node(key,value)
       self.cache[key]=new
       self._add_to_front(new)
       if len(self.cache)>self.capacity:
          lru=self.tail.prev
          self._remove(lru)
          del self.cache[lru.key]

[[verification]]Need note: cache.get returns None if key missing, but if node could be None? no. Good.

Could mention if values can be None still node not None. get returns -1 missing; existing None returns None. Fine.

[[conclusion]]Need final.
