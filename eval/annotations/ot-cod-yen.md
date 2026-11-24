---
trace: ot-cod-yen
annotator: Kostya
drafted_by: Claude (AI assistant), to be corrected
status: corrected
concepts: [1000-yen bill, change, multiple of 1000, ceiling, floor division, modulo, formula]
topics:
- [bill, yen, change, paid]
- [ceiling, floor division, multiple, remainder]
- [modulo, formula, approach]
- [code, input, test, sample]
---
[[planning]]Okay, I need to solve this problem where I have to calculate the change when paying with 1000-yen bills. Let's see. The problem says that we pay using only 1000-yen bills and use the minimum number of bills. So the total amount paid would be the smallest multiple of 1000 that is equal to or greater than N. Then subtract N from that to get the change.

[[verification]]Wait, right. For example, if N is 1900, then the next multiple of 1000 after 1900 is 2000. So the change is 2000 - 1900 = 100. Which matches the sample output.

[[planning]]So the steps are: find the smallest number of 1000-yen bills such that their total is at least N. Then compute the change as (total paid) - N.

[[development]]But how do I calculate that total paid?

Hmm. Let's think. For any N, the minimum number of 1000-yen bills is the ceiling of N divided by 1000. Because if N is exactly divisible by 1000, you use N/1000 bills. Otherwise, you use (N//1000 + 1) bills.

Wait, for example, N=1000: 1000/1000 =1, so 1 bill. Change is 0.

If N=500, then 1 bill (500//1000 is 0, so 0+1=1). Then 1000-500=500 change.

So the formula for total paid is (ceil(N / 1000)) * 1000. Then subtract N to get change.

[[development]]But how to compute ceil(N / 1000) in Python.

Wait, in Python, when dividing integers, you can use the floor division. So for example, 1900 // 1000 is 1. But ceil(1900/1000) is 2. So how?

[[alternative]]Alternatively, for any N, the minimal multiple is ((N + 999) // 1000) * 1000. Because adding 999 ensures that any remainder will round up. Let's see:

For N=1900: 1900 +999= 2899. 2899//1000 is 2. Multiply by 1000 gives 2000. Which is correct.

For N=1000: 1000+999=1999, divided by 1000 is 1. 1*1000=1000. Correct.

For N=999: 999+999=1998, divided by 1000 is 1. 1000 -999=1. Correct.

So this formula works. Then the change is ((N + 999) // 1000) * 1000 - N.

Alternatively, another approach is to compute how many bills. The number of bills is (N + 999) // 1000. Then multiply by 1000 to get total paid.

So the calculation can be written as ( (N + 999) // 1000 ) * 1000 - N.

Yes. [[planning]]So the steps for the code:

Read N from input.

Compute the total paid as the next multiple of 1000 after N. Then subtract N.

So code steps:

Read N as integer.

Compute change = ( (N // 1000) + 1 ) * 1000 - N if N is not divisible by 1000. Otherwise, 0.

Wait, but that's more complicated. The previous formula of (N +999) // 1000 *1000 -N seems easier.

[[development]]So, code:

n = int(input())
change = ((n + 999) // 1000) * 1000 - n
print(change)

[[verification]]Wait, let's test with sample input. 1900.

1900 +999=2899. 2899//1000 is 2. 2*1000=2000. 2000-1900=100. Correct.

Another test case: N=1000. 1000+999=1999, 1999//1000=1. 1*1000=1000. 1000-1000=0. Correct.

N=500: 500+999=1499 →1 →1000 →1000-500=500. Correct.

N=999: (999+999)=1998 →1 →1000 →1 change. Wait, 1000-999=1. Correct.

So the formula works.

[[alternative]]So the code is straightforward.

So the function would read N from input, compute this value, and print it.

So the Python code would be:

n = int(input())
print( (1000 - (n % 1000)) % 1000 )

Wait, wait, another approach. Because the required total is the next multiple of 1000. So if the remainder is r when divided by 1000, then the required total is (n + (1000 - r)) % 1000? Wait, no. Let's think.

If n mod 1000 is r, then if r is zero, the next multiple is n, so change is 0. Otherwise, the next multiple is n + (1000 - r). So change is 1000 - r.

But wait, 1000 - r. For example, n=1900: 1900 mod 1000 is 900. 1000-900=100. Which is correct.

n=500: 500 mod 1000 is 500. 1000-500=500.

n=999: mod 1000 is 999. 1000-999=1.

n=1000: mod 1000 is 0. 1000-0=0.

So the change is (1000 - (n % 1000)) % 1000.

Wait, but when n is a multiple of 1000, n mod 1000 is 0. So 1000 -0 is 1000. Then mod 1000 gives 0. So in that case, yes.

So the formula is (1000 - (n % 1000)) % 1000.

[[development]]So code can also be written as:

n = int(input())
print( (1000 - (n % 1000)) % 1000 )

[[verification]]Let's test this.

Sample input 1900: 1900 mod 1000 is 900. 1000-900=100. mod 1000 is 100. Correct.

n=1000: 1000 mod 1000=0. 1000-0=1000. 1000 mod 1000=0. Correct.

n=500: 500 mod 1000=500. 1000-500=500. mod 1000 is 500. Correct.

n=999: 999 mod 1000=999. 1000-999=1. mod 1000 is 1. Correct.

So yes, this formula works as well.

[[conclusion]]So which approach is better? Both are correct. Both give the same result.

So in code, either approach can be used. But the second approach might be more efficient, as it's a simple modulo operation.

So the code could be either way.

But the first approach uses integer division, but adding 999. Either way, the code is simple.

So the code can be written as:

n = int(input())
print( (1000 - (n % 1000)) % 1000 )

Which is concise.

[[verification]]But why the modulo 1000 at the end? Because if n is a multiple of 1000, then 1000 - (n%1000) is 1000, and modulo 1000 gives 0. So that's necessary.

Yes.

So this code should handle all cases.

[[conclusion]]Thus, the solution is to compute (1000 - (n mod 1000)) mod 1000.

Hence, the Python code is as above.
