---
trace: ds-sci-01
annotator: Codex (AI)
status: corrected
concepts: []
topics: []
---
[[planning]]We need answer. Need parse problem. Need be careful. Rigid cylinder uniform density 750 kg/m3 floats vertically in water 1000. Held upright by frictionless guide. Height 40 cm, area 50 cm2. A 300 g load rests on top. Find its new freeboard and largest further mass it can carry before top reaches water. Verify by displaced volume.

Need interpret. Cylinder initially? "A rigid cylinder ... floats vertically in water... held upright by a frictionless guide. It is 40 cm tall ... A 300 g load rests on top. Find its new freeboard and the largest further mass it can carry before top reaches water." Maybe cylinder initially floating without load? Then add 300g, find freeboard. Then largest further mass before top reaches water. Need determine.

[[development]]Need compute mass cylinder: density 750 kg/m3, volume area*height. A=50 cm2 = 50e-4=0.005 m^2. H=0.40 m. Volume=0.002 m^3. Mass=0.75? [[backtrack]]0.002*750=1.5 kg. Weight=14.715 N.

Water rho=1000. Load=0.300 kg. [[development]]Total mass =1.8 kg. For floating, displaced water mass equals total mass =1.8 kg. Volume displaced = m/rho_water =1.8/1000=0.0018 m3 = 1800 cm3. Cylinder area 50 cm2, submerged height = V/A=0.0018/0.005=0.36 m =36 cm. Cylinder height 40 cm. Freeboard above water = total top? Top of cylinder above water = H - submerged height =4 cm. [[alternative]]But there's a load on top. Freeboard usually distance from waterline to top of cylinder (top edge) = 4 cm. Does load height matter? likely no. [[verification]]"new freeboard" after adding load maybe initially freeboard? Let's compute before load: mass 1.5 kg, displaced volume 1.5e-3 m3, submerged h=0.3 m=30 cm, freeboard=10 cm. After 300g, freeboard=4 cm. It says "new freeboard" maybe after the 300 g load. Yes.

[[development]]Largest further mass it can carry before top reaches water. At top reaches water, submerged height = full height 40 cm =0.4 m. Displaced volume=0.005*0.4=0.002 m3, displaced mass =2 kg. Total supported mass =2 kg. Current mass =1.5+0.3=1.8 kg. Further mass max =0.2 kg =200 g. Check. [[verification]]If load's own volume? It rests on top, mass only; it doesn't displace water? If top reaches water before load maybe "before top reaches water" cylinder top. The load is on top; at top waterline, load may enter? It says load rests on top, largest further mass before top reaches water. We assume load does not add buoyancy. Further mass=200g.

[[verification]]But there is mention "held upright by a frictionless guide" could imply guide exerts vertical? Frictionless guide prevents tilt/lateral, no vertical force. Fine.

But potential ambiguity: The 300g load rests on top, and the largest further mass it can carry before the top reaches the water. Need maybe after adding 300 g, what is new freeboard and max additional mass? We got.

[[planning]]Need "Verify by displaced volume." Need perhaps provide calculations using displaced volume to verify. Could show:
[[verification]]Cylinder mass m_c = rho_c A H =750*(50e-4)*(0.40)=1.5 kg.
With 0.3 kg, total =1.8 kg, so displaced water volume V_d = m_total/rho_w =0.0018 m3 =1800 cm3. Height submerged = V_d/A =0.36 m=36cm. Since height 40, freeboard =4 cm.
At top at water level, max displaced volume= A H=0.002 m3=2000 cm3, corresponding water mass=2.0 kg. Total capacity=2.0 kg. Existing total 1.8, additional =0.2 kg. Also freeboard at current is 4 cm; additional mass needed to submerge 4 cm is rho_w A *0.04 =1000*0.005*0.04=0.2 kg. Wait 4 cm =0.04m. Yes additional =0.2 kg. Verify.

[[verification]]Need ensure units: cross-sectional area 50 cm2 = 50*(1e-2 m)^2 =50e-4=5e-3. Height 40cm=0.4m. Volume=2e-3 m3. cylinder density 750 -> mass=1.5 kg.

Potential issue with "freeboard" defined as vertical distance from water surface to top of cylinder excluding load. If load sits on top, top edge? Yes.

[[alternative]]Let's consider if "new freeboard" could ask original freeboard after load? Yes.

Maybe there is a trick: The cylinder is held upright by a frictionless guide, and load on top. A uniform density cylinder floats vertically. [[verification]]Density 750<1000, so without load it floats with 75% submerged? Let's calculate: submerged height = (rho_cyl/rho_water)*H =0.75*0.4=0.3m, freeboard=0.1m. Add 300g, freeboard reduces by 6 cm? Wait additional 300g submerges volume =0.3/1000=0.0003m3; height 0.0003/0.005=0.06m=6cm. So freeboard=10-6=4cm. Then max further before top =4cm worth =0.005*0.04*1000=0.2 kg. Good.

[[alternative]]But wait if 300g load "rests on top" and "new freeboard" maybe the top of load? Usually freeboard of cylinder: distance from waterline to top of cylinder. Load might be on top and increases top height, but freeboard of ship includes deck to water, not cargo. Since only cylinder dimensions given. Good.

[[conclusion]]Need likely provide final with clear steps. Since "verify by displaced volume," maybe do both mass force and displaced volume. We can mention neglecting volume of load (assumed compact/no buoyancy) and guide has no vertical force.

Need maybe discuss frictionless guide: no vertical friction, so force balance only weight buoyancy. If guide "held upright" may be fixed in horizontal but allows vertical; no vertical effect.

Let's craft final answer with calculations.

Need ensure not overexplain. Desired oververbosity 5. Include formulas.

[[verification]]Potential alternative: "largest further mass it can carry before the top reaches the water" Could mean when the top just reaches water, freeboard zero. If load is resting on top, before top reaches water means water just reaches top edge of cylinder, not load. Good.

[[conclusion]]Let's formulate:

Given:
A=50 cm²=5.0×10^-3 m²
H=40 cm=0.40 m
ρ_c=750 kg/m³
ρ_w=1000 kg/m³
m_load=0.300 kg

Cylinder mass:
m_c=ρ_c A H=750(5e-3)(0.40)=1.50 kg.
Total with load=1.80 kg.

Floating:
m_total=ρ_w A x_sub ⇒ x_sub=m_total/(ρ_w A)=1.8/(1000*0.005)=0.36m=36cm.
Freeboard f=H-x_sub=40-36=4.0cm.

Maximum:
At top at waterline, x_sub=H=0.40m, displaced mass:
m_max displaced=ρ_w A H=1000(0.005)(0.40)=2.00 kg.
Total load capacity (including cylinder) =2.00 kg. Existing total mass=1.80 kg. Further mass=2.00-1.80=0.20 kg=200g.

Displaced volume verification:
With load: V_d=m/ρ=1.8/1000=1.8e-3 m³=1800 cm³. Submerged height=V_d/A=1800/50=36 cm.
At max: V_d,max=A H=50*40=2000 cm³, displaced mass=ρ V=1000*2e-3=2.0 kg. Additional volume needed to go from 36 to 40 cm: 50cm²*(4cm)=200cm³, mass=200cm³*1g/cm³=200g.

Need maybe include "new freeboard after 300 g load is 4.0 cm" and "largest further mass 0.20 kg". Good.

Let's final.
