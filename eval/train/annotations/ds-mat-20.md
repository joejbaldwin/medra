---
trace: ds-mat-20
annotator: Codex (AI)
status: corrected
concepts: []
topics: []
---
[[planning]]We need answer. Need solve classic Bertrand? Question: "An artist draws 'a random chord' of a unit circle. Compute the chance its length exceeds the radius for two procedures: join two independent uniform boundary points, or choose a uniform midpoint in the disc and draw the chord bisected there. Explain the role of the centre."

Need compute probability chord length > radius (unit circle). For two procedures:
1 endpoints independent uniform boundary points. [[development]]Chord length L=2 sin(theta/2) where theta smaller central angle? Radius=1. We need L>1 => 2 sin(theta/2)>1 => sin(theta/2)>1/2 => theta/2>pi/6 (assuming theta in [0,pi]) => theta>pi/3. Distribution of theta angle between two random points: choose first at 0, second uniform on circumference, central minor angle uniformly? The angle difference U uniform [0,2pi); minor angle Θ in [0,pi] has uniform distribution? Yes density 1/pi? [[verification]]Let's check: if difference uniform 0-2pi, minor angle distribution uniform on [0,pi] because two symmetric intervals. P(Θ>π/3)= (π-π/3)/π=2/3. Alternatively probability endpoints separated by >60 deg =? Starting point fixed, favorable arc length 4π/3? Wait condition minor angle > 60. For second point, unfavorable within ±π/3 arc total 2π/3, favorable 4π/3, prob 2/3. Correct.

[[alternative]]2 choose uniform midpoint in disc and draw chord bisected there. Need clarify chord whose midpoint is point M in disk, chord perpendicular to radius at M? For a point inside circle, unique chord with midpoint M along radial line? [[development]]Let's derive. Unit circle center O. Point M uniformly in disk with distance r from center. The chord through point M with midpoint M has distance from center r, and length = 2 sqrt(1 - r^2). Wait if midpoint is M, line chord perpendicular OM; distance from center to chord is OM=r. Length = 2 sqrt(1-r^2). Condition L>1 => 2 sqrt(1-r^2)>1 => 1-r^2>1/4 => r^2 <3/4 => r < sqrt3/2. M uniform in disk area density r dr / (1/2). Probability = area radius sqrt3/2 / area unit = (π*(3/4))/(π)=3/4. [[verification]]Wait check. If uniform midpoint in disc, yes P=3/4. But hold on known Bertrand paradox: random midpoint uniform in disc gives probability chord longer than side of inscribed equilateral triangle (sqrt3) =1/4. For length > radius different. Good.

[[planning]]Need "Explain the role of the centre." This likely references Bertrand paradox: "artist draws random chord" ambiguous; different methods yield different probabilities. Centre? The two procedures maybe have different treatment of center? Need explain role of centre maybe in choosing midpoint in disc: center more likely? Wait endpoints independent uniform boundary points: midpoint distribution not uniform; density concentrated toward center? Need compute role? The phrase "Explain the role of the centre" might refer to a trick from problem? [[alternative]]Maybe one procedure chooses uniform midpoint in disc; the centre of circle has zero-area point; maybe center as chord midpoint corresponds to diameter. Or "role of centre" maybe in endpoint procedure the centre isn't invariant? Let's parse.

Question: "An artist draws 'a random chord' of a unit circle. Compute the chance its length exceeds the radius for two procedures: join two independent uniform boundary points, or choose a uniform midpoint in the disc and draw the chord bisected there. Explain the role of the centre."

Need give probabilities and explanation. [[development]]The role of centre: Random chord is not well-defined; center symmetry? "centre" maybe crucial because when endpoints independent uniform boundary, the chord's midpoint distribution is not uniform; center is less? Let's calculate midpoint distribution? It may help explain discrepancy. They ask "Explain the role of the centre." Could mean: In the second procedure, choosing a uniform midpoint in the disc, the center is a single point and has probability zero; but chords near the center are diameters and longer than radius, and center is special. For length > radius, favorable midpoints lie within radius sqrt3/2, so center region leads to long chords; the excluded annulus near boundary yields short chords. In first procedure, endpoints uniform, many short chords near boundary; center doesn't bias? Let's investigate.

Could also be from a known puzzle where "An artist draws a random chord of a circle. What is probability its length exceeds radius? Consider two methods, explain role of centre." Perhaps one method: choose two independent uniform points on circumference. Second: choose midpoint uniformly in disc. [[verification]]They yield 2/3 and 1/4? Wait maybe ask length exceeds radius, not side of equilateral. We got 2/3 and 3/4.

But "Explain the role of the centre" maybe asks why the probabilities differ despite center? Maybe because "midpoint" for diameter: every chord has unique midpoint except? Actually every chord of a circle has a unique midpoint, including diameters whose midpoint is center. For first method, distribution of chord midpoints: are they uniform in disc? Let's check. [[development]]If endpoints uniform, chord midpoint position M = (A+B)/2. Its radial distance R = |cos(Θ/2)|? Suppose endpoints central angles ±φ around some midpoint angle; φ uniform? Let chord length 2 sin(θ/2) where θ minor central separation. Distance from center to chord = cos(θ/2). Midpoint M lies on angle average at distance cos(θ/2). Distribution: θ uniform [0,π]? The radial distance ρ = cos(θ/2), with θ uniform [0,π]? Then ρ ranges 1 to 0, density ∝ 1/sqrt(1-ρ^2)? Actually θ=2 arccos ρ, dθ/dρ = -2/√(1-ρ^2). density f_ρ = (1/π)*2/√(1-ρ^2)? ρ ∈[0,1]. Not uniform in disc (which f_ρ=2ρ). More mass near boundary? fρ increases to infinity near boundary? Wait for ρ near 1, density large; endpoint method chord midpoints are near boundary often? Let's test random endpoints close together -> short chord near boundary, midpoint near boundary; yes. Uniform midpoint in disc density radial 2ρ also near boundary but different.

[[verification]]"Role of the centre" might be about endpoints "independent uniform boundary points" have rotational symmetry but not uniform midpoint; center (diameter) occurs with what probability? Diameter exactly when endpoints antipodal, probability zero. Uniform midpoint: center also probability zero. Both center zero. But the center is a distinguished point because a chord's perpendicular distance from center equals distance from center to midpoint; the chord length depends only on that distance. The condition L>R corresponds to midpoints within a concentric circle radius √3/2 for midpoint procedure. For endpoint procedure, can condition be expressed with midpoint radius? Need distribution.

Need maybe mention "center" in choosing endpoint: One might incorrectly fix first endpoint? For two independent uniform boundary points, rotational invariance means fix first endpoint anywhere; the centre does not appear in distribution of angular separation. But in midpoint method, the centre determines radial distance and chord length; uniform area weights annular regions by r, giving different distribution.

[[conclusion]]Let's plan final:

Let unit circle radius 1. Chord length L=2 sin(α/2) where α is central angle between endpoints, 0≤α≤π. Condition L>1 iff α>π/3.

Procedure A: endpoints independent uniform on circumference. Fix A; B's angular position uniform on [0,2π). Minor central angle α is uniform on [0,π] (or just compute favorable arc). Unfavorable α≤π/3 occurs on arc of length 2π/3 total (±π/3), so P_fail= (π/3*2)/2π=1/3. P(L>1)=2/3. Alternative P=(π-π/3)/π=2/3.

Procedure B: choose midpoint M uniform in disk. Let R=OM. Area density f_R(r)=2r, 0≤r≤1. The chord with midpoint M has distance r from center, length L=2√(1-r²). Condition L>1 iff r<√3/2. Therefore P = area of disk radius √3/2 / area of unit disk = (√3/2)² = 3/4 (or ∫0^√3/2 2r dr=3/4).

Explain role of centre:
- Chord length depends only on distance d from center to chord, equal to OM for the midpoint; maximum at center (diameter length 2), decreases to 0 at boundary. Thus "longer than radius" corresponds to midpoints in central disk of radius √3/2. Uniform area in disc favors outer annuli by area (though condition central region).
- But if endpoints are chosen uniformly, the induced distribution of chord midpoints is not uniform in the disk; it is biased near the boundary, corresponding to many short chords. The center itself has probability zero in both continuous models; it is not a point mass. The apparent ambiguity/Bertrand paradox arises because "random chord" needs a measure on chord space; different geometric samplings weight chords differently. The centre provides natural radial coordinate for chord length, but does not fix the random procedure; you must say whether endpoints or midpoints are uniform.

[[verification]]Need maybe compute induced midpoint density to show role? Could include formula. Let's derive correctly.

For endpoints independent uniform boundary, let θ be minor angular separation ∈[0,π] with density 1/π? Wait if define θ minor in [0,π], yes uniform? Let's verify density: Difference Δ uniform [0,2π). Minor angle Θ = min(Δ,2π-Δ). For θ∈[0,π], P(Θ≤θ)? Δ in [0,θ] or [2π-θ,2π], total 2θ/(2π)=θ/π. density 1/π. Yes.

Midpoint radius ρ = cos(θ/2), since distance from center to chord. As θ increases 0 to π, ρ decreases 1 to 0. Distribution density f_ρ(ρ)= f_θ(2 arccos ρ)*|dθ/dρ| = (1/π)*(2/√(1-ρ²)), for ρ∈[0,1]. This is normalized? ∫0^1 2/(π√(1-ρ²)) dρ = 2/π * π/2=1. Yes. It diverges at ρ=1, meaning near boundary? Wait ρ is distance of midpoint from center. For short chords, θ small, midpoint near circle boundary ρ≈1. Density diverges at boundary; no midpoints beyond 1. Uniform disc radial density 2ρ, which is zero at center, linear to 2 at boundary. Endpoint distribution much more concentrated near boundary. But condition ρ < √3/2 gives probability ∫0^√3/2 2/(π√(1-ρ²)) dρ = (2/π) arcsin(√3/2)= (2/π)*(π/3)=2/3. Yes.

Could mention "centre has measure zero; no special probability mass. But radial distance from center determines length. For midpoint-uniform sampling, the area element 2πr dr gives the annular weighting, so center not favored; for endpoint sampling, distribution is different."

[[alternative]]Potential ambiguity: "choose a uniform midpoint in the disc and draw the chord bisected there." For a point M, there is exactly one chord with M as its midpoint? Let's confirm: Given M interior, chord whose midpoint M is perpendicular to OM, at distance OM from center. Yes unique. For M=center, diameter orientation arbitrary? Actually point center as midpoint: all diameters have center as midpoint, so not unique; but center has probability zero. Maybe "Explain the role of the centre" due to this nonuniqueness at the center? Wait! Important. [[conclusion]]If choose uniform midpoint in the disc, at center M=O, there is not a unique chord bisected there—any diameter has midpoint O. Measure zero, so ignore. But "role of the centre" might be about this uniqueness? The problem wording: "choose a uniform midpoint in the disc and draw the chord bisected there. Explain the role of the centre." Hmm.

Maybe they want discuss "centre" as not a point on any chord's midpoint? Let's see.

[[alternative]]The phrase "Explain the role of the centre" could be from an exam perhaps about a "random chord" problem and "centre" ambiguity. They may expect: In the first procedure, joining two independent uniform boundary points, the center of the circle can be ignored by symmetry? In the second, choosing a uniform midpoint in disc treats the center as one of possible midpoints; but for the center, chord not uniquely determined. Since probability zero, okay. However, center's role in determining chord length: chord length is determined by distance of midpoint from center. Need mention that.

[[planning]]Let's consider all possible interpretations and include enough.

Need maybe answer if "length exceeds the radius" unit circle. We have probabilities.

Let's be meticulous:

[[verification]]Procedure 1:
Let X,Y i.i.d. Uniform(S^1). Let D be shorter arc central angle. D uniform on [0,π]? More exactly D has CDF d/π. L = 2 sin(D/2). Condition L>1 iff D>π/3. P=1 - (π/3)/π =2/3.

Wait check CDF D uniform? Yes P(D≤d)=d/π for d∈[0,π]. Then fail D≤π/3 =1/3. Good.

[[verification]]Procedure 2:
M uniform in unit disk. Let R=OM. The chord with midpoint M is perpendicular to OM. Its distance from O is R; half-length = √(1-R²). L=2√(1-R²). Condition >1 iff R<√3/2. Since M uniform, P(R<r)= area radius r / area unit = r². Plug r²=3/4. P=3/4.

[[conclusion]]Centre role:
- For any chord, the perpendicular from center meets chord at its midpoint, so distance from centre to chord equals distance from centre to midpoint. Thus L=2√(1-d²).
- The condition L>1 is d<√3/2: midpoints must lie within a central disk.
- But "uniform midpoint" samples area uniformly, hence P is area ratio. Endpoint sampling gives a different density of midpoints f(d)=2/(π√(1-d²)) for d∈[0,1], not uniform; it overweights chords near boundary. The center itself has probability 0 in both; at M=O the chord is a diameter (orientation arbitrary), but this exceptional point doesn't affect probability. The discrepancy (Bertrand paradox) shows "random chord" not determined by circle alone; the center provides radial length formula but not a sampling distribution.

Need be cautious with phrase "uniform midpoint in the disc and draw the chord bisected there": If M=center, "the chord bisected there" is not unique; but measure zero. We can state.

[[verification]]Let's also think whether in procedure 2, "choose a uniform midpoint in the disc" means midpoint of chord uniform conditional on chord? The distribution of midpoint of a chord under invariant measure? There is also "uniform midpoint in the disc" known method, yes. There is subtlety: A point closer to boundary has unique chord perpendicular to radius; center all diameters. Fine.

What if "choose a uniform midpoint in the disc" could mean choose point uniformly in disk as midpoint of chord, then chord is perpendicular to line from center to point. We used.

Need maybe mention radius of circle is 1, so chord length comparable to radius. Good.

[[conclusion]]Let's craft final answer with clear computations and maybe small note.

Desired oververbose 5. Need not huge. Include formulas.

Let's produce final in prose/equations.
