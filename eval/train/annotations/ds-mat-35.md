---
trace: ds-mat-35
annotator: Codex (AI)
status: corrected
concepts: []
topics: []
---
[[planning]]We need answer. Need parse problem. Nine sorted nonnegative integers. Median 8. "Using the median of each four-item half after excluding the centre, its quartiles are 4 and 12." Means for 9 data, sorted x1<=...<=x9, median x5=8. Lower quartile = median of lower four excluding center: for 4 items, median? Typically median of 4 data is average of middle two? But says quartiles are 4 and 12 integers. Need interpret. "Using the median of each four-item half after excluding the centre" Could mean quartile is median of each four-item half. For four items, median could be average of 2nd and 3rd. Since integers and median? [[development]]lower half x1..x4 has median (x2+x3)/2 = 4. Upper half x6..x9 median (x7+x8)/2=12. Need verify. Or could mean median of four-item half after excluding centre maybe "the median" with four numbers convention median is average of middle two. Need solve.

Need maximize mean = sum/9. [[development]]Conditions nonnegative integers sorted:
x1<=x2<=x3<=x4<=x5=8<=x6<=x7<=x8<=x9=15? maximum =15, so x9=15. Need quartiles:
(x2+x3)/2 = 4 => x2+x3=8, with x1<=x2<=x3<=x4<=8. Since nonnegative.
(x7+x8)/2=12 => x7+x8=24, with 8<=x6<=x7<=x8<=15.
We want maximize sum x1+...+x9. Since variables constrained monotone and quartile sums fixed. Maximize x1? Actually lower half: x2+x3 fixed 8, x1 <= x2, x4 <=8 and >=x3. Upper: x7+x8=24, x6<=x7, x9=15. To maximize total, for lower half maximize x1+x4 given x2+x3=8 and sorted x1<=x2<=x3<=x4<=8. Since x2+x3 fixed, lower sum = x1 + (x2+x3)+x4 = x1+8+x4. Max x1 as high as x2, max x4 as high as 8, but x2+x3=8 and x2<=x3. Need choose x2,x3 to allow high x1 and x4. x4 max independent <=8 and >=x3, can set x4=8. x1 max = x2. Need maximize x2 subject x2<=x3, x2+x3=8 => x2<=4. Max x2=4, then x3=4. Then x1 max 4. Sequence x1=4,x2=4,x3=4,x4=8. Lower sum=4+4+4+8=20 (plus x5 8).
[[development]]Upper: x7+x8=24, x7<=x8<=15, x6<=x7. Want total x6+x7+x8+x9 = x6+24+15 max. Set x9=15, x8? Equation x8=24-x7 <=15 => x7>=9. Sorted x6<=x7. We want max x6 given x7? x6 <= x7; and also x6>=x5=8. To maximize x6, choose x7 maybe? x6 can equal x7. Need x7>=9, x8=24-x7. Also x7<=x8 => x7<=12. Maximize x6 with x6<=x7, x6>=8, and x7 between 9 and12. x6 max = x7, so maximize x7 subject x7<=12 and x8=24-x7 with x7<=x8 and x8<=15 (upper). x7 max=12, then x8=12, x6=12. But sorted: 8<=x6=12<=x7=12<=x8=12<=15. upper sum=12+12+12+15=51. [[conclusion]]Total sum = lower 20 + median8 + upper51 =79. Mean 79/9 = 8.777... [[verification]]Sequence [4,4,4,8,8,12,12,12,15]? Check lower half x1..x4 median (4+4)/2=4. Upper x6..x9 = 12,12,12,15 median (12+12)/2=12. Max 15. Sum 4+4+4+8+8+12+12+12+15 =79. Is this max? Need rigorous.

[[alternative]]But maybe quartile convention could be median of four-item half as the 2.5 item? In school sometimes lower quartile for n=9 is 3rd value, upper is 7th value. "Using the median of each four-item half after excluding the centre" Could mean take median of lower half (which has four items) perhaps average of two middle. They explicitly say after excluding centre. For 9 sorted, lower half is first four. Median of four item set can be ambiguous. Many contest problems may define median of even number as average of middle two. Then quartiles 4,12. However if lower quartile is x3? Let's parse.

"Using the median of each four-item half after excluding the centre, its quartiles are 4 and 12." In some textbooks, to find quartiles: median of whole; lower quartile is median of lower half (excluding median if odd). The lower half has 4 items. To find median of four items, average middle two. So yes.

[[planning]]Need "Find largest possible mean and give list achieving it. Show why no higher value works." Need present proof.

Need be careful: nonnegative integers and sorted list, median 8 means fifth=8. Maximum=15 means ninth=15? If sorted, max 15 yes x9=15.

[[verification]]Let list a1<=...<=a9.

Quartiles:
(a2+a3)/2 =4 -> a2+a3=8.
(a7+a8)/2=12 -> a7+a8=24.
Median a5=8.
Max a9=15.
Need maximize sum. We can use monotonic inequalities.

Lower bound:
a1 <= a2, and a4 <=8. Lower four sum a1+a2+a3+a4 = a1+(a2+a3)+a4 <= a2+8+8 = a2+16. Since a2+a3=8 and a2<=a3, 2a2<=8 -> a2<=4. Therefore lower four sum <=4+16=20. Equality when a1=a2=4, a2+a3=8=>a3=4, a4=8. Good. Alternatively if a4 max 8, a1 max a2 max4.

Centre a5=8.

Upper: a6+... sum = a6+(a7+a8)+a9 = a6+24+15 = a6+39. Need bound a6 <=? a6<=a7 and a7+a8=24, a7<=a8<=15. Since a8=24-a7 <=15 => a7>=9. Also a7<=a8 -> a7<=12. Since a6<=a7, a6<=12. Thus upper sum <=12+39=51. Equality when a6=a7=12 and then a8=12. Wait equality a6=12, a7=12 possible, a8=12, a7+a8=24. Yes. But if a6<=a7 and max a7=12. So upper sum <=51.

[[conclusion]]Total <=20+8+51=79. Mean<=79/9.

List achieves [4,4,4,8,8,12,12,12,15]. Verify sorted and conditions. Sum 79.

Need address "largest possible mean" maybe mean is 79/9. Could also be decimal 8 7/9.

Need show no higher. Fine.

[[alternative]]Potential issue: if quartiles defined as x3=4 and x7=12? Let's explore alternate in case. The wording "Using the median of each four-item half after excluding the centre, its quartiles are 4 and 12." If lower half four items, its median could be average. If they instead use "median of four-item half" maybe in some contest, median of even number is the average, so yes. If not, x3=4 and x7=12? Let's solve alternate to see possible answer, maybe not matching expected? [[development]]With x3=4 and x7=12, sorted 9, median 8, max15. Max sum: x1<=x2<=4 -> maximize x1,x2? Wait x3=4. To max lower: x1,x2 can be 4 each? sorted x1<=x2<=4, max sum x1+x2+x3+x4 with x4<=8 and >=4; set x1=x2=4, x4=8. Lower sum=4+4+4+8=20 same. Upper with x7=12: x6<=12, x8>=12, x9=15, max x6=12, x8=15? sorted x7=12<=x8<=x9=15, maximize x8=15, x9=15. Upper = x6(12)+12+15+15=54. total 20+8+54=82, mean 82/9. List [4,4,4,8,8,12,12,15,15]? Wait max 15, x9=15 and x8=15. [[verification]]But quartile upper median of four x6..x9 = (x7+x8)/2=(12+15)/2=13.5 not 12. If convention uses x7 as Q3, then yes. [[conclusion]]But problem says quartiles are 4 and 12, and "Using the median of each four-item half" strongly indicates average middle. For upper four half x6..x9, median is average x7+x8, so condition x7+x8=24. Then [.., 12,12,12,15] yes. If convention for quartiles "median of each four-item half" maybe for even number, median is average. We'll use.

Let's think if any hidden nuance: "A sorted list of nine nonnegative integers has median 8. Using the median of each four-item half after excluding the centre, its quartiles are 4 and 12." Maybe "using median of each four-item half after excluding center" could mean Q1 and Q3 are medians of the two halves. For four-item half, median is average. Yes.

Need formulate answer concise but with proof.

[[verification]]Need perhaps mention integer condition used? Conditions x2+x3=8 and x7+x8=24 derive because quartiles are integer? Actually if average equals 4, sum=8 integer anyway. We need x_i integers for sum? The max equality has integers. For upper bound used sums. We didn't use integer much except parity? If x2+x3=8, a2<=a3 and integers nonnegative: a2<=4 (could be 3.5 if real? a2<=4 anyway). Upper a7 between 9 and12 by a8<=15 and a7<=a8. If real, max a6 <= a7; maximize a7 subject a7+a8=24, a7<=a8, a8<=15 -> a7<=12 and a7>=9; max a6 = a7 max=12. No issue. Equality requires integers list. Fine.

[[conclusion]]Let's produce final answer. Use variables x_i.

Need "give list achieving it" and "show why no higher value works". We'll provide.

[[verification]]Double-check sum: 4+4+4=12, +8=20, +8=28, +12=40, +12=52, +12=64, +15=79. Mean = 79/9.

Could maximum mean maybe mean is sum/9. "largest possible mean" answer 79/9.

[[conclusion]]Let's craft final:

Let sorted list be x1≤...≤x9.

Median x5=8. Max x9=15.

Lower quartile: (x2+x3)/2=4 => x2+x3=8. Since x1≤x2≤x3 and nonneg/sorted, x2≤4. Then sum first four:
x1+x2+x3+x4 ≤ x2+8+8 ≤ 4+16=20. More explicit x1≤x2, x4≤x5=8, x2≤4. Equality conditions x1=x2=4, x3=4, x4=8.

Actually x4≤x5=8. yes.

Upper quartile: (x7+x8)/2=12 => x7+x8=24. Since x7≤x8 and x9=15? [[backtrack]]Wait x8≤x9=15, so x8≤15. Since x7+x8=24, x7=24-x8 ≥9. Also x7≤x8 -> x7≤12. And x6≤x7≤12, so x6≤12. Then sum last four:
x6+x7+x8+x9 = x6+24+15 ≤12+39=51. Equality x6=12, x7=12, x8=12 (x7≤12 equality and sum). Wait from x7≤12; to have x6=12 and x7? Product equality x6=12 and x7=12. Then x8=12.

[[conclusion]]Total sum ≤20+8+51=79. Mean≤79/9.

List as above. [[verification]]Verify quartiles:
lower four [4,4,4,8] median (4+4)/2=4
upper four [12,12,12,15] median (12+12)/2=12
median whole 8, max 15. Sum 79.

One minor detail: In lower half, x4 ≤ x5 =8 yes. Equality lower bound x4=8. To achieve x2≤4 equality x2=4, x3=4, x1=4. yes.

Upper equality: x7≤x8 and x8≤15; equation x7+x8=24. We said x7≤12. Actually x6≤x7≤12 and total upper = x6+39, maximize x6. To get x6=12 need x7≥12. Since x7≤12, x7=12, x8=12. Equality. Good.

[[conclusion]]Final answer with boxed.
