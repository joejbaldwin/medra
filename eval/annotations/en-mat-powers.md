---
trace: en-mat-powers
annotator: Laith
drafted_by: Claude (AI assistant), to be corrected
status: draft
concepts: [last two digits, period, exponent, CRT, Euler theorem, mod]
topics:
- [period, exponent, power, last two digits]
- [Euler theorem, phi, Carmichael, lambda]
---
[[planning]]We need answer. Need solve. Need be careful "last two digits" mod100. Compute 7^2026 mod100, 3^2026 mod100. Check each answer with second method. Need present methods.

Let's compute. [[development]]For 7 mod100. Since gcd, Carmichael? phi100=40, lambda=20? For 7, 7^4=2401 ≡1 mod100? 2401 mod100=1 yes. So period divides 4. 2026 mod4 = 2. 7^2=49. So 7^2026 ≡49 mod100. [[verification]]Second method CRT mod4 and mod25. Mod4 7≡-1, even exp =>1. Mod25: phi20, 2026 mod20=6. 7^6 mod25. 7^2=49≡-1 mod25? 49 ≡ -1 yes. 7^6=(7^2)^3 ≡(-1)^3=-1≡24 mod25. Need x≡1 mod4, x≡24 mod25. 24 mod4=0, add25k: 24+25k ≡ 0 + k (since25≡1) mod4 need ≡1 => k≡1 mod4. k=1 gives 49 mod100. Good.

[[development]]3^2026 mod100. Period? 3^1=3,3^2=9,3^3=27,3^4=81,3^5=43,3^6=29,3^7=87,3^8=61,3^9=83,3^10=49,3^11=47,3^12=41,3^13=23,3^14=69,3^15=7,3^16=21,3^17=63,3^18=89,3^19=67,3^20=1. Period 20. 2026 mod20=6. 3^6=729 =>29 mod100. So answer 29. [[verification]]Second method CRT. Mod4: 3≡-1, even exponent =>1. Mod25: phi20, 2026 mod20=6. 3^6 mod25 =729; 25*29=725 remainder4. Need x≡1 mod4, x≡4 mod25. x=4+25k; mod4: 0 +1*k need1 => k≡1 mod4. k=1 ->29. Or direct repeated squares.

[[planning]]Need answer maybe mention exponent 2026 even. Need explain check each with second method. User asks "What are last two digits ... Then find ... Check each answer with a second method." Could be wanting both. Need maybe include two methods for each.

Need be aware "last two digits" include leading zero if any, but not relevant.

Let's craft with concise but enough detail. Could mention mod 100.

Let's produce final answer. Need no overcomplication. Maybe table? 

[[conclusion]]Method 1: period property.
For 7: 7^4≡1 mod100, 2026 ≡2 mod4 => 7^2026≡7^2=49.
For 3: 3^20≡1 mod100 (or calculate), 2026≡6 mod20 =>3^6=729≡29.

[[verification]]Check with CRT:
7^2026:
mod4 = (-1)^2026=1.
mod25: φ(25)=20, exponent mod20=6. 7^2≡-1, so 7^6≡(-1)^3=-1≡24 mod25.
Solve x≡1 mod4, x≡24 mod25. numbers 24,49,...; 49≡1 mod4, so x≡49 mod100.

3^2026:
mod4 = (-1)^2026=1.
mod25: 2026≡6 mod20, 3^6=729≡4 mod25.
x≡1 mod4, x≡4 mod25. x=4+25k. mod4: 4+25k≡k mod4, need k≡1 mod4. k=1 gives29. x≡29 mod100.

[[verification]]Need note 3^20≡1 mod100 maybe shown by direct? 3^10=59049≡49, square? 3^20 ≡49^2=2401≡1. Or Euler phi? phi100=40 not enough? Actually 3^20 mod100=1 due lambda? Need check. We can state computed: 3^4=81, 3^8=61, 3^16=21, multiply 3^4*3^16? Hmm easier find 3^20: 3^10=59049 ≡49; 3^20 ≡49^2=2401≡1. Good.

[[alternative]]Could use Euler theorem: since gcd(3,100)=1, φ(100)=40, so 3^40≡1; not period 20. Need reduce exponent mod40: 2026 mod40 = 26, then 3^26? We can compute perhaps. But period 20. Need support 3^20≡1. Or use CRT method as check.

[[planning]]For first method 3: direct modular exponent via 3^10 ≡49; 3^20≡1; then exponent 6. Include.

Potential alternative: use Chinese remainder as second. Good.

[[conclusion]]Need final with boxed results.
