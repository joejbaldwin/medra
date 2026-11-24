---
trace: en-cod-anagrams
annotator: Kostya
drafted_by: Claude (AI assistant), to be corrected
status: corrected
concepts: [anagram, sorting key, letter count, Counter, empty string, uppercase, casefold, group]
topics:
- [anagram, word, group, key]
- [Counter, count, letter, alphabet]
- [uppercase, casefold, case, empty string]
---
[[planning]]We need answer. Need write Python function groups anagrams. Compare sorting-based key vs letter-count key. Discuss uppercase and empty strings. Need likely include code and explanation. Need not use analysis. We need craft final. Need think thoroughly.

Question: "Write a Python function that groups a list of words into anagrams, for example ['eat','tea','tan','ate','nat','bat']. Compare a sorting-based key with a letter-count key, and discuss uppercase letters and empty strings."

[[planning]]Need provide Python function. Maybe one function with sorting, and compare alternative key using counts. Need discuss uppercase letters and empty strings. Need decide output format: list of groups or dict? "groups a list of words into anagrams" likely return list of lists. Example output [['eat','tea','ate'],['tan','nat'],['bat']] or preserving order. Need mention order depends on insertion order. Need uppercase: either case-insensitive by lowercasing or case-sensitive by default. Empty strings: all empty strings are anagrams of each other; if one empty string, group ['']. Need decide behavior. [[development]]Need compare sorting key O(n k log k) per word vs counting O(n k + alphabet) or O(n k) with dict, better for long words? Letter-count key uses tuple(sorted(Counter)) or tuple(counts). But Unicode? Need consider uppercase and empty. Need maybe use collections.defaultdict.

[[development]]Need write robust function:

from collections import defaultdict
from collections import Counter

def group_anagrams(words, case_sensitive=True):
    groups = defaultdict(list)
    for word in words:
        key_word = word if case_sensitive else word.lower()
        key = tuple(sorted(key_word))
        groups[key].append(word)
    return list(groups.values())

[[alternative]]Or using count key:
def group_anagrams_count(words, case_sensitive=True):
    groups = defaultdict(list)
    for word in words:
        key_word = word if case_sensitive else word.lower()
        counts = [0]*? But for Unicode can't use 26. Use dict of counts sorted by char? Could use tuple(sorted(Counter(key_word).items())) but that's sorting distinct chars, less than full sort maybe. Better: key = tuple(sorted(Counter(key_word).items())) or tuple(Counter(key_word)[c] for c in sorted(set(...)))? Need compare. General alphabet: tuple(sorted(Counter(s).items())). But for anagrams, sorting-based key uses sorted string; letter-count key uses counts of characters. For ASCII lower, [0]*26 maybe. But uppercase discussion means case handling.

[[development]]Need provide comparison. Sorting-based key simple, correct, handles Unicode by code point, empty string gives empty tuple. Complexity O(total characters log k) maybe per word. Letter-count key O(total chars + distinct chars log distinct) to canonicalize; if fixed alphabet (26 letters), O(total chars). It avoids sorting all letters, can be faster for long words, but more code and must handle arbitrary alphabet/Unicode and case. Need mention sorting key returns same key for permutations; counts key returns same counts. Empty string: sorted('') = '', tuple? If key=tuple(sorted(word)) => (). Counter('') empty; tuple(sorted(Counter('').items())) => (). All empty strings group. But if using ''.join(sorted(...)) returns '' too. Need mention if you filter empty strings, then no group. If case-insensitive, lower before key; this merges 'Eat' and 'eat'. If case-sensitive, treats uppercase and lowercase as distinct letters. Need mention preserving original words in output or normalized? We append original word, so output preserves input. If case-insensitive grouping, keys normalized but original words preserved. If you want output normalized, append key_word.

[[conclusion]]Need perhaps answer with code both implementations and compare. Need maybe mention if using sorting-based key with Counter? Let's craft.

Potential final:

```python
from collections import defaultdict, Counter
from typing import Iterable, List

def group_anagrams_sort(words, *, case_sensitive=True):
    groups = defaultdict(list)
    for w in words:
        norm = w if case_sensitive else w.lower()
        key = tuple(sorted(norm))
        groups[key].append(w)
    return list(groups.values())

def group_anagrams_count(words, *, case_sensitive=True):
    groups = defaultdict(list)
    for w in words:
        norm = w if case_sensitive else w.lower()
        key = tuple(sorted(Counter(norm).items()))
        groups[key].append(w)
    return list(groups.values())
```

Example:

```python
words = ['eat','tea','tan','ate','nat','bat']
print(group_anagrams_sort(words))
# [['eat', 'tea', 'ate'], ['tan', 'nat'], ['bat']]
print(group_anagrams_count(words))
# same

print(group_anagrams_sort(['Eat', 'tea', 'ate']))
# [['Eat'], ['tea', 'ate']] by default case-sensitive
print(group_anagrams_sort(['Eat', 'tea', 'ate'], case_sensitive=False))
# [['Eat', 'tea', 'ate']]
print(group_anagrams_sort(['', '', 'a']))
# [['', ''], ['a']]
```

[[verification]]Need be careful: If default case_sensitive=True, 'Eat' and 'tea'? 'Eat' sorted ('E','a','t'), 'tea' sorted ('a','e','t') -> not same. 'ate' sorted ('a','e','t') so tea and ate group. Yes.

For Counter key using tuple(sorted(Counter(norm).items())). For empty string: Counter('') empty; tuple(sorted(...)) == (). For two empty strings group. For 'a' key (('a',1),). Fine.

[[development]]Need discuss uppercase: Python sorting compares Unicode code points; 'A' < 'a'; so case-sensitive. If you want case-insensitive, use `.casefold()` rather than `.lower()` for better Unicode (e.g. German ß). But if output original. Need mention casefold. However for letter-count key, casefold before Counter. For sorting key, casefold. Maybe include casefold note. Empty strings: sorting key returns empty tuple; Counter key returns empty tuple. All empty strings are mutually anagrams (they have same empty multiset). If empty strings should be ignored, `if not w: continue`. If you want to include them as a group, code naturally groups them. Need mention whitespace? Not asked. Need not overdo.

[[development]]Need compare sorting-based key vs letter-count key in table:

- Sorting key: `''.join(sorted(norm))` or tuple(sorted(norm)). Simple, stable, handles any hashable chars. Time per word O(k log k), total O(∑ k_i log k_i). Memory O(k) per key. Empty -> '' or (). Case: normalize first. For short words simple; for long words with many repeated letters sorting does more work than needed.
- Count key: `tuple(sorted(Counter(norm).items()))` or for known alphabet `tuple(counts)`. Time O(k + d log d) where d distinct chars (or O(k + A) if fixed alphabet). More efficient for long words/large repeated letters, but more complex; need choose alphabet or canonicalize counts. Counter items sorted by char necessary so dict order doesn't affect key. Handles Unicode. Empty -> (). Case: normalize first. If using array of 26, only works for a-z and must normalize, handle non-letters. Counter general.

[[development]]Need maybe mention using `frozenset`? no.

Need output list of groups: `list(groups.values())` order of groups first occurrence, order within group input order (due to append). If need deterministic sorted groups, sort each group and/or groups. But example output maybe not sorted. Could include optional sorted return? Not necessary. But maybe user expects groups. We can say change to `return [sorted(g) for g in groups.values()]` if desired.

[[conclusion]]Need maybe provide function "group_anagrams" with sorting-based key. Then compare. The prompt: "Write a Python function that groups a list of words into anagrams, for example... Compare a sorting-based key with a letter-count key, and discuss uppercase letters and empty strings." So final should include code for both and discussion. Need answer concise but sufficient. Desired oververbosity 5. Need not extremely long.

Need maybe include type hints. Ensure code works in Python. Let's craft final with sections.

Potential final:

```python
from collections import defaultdict, Counter
from typing import Iterable, List

def group_anagrams(
    words: Iterable[str], *, case_sensitive: bool = True
) -> List[List[str]]:
    groups = defaultdict(list)
    for word in words:
        norm = word if case_sensitive else word.casefold()
        key = tuple(sorted(norm))          # sorting-based key
        groups[key].append(word)
    return list(groups.values())

def group_anagrams_count(
    words: Iterable[str], *, case_sensitive: bool = True
) -> List[List[str]]:
    groups = defaultdict(list)
    for word in words:
        norm = word if case_sensitive else word.casefold()
        key = tuple(sorted(Counter(norm).items()))  # letter-count key
        groups[key].append(word)
    return list(groups.values())
```

Example:

```python
words = ['eat','tea','tan','ate','nat','bat']
print(group_anagrams(words))
# [['eat', 'tea', 'ate'], ['tan', 'nat'], ['bat']]
```

[[verification]]Need check order: words order: eat key ('a','e','t') group eat; tea same group append; tan key ('a','n','t') group tan; ate append eat group; nat append tan group; bat key ('a','b','t') group bat. So output as above. Yes.

[[conclusion]]Then discussion:

Sorting key:
- key = tuple(sorted(word.casefold())).
- Correct because sorted letters canonicalize all anagrams.
- Complexity O(k log k) per word; total O(sum k_i log k_i).
- Simple, works with any Unicode string; empty -> ().

Letter-count key:
- key = tuple(sorted(Counter(word.casefold()).items())) e.g. (('a',1),('e',1),('t',1)).
- Correct because anagrams have same character counts.
- Complexity O(k + d log d) per word, or O(k + alphabet) for fixed alphabet; often faster for long words. More code; must canonicalize dict (sort items) because dict order not a key. For fixed ASCII, can use 26-tuple.

Uppercase:
- Default case-sensitive: 'Eat' and 'eat' are different (different Unicode code points). Use case_sensitive=False or `.casefold()` to merge case variants; `.casefold()` better than `.lower()` for Unicode. Original words preserved in output.
- If case-insensitive, keys normalized, but output original spelling.

Empty strings:
- Empty string is an anagram of itself. Both keys become `()` so multiple `''` are grouped together: `[['', '']]` (or with other groups). If you don't want to include them, skip `if not word: continue`. If using `''.join(sorted(...))`, empty key is `''`; still groups.

Need maybe mention letter-count key with empty string: `Counter('')` empty. Sorting key tuple sorted empty. Good.

[[verification]]Need maybe mention if word is not str? no.

Need maybe mention if using `casefold` and original word: the key for 'Straße' and 'STRASSE' could be same? Actually casefold('Straße') = 'strasse'; casefold('STRASSE') = 'strasse'. Good. Sorting key then same. Counter same. Good.

[[conclusion]]Need ensure final answer not too verbose. Could include table.

Need answer likely final only. Need not mention "I". Use markdown.

Need consider if the user wants "Write a Python function" singular maybe include one function and comparison. But answer with both functions is fine.

Let's craft final. Keep code and discussion. Mention if you need list sorted groups? optional.

Potential final:

```
def group_anagrams(words, case_sensitive=True):
    ...
```

Then comparison.

Need maybe include "sorting-based key" and "letter-count key" as two choices. Could provide a function with `key_type="sort"`? Maybe simpler to show two functions. But question says "Write a Python function ... Compare..." We can provide one main function using sorting key, then alternative count key. That's good.

Need include code for example. Use `casefold` even though default true. For default true, no casefold. If case_sensitive=False, use casefold. Code:

```python
from collections import defaultdict, Counter
from typing import Iterable, List

def group_anagrams(words: Iterable[str], *, case_sensitive: bool = True) -> List[List[str]]:
    groups = defaultdict(list)
    for word in words:
        normalized = word if case_sensitive else word.casefold()
        key = tuple(sorted(normalized))
        groups[key].append(word)
    return list(groups.values())
```

Alternative:

```python
def group_anagrams_count(words: Iterable[str], *, case_sensitive: bool = True) -> List[List[str]]:
    groups = defaultdict(list)
    for word in words:
        normalized = word if case_sensitive else word.casefold()
        key = tuple(sorted(Counter(normalized).items()))
        groups[key].append(word)
    return list(groups.values())
```

Example output:

```python
words = ['eat','tea','tan','ate','nat','bat']
print(group_anagrams(words))
# [['eat', 'tea', 'ate'], ['tan', 'nat'], ['bat']]
```

Need maybe include "the group order follows first appearance, not alphabetically." Good.

Need mention "If you prefer a dict mapping key -> words, return groups instead". Not necessary.

Need answer with comparison maybe bullet.

Let's compose final with moderate detail.
