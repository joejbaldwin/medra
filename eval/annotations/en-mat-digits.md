---
trace: en-mat-digits
annotator: Kostya
drafted_by: Claude (AI assistant), to be corrected
status: draft
concepts: [four-digit number, digit, digit sum, first digit, inclusion-exclusion, nonnegative solution, upper bound,
  generating function]
topics:
- [digit, first digit, leading zero, four-digit number]
- [solution, variable, upper bound, violation]
- [case, table, sum]
---
[[planning]]We need answer. Need solve combinatorics. Need interpret four-digit numbers: first digit 1-9, other digits 0-9, sum digits 12. Count. Need two different ways and check agree. Need be careful leading zeros excluded. Let's compute.

Count nonnegative integer solutions d1+d2+d3+d4=12 with d1>=1, d2-d4 between 0 and9, d1<=9. Since sum 12, d1<=9 redundant? d1>=1 and sum12 means d1<=12 but digit max9 so need subtract d1>=10. Other digits <=9; sum 12 so at most one digit could be >=10, but among d2-d4, can be 10,11,12, need exclude. Also d1 max.

[[development]]Method 1 inclusion-exclusion using positive first.

Let x1 = d1-1 >=0. Then x1+d2+d3+d4=11. Count nonnegative solutions minus violations xi/d? Actually variables y1=x1 for first digit minus1, y2..y4 = other digits. y1<=8, others<=9. Sum 11. Unrestricted C(14,3)=364. Exclude y1>=9: set z1=y1-9 sum 2 -> C(5,3)=10. Exclude any other y_i>=10: set y_i' = y_i-10 sum 1 among 4 vars -> C(4,3)=4 each *3=12. Cannot have two violations? Sum 11: y1>=9 and other>=10 sum>=19 no; two other>=10 sum>=20. Intersections zero. Count 364-10-12=342. Wait subtract y1 violation 10 and others 12 gives 342.

[[verification]]Check via unrestricted d1 positive no max and subtract leading digit >9 and other >9. Nonnegative with d1>=1: x1+d2+d3+d4=11 C14,3=364. subtract d1>=10: let d1'=d1-10? Wait d1 positive sum12, violation d1>=10 (since digit max 9) i.e. d1=10,11,12. Using x1=d1-1 >=9. Number y1>=9 and total y sum 11: let y1'=y1-9, sum remaining total 2 among 4 vars? Variables y1,d2,d3,d4, y1' + d2+d3+d4 =2. Count C(5,3)=10. This corresponds d1>=10. Others digit >9: d2>=10, sum 12, d1>=1, remaining after d2=10: d1+d3+d4=2 with d1>=1. Count solutions a+d3+d4=1 after d1-1? Let's calculate: d1>=1, d3,d4>=0, d1+d3+d4=2. Set d1'=d1-1: d1'+d3+d4=1 C(3,2)=3 for each of 3 other positions =9, not 12. [[backtrack]]Wait conflict with earlier? Let's re-evaluate.

Earlier using x1=d1-1 sum x1+d2+d3+d4=11. Other digit d2<=9; violation d2>=10. Set d2'=d2-10, then x1+d2'+d3+d4 =1. Variables 4 nonnegative, count C(1+4-1,3)=C(4,3)=4. Wait why discrepancy? Because y variables sum 11, d2>=10 leaves remaining sum 1, count C(1+3? Actually variables x1,d2',d3,d4 = 4 variables sum 1 -> C(4,3)=4. But direct d1>=1, d2=10+k, d3,d4 nonneg sum: d1+(10+k)+d3+d4=12 => d1+k+d3+d4=2, d1>=1. Set d1'=d1-1, then d1'+k+d3+d4=1. 4 variables sum 1 -> 4 solutions. Why previously I set after d2=10: d1+d3+d4=2 yes set d1' d1-1 => d1'+d3+d4=1, count 3? There are variables d1', d3,d4 = 3 variables sum1 => C(3,? C(1+3-1,3-1)=C3,2=3). Wait d2 can be 10 or 11? d2=10+k; equation d1+k+d3+d4=2. I omitted k. Full variables d1', k, d3,d4 sum 1? Let's derive: d1=1+a, d2=10+b. Sum: 1+a+10+b+d3+d4=12 => a+b+d3+d4=1. Four variables ->4. Correct. Direct from sum d1+d3+d4=2 when d2=10, but d2 can 11 too. If d2=10: d1+d3+d4=2 with d1>=1 gives 3 solutions. If d2=11: d1+d3+d4=1 with d1>=1 gives 1 solution. Total4. Good.

[[planning]]So count 342. Need second method.

Could use generating functions coefficient: (x+x^2+...+x^9)(1+x+...+x^9)^3 coefficient x^12. Compute maybe via total positive and inclusion-exclusion or complementary.

Alternative second method: Count all nonnegative digit quadruples summing 12 with first digit 0-9 etc, then subtract those with first digit 0? Hmm.

[[verification]]Method 2: Count four-digit numbers with digit sum12 by cases on first digit d. For d=1..9, count ordered triples nonnegative <=9 summing 12-d. Since 12-d <=11, for d>=3 sum<=9, no upper bound needed. For d=1,2 need handle. Let's calculate.

For first digit a.

a=9: b+c+d=3: C(5,2)=10.
a=8: sum4: C(6,2)=15.
a=7: sum5: C(7,2)=21.
a=6: sum6: C(8,2)=28.
a=5: sum7: C(9,2)=36.
a=4: sum8: C(10,2)=45.
a=3: sum9: C(11,2)=55.
a=2: sum10 for last 3 digits each <=9. Unrestricted C(12,2)=66 minus any variable>=10. If one >=10, set subtract10, sum0 among 3, number 3* C(2,2)? Let's compute: For b>=10, b'=b-10, b'+c+d=0 ->1 solution. 3 variables =>3. No double. Count 66-3=63.
a=1: sum11 for last3 <=9. Unrestricted C(13,2)=78. Subtract variable>=10: let b'=b-10, sum=1 among 3 variables: C(1+3-1,2)=C3,2=3 per variable *3=9. No double. Count 78-9=69.
[[verification]]Sum: for a=9 down3: 10+15+21+28+36+45+55 =? 10+15=25+21=46+28=74? Wait 25+21=46 yes +28=74? No 46+28=74? Oops 46+28=74 yes? Actually 46+28=74? Wait 46+28=74 indeed? 46+30=76-2=74. That's wrong? 46+28 = 74? 40+20=60; 6+8=14 total 74. yes. +36=110. +45=155? Wait 110+45=155 yes. +55=210. Then plus a=2 63 plus a=1 69 => 342. Check sum sequence: a=9 to3 terms: 10,15,21,28,36,45,55. Sum: 10+15=25; +21=46; +28=74; +36=110; +45=155; +55=210. +63=273; +69=342. Good.

[[conclusion]]Need present two methods. Could choose generating functions as second. Need answer. Need perhaps mention digits sum exactly 12. Need "four-digit numbers" no leading zero. Let's formulate.

Need ensure not too verbose. Provide two methods and check.

Potential issue: "four-digit numbers have digits that add up to 12" could include number 100? No four-digit. Leading digit nonzero. Good.

[[conclusion]]Method 1 inclusion-exclusion detail. Define digits a,b,c,d with a in 1..9, b,c,d in 0..9. Let x=a-1. Then x+b+c+d=11 with x,b,c,d>=0, x<=8, b,c,d<=9. Without upper bounds C(14,3)=364. Subtract x>=9: set x'=x-9, x'+b+c+d=2 -> C(5,3)=10. Subtract b>=10 (or c/d): set b'=b-10, x+b'+c+d=1 -> C(4,3)=4 for each of b,c,d, total 12. No overlap. Count 364-10-12=342. Need ensure upper bounds: x<=8 because a<=9, and b,c,d<=9. Good.

[[conclusion]]Method 2 case first digit. Could show table perhaps concise. For a=1..9, count triples sum 12-a. Need include values. Use table with a and count. We must present in final. Maybe table.

Let's consider if there is more elegant second method with generating functions. But case table is okay. Need "Solve in two different ways and check answers agree." We can show sum =342.

Let's craft final with formula for a=1,2 using inclusion-exclusion. For a≥3, sum ≤9, count C(12-a+2,2)=C(14-a,2). Wait check a=3 sum=9, number nonnegative triples = C(9+2,2)=C11,2=55. Formula C(14-a,2): C11,2 yes. a=9 C5,2=10. For a=1,2 need subtract. Table. The sum for a=3..9: use formula. a=1: last digits sum 11: C(13,2)-3*C? Let's detail. If one of b,c,d≥10, set subtract 10, remaining sum 1 among 3 variables, number C(1+2,2)=3 each, total9. Count78-9=69. For a=2: sum10: C(12,2)=66 minus 3*1=63. For a≥3 no upper bound violations because sum≤9. Sum a=3 to9 C(14-a,2) = for a=3..9 gives C11,2 + C10,2 + ... C5,2. Wait C(14-a,2) a=3 => C11,2; a=9=>C5,2. Sum = C? 55+45+36+28+21+15+10 =210. Include a=1 69, a=2 63 total 342. Need be careful display not confuse.

[[alternative]]Alternative second method use generating function coefficient maybe shorter:
Coefficient of x^12 in (x+x^2+...+x^9)(1+x+...+x^9)^3. Evaluate. Coefficient = [x^11](1-x^9)/(1-x) * ((1-x^10)/(1-x))^3? Actually (x(1-x^9)/(1-x))*((1-x^10)/(1-x))^3. Need coefficient. Could compute via inclusion-exclusion same as method 1, not different enough. Case table distinct.

[[conclusion]]Let's produce final with both. Desired oververbosity 5; moderate.
