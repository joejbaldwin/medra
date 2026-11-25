---
trace: ds-sci-12
annotator: Codex (AI)
status: corrected
concepts: []
topics: []
---
[[planning]]We need answer. Need reason. Need parse. Capacitor 6 µF charged to 12 V. Then dielectric doubles capacitance inserted. Case 1 battery disconnected. Case 2 battery connected. Compute stored energy change each, battery work when connected. Account for difference energy balance.

Need clarify initial? A 6 μF capacitor charged to 12 V. Dielectric doubles capacitance. [[development]]Initial capacitance C0=6µF, V0=12, Q0=C0 V0=72µC. U0=1/2 C V^2 = 0.5*6e-6*144=432e-6 J = 432 µJ (or 4.32e-4 J). [[verification]]Alternatively Q^2/2C: (72e-6)^2/(12e-6)=? Q^2=5184e-12, denom 12e-6 =>432e-6.

[[development]]Case disconnected: Q constant. C' = 2C=12 µF. U' = Q^2/(2 C') = 1/2 initial (since C doubles) =216 µJ. Change ΔU = U' - U = -216 µJ (decrease). [[planning]]Work by external agent inserting dielectric? Need perhaps account. If induced polarization draws slab? [[development]]Energy reduces, appears as work done by field on dielectric (mechanical work by capacitor = -ΔU = +216µJ? Need sign). No battery.

[[alternative]]Case connected: V remains 12 V. [[development]]C' =12µF. Q'= C'V=144 µC. U'=1/2 C' V^2 = 1/2*12e-6*144=864 µJ. Initial 432 µJ. ΔU=+432 µJ (increase). Battery moves additional charge ΔQ = Q'-Q=72 µC through potential V. Work done by battery? W_batt = V ΔQ =12*72e-6=864 µJ (positive work by battery on circuit, if current leaves positive? Need sign). [[development]]But energy stored increased by 432 µJ. Where other 432 µJ go? Work done by battery 864 µJ; half increases field energy, half is mechanical work done on dielectric by field (or heat? Actually if dielectric inserted with battery connected, field pulls it in doing mechanical work. Energy balance: W_batt = ΔU + W_mech by capacitor/field on dielectric? [[verification]]Let's derive sign carefully.

Question: "Compute the stored energy change in each case and the battery's work when connected. Account for the difference in the energy balance." Need state battery work = 864 µJ supplied; stored energy increase 432, remaining 432 mechanical work done by field pulling dielectric in (or external agent must remove negative?).

Need be cautious signs. If we calculate battery work maybe W_battery = ΔQ V = +864 µJ. Some texts Q: Work done by battery = VΔQ. Energy supplied = VΔQ. Then energy stored increased by 432. Remaining 432 dissipated/mechanical. But note dielectric insertion with battery connected, if dielectric is drawn into capacitor, the field does mechanical work on dielectric, which if not extracted could become kinetic/heat. Thus "account for difference": extra 432 µJ is work done by electrical system on dielectric (mechanical work) or equivalently external agent would have to do -432 µJ (receive 432) to insert quasistatically? [[alternative]]Let's set thermodynamic energy of capacitor + battery + mechanical.

We can use differential dU = V dQ + F_x dx? For capacitor at voltage source? If inserting dielectric, capacitance increases. Energy supplied by source = V dQ. Change stored = (1/2)V dQ if V const from relation? Actually in our finite step no if C changes from C to 2C while V const, source supplies V ΔQ; ΔU=1/2 V ΔQ. Difference =? The mechanical work done by field on slab = ∫ F dx =? dU at fixed charge etc. [[development]]Let's derive sign.

For a capacitor connected to source, with capacitance C(x), voltage V fixed. Source work dW_s = V dQ = V^2 dC. Stored energy dU = 1/2 V^2 dC. Mechanical work done by electric field? Energy conservation: dW_source = dU + dW_mech_ByField + losses. Thus dW_mech_ByField = V^2 dC - 1/2 V^2 dC = 1/2 V^2 dC. Positive when C increases, so field does positive mechanical work on dielectric (pulls it in). Integrated = 1/2 V^2 ΔC = 0.5*144*(6e-6)=432 µJ. [[conclusion]]Good.

But if considering external agent inserts slowly, field pulls it, external agent must hold back, extracting 432 µJ; or if released, gets kinetic. The "difference" is 432 µJ not stored; it is mechanical work done by the field on the dielectric, equal to half battery energy, or heat if damping.

Need also mention disconnected with dielectric insertion energy decreases by 216 µJ; this is released mechanically because field pulls dielectric in; if quasistatically external agent extracts 216 µJ. Does battery disconnected have no battery work. [[planning]]Need maybe account for "difference" between cases? Let's parse prompt: "A 6 microfarad capacitor is charged to 12 V. A dielectric that doubles its capacitance is inserted, first with the battery disconnected and in a separate experiment with it connected. Compute the stored energy change in each case and the battery's work when connected. Account for the difference in the energy balance."

Could mean compute stored energy change in disconnected and connected, and battery work connected, then account for difference. Need include initial energy, final etc.

[[verification]]Let's verify values:
C0=6e-6 F, V0=12 V, Q0=72e-6 C, U0=0.5*6e-6*144=432e-6 J.
Disconnected:
C1=12e-6 F. Q constant. V1=Q/C1=72e-6/12e-6=6 V. U1=0.5*C1*V1^2=0.5*12e-6*36=216e-6 J. Or 0.5 Q V =0.5*72e-6*6=216e-6. ΔU=-216e-6 J. Work on dielectric by field? = U0-U1=216 µJ (released). If external controls, external work required -216 µJ; mechanical work by field +216.
[[verification]]Connected:
Battery remains 12 V. C2=12e-6 F. Q2=C2 V=144e-6 C. U2=0.5*12e-6*144=864e-6 J. ΔU=+432e-6 J. Charge supplied by battery = Q2-Q0=72e-6 C. Work by battery = V ΔQ =12*72e-6=864e-6 J (positive supplied). Energy balance: W_batt = ΔU + W_mech by field? 864=432+432. The extra 432 is mechanical work done on dielectric by field pulling it in (or if no mechanism to extract, kinetic/heat). If external agent inserts quasistatically and removes energy, agent does -432? Need phrase.

[[alternative]]But check if battery work in connected case might be -? Some might define work done on the battery. If "battery's work when connected" could be work done by battery. We can state sign convention. If asked work done by battery: +864 µJ. Work done on battery by circuit: -864 µJ? Actually battery supplies energy, so work done by battery on circuit +864. The circuit does work on battery = -864 (or battery absorbs negative). [[conclusion]]Additional charge flows from battery into capacitor.

Need perhaps discuss if battery is disconnected before insertion vs connected while dielectric inserted, same initial. In connected case, when inserting dielectric at constant voltage, "battery's work" = 864 μJ. [[alternative]]But note in connected case there might be spark? Assuming quasistatic. If dielectric inserted at constant voltage, source supplies.

Need mention energy density? no.

[[verification]]Potential nuance: "A 6 microfarad capacitor is charged to 12 V. A dielectric that doubles its capacitance is inserted..." If battery disconnected after charging: initial Q. If battery connected in separate experiment: It's charged to 12 V then dielectric inserted while battery remains connected. Yes.

[[development]]Let's think about exact energy balance "difference in the energy balance." Could be they expect realizing for constant voltage, battery supplies twice the energy increase, with half mechanical work. Also disconnected, the energy decrease equals mechanical work done by field. Maybe compare: ΔU_connected = +432 µJ, battery energy spent 864 µJ, mechanical work +432. Disconnected: ΔU=-216 µJ. Why such difference? Because battery supplies charge to maintain voltage. In disconnected, capacitor voltage drops to 6 V and energy halves. In connected, voltage stays 12, charge doubles, energy doubles. Wait initial 432 to final 864, Δ=432. In disconnected initial 432 to final 216, Δ=-216. [[alternative]]Sum? Difference in ΔUs =648. Battery work =864; mechanical? Need account.

[[conclusion]]Let's consider the wording "Account for the difference in the energy balance." It might be a known problem about dielectric insertion with/without battery; battery work must account for energy. They may expect "with battery connected, battery does 864 µJ work, but energy increases only 432 µJ; remaining 432 is work done in pulling dielectric into capacitor." In disconnected, no battery, energy decreases by 216, so work done by gravitational/mechanical? Let's present both.

Need likely answer concise. But maybe include sign conventions and formulas.

[[conclusion]]Let's craft final with steps.

Let's denote C_i=6μF, V_i=12 V. Q_i=72 μC, U_i=432 μJ.

Case 1: battery disconnected:
C_f=12 μF, Q=72 μC, V_f=6 V, U_f=216 μJ. ΔU = -216 μJ. The capacitor field does mechanical work 216 μJ on dielectric (if released, it appears kinetic/heat; if quasistatic, external agent extracts 216 μJ).

Case 2: battery connected:
V=12 V, C_f=12 μF, Q_f=144 μC, U_f=864 μJ. ΔU=+432 μJ. Charge delivered by battery ΔQ=72 μC. Work done by battery W_b = VΔQ = 864 μJ.

Energy balance: W_b = ΔU + W_mech, so W_mech=864−432=432 μJ. The field pulls dielectric in, doing 432 μJ mechanical work. Thus only half of battery work is stored; half is available as mechanical work (or dissipated if damping). If external agent inserts quasistatically, it removes/absorbs 432 μJ (does −432 μJ work on slab); no contradiction.

We can mention if "work done on battery" is opposite sign.

Need maybe differentiate work by battery and work on dielectric sign. [[verification]]In disconnected, field does +216 mechanical work. But wait if field pulls dielectric in, capacitor energy decreases by 216; conservation U0 = U1 + W_mech (if no loss) -> W_mech=216. Correct.

In connected, U0 + W_b = U1 + W_mech? If W_mech is work done by field on dielectric, energy source initially U0 + battery = U1 + W_mech; 432+864=864+432. correct.

If the dielectric is inserted by an external agent slowly, to avoid acceleration, external agent does negative work (takes energy out) in both cases. Some sources state "work done in inserting dielectric" by external agent is negative; mechanical work by field positive. Need clarify.

[[verification]]Potential issue: "A 6 microfarad capacitor is charged to 12 V. A dielectric that doubles its capacitance is inserted, first with the battery disconnected and in a separate experiment with it connected." In the connected case, when battery remains connected from before, inserting dielectric pulls it in and charges capacitor. But if dielectric inserted rapidly, no quasi-static and can oscillate/radiate. Assuming equilibrium. We can mention ideal quasistatic/lossless.

Potential issue: If battery remains connected, initial capacitance before dielectric is 6uF? yes. It was charged to 12 and battery connected. Then dielectric doubles to 12uF. Fine.

[[conclusion]]Let's produce final with table perhaps. Desired oververbosity 5. Use clear.
