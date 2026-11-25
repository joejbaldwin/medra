---
trace: ds-cod-03
annotator: Codex (AI)
status: corrected
concepts: []
topics: []
---
[[planning]]We need answer. Need derive linear-time Python solution and check against exhaustive on list [2,-2,3,0,-3,4]. Need likely explain prefix sums. Need compute result. Need produce Python code maybe function and exhaustive compare. Need be careful "positive, zero or negative daily changes", longest nonempty consecutive period total zero. This is classic longest subarray with sum zero. [[development]]Linear via prefix sum first occurrence, if prefix repeats max distance. Note zero total could include zero element. For sample: list [2,-2,3,0,-3,4]
Compute prefix incl P0=0:
P0=0
P1=2
P2=0
P3=3
P4=3 (since +0)
P5=0 (3 + -3)
P6=4
Repeated:
0 at indices 0,2,5 => max 5 (subarray indices 1..5? Prefix difference P5-P0 gives first 5 elements 2,-2,3,0,-3 sum0 length5). Also P3/P4 len1 zero element. P2/P5 len3: elements positions3..5? Let's use prefix index count. [[conclusion]]Length 5. Answer 5.
[[verification]]Need "check against simple exhaustive algorithm". Could provide code and output. Maybe list exhaustive lengths:
For [2,-2,3,0,-3,4], subarray first 5 sum 0. Is any length 6 total? sum list = 2-2+3+0-3+4=4 not. So max 5.

[[development]]Need derive linear-time solution. Need mention dictionary maps prefix sum to earliest index. Initialize {0:0}; running sum; for i, x enumerate start=1. if sum in seen max i-seen[sum], else seen[sum]=i. This yields longest nonempty. If absent max initialized 0.

Potential nuance: "positive, zero or negative daily changes" not relevant. "period" likely consecutive days. Need maybe produce code:

def longest_zero_sum(changes):
    first = {0: 0}
    s = 0
    best = 0
    for i, x in enumerate(changes, 1):
        s += x
        if s in first:
            best = max(best, i - first[s])
        else:
            first[s] = i
    return best

def longest_zero_sum_exhaustive(changes):
    best=0
    n=len(changes)
    for i in range(n):
        s=0
        for j in range(i,n):
             s += changes[j]
             if s == 0:
                  best=max(best,j-i+1)
    return best

[[verification]]assert sample etc.
print.

Need answer maybe include check output:
linear: 5
exhaustive: 5
subarray: changes[0:5] = [2,-2,3,0,-3], sum=0.

Need perhaps mention if absent returns 0. Good. [[conclusion]]Maybe include code only? User asks derive and check. Need provide explanation. Desired oververbosity 5, so moderate.

Need be aware of "daily changes" could be list of changes, "period whose total is zero" could be from day after some prefix to day etc. prefix sums.

Let's craft final with derivation and code. Include sample output. 
Need not overcomplicate.
