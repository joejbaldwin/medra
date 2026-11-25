---
trace: ds-cod-26
annotator: Codex (AI)
status: corrected
concepts: []
topics: []
---
[[planning]]We need answer. Need parse task. "Implement dense and competition ranking for scores in arbitrary order, returning ranks aligned to original input with highest score ranked 1. Use [70,90,90,80,70] to test distinction. Discuss how to avoid sorting all n entries when there are only u distinct scores."

We need likely provide implementation? Need explain dense ranking vs competition ranking. Need use example. Need discuss avoid sorting all n entries when only u distinct scores. Need maybe in Python. Need clearly define highest score ranked 1.

[[development]]Dense ranking: ties same rank, next distinct rank increases by 1. For [70,90,90,80,70], descending unique [90,80,70], ranks: 90->1, 80->2,70->3. Aligned input: [3,1,1,2,3].

Competition ranking ("standard competition"/1224): ties same rank, next rank skips based on count. Descending sorted positions: 90 position1, 90 position1, 80 position3, 70 position4, 70 position4. Aligned: [4,1,1,3,4]. [[verification]]Wait input [70,90,90,80,70]: indices: 70 rank 4, 90 rank1, 90 rank1, 80 rank3, 70 rank4. Yes.

[[development]]Need discuss avoid sorting all n entries when only u distinct scores. Since ranks depend only on distinct scores, can compute ranking of unique values, then map each original score to rank via dict/hash. Complexity O(n + u log u) time and O(n+u) for output/map? Actually to get unique scores can use hash set O(n) avg, sort u unique O(u log u), dictionary score->rank O(u), map original O(n). Better than sorting n O(n log n) especially u << n. If input order arbitrary and need aligned, we scan n to output. [[alternative]]If scores bounded/integer maybe use counting/radix/bucket sort to get unique in O(n + range) or O(n+u). Or order statistics with balanced trees? But for ranking need relative order of distinct scores. Could use iterative selection? Not generally avoids O(u log u) comparison? Need discuss.

[[conclusion]]Could avoid sorting all n but must determine ordering of u distinct values. We can deduplicate first. [[alternative]]Alternative if stream and need ranks online: use balanced BST/order-stat tree with duplicate counts, compute rank of each score as it arrives? To assign competition rank, need number of elements greater plus 1. With ordered multiset supporting count greater in O(log u) per item, total O(n log u) and store output. Dense rank: need number of distinct scores greater +1. We can use Fenwick over compressed scores or balanced tree. But compression requires unique sorted. If all values known, dedupe+sort unique. If streaming, balanced tree. [[conclusion]]But question "when there are only u distinct scores" likely answer: sort unique values not all n. [[alternative]]Also mention if using SQL? "Implement dense and competition ranking for scores in arbitrary order, returning ranks aligned to original input with highest score ranked 1." Could be asking for code and discussion. Need maybe include SQL? Wording "Implement dense and competition ranking" maybe from coding. Need decide language. Provide Python function. Could also mention SQL RANK and DENSE_RANK? But "returning ranks aligned to original input" suggests code.

[[conclusion]]Let's craft answer with Python implementation.

Need be precise for competition ranking with duplicates: Formula: For distinct value sorted descending with cumulative counts:
- competition rank of first occurrence of value v = total count of scores greater than v + 1. Equivalent in descending order, rank for group = current 1-based position (including duplicates), then after group advance by multiplicity.
- dense rank for v = number of distinct scores greater + 1.

Implementation options:
1. Sort unique scores descending. Build rank maps:
```
def ranks(scores, dense=True):
    uniq = sorted(set(scores), reverse=True)
    if dense:
        rank = {v:i+1 for i,v in enumerate(uniq)}
        return [rank[x] for x in scores]
    # competition
    rank={}
    current_rank=1
    counts = Counter(scores) # O(n)
    for v in uniq:
        rank[v]=current_rank
        current_rank += counts[v]
    return [rank[x] for x in scores]
```
This is O(n + u log u) time, O(n + u) memory. But for competition, current_rank can be computed without sorting all n. Need Counter O(n). Could build counts while dedupe. Or just use sorted unique and count dictionary. [[verification]]Example:
```
scores=[70,90,90,80,70]
dense_ranks(scores) -> [3,1,1,2,3]
competition_ranks(scores) -> [4,1,1,3,4]
```
Need ensure dense rank for 70 -> 3, 90 ->1,80->2. Aligned [3,1,1,2,3]. Competition as above.

[[alternative]]Potential alternative using `bisect` on sorted unique and prefix counts. For each score map via dict.

[[development]]Discussion avoid sorting all n: Use set/dict to find u distinct scores, sort just those. Build mapping from each distinct score to its rank. Then linear pass to produce aligned ranks. Complexity O(n + u log u), better than O(n log n) when u << n. If score domain small/integer, use counting/array to get distinct ordered in O(n + range) (or O(n+u) after range) and avoid comparison sort. For streaming: maintain ordered multiset of distinct scores with subtree sizes/counts; query number greater or distinct greater in O(log u) per score; total O(n log u). If offline but need memory, no need sort all n.

Need perhaps mention "arbitrary order" and "aligned to original input" means don't sort the original; sort only unique or use maps.

Need perhaps address "highest score ranked 1", if ascending rank? Use reverse=True.

[[verification]]Need edge cases: empty list returns [], all same => dense [1,1,...], competition [1,1,...]. Negative values fine. NaN? Not needed.

Need maybe mention competition rank can use "RANK()" in SQL, dense "DENSE_RANK()". But not necessary.

[[alternative]]Let's think if there is any trick: The phrase "scores in arbitrary order, returning ranks aligned to original input" Could they ask "Implement dense and competition ranking for scores in arbitrary order" maybe in JavaScript? We can choose Python. Could mention with SQL window functions:
```
SELECT score,
       DENSE_RANK() OVER (ORDER BY score DESC) AS dense_rank,
       RANK() OVER (ORDER BY score DESC) AS competition_rank
FROM scores;
```
But aligned to original input requires order column. However question uses Python list likely. We can include both maybe. Desired oververbosity 5. Need not overdo. [[conclusion]]But include code, example, complexity, discussion.

Need maybe provide code with `collections.Counter`. Implementation:
```
from collections import Counter

def dense_rank(scores):
    unique = sorted(set(scores), reverse=True)
    rank = {score: i+1 for i, score in enumerate(unique)}
    return [rank[s] for s in scores]

def competition_rank(scores):
    counts = Counter(scores)
    unique = sorted(counts, reverse=True)
    rank = {}
    next_rank = 1
    for score in unique:
        rank[score] = next_rank
        next_rank += counts[score]
    return [rank[s] for s in scores]
```
Test:
```
scores = [70,90,90,80,70]
print(dense_rank(scores)) # [3, 1, 1, 2, 3]
print(competition_rank(scores)) # [4, 1, 1, 3, 4]
```
[[verification]]Need verify competition next_rank: Start next_rank=1. 90 count 2: rank[90]=1, next_rank=3. 80 count 1: rank[80]=3, next_rank=4. 70 count 2: rank[70]=4, next_rank=6. Aligned [4,1,1,3,4]. Correct.

Need maybe clarify if value sorted descending. `sorted(counts, reverse=True)` iterates keys. Good.

[[development]]Discussion of avoiding sorting all n:
- Distinct rank maps depend on sorted distinct values, not positions of duplicates.
- Deduplicate via set/Counter first: O(n). Sort u distinct values: O(u log u). Map. Produce ranks O(n).
- Total O(n + u log u) time vs O(n log n) for full sort. Memory O(n+u) if include input/output; extra O(u) for map/counts.
[[alternative]]- If scores are small integers, counting sort over min..max or dictionary + bucket can reduce sort to O(n+range) or O(n+u) after compression.
- For online/streaming, use balanced BST/Fenwick tree keyed by compressed scores: maintain counts (competition) or presence (dense). To get rank of x:
  - competition: #elements > x + 1 = n_seen - prefix_count(<=x?) [[backtrack]]Wait for each arriving score with all previous? If final ranks depend on all scores. For online final ranks, need process all first or compute rank after each insertion using current counts? Competition rank final = count greater +1 among all values. If input can be stored and unique compressed. Streaming with balanced tree can compute rank for each incoming if we insert counts before/after? If we insert x then count greater? Let's see: For final rank, need total count greater than x across all n. In online, if processing final after all known, can query final. Or process after building ordered stats. But if need ranks online as they arrive, ranks of previous elements can change as higher scores arrive. So not straightforward. But can maintain ordered multiset and output after all. [[conclusion]]The question likely about offline. If streaming and need final, use balanced tree to accumulate counts and then query each score; O(n log u). Or store scores and unique set.
  - Dense rank: number of distinct greater +1. Fenwick presence tree.
But maybe unnecessary. Keep brief.

Need mention "arbitrary order" and "aligned to original input" satisfied by mapping and reconstructing. Could also show equivalent SQL:
```
DENSE_RANK() OVER (ORDER BY score DESC)
RANK() OVER (ORDER BY score DESC)
```
But not needed. Maybe include note.

Need decide final structure:
1. Definitions.
2. Python code implementation.
3. Example output.
4. Efficient unique approach discussion.

Let's craft final with moderate detail. Need answer directly, no hidden analysis.

Potential issue: "competition ranking" sometimes called "standard competition" ranking with highest score rank 1 and ties get same rank, next rank skips. We align. Good.

Need perhaps include "dense vs competition distinction: 70 gets dense rank 3 vs competition rank 4" due to two 90s. Actually 80 has dense 2, competition 3. 70 dense 3, competition 4. Yes.

Need maybe include complexity line: `O(n + u log u)` time, `O(u)` extra space plus output. [[verification]]If using Counter plus set, O(u) extra. `sorted(set(scores))` creates set O(n) memory? Actually set of u. `Counter` O(u). Good.

[[conclusion]]Let's formulate.

Could also mention "don't call `.sort()` on scores list; it preserves input order." That's simple.

Let's provide final.
