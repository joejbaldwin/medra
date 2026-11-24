---
trace: en-mat-square
annotator: Laith
drafted_by: Claude (AI assistant), to be corrected
status: corrected
concepts: [perfect square, factor pair, prime, positive integer, parity, expression]
topics:
- [factor, prime, divisor, product, pair]
- [square, expression]
- [parity, odd]
---
[[planning]]We need answer. Need solve both. Need find positive integers n such that expression square, prove exhaustive.

[[development]]Let x^2 = n^2 + 2n + 12 = (n+1)^2 + 11. Let m = n+1 positive >=2. Then m^2 + 11 = x^2. So x^2 - m^2 = 11 => (x-m)(x+m)=11. Positive factors. Since 11 prime. x>m positive. Factor pairs (1,11) or? x-m and x+m positive integers same parity. Product 11 odd -> both odd. Let x-m=1, x+m=11 => x=6,m=5. n=m-1=4. Check 16+8+12=36. If negative factor? x+m positive, x-m could? x^2 > m^2 so x>m for positive? Expression bigger than m^2? m^2+11, x positive; x>m. so positive. only n=4. Nice.

[[development]]Second: n^2+6n+50. Complete square (n+3)^2 +41? n^2+6n=(n+3)^2-9, +50 = (n+3)^2+41. Need square. Let m=n+3 >=4. x^2 = m^2+41. Then (x-m)(x+m)=41 prime. Solutions x-m=1, x+m=41 => x=21,m=20 => n=17. Check 289+102+50=441=21^2. But wait also factor pair? 41 prime, positive. Same parity both odd. Only. However need be careful n positive integer, m>=4. Solution m=20 -> n=17. Is there any other factor pair (41,1) yields x-m=41, x+m=1 impossible. Could x-m negative? no.

[[verification]]But wait the problem asks "Then do the same for n^2+6n+50." Seems simple. But perhaps there are multiple? Let's check if m could be? x^2 - m^2 = 41. Since 41 prime, yes only n=17. But maybe if considering x-m and x+m negative? x positive can choose x nonnegative. Fine.

[[conclusion]]Need craft final with proof no others. Need mention perfect square integer square. Positive n. Could present both. Need maybe address x nonnegative. For expression positive, if y^2 equals it, take y positive. Then y>n+1 for first; factor.

[[verification]]But wait first expression: n^2+2n+12 = (n+1)^2+11. If y^2 = ..., then y^2 - (n+1)^2=11. Factors (y-(n+1))(y+(n+1))=11. Need note y>n+1 since y^2 bigger than (n+1)^2. Both positive factors. Since product 11, smaller positive divisor 1. Then y-(n+1)=1 and y+(n+1)=11. Solve n+1=5 n=4. Done.

[[verification]]Second similarly y^2=(n+3)^2+41. y>n+3. Difference factors =41. Only y-(n+3)=1, y+(n+3)=41. Solve n+3=20 n=17. Good.

[[verification]]Need perhaps mention factorization of primes. Since 11 and 41 primes. If product equals p, positive factors 1,p. Same parity automatic? For p odd, x,m parity? If product odd, factors odd. Equations solve.

[[conclusion]]Need maybe final answer no others. Desired oververbosity 5, keep concise. The prompt says "Then do the same" perhaps wants both fully proven. We can structure.

Let's draft final.
