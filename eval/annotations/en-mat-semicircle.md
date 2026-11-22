---
trace: en-mat-semicircle
annotator: Joe
drafted_by: Claude (AI assistant), to be corrected
status: draft
concepts: [rectangle, semicircle, diameter, area, derivative, vertex, arc, radius]
topics:
- [rectangle, vertex, corner, base, width, height]
- [semicircle, diameter, arc, radius, circle]
- [area, derivative, maximum, calculus]
- [trig, AM-GM, equality]
---
[[planning]]We need answer. Need solve calculus and check another way. Need be careful geometry. Rectangle inscribed in semicircle radius 5, one side on diameter. Need max area. Let's parse.

[[planning]]Semicircle radius 5: likely upper half of circle x^2+y^2=25, y>=0. Rectangle with one side on diameter (x-axis). Usually base lies along diameter, symmetric? If rectangle inscribed in semicircle with one side on diameter: base on diameter, two upper vertices on arc. To maximize area, rectangle centered? Need consider if one side on diameter not necessarily entire base centered? Let base endpoints on diameter? A rectangle with bottom side on diameter and upper two vertices on semicircular arc? [[development]]If bottom side endpoints at (a,0),(b,0) with a<b, top corners at (a,h),(b,h). Both top corners on arc requires a^2+h^2=25 and b^2+h^2=25 => a^2=b^2. Since a<b and within [-5,5], if h>0, a=-b. So centered automatically if both top vertices on arc. If one top vertex maybe? "Inscribed" typically all four vertices on boundary? In semicircle, bottom side on diameter means bottom vertices lie on diameter (boundary). Top vertices on arc. Thus centered. [[development]]Width 2x, height y, with x^2+y^2=25, x>=0. Area A=2xy =2x sqrt(25-x^2). Maximize. Derivative etc: A^2=4x^2(25-x^2); max at x^2=25/2. A=2*(5/sqrt2)*(5/sqrt2)=? x=y=5/sqrt2. Width=2x=5sqrt2, height=5/sqrt2. Area=2 x y = 2*(25/2)=25. Wait width*height =5sqrt2 *5/sqrt2=25. yes.

[[verification]]Check another way: AM-GM or trig. Let x=5 cos theta, y=5 sin theta? Area=2*(25) sinθ cosθ? Actually width 2*5 cosθ? Coordinates top vertex (5 cosθ,5 sinθ), width 2x=10 cosθ, height y=5 sinθ. Area=50 sinθ cosθ=25 sin 2θ ≤25 equality θ=π/4. Or AM-GM: x^2+y^2=25. Max 2xy when x=y due x^2 y^2. Or geometric? Need "check it another way." Could use calculus then check via trig/AM-GM.

[[alternative]]Need answer concise. Maybe mention if interpretation less strict? Let's consider possibility rectangle base does not necessarily have both upper vertices on arc? "Inscribed in semicircle" means rectangle contained in semicircle and one side on diameter. For maximum, likely top corners on arc. Could there be rectangle with one side along diameter but not symmetric, with upper vertices within semicircle? To be inscribed, all vertices on boundary? In a semicircle, base side endpoints on diameter (boundary), top side endpoints on arc? Yes.

[[development]]Let's craft with calculus.

Set up coordinates:
Semicircle: x^2+y^2≤25, y≥0. Let right top corner be (x,y), then width = 2x (by symmetry? Need derive maybe). If base on diameter and rectangle inscribed, top vertices at (-x,y),(x,y), so x^2+y^2=25. Area A(x)=2x y=2x√(25-x²), 0<x<5.
Differentiate:
A'(x)=2√(25-x²) - 2x²/√(25-x²) = [2(25-2x²)]/√(25-x²). A'=0 x²=25/2. A'' or endpoints show max. y=√(25-25/2)=5/√2, x=5/√2. A_max=2*(5/√2)*(5/√2)=25.

[[alternative]]Alternatively differentiate log A? fine.

[[verification]]Check via trig:
Let x=5 cos θ, y=5 sin θ, 0<θ<π/2. Area A=2(5 cosθ)(5 sinθ)=50 sinθ cosθ=25 sin2θ ≤25 with equality at 2θ=π/2, θ=π/4. Dimensions x=y=5/√2, width 5√2 height 5/√2 area 25.

Could also check by AM-GM: A²=4x²y²≤(x²+y²)²? Wait AM-GM: x² y² ≤ ((x²+y²)/2)² = (25/2)², so A ≤ 25. equality x²=y²=12.5. Nice.

[[conclusion]]Need maybe include "maximum area = 25 square units." Perhaps "not 50". Let's final with steps.
