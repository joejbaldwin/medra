---
trace: ds-mat-07
annotator: Codex (AI)
status: corrected
concepts: []
topics: []
---
[[planning]]We need solve. Need be careful interpret: 15 equally spaced marks on circle, choose 3 different marks uniformly (C(15,3)). Triangle formed by these points on circle. Probability triangle has a right or obtuse angle. For points on circle, angle subtended by side? Need count triples whose inscribed triangle has right or obtuse angle. Equivalent triangle not acute. For triangle inscribed in circle, angle obtuse/right iff corresponding arc opposite? Need count.

We have regular 15-gon vertices. Choose 3 vertices. Need probability triangle has at least one angle >=90. Since sum angles 180, at most one non-acute (unless right? At most one >=90; right possible, obtuse possible). Need count triples containing three points such that one angle right/obtuse.

[[development]]For triangle with vertices on circle. An angle at a chosen vertex A is half the measure of the arc between the other two vertices not containing A. Angle >=90 iff that opposite arc >=180 degrees. Since 15 marks, arcs in units of central angle 24° (360/15). Angle at A >=90 iff intercepted arc BC not containing A has at least 180°, i.e. at least 7.5 steps => integer arcs >=8 steps? But circle has 15 points, arc between B,C along one direction (not containing A) can be length k steps (number of edges along minor? Need "not containing A"). The measure of arc BC not containing A is central angle corresponding to number of steps along that arc. It can be k = 1..14. Half = k*12°. >=90 iff k>=7.5 => k>=8. Since total 15, if one arc length k>=8, the other is 15-k<=7. A is on complement of that arc (not containing A), meaning A lies on the other arc of length 15-k? Let's formalize.

Pick ordered? For any angle at vertex A, let B,C be other two. There are two arcs between B and C. The one not containing A. Its length in steps m. angle A = m*24°/2 = 12m°. Right/obtuse iff m>=8 (since m integer; m= ? [[verification]]90 requires 7.5 impossible? Actually right angle inscribed intercepts diameter. With odd 15 no antipodal points, no right angles. So m>=8 actually gives >90? 8*12=96 obtuse. There are no right triangles because no diametrically opposite marks. Good. Condition angle obtuse iff intercepted arc >=8 (strict? right none).

[[planning]]Need count triples with at least one obtuse angle. Could count by apex A: number of pairs B,C such that arc BC not containing A has length >=8. Since any obtuse triangle has unique obtuse angle, can sum over A counts (ordered apex unique) without overcount. For each A, choose two other vertices B,C such that one of arcs between B,C not containing A length >=8. But for fixed A, and unordered B,C, exactly one of the two arcs not containing A? [[development]]Wait remove A, the other 14 points form a path around circle from A's neighbors. For any B,C, the circle minus A is connected arc (path) containing both B,C and length 14 edges from one neighbor to other. The arc between B,C not containing A is the one within this path. It has length equal to clockwise distance between B,C along the path, but there are two? Actually if remove A, the remaining points form a linear sequence of 14 vertices between the two neighbors of A. The arc between B,C not containing A is exactly the segment of this path between them; unique, length difference in their positions along this sequence. Condition length >=8.

So for fixed A, label remaining vertices in order along the 14-vertex path: positions 1..14 along circle after A? Need coordinates modulo 15. Let A=0. Other vertices 1,...,14 around clockwise. For chosen B=i, C=j with 1<=i<j<=14. The arc between B,C not containing A is from i to j along this interval (the path not through A), length j-i steps. Angle at A intercepts arc from B to C that does not contain A. If B,C in this path interval, the arc not containing A is indeed clockwise from i to j (or reverse) length j-i, provided i<j. Because the other arc from j through A to i contains A. So angle A >=90 iff j-i >=8. (No right; if j-i =? central arc = (j-i)*24. Half=12(j-i). >=90 iff j-i>=7.5 ->>=8.)
Count pairs 1<=i<j<=14 with j-i>=8. Let d=j-i. For d=8..13? max 13. Number pairs with diff d in range 1..14 length is 14-d. Sum d=8..13 (14-d) = for d=8:6,9:5,10:4,11:3,12:2,13:1 total21. For each A 21 possibilities. A has 15 choices. Since unique obtuse angle in any obtuse triangle, total obtuse triangles =15*21=315. Total C(15,3)=455. [[verification]]Probability 315/455 = simplify divide 35? 315/455 = 9/13? 455*9/13=35*9? 455/13=35, *9=315 yes 9/13.

[[verification]]Need justify boundary condition "right or obtuse", count right vs obtuse. Right impossible due no antipodal marks on odd 15. Obtuse counted by arc length >=? Wait condition angle right or obtuse means m >= 7.5 steps. But if arc length exactly 7.5 not integer; no equality. Need maybe angle = 90 when opposite arc 180°, requiring B,C separated by 7.5 marks, impossible. So right none. Obtuse m>=8. But careful: In a triangle on circle with odd n, can an angle be exactly 90? Inscribed angle theorem right iff diameter endpoints B,C, no diametric pair. correct.

Need also consider count of triangles with right or obtuse: any triangle with an obtuse angle. Since sum, unique. Count for each vertex as possible obtuse apex. For each A, count pairs with arc not containing A length >=8. Wait if j-i>=8, angle at A = half arc BC not containing A. But arc measure is (j-i)*? Need check degrees: 15 equally spaced, adjacent central angle 24°. Arc length from i to j along path excluding A = (j-i)*24°. Inscribed angle intercepts the arc BC not containing A, measure half central. So angle at A = (j-i)*12°. If j-i=8 => 96°, obtuse. j-i=7 =>84° acute. Yes.

[[verification]]But I must be extra careful: For fixed A coordinates 0, vertices i and j among 1..14. The arc between B=i and C=j not containing A: If i<j, the shorter? It is clockwise from i to j not passing through A, length j-i. But there is also counterclockwise from i to j via A? The one not containing A is yes j-i. However arc measure can be >180? j-i can be up to14. Inscribed angle theorem says angle = half measure of arc BC that does not contain A. This arc could be major >180, angle >90. For j-i=13, angle =156? Actually 13*24/2=156°, possible if A on minor arc of 2 steps? Wait triangle interior angle at A can be 156, sum. Yes.

[[backtrack]]Count sum d 8..13 gave 105 per? Let's recompute sum: d=8..13: (14-d): 6+5+4+3+2+1=21. For all A 315. Total 455. Probability ~0.6923. [[verification]]Is that plausible? For random 3 vertices on 15-gon, acute probability 4/13 ~0.3077. For continuous random points on circle, probability triangle acute =1/4, obtuse/right=3/4. For n=15 discrete maybe around .308, plausible.

But wait random three vertices on regular odd polygon: Is count of acute triangles maybe? There is known formula: For n odd, number of acute triangles = n * C((n-1)/2,2)? Let's check. Total 455. Our obtuse 315. Acute 140. Probability acute 140/455 = 4/13 ≈.3077. [[alternative]]Known count for n=15 acute = 15*C(7,2)=15*21=315? Wait conflict. Let's analyze known formula. For an angle at A to be acute, the opposite arc not containing A < 180 => steps <=7. For fixed A, pairs B,C with j-i <=7? Count maybe 42? Acute triangle requires all angles acute. Counting by apex condition maybe not simple.

[[verification]]Let's verify count obtuse by alternative. For any obtuse triangle, unique obtuse angle at a vertex. For fixed A, angle at A obtuse iff B and C lie such that the arc BC not containing A > 180°, i.e. B and C are separated by at least half. For n=15, if A fixed, how many unordered pairs (B,C) among remaining 14 yield A obtuse? We computed 21. That seems low. But 21 * 15 =315. If more than half triangles obtuse, 315. Total 455, acute+right =140. For fixed A, obtuse probability conditional A included? But each triangle has 3 vertices, sum over apices count each triangle 3 times for all possible angle obtuse? We counted only cases where A is obtuse, so sum = # obtuse triangles (unique), not divided by 3. Correct. So 315 obtuse. Then non-obtuse (acute/right) =140. Need ensure each triangle has at most one obtuse, yes.

[[verification]]Let's test with n=5: total C5,3=10. Formula obtuse count n * sum_{d=ceil(5/2)}^{?}? For n=5, fixed A remaining positions 1..4; angle obtuse iff diff? central step 72°, angle A = (diff)*36°? Need >90 iff diff >2.5 ->>=3. Pairs with diff>=3: (1,4) diff3, (2? max 4) count? d=3:1, d? j-i=3 only (1,4):1. per A 1 =>5 obtuse. But C5,3=10. There are also 5 acute? For regular pentagon, choose any 3 vertices: Are all triangles isosceles with angles? There are two types? Actually any 3 distinct vertices of pentagon form a triangle. Since no diameter, none right. Number acute? A triangle from pentagon: choose three consecutive vertices arcs gaps e.g. 1,1,3: interior angles half opposite arcs: arcs between selected points lengths 1,1,3. Angles? 1*36? Let's compute one triangle with vertices 0,1,2. angle at 1 intercepts arc 0-2 not containing1 length 3 steps? central 216, half108 obtuse. So only triangle using three consecutive has obtuse. Number such? 5. What about vertices 0,1,3: gaps 1,2,2; angles half arcs: at 0 intercept arc 1-3 not containing0 length2 =>72; at1 intercept arc0-3 not containing1 length? arc 3-0 length2? central144 half72; at3 intercept arc0-1 length1 central72 half36. Acute. There are 5? total 10, remaining 5 acute. Our count obtuse 5, yes. Good.

[[conclusion]]For n=15, per A count 21. n*21=315. Seems plausible.

[[planning]]But the problem wording: "choose three different marks uniformly. What is the probability that they form a triangle with a right or an obtuse angle? Justify how you count triangles on the boundary of the condition." The "boundary of the condition" likely refers to right angle boundary (>=90); because no right due odd; must justify count of equality? Also obtuse condition uses strict > 90; on boundary right triangles maybe none. Need explicitly mention right angle occurs when one side is a diameter, requiring opposite marks, impossible with 15 (odd); so right-angle count zero. For obtuse, the arc opposite the obtuse angle must exceed a semicircle, i.e., contain at least 8 of the 15 equal arcs. Need perhaps careful: central arc >180°, with 15 marks, minimal length 8 intervals =192°, yes. Count.

[[conclusion]]Let's formulate with total and favorable. Could count favorable directly with complement? Need possibly explain boundary.

Detailed counting:
Total triples = C(15,3)=455.

No right triangles: any right angle in an inscribed triangle intercepts a diameter. A diameter connects two marks opposite each other; with 15 odd, no pair of opposite marks. Thus right angle impossible.

To count obtuse triangles: For any obtuse triangle, obtuse angle is unique. Sum over choice of obtuse-angle vertex A. Fix A. Going clockwise from A, label remaining marks 1,2,...,14. If the other two chosen marks are at positions i<j, then the angle at A intercepts the arc from i to j not containing A, with measure (j-i) steps of 24°. It is obtuse iff (j-i)*24°/2 > 90° ⇔ j-i > 7.5 ⇔ j-i≥8. (The boundary j-i=7.5 would be right but impossible because integer; if considered as > 180 for intercepted arc, equality also impossible.)

For a given separation d=j-i, number of pairs among positions 1..14 is 14-d. Sum d=8 to 13 (since max difference 13 among 1..14) of (14-d) = 6+5+4+3+2+1=21. There are 15 choices for A. Since no triangle has more than one obtuse angle, no overcount: favorable =15*21=315.

Probability =315/455=9/13.

[[alternative]]Alternative count: For fixed A, the two other vertices must lie within an arc? Wait our count sums d 8..13. Let's re-express maybe easier: The arc between B,C not containing A > semicircle. With A fixed, how many pairs have difference >=8 in the remaining linear order. Yes.

[[verification]]Check "boundary of condition" maybe they expect count right triangles on boundary: In continuous, boundary is right triangles. Since 15 odd, none. If n even, right triangles count etc. Need mention j-i=7.5 cannot happen; j-i=7 gives 84° and j-i=8 gives96°, so no equality. Also no diametric pairs.

Could there be a triangle with an angle exactly 90 not requiring selected B,C antipodal? In a circle, yes side BC is diameter, so B and C opposite marks. Since 15 odd impossible. Good.

[[alternative]]Potential issue: The phrase "On a circular dial with 15 equally spaced marks, choose three different marks uniformly." Could mean choose 3 marks with replacement? No, three different marks uniformly means sample without replacement among marks. Yes.

[[verification]]Let's maybe include a diagramless check for overcounting: Any obtuse triangle has exactly one obtuse angle; if we select A as the obtuse vertex, B,C are fixed. Distinct A produce disjoint sets. Good.

Let's perhaps mention triangles with right or obtuse: favorable = right + obtuse =0+315. Total.

Let's also consider if "triangle with a right or an obtuse angle" includes degenerate? Three marks distinct non-collinear? On circle no three collinear except? A line intersects circle at <=2, so nondegenerate.

[[conclusion]]Let's prepare final answer with moderate detail. Use "steps" and central angle 360/15=24°.

[[verification]]Maybe derive count another way to justify boundary:
For fixed A, there are C(14,2)=91 pairs. Count obtuse at A. Condition j-i ≥8. Count:
d=8: pairs (1,9)...(6,14) =6
d=9:5
d=10:4
d=11:3
d=12:2
d=13:1
sum21.
Wait d could be more? j-i max 13 because i=1,j=14. Yes. What about d=14? No j-i=14 impossible with i>=1,j<=14. okay.
Maybe d from 8 to 14? d=14 count0. Sum same.

[[verification]]Let's verify per A count via complement perhaps if A acute/right? For A fixed, total pairs 91. Obtuse at A 21. Does that mean probability angle at A obtuse ~0.231. For a triangle with fixed one vertex, plausible. Then expected # obtuse angles per triangle =3*21/91? Wait if choose A fixed and B,C random among all C(14,2), probability A angle obtuse =21/91. In a random triangle, expected number obtuse angles =3*21/91=63/91=0.6923, matches probability of obtuse triangle because at most one. Nice.

[[conclusion]]Need maybe note total choices for A? Sum over all A and pairs B,C counts each obtuse triangle once (not 3) because only obtuse vertex A counted. If summing over all A, for an acute triangle A angle not counted; for an obtuse triangle the obtuse vertex A counted exactly once; for right (none) counted once if right? Right angle unique too. Good.

Let's final.
