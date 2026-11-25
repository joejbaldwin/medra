---
trace: ds-sci-08
annotator: Codex (AI)
status: corrected
concepts: []
topics: []
---
[[planning]]We need answer. Need parse. Need be careful. Problem likely trick: pan initially 300g of 12% salt solution by mass. [[development]]Thus salt = 36g, water=264g. Water evaporates leaving total 100g. At that temperature solubility: at most 36 g salt dissolve per 100 g liquid water. Need find masses dissolved and crystalline salt. Need check conservation and distinguish concentration in liquid from salt fraction whole pan.

[[planning]]We need determine final liquid water amount? Total final = 100g = liquid water + dissolved salt + crystalline salt. Water evaporated = initial water 264 - final water. But final water unknown. Solubility condition may indicate saturated? We need solve. [[development]]Initial salt 36g. Final total 100. [[alternative]]If all salt dissolved? final water =64g. Solubility limit for 64g water: dissolved max = (36/100)*64=23.04 g. But salt available 36, so some crystallizes. [[development]]Let W final liquid water. If crystals present, liquid saturated: dissolved salt D = 0.36 W (since 36 per 100). C crystalline = 36-D. Total final mass: W + D + C = W +36 =100? Wait total salt conserved=36, water W, crystals C. Total = W + D + C = W+36. If total final =100, W=64 g. Then D=0.36*64=23.04. C=36-23.04=12.96. [[verification]]Check total =64+23.04+12.96=100. This seems straightforward. [[development]]But there is subtle distinction concentration in liquid: D/(W+D)=23.04/(64+23.04)=23.04/87.04=26.4706% salt by mass of liquid solution; vs solubility ratio 36g/100g water = 36/(136)=26.47% by mass solution. Salt fraction whole pan =36/100=36%, not same. Need distinguish. [[verification]]Check conservation: salt dissolved + crystalline = 36 (initial). water final 64, initial 264, evaporated 200. Liquid solution mass = W+D = 87.04 g. Whole pan mass = liquid solution + crystals = 87.04+12.96=100. Salt fraction pan 36/100=36%. [[alternative]]If someone may mistakenly use 36g per 100g liquid water as 36% of total? Need explain.

But need consider wording: "Water evaporates, leaving 100 g total in the pan at a temperature where at most 36 g of salt dissolve per 100 g of liquid water." Is final total includes crystals? Yes. Need final masses dissolved and crystalline. We have.

[[conclusion]]Let's craft final with equations, maybe note saturation is assumed because if all dissolved would require more water than available under solubility. Actually final water determined by total and salt conservation. Need show.

Let's denote initial: m_salt = 0.12*300=36 g. m_water initial=264. Let final liquid water = w, dissolved salt = d, crystals = c. Conservation salt: d+c=36. Final total: w+d+c=100 => w+36=100 => w=64. Solubility: at saturation d/w=36/100 if c>0; assume c positive. d=0.36*64=23.04. c=12.96. Check if all dissolved impossible: if c=0 then final solution 100g with d=36g and water=64g, ratio d/w=36/64=0.5625 >0.36, exceeds solubility. So crystals present and saturated assumption valid. Actually if c=0 total would imply w=64. It exceeds. Good.

Need perhaps consider "at most 36 g salt dissolve per 100 g liquid water" final should be saturated if crystals present. Since there are crystals, exactly at max. We can derive.

Check liquid concentration: d/(d+w)=23.04/(23.04+64)=23.04/87.04. Compute exact: 23.04=576/25? Wait 23.04 = 576/25? 23.04*25=576 yes. W=64=1600/25. Sum=2176/25=87.04. Ratio (576/25)/(2176/25)=576/2176= divide 64? 576/64=9, 2176/64=34. So 9/34 = 0.264705882. Ah exact. Solute per 100g liquid water = d/w = (576/25)/64 = 576/1600 = 0.36. Solution mass percentage = D/(W+D) = 0.36/(1.36) = 36/136=9/34 = 26.47%. Whole pan salt fraction = (d+c)/(w+d+c)=36/100=36%. Whole pan "concentration" as mass percent includes crystals? Usually if salt fraction of whole pan = 36% but not dissolved concentration. Need mention.

Need maybe mention "liquid water" not "liquid solution". The phrase "at most 36 g salt dissolve per 100 g liquid water" means ratio D/W ≤0.36. If using concentration in liquid as mass fraction, saturated brine is 36/(100+36)=26.47% salt by mass, not 36%. The whole pan with crystals has 36g salt/100g total=36% salt by mass, but only 23.04g dissolved in 87.04g liquid solution (26.47% in solution), and 12.96g crystals.

Need answer concise. Could mention evaporation amount = 200g. [[verification]]Check mass: final liquid water 64g + dissolved salt 23.04 + crystals 12.96=100. Salt total=36, water total=64, evaporated=264-64=200.

[[conclusion]]Let's final.
