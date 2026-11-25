---
trace: ds-mat-22
annotator: Codex (AI)
status: corrected
concepts: []
topics: []
---
[[planning]]We need answer. Need parse problem. "Five paired observations have mean x=3, mean y=4, sum of squared x deviations 10 and sum of cross deviations 15. Add the point (9,4). Find the new least-squares slope and intercept, and check that the fitted line goes through the new mean point."

We need compute updated regression. Need be careful notation sum of cross deviations? likely SP_xy = sum (x_i - xbar)(y_i - ybar) = 15. SS_x = 10. n=5, xbar=3 ybar=4.

Add point (x_new,y_new)=(9,4). New n=6.

Need compute new means, new corrected sums. Formula for combining.

[[development]]Original n1=5, means xbar1=3, ybar1=4.
New point n2=1, x2=9,y2=4.
Combined mean xbar_new = (5*3 +9)/6 = (15+9)/6=24/6=4. ybar_new=(5*4+4)/6=24/6=4. So mean point (4,4).

Need new SS_x and SP_xy.

For combining groups:
SSx_total = SSx1 + SSx2 + n1 n2/(n1+n2) (xbar1-xbar2)^2 if group sizes n1=5,n2=1. [[alternative]]Or easier compute using old centered sum plus shift due to new mean over all observations:
Given old data with sum deviations from old mean: SSx_old=10. The sum squared deviations from new mean for old points? Formula.

[[development]]Compute new Sxx = sum_i=1^6 (x_i - xbar_new)^2.
For old 5: sum (x_i -4)^2 = sum [(x_i-3) -1]^2 = sum (x_i-3)^2 -2 sum(x_i-3)+5*1 =10 -0 +5=15.
New point: (9-4)^2=25.
Total Sxx=40.
[[verification]]Alternatively combine: 10 + (5*1/6)(3-9)^2 =10 + (5/6)*36=10+30=40 yes.

[[development]]New SP? Sxy = sum (x_i-xbar_new)(y_i-ybar_new). ybar_new=4 = old ybar. New point y=4 same as mean, so no effect y. For old points ybar_new = old ybar =4. xbar shift from 3 to4: sum_i old (x_i-4)(y_i-4) = sum [(x_i-3)-1](y_i-4) = sum (x_i-3)(y_i-4) - sum(y_i-4). Old SP =15 = sum (x_i-3)(y_i-4). Sum(y_i-4)=0 (since ybar old 4). So =15. New point: (9-4)(4-4)=0. Total SP=15.
Thus new slope b = SP/Sxx = 15/40 = 3/8 =0.375.

Intercept a = ybar_new - b*xbar_new =4 - (3/8)*4 =4 - 12/8 =4 -1.5=2.5 =5/2. [[conclusion]]Equation yhat = 5/2 + (3/8)x. [[verification]]Check mean point (4,4): yhat=2.5+1.5=4.

[[alternative]]Need maybe clarify "sum of cross deviations" could be sum x_i y_i? But wording "cross deviations" likely ∑(x_i - xbar)(y_i-ybar). Could be "sum of cross deviations" = SP_xy. We'll state assuming. Could there be confusion? Let's inspect original: "Five paired observations have mean x=3, mean y=4, sum of squared x deviations 10 and sum of cross deviations 15. Add the point (9,4). Find the new least-squares slope and intercept, and check that the fitted line goes through the new mean point." This is standard regression update. [[conclusion]]Answer as above.

Need perhaps include calculations concise. [[alternative]]Could also derive using direct formulas from original sums.

[[conclusion]]Let's formulate final with n, means. Maybe mention old slope? Old slope =15/10=1.5, old intercept =4-1.5*3=-0.5, but new changes. New means and cross products.

[[verification]]Check: Combined x mean 4, y mean 4. Sxx new = 10 + [5*1/(5+1)](9-3)^2 =10 +(5/6)*36=40. Sxy? Original SP=15. Need group combination for covariance? For Sxy total = SP1 + n1 n2/(n1+n2)(xbar1-xbar2)(ybar1-ybar2). Here ybar difference 0, so total =15+0 =15. Wait is that fully? Yes. But careful formula: Sxy total = Sxy1 + n1 n2/(n1+n2)(xbar1-xbar2)(ybar1-ybar2). Since y equal, =15. New point group has Sxy2=0. Okay.

[[conclusion]]Then b =15/40=3/8. intercept = ybar - b xbar =4 - 3/8*4=4-3/2=5/2.

[[verification]]Fit at xbar_new=4: 5/2 + (3/8)(4)=5/2+3/2=4=ybar. It goes through mean point (4,4).

[[conclusion]]Need perhaps mention slope/intercept in fraction and decimal. Done.
