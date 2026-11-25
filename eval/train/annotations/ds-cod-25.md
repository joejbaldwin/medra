---
trace: ds-cod-25
annotator: Codex (AI)
status: corrected
concepts: []
topics: []
---
[[planning]]We need answer. Need parse request. Need write generator takes finite list of possibly infinite iterators and yields one item per live iterator per round in original order. Retire exhausted inputs without skipping one after them. Explain fairness and check first two rounds when middle iterator empty.

We need likely Python generator. Need be careful: finite list of possibly infinite iterators. "yields one item per live iterator per round in original order" Means round-robin over iterators, one item each per round, in original order, for live iterators. When an iterator exhausted, retire it. "without skipping the one after them" specifically when middle iterator empty, after trying middle and finding exhausted, in same round need still yield from next iterator, not skip it due to e.g. remove during iteration causing skip. Need generator that handles empty middle. Need check first two rounds when middle iterator is empty.

We need produce code. [[development]]Need decide behavior: each round, iterate over current live iterators in order, trying next on each. If StopIteration, remove and continue to next. If yielded, include. Need handle removal without skipping. If using while index loop over list, when remove at i, do not increment i, so next at same index. [[alternative]]Or collect survivors then next round? But requirement "per round" and "retire exhausted inputs without skipping the one after them" means in same round, after empty middle, next should be considered. If we collect survivors after round, the next might wait next round? Actually first round: if middle empty, we should still yield from right iterator in first round? Let's reason.

[[verification]]"yields one item per live iterator per round in original order. Retire exhausted inputs without skipping the one after them." Suppose iterators A (nonempty), B empty, C nonempty. Round 1: live are A,B,C. Try A yield a0. Try B exhausted retire. "without skipping the one after them": should not skip C. So yield C c0 in same round. Round 2: live A,C. Yield a1, c1 if available. If B were removed by looping `for it in iterators` with removal, C skipped. Need avoid.

But there is nuance: If B empty, after first round it is retired. Is C considered live at start of round? It was live at start (not known exhausted). So yes yield C in round 1. The phrase first two rounds check when middle iterator is empty likely demonstrate:
inputs [iter([1,2]), iter([]), iter([3,4])]
First round yields 1,3
Second round yields 2,4
If incorrectly skipped: first round 1; second round 2,3; etc. Need explain.

[[planning]]Need write generator. Let's design.

Option 1:

[[development]]def roundrobin(iterators):
    iters = [iter(it) for it in iterators]
    while iters:
        survivors = []
        for it in iters:
            try:
                yield next(it)
            except StopIteration:
                pass
            else:
                survivors.append(it)
        iters = survivors

[[verification]]Does this retire exhausted without skipping one after? Let's test with A,B,C. iters = A,B,C. for it in iters: A yield a0, survivors A. B next raises, not append. C next yields c0, survivors A,C. End iters=A,C. This does not skip C because for loop continues over original list even though not mutating. It retires B after round (survivors). This yields one per live iterator per round? At start round, B live? It wasn't known exhausted, but was exhausted. We attempted B, no yield. C yields. Good. But note B remains in `iters` during round but no yield; logically retired. Next round survivors exclude. Good. This is simple.

[[verification]]But does "per live iterator per round" mean if an iterator becomes exhausted during the round (by StopIteration) it is retired; if an iterator yields its last item, it's still considered live for rest of current round? It only gets one yield per round anyway. It will be attempted next round and retired. That's fine.

Potential issue with list of maybe infinite iterators. For a list containing infinite iterators, loop never ends? The generator while iters: for each, yields one. If all infinite, infinite generator. That's expected. Finite list of possibly infinite iterators. If at least one infinite, generator infinite round robin; if some finite, they retire eventually. If all finite, terminates.

But if `iters` contains an iterator that is itself a Python iterator. We should call iter on each initial to ensure. "possibly infinite iterators" likely already iterators. But robust.

Need consider "Retire exhausted inputs without skipping the one after them." The survivors approach doesn't mutate list during iteration; it evaluates all original entries in round. It doesn't skip. But does it "retire" after the round? It removes exhausted from next round. If middle empty, first round still attempts B then C. Good.

[[alternative]]Alternative while-index mutation:

def roundrobin(iterators):
    iters = [iter(x) for x in iterators]
    while iters:
        i = 0
        while i < len(iters):
            try:
                yield next(iters[i])
                i += 1
            except StopIteration:
                del iters[i]  # do not increment i
This yields one per live per round, but subtle: if an iterator exhausts during the round, it is removed immediately, and next iterator at same index (former i+1) will be processed. This also works. If C yields, i increments. At end round, if A yielded its last item (not yet StopIteration), it remains; next round attempt A raises, remove, then B? Wait B and C? Need be careful with removal and same round.

[[verification]]Let's simulate A=[1], B empty, C=[3]. Start i=0 iters A,B,C. try A yield 1 i=1. try B StopIteration del index1 -> iters A,C, i remains1. while i<2: try iters[1]=C yield3 i=2. End round. iters A,C. Round2: i=0 try A StopIteration del index0 -> iters C, i remains0. while i<1: try C StopIteration del index0 -> iters [], i remains0. End. This retires A at start of round2, then C also attempted and exhausted in same round2 (though C had no item after round1). Is that okay? Round 2 live at start A,C. A exhausted, retire; C also exhausted? It was live at start, but had no items. It gets attempted and retired same round. That seems fine. But if C had [3,4], Round1 yields A1, C3. Round2: A exhausted removed, then C4 yielded. So C gets its second item in round2 despite A retired before C. Is that fair? [[verification]]Let's compare survivors approach:
Round1 iters A,B,C: A yield1 survivors A; B Stop none; C yield3 survivors A,C. End round iters A,C.
Round2: A next Stop none; C next yield4 survivors C. End iters C.
Round3: C next Stop none. End. It yields C4 in round2. Same. Good.

If A=[1,2], B=[], C=[3,4]. Mutation method:
Round1: A1, B stop remove, C3 -> iters A,C.
Round2: A2, C4 -> iters A,C.
Round3: A stop remove i0 -> C stop remove -> terminate. Survivors:
Round1 A1,C3; Round2 A2,C4; Round3 retire. Same.

[[alternative]]Potential difference if an iterator yields last item in round and later another iterator empty. Survivors defers removal of last item until next round; mutation removes empty immediately. But yields same sequence? [[verification]]Let's test A=[1], B=[], C=[3,4]. Mutation:
Round1: A1 (i=1), B stop remove, C3 (i=2) end iters A,C.
Round2: A stop remove i0, C4 yield i1? Let's step: i=0, A Stop delete A -> iters C, i=0. while i<1, next C yields 4, i=1. End. Round3: C stop remove. Sequence A1,C3,C4. Survivors:
Round1 A1, B stop, C3. survivors A,C.
Round2 A next Stop no survivor, C next 4 survivor C. End iters C.
Round3 C stop. Sequence A1,C3,C4. Same.

What about A=[1], B empty, C=[3]. Mutation yields A1, C3; Round2 A retire then C retire no yields. Survivors yields same. Good.

But "yields one item per live iterator per round" with immediate retirement: If A exhausts at start of round2, then C yields in round2. C still one item in round2. Fine.

[[development]]Need "Explain fairness" likely fairness means no live iterator is starved: each round visits all currently live iterators in order, at most one item per round per iterator; infinite inputs progress equally; finite exhaustion doesn't cause later items to be ignored or reordered. But if some iterators infinite and a finite one? The generator will eventually retire finite and continue. If one iterator takes long to produce next (blocking), round-robin blocks on next for that iterator; fairness is about scheduling attempts, not time/blocking. Need mention.

[[verification]]Need "check the first two rounds when the middle iterator is empty." Provide example. Let's choose:
a = iter([1])
b = iter([])
c = iter([3,4,5])? Need two rounds show. We can use [1,2] and [3,4] to show two rounds:
inputs = [iter([1,2]), iter([]), iter([3,4])]
Round 1: try first -> yield 1; try middle -> StopIteration, retire; try third -> yield 3. Output so far: 1, 3.
Round 2: live [first, third]. first -> yield 2; third -> yield 4. Output 2,4.
Then round 3: both exhaust. Need check "first two rounds when middle iterator is empty" yes.

But note if first has [1,2] and third [3,4], after round2 first yields 2 (its last), third yields4 (last). Round3 will retire both. Sequence 1,3,2,4. If middle empty were mishandled by deleting during for, first round might be 1, then? Let's see. But explain.

[[conclusion]]Need decide final answer format. Include generator code, fairness explanation, round check. Desired oververbosity 5. Provide concise but complete.

Need consider Python code details. Let's write:

from collections.abc import Iterable, Iterator
from typing import TypeVar, Iterable, Iterator

T = TypeVar("T")

def round_robin(iterables: Iterable[Iterable[T]]) -> Iterator[T]:
    live = [iter(x) for x in iterables]
    while live:
        next_live = []
        for it in live:
            try:
                item = next(it)
            except StopIteration:
                continue
            else:
                yield item
                next_live.append(it)
        live = next_live

This is simple. [[verification]]But wait: We append to survivors only after yield. If consumer doesn't resume generator after yield, it may never append. But generator state semantics: The code after yield (append) runs when resumed. But if generator is abandoned, irrelevant. If resumed, append before next iteration. However subtle: If `yield item` and then consumer throws? Not relevant.

But there is a subtle issue: In this implementation, for each iterator, we call next before yield; after yield, append to next_live. If consumer stops after some yields, no matter. If consumer resumes, append. At end of for, live = next_live. It works.

But consider if `yield` raises GeneratorExit, not relevant.

Potential issue: `next_live.append(it)` after yield means the survivor list is built after each yield. Suppose the consumer sends value into generator? `yield item` returns sent value ignored, then append. Fine. Suppose consumer calls `.throw`? Not relevant.

[[alternative]]Could write append before yield to avoid any weirdness:
try:
    item = next(it)
except StopIteration:
    pass
else:
    next_live.append(it)
    yield item
This is cleaner: mark survivor before yielding. If consumer stops, no difference. Use this.

[[development]]Code:

def round_robin(iterators):
    live = [iter(it) for it in iterators]
    while live:
        survivors = []
        for it in live:
            try:
                item = next(it)
            except StopIteration:
                continue
            else:
                survivors.append(it)
                yield item
        live = survivors

[[verification]]Does this retire exhausted without skipping? It doesn't remove during iteration; survivors excludes exhausted after they are encountered. It continues to next in same `for`, so no skip. Good.

Need maybe mention if an iterator raises StopIteration from inside? In Python, if an iterator's __next__ raises StopIteration, it's considered exhausted. If it raises RuntimeError? no.

[[development]]Need fairness: Because each round processes each live iterator once in original order. An iterator that yields is kept for next round. Exhausted ones removed. No iterator is advanced more than once per round, so a slow or infinite iterator doesn't starve others. If one iterator blocks, round-robin can't preempt it; fairness is cooperative.

Need discuss if middle empty: We use snapshot `live` list for the round, so when middle raises StopIteration, we `continue` to third in same round. We don't delete from list while iterating, avoiding skipped next element. In next round, middle absent.

Need maybe note original order: We preserve list order. In each round, yields in current live order, which remains original order because we only filter, never reorder. If middle exhausted, third shifts left but still after first.

[[planning]]Potential question "Write a generator which takes a finite list of possibly infinite iterators and yields one item per live iterator per round in original order. Retire exhausted inputs without skipping the one after them. Explain fairness and check the first two rounds when the middle iterator is empty."

Maybe they expect code and explanation. Could mention if using `list.pop()` during `for` causes skip. We'll use survivors.

Let's think deeply about definitions. "takes a finite list of possibly infinite iterators" Could be Python 3. "generator" maybe class or function. We can provide function.

[[verification]]Could there be an edge case: empty input list. Generator returns immediately. `live=[]`, while false. Good.

Could there be an iterator that is empty and is the middle. The first round: we call next on first, yield first item; call next on middle, StopIteration; continue to third, yield third item. Good.

[[conclusion]]Let's produce answer with code block.

Maybe include type hints:

from typing import Iterable, Iterator, TypeVar

T = TypeVar("T")

def round_robin(iterators: Iterable[Iterator[T]]) -> Iterator[T]:
    live = [iter(it) for it in iterators]
    while live:
        survivors = []
        for it in live:
            try:
                item = next(it)
            except StopIteration:
                continue
            else:
                survivors.append(it)
                yield item
        live = survivors

Note iterators input type: `Iterable[Iterable[T]]` maybe because list of iterators. Use `Iterable[Iterable[T]]`. If already iterators, `iter(it)` returns itself. Good.

Then example:
it = round_robin([iter([1,2]), iter([]), iter([3,4])])
print(list(it))  # [1,3,2,4]

But wait `list(it)` will continue until all exhausted. Let's simulate final: Round1 yields 1,3. survivors [first, third]. Round2 yields 2,4. survivors [first, third] because first yielded 2 (last item) and third yielded4 (last). Round3: first next Stop, third next Stop, survivors empty. So list [1,3,2,4]. Good.

Check first two rounds:
Round 1:
- live = [A,B,C]
- A next -> 1 (survives)
- B next -> StopIteration, retire (no yield)
- C next -> 3 (survives)
output: 1,3; survivors A,C
Round 2:
- A next -> 2 (survives)
- C next -> 4 (survives)
output: 1,3,2,4; survivors A,C
Round 3 would attempt A and C, both StopIteration, retire, terminate.

Maybe mention if middle empty and correct handling: B is retired but C is not skipped in round1. If we had deleted B while iterating a list with `for` and index, C might be skipped. Our survivors approach avoids that.

Need answer "Explain fairness" more detailed. Fairness: round-robin. Each live iterator gets at most one `next()` per round; all live iterators are attempted before any gets a second. Since order is original, deterministic. Infinite iterators will not starve finite ones except finite eventually exhaust; no live iterator is skipped due to an exhausted predecessor. However if an iterator's `next()` blocks, the generator blocks and cannot be preemptive; fairness assumes `next()` returns or raises promptly. Also if all live iterators are infinite, generator never terminates and yields infinitely. If some finite, they retire and order among remaining preserved.

[[verification]]Let's consider if there is any issue with "one item per live iterator per round" and our survivors list after yielding. Suppose an iterator is exhausted but not yet retired (because it yielded last item in round). In next round it is still considered live at start, we call next and retire. That's standard. If strict definition says after yielding last item, it should be known exhausted and retired immediately? Cannot know without extra lookahead, which would advance it an extra time. Our behavior is correct. It may cause an empty iterator after last item to be attempted in next round, but no yield. Does that affect "one item per live iterator per round"? It doesn't yield an extra item. It only incurs an extra `next()` attempt at start of next round. If a finite iterator had exactly N items, it yields N times, then retirement attempt. Fine.

[[alternative]]Potential alternative: The generator could use `yield from`? No.

Let's maybe include a note: "This does not try to prefetch to discover exhaustion after the last yielded item; it discovers it on the next round. That is normal and does not change the yielded sequence." Could be useful but not necessary.

[[conclusion]]Let's ensure final answer doesn't overdo. We'll include code, explanation, example.

Need maybe include "finite list" means input list finite; iterators may be infinite. Our `live` list finite, but if any iterator infinite, while loop infinite. That's expected.

Let's craft final response:

```python
def round_robin(iterables):
    live = [iter(x) for x in iterables]
    while live:
        survivors = []
        for it in live:
            try:
                value = next(it)
            except StopIteration:
                continue
            else:
                survivors.append(it)
                yield value
        live = survivors
```

Then fairness paragraph.

Then example:
A = iter([1, 2])
B = iter([])
C = iter([3, 4])
g = round_robin([A, B, C])
First two rounds:
Round 1: A gives 1; B raises StopIteration and is retired; C still gives 3 -> yields 1,3.
Round 2: live A,C; A gives2; C gives4 -> yields 2,4.
Thus first two rounds are `[1,3]` and `[2,4]`; flattened sequence begins `1,3,2,4`. Middle empty did not cause C to be skipped: B was retired but the loop continued to C in same round.

Need maybe mention "original order" maintained. Good.

Let's final.
