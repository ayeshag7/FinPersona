# Held-out-scenario split (weakness 67): train on three scenarios, score the fourth

| held out | feature set | model | population | n rows | R2(x) [CI] |
|---|---|---|---|---|---|
| bull_trap | full | ridge | all | 72000 | -1.1234 [-1.2708, -1.0018] |
| bull_trap | full | ridge | calm | 11681 | +0.0439 [-0.0761, +0.1421] |
| bull_trap | full | gbt | all | 72000 | -1.2652 [-1.4194, -1.1456] |
| bull_trap | full | gbt | calm | 11681 | +0.2933 [+0.1715, +0.3769] |
| bull_trap | price_only | ridge | all | 72000 | -1.2877 [-1.4389, -1.1688] |
| bull_trap | price_only | ridge | calm | 11681 | -0.0070 [-0.1368, +0.0915] |
| bull_trap | price_only | gbt | all | 72000 | -1.3103 [-1.4716, -1.1905] |
| bull_trap | price_only | gbt | calm | 11681 | +0.1753 [+0.0694, +0.2480] |
| crash | full | ridge | all | 144000 | -0.3849 [-0.4441, -0.3262] |
| crash | full | ridge | calm | 35655 | -1.0661 [-1.2910, -0.8852] |
| crash | full | gbt | all | 144000 | -0.6806 [-0.7641, -0.6059] |
| crash | full | gbt | calm | 35655 | -0.2874 [-0.4780, -0.1544] |
| crash | price_only | ridge | all | 144000 | -0.2999 [-0.3522, -0.2464] |
| crash | price_only | ridge | calm | 35655 | -1.0095 [-1.2485, -0.8134] |
| crash | price_only | gbt | all | 144000 | -0.8211 [-0.8885, -0.7569] |
| crash | price_only | gbt | calm | 35655 | -0.8616 [-1.0652, -0.7077] |
| flat | full | ridge | all | 36000 | -0.3570 [-0.5387, -0.2234] |
| flat | full | ridge | calm | 36000 | -0.3570 [-0.5387, -0.2234] |
| flat | full | gbt | all | 36000 | -0.2312 [-0.3831, -0.1047] |
| flat | full | gbt | calm | 36000 | -0.2312 [-0.3831, -0.1047] |
| flat | price_only | ridge | all | 36000 | -0.1218 [-0.2547, -0.0181] |
| flat | price_only | ridge | calm | 36000 | -0.1218 [-0.2547, -0.0181] |
| flat | price_only | gbt | all | 36000 | -0.2518 [-0.3950, -0.1296] |
| flat | price_only | gbt | calm | 36000 | -0.2518 [-0.3950, -0.1296] |
| sustained_bull | full | ridge | all | 36000 | -2.3498 [-2.8836, -1.8797] |
| sustained_bull | full | ridge | calm | 36000 | -2.3498 [-2.8836, -1.8797] |
| sustained_bull | full | gbt | all | 36000 | -3.1417 [-3.9517, -2.5038] |
| sustained_bull | full | gbt | calm | 36000 | -3.1417 [-3.9517, -2.5038] |
| sustained_bull | price_only | ridge | all | 36000 | -1.3974 [-1.6947, -1.1436] |
| sustained_bull | price_only | ridge | calm | 36000 | -1.3974 [-1.6947, -1.1436] |
| sustained_bull | price_only | gbt | all | 36000 | -2.2972 [-2.7847, -1.8848] |
| sustained_bull | price_only | gbt | calm | 36000 | -2.2972 [-2.7847, -1.8848] |
