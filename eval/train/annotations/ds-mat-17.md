---
trace: ds-mat-17
annotator: Codex (AI)
status: corrected
concepts: []
topics: []
---
[[planning]]We need answer. Need parse. Need count integer points strictly inside triangle vertices (0,0),(12,0),(4,8). Count once by horizontal slices and once area+boundary (Pick). Explain handling slices through vertex. Need careful: integer points strictly inside triangle. We need count. Let's compute.

Triangle T. Coordinates. [[development]]Edges:
A(0,0), B(12,0), C(4,8).

Boundary lattice points:
AB horizontal y=0 from x=0..12: 13 points.
AC from (0,0) to (4,8): gcd(4,8)=4, primitive (1,2), lattice boundary segments count gcd+1=5; interior points (1,2),(2,4),(3,6).
BC from (12,0) to (4,8): diff (-8,8), gcd=8. 9 points? gcd+1=9. interior 7? Need.
Boundary total B = gcd(12,0)+gcd(4,8)+gcd(8,8)? For polygon boundary lattice count sum gcd over edges =12 +4+8=24. [[verification]]Number boundary lattice points on closed polygon = sum gcd =24? Wait sum gcd counts? For polygon, B = sum over edges gcd(|dx|,|dy|). Here 12+4+8=24. Includes vertices once due formula. yes B=24.

[[development]]Area: base 12 height 8 /2 =48. Pick: A = I + B/2 -1. Strictly interior lattice I = A - B/2 +1 =48 -12+1=37. [[conclusion]]So interior count 37. [[verification]]Need verify with horizontal slices.

Horizontal slices: y integer? Strictly inside. Vertices y range 0 to8. For y=1,...,7 maybe y=0 and y=8 boundary? At y=8 only vertex C boundary. y=0 base boundary. Strictly inside requires 0< y <8. For each integer y=1..7, x interval between left and right boundary edges. Need left edge AC: from (0,0) to (4,8): x = y/2 (since slope 2? line x = y/2). Right edge BC from (12,0) to (4,8): slope (8)/(4-12)=8/-8=-1, equation y=-x+12? Check through B: 0=-12+12 yes, C:8=-4+12 yes, x=12-y. For horizontal y, inside x between x_left = y/2 and x_right=12-y, with y>0 and below? Need orientation: base 0 to12, apex x=4. At y=4, left x=2, right x=8. yes.

Strictly inside: y/2 < x < 12-y. x integer.

For each y=1..7 count integers x satisfying. [[development]]Need be careful if slice passes through vertex? Here y? y=0 through base vertices, y=8 through top vertex. y integer slices at y=1..7 do not pass vertices (except maybe? vertices y 0 or8). But question says explain how handle slices through a vertex. Need discuss if y=0 or y=8 included, strict boundary excluded; endpoints on edges excluded. If slice passes through vertex, interval may be a point or degenerate; do not count boundary; for vertices y=0, y=8 count zero on those slices for strict interior. For y=0 interval [0,12] but y=0 boundary entirely, none strict. For y=8 x=4 point boundary none.

[[verification]]Count for y=1..7:
y=1: 0.5 < x < 11 => integer x=1..10? x > .5 means min 1, x<11 max 10 =>10.
y=2: 1 < x <10 => x=2..9? Strict x>1, x<10 => 2..9 count8.
y=3: 1.5<x<9 => x=2..8 count7.
y=4: 2<x<8 => x=3..7 count5.
y=5:2.5<x<7 => x=3..6 count4.
y=6:3<x<6 => x=4,5 count2.
y=7:3.5<x<5 => x=4 count1.
Sum 10+8+7+5+4+2+1=37. Yes.

[[verification]]Wait check y=1: x_right=11, strict x<11, max 10 count10. left=0.5 min1. okay.
y=2: right10, strict <10 max9; left=1 strict >1 min2 count 8 (2-9). yes.
y=3: right9 strict<9 max8; left1.5 min2 count7. yes.
y=4: right8 strict<8 max7; left2 strict>2 min3 count5.
y=5: right7 max6; left2.5 min3 count4.
y=6: right6 max5; left3 min4 count2.
y=7: right5 max4; left3.5 min4 count1.

[[development]]Need answer explain how handle slices through a vertex. Need perhaps mention if using formula: For each integer y, determine open interval (L(y), R(y)) from intersecting triangle with line y. Count integers satisfying L(y)<x<R(y). If slice passes through a vertex at endpoint, the equality is on boundary and excluded for strict interior. If line touches only at a vertex, interval length zero or includes no strict points (e.g., y=8 point (4,8)). If a whole horizontal edge lies on slice (y=0), all its points are boundary, so no strict interior points. [[alternative]]Potential issue if slice through vertex that is not apex? But our triangle has vertex at y=8; base at y=0 through two vertices. Explain generally: If slice y=v passes through a vertex, include the vertex only if it were not boundary? But strict inside excludes every lattice point lying on triangle boundary. At that y, the horizontal cross-section may be a segment whose endpoints are boundary; use strict inequalities at x endpoints. If cross-section degenerates to a single point (line y through apex), strict interior cross-section is empty, even though the vertex is lattice. If slice through an endpoint of a horizontal edge, cross-section is the edge segment, all are boundary; no strict interior. If slice passes through a non-horizontal vertex with two edges, cross-section extends to one side and the vertex is one endpoint; exclude x equal to that endpoint. Need articulate.

[[verification]]Need also possibly use area and boundary lattice points. We already computed via Pick. Need demonstrate B maybe via gcd. For a lattice polygon, B = sum gcd(|Δx|,|Δy|). Edges:
AB: gcd(12,0)=12
AC: gcd(4,8)=4
CB: gcd(8,8)=8
B=24.
Area = determinant? Coordinates: 1/2 |12*8 -0| =48. Or base-height. Pick I = A - B/2 +1 = 48-12+1=37. Note Pick's I counts strictly interior lattice points. Good.

[[planning]]Need maybe mention "boundary lattice points" are B=24. Some might confuse B computed sum gcd. Need maybe list boundary? Not necessary, but can.

[[verification]]Potential concern: Horizontal slices included points on vertical? Strictly inside at integer y. Need count with endpoints excluded. We can show table.

[[conclusion]]Let's craft final at moderate detail. The user requests "Count integer points strictly inside ... Obtain count once by horizontal slices and once using its area and boundary lattice points. Explain how to handle slices through a vertex." We'll answer fully.

Let's include equations for edges:
AC: y=2x => x=y/2 (or y=2x). [[verification]]Wait line through (0,0),(4,8) y=2x. So x=y/2.
BC: through (12,0),(4,8): y=-x+12? Check slope -1, equation y=-x+12, so x=12-y.
For a fixed integer y with 0<y<8, inside cross-section: y/2 < x < 12-y. Note lower bound left edge, upper right. For y=0 or y=8 no strict interior due boundary.

[[conclusion]]Table:
y | allowable integer x | count
1 1≤x≤10 ->10
2 2≤x≤9 ->8
3 2≤x≤8 ->7
4 3≤x≤7 ->5
5 3≤x≤6 ->4
6 4≤x≤5 ->2
7 4≤x≤4 ->1
Sum 37.

[[verification]]Check table for y=3: x integer satisfying 1.5<x<9 => 2..8 count7 yes. y=2 1<x<10 ->2..9. y=1 0.5<x<11 ->1..10. Good.

[[conclusion]]Need discuss "handle slices through vertex" maybe use endpoints:
At y=0: cross-section of closed triangle is [0,12], but the entire slice is boundary (base), and strict inside wants y>0, so count none.
At y=8: cross-section collapses to x=4, vertex boundary, count none.
If a slice goes through a non-horizontal vertex not at global y max/min, e.g. y=v, then use open interval determined by incident edges; exclude x at the vertex and use strict inequalities. The general rule: for strictly inside, take open intersection of horizontal line with triangle; lattice points on endpoints/edges are excluded. A degenerate open interval has no integer points. Good.

Need maybe note every integer point inside has integer y, so slicing at integer y is sufficient. For y not integer no lattice points.

Could also mention Pick's theorem valid because vertices are lattice points.

Let's craft final.

Need answer with requested "once by horizontal slices and once using its area and boundary lattice points". Make explicit.

Let's ensure no hidden issue: The area and boundary method uses Pick. Count I. B=24. Area=48. I=48-24/2+1 =37. yes.

Let's formulate concise but sufficient explanation.
