---
trace: ds-sci-04
annotator: Codex (AI)
status: corrected
concepts: []
topics: []
---
[[planning]]We need answer. Need parse astronomy transit geometry. Need estimate speed for two contact durations. Star diameter D=1.40e6 km. Planet diameter = one tenth =1.40e5 km. Crosses centre of star's disc in 6.0 hours at constant projected speed. Ambiguity: duration 6.0 hours maybe "crosses centre ... in 6 h" for what contact? They ask Estimate speed if duration is first to last contact and if second to third contact. State geometry behind each reading.

We need determine projected speed based on chords central. [[development]]First-to-last contact (external contacts) duration from planet's leading limb touches stellar limb to trailing limb leaves, with centers separated along path by star radius + planet radius at ingress/egress? Actually "duration is first to last contact" likely total transit duration from first contact (planet just touches star's disk externally) to last contact (fully leaves) when path crosses center. During first-to-last, planet center moves distance equal star diameter + planet diameter? Let's derive.

Top view projected: Star disk radius R. Planet disk radius r. Planet moves along center line (impact parameter b=0). Contact definitions:
1st contact: planet's leading edge touches star's left limb externally. Centers separated by R+r. Let x1 = -(R+r) if moving in +x, just before overlapping? Actually first contact at left side: planet center x=-(R+r).
[[development]]2nd contact: planet's trailing edge? Need nomenclature: For transit:
First contact: planet's leading limb touches star's limb (planet fully outside; external tangent).
Second contact: planet fully enters disk, its trailing limb? Wait. Standard:
1st contact: planet's leading edge contacts stellar disk (start transit).
2nd contact: planet's trailing edge contacts stellar limb? Let's visualize planet moving from left to right across star. At first contact, planet's rightmost point touches star's leftmost point. Center at x=-(R+r). Then as moves in, at second contact the planet is entirely inside stellar disk, just after full disk overlap begins: its leftmost point tangent to star's left limb. Center x=-(R-r). Wait if moving right, planet center at x=-(R-r), left edge at x-R? Check: planet left edge = x - r. Star left limb = -R. For second contact full entry: planet's left edge meets star's left limb as it moves inside? At x= -R + r, planet left edge = -R, yes. But standard 2nd contact occurs when planet's trailing edge (left side because moving right? Let's clarify leading/trailing: moving right, leading limb is right side, trailing is left. First contact leading limb touches star's left limb as center x=-(R+r) (right edge at -R). Second contact trailing limb touches star's left limb as center x=-R+r? At that point left edge at -R? But trailing limb is left edge; yes it touches star's left limb. During interval centers move distance 2r. Hmm that seems short 2r, which is ~0.1 D, duration ~0.6h. [[alternative]]Standard second-to-third contact is full transit duration between internal contacts = 2 sqrt((R-r)^2 - b^2)/v, near center =2(R-r)/v. First-to-fourth = 2 sqrt((R+r)^2-b^2)/v. So 1st-to-last distance (first to fourth) =2(R+r) at b=0. Second-to-third distance=2(R-r). Alternatively if last contact is fourth: center x=+(R+r), total distance 2(R+r). 2nd to 3rd: centers at x=-(R-r) and +(R-r): distance 2(R-r).

[[verification]]But user wording: "duration is first to last contact and if it is second to third contact." Need map: first-to-last contact duration, if 6 h is first contact to last contact, then speed = (star diam + planet diam? wait 2(R+r)=D_s + D_p) / duration. If 6 h is second-to-third contact (full transit of planetary disk across star? Actually interval when planet fully within star) then speed = (D_s - D_p? Wait 2(R-r)=D_s - D_p) / duration. [[development]]Need check: R=7e5, r=7e4. First-last distance =2(R+r)=2(770,000)=1,540,000 km = D_s + D_p =1.54e6 km. Second-third distance=2(R-r)=2(630,000)=1,260,000 km =D_s - D_p=1.26e6 km.

Given 6 h, speeds:
v1=1.54e6 km / 6 h = 256666.7 km/h = 71.3 km/s.
v2=1.26e6/6=210000 km/h=58.3 km/s.
[[verification]]Maybe if first-to-last duration includes from first to fourth, yes.

But wait phrase "A small planet crosses the centre of a star's disc in 6.0 hours at constant projected speed. Its own diameter is one tenth of the star's diameter ... Estimate speed if duration is first to last contact and if it is second to third contact. State geometry behind each reading."

Could mean "crosses the centre of a star's disc in 6h" perhaps they provide same 6h duration for crossing centre? Actually they ask estimate speed if duration is first to last contact and if second to third contact. Need calculate both scenarios with same 6h. Need define contacts and geometry. They may expect first-to-last contact: from first contact (leading edge just touches) to last contact (trailing edge just leaves) the center travels distance equal to diameter of star plus diameter of planet? Need state geometry.

Let's double-check possible interpretation of "first to last contact" maybe first contact (limb touches) to last contact (center? no last = fourth contact). We should label 1st and 4th. Distance = D_star + D_planet because total path swept by union of their projected disks from just tangent on one side to just tangent on other. Alternatively "first to last contact" may be first contact to fourth = star diameter + planet diameter along centerline. If someone might use D_star + 2r? Wait let's verify with geometry carefully.

Coordinate star center at 0, radius R. Planet radius r moving along x-axis y=0. First contact leading edge touches star's left limb: x_p + r = -R (if moving right; leading edge is right side, right edge = x+r). So x_p = -R - r. Last contact leading? fourth contact trailing edge leaves star's right limb? At exit, planet's left (trailing) edge touches star's right limb as overlap ceases: x_p - r = +R. x_p = R + r. Distance = (R+r)-(-R-r)=2(R+r)=D_s + D_p. Yes.

Second contact: after full entry, planet's trailing edge (left edge) tangent to star's left limb: x_p - r = -R => x= -R + r = -(R-r). Third contact before exit, leading edge tangent to star right limb: x_p + r = +R => x=R-r. Distance=2(R-r)=D_s - D_p. Good.

[[verification]]Speeds:
D_star =1.40 million km =1.40×10^6 km. D_planet=0.1 D_star=1.40×10^5 km.
First-last distance=1.40e6 +1.40e5=1.54e6 km. Time 6h. Speed =2.5667e5 km/h. Convert m/s? Use km/s divide 3600 =71.296 km/s. Maybe present 7.1e4 m/s? 71 km/s.

Second-third distance=1.40e6 -1.40e5=1.26e6 km. /6h=2.10e5 km/h =58.333 km/s.

[[conclusion]]Need mention constant projected speed; central transit chord; no impact parameter. Geometry maybe "first contact: leading limb just touches stellar limb; fourth contact: trailing limb just leaves opposite limb". "second contact: planet fully inside, trailing limb at ingress limb; third contact: leading limb at egress limb." The center of planet moves D*±D_p along the diameter.

Could also note if duration uses same 6.0 h for both, the inferred speed differs; they cannot both be true for same planet/star. If one observed duration is first-to-last then v=71 km/s; if observed duration corresponds to second-to-third then v=58 km/s. If actual 6h meant something else, adjust.

Let's formulate final with equations.

[[verification]]Need be cautious with contact terminology maybe first-to-last contact vs first-to-fourth. I can state assuming "last" = fourth contact. Geometry diagrams verbally.

Let's include maybe "at central crossing, impact parameter b=0." If not exactly central? It says centre, so yes.

Let's maybe explain "projected speed" is the speed of planet's center across plane of sky, not orbital speed. The "duration" is time interval between specified contacts. The center moves a horizontal distance L = v Δt. For first-to-last, L = D_s + D_p. For second-to-third, L = D_s - D_p.

[[verification]]Let's calculate exact:
D_s=1.40 million km (1.40×10^6 km).
D_p=0.10×D_s=1.40×10^5 km.
T=6.0 h = 2.16×10^4 s.
v_1 = (1.40e6+0.14e6) km / 2.16e4 s =1.54e6/21600 =71.2963 km/s. In m/s =7.13e4 m/s.
v_2=(1.40e6-0.14e6)/21600 =1.26e6/21600 =58.333 km/s.
In km/h: 2.57e5 km/h, 2.10e5 km/h.

Maybe use million: first travel 1.54 million km in 6h. second travel 1.26 million km. Good.

[[conclusion]]Let's final with concise but enough.
