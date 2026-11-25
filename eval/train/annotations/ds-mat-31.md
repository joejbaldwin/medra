---
trace: ds-mat-31
annotator: Codex (AI)
status: corrected
concepts: []
topics: []
---
[[planning]]We need answer. Need parse problem. Disc radius 2 centered at uniformly random point of square side 10. "crosses exactly one supporting line of the square." Need probability. Supporting lines of square? Likely the four lines containing sides (extensions?) "crosses a supporting line" means circumference intersects line? Disc crosses side line? Need understand.

A disc centered at random point inside square. "supporting line of the square" maybe lines containing sides? Exactly one supporting line of the square. Need probability disk crosses exactly one supporting line. Radius 2, square side 10. Center inside square. [[development]]A disk crosses a side line if its circumference intersects that line (distance from center to line < r?) Or disk "crosses line" could pass through line (intersect) iff distance from center to line <= r, but if center inside square and line boundary, distance to side line = distance to nearest side if considering four side lines. Exactly one supporting line: only one side line is within distance 2? Let's analyze.

Square side 10, center uniformly in interior. Supporting lines are x=0,x=10,y=0,y=10 (assuming square [0,10]^2). Distance from center (x,y) to each supporting line: x, 10-x, y, 10-y. Disk radius 2 "crosses" a support line if line cuts disk. [[verification]]For crossing (not just tangent) need distance <2. Probability tangent zero. Exactly one of these four distances <2. But center inside. If near corner, two distances <2; near side, one; interior none. [[planning]]Need area where exactly one coordinate within 2 of boundary. Since square side 10 and radius 2<5, lateral forbidden strips? Let's compute.

[[development]]Events:
A_xleft: x<2
A_xright: x>8
A_ybottom: y<2
A_ytop: y>8.

Exactly one event among four. Because radius 2<5, left and right mutually exclusive, bottom/top mutually exclusive, but adjacent can overlap near corners. Count area exactly one strip. Total area 100.

Area with at least one? Use partition zero one two crossings. User asks "Check by partitioning square into regions with zero, one and two crossings." Max 4? For radius 2<5, can only cross up to 2 supporting lines? Wait if near a corner, distance to two adjacent side-lines <2, so crosses two lines. Could a disk near corner also cross? No because 2 < 5, cannot be within 2 of opposite sides simultaneously. So zero, one, two only.

[[development]]We can compute area exactly one strip excluding corner overlaps. Each side strip 10*2=20 area. Sum strips=80. Overlap corners: four 2x2 squares =16 (counted twice). Union=80-16=64. Exactly one = sum strip areas minus 2*? Let's use inclusion. Area exactly one = area in one strip only. For each side strip area 20 minus corner overlaps at two ends (each 4) =12 central-only per side? Wait side strip y in [0,2] all x; overlapping with left strip x<2 area 4, with right x>8 area 4. Thus part with only bottom event = (width 10 - 2-2?) Need careful: y<2; not x<2 nor x>8 => x in [2,8], length6, height2 area12. Four sides each 12 =>48. Exactly two = corner overlap regions but only counts overlap of adjacent strips: four 4 =16. Zero =100 -64 =36. [[conclusion]]Exactly one area 48, probability 48/100 = 12/25 =0.48.

[[alternative]]But wait definition "disc crosses exactly one supporting line of the square": Could "supporting line" mean a line that supports the disk and is a side of square? Hmm wording: A disc of radius 2 is centered at random point of square side 10. Find probability it crosses exactly one supporting line of the square. Check by partitioning the square into regions with zero, one and two crossings.

"supporting line of the square" maybe a line through a side of square (supporting line to square). Disc crosses exactly one such line if it intersects one side line. If center within radius 2 of side, the disk intersects line. But do we require "crosses" line (not contains) means interior of disc intersects line, indeed distance <2. Since center inside, for side line distance positive unless on boundary zero probability. Good.

[[alternative]]However possible alternative: disc "crosses a supporting line" means the circumference intersects the line at two points? Same criterion center distance < radius to line, except if line is outside square and center inside, distance to side line <=? yes.

[[conclusion]]Need answer likely 12/25. Need explain partition areas: zero crossings area 36, one crossings area 48, two crossings area 16. Check includes maybe exact? Let probability exactly one = 48/100.

Let's craft final with square coordinates. Mention supporting lines x=0,x=10,y=0,y=10. Since radius 2<5, at most two side-lines can be crossed. [[verification]]Regions:
- zero: central square with margins 2 from each side: side length 10-4=6, area 36.
- one: strips along sides excluding 2x2 corners, each area (10-4)*2=12, four area 48. Wait central region is x in [2,8], y in [2,8] area 36 yes.
- two: four corner squares 2x2, area 4 each total 16. These correspond centers within 2 of both sides meeting at corner, crossing two supporting lines.
Total area 36+48+16=100.
[[conclusion]]Probability exactly one = 48/100=12/25.

Need perhaps note boundary tangencies have prob zero ignored. "Check by partitioning" satisfy. final concise.
