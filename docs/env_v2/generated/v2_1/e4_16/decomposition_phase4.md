# E3.8 the level-free channel, block by block (PREREG_PHASE_3.md section 11; P2-18's hand-off)

E3.8: the level-free calm channel decomposed one volatility block at a time at the Phase-3 parameters in force; the events and sentiment channels remain Phase 6's, and the full generator's number is the after-state SEP audit's.

| arm | level-free calm R2(x) [95 % CI] | delta over exact | Gaussian bound (window avg) |
|---|---|---|---|
| exact (the bound's model) | 0.145 [0.108, 0.176] | +0.000 | 0.163 |
| + GJR-t innovation (block in force) | 0.145 [0.096, 0.184] | +0.000 | 0.163 |
| + jumps (FIT lambda, sigma_J) | 0.192 [0.105, 0.288] | +0.047 | 0.177 |
| + GJR-t + jumps (the Phase-3 x innovation) | 0.203 [0.141, 0.262] | +0.057 | 0.177 |

The Gaussian bound applies exactly to the first arm only; for the others it is the reference line a NON-Gaussian innovation may legitimately exceed (Appendix B's own caveat). The full generator's calm number (events + sentiment on top) is in the after-state audit; the remaining gap between the last arm and that number is the events-plus-sentiment share, Phase 6's to characterise.
