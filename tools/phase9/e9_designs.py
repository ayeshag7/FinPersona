"""
v2.1 Phase 9 -- the CANDIDATE designs the wall-clock table prices (execution prompt, "Decisions: what governs what you
may start"; plan 13.1-13.2).

Nothing in this module is the pre-registered design.  `PREREG_PHASE_9.md` fixes the design after the team answers D2
under P9-1.  Every run count is computed from the factor lists below, never typed.  A design names:

* the factor lists it is the product of;
* whether it runs on every roster model or on one model;
* the calls a run makes: 200 decisions for a stateless run, plus side calls such as REG-9's probes.

Seeds per persona x scenario cell are a parameter of the table, not of the design: Phase 8's registered rule gives 93
(P8-16), and the roster pilots re-derive it (E9.2).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Tuple

T = 200
PERSONAS = ("ISFJ", "INTJ", "ENTJ")
CONTRAST_ARMS = ("static", "memory")
SCEN_E85 = ("flat", "bull_trap", "crash", "sustained_bull")      # E8.5's cells: 3 x 4 = 12 (P8-16's contrast cells)
SCEN_TIER_A = ("flat", "crash", "bull_trap")                     # plan 13.2's Tier A
N_GENERATOR_PARAMS = 6                                           # plan 13.1; REG-16 (i)
LEVELS_BESIDE_DEFAULT = 2                                        # low / high (plan 13.1's table)
SETTINGS_ALL = 1 + N_GENERATOR_PARAMS * LEVELS_BESIDE_DEFAULT    # 13 = default + 6 x 2
SETTINGS_SWEEP = N_GENERATOR_PARAMS * LEVELS_BESIDE_DEFAULT      # 12 non-default settings
CONTEXT_LEVELS = (5, 20, 50, "full")                             # P8-7
# REG-1 (register entry 1, "What would show which option is right", item 2)
REG1_PATHS, REG1_PERSONAS, REG1_SCEN = 10, 3, ("flat", "crash")
REG1_RENDERINGS = ("A_V20", "A_V100", "A_V400", "B")
# REG-9 (register entry 9): 3 renderings x 2 scenarios x 15 seeds on Flash, a probe at 20 stratified days per run
REG9_RENDERINGS, REG9_SCEN, REG9_SEEDS, REG9_PROBES_PER_RUN = 3, 2, 15, 20


@dataclass(frozen=True)
class Design:
    name: str
    label: str
    factors: Dict[str, int]                 # factor -> number of levels; seeds are multiplied in separately
    per_seed: bool = True                   # False: the seed count is inside `factors` (a fixed register design)
    all_models: bool = True                 # False: runs on one model (Flash, as the register writes it)
    calls_per_run: int = T
    stateful: bool = False
    note: str = ""

    def runs(self, seeds: int) -> int:
        n = 1
        for v in self.factors.values():
            n *= int(v)
        return n * (int(seeds) if self.per_seed else 1)


def designs() -> Dict[str, Design]:
    P, A = len(PERSONAS), len(CONTRAST_ARMS)
    out = [
        Design("headline_12cells", "static-memory contrast, default generator, E8.5's 12 persona x scenario cells",
               {"settings": 1, "personas": P, "arms": A, "scenarios": len(SCEN_E85)},
               note="the contrast P8-16 sized; stage 1 of a staged grid"),
        Design("headline_9cells", "static-memory contrast, default generator, Tier A's 3 scenarios",
               {"settings": 1, "personas": P, "arms": A, "scenarios": len(SCEN_TIER_A)}),
        Design("sweep_tierA", "the 12 non-default generator settings, Tier A's 3 scenarios",
               {"settings": SETTINGS_SWEEP, "personas": P, "arms": A, "scenarios": len(SCEN_TIER_A)},
               note="stage 2 of a staged grid"),
        Design("tierA_shape", "plan 13.2's Tier A shape: 13 settings x 3 personas x 2 arms x 3 scenarios",
               {"settings": SETTINGS_ALL, "personas": P, "arms": A, "scenarios": len(SCEN_TIER_A)}),
        Design("tierA_shape_4scen", "Tier A's shape on E8.5's 4 scenarios",
               {"settings": SETTINGS_ALL, "personas": P, "arms": A, "scenarios": len(SCEN_E85)}),
        Design("context_levels", "the context-length factor {5, 20, 50, full} x 2 arms on the default generator, Tier A's scenarios",
               {"levels": len(CONTEXT_LEVELS), "personas": P, "arms": A, "scenarios": len(SCEN_TIER_A)}, stateful=True,
               note="stateful: the latency of a call grows with the context (P8-7); not measured -- priced at the "
                    "stateless rate, which is a lower bound on its time"),
        Design("reg1_magnitude", "REG-1's LLM magnitude test as its factor list reads",
               {"paths": REG1_PATHS, "personas": REG1_PERSONAS, "scenarios": len(REG1_SCEN),
                "renderings": len(REG1_RENDERINGS)}, per_seed=False, all_models=False,
               note="the register writes '60 + 60 runs'; its own factor list (10 paths x 3 personas x 2 scenarios "
                    "x 4 renderings) is 240 -- the count is computed from the factors and the discrepancy reported"),
        Design("reg9_probe", "REG-9's phase-restatement probe",
               {"renderings": REG9_RENDERINGS, "scenarios": REG9_SCEN, "seeds": REG9_SEEDS}, per_seed=False,
               all_models=False, calls_per_run=T + REG9_PROBES_PER_RUN),
    ]
    return {d.name: d for d in out}


def seeds_grid() -> Tuple[int, ...]:
    """The seed counts the table is shown at, each read from its file where one exists (e8_5/power.json,
    e8_5/transfer.json via experiments/params/inference.json's main_grid_sizing block)."""
    from experiments import inference_params as IP
    v = IP.block("main_grid_sizing")["value"]
    return tuple(sorted({int(v["flash_only_seeds"]), int(v["paired_correct_seeds"]),
                         int(v["seeds_per_persona_scenario_cell"]), int(v["at_ratio_upper_seeds"])}))
