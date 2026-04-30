# Tax Reform Model v3 — Open Economy with Trade Diversification

A macroeconomic simulation of progressive tax reform combined with a Negative Income Tax (NIT) and Aid-for-Trade (AfT) export-promotion mechanism, evaluated under an open-economy GDP framework with World Bank income-tier-stratified trade flows.

> **Status:** Research project — Northeastern University. The proposed tax brackets and policy parameters are a thought experiment, not a policy endorsement. The model is calibrated against published macro literature and BEA baselines, but all conclusions should be read as illustrative.

---

## Headline Result

Under joint Monte Carlo simulation (N = 50,000) over five key parameters:

- **ΔY:** ~$1,090B (≈ +3.85% GDP), 90% CI broadly positive across all draws
- **ΔNX:** trade balance **deteriorates in every Monte Carlo draw** — import leakage from higher MPM dominates the export gain from Aid-for-Trade
- **Multiplier drag:** raising aggregate MPM from 0.150 → ~0.180 reduces *k* meaningfully, costing ~$200B+ in foregone GDP relative to a no-diversification counterfactual

The model's most useful finding is arguably negative: *the trade-balance cost of diversification is structural, not a modeling artifact, and policymakers would need α ≥ ~3× higher export elasticity (or slower γ ramp on MFN imports) to neutralize it.*

---

## Model Structure

**Core identity:** `Y = C + I + G + (X − M)`

| Component | Specification | Notes |
|---|---|---|
| C | C₀ + C₁·(Y − T) | MPC stratified across 7 income brackets; λ = 0.15 permanent-income discount |
| I | I₀ − I₁·r | Exogenous |
| G | G₀ + G_aft | G_aft = φ · net fiscal surplus, φ = 6.5% |
| X | X₀ + α·G_aft | Endogenous export response with transition contraction |
| M | Σⱼ [M₀ⱼ + M₁ⱼ·Y] | Stratified by World Bank tier (HI / UMI / LMI / LI) |

**Tax structure**
- 7 brackets, current 2026 law vs. proposed 1933-inflation-adjusted schedule
- Behavioral income shrinkage: ε · ΔRate / (1 − rate_current), capped at 80%
- NIT transfers calibrated at 25% of original design values (fiscal-budget constrained)

**Trade diversification mechanisms**
1. MFN import expansion to developing tiers (γ_UMI = 0.25, γ_LMI = 0.40, γ_LI = 0.60)
2. Aid-for-Trade export promotion (α_UMI = 0.20, α_LMI = 0.12, α_LI = 0.05)
3. Transition contraction in developing-tier exports (8–18%)
4. HI trade fully preserved (τ_HI = 0)

---

## Calibration & Sources

| Parameter | Value | Source |
|---|---|---|
| λ (PIH discount) | 0.15 | Carroll (2001) buffer-stock; Jappelli & Pistaferri (2010); CBO (2023) |
| MPC gradient | 0.95 → 0.06 | Dynan, Skinner & Zeldes (2004) |
| Aggregate MPM baseline | 0.150 | BEA (2024) |
| Behavioral elasticity | 0.10–0.70 across brackets | Feldstein (1995); Saez et al. (2012) |
| GDP baseline | $28,300B (2026) | BEA NIPA |
| World Bank tier thresholds | 2026 GNI per capita | World Bank Atlas method |

λ = 0.15 is deliberately at the **lower bound** of the literature, making the consumption-response estimates conservative.

---

## Repository Contents

```
.
├── tax_reform_v3.py          Main simulation script
├── README.md                 This file
├── outputs/
│   ├── fig1_gdp_multiplier.png
│   ├── fig2_brackets.png
│   ├── fig3_nit_consumption.png
│   ├── fig4_trade.png
│   ├── fig5_summary.png
│   ├── figA_nit_defense.png        NIT design defense & calibration
│   ├── figB_uncertainty.png        Monte Carlo dashboard
│   └── figC_trade_balance.png      Trade balance spotlight
└── docs/
    └── presentation.pdf      Campus presentation deck
```

---

## How to Run

Requirements: Python 3.9+, NumPy, Matplotlib, SciPy.

```bash
git clone https://github.com/TheDataGatherer99/tax-reform-v3.git
cd tax-reform-v3
pip install numpy matplotlib scipy
python tax_reform_v3.py
```

The script auto-creates `./outputs/` and writes all eight figures plus a console summary of fiscal flows, multipliers, and trade-balance decomposition. Random seed is fixed at 42 for full reproducibility of the Monte Carlo results.

Runtime: ~30 seconds on a modern laptop (Monte Carlo dominates).

---

## Figures

**Fig 1 — GDP Decomposition & Multiplier Analysis.** Waterfall of ΔC, ΔG, ΔX, ΔM, ΔY across diversified vs. counterfactual scenarios; multiplier leakage decomposition; *k* sensitivity to MPM and to φ.

**Fig 2 — Tax Bracket Analysis.** Marginal vs. effective rates, behavioral shrinkage by bracket, ΔTax per person, aggregate revenue contribution, threshold comparison on log scale.

**Fig 3 — NIT Transfers & Consumption Function.** Transfer schedule, net tax after NIT, MPC matrix decomposition (durables / non-durables / services), λ sensitivity for first-round ΔC.

**Fig 4 — Trade Diversification Structure.** Import and export shares pre/post by tier, M₁ shifts, ΔM by tier, G_aft → ΔX with transition contraction, α and γ sensitivity curves.

**Fig 5 — Summary Dashboard.** Single-page synthesis of all mechanisms with full equation summary.

**Fig A — NIT Design Defense.** Phased calibration (10%/25%/50%/100%), λ literature anchoring, fiscal sustainability chain, MPC pass-through, design rationale.

**Fig B — Monte Carlo Uncertainty Dashboard.** N=50,000 joint distribution over (λ, φ, m, ε, α); marginal distributions for ΔY, ΔNX, ΔY%; sensitivity tornado; 2D joint plots; variance decomposition.

**Fig C — Trade Balance Deterioration Spotlight.** Net export position pre/post, ΔX vs. ΔM asymmetry, leakage tier breakdown, multiplier drag, break-even α and γ analysis, policy options.

---

## Limitations & Honest Caveats

- **Static-equilibrium framework.** No dynamic adjustment, no monetary policy reaction, no nominal vs. real distinction. The model captures first-round fiscal arithmetic, not transition dynamics.
- **Linear MPC and behavioral response.** Both are stylized. Saez-elasticity literature gives wide ranges; I use a conservative midpoint with sensitivity testing.
- **Trade flows are reduced-form.** No CES import demand, no Armington elasticities, no terms-of-trade adjustment. The γ and α coefficients are calibrated to plausible orders of magnitude, not estimated.
- **Monte Carlo assumes parameter independence.** In reality (λ, m, ε) likely co-move; full joint estimation is out of scope for this project.
- **Income-bracket means are stylized representative agents.** Real distributions within each bracket have meaningful variance the model does not capture.
- **Proposed bracket schedule is illustrative.** The 1933-inflation-adjusted thresholds and rates (up to 94%) are a thought experiment about progressivity; they are not a policy proposal.

The trade-balance finding is robust to all these caveats — the asymmetry between ΔM and ΔX appears across the full Monte Carlo support — which is why I treat it as the project's central honest result.

---

## Citation

If you reference this work:

```
David Odell. (2026). Tax Reform Model v3 — Open Economy with Trade Diversification.
Northeastern University. https://github.com/TheDataGatherer99/tax-reform-v3
```

---

## License

MIT — free to use, modify, and extend with attribution.
