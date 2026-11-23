---
trace: en-log-league
annotator: Kostya
drafted_by: Claude (AI assistant), to be corrected
status: draft
concepts: [team, match, draw, win, point, loss, record, decisive match]
topics:
- [win, draw, loss, point]
- [team, match, result]
- [record, decisive match, draw match]
---
[[planning]]We need answer solve. Need be careful: Four teams round robin once = 6 matches. [[development]]Points totals sum = 7+5+3+1=16. In football 3-1-0, each match total points is either 3 (decisive) or 2 (draw). If all 6 decisive total 18. Let x draws, total = 18 - x. Here 16 => x=2 draws. [[planning]]Need determine match results uniquely? Let's solve.

Teams A 7, B5, C3,D1 with 3 games each. Need assign outcomes among pairs AB, AC, AD, BC, BD, CD (depending order).

Let W,L,D counts per team. Points 3W + D. Games=3 so W+D+L=3.

[[development]]A: 3W_A + D_A=7. possibilities W=2,D=1 ->7, L=0. W=1 gives D=4 impossible; W=... So A: 2 wins, 1 draw, 0 losses.
B: 3W_B + D_B=5. possibilities W=1,D=2,L=0 (1*3+2=5). W=0 D=5 impossible; W=... So B: 1 win,2 draws,0 losses.
C: 3W_C+D_C=3. possibilities W=1,D=0,L=2. Or W=0,D=3,L=0? Points 3 with 3 draws possible too. Need consider. C: either (1W,0D,2L) or (0W,3D,0L). [[development]]But total draws count? Each draw contributes two draws to team counts. Total D_i = 2*#draws matches =4. A D=1, B D=2 already sum3. D team? Let's continue.
D: 3W+D=1. possibilities W=0,D=1,L=2. (since win impossible). So D D=1.

Team draw counts: A1+B2+C?+D1 =4. Thus C's D count must be 0 (1+2+0+1=4). Therefore C: 1W,0D,2L. Good. Unique records.

[[verification]]Total wins counts: A2,B1,C1,D0 sum=4. Total losses: A0,B0,C2,D2 sum4. So exactly 2 decisive matches? Wait with 2 draws, decisive matches=4, each has one win one loss, sum wins=4 yes.

[[development]]We need construct outcomes satisfying records and match pair results. Draws are edges (AB etc) matching D counts:
Draw incidences: A one draw, B two draws, C zero, D one draw. C no draws. Since C no draws, matches involving C all decisive: AC, BC, CD. A has one draw among AB/AD? Since AC decisive. B has two draws among AB,BD? (BC decisive). D has one draw among AD,BD? (CD decisive). Need choose draws edges with degrees A1,B2,D1,C0 on K4. Sum degrees 4 => 2 edges. B degree2 means B must draw with A and D? Since only opponents not C: A,D (and maybe C no). B must draw both AB and BD? B has 3 matches: vs A, C, D. C match decisive, so B needs 2 draws, indeed must draw with A and D. Then D has draw vs B, so no draw vs A. A draw vs B only. Thus draw matches: A-B draw, B-D draw. All other matches decisive. Then outcomes for decisive based records.

[[development]]Let's determine:
A record: 2W,1D,0L. Draw vs B. Must beat C and D.
B: 1W,2D,0L. Draw A,D. Must beat C.
C: 1W,0D,2L. Loses to A,B? If A beats C and B beats C, then C has 2 losses, cannot get win? It has matches A,B,D; loses to A,B, so must beat D to have 1W. Yes C beats D.
D: 0W,1D,2L. Draw B, loses to A and C. Consistent.
[[conclusion]]So unique results:
A beats C, A beats D; A-B draw.
B draws A, B draws D, B beats C.
C beats D; loses to A,B.
D draws B; loses to A,C.
[[planning]]Need answer question "What was result of every match? Is it only possibility?" Explain uniqueness. Need maybe mention if points totals determine records; no alternative. [[verification]]But let's verify no hidden issue: Could there be different with C 3 draws? We excluded via draw count due total sum. Let x draws computed from total points 16. If C had 3 draws, then A D1+B D2+C D3+D? sum draw incidences would at least6 -> #draws3; total points? Wait total 16 dictates exactly 2 draws because each draw reduces total by 1 from decisive maximum 18. But sum per team: A 7 possible (2W1D). B 5 (1W2D). If C 0W3D, D 0W1D, total team draw incidences=1+2+3+1=7 odd impossible because each draw counts 2; also #draws=3.5 not. So no.

[[planning]]Let's craft concise but with method. Maybe table.

Need be careful match notation "A v B: draw" etc. Provide points check.

[[conclusion]]Let's final with table:

A vs B: 1-1 (or draw)
A vs C: A wins
A vs D: A wins
B vs C: B wins
B vs D: draw
C vs D: C wins

Need if exact scores? The question "result" maybe win/draw/loss, not scores; impossible to know scorelines. We can say any scores realizing these (e.g., 1-0). Use table result.

[[verification]]Also uniqueness proof:
Total points =16. Six matches. If all wins total 18. Each draw reduces total by1, so exactly 2 draws.
A must be 2W1D; B must be 1W2D; D must be 0W1D (D has 1 point). Total draw incidences from A,B,D =1+2+1=4, which exactly accounts for two draws, so C has no draws. Thus C from 3 points with no draws =1W2L. Since C no draws, its games are decisive. B has two draws and one win; cannot draw C (C no draws), so B draws both A and D. Then A has its only draw used, D its only draw used. Remaining decisive: A beats C,D; B beats C; C beats D. Unique.

[[conclusion]]Let's final.
