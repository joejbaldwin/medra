---
trace: en-mat-dice
annotator: Laith
drafted_by: Claude (AI assistant), to be corrected
status: draft
concepts: [probability, dice, outcome, nonnegative solution, generating function, inclusion-exclusion, permutation,
  triple]
topics:
- [probability, outcome, sum]
- [solution, variable, coefficient, generating function]
- [triple, permutation, partition, combination]
---
[[planning]]We need answer. Need solve and check two ways. Need be careful. Probability sum exactly 10 for 3d6. Total outcomes 6^3=216. Count ordered triples (a,b,c in 1..6) sum 10.

[[development]]Let xi=a-1 etc nonnegative 0..5, sum xi=7. Count nonnegative solutions sum7 minus those with xi>=6. Without upper: C(7+3-1,2)=C(9,2)=36. Invalid: one xi>=6, set yi=xi-6 sum=1 -> C(1+3-1,2)=C(3,2)=3 per variable, three variables =9? Need check overlaps none since sum 7 can't have two >=6? two min 12 >7. Count 27. Probability 27/216 =1/8.

[[verification]]Need check two ways. Way1 generating functions: coefficient of x^10 in (x+x^2+...+x^6)^3. Equivalent coefficient x^7 in (1+x+...+x^5)^3 = ((1-x^6)/(1-x))^3. coefficient x^7 in (1-x^6)^3 (1-x)^-3. Coefficient x^7 of (1-x)^-3 minus 3 coeff x^1 of (1-x)^-3? Let's compute: (1 -3x^6+...)* sum C(n+2,2)x^n. x7 coefficient = C(9,2) -3*C(? for x1 in inverse) wait x^7 term from -3x^6 * coeff x^1 of (1-x)^-3 = -3*C(1+2,2)= -3*3=-9. 36-9=27. Good.

[[planning]]Way2 inclusion-exclusion or perhaps explicit combinations. Need phrase check two different ways. Maybe list dice sum combinations and permutations.

[[verification]]Unordered sums of three positive <=6 equal 10:
1,3,6 permutations 6
1,4,5 permutations 6
2,2,6 permutations 3
2,3,5 permutations 6
2,4,4 permutations 3
3,3,4 permutations 3
Total 27. Wait check also 1,? Let's systematically partitions into 3 parts max6 min1 sum10:
1,3,6 (6)
1,4,5 (6)
2,2,6 (3)
2,3,5 (6)
2,4,4 (3)
3,3,4 (3). total 27. Yes.

[[verification]]Could also complement symmetry? For 3d6 distribution symmetric around 10.5, P(sum=10)=P(sum=11)? Actually possible. Exactly 10 count 27. Sum exactly 10.

[[conclusion]]Need answer maybe mention ordinary fair dice. "Check it in two different ways" means present two methods. We can present first inclusion-exclusion/generating function, second enumeration. Need be concise but explanatory.

Need perhaps verify probability = 27/216=1/8. Let's craft final with two independent checks.

Potential pitfalls: The question asks "Check it in two different ways." So do both, not just one.

[[conclusion]]Let's formulate:

Method 1: Count nonnegative solutions xi=die_i-1, sum xi=7 with 0<=xi<=5. Total nonnegative solutions to x1+x2+x3=7 is C(9,2)=36. Subtract cases xi>=6: for each die set yi=xi-6; equation y1+...+y3=1; count C(3,2)=3 per die? [[verification]]Wait let's recalc carefully! If xi>=6 for a specific i, set xi'=xi-6. Sum xi' = 7-6 =1 over 3 variables. Number nonnegative solutions to sum 1 over 3 variables: C(1+3-1,3-1)=C(3,2)=3. There are 3 choices for variable =9. No double overlap. Count=36-9=27. Probability 27/216=1/8. This is inclusion-exclusion/generating maybe.

[[conclusion]]Method 2: Enumerate unordered triples:
(1,3,6):6 perms
(1,4,5):6
(2,2,6):3
(2,3,5):6
(2,4,4):3
(3,3,4):3
Total 6+6+3+6+3+3=27. Probability same.

[[verification]]Need maybe avoid "check" with same counting? It's okay.

[[conclusion]]Let's answer final with both.
