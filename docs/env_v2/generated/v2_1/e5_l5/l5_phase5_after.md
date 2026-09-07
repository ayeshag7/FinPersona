# L5 observables oracle vs true-V oracle (Phase-5 state; oracle encodes 'n/m' as the audit does)

Training seeds 500..539; T = 200; state {'events_json': True, 'control': 'A', 'dynamics': 'A', 'blowoff': 'dynamic', 'post_top': 'decay/40.0', 'randomise_eps_quarter': True, 'depth_mode': 'centred', 'volatility_json': True, 'iv': 'v21', 'observables_json': True, 'observables': 'multiple=B eps=v21 dividend=v21/shown analyst=C/shown sentiment=A volume=A'}.

## Per-phase OOS R2 / sign accuracy of x_hat on the training pool

- full: calm: R2 -0.03, sign 0.83; event: R2 0.57, sign 0.90; resolution: R2 0.49, sign 0.88
- price_only: calm: R2 -0.14, sign 0.80; event: R2 0.53, sign 0.87; resolution: R2 0.20, sign 0.80
- level_free: calm: R2 -0.07, sign 0.75; event: R2 0.49, sign 0.86; resolution: R2 0.24, sign 0.81
