---
trace: ds-cod-37
annotator: Codex (AI)
status: corrected
concepts: []
topics: []
---
[[planning]]We need answer. Need parse. Need write integer-only Python function downsample n ordered samples to k indices, retaining endpoints and placing targets at integer indices nearest to j*(n-1)/(k-1), ties toward smaller index. Need function for 2<=k<=n. Prove never emits duplicates and check case with exact half-integer target.

Need craft solution. Need think about tie rounding. Integer-only Python. Need output indices list length k? "Downsample n ordered samples to k indices" likely select k indices from 0..n-1 inclusive. Retain endpoints 0,n-1. For j=0..k-1 target = j*(n-1)/(k-1). nearest integer, ties smaller. Need generate. [[development]]But if simply round each target independently, with duplicates possible if n<k? Given k<=n and targets spaced (n-1)/(k-1) >=1. If spacing exactly 1? unique maybe endpoints. If spacing >1, no duplicates due monotonic increasing. [[verification]]Wait nearest rounding of strictly increasing values spaced >=1 can produce duplicates? Example targets 0, 1.1, 2.2 nearest 0,1,2 no. If spacing exactly 1: 0,1,2. Dups no. If spacing >1, distance >1 can round same? Suppose targets 0.6 and 1.6 round (ties?) 1 and 2 (if .6->1, 1.6->2) no. If targets 0.4 and 1.4 ->0 and1. Difference >=1. Rounding to nearest integer cannot duplicate if two values differ >=1? If difference exactly 1, e.g. 0.5 and 1.5 with tie smaller: 0 and1? Wait 0.5 target tie -> smaller 0 (assuming integer 0), 1.5 tie ->1. unique. If diff >1, unique? Consider a=0.6 ->1, b=1.6 ->2. a=0.4 ->0, b=1.4 ->1. Yes. If diff=1.0: a=0.0 ->0, b=1.0->1. a=0.1 ->0, b=1.1->1. a=0.9 ->1, b=1.9 ->2. unique. [[planning]]Need account ties toward smaller maybe function. So proof: indices nondecreasing and consecutive selected differ at least 1? Could show rounded values strictly increasing because q_{j+1}-q_j >=1 and rounding tie lower. [[development]]Need formal: let r(x)=floor(x+1/2 - epsilon?) For ties toward smaller, for x>=0, nearest integer ties down = floor(x + 1/2) except when x+1/2 integer? Wait floor(x+1/2) gives ties up, e.g x=0.5 -> floor(1)=1, but ties down should 0. Need formula. Need integer-only avoiding floats.

Need compute rounded nearest with ties toward smaller for numerator A = j*(n-1), denominator d=k-1. target = A/d. Need integer nearest, ties down. For x=A/d. We need q = floor(x + 1/2) with tie down. Equivalent floor((A + d/2? careful). Let's derive.

Round-to-nearest ties lower: q = floor(x + 1/2) except when fractional part exactly 1/2, choose floor x. floor(x+1/2) chooses ceil at .5. Need subtract epsilon: q = floor((A/d) + 1/2 - epsilon). Integer formula: q = (2*A + d - 1) // (2*d)? [[verification]]Let's test. For x=A/d. Want q such that q <= x+0.5? Tie down means q = floor(x + 0.5) if non-tie, for tie .5 use q= floor x = floor(x+0.5)-1. Formula floor((2A + d - 1)/(2d)). Because nearest with ties lower = floor((A + d/2 - tiny)?). More directly compare 2A to d*?

Standard rounding half down: q = floor((A + d/2 - epsilon)). For integer d maybe q = (2A + d - 1)//(2d). Test A/d=0.5: A=1,d=2 => (2+2-1)//4=3//4=0 correct. 1.5: A=3,d=2 =>(6+2-1)//4=7//4=1 correct. 2.4 d=5 A=12: (24+5-1)//10=28//10=2 (target 2.4 nearest2) correct. 2.5 A=5,d=2:(10+2-1)//4=11//4=2 correct ties down. 2.6 A=13,d=5:(26+5-1)//10=30//10=3 correct. Good.

[[alternative]]Could also use divmod: q, rem = divmod(2*A, d); if rem? Wait nearest tie lower. q = floor(A/d + 1/2 - epsilon). Formula easiest.

[[verification]]But potential issue j=0 target 0: (0 + d -1)//(2d)=0. j=k-1 A=(k-1)(n-1)=d(n-1). Formula q=(2d(n-1)+d-1)//(2d)=? For n maybe. Suppose n=5,k=3 d=2,j=2 A=8? target=4. formula (16+2-1)//4=17//4=4 correct. General gives n-1? A=d(n-1). (2d(n-1)+d-1)//(2d)= n-1 + (d-1)//2d? For d>=1 d-1<2d, floor n-1. correct.

[[development]]Need integer-only function. Python function:
def downsample_indices(n: int, k: int) -> list[int]:
    if not (2 <= k <= n): raise ValueError
    d = k - 1
    den = 2*d
    res = []
    for j in range(k):
        a = j * (n - 1)
        idx = (2*a + d - 1) // den
        res.append(idx)
    # endpoints exact automatically, but maybe set? retaining endpoints. For j=0, idx=0; j=k-1, idx=n-1. Could mention.
    return res

Need ensure tie smaller. [[verification]]Test exact half-integer target. Need find case. Need n,k such that j*(n-1)/(k-1) has fractional .5.

Need 2<=k<=n. Need some j. Example n=6,k=3? d=2, n-1=5, j=1 target=5/2=2.5. k=3 n=6. Indices:
j0=0
j1 target 2.5 tie lower =2 (formula: d=2; j=1 A=5; (2*5+2-1)//4=(10+1)//4=11//4=2)
j2=5. result [0,2,5]. Is 3 indices from n=6. Endpoints retained. Exact half target at j=1. Good.

[[development]]Need prove no duplicates. Need perhaps there is subtlety: nearest rounding of targets q_j. For j increasing, q_j strictly increasing? Target spacing = (n-1)/(k-1) >=1 because n>=k. Consecutive target difference δ >=1. Need prove rounding maps with tie down is strictly increasing for points distance >=1. Let's formalize.

Let x<y, y-x>=1. Let r(t)= nearest integer to t ties down. Need r(y)>r(x). Is that always true for x,y nonnegative? Let's prove. Suppose by contradiction r(y)<=r(x). Since y>x, nearest rounding nondecreasing, so r(y)>=r(x), hence equal m. Then both x,y lie in interval of values rounding to m. What is interval? r(t)=m iff m - 1/2 < t < m + 1/2? Tie behavior boundaries: At lower tie t=m-1/2 rounds down to m-1 (not m), so m interval is (m-1/2, m+1/2]? Wait tie down: At t=m+1/2, rounds down to m, so included. At t=m-1/2, rounds down to m-1, excluded. Thus interval length 1 (open-left, closed-right): m-1/2 < t <= m+1/2. The maximum difference between two values in same interval is < or <=? y-x can approach 1 but not exceed? Since x > m-0.5, y <= m+0.5, y-x <1? Actually sup =1 not attained because x strict. Thus y-x<1. Contradiction with >=1. If use interval ( -∞? endpoints? For integer? Good. Thus no duplicates, strictly increasing.

Need consider if x_j nonnegative. yes.

[[verification]]But wait our rounding formula q=(2A+d-1)//2d corresponds tie down. Need verify interval includes upper .5. Example target 2.5 formula q=2. yes interval (1.5,2.5] maps to2. Good. If difference exactly 1 with one at m+0.5? e.g x=1.5 rounds 1, y=2.5 rounds2 diff 1. no dup. For x= m-0.5? excluded. Unique.

[[conclusion]]Need maybe "integer-only Python function" means avoid float, use integer arithmetic. We can present type hints maybe list[int]. Need for 2<=k<=n. Could assert. Might use ValueError. Should be robust.

Need perhaps include "retaining endpoints" automatically but maybe function can assign endpoints directly. Need prove endpoints: j=0 =>0. j=k-1: A=(k-1)(n-1), formula floor( (2d(n-1)+d-1)/(2d)) = n-1 + floor((d-1)/(2d)) for d? Wait floor(n-1 + (d-1)/(2d)) = n-1 since d>=1 and numerator d-1 <2d. Good. For d=0 not allowed. k=2 d=1. endpoints formula: j1 A=n-1; q=(2(n-1)+0)//2 = n-1. Good.

Need possibly "targets at integer indices nearest to j*(n-1)/(k-1), ties toward the smaller index." If tie exact half-integer target at j? Use formula. Good.

[[verification]]Need maybe discuss tie toward smaller index means for .5 choose floor target. Formula uses d-1, not d? Let's verify with d odd/even? q = (2A+d-1)//2d. This gives floor((A + (d-?)/2? Let's derive carefully to avoid off-by-one. We want nearest integer to A/d, ties toward smaller.

Rounding nearest with ties down = floor( (A/d) + 1/2 ) except if fractional exactly .5 subtract. Standard formula: floor((2A + d - 1) / (2d))? Let's derive from inequality. Candidate m = floor((2A + d - 1)/(2d)). Let B=2A. Need find largest integer m such that m <= x+0.5? Actually tie down means m = floor(x+0.5) if x+0.5 not integer? Wait tie down q= floor(x) when x=m+0.5, but floor(x+0.5)=m+1. So q = ceil(x+0.5)-1? Let's use formula floor((2A + d -1)/(2d)). Need verify more tests.

x=0.4 A? d=5 A=2. q=(4+5-1)//10=8//10=0 correct nearest0.
x=0.5 d=2 A=1; q=(2+2-1)//4=3//4=0 correct.
x=0.6 d=5 A=3; q=(6+5-1)//10=10//10=1 correct.
x=1.4 d=5 A=7; q=(14+5-1)//10=18//10=1 correct.
x=1.5 d=2 A=3; q=(6+2-1)//4=7//4=1 correct.
x=1.6 d=5 A=8; q=(16+5-1)//10=20//10=2. correct.

Formula appears.

[[alternative]]Alternative using divmod: q = A // d; rem = A % d; if 2*rem > d or (2*rem == d and? ties down choose q not q+1). So if 2*rem > d: q+=1. That's integer and maybe clearer. Because compare fractional r/d to 1/2. Ties toward smaller means increment only if rem/d > 1/2, i.e. 2*rem>d. This avoids formula confusion. [[development]]Could implement:
def downsample_indices(n,k):
    d=k-1
    out=[]
    for j in range(k):
        a=j*(n-1)
        q,r=divmod(a,d)
        if 2*r > d:
            q += 1
        out.append(q)
    return out
This is integer-only and clear. But note for d, k>=2 so d>=1. Ties exact 2r==d no increment, ties smaller. This perhaps easier prove. [[verification]]Need endpoints: j=k-1 a=(k-1)(n-1); divmod a,d gives q=n-1, r=0. Good. j=0 q=0. Either function.

Use divmod with d, not d? Yes. q=floor target. Rounding: nearest; compare fractional part rem/d; if >1/2 round up, if = tie down. Good.

Need ensure target j*(n-1)/(k-1). q, r = divmod(j*(n-1), k-1). If 2*r > d q +=1. This is simple. Is it integer-only? Yes. It uses only ints. Great.

[[verification]]Need prove no duplicates. Could use target difference:
x_{j+1} - x_j = (n-1)/(k-1) >=1 because n>=k => n-1 >= k-1.
Define r(x) round nearest ties down. Need show x<y and y-x>=1 implies r(x)<r(y). Use interval argument. For any integer m, set of x rounding to m is (m - 1/2, m + 1/2] (with tie down at right; at left tie goes to m-1). Its length is 1 but strictly more than? Actually it's length 1? Interval from -0.5 to 0.5 length 1 open-left closed-right. Any two in same interval have difference <1? Max? y <= m+0.5, x > m-0.5 => y-x < (m+0.5) - (m-0.5)=1. Yes strictly <1. Thus two targets separated by at least 1 cannot round to same integer. Since x_j increasing, rounded indices strictly increasing. No duplicates. Need be precise for q=0 lower interval? For x>=0, set r(x)=0 includes [0,0.5]? Wait formula interval (m-0.5, m+0.5] for all real but for x>=0. For m=0, interval (-0.5,0.5]. If x=0.4 rounds 0, x? x negative not relevant. Difference between two nonnegative in interval <=0.5? okay <1. For m positive.

Potential issue "r(x)" at exact left tie x=m-0.5 rounds to m-1, not m; interval (m-0.5, m+0.5]. Good.

[[alternative]]Alternatively prove using floor formula:
q_j = floor((j*(n-1))/(k-1)+1/2) with tie correction. But interval proof sufficient.

[[verification]]Need check exact half-integer target case. Use n=6,k=3, targets:
j=0:0*(5)/2=0 ->0.
j=1:1*5/2=2.5 -> tie toward smaller 2 (not 3). Function: d=2,a=5,q,r=divmod(5,2)=(2,1); 2*r=2 not >d=2, so q remains2.
j=2:10/2=5 ->5.
Output [0,2,5]. Good. We can include.

Need consider if k=2. d=1. targets: j=0 0; j=1 n-1. divmod(a,1), r=0; no increment. Output endpoints. no duplicates since n>=2; 0 < n-1. Good. If n=2,k=2: [0,1]. Fine.

[[conclusion]]Need answer likely just code and proof/check. Need mention asserts/raises. "Write an integer-only Python function..." Use no floats. 

Need decide final content. Since desired oververbosity 5, moderate. Provide function, tie behavior, proof, example.

Need maybe include docstring. [[development]]Code:
def downsample_indices(n: int, k: int) -> list[int]:
    if not (2 <= k <= n):
        raise ValueError("require 2 <= k <= n")
    d = k - 1
    indices = []
    for j in range(k):
        num = j * (n - 1)
        q, r = divmod(num, d)
        if 2 * r > d:  # strictly greater: ties stay down
            q += 1
        indices.append(q)
    return indices

Need ensure type list[int] requires py3.9, okay. "integer-only" no float. Maybe for broad compatibility use List from typing? But list[int] accepted modern. Could not import. Fine.

[[verification]]Could set endpoints guaranteed; maybe mention no explicit forcing. Maybe if someone complains "retaining endpoints" perhaps code uses formula and endpoint exact. We can also set result[0] and result[-1]? Not needed. Could explicitly:
indices[0]=0; indices[-1]=n-1? But no need, and if code bug? Better not.

Need proof duplicates with formula. Need maybe explain q_j formula equivalent to nearest tie down. For target x = A/d. q=floor(x), r=A mod d. Fractional part r/d. Round up iff fractional > 1/2 i.e. 2r>d. If =1/2, no round up, tie smaller. Good.

[[development]]Proof no duplicates:
Target x_j = j(n-1)/(k-1). For consecutive j, Δ = (n-1)/(k-1) ≥1. Let y_j be rounded index. Rounding function R(x). For any integer m, R(x)=m iff m-1/2 < x ≤ m+1/2 due tie down. This interval's width is 1, but with open left so two numbers in it differ by <1. Therefore two targets distance ≥1 cannot map to same m. Since targets strictly increase, rounded indices strictly increase; no duplicates. Also length k entries all distinct, from 0 to n-1 due endpoints? Distinct and endpoints included. Need maybe prove they fit within 0..n-1:
targets in [0,n-1], rounding to nearest could produce? For x=0, R=0; for x=n-1, R=n-1; interior within. Nonnegative and ≤n-1? Rounding nearest of x∈[0,n-1] can't exceed n-1, can't below0. Good.

[[verification]]Need check exact half. Include code output. Let's calculate output with function:
>>> downsample_indices(6,3)
[0,2,5]
We can mention exact half target 2.5 at j=1. Formula divmod(5,2) = (2,1), 2*1 ==2 so no increment, hence 2. Good.

Need perhaps mention "ties toward smaller index" could mean when target exactly half-integer, choose lower integer index, e.g. 2.5 -> 2. Done.

[[verification]]Let's consider if there is any hidden challenge: "Downsample n ordered samples to k indices" maybe expects target count k? Yes. "retaining endpoints and placing targets at integer indices nearest to j*(n-1)/(k-1)" This is like linspace indices. Need k indices inclusive endpoints. Good.

Potential issue if k=1? They restrict 2<=k, okay.

Could there be duplicates for n=k? Then d=n-1. target = j*(n-1)/(n-1)=j exact, output 0..n-1 all unique. Good.

[[conclusion]]Let's formulate final answer maybe:

```python
def downsample_indices(n: int, k: int) -> list[int]:
    if not (2 <= k <= n):
        raise ValueError("require 2 <= k <= n")
    d = k - 1
    out = []
    for j in range(k):
        numer = j * (n - 1)
        q, r = divmod(numer, d)
        if 2 * r > d:  # strictly greater, so half-integers round down
            q += 1
        out.append(q)
    return out
```

Proof. Check.

Need ensure "integer-only" maybe they don't want use `divmod`? It's integer-only. Fine.

Let's write final with concise but complete.
