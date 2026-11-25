---
trace: ds-mat-04
annotator: Codex (AI)
status: corrected
concepts: []
topics: []
---
[[planning]]We need answer. Need parse. Urn 4 white W,3 blue B,2 orange O total9. Draw without replacement until first orange. Count number of different non-orange colours seen before stopping. Non-orange colors are W and B. Need expected number of distinct colors among {W,B} observed before first orange. This can be 0,1,2. Need compute and check by method no complete draw sequences. Need provide likely exact.

We need reason. We can derive indicator method. [[development]]Let X = I_white seen before first O + I_blue seen before first O. E X = P(W before first O among W and O? Need blue ignored?) White is seen before first orange iff in the relative order of the 4 W and 2 O, first among these is W. B beads can intersperse but irrelevant. Since white count 4, orange count 2. P(a W precedes all O's in restricted permutation of W/O) = n_W/(n_W+n_O)=4/(4+2)=2/3. Similarly blue seen before first orange iff first among 3 B and 2 O is B =3/(3+2)=3/5. [[conclusion]]Then expectation = 2/3 + 3/5 = 19/15 = 1.266666. [[verification]]Wait is distinct count sum indicators? Yes each non-orange colour seen before stopping. Need account orange first overall? If first orange maybe before any. The event color c seen before first orange only depends on relative order of that color and oranges; other colors ignored. Correct.

[[verification]]Check with method not enumerate complete draw sequences. Could use survival formula E[N]=sum_{k>=1} P(N >= k). N number distinct non-orange colors seen. N∈{0,1,2}. E[N]=P(N≥1)+P(N≥2). Alternatively P(N≥1)=1-P(no W or B before first O) =1-P(first bead is orange or all non-oranges? Actually no non-orange before first O means first draw is orange (since if first non-orange before orange, then seen). P first draw orange=2/9. So P(N≥1)=7/9. P(N≥2)=both W and B seen before first O. Need compute via inclusion-exclusion: P(W seen and B seen before O)=1 - P(W not seen before O)-P(B not seen before O)+P(neither seen before O). W not before first O means first among W/O is O =2/(4+2)=1/3. B not before first O =2/(3+2)=2/5. Neither W nor B before O means first bead is O =2/9. Thus P(both)=1-1/3-2/5+2/9 = common45:45-15-18+10=22/45? Wait 1 - .333 -.4 +.222= .4889 yes 22/45. Then E=7/9+22/45=35/45+22/45=57/45=19/15. Good.

[[verification]]Could also compute directly distribution: P(N=0)=2/9. P(N=1)=? sum only one color before first orange. P(W seen, B not) = P(W before O and B after first O?) Need not simple maybe. But not needed.

[[conclusion]]Need present answer. User says "Check your result by a method that does not enumerate complete draw sequences." Need explicitly show verification using indicator plus survival perhaps. Need maybe phrase "first method indicator, check via tail-sum/inclusion-exclusion." It says "Check your result by a method..." Could mean compute using one method, then check by another not enumerating sequences. We can present both.

[[verification]]Let's ensure no subtlety: Draw until first orange, count different non-orange colors seen before stopping. Does "before stopping" include draw that is orange? No non-orange. If an orange drawn, stop; non-orange colours seen prior. If multiple beads same color before first orange count once. Indicators for white/blue being present before first orange.

[[alternative]]Alternative direct enumeration by first orange position and colors? Not complete sequences. Could derive P(N=1). But expectation indicator easiest.

[[development]]Let's formulate:
Let A_W = {at least one white appears before first orange}. Let A_B. N=1_{A_W}+1_{A_B}.
For A_W, ignore blue beads. Among the 4 white and 2 orange beads, in their relative order all orders equally likely (because blue insertions do not affect). The first among these six is white with probability 4/(4+2)=2/3. Similarly P(A_B)=3/(3+2)=3/5.
[[conclusion]]Thus E[N]=2/3+3/5=19/15.

[[verification]]Check: Tail-sum formula:
E[N]=P(N≥1)+P(N≥2), since N≤2.
P(N≥1)=1-P(no W or B before first O)=1-P(first bead is O)=1-2/9=7/9.
P(N≥2)=P(A_W∩A_B)=1-P(A_W^c)-P(A_B^c)+P(A_W^c∩A_B^c).
A_W^c: no W before first O iff first among W and O is O -> 2/6=1/3.
A_B^c: first among B and O is O ->2/5.
A_W^c∩A_B^c: no W/B before first O iff first bead O ->2/9.
So P(both)=1-1/3-2/5+2/9 = compute. 1=45/45, -15/45, -18/45,+10/45 =22/45.
Then E=7/9+22/45=35/45+22/45=57/45=19/15.
This check uses events/tail-sum, not complete sequence enumeration. Good.

[[conclusion]]Need perhaps mention expected = 1.266... Does "different non-orange colours" could be interpreted as number of colors among all non-orange beads drawn before first orange. Since only two possible, yes.

Let's craft final with clarity. Maybe note "blue beads are irrelevant to whether a white is seen before orange" and relative order argument. We can include exact and decimal.

Need ensure no final too long but desired 5. Provide concise.
