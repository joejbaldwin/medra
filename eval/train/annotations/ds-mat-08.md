---
trace: ds-mat-08
annotator: Codex (AI)
status: corrected
concepts: []
topics: []
---
[[planning]]We need answer. Need parse problem. Exam 12 questions 1 point each. Instructor drops worst two questions. Two readings: (1) "removes two questions for each student" individually drop worst two per student. (2) "another removes the same two globally" drop same two questions for all students. A student answered 8 correctly. Find possible adjusted percentages under each reading and show which global outcomes can occur.

Need be careful ambiguity. We consider one student with 8 correct out 12, and drop worst two questions? [[development]]For individual student, drop two questions they got wrong if possible; if fewer than 2 wrong, drop among correct? "worst" means incorrect presumably, but if student got 8 correct, they got 4 wrong, so drop two wrong -> score 8/10 = 80%. That's straightforward. But possible adjusted percentages? Maybe if "worst two questions" meaning the two questions on which student performed worst; since raw correct/incorrect, any two among wrong. Since 8 correct, 4 wrong, dropping two wrong leaves 8 correct out of 10 = 80%. Only possible under individual. But wording "possible adjusted percentages" maybe asks for range? Need examine.

[[alternative]]Global same two: Instructor removes same two questions globally. A target student answered 8 correctly. Depending which two global questions are dropped and whether student got them correct/wrong, adjusted score numerator among remaining correct = 8 - (# of dropped questions student got correct) (can't exceed? If drops questions correct, student's total correct remaining decreases; if drops wrong, unchanged). Denominator 10. The possible # correct remaining from 6 to 8, i.e. percentages 60%,70%,80%. [[planning]]But global outcomes can occur under what constraints of class? "show which global outcomes can occur" maybe with entire class? Need infer maybe from known puzzle? It might be asking about drop-two-lowest vs fixed questions, "A student answered 8 correctly. Find possible adjusted percentages under each reading and show which global outcomes can occur." Maybe they ask compare individual drop worst two per student vs global drop same two. Need "another removes same two globally." If a student answered 8 correctly, find possible adjusted percentages under each reading and show which global outcomes can occur.

Could be asking: For a given student, with individual drops, possible adjusted percentages? With global drops, possible adjusted percentages and which global choices (drop 0,1,2 questions student got correct) can occur. [[alternative]]However "show which global outcomes can occur" may refer to "globally dropping the two questions with the lowest overall correct counts" can lead to different outcomes? Need parse.

The problem statement: "An exam has 12 questions worth one raw point each. The instructor will "drop the worst two questions". One reading removes two questions for each student; another removes the same two globally. A student answered 8 correctly. Find the possible adjusted percentages under each reading and show which global outcomes can occur."

This likely from an argument about interpreting "drop the worst two questions": Does it mean drop two questions *for each student* or drop two questions *from exam globally*? A student answered 8 correctly. Find possible adjusted percentages under each reading and show which global outcomes can occur. Maybe "global outcomes" means under global drop, how many of the student's 8 correct can be affected. [[development]]If same two globally, depending which two, the student's resulting score may be 8/10, 7/10, or 6/10. Need show feasible given 4 wrong? Since total 8 correct, 4 wrong. To drop two questions:
- if both dropped were wrong for student: 8 correct remain -> 8/10=80%.
- one correct one wrong: 7 correct ->70%.
- two correct: 6 correct ->60%.
All are possible because student has at least 2 correct and at least 2 wrong (yes 8,4).

[[conclusion]]Under individual drop worst: drop two of student's incorrect, score remains 8 correct out of 10 = 80% (if among 4 wrong; assuming no partial). Possible percentages maybe only 80%.

[[alternative]]But need consider "worst two questions" if same globally could be chosen based on class total, and "which global outcomes can occur" may depend on class distribution. The target student's result depends on aggregate class performance. For a global choice to drop a correct answer of this student, the question must be among globally worst two, which could happen if enough others miss it. The problem may want enumerate which pairs of questions can be globally dropped given student has 8 correct? Without class data, any pair of questions? We need "show which global outcomes can occur" perhaps in terms of number correct dropped: 0,1,2 among the student's correct, and all possible. But "global outcomes" maybe asks to show that when globally dropping, the student's percentage can be 80,70,60. Need phrase.

Let's read exact: "An exam has 12 questions worth one raw point each. The instructor will "drop the worst two questions". One reading removes two questions for each student; another removes the same two globally. A student answered 8 correctly. Find the possible adjusted percentages under each reading and show which global outcomes can occur."

[[verification]]Potential issue: Under individual reading, if drop worst two *questions for each student*, for a student with 8 correct, they have 4 wrong, so drop two wrong. Adjusted percentage 8/10=80%. If a student had 11 correct, drop one wrong and one correct? Then 10/10? But not here.

Under global, if same two questions dropped, possible adjusted percentages based on how many of the two dropped were answered correctly by the student. If both were incorrect: 8 correct remains /10=80. If one correct: 7/10=70. If two correct: 6/10=60. [[verification]]Could also if instructor decides worst two globally based on overall class; for this student, if he answered 8 correct, among 4 incorrect and 8 correct. Any pair? If the selected questions are from all 12, any pair can be globally worst under some class distribution while this student's pattern fixed? Need check. For any pair of questions to be the worst globally, can construct other students so those two have lowest correct count, but target student's answers on those questions may be correct or incorrect. Yes likely. If only considering this student's data, all combinations possible because no info on other students. But perhaps there is constraint if the student answered 8 correctly: Can a pair include both correct? Sure. Both wrong? Sure. One each sure.

Question: "show which global outcomes can occur" might mean if the same two questions are dropped globally, the student's adjusted score can be 6,7,8 out of 10. Show each.

[[conclusion]]Let's formulate final answer with assumptions. Include formula. Mention if "worst" means unanswered/incorrect; if there are fewer than two incorrect, etc., but here 4 incorrect.

Need maybe discuss percentages: 80%, 70%, 60%. "Adjusted percentages" perhaps percentages out of 100: 80.00%, 70.00%, 60.00%.

Need "which global outcomes can occur": Under global drop, possible count of dropped questions the student got right k=0,1,2. Then final correct =8-k; total=10; percentage=(8-k)/10*100. All k possible because student has 4 wrong and 8 right, so choose global pair: two wrong -> k=0; one wrong one right -> k=1; two right -> k=2. If global pair is determined by class aggregate, without additional class data any of these can be arranged; with actual class totals, it's whichever pair is globally worst and one checks their answers.

Could include table:
Reading, dropped questions relative to student, remaining correct, adjusted.
Individual: 2 wrong (since 4 wrong) -> 8/10 =80%.
Global:
- 2 wrong -> 8/10=80%
- 1 correct, 1 wrong -> 7/10=70%
- 2 correct -> 6/10=60%.

Need answer "find possible adjusted percentages under each reading". So final concise.

[[verification]]But let's consider if individual reading could be "drop worst two questions for each student" meaning the instructor drops each student's two lowest-scoring questions after considering their own performance? Since questions are binary, yes.

Could there be "worst two" in global reading determined by aggregate performance. For this student answered 8 correctly; possible adjusted percentage under global depends on class. Under some class patterns, the globally worst two could both be questions the student got correct, etc., all possible. But if the global worst two must have the lowest fraction correct across whole class, can we always make the target student's outcomes for those pair as desired. Yes.

[[conclusion]]Let's craft final answer with a note: "Assuming no partial credit and exactly two questions are always dropped, even if they were answered correctly by some students."

Need maybe address if "worst" means lowest raw score for the student; if student has 4 wrong, drop any two. There are C(4,2)=6 choices but same adjusted score.

Let's prepare final. Need not overdo. Include table. Mention global outcomes "k=0,1,2 correct questions removed".

Let's also mention if the global dropped pair is fixed, numerator is original score minus number dropped that the student had correct, over 12-2=10. Thus possible scores:
k=0: 80%
k=1: 70%
k=2: 60%
No other global outcomes. Individual always 80%.

[[verification]]Could there be possibility of 100% if "drop worst two" per student and if student got 8 correct? No. If dropping two questions they got wrong, correct count remains 8 but denominator 10, percentage 80. It actually penalizes? Wait if score is total correct after dropping: The student got 8 correct originally. Dropping questions that they got wrong doesn't increase numerator, removes denominator from 12 to 10. Original 8/12=66.7, adjusted 8/10=80. If they dropped two correct instead, 6/10=60. "Worst" chooses wrong, so 80.

[[alternative]]Potential subtlety: Some grading schemes "drop worst two questions" could give credit for dropped questions? Actually when dropping a question, you remove both earned points and possible points. If a student answered a question correctly and it is dropped, they lose that point. If answered wrong, they don't gain. So individual drop worst (incorrect) indeed leaves correct count unchanged but reduces denominator. This is standard. But sometimes "drop" means set denominator to 10 and ignore those questions; yes.

[[conclusion]]Let's answer.
