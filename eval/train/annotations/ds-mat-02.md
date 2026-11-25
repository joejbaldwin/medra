---
trace: ds-mat-02
annotator: Codex (AI)
status: corrected
concepts: []
topics: []
---
[[planning]]We need answer. Need parse geometry. Need be careful. Courtyard rectangle 14 m by 9 m. Long sides? Dimensions likely length 14 (east-west?) by width 9 (north-south). Two gates are on opposite long sides, respectively 3 m and 10 m from the west wall. Need walker starts at one gate, ends at other? Must touch west wall once between gates? "between gates" maybe touch west wall once while going from one gate to another? But gates on opposite long sides. Need find shortest route and contact point. Verify point lies on wall segment.

We need interpret. Rectangle 14 m by 9 m. Long sides are top and bottom length 14, west/east walls are vertical width 9. Two gates on opposite long sides (one on north, one on south) distances 3 m and 10 m from west wall. Need route from one gate to other touching west wall once. "between gates" could mean walker must touch west wall once (i.e. route goes from gate to west wall to other gate). Find shortest route and contact point. Verify point lies on wall segment. [[development]]This is reflection problem.

Set coordinates: west wall x=0, east x=14, south y=0, north y=9. Gates on opposite long sides: top y=9 at x=3? bottom y=0 at x=10? [[alternative]]"respectively 3 m and 10 m from the west wall" ambiguous which side. Usually two gates on opposite long sides, at distances 3 and 10 from west wall. Could be north side gate 3, south side gate 10. Need likely. There may be interpretation "between gates" means contact point on west wall segment between the projections? Actually gates are on opposite long sides with x positions 3 and 10. The west wall vertical x=0 from y=0 to9; "touch west wall once between gates" maybe "once, between the gates" spatially? Wait west wall is not between gate positions if gates on top/bottom? The west wall is side, touching it is between gates along boundary? [[planning]]Let's parse original: "A rectangular courtyard is 14 m by 9 m. Two gates are on opposite long sides, respectively 3 m and 10 m from the west wall. A walker must touch the west wall once between gates. Find the shortest route and its contact point. Verify the point lies on the wall segment." This sounds classic shortest path with obstacle/reflection, perhaps gates on opposite long sides, must touch one of the side walls? Wait "between gates" maybe "A walker must touch the west wall once between [visiting?] gates" from one gate to other. Need contact point.

[[development]]If gates are on opposite long sides at x=3 and x=10. To go from one gate to other touching west wall x=0. Reflect one gate across west wall and connect. Contact y coordinate determined by straight line. Need check y in [0,9]. Let's compute for assumptions.

Case A: Gate A on north y=9 x=3; Gate B on south y=0 x=10. Reflect B across x=0 to B'=(-10,0). Line A(3,9) to B'(-10,0). Intersection x=0: parameter t from A to B': x=3 + t(-13)=0 => t=3/13. y=9 + (3/13)(0-9)=9 - 27/13 = (117-27)/13=90/13 ≈6.923. This lies [0,9]. Distance = sqrt(13^2+9^2)=sqrt(169+81)=sqrt250=5√10≈15.811. Route length via wall: A to P + P to B. Reflection distance same. Contact P=(0,90/13). This is near top, y within.

[[alternative]]If swap gates: A north x=10, B south x=3. Reflect B'(-3,0); line from A(10,9) to B'(-3,0): x=10 -13t=0 t=10/13; y=9 -90/13=(117-90)/13=27/13≈2.077. Distance sqrt(13^2+9^2)=same. Contact y=27/13. Both possible depending assignment. [[verification]]Which is correct? Need identify "respectively 3 m and 10 m from west wall": if mention gates on opposite long sides respectively 3 and 10. Maybe one gate 3 from west, other 10 from west. Without labels, there are two possible contact points (symmetric vertical reflection? Actually not symmetric due distances; swapping x and starting gate maybe contact complementary). Need answer maybe depends on which gate start; shortest from gate 3m to gate 10m touching west wall is P y=90/13 if gate at x=3 on north and x=10 on south? If gate distances independent of side? Let's reason.

Coordinates could set gates: top (north) at 3 m from west; bottom (south) at 10 m from west. Then P=(0,90/13). If reverse sides (top at 10, bottom at3) P=(0,27/13). The route length same. If start at either gate, path may be reverse? Wait start and end gates fixed but "route" from one to other can be traversed either direction. The contact point is same for geometric shortest path independent of direction. If top gate at x=3, bottom at x=10, P y=90/13. If top x=10, bottom x=3, P y=27/13. So side assignment matters.

[[alternative]]Could there be "west wall once between gates" meaning the west wall must be touched at a point whose y coordinate is between the two gates? Since gates on opposite long sides, "between gates" might mean contact point along west wall between their perpendiculars? But west wall vertical, gates are at x=3 and 10, so no. Actually if gates are on opposite long sides (north and south), their y coordinates are 9 and 0; "touch west wall once between gates" might mean the walker starts at one gate and ends at the other, with west wall touch in between (temporally). The phrase "between gates" likely means wall touch occurs on path between gates, not spatial.

Need provide shortest route and contact point, verify lies on segment. Need maybe mention if the 3m gate is on north and 10m gate on south. [[conclusion]]Let's craft solution with coordinate setup and note if labels reversed use mirror.

Need also consider if the "west wall" is vertical of length 9 or maybe rectangle 14 by 9 and "west wall" is a short side? Typically rectangular courtyard 14 m by 9 m: long sides are length 14. Gates are on opposite long sides, respectively 3 m and 10 m from the west wall. The west wall is a short side of length 9. If length (east-west) is 14, width (north-south) is 9. Yes.

[[development]]Need compute route length maybe includes segments? "shortest route and its contact point." Need give total distance and maybe distances from P to gates. Let's compute.

Coordinates: west wall x=0, east x=14, south side y=0, north y=9. Suppose north gate G1=(3,9), south gate G2=(10,0). Contact P=(0, 90/13) = (0, 6.923). Verify y in [0,9].

Route length: Reflection of G2 across west wall: G2'=(-10,0). Distance G1G2' = sqrt((3+10)^2 + (9-0)^2)=sqrt(13^2+9^2)=sqrt250=5√10≈15.811 m. The actual path length G1P + PG2 same. Compute individual distances maybe:
G1=(3,9), P=(0,90/13). dx=3, dy=9-90/13 = (117-90)/13=27/13. Length G1P = sqrt(9 + (27/13)^2) = sqrt((1521+729)/169?) Wait 9 = 1521/169, plus 729/169 =2250/169, sqrt=√2250/13=15√10? √2250=15√10? 2250=225*10, yes =15√10/13 ≈3.65. G2=(10,0), P=(0,90/13). dx=10, dy= -90/13. length = sqrt(100 + 8100/169)= sqrt((16900+8100)/169)=sqrt25000/13 =50√10/13? sqrt25000=50√10? 2500*10 yes. Sum =65√10/13 =5√10. Good.

[[alternative]]If top gate at 10 and bottom at 3: P=(0,27/13). Distances maybe gate top (10,9) to P etc. Total same.

[[verification]]Need maybe derive using reflection: shortest broken path touching line x=0 equals straight line after reflecting endpoint across wall. Contact is intersection.

Need address "Verify the point lies on the wall segment." y=90/13 ~6.92, between 0 and 9, so within west wall segment. If orientation reversed, y=27/13 ~2.08 also within.

Could there be issue route must not leave courtyard? The straight line after reflection may pass outside? Actual path lies inside rectangle? Segment G1-P from (3,9) to (0,6.923): x from3 to0, y decreasing within rectangle yes. Segment P-G2 from (0,6.923) to (10,0): for x between 0 and10 y between 6.923 and0, within. Good.

Need maybe mention "two equal shortest routes?" If start/end order? Route reverse same. If gates positions swapped? Need not.

[[verification]]Let's read exact wording: "A rectangular courtyard is 14 m by 9 m. Two gates are on opposite long sides, respectively 3 m and 10 m from the west wall. A walker must touch the west wall once between gates. Find the shortest route and its contact point. Verify the point lies on the wall segment."

Maybe "touch the west wall once between gates" could mean "touch the west wall once, [while walking] between gates." They say "respectively 3 m and 10 m from the west wall." In a standard "A rectangular field is 14m by 9m. Two gates at opposite corners? Actually gates on opposite sides 3 and 10 from west wall. A man has to go from one gate to other touching one side of the field." This may be a known problem. There may be a wall segment issue: The shortest path via reflection may give a point outside if difference exceeds? Need verify. Here P on segment.

Let's consider if gates are on "opposite long sides" meaning top/bottom, distances along top/bottom from west wall. The west wall is one short side. Good.

[[conclusion]]Need write final concise with coordinate, equations. Since desired oververbosity 5, enough explanation.

[[verification]]Need maybe include formula for contact point in general: If G1=(a,9), G2=(b,0), reflection G2' =(-b,0). Line from G1 to G2'. x coordinate parameter t=a/(a+b) to x=0? Wait line G1(a,9) to G2'(-b,0): x=a + t(-b-a). Set 0 => t=a/(a+b). y=9 + t(0-9)=9(1-t)=9b/(a+b). For a=3,b=10 gives 9*10/(13)=90/13. If labels reversed, 9*3/(13)=27/13. Good.

Check length general: sqrt((a+b)^2+9^2). Here sqrt(13^2+9^2)=5√10.

[[conclusion]]Let's prepare final: state assumption: gate on north side is 3m from west, gate on south side is 10m. If opposite assignment, replace contact y by 27/13.

Need maybe "The contact point is on the west wall at 90/13 m north of the south wall, or 27/13 m south of the north wall (since 9 - 90/13 = (117-90)/13=27/13)." This is useful.

Let's craft.

Potential nuance: If gate at x=3 on one long side and x=10 on other long side, there are two possible choices for which side is north/south. But since gates are on opposite long sides and assignment maybe can be chosen; route length same, contact point either y=90/13 or y=27/13. Need mention.

Let's final with diagram-free coordinate.
