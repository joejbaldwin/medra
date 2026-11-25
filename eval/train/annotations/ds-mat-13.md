---
trace: ds-mat-13
annotator: Codex (AI)
status: corrected
concepts: []
topics: []
---
[[planning]]We need answer. Need parse problem. Upright 2 m pole stands 3 m from a point lamp whose height uniformly distributed 3 to 6 m. Find mean length of pole's shadow on level ground and probability it exceeds that mean. Explain why using mean lamp height can give different value.

Need derive geometry. Lamp point? Ground level? Pole vertical height 2 m. Distance from pole to point lamp? The lamp is at horizontal distance 3 m from pole, height H above ground. Shadow length on level ground due to point source. Need derive L as function of H. Need consider lamp on one side of pole. If light source height H, pole height h=2, horizontal distance d=3 from lamp to pole. [[development]]The shadow extends on opposite side of pole from lamp if H > h? Let's check. If source height > pole, ray from lamp through top of pole hits ground beyond pole on side opposite source. If source lower than top, ray through pole top upward? Actually source H=3 to 6 >2, so yes. Shadow length L can be similar triangles.

Set ground x-axis. Lamp at x=0, height H. Pole at x=3, from y=0 to y=2. Ray through lamp (0,H) and pole top (3,2). Intersect ground y=0 at x = ? Parameter line. Slope from lamp to pole = (2-H)/3. Equation y = H + ((2-H)/3) x. Set y=0: 0=H + (2-H)x/3 -> (H-2)x/3 = H -> x=3H/(H-2). This x coordinate from lamp. Pole at x=3. Shadow beyond pole length L = x - 3 = 3H/(H-2)-3 = [3H -3(H-2)]/(H-2)=6/(H-2). [[verification]]Wait that's distance from pole to intersection. Is it positive for H>2. For H=3 L=6; H=6 L=6/4=1.5. That seems plausible: higher lamp shorter shadow. Need verify alternative formula often shadow length = h*d/(H-h) if distance from pole to source = d. Here h=2, d=3, L=hd/(H-h)=6/(H-2). Yes.

[[development]]H uniform on [3,6]. Let L=g(H)=6/(H-2). H in [3,6] => L from at H=6:1.5 to at H=3:6. Need mean E[L] = ∫_3^6 6/(H-2) * 1/3 dH = 2 ∫_3^6 1/(H-2) dH? Check: (1/3)*6=2; integral =2[ln(H-2)]_3^6 =2(ln4 - ln1)=2 ln 4 = 4 ln2 ≈2.7725887. Alternatively transform L distribution.

Probability it exceeds that mean: L > E[L]=2 ln4? Need solve 6/(H-2)>2 ln4? Note L decreases with H. L>m means 6/(H-2)>m => H-2 < 6/m => H < 2+6/m. m=2 ln4=4 ln2 ≈2.77259. 6/m = 6/(2.77259)=2.164042? 2+ =4.16404. Since H uniform [3,6], probability = (4.16404-3)/3? Wait condition H<4.164 and H≥3 so length 1.16404 /3=0.3880. Need exact: P(L>m) = P(H-2 <6/m) = P(H<2+6/m). Since lower H=3. = [(2+6/m)-3]/3 = (6/m -1)/3 = 2/m -1/3. m=4 ln 2? Wait m = E L = 4 ln2. Then 6/m = 6/(4 ln2)=3/(2 ln2). P = (3/(2 ln2) -1)/3 = 1/(2 ln2) -1/3. Numeric ln2=0.693147; 1/(1.386294)=0.7213475; -0.333333=0.388014. [[verification]]Check.

But careful: mean length of shadow perhaps from formula? Need consider if lamp height uniformly distributed but geometry source point at height varies along vertical at fixed distance? "stands 3 m from a point lamp whose height is uniformly distributed from 3 m to 6 m." Point lamp at a point located 3m horizontally, height random. Yes.

[[development]]Need explain why using mean lamp height can give different value. If use mean H = 4.5, shadow L(4.5)=6/(2.5)=2.4 m. This differs from E[L]=2.7726. Because L is nonlinear in H (convex? 6/(H-2) convex for H>2, second derivative positive: 12/(H-2)^3 >0; Jensen E[L] > L(EH). Need mention if asked "using mean lamp height can give different value" possibly expected mean length by substituting mean height = 2.4, while true mean 2.77. Why? Shadow length is nonlinear and distribution matters; expectation of a nonlinear function not function of expectation. [[alternative]]Also probability? They might ask "probability it exceeds that mean", which mean? "that mean" likely mean length computed. Need clarify if using mean lamp height? Let's parse exact wording: "Find the mean length of the pole's shadow on level ground and the probability it exceeds that mean. Explain why using the mean lamp height can give a different value." So compute E[L]; probability L > E[L]; then explain using mean lamp height can give different value [for mean shadow?]. It might also be a trap about "mean lamp height" vs "mean shadow length". Need include calculation using mean height L(4.5)=2.4 and compare.

[[verification]]Could there be issue with direction/geometry when lamp height 3-6, pole height 2, shadow length formula. Let's double-check all coordinate and definitions. Suppose pole at distance 3 from lamp, lamp height H. Top of pole at height 2. The shadow's length on ground from base of pole away from lamp is x? Use similar triangles maybe (H-2)/3 = H/(3+s)? Wait draw: Lamp at height H above point O on ground 3 m from pole base P. Pole is height 2. The ray from lamp through top T intersects ground at S beyond P. Triangles: lamp height H from O to L; pole? Could use distance from line? Let's coordinate: O at x=0, lamp L=(0,H), pole base P=(3,0), top T=(3,2). Ray L-T intersects ground at S=(3+s,0). Similar triangles comparing L-O-S and T-P-S? Vertical distances: H at x=0, 2 at x=3; slope down. The drop from L to T is H-2 over horizontal 3. From T to S drop is 2 over horizontal s. Since same line: (H-2)/3 = 2/s (positive downward per horizontal). Then s = 6/(H-2). Yes.

For H=3, lamp same height 3, pole top 2: slope down from source to top =1/3; continue down 2 more horizontal -> s=6. Yes. H=6, drop 4 over 3 -> slope 4/3, from top drop 2 -> s=1.5. Good.

[[verification]]Mean integral: H uniform density 1/3. E[S]=∫3^6 6/(H-2)*(1/3)dH = 2[ln(H-2)]_3^6 =2(ln4 - ln1)=4 ln2 =2.7726. Note average of endpoint lengths? Since reciprocal nonlinear. Good.

Probability S > mean: S decreasing in H. S>4 ln2? Solve 6/(H-2)>4 ln2 => 6 >4 ln2(H-2) => H-2 < 6/(4 ln2)=3/(2 ln2)=2.16404 => H<4.16404. Probability with H U[3,6] = (4.16404-3)/3 =0.388014. [[verification]]Alternatively distribution S: H=2+6/S, dH/dS=-6/S^2, f_S(s)=? For s in [1.5,6], f=(1/3)*6/s^2? Wait |dH/ds|=6/s^2, so f_S(s)=2/s^2 for s∈[1.5,6]. Check integrates -2/s from 1.5 to 6 =2(2/3-1/6)=2(1/2)=1. E=∫ s*2/s^2 ds=∫ 2/s ds from1.5 to6=2 ln4 =? That would be 2.772? Wait 2 ln(6/1.5)=2 ln4=2.772 yes same as 4 ln2. Good. Probability S>m=∫_m^6 2/s^2 ds = 2(1/m -1/6) =2/m -1/3=0.388. Good.

[[alternative]]Need mention maybe if "probability it exceeds that mean" could be ambiguous: If "it" refers to shadow length, compute above. If "it" refers to lamp height exceeds mean lamp height? But no, probability it exceeds that mean likely shadow length. Need perhaps state.

[[development]]Need explain using mean lamp height: E[shadow at mean height]? If lamp height mean μ_H=4.5, L(μ_H)=6/(4.5-2)=2.4, not E[L]=2.7726. Also P(L>2.4)? If someone uses that as "mean" incorrectly, probability L>2.4: Solve H < 2+6/2.4=2+2.5=4.5, P=(4.5-3)/3=0.5. Interesting! They may ask "probability it exceeds that mean" and "explain why using mean lamp height can give different value." Perhaps there is a known paradox: If use mean lamp height 4.5, calculate shadow=2.4 and probability shadow exceeds 2.4? Since median H=4.5, but L monotone, P(L>2.4)=0.5. But true mean L=2.77, P(L>true mean)=0.388, not 0.5. Need explain. Could mention that using mean height gives shadow length 2.4, which is not expected shadow length; it may also lead to probability 1/2 that shadow exceeds that value, whereas for true mean it's 0.388. [[conclusion]]Need articulate.

Need maybe discuss "point lamp whose height is uniformly distributed..." It might be a probability notation issue: let X lamp height uniform. Shadow length Y=?? Find E[Y], P(Y>E[Y]). The mean shadow is not L(E[X]). Because 1/(X-2) is convex, Jensen gives E[L] > L(E[H]). Since L is nonlinear reciprocal, height fluctuations disproportionately increase shadow when lamp is low. This is a nice explanation. Maybe mention mean height 4.5 yields L=2.4; actual mean 2.77 because low lamps (short H) create very long shadows and dominate average. [[verification]]But wait reciprocal convex? Function in H 1/(H-2) convex, so E > f(E), yes low H near 3 has large values, average larger. Good.

[[conclusion]]Let's craft final answer with equations and probability. Desired oververbosity 5. Need provide clear but not too lengthy. Could include geometry diagram description.

[[verification]]Let's ensure no hidden issue: "upright 2 m pole stands 3 m from a point lamp whose height is uniformly distributed from 3 m to 6 m." Could "3 m from a point lamp" mean distance from pole to lamp along ground? Usually yes. If distance is between pole and lamp? The lamp is a point at height H, horizontal distance? It says point lamp whose height; stands 3 m from a point lamp. The lamp is at a point in 3D? If "3 m from" could be slant distance from base? But height random from 3 to6, lamp position maybe directly above point? Standard problem: pole stands 3 m from a point source of light whose height above ground is random. "from a point lamp" means ground distance probably. We used. If "distance from top of pole to lamp" fixed 3, would complicate. But phrase "stands 3 m from a point lamp" in shadow problems typically horizontal distance to the point below lamp? Let's assess. Lamp is a point in space, not on ground; "stands 3 m from a point lamp whose height..." Could mean the horizontal distance between pole and the vertical line through lamp? Since point lamp's height distributed, its horizontal position fixed at 3m from pole. Yes.

Maybe there is no "point below lamp" explicitly. But "stands 3 m from a point lamp" colloquially means distance on ground? If lamp height varies, actual Euclidean distance from pole to lamp would vary unless horizontal. Since they mention height, standard to fix horizontal separation. [[conclusion]]We can perhaps state "taking the 3 m as the horizontal distance from the pole to the vertical line through the lamp." Good.

Let's derive in final.

Need maybe mention H has density 1/3 on [3,6]. L(H)=hd/(H-h). Let h=2,d=3.

Mean:
E[L]= (1/3)∫_3^6 6/(h-2) dh = 2 [ln(h-2)]_3^6 =4 ln2 ≈2.773.

Probability:
Let m=4 ln2. Since L decreases in h,
P(L>m) = P(6/(H-2)>4 ln2) = P(H<2+3/(2 ln2)) = [2+3/(2 ln2)-3]/3 = 1/(2 ln2)-1/3 ≈0.3880.

[[verification]]Double-check algebra: 6/(4ln2)=3/(2ln2). yes.

[[conclusion]]Using mean height H=4.5:
L(4.5)=6/2.5=2.4 ≠2.773. If treat 2.4 as shadow threshold, P(L>2.4)=P(H<4.5)=0.5. This underscores nonlinearity; expectation doesn't commute with nonlinear transformation. Because L is convex in H, E[L]>L(E[H]). Low lamp heights produce disproportionately long shadows.

[[alternative]]Would it be useful to calculate median? Distribution L CDF; P(L>mean). Fine.

[[conclusion]]Potential issue: "probability it exceeds that mean" If they mean "probability the shadow length exceeds the mean length" as above. If one instead uses "mean lamp height" to compute shadow length, P(L > L(mean H)) = 0.5 because H continuous symmetric and L monotone. But for true mean P =0.388. Include both.

Let's perhaps include a small "If by mistake one sets H=E[H]" paragraph.

Need final answer not too verbose but with explanation.
