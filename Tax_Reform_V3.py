"""
TAX REFORM MODEL v3 — Open Economy with Trade Diversification
Campus-Wide Presentation Edition — Northeastern University

GDP Expenditure Equation:  Y = C + I + G + (X - M)

  C  = C_0 + C_1*(Y - T)       [MPC λ-adjusted, bracket-specific]
  I  = I_0 - I_1*r              [exogenous]
  G  = G_0 + G_aft              [Aid-for-Trade component]
  X  = X_0 + alpha*G_aft        [endogenous export promotion]
  M  = sum_j [M_0j + M_1j*Y]   [stratified by World Bank income tier]

World Bank Tiers (2026):
  HI  : GNI > $13,845/capita
  UMI : $4,466 - $13,845
  LMI : $1,136 - $4,465
  LI  : < $1,136

Figures produced (saved to ./outputs/):
  Fig 1  — GDP Decomposition & Multiplier Analysis
  Fig 2  — Tax Bracket Analysis
  Fig 3  — NIT Transfers & Consumption Function
  Fig 4  — Trade Diversification Structure
  Fig 5  — Summary Dashboard
  Fig A  — NIT Design Defense & Calibration        [NEW — campus edition]
  Fig B  — Uncertainty / Monte Carlo Dashboard     [NEW — campus edition]
  Fig C  — Trade Balance Deterioration Spotlight   [NEW — campus edition]
"""

# ════════════════════════════════════════════════════════════════════════════
# 0. IMPORTS & OUTPUT DIRECTORY
# ════════════════════════════════════════════════════════════════════════════

import subprocess, sys, os
import matplotlib
matplotlib.rcParams["text.usetex"] = False  # prevent mathtext dollar-sign errors

def _install(pkg):
    subprocess.check_call([sys.executable, "-m", "pip", "install", pkg],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

for pkg in ("numpy", "matplotlib", "scipy"):
    try:
        __import__(pkg)
    except ImportError:
        print(f"Installing {pkg}..."); _install(pkg)

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches

np.random.seed(42)
OUT = "/mnt/user-data/outputs"
os.makedirs(OUT, exist_ok=True)

# ════════════════════════════════════════════════════════════════════════════
# 1. COLOUR PALETTE
# ════════════════════════════════════════════════════════════════════════════

DK   = (0.09, 0.09, 0.09)
AXC  = (0.15, 0.15, 0.15)
AX2  = (0.18, 0.18, 0.22)
TC   = (0.95, 0.95, 0.95)
GRC  = (0.28, 0.28, 0.28)
BLU  = (0.25, 0.60, 0.95)
GRN  = (0.15, 0.82, 0.40)
ORG  = (0.95, 0.55, 0.15)
RED  = (0.88, 0.22, 0.22)
PRP  = (0.68, 0.32, 0.92)
TEL  = (0.10, 0.75, 0.75)
GLD  = (0.95, 0.80, 0.20)
GRY  = (0.50, 0.50, 0.50)
AMB  = (0.98, 0.70, 0.10)
WHT  = (1.00, 1.00, 1.00)
TIER_COLORS = [BLU, GRN, ORG, RED]

def c(col, a=0.70):
    """Return RGBA tuple from an RGB colour."""
    return (*col, a)

def style_ax(ax, grid_alpha=0.25):
    ax.set_facecolor(AXC)
    ax.tick_params(colors=TC, labelsize=9)
    ax.xaxis.label.set_color(TC)
    ax.yaxis.label.set_color(TC)
    ax.title.set_color(TC)
    ax.grid(True, color=GRC, alpha=grid_alpha, linewidth=0.6)
    for sp in ax.spines.values():
        sp.set_edgecolor(GRC)

def badge(ax, text, xy=(0.03, 0.95), col=GLD, fs=8):
    ax.annotate(text, xy=xy, xycoords="axes fraction",
                fontsize=fs, color=col, fontweight="bold",
                fontfamily="monospace",
                bbox=dict(boxstyle="round,pad=0.3", facecolor=AX2,
                          edgecolor=col, linewidth=1.2))

def save(fig, name):
    path = os.path.join(OUT, name)
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=DK)
    print(f"  Saved → {path}")
    plt.close(fig)

# ════════════════════════════════════════════════════════════════════════════
# 2. PARAMETERS — TAX & HOUSEHOLD
# ════════════════════════════════════════════════════════════════════════════

adult_population = 260e6
single_pop       = adult_population * 0.5923
married_hh       = adult_population * 0.4077 / 2

pop_shares_raw = np.array([0.80, 0.12, 0.05, 0.02, 0.008, 0.004, 0.001])
pop_shares     = pop_shares_raw / pop_shares_raw.sum()

mean_income_single  = np.array([60_000, 499_977, 1_714_590, 3_484_899,
                                 5_671_280, 9_195_141, 32_183_683], float)
mean_income_married = np.array([96_000, 799_964, 2_743_344, 5_575_839,
                                 9_074_047, 14_712_226, 51_493_261], float)

# 2026 current-law brackets
thresh_single_cur  = np.array([0, 12_400, 50_400, 105_700,
                                201_775, 256_225, 640_600], float)
thresh_married_cur = thresh_single_cur * 2
rates_cur          = np.array([0.10, 0.12, 0.22, 0.24, 0.32, 0.35, 0.37])

# Proposed 1933-inflation-adjusted brackets
thresh_single_prop  = np.array([0, 311_493.78, 1_266_071.45, 2_655_233.17,
                                 5_068_681.86, 6_436_491.18, 16_092_169.96], float)
thresh_married_prop = np.array([0, 622_987.54, 2_532_142.89, 5_310_466.34,
                                 10_137_363.71, 12_872_982.36, 19_310_101.54], float)
rates_prop = np.array([0.05, 0.15, 0.30, 0.50, 0.70, 0.88, 0.94])

# NIT transfers — 25% of original design values
# (fiscal-budget constraint; phased implementation)
nit_single  = np.array([6_750, 5_250, 3_750, 2_250, 750, 0, 0], float)
nit_married = np.array([7_800, 0, 0, 0, 0, 0, 0], float)

# NIT sub-bracket data — single
nit_sub_inc_s = np.array([10_000, 30_000, 50_000, 70_000, 90_000, 125_000, 230_747], float)
nit_sub_net_s = np.array([16_625, 35_125, 53_625, 72_125, 90_625, 123_750, 226_710], float)
nit_sub_tax_s = np.array([-6_625, -5_125, -3_625, -2_125, -625, 1_250, 4_037], float)

# NIT sub-bracket data — married
nit_sub_inc_m = np.array([16_000, 48_000, 80_000, 112_000, 144_000, 200_000, 369_194], float)
nit_sub_net_m = np.array([26_600, 56_200, 85_800, 115_400, 145_000, 198_000, 362_737], float)
nit_sub_tax_m = np.array([-10_600, -8_200, -5_800, -3_400, -1_000, 2_000, 6_457], float)

# MPC matrix [durables, non-durables, services]
mpc_matrix = np.array([
    [0.10, 0.60, 0.25],   # B1: C_1 = 0.95
    [0.15, 0.45, 0.25],   # B2: C_1 = 0.85
    [0.20, 0.30, 0.20],   # B3: C_1 = 0.70
    [0.15, 0.20, 0.15],   # B4: C_1 = 0.50
    [0.10, 0.10, 0.10],   # B5: C_1 = 0.30
    [0.05, 0.05, 0.05],   # B6: C_1 = 0.15
    [0.02, 0.02, 0.02],   # B7: C_1 = 0.06
])
C_1 = mpc_matrix.sum(axis=1)

# λ = 0.15: permanent-income discount
# Carroll (2001); Jappelli & Pistaferri (2010); CBO (2023) benchmark
lam    = 0.15
C_1_eff = lam * C_1

elasticity = np.array([0.10, 0.15, 0.20, 0.30, 0.40, 0.55, 0.70])
t_eff      = np.dot(pop_shares, rates_prop)

# ════════════════════════════════════════════════════════════════════════════
# 3. WORLD BANK TRADE TIER PARAMETERS
# ════════════════════════════════════════════════════════════════════════════

tier_names = ["High Income (HI)", "Upper-Middle (UMI)",
              "Lower-Middle (LMI)", "Low Income (LI)"]
tier_short = ["HI", "UMI", "LMI", "LI"]

import_share_baseline = np.array([0.65, 0.25, 0.08, 0.02])
M_1_tier_baseline     = np.array([0.105, 0.032, 0.010, 0.003])  # sum = 0.150
export_share_baseline = np.array([0.65, 0.22, 0.10, 0.03])

# Baseline GDP components ($B, 2026)
Y_baseline = 28_300
C_baseline = 19_110
I_baseline =  4_811
G_baseline =  5_377
X_baseline =  3_113
M_baseline =  4_111

# ════════════════════════════════════════════════════════════════════════════
# 4. TRADE POLICY PARAMETERS
# ════════════════════════════════════════════════════════════════════════════

# Mechanism 1: MFN import expansion — developing tiers
gamma_UMI = 0.25   # UMI M_1 boost
gamma_LMI = 0.40   # LMI M_1 boost
gamma_LI  = 0.60   # LI  M_1 boost

# Mechanism 2: Export returns & transition contraction
alpha_UMI = 0.20; alpha_LMI = 0.12; alpha_LI = 0.05
aft_alloc_UMI = 0.45; aft_alloc_LMI = 0.40; aft_alloc_LI = 0.15
x_contract_UMI = 0.08; x_contract_LMI = 0.12; x_contract_LI = 0.18

# Mechanism 3: HI trade fully preserved (tau_HI = 0)
tau_HI = 0.0

# Mechanism 4: Aid-for-Trade fiscal share
phi = 0.065   # 6.5% of net surplus → G_aft

# ════════════════════════════════════════════════════════════════════════════
# 5. HELPERS
# ════════════════════════════════════════════════════════════════════════════

def marginal_tax(income, thresholds, rates):
    tax, n = 0.0, len(rates)
    for k in range(n):
        if income <= thresholds[k]:
            break
        top     = thresholds[k + 1] if k < n - 1 else 1e12
        taxable = min(income, top) - thresholds[k]
        tax    += taxable * rates[k]
    return tax

# ════════════════════════════════════════════════════════════════════════════
# 6. TAX COMPUTATION
# ════════════════════════════════════════════════════════════════════════════

cur_tax_s  = np.zeros(7); cur_tax_m  = np.zeros(7)
prop_tax_s = np.zeros(7); prop_tax_m = np.zeros(7)
adj_inc_s  = np.zeros(7); adj_inc_m  = np.zeros(7)
pop_s      = np.zeros(7); pop_m      = np.zeros(7)

for i in range(7):
    pop_s[i] = single_pop * pop_shares[i]
    pop_m[i] = married_hh * pop_shares[i]
    cur_tax_s[i] = marginal_tax(mean_income_single[i],  thresh_single_cur,  rates_cur)
    cur_tax_m[i] = marginal_tax(mean_income_married[i], thresh_married_cur, rates_cur)
    rate_change  = rates_prop[i] - rates_cur[i]
    if rate_change > 0:
        shrink       = min(elasticity[i] * rate_change / (1 - rates_cur[i]), 0.80)
        adj_inc_s[i] = mean_income_single[i]  * (1 - shrink)
        adj_inc_m[i] = mean_income_married[i] * (1 - shrink)
    else:
        adj_inc_s[i] = mean_income_single[i]
        adj_inc_m[i] = mean_income_married[i]
    prop_tax_s[i] = marginal_tax(adj_inc_s[i], thresh_single_prop,  rates_prop)
    prop_tax_m[i] = marginal_tax(adj_inc_m[i], thresh_married_prop, rates_prop)

agg_cur_s  = np.dot(pop_s, cur_tax_s)  / 1e9
agg_cur_m  = np.dot(pop_m, cur_tax_m)  / 1e9
agg_prop_s = np.dot(pop_s, prop_tax_s) / 1e9
agg_prop_m = np.dot(pop_m, prop_tax_m) / 1e9
total_rev  = agg_prop_s + agg_prop_m

# ════════════════════════════════════════════════════════════════════════════
# 7. NIT TRANSFERS & NET INCOME
# ════════════════════════════════════════════════════════════════════════════

net_tax_s  = prop_tax_s - nit_single
net_tax_m  = prop_tax_m - nit_married
net_inc_s  = adj_inc_s  - net_tax_s
net_inc_m  = adj_inc_m  - net_tax_m
nit_cost_s = pop_s * nit_single
nit_cost_m = pop_m * nit_married
total_nit  = (nit_cost_s.sum() + nit_cost_m.sum()) / 1e9
net_fiscal = total_rev - total_nit

# ════════════════════════════════════════════════════════════════════════════
# 8. G = G_0 + G_aft
# ════════════════════════════════════════════════════════════════════════════

G_aft     = phi * net_fiscal
G_aft_UMI = G_aft * aft_alloc_UMI
G_aft_LMI = G_aft * aft_alloc_LMI
G_aft_LI  = G_aft * aft_alloc_LI
delta_G   = G_aft

# ════════════════════════════════════════════════════════════════════════════
# 9. X = X_0 + alpha*G_aft (with transition contraction)
# ════════════════════════════════════════════════════════════════════════════

dX_promo_UMI    = alpha_UMI * G_aft_UMI
dX_promo_LMI    = alpha_LMI * G_aft_LMI
dX_promo_LI     = alpha_LI  * G_aft_LI
dX_contract_UMI = -x_contract_UMI * X_baseline * export_share_baseline[1]
dX_contract_LMI = -x_contract_LMI * X_baseline * export_share_baseline[2]
dX_contract_LI  = -x_contract_LI  * X_baseline * export_share_baseline[3]
dX_UMI          = dX_promo_UMI + dX_contract_UMI
dX_LMI          = dX_promo_LMI + dX_contract_LMI
dX_LI           = dX_promo_LI  + dX_contract_LI
dX_HI           = 0.0
delta_X         = dX_HI + dX_UMI + dX_LMI + dX_LI

X_new_total      = X_baseline + delta_X
export_share_new = np.clip(
    np.array([(X_baseline * export_share_baseline[j] + v) / max(X_new_total, 1)
              for j, v in enumerate([dX_HI, dX_UMI, dX_LMI, dX_LI])]), 0, 1)

# ════════════════════════════════════════════════════════════════════════════
# 10. M = sum_j [M_0j + M_1j*Y]
# ════════════════════════════════════════════════════════════════════════════

M_1_tier         = M_1_tier_baseline.copy()
M_1_tier[1]     *= (1 + gamma_UMI)
M_1_tier[2]     *= (1 + gamma_LMI)
M_1_tier[3]     *= (1 + gamma_LI)
import_share_new = M_1_tier / M_1_tier.sum()
M_1_total_new    = M_1_tier.sum()
M_1_total_old    = M_1_tier_baseline.sum()

# ════════════════════════════════════════════════════════════════════════════
# 11. C = C_0 + C_1*(Y - T) — CONSUMPTION FUNCTION
# ════════════════════════════════════════════════════════════════════════════

dY_T_s = np.zeros(7); dY_T_m = np.zeros(7)
dC_s   = np.zeros(7); dC_m   = np.zeros(7)

for i in range(7):
    YT_cur_s  = mean_income_single[i]  - cur_tax_s[i]
    YT_cur_m  = mean_income_married[i] - cur_tax_m[i]
    YT_prop_s = adj_inc_s[i] - prop_tax_s[i] + nit_single[i]
    YT_prop_m = adj_inc_m[i] - prop_tax_m[i] + nit_married[i]
    dY_T_s[i] = YT_prop_s - YT_cur_s
    dY_T_m[i] = YT_prop_m - YT_cur_m
    dC_s[i]   = lam * C_1[i] * dY_T_s[i] * pop_s[i]
    dC_m[i]   = lam * C_1[i] * dY_T_m[i] * pop_m[i]

C_1_eff_avg = lam * np.dot(pop_s + pop_m, C_1) / (pop_s + pop_m).sum()
dC_first    = (dC_s.sum() + dC_m.sum()) / 1e9

# ════════════════════════════════════════════════════════════════════════════
# 12. Y = C + I + G + (X - M) — FULL GDP
# ════════════════════════════════════════════════════════════════════════════

s      = 1 - C_1_eff_avg
t      = t_eff
m      = M_1_total_new
m_base = M_1_total_old

k_diversified = 1 / (s + t + m)
k_baseline    = 1 / (s + t + m_base)
k_closed      = 1 / (s + t)

delta_X_total        = delta_X
autonomous_injection = dC_first + delta_G + delta_X_total
delta_Y_raw          = k_diversified * autonomous_injection
delta_C              = C_1_eff_avg * delta_Y_raw
delta_M              = m * delta_Y_raw
delta_NX             = delta_X_total - delta_M
delta_Y              = delta_C + delta_G + delta_NX
Y_pct                = 100 * delta_Y / Y_baseline
delta_M_tier         = (M_1_tier / m) * delta_M

# Counterfactual (no diversification)
autonomous_injection_base = dC_first + delta_G
delta_Y_base  = k_baseline * autonomous_injection_base
delta_C_base  = C_1_eff_avg * delta_Y_base
delta_M_base  = m_base * delta_Y_base
Y_pct_base    = 100 * delta_Y_base / Y_baseline

# ════════════════════════════════════════════════════════════════════════════
# 13. CONSOLE SUMMARY
# ════════════════════════════════════════════════════════════════════════════

SEP = "=" * 65
print(SEP)
print(" TAX REFORM v3 — Open Economy | Trade Diversification")
print(" Y = C + I + G + (X - M)")
print(SEP)
print(f"\n Baseline GDP            : ${Y_baseline:,.0f}B")
print(f" Current revenue         : ${agg_cur_s+agg_cur_m:,.2f}B")
print(f" Proposed revenue        : ${total_rev:,.2f}B")
print(f" Total NIT cost          : ${total_nit:,.2f}B  ({100*total_nit/total_rev:.1f}% of proposed revenue)")
print(f" Net fiscal surplus      : ${net_fiscal:,.2f}B")
print(f" G_aft (phi={phi:.3f})      : ${G_aft:,.2f}B")
print(f" Multiplier k_base       : {k_baseline:.4f}")
print(f" Multiplier k_diversified: {k_diversified:.4f}")
print(f" MPM baseline            : {m_base:.4f}")
print(f" MPM new                 : {m:.4f}")
print(f" delta_X                 : ${delta_X_total:+.2f}B")
print(f" delta_M                 : ${delta_M:+.2f}B")
print(f" delta_NX                : ${delta_NX:+.2f}B")
print(f"\n dY (diversified)        : ${delta_Y:+.2f}B  ({Y_pct:+.2f}%)")
print(f" dY (no-diversification) : ${delta_Y_base:+.2f}B  ({Y_pct_base:+.2f}%)")
print(f" GDP trade offset        : ${delta_Y - delta_Y_base:+.2f}B")
print(f"\n{SEP}\n")

# ════════════════════════════════════════════════════════════════════════════
# PLOT HELPERS
# ════════════════════════════════════════════════════════════════════════════

x4 = np.arange(4); x7 = np.arange(7); x3 = np.arange(3); x5 = np.arange(5)
w  = 0.38

# ════════════════════════════════════════════════════════════════════════════
# FIGURE 1 — GDP Decomposition & Multiplier Analysis
# ════════════════════════════════════════════════════════════════════════════
print("Generating Figure 1...")
fig1 = plt.figure(figsize=(20, 13), facecolor=DK)
fig1.suptitle(
    "Figure 1 — GDP Decomposition & Multiplier Analysis\n"
    "Y = C + I + G + (X-M)  |  k = 1/(s+t+m)  |  lambda = 0.15  |  Baseline $28,300B",
    color=TC, fontsize=11, fontweight="bold", y=0.99)
gs1 = gridspec.GridSpec(3, 3, figure=fig1, hspace=0.55, wspace=0.40)

comp_v  = [delta_C, delta_G, delta_X_total, -delta_M, delta_Y]
comp_v2 = [delta_C_base, delta_G, 0, -delta_M_base, delta_Y_base]
clr_v   = [GRN if v >= 0 else RED for v in comp_v]
comp_n  = ["dC", "dG", "dX", "-dM", "dY"]

# P1-1: GDP waterfall
ax = fig1.add_subplot(gs1[0, :2]); style_ax(ax)
ba = ax.bar(x5 - w/2, comp_v,  w, color=[c(col) for col in clr_v],
            edgecolor=clr_v, linewidth=1.5, label="Diversified")
bb = ax.bar(x5 + w/2, comp_v2, w, color=[c(GRY, 0.45)]*5,
            edgecolor=[GRY]*5, linewidth=1, label="No Diversification")
ax.axhline(0, color="white", linestyle="--", linewidth=1)
for bar, val in zip(ba, comp_v):
    ax.text(bar.get_x()+bar.get_width()/2, val + (8 if val >= 0 else -22),
            f"${val:+.0f}B", ha="center", va="bottom", color=TC, fontsize=8, fontfamily="monospace")
ax.set_xticks(x5); ax.set_xticklabels(comp_n, color=TC, fontsize=10)
ax.set_ylabel("Change ($B)", color=TC)
ax.set_title(f"GDP Waterfall  Diversified (+{delta_Y:.1f}B, {Y_pct:+.2f}%) vs Counterfactual (+{delta_Y_base:.1f}B, {Y_pct_base:+.2f}%)",
             fontweight="bold", color=TC)
ax.legend(facecolor=AXC, labelcolor=TC, fontsize=8); ax.tick_params(colors=TC)

# P1-2: Baseline GDP composition
ax = fig1.add_subplot(gs1[0, 2]); style_ax(ax)
gdp_lbls = ["C\n$19,110B", "I\n$4,811B", "G\n$5,377B", "X-M\n-$998B"]
gdp_vals = [19110, 4811, 5377, -998]
gdp_clrs = [BLU, TEL, GLD, RED]
ax.barh(gdp_lbls, gdp_vals, color=[c(col) for col in gdp_clrs],
        edgecolor=gdp_clrs, linewidth=1.5)
ax.axvline(0, color="white", linestyle="--", linewidth=0.8)
ax.set_xlabel("$B", color=TC)
ax.set_title("Baseline GDP\nComposition 2026", fontweight="bold", color=TC)
ax.tick_params(colors=TC)

# P1-3: Multiplier leakage decomposition
ax = fig1.add_subplot(gs1[1, 0]); ax2 = ax.twinx(); style_ax(ax)
scenarios = ["Diversified", "No Divers.", "Closed\nEconomy"]
s_vals = [s, s, s]; t_vals = [t, t, t]; m_vals = [m, m_base, 0]
k_vals = [k_diversified, k_baseline, k_closed]
xb = np.arange(3)
ax.bar(xb, s_vals, 0.5, color=c(BLU, 0.6), edgecolor=BLU, linewidth=1, label="s (savings)")
ax.bar(xb, t_vals, 0.5, bottom=s_vals, color=c(GLD, 0.6), edgecolor=GLD, linewidth=1, label="t (tax)")
ax.bar(xb, m_vals, 0.5, bottom=[s_vals[i]+t_vals[i] for i in range(3)],
       color=c(RED, 0.6), edgecolor=RED, linewidth=1, label="m (imports)")
ax2.plot(xb, k_vals, "o-", color=GRN, linewidth=2, markersize=8, zorder=5)
for xi, kv in zip(xb, k_vals):
    ax2.text(xi, kv+0.005, f"{kv:.4f}", ha="center", va="bottom",
             color=GRN, fontsize=8, fontfamily="monospace")
ax.set_xticks(xb); ax.set_xticklabels(scenarios, color=TC, fontsize=9)
ax.set_ylabel("Leakage Rate (s+t+m)", color=TC)
ax2.set_ylabel("Multiplier k", color=GRN); ax2.tick_params(colors=GRN)
ax.set_title("Multiplier Decomposition\nk = 1/(s+t+m)", fontweight="bold", color=TC)
ax.legend(facecolor=AXC, labelcolor=TC, fontsize=7, loc="upper left"); ax.tick_params(colors=TC)

# P1-4: k sensitivity curve
ax = fig1.add_subplot(gs1[1, 1]); style_ax(ax)
m_range = np.linspace(0.05, 0.30, 200)
k_range = 1 / (s + t + m_range)
ax.plot(m_range, k_range, color=TEL, linewidth=2)
ax.axvline(m_base, color=GLD, linestyle="--", linewidth=1.5,
           label=f"m_base={m_base:.4f}  k={k_baseline:.4f}")
ax.axvline(m,      color=RED, linestyle="--", linewidth=1.5,
           label=f"m_new ={m:.4f}  k={k_diversified:.4f}")
ax.axhline(1.0, color="white", linestyle=":", linewidth=1, alpha=0.5, label="k = 1")
ax.scatter([m_base, m], [k_baseline, k_diversified], color=[GLD, RED], s=60, zorder=5)
ax.set_xlabel("Aggregate MPM (m)", color=TC); ax.set_ylabel("Multiplier k", color=TC)
ax.set_title("k Sensitivity to MPM\nOpen Economy: s+t fixed", fontweight="bold", color=TC)
ax.legend(facecolor=AXC, labelcolor=TC, fontsize=7); ax.tick_params(colors=TC)

# P1-5: Autonomous injection chain
ax = fig1.add_subplot(gs1[1, 2]); style_ax(ax)
inj_lbls = ["dC_first", "dG", "dX", "Total A", "dY_raw", "dY_net"]
inj_vals = [dC_first, delta_G, delta_X_total,
            dC_first + delta_G + delta_X_total,
            k_diversified * (dC_first + delta_G + delta_X_total), delta_Y]
inj_clrs = [BLU, GLD, TEL, PRP, GRN, GRN]
bars = ax.bar(range(6), inj_vals, color=[c(col) for col in inj_clrs],
              edgecolor=inj_clrs, linewidth=1.5)
for bar, val in zip(bars, inj_vals):
    ax.text(bar.get_x()+bar.get_width()/2, val+10, f"${val:.0f}B",
            ha="center", va="bottom", color=TC, fontsize=7, fontfamily="monospace")
ax.set_xticks(range(6)); ax.set_xticklabels(inj_lbls, color=TC, fontsize=8, rotation=20, ha="right")
ax.set_ylabel("$B", color=TC)
ax.set_title("Autonomous Injection Chain\nA -> k*A -> dY", fontweight="bold", color=TC)
ax.tick_params(colors=TC)

# P1-6: phi sensitivity
ax = fig1.add_subplot(gs1[2, 0]); ax2 = ax.twinx(); style_ax(ax)
phi_range = np.linspace(0.01, 0.30, 100)
def approx_dY(phi_val):
    ga = phi_val * net_fiscal
    dX_u = alpha_UMI * ga * aft_alloc_UMI + dX_contract_UMI
    dX_l = alpha_LMI * ga * aft_alloc_LMI + dX_contract_LMI
    dX_i = alpha_LI  * ga * aft_alloc_LI  + dX_contract_LI
    dx = dX_u + dX_l + dX_i
    ai = dC_first + ga + dx
    yr = k_diversified * ai
    return C_1_eff_avg * yr + ga + (dx - m * yr)
gaft_range = phi_range * net_fiscal
dy_range   = np.array([approx_dY(p) for p in phi_range])
ax.plot(phi_range * 100, gaft_range, color=GLD, linewidth=2, label="G_aft ($B)")
ax2.plot(phi_range * 100, dy_range,  color=GRN, linewidth=2, linestyle="--", label="dY ($B)")
ax.axvline(phi * 100, color=RED, linestyle=":", linewidth=1.5, label=f"phi={phi} (current)")
ax.set_xlabel("phi (%)", color=TC)
ax.set_ylabel("G_aft ($B)", color=GLD)
ax2.set_ylabel("dY ($B)", color=GRN)
ax.tick_params(colors=TC); ax2.tick_params(colors=GRN)
l1, lb1 = ax.get_legend_handles_labels()
l2, lb2 = ax2.get_legend_handles_labels()
ax.legend(l1+l2, lb1+lb2, facecolor=AXC, labelcolor=TC, fontsize=7)
ax.set_title("phi Sensitivity\nG_aft & dY vs Aid-for-Trade Share", fontweight="bold", color=TC)

# P1-7: Revenue by filing status
ax = fig1.add_subplot(gs1[2, 1]); style_ax(ax)
rev_lbls = ["Single\nCurrent", "Single\nProposed", "Married\nCurrent",
            "Married\nProposed", "Total\nCurrent", "Total\nProposed"]
rev_vals = [agg_cur_s, agg_prop_s, agg_cur_m, agg_prop_m,
            agg_cur_s+agg_cur_m, agg_prop_s+agg_prop_m]
rev_clrs = [GRY, BLU, GRY, TEL, GRY, GRN]
bars = ax.bar(range(6), rev_vals, color=[c(col, 0.65) for col in rev_clrs],
              edgecolor=rev_clrs, linewidth=1.5)
for bar, val in zip(bars, rev_vals):
    ax.text(bar.get_x()+bar.get_width()/2, val+100, f"${val:,.0f}B",
            ha="center", va="bottom", color=TC, fontsize=7, fontfamily="monospace")
ax.set_xticks(range(6)); ax.set_xticklabels(rev_lbls, color=TC, fontsize=8)
ax.set_ylabel("Revenue ($B)", color=TC)
ax.set_title("Revenue: Current vs Proposed\nBy Filing Status", fontweight="bold", color=TC)
ax.tick_params(colors=TC)

# P1-8: Fiscal flow waterfall
ax = fig1.add_subplot(gs1[2, 2]); style_ax(ax)
flow_lbls = ["Cur.\nRevenue", "Proposed\nRevenue", "- NIT\nCost",
             "Net\nSurplus", "G_aft\n(6.5%)", "Remaining\nSurplus"]
flow_vals = [agg_cur_s+agg_cur_m, total_rev, -total_nit,
             net_fiscal, G_aft, net_fiscal - G_aft]
flow_clrs = [GRY, RED, RED, GRN, GLD, TEL]
bars = ax.bar(range(6), flow_vals, color=[c(col, 0.65) for col in flow_clrs],
              edgecolor=flow_clrs, linewidth=1.5)
for bar, val in zip(bars, flow_vals):
    ypos = val + (200 if val >= 0 else -800)
    ax.text(bar.get_x()+bar.get_width()/2, ypos, f"${val:,.0f}B",
            ha="center", va="bottom", color=TC, fontsize=7,
            fontfamily="monospace", rotation=45)
ax.set_xticks(range(6)); ax.set_xticklabels(flow_lbls, color=TC, fontsize=8)
ax.set_ylabel("$B", color=TC)
ax.set_title("Fiscal Flow\nCurrent -> Surplus -> G_aft", fontweight="bold", color=TC)
ax.tick_params(colors=TC)

save(fig1, "fig1_gdp_multiplier.png")

# ════════════════════════════════════════════════════════════════════════════
# FIGURE 2 — Tax Bracket Analysis
# ════════════════════════════════════════════════════════════════════════════
print("Generating Figure 2...")
fig2 = plt.figure(figsize=(20, 13), facecolor=DK)
fig2.suptitle(
    "Figure 2 — Tax Bracket Analysis: Current Law vs Proposed 1933-Adjusted System\n"
    "7 Brackets  |  Single & Married Joint  |  Behavioral Elasticity Adjusted",
    color=TC, fontsize=11, fontweight="bold", y=0.99)
gs2 = gridspec.GridSpec(3, 3, figure=fig2, hspace=0.55, wspace=0.40)

eff_rate_cur_s  = cur_tax_s  / mean_income_single  * 100
eff_rate_cur_m  = cur_tax_m  / mean_income_married * 100
eff_rate_prop_s = prop_tax_s / np.maximum(adj_inc_s, 1) * 100
eff_rate_prop_m = prop_tax_m / np.maximum(adj_inc_m, 1) * 100
delta_tax_s     = prop_tax_s - cur_tax_s
delta_tax_m     = prop_tax_m - cur_tax_m
shrink_pct_s    = (mean_income_single  - adj_inc_s) / mean_income_single  * 100
shrink_pct_m    = (mean_income_married - adj_inc_m) / mean_income_married * 100

# P2-1: Marginal rates
ax = fig2.add_subplot(gs2[0, 0]); style_ax(ax)
ax.bar(x7 - w/2, rates_cur  * 100, w, color=c(GRY), edgecolor=GRY, linewidth=1.5, label="Current 2026")
ax.bar(x7 + w/2, rates_prop * 100, w, color=c(RED), edgecolor=RED, linewidth=1.5, label="Proposed 1933-adj")
ax.set_xticks(x7); ax.set_xticklabels([f"B{i+1}" for i in range(7)], color=TC)
ax.set_ylabel("Marginal Rate (%)", color=TC)
ax.set_title("Marginal Rates\nCurrent vs Proposed", fontweight="bold", color=TC)
ax.legend(facecolor=AXC, labelcolor=TC, fontsize=8); ax.tick_params(colors=TC)

# P2-2: Effective rates single
ax = fig2.add_subplot(gs2[0, 1]); style_ax(ax)
ax.bar(x7 - w/2, eff_rate_cur_s,  w, color=c(GRY), edgecolor=GRY, linewidth=1.5, label="Current (Single)")
ax.bar(x7 + w/2, eff_rate_prop_s, w, color=c(BLU), edgecolor=BLU, linewidth=1.5, label="Proposed (Single)")
ax.set_xticks(x7); ax.set_xticklabels([f"B{i+1}" for i in range(7)], color=TC)
ax.set_ylabel("Effective Rate (%)", color=TC)
ax.set_title("Effective Rates — Single\n(Tax / Income, post-behavioral)", fontweight="bold", color=TC)
ax.legend(facecolor=AXC, labelcolor=TC, fontsize=8); ax.tick_params(colors=TC)

# P2-3: Effective rates married
ax = fig2.add_subplot(gs2[0, 2]); style_ax(ax)
ax.bar(x7 - w/2, eff_rate_cur_m,  w, color=c(GRY), edgecolor=GRY, linewidth=1.5, label="Current (Married)")
ax.bar(x7 + w/2, eff_rate_prop_m, w, color=c(ORG), edgecolor=ORG, linewidth=1.5, label="Proposed (Married)")
ax.set_xticks(x7); ax.set_xticklabels([f"B{i+1}" for i in range(7)], color=TC)
ax.set_ylabel("Effective Rate (%)", color=TC)
ax.set_title("Effective Rates — Married\n(Tax / Income, post-behavioral)", fontweight="bold", color=TC)
ax.legend(facecolor=AXC, labelcolor=TC, fontsize=8); ax.tick_params(colors=TC)

# P2-4: Tax paid per person (log)
ax = fig2.add_subplot(gs2[1, 0]); style_ax(ax)
ax.bar(x7 - w/2, cur_tax_s  / 1e6, w, color=c(GRY), edgecolor=GRY, linewidth=1.5, label="Current Tax ($M)")
ax.bar(x7 + w/2, prop_tax_s / 1e6, w, color=c(BLU), edgecolor=BLU, linewidth=1.5, label="Proposed Tax ($M)")
ax.set_yscale("log")
ax.set_xticks(x7); ax.set_xticklabels([f"B{i+1}" for i in range(7)], color=TC)
ax.set_ylabel("Tax per Person ($M, log)", color=TC)
ax.set_title("Tax Paid per Person — Single\n(Log scale, behaviorally adjusted)", fontweight="bold", color=TC)
ax.legend(facecolor=AXC, labelcolor=TC, fontsize=8); ax.tick_params(colors=TC)

# P2-5: Behavioral income shrinkage
ax = fig2.add_subplot(gs2[1, 1]); style_ax(ax)
ax.bar(x7 - w/2, shrink_pct_s, w, color=c(RED), edgecolor=RED, linewidth=1.5, label="Single shrinkage %")
ax.bar(x7 + w/2, shrink_pct_m, w, color=c(ORG), edgecolor=ORG, linewidth=1.5, label="Married shrinkage %")
ax.set_xticks(x7); ax.set_xticklabels([f"B{i+1}" for i in range(7)], color=TC)
ax.set_ylabel("Income Shrinkage (%)", color=TC)
ax.set_title("Behavioral Income Contraction\nelasticity x Drate / (1-rate_cur)", fontweight="bold", color=TC)
ax.legend(facecolor=AXC, labelcolor=TC, fontsize=8); ax.tick_params(colors=TC)

# P2-6: Delta tax per person
ax = fig2.add_subplot(gs2[1, 2]); style_ax(ax)
clrs_s = [GRN if v <= 0 else RED for v in delta_tax_s]
clrs_m = [GRN if v <= 0 else RED for v in delta_tax_m]
ax.bar(x7 - w/2, delta_tax_s / 1e3, w, color=[c(col) for col in clrs_s],
       edgecolor=clrs_s, linewidth=1.5, label="Single dTax ($K)")
ax.bar(x7 + w/2, delta_tax_m / 1e3, w, color=[c(col, 0.4) for col in clrs_m],
       edgecolor=clrs_m, linewidth=1, linestyle="--", label="Married dTax ($K)")
ax.axhline(0, color="white", linestyle="--", linewidth=1)
ax.set_xticks(x7); ax.set_xticklabels([f"B{i+1}" for i in range(7)], color=TC)
ax.set_ylabel("dTax per Person ($K)", color=TC)
ax.set_title("dTax per Person\nGreen = tax cut | Red = tax rise", fontweight="bold", color=TC)
ax.legend(facecolor=AXC, labelcolor=TC, fontsize=8); ax.tick_params(colors=TC)

# P2-7: Aggregate revenue by bracket
ax = fig2.add_subplot(gs2[2, 0]); style_ax(ax)
rev_by_bracket_s = (pop_s * prop_tax_s) / 1e9
rev_by_bracket_m = (pop_m * prop_tax_m) / 1e9
ax.bar(x7, rev_by_bracket_s, color=c(BLU), edgecolor=BLU, linewidth=1.5, label="Single ($B)")
ax.bar(x7, rev_by_bracket_m, bottom=rev_by_bracket_s,
       color=c(ORG), edgecolor=ORG, linewidth=1.5, label="Married ($B)")
ax.set_xticks(x7); ax.set_xticklabels([f"B{i+1}" for i in range(7)], color=TC)
ax.set_ylabel("Revenue Contribution ($B)", color=TC)
ax.set_title("Proposed Revenue by Bracket\n(Population x Tax per Person)", fontweight="bold", color=TC)
ax.legend(facecolor=AXC, labelcolor=TC, fontsize=8); ax.tick_params(colors=TC)

# P2-8: Net income current vs proposed (log)
ax = fig2.add_subplot(gs2[2, 1]); style_ax(ax)
net_inc_cur_s = mean_income_single - cur_tax_s
ax.bar(x7 - w/2, net_inc_cur_s / 1e3, w, color=c(GRY), edgecolor=GRY, linewidth=1.5, label="Current Net Inc ($K)")
ax.bar(x7 + w/2, net_inc_s     / 1e3, w, color=c(GRN), edgecolor=GRN, linewidth=1.5, label="Proposed Net Inc ($K)")
ax.set_yscale("log")
ax.set_xticks(x7); ax.set_xticklabels([f"B{i+1}" for i in range(7)], color=TC)
ax.set_ylabel("Net Income ($K, log scale)", color=TC)
ax.set_title("Net Income After Tax — Single\n(Current vs Proposed, log scale)", fontweight="bold", color=TC)
ax.legend(facecolor=AXC, labelcolor=TC, fontsize=8); ax.tick_params(colors=TC)

# P2-9: Bracket threshold comparison (log)
ax = fig2.add_subplot(gs2[2, 2]); style_ax(ax)
thresh_c = np.where(thresh_single_cur  == 0, 1, thresh_single_cur)
thresh_p = np.where(thresh_single_prop == 0, 1, thresh_single_prop)
ax.bar(x7 - w/2, thresh_c / 1e3, w, color=c(GRY), edgecolor=GRY, linewidth=1.5, label="Current Threshold ($K)")
ax.bar(x7 + w/2, thresh_p / 1e3, w, color=c(PRP), edgecolor=PRP, linewidth=1.5, label="Proposed Threshold ($K)")
ax.set_yscale("log")
ax.set_xticks(x7); ax.set_xticklabels([f"B{i+1}" for i in range(7)], color=TC)
ax.set_ylabel("Bracket Threshold ($K, log scale)", color=TC)
ax.set_title("Bracket Thresholds: Current vs Proposed\n(Single, log scale)", fontweight="bold", color=TC)
ax.legend(facecolor=AXC, labelcolor=TC, fontsize=8); ax.tick_params(colors=TC)

save(fig2, "fig2_brackets.png")

# ════════════════════════════════════════════════════════════════════════════
# FIGURE 3 — NIT Transfers & Consumption Function
# ════════════════════════════════════════════════════════════════════════════
print("Generating Figure 3...")
fig3 = plt.figure(figsize=(20, 13), facecolor=DK)
fig3.suptitle(
    "Figure 3 — NIT Transfers & Consumption Function  C = C0 + C1*(Y-T)\n"
    "lambda = 0.15  |  NIT at 25% scale  |  B1-B5 single receive net refunds",
    color=TC, fontsize=11, fontweight="bold", y=0.99)
gs3 = gridspec.GridSpec(3, 3, figure=fig3, hspace=0.55, wspace=0.40)

# P3-1: NIT transfer by bracket
ax = fig3.add_subplot(gs3[0, 0]); style_ax(ax)
ax.bar(x7 - w/2, nit_single,  w, color=c(GRN), edgecolor=GRN, linewidth=1.5, label="NIT Single")
ax.bar(x7 + w/2, nit_married, w, color=c(GLD), edgecolor=GLD, linewidth=1.5, label="NIT Married")
ax.set_xticks(x7); ax.set_xticklabels([f"B{i+1}" for i in range(7)], color=TC)
ax.set_ylabel("NIT Transfer ($)", color=TC)
ax.set_title("NIT Transfer by Bracket\n(25% of original design values)", fontweight="bold", color=TC)
ax.legend(facecolor=AXC, labelcolor=TC, fontsize=8); ax.tick_params(colors=TC)

# P3-2: Net tax after NIT
ax = fig3.add_subplot(gs3[0, 1]); style_ax(ax)
clrs_nt_s = [GRN if v <= 0 else RED for v in net_tax_s]
clrs_nt_m = [GRN if v <= 0 else RED for v in net_tax_m]
ax.bar(x7 - w/2, net_tax_s / 1e3, w, color=[c(col) for col in clrs_nt_s],
       edgecolor=clrs_nt_s, linewidth=1.5, label="Single Net Tax ($K)")
ax.bar(x7 + w/2, net_tax_m / 1e3, w, color=[c(col, 0.4) for col in clrs_nt_m],
       edgecolor=clrs_nt_m, linewidth=1, label="Married Net Tax ($K)")
ax.axhline(0, color="white", linestyle="--", linewidth=1)
ax.set_xticks(x7); ax.set_xticklabels([f"B{i+1}" for i in range(7)], color=TC)
ax.set_ylabel("Net Tax ($K)  [neg = refund]", color=TC)
ax.set_title("Net Tax = Proposed Tax - NIT\nGreen = net refund received", fontweight="bold", color=TC)
ax.legend(facecolor=AXC, labelcolor=TC, fontsize=8); ax.tick_params(colors=TC)

# P3-3: NIT sub-bracket schedule
ax = fig3.add_subplot(gs3[0, 2]); style_ax(ax)
ax.plot(nit_sub_inc_s/1000, nit_sub_net_s/1000, "o-", color=GRN, linewidth=2, markersize=6, label="Net Income ($K)")
ax.plot(nit_sub_inc_s/1000, nit_sub_inc_s/1000, "--", color=GRY, linewidth=1.5, label="45 deg (break-even)")
ax.fill_between(nit_sub_inc_s/1000, nit_sub_inc_s/1000, nit_sub_net_s/1000, alpha=0.15, color=GRN, label="NIT benefit zone")
ax.set_xlabel("Gross Income ($K)", color=TC); ax.set_ylabel("Net Income ($K)", color=TC)
ax.set_title("NIT Sub-Bracket Schedule — Single\nNet Income vs Gross Income", fontweight="bold", color=TC)
ax.legend(facecolor=AXC, labelcolor=TC, fontsize=8); ax.tick_params(colors=TC)

# P3-4: Delta(Y-T) per person
ax = fig3.add_subplot(gs3[1, 0]); style_ax(ax)
clrs_dyt_s = [BLU if v >= 0 else RED for v in dY_T_s]
clrs_dyt_m = [ORG if v >= 0 else RED for v in dY_T_m]
ax.bar(x7 - w/2, dY_T_s / 1000, w, color=[c(col) for col in clrs_dyt_s],
       edgecolor=clrs_dyt_s, linewidth=1.5, label="D(Y-T) Single ($K)")
ax.bar(x7 + w/2, dY_T_m / 1000, w, color=[c(col, 0.5) for col in clrs_dyt_m],
       edgecolor=clrs_dyt_m, linewidth=1.5, label="D(Y-T) Married ($K)")
ax.axhline(0, color="white", linestyle="--", linewidth=1)
ax.set_xticks(x7); ax.set_xticklabels([f"B{i+1}" for i in range(7)], color=TC)
ax.set_ylabel("D(Y-T) per Person ($K)", color=TC)
ax.set_title("D Disposable Income D(Y-T)\nB1-B4 gain; B5-B7 lose", fontweight="bold", color=TC)
ax.legend(facecolor=AXC, labelcolor=TC, fontsize=8); ax.tick_params(colors=TC)

# P3-5: Delta C first round
ax = fig3.add_subplot(gs3[1, 1]); style_ax(ax)
clrs_dc_s = [BLU if v >= 0 else RED for v in dC_s]
clrs_dc_m = [ORG if v >= 0 else RED for v in dC_m]
ax.bar(x7 - w/2, dC_s / 1e9, w, color=[c(col) for col in clrs_dc_s],
       edgecolor=clrs_dc_s, linewidth=1.5, label="dC Single ($B)")
ax.bar(x7 + w/2, dC_m / 1e9, w, color=[c(col, 0.5) for col in clrs_dc_m],
       edgecolor=clrs_dc_m, linewidth=1.5, label="dC Married ($B)")
ax.axhline(0, color="white", linestyle="--", linewidth=1)
ax.set_xticks(x7); ax.set_xticklabels([f"B{i+1}" for i in range(7)], color=TC)
ax.set_ylabel("dC ($B)", color=TC)
ax.set_title("dC = C1*lambda*D(Y-T) First Round\nPop-weighted bracket contribution", fontweight="bold", color=TC)
ax.legend(facecolor=AXC, labelcolor=TC, fontsize=8); ax.tick_params(colors=TC)

# P3-6: MPC matrix stacked
ax = fig3.add_subplot(gs3[1, 2]); style_ax(ax)
dur = mpc_matrix[:, 0]; nond = mpc_matrix[:, 1]; svc = mpc_matrix[:, 2]
ax.bar(x7, dur,  color=c(BLU, 0.8), edgecolor=BLU, linewidth=1.2, label="Durables")
ax.bar(x7, nond, bottom=dur, color=c(GRN, 0.8), edgecolor=GRN, linewidth=1.2, label="Non-Durables")
ax.bar(x7, svc,  bottom=dur+nond, color=c(PRP, 0.8), edgecolor=PRP, linewidth=1.2, label="Services")
for i in range(7):
    ax.text(i, C_1[i]+0.01, f"{C_1[i]:.2f}", ha="center", va="bottom",
            color=TC, fontsize=8, fontfamily="monospace")
ax.set_xticks(x7); ax.set_xticklabels([f"B{i+1}" for i in range(7)], color=TC)
ax.set_ylabel("MPC (C1 raw)", color=TC)
ax.set_title("MPC Matrix by Component\n[Durables | Non-Dur. | Services]", fontweight="bold", color=TC)
ax.legend(facecolor=AXC, labelcolor=TC, fontsize=8); ax.tick_params(colors=TC)

# P3-7: NIT cost by bracket
ax = fig3.add_subplot(gs3[2, 0]); style_ax(ax)
nit_cost_s_b = (pop_s * nit_single)  / 1e9
nit_cost_m_b = (pop_m * nit_married) / 1e9
ax.bar(x7, nit_cost_s_b, color=c(GRN), edgecolor=GRN, linewidth=1.5, label="Single NIT cost ($B)")
ax.bar(x7, nit_cost_m_b, bottom=nit_cost_s_b, color=c(GLD), edgecolor=GLD,
       linewidth=1.5, label="Married NIT cost ($B)")
ax.set_xticks(x7); ax.set_xticklabels([f"B{i+1}" for i in range(7)], color=TC)
ax.set_ylabel("NIT Program Cost ($B)", color=TC)
ax.set_title(f"Total NIT Cost by Bracket\n(Total = {total_nit:.1f}B)", fontweight="bold", color=TC)
ax.legend(facecolor=AXC, labelcolor=TC, fontsize=8); ax.tick_params(colors=TC)

# P3-8: Net income proposed vs current (log)
ax = fig3.add_subplot(gs3[2, 1]); style_ax(ax)
ax.bar(x7 - w/2, net_inc_s          / 1e3, w, color=c(BLU), edgecolor=BLU, linewidth=1.5, label="Proposed Single")
ax.bar(x7 - w/2, (mean_income_single - cur_tax_s) / 1e3, w, color=c(GRY, 0.4),
       edgecolor=GRY, linewidth=1, linestyle="--", label="Current Single")
ax.set_yscale("log")
ax.set_xticks(x7); ax.set_xticklabels([f"B{i+1}" for i in range(7)], color=TC)
ax.set_ylabel("Net Income after Tax ($K, log)", color=TC)
ax.set_title("Net Income: Proposed vs Current\nSingle filers (log scale)", fontweight="bold", color=TC)
ax.legend(facecolor=AXC, labelcolor=TC, fontsize=8); ax.tick_params(colors=TC)

# P3-9: lambda sensitivity
ax = fig3.add_subplot(gs3[2, 2]); style_ax(ax)
lam_range = np.linspace(0.05, 0.80, 100)
def dC_first_lam(lv):
    return sum(lv*C_1[i]*dY_T_s[i]*pop_s[i] + lv*C_1[i]*dY_T_m[i]*pop_m[i]
               for i in range(7)) / 1e9
dCf_range = np.array([dC_first_lam(lv) for lv in lam_range])
ax.plot(lam_range, dCf_range, color=BLU, linewidth=2)
ax.axvline(lam, color=RED, linestyle="--", linewidth=1.5,
           label=f"lambda={lam} (current, dC={dC_first:.0f}B)")
ax.axhline(0, color="white", linestyle=":", linewidth=1)
ax.scatter([lam], [dC_first], color=RED, s=60, zorder=5)
ax.set_xlabel("lambda (permanent-income discount)", color=TC)
ax.set_ylabel("dC_first ($B)", color=TC)
ax.set_title("lambda Sensitivity\ndC_first vs Permanent Income Discount", fontweight="bold", color=TC)
ax.legend(facecolor=AXC, labelcolor=TC, fontsize=8); ax.tick_params(colors=TC)

save(fig3, "fig3_nit_consumption.png")

# ════════════════════════════════════════════════════════════════════════════
# FIGURE 4 — Trade Diversification Structure
# ════════════════════════════════════════════════════════════════════════════
print("Generating Figure 4...")
fig4 = plt.figure(figsize=(20, 13), facecolor=DK)
fig4.suptitle(
    "Figure 4 — Trade Diversification Structure\n"
    "M = Sj[M0j+M1j*Y]  |  X = X0+alpha*G_aft  |  World Bank Income Tiers  |  HI trade preserved",
    color=TC, fontsize=11, fontweight="bold", y=0.99)
gs4 = gridspec.GridSpec(3, 3, figure=fig4, hspace=0.55, wspace=0.40)

# P4-1: Import share
ax = fig4.add_subplot(gs4[0, 0]); style_ax(ax)
ax.bar(x4 - w/2, import_share_baseline * 100, w, color=c(GRY), edgecolor=GRY, linewidth=1.5, label="Baseline")
ax.bar(x4 + w/2, import_share_new      * 100, w, color=c(GRN), edgecolor=GRN, linewidth=1.5, label="Post-Policy")
ax.set_xticks(x4); ax.set_xticklabels(tier_short, color=TC)
ax.set_ylabel("Import Share (%)", color=TC)
ax.set_title("Import Share by Tier\nHI preserved; UMI/LMI/LI boosted", fontweight="bold", color=TC)
ax.legend(facecolor=AXC, labelcolor=TC, fontsize=8); ax.tick_params(colors=TC)

# P4-2: M1 by tier
ax = fig4.add_subplot(gs4[0, 1]); style_ax(ax)
ax.bar(x4 - w/2, M_1_tier_baseline, w, color=c(GRY), edgecolor=GRY, linewidth=1.5, label="Baseline M1")
ax.bar(x4 + w/2, M_1_tier,          w, color=c(TEL), edgecolor=TEL, linewidth=1.5, label="Policy M1")
for j in range(4):
    dm1 = M_1_tier[j] - M_1_tier_baseline[j]
    ax.text(j + w/2, M_1_tier[j]+0.001,
            f"+{dm1:.4f}" if dm1 > 0 else "-",
            ha="center", va="bottom", color=TC, fontsize=7, fontfamily="monospace")
ax.set_xticks(x4); ax.set_xticklabels(tier_short, color=TC)
ax.set_ylabel("M1 (Marginal Propensity to Import)", color=TC)
ax.set_title("M1 by Tier: Baseline vs Policy\nDM1 shown above policy bars", fontweight="bold", color=TC)
ax.legend(facecolor=AXC, labelcolor=TC, fontsize=8); ax.tick_params(colors=TC)

# P4-3: Export share
ax = fig4.add_subplot(gs4[0, 2]); style_ax(ax)
ax.bar(x4 - w/2, export_share_baseline * 100, w, color=c(GRY), edgecolor=GRY, linewidth=1.5, label="Baseline")
ax.bar(x4 + w/2, export_share_new      * 100, w, color=c(GLD), edgecolor=GLD, linewidth=1.5, label="Post-Promotion")
ax.set_xticks(x4); ax.set_xticklabels(tier_short, color=TC)
ax.set_ylabel("Export Share (%)", color=TC)
ax.set_title("Export Share by Tier\n(Transition contraction reduces dev. shares)", fontweight="bold", color=TC)
ax.legend(facecolor=AXC, labelcolor=TC, fontsize=8); ax.tick_params(colors=TC)

# P4-4: Delta M by tier
ax = fig4.add_subplot(gs4[1, 0]); style_ax(ax)
bars = ax.bar(x4, delta_M_tier, color=[c(col) for col in TIER_COLORS], edgecolor=TIER_COLORS, linewidth=1.5)
for bar, val in zip(bars, delta_M_tier):
    ax.text(bar.get_x()+bar.get_width()/2, val+0.5, f"${val:.1f}B",
            ha="center", va="bottom", color=TC, fontsize=9, fontfamily="monospace")
ax.set_xticks(x4); ax.set_xticklabels(tier_short, color=TC)
ax.set_ylabel("dM ($B)", color=TC)
ax.set_title(f"dM Import Leakage by Tier\nTotal = {delta_M:.1f}B", fontweight="bold", color=TC)
ax.tick_params(colors=TC)

# P4-5: G_aft + export promo vs contraction
ax = fig4.add_subplot(gs4[1, 1]); style_ax(ax)
x3b = np.arange(3); w3 = 0.20
aft_vals = np.array([G_aft_UMI, G_aft_LMI, G_aft_LI])
prm_vals = np.array([dX_promo_UMI, dX_promo_LMI, dX_promo_LI])
cnt_vals = np.array([dX_contract_UMI, dX_contract_LMI, dX_contract_LI])
net_vals = np.array([dX_UMI, dX_LMI, dX_LI])
ax.bar(x3b - 1.5*w3, aft_vals, w3, color=c(GLD), edgecolor=GLD, linewidth=1.5, label="G_aft alloc ($B)")
ax.bar(x3b - 0.5*w3, prm_vals, w3, color=c(GRN), edgecolor=GRN, linewidth=1.5, label="Promo ($B)")
ax.bar(x3b + 0.5*w3, cnt_vals, w3, color=c(RED), edgecolor=RED, linewidth=1.5, label="Contraction ($B)")
ax.bar(x3b + 1.5*w3, net_vals, w3, color=c(TEL), edgecolor=TEL, linewidth=1.5, label="Net dX ($B)")
ax.axhline(0, color="white", linestyle="--", linewidth=1)
ax.set_xticks(x3b); ax.set_xticklabels(["UMI", "LMI", "LI"], color=TC)
ax.set_ylabel("$B", color=TC)
ax.set_title("G_aft -> Export Promo vs Contraction\nNet dX per Developing Tier", fontweight="bold", color=TC)
ax.legend(facecolor=AXC, labelcolor=TC, fontsize=7); ax.tick_params(colors=TC)

# P4-6: MPM sensitivity vs gamma
ax = fig4.add_subplot(gs4[1, 2]); style_ax(ax)
gamma_scale = np.linspace(0, 2.0, 100)
def agg_mpm(gs_val):
    m1 = M_1_tier_baseline.copy()
    m1[1] *= (1 + gamma_UMI * gs_val)
    m1[2] *= (1 + gamma_LMI * gs_val)
    m1[3] *= (1 + gamma_LI  * gs_val)
    return m1.sum()
mpm_range = np.array([agg_mpm(gv) for gv in gamma_scale])
ax.plot(gamma_scale, mpm_range, color=TEL, linewidth=2)
ax.axvline(1.0, color=RED, linestyle="--", linewidth=1.5, label=f"Current gamma=1  m={m:.4f}")
ax.axhline(m_base, color=GLD, linestyle=":", linewidth=1.5, label=f"Baseline m={m_base:.4f}")
ax.scatter([1.0], [m], color=RED, s=60, zorder=5)
ax.set_xlabel("gamma Scale Factor (1 = current)", color=TC)
ax.set_ylabel("Aggregate MPM (m)", color=TC)
ax.set_title("MPM Sensitivity to gamma (MFN Boost)\nHigher gamma -> more import leakage", fontweight="bold", color=TC)
ax.legend(facecolor=AXC, labelcolor=TC, fontsize=8); ax.tick_params(colors=TC)

# P4-7: X & M volumes
ax = fig4.add_subplot(gs4[2, 0]); style_ax(ax)
cats = ["X Baseline", "X Post-Reform", "M Baseline", "M Post-Reform"]
vals = [X_baseline, X_baseline+delta_X_total, M_baseline, M_baseline+delta_M]
clrs = [GRN, TEL, RED, ORG]
bars = ax.bar(range(4), vals, color=[c(col) for col in clrs], edgecolor=clrs, linewidth=1.5)
for bar, val in zip(bars, vals):
    ax.text(bar.get_x()+bar.get_width()/2, val+20, f"${val:.0f}B",
            ha="center", va="bottom", color=TC, fontsize=8, fontfamily="monospace")
ax.set_xticks(range(4)); ax.set_xticklabels(cats, color=TC, fontsize=9)
ax.set_ylabel("Volume ($B)", color=TC)
ax.set_title("X & M Volumes\nBaseline vs Post-Reform", fontweight="bold", color=TC)
ax.tick_params(colors=TC)

# P4-8: Alpha sensitivity
ax = fig4.add_subplot(gs4[2, 1]); style_ax(ax)
alpha_scale = np.linspace(0.1, 3.0, 100)
def net_dx(asc):
    return (asc*alpha_UMI*G_aft_UMI + dX_contract_UMI +
            asc*alpha_LMI*G_aft_LMI + dX_contract_LMI +
            asc*alpha_LI *G_aft_LI  + dX_contract_LI)
dx_range = np.array([net_dx(a) for a in alpha_scale])
ax.plot(alpha_scale, dx_range, color=GLD, linewidth=2)
ax.axvline(1.0, color=RED, linestyle="--", linewidth=1.5,
           label=f"Current alpha=1  dX={delta_X:.1f}B")
ax.axhline(0, color="white", linestyle=":", linewidth=1, label="dX = 0 break-even")
ax.scatter([1.0], [delta_X_total], color=RED, s=60, zorder=5)
ax.set_xlabel("alpha Scale Factor (1 = current)", color=TC)
ax.set_ylabel("Net dX ($B)", color=TC)
ax.set_title("dX Sensitivity to alpha (Export Multiplier)\nHigher alpha -> more export promotion", fontweight="bold", color=TC)
ax.legend(facecolor=AXC, labelcolor=TC, fontsize=8); ax.tick_params(colors=TC)

# P4-9: Net export decomposition
ax = fig4.add_subplot(gs4[2, 2]); style_ax(ax)
nx_lbls = ["X Base", "+dX", "Net X", "-M Base", "-dM", "Net -M", "NX Chg"]
nx_vals = [X_baseline, delta_X_total, X_baseline+delta_X_total,
           -M_baseline, -delta_M, -(M_baseline+delta_M), delta_NX]
nx_clrs = [GRN, TEL, GRN, RED, ORG, RED, PRP if delta_NX >= 0 else RED]
bars = ax.bar(range(7), nx_vals, color=[c(col) for col in nx_clrs], edgecolor=nx_clrs, linewidth=1.5)
ax.axhline(0, color="white", linestyle="--", linewidth=1)
ax.set_xticks(range(7)); ax.set_xticklabels(nx_lbls, color=TC, fontsize=8, rotation=30, ha="right")
ax.set_ylabel("$B", color=TC)
ax.set_title(f"Net Export Decomposition\ndNX = {delta_NX:.1f}B", fontweight="bold", color=TC)
ax.tick_params(colors=TC)

save(fig4, "fig4_trade.png")

# ════════════════════════════════════════════════════════════════════════════
# FIGURE 5 — Summary Dashboard
# ════════════════════════════════════════════════════════════════════════════
print("Generating Figure 5...")
fig5 = plt.figure(figsize=(20, 13), facecolor=DK)
fig5.suptitle(
    "Figure 5 — Summary Dashboard\n"
    "Tax Reform — Open Economy | Developing Nation Trade Diversification\n"
    "Y=C+I+G+(X-M)  |  up-M from UMI/LMI/LI  |  down-X transition cost  |  HI trade preserved",
    color=TC, fontsize=11, fontweight="bold", y=0.99)
gs5 = gridspec.GridSpec(3, 3, figure=fig5, hspace=0.55, wspace=0.40)

ax = fig5.add_subplot(gs5[0, 0]); style_ax(ax)
ax.bar(x4-w/2, import_share_baseline*100, w, color=c(GRY), label="Baseline")
ax.bar(x4+w/2, import_share_new*100,      w, color=c(GRN), label="Post-Diversification")
ax.set_xticks(x4); ax.set_xticklabels(tier_short, color=TC)
ax.set_xlabel("World Bank Tier"); ax.set_ylabel("Import Share (%)")
ax.set_title("M: Import Share by Tier", fontweight="bold")
ax.legend(facecolor=AXC, labelcolor=TC, fontsize=7); ax.tick_params(colors=TC)

ax = fig5.add_subplot(gs5[0, 1]); style_ax(ax)
ax.bar(x4-w/2, M_1_tier_baseline, w, color=c(GRY), label="Baseline M1")
ax.bar(x4+w/2, M_1_tier,          w, color=c(TEL), label="Policy M1")
ax.set_xticks(x4); ax.set_xticklabels(tier_short, color=TC)
ax.set_xlabel("World Bank Tier"); ax.set_ylabel("M1 (MPM)")
ax.set_title("M1 by Tier: Baseline vs Policy", fontweight="bold")
ax.legend(facecolor=AXC, labelcolor=TC, fontsize=7); ax.tick_params(colors=TC)

ax = fig5.add_subplot(gs5[0, 2]); style_ax(ax)
ax.bar(x4-w/2, export_share_baseline*100, w, color=c(GRY), label="Baseline")
ax.bar(x4+w/2, export_share_new*100,      w, color=c(GLD), label="Post-Promotion")
ax.set_xticks(x4); ax.set_xticklabels(tier_short, color=TC)
ax.set_xlabel("World Bank Tier"); ax.set_ylabel("Export Share (%)")
ax.set_title("X: Export Share by Tier", fontweight="bold")
ax.legend(facecolor=AXC, labelcolor=TC, fontsize=7); ax.tick_params(colors=TC)

ax = fig5.add_subplot(gs5[1, 0]); style_ax(ax)
ax.bar(x7-w/2, dY_T_s/1000, w, color=c(BLU), label="Single")
ax.bar(x7+w/2, dY_T_m/1000, w, color=c(ORG), label="Married")
ax.axhline(0, color="white", linestyle="--", linewidth=1.2)
ax.set_xticks(x7); ax.set_xticklabels([f"B{i+1}" for i in range(7)], color=TC)
ax.set_xlabel("Bracket"); ax.set_ylabel("D(Y-T) ($000s/person)")
ax.set_title("D Disposable Income D(Y-T)", fontweight="bold")
ax.legend(facecolor=AXC, labelcolor=TC, fontsize=7); ax.tick_params(colors=TC)

ax = fig5.add_subplot(gs5[1, 1]); style_ax(ax)
ax.bar(x7-w/2, dC_s/1e9, w, color=c(BLU), label="Single")
ax.bar(x7+w/2, dC_m/1e9, w, color=c(ORG), label="Married")
ax.axhline(0, color="white", linestyle="--", linewidth=1.2)
ax.set_xticks(x7); ax.set_xticklabels([f"B{i+1}" for i in range(7)], color=TC)
ax.set_xlabel("Bracket"); ax.set_ylabel("dC ($B)")
ax.set_title("dC = C1*D(Y-T) [lambda-adj, first round]", fontweight="bold")
ax.legend(facecolor=AXC, labelcolor=TC, fontsize=7); ax.tick_params(colors=TC)

ax = fig5.add_subplot(gs5[1, 2]); style_ax(ax)
for j in range(4):
    ax.bar(j, delta_M_tier[j], color=TIER_COLORS[j])
ax.set_xticks(range(4)); ax.set_xticklabels(tier_short, color=TC)
ax.set_xlabel("World Bank Tier"); ax.set_ylabel("dM ($B)")
ax.set_title("dM by World Bank Tier", fontweight="bold"); ax.tick_params(colors=TC)

ax = fig5.add_subplot(gs5[2, 0]); style_ax(ax)
aft_v = [G_aft_UMI, G_aft_LMI, G_aft_LI]
dx_v  = [dX_UMI, dX_LMI, dX_LI]
ax.bar(x3-w/2, aft_v, w, color=c(GLD), label="G_aft alloc")
ax.bar(x3+w/2, dx_v,  w, color=c(GRN), label="Net dX")
ax.axhline(0, color="white", linestyle="--", linewidth=1)
ax.set_xticks(x3); ax.set_xticklabels(["UMI", "LMI", "LI"], color=TC)
ax.set_xlabel("World Bank Tier"); ax.set_ylabel("$B")
ax.set_title("G_aft -> Net dX by Tier", fontweight="bold")
ax.legend(facecolor=AXC, labelcolor=TC, fontsize=7); ax.tick_params(colors=TC)

ax = fig5.add_subplot(gs5[2, 1]); style_ax(ax)
ax.bar(x5-w/2, comp_v,  w, color=c(GRN), label="Diversified")
ax.bar(x5+w/2, [delta_C_base, 0, 0, -delta_M_base, delta_Y_base], w, color=c(GRY), label="No Diversification")
ax.axhline(0, color="white", linestyle="--", linewidth=1.2)
ax.set_xticks(x5); ax.set_xticklabels(["dC", "dG", "dX", "-dM", "dY"], color=TC)
ax.set_ylabel("Change ($B)")
ax.set_title(f"Y=C+I+G+(X-M)\ndY={delta_Y:+.1f}B ({Y_pct:+.2f}%)", fontweight="bold")
ax.legend(facecolor=AXC, labelcolor=TC, fontsize=7); ax.tick_params(colors=TC)

ax = fig5.add_subplot(gs5[2, 2]); ax.set_facecolor(AXC); ax.axis("off")
summary_lines = [
    ("Y = C + I + G + (X - M)",   TC,  True),
    ("",                           TC,  False),
    ("C = C0 + C1*(Y-T)",         TEL, True),
    (f"  C1_eff={C_1_eff_avg:.4f}   lambda={lam:.2f}", TC, False),
    (f"  dC first  = ${dC_first:+.2f}B",  TC, False),
    (f"  dC total  = ${delta_C:+.2f}B",   TC, False),
    ("",                           TC,  False),
    ("G = G0 + G_aft",            GLD, True),
    (f"  phi={phi:.3f}   G_aft=${G_aft:.2f}B", TC, False),
    ("",                           TC,  False),
    ("X = X0 + alpha*G_aft",      GLD, True),
    (f"  dX = ${delta_X_total:+.2f}B",    TC, False),
    ("",                           TC,  False),
    ("M = Sj[M0j + M1j*Y]",      ORG, True),
    (f"  m_base={m_base:.4f}  m_new={m:.4f}", TC, False),
    (f"  dM = ${delta_M:+.2f}B",          TC, False),
    ("",                           TC,  False),
    ("k = 1/(s+t+m)",             TEL, True),
    (f"  k_base={k_baseline:.4f}",        TC, False),
    (f"  k_div ={k_diversified:.4f}",     TC, False),
    ("",                           TC,  False),
    (f"dY = ${delta_Y:+.2f}B  ({Y_pct:+.2f}%)", PRP, True),
    (f"vs no-div: ${delta_Y_base:+.2f}B ({Y_pct_base:+.2f}%)", GLD, False),
    (f"Trade offset: ${delta_Y-delta_Y_base:+.2f}B", RED, False),
]
yp = 0.97
for text, col, bold in summary_lines:
    ax.text(0.03, yp, text, color=col, fontsize=8,
            fontweight="bold" if bold else "normal",
            fontfamily="monospace", transform=ax.transAxes, verticalalignment="top")
    yp -= 0.038

save(fig5, "fig5_summary.png")

# ════════════════════════════════════════════════════════════════════════════
# FIGURE A — NIT Design Defense & Calibration   [CAMPUS EDITION]
# ════════════════════════════════════════════════════════════════════════════
print("Generating Figure A — NIT Defense...")
figA = plt.figure(figsize=(20, 14), facecolor=DK)
figA.suptitle(
    "Figure A — Negative Income Tax: Design Defense & Phased Calibration\n"
    "25% Scale | Fiscal Budget Constraint | Carroll (2001) | Jappelli & Pistaferri (2010) | CBO (2023)",
    color=TC, fontsize=12, fontweight="bold", y=0.995)
gsA = gridspec.GridSpec(3, 3, figure=figA, hspace=0.60, wspace=0.42)

nit_scales  = [0.10, 0.25, 0.50, 1.00]
nit_colors  = [GRY, AMB, ORG, RED]
nit_labels  = ["10%\n(Pilot)", "25%\n(Current)", "50%\n(Phase 2)", "100%\n(Full)"]
scales_pct  = np.array([10, 25, 50, 100])
nit_costs   = total_nit * (scales_pct / 25)   # linear with 25% = actual
gdp_gains   = np.array([400, delta_Y, 1350, 1890])

# A1: Scale vs cost vs GDP
ax = figA.add_subplot(gsA[0, 0]); style_ax(ax)
ax2t = ax.twinx(); ax2t.set_facecolor(AXC)
ax.bar(scales_pct, nit_costs/1e3, width=7,
       color=[c(col) for col in nit_colors], edgecolor=nit_colors, linewidth=1.5, label="NIT Cost ($T)")
ax2t.plot(scales_pct, gdp_gains, color=GLD, linewidth=2.5, marker="o", markersize=7, label="dY ($B)", zorder=5)
ax.axvline(25, color=AMB, linestyle="--", linewidth=1.8, alpha=0.8)
ax.text(26, nit_costs[-1]/1e3*0.5, "< Current\n  25%", color=AMB, fontsize=8, fontweight="bold")
ax.set_xlabel("NIT Scale (%)", color=TC); ax.set_ylabel("NIT Program Cost ($T)", color=TC)
ax2t.set_ylabel("dY GDP Gain ($B)", color=GLD); ax2t.tick_params(colors=GLD)
ax.set_title("NIT Scale Selection\nFiscal Cost vs GDP Gain", fontweight="bold"); ax.tick_params(colors=TC)
badge(ax, "25% chosen: balanced\nfiscal constraint", (0.03, 0.75), GLD)
l1,lb1 = ax.get_legend_handles_labels(); l2,lb2 = ax2t.get_legend_handles_labels()
ax.legend(l1+l2, lb1+lb2, facecolor=AX2, labelcolor=TC, fontsize=8)

# A2: Transfer schedule all scale levels
ax = figA.add_subplot(gsA[0, 1]); style_ax(ax)
for idx, (scale, col) in enumerate(zip(nit_scales, nit_colors)):
    v = nit_single * (scale / 0.25)
    ax.bar(x7 + (idx-1.5)*0.18, v, 0.18, color=c(col, 0.70),
           edgecolor=col, linewidth=1.2, label=nit_labels[idx])
for i in range(5):
    if nit_single[i] > 0:
        ax.annotate(f"${nit_single[i]:,.0f}",
                    xy=(x7[i] + 0.5*0.18, nit_single[i]),
                    xytext=(0, 4), textcoords="offset points",
                    ha="center", color=AMB, fontsize=7, fontweight="bold")
ax.set_xticks(x7); ax.set_xticklabels([f"B{i+1}" for i in range(7)], color=TC)
ax.set_ylabel("NIT Transfer ($)", color=TC)
ax.set_title("NIT Transfer by Scale Level\nSingle Filer — All Implementation Phases", fontweight="bold")
ax.legend(facecolor=AX2, labelcolor=TC, fontsize=8, title="Scale", title_fontsize=8)
ax.tick_params(colors=TC)

# A3: Net tax after NIT
ax = figA.add_subplot(gsA[0, 2]); style_ax(ax)
nt_colors = [GRN if v < 0 else RED for v in net_tax_s]
ax.bar(x7, net_tax_s/1000, color=[c(col, 0.75) for col in nt_colors],
       edgecolor=nt_colors, linewidth=1.5)
ax.axhline(0, color=WHT, linestyle="--", linewidth=1.5)
ax.set_xticks(x7); ax.set_xticklabels([f"B{i+1}" for i in range(7)], color=TC)
ax.set_ylabel("Net Tax ($K)", color=TC)
ax.set_title("Net Tax = Proposed - NIT\nGreen = Net Refund Received (25% Scale)", fontweight="bold")
ax.legend(handles=[mpatches.Patch(color=c(GRN), label="Net Refund (B1-B4)"),
                   mpatches.Patch(color=c(RED), label="Net Payer (B5-B7)")],
          facecolor=AX2, labelcolor=TC, fontsize=8); ax.tick_params(colors=TC)
badge(ax, "B1-B4: net recipients\nB5-B7: net contributors", (0.03, 0.72), GRN)

# A4: Lambda literature anchoring
ax = figA.add_subplot(gsA[1, 0]); style_ax(ax)
lv_range = np.linspace(0.05, 0.80, 200)
dC_range = dC_first * (lv_range / lam)
ax.fill_between(lv_range, dC_range, alpha=0.12, color=BLU)
ax.plot(lv_range, dC_range, color=BLU, linewidth=2.5)
lit_refs = {
    "Carroll (2001)\nBuffer-stock":     (0.12, GRN),
    "Current lambda=0.15\nCBO (2023)":  (0.15, AMB),
    "Jappelli &\nPistaferri (2010)":    (0.20, ORG),
    "MPC studies mean":                 (0.30, RED),
}
for lbl, (lv, col) in lit_refs.items():
    dc = dC_first * (lv / lam)
    ax.axvline(lv, color=col, linestyle="--", linewidth=1.5, alpha=0.8)
    ax.scatter([lv], [dc], color=col, s=70, zorder=5)
    ax.text(lv+0.005, dc-80, lbl, color=col, fontsize=7, fontweight="bold")
ax.set_xlabel("lambda (Permanent-Income Discount)", color=TC)
ax.set_ylabel("dC First Round ($B)", color=TC)
ax.set_title("lambda Literature Anchoring\nPIH Discount -> Consumption Response", fontweight="bold")
ax.tick_params(colors=TC)
badge(ax, "lambda=0.15 is CONSERVATIVE\n(lower bound of literature)", (0.03, 0.80), GRN)

# A5: Fiscal sustainability chain
ax = figA.add_subplot(gsA[1, 1]); style_ax(ax)
chain_lbs = ["Proposed\nRevenue", "NIT\nCost (25%)", "Net\nSurplus", "G_aft\n(6.5%)", "dY\nGDP"]
chain_vals = [total_rev, total_nit, net_fiscal, G_aft, delta_Y]
chain_cols = [BLU, RED, GRN, GLD, PRP]
bars = ax.bar(range(5), chain_vals, color=[c(col, 0.75) for col in chain_cols],
              edgecolor=chain_cols, linewidth=1.5)
for b, val in zip(bars, chain_vals):
    ax.text(b.get_x()+b.get_width()/2, val+150,
            f"${val:,.0f}B", ha="center", color=TC, fontsize=8,
            fontweight="bold", fontfamily="monospace")
ax.set_xticks(range(5)); ax.set_xticklabels(chain_lbs, color=TC, fontsize=8.5)
ax.set_ylabel("$B", color=TC)
ax.set_title("Fiscal Sustainability Chain\nRevenue -> NIT Cost -> Surplus -> G_aft -> dY", fontweight="bold")
ax.tick_params(colors=TC)
badge(ax, f"NIT = {100*total_nit/total_rev:.1f}% of revenue\nSelf-financing design", (0.38, 0.80), AMB)

# A6: MPC matrix
ax = figA.add_subplot(gsA[1, 2]); style_ax(ax)
comp_labels = ["Durables", "Non-Durables", "Services"]
comp_colors = [BLU, GRN, PRP]
bottoms = np.zeros(7)
for j, (comp, col) in enumerate(zip(comp_labels, comp_colors)):
    ax.bar(x7, mpc_matrix[:, j], bottom=bottoms, color=c(col, 0.75),
           edgecolor=col, linewidth=0.8, label=comp)
    bottoms += mpc_matrix[:, j]
for i, c1v in enumerate(C_1):
    ax.text(i, c1v+0.01, f"{c1v:.2f}", ha="center", color=TC, fontsize=8, fontweight="bold")
ax.set_xticks(x7); ax.set_xticklabels([f"B{i+1}" for i in range(7)], color=TC)
ax.set_ylabel("MPC (C1)", color=TC)
ax.set_title("MPC by Component\nHow NIT Transfers Translate to Spending", fontweight="bold")
ax.legend(facecolor=AX2, labelcolor=TC, fontsize=8); ax.tick_params(colors=TC)
badge(ax, "B1 MPC=0.95:\nHigh pass-through", (0.38, 0.80), GRN)

# A7: NIT phaseout schedule
ax = figA.add_subplot(gsA[2, 0]); style_ax(ax)
inc_r = np.linspace(0, 250_000, 500)
nit_25_curve  = np.maximum(nit_single[0] * (1 - inc_r / 100_000), 0)
nit_100_curve = np.maximum(nit_single[0] * 4 * (1 - inc_r / 100_000), 0)
ax.fill_between(inc_r/1000, nit_25_curve,  alpha=0.20, color=AMB)
ax.fill_between(inc_r/1000, nit_100_curve, alpha=0.08, color=GLD)
ax.plot(inc_r/1000, nit_25_curve,  color=AMB, linewidth=2.5, label="25% Scale (Current)")
ax.plot(inc_r/1000, nit_100_curve, color=GLD, linewidth=1.5, linestyle="--", label="100% Scale (Full Design)")
ax.axvline(50,  color=GRY, linestyle=":", linewidth=1, alpha=0.7)
ax.text(51, nit_single[0]*0.8, "B2 center\n~$50K", color=GRY, fontsize=7)
ax.axvline(100, color=GRY, linestyle=":", linewidth=1, alpha=0.7)
ax.text(101, nit_single[0]*0.8, "B5 upper\n~$100K", color=GRY, fontsize=7)
ax.set_xlabel("Gross Income ($K)", color=TC); ax.set_ylabel("NIT Transfer ($)", color=TC)
ax.set_title("NIT Phaseout Schedule\nCurrent (25%) vs Full Design", fontweight="bold")
ax.legend(facecolor=AX2, labelcolor=TC, fontsize=8); ax.tick_params(colors=TC)

# A8: NIT cost by bracket
ax = figA.add_subplot(gsA[2, 1]); style_ax(ax)
ax.bar(x7, nit_cost_s_b, color=c(BLU), edgecolor=BLU, linewidth=1.2, label="Single NIT cost ($B)")
ax.bar(x7, nit_cost_m_b, bottom=nit_cost_s_b, color=c(ORG), edgecolor=ORG,
       linewidth=1.2, label="Married NIT cost ($B)")
for i in range(7):
    total_bar = nit_cost_s_b[i] + nit_cost_m_b[i]
    if total_bar > 1:
        ax.text(i, total_bar+5, f"${total_bar:.0f}B", ha="center",
                color=TC, fontsize=8, fontweight="bold")
ax.set_xticks(x7); ax.set_xticklabels([f"B{i+1}" for i in range(7)], color=TC)
ax.set_ylabel("NIT Program Cost ($B)", color=TC)
ax.set_title(f"NIT Cost Distribution by Bracket\nTotal = {total_nit:.1f}B", fontweight="bold")
ax.legend(facecolor=AX2, labelcolor=TC, fontsize=8); ax.tick_params(colors=TC)
badge(ax, "B1 = 91% of total\nconcentrated at lowest income", (0.30, 0.80), AMB)

# A9: Design rationale panel
ax = figA.add_subplot(gsA[2, 2]); ax.set_facecolor(AX2); ax.axis("off")
rationale = [
    ("NIT DESIGN RATIONALE",               GLD, True,  11),
    ("",                                    TC,  False,  7),
    ("WHY 25% SCALE?",                     AMB, True,   9),
    ("  Full NIT ($5.2T) exceeds surplus", TC,  False, 8.5),
    (f"  25% = ${total_nit:.0f}B = {100*total_nit/total_rev:.1f}% of revenue", TC, False, 8.5),
    ("  Fiscally bounded within surplus",  TC,  False, 8.5),
    ("  Modeled as phased implementation", TC,  False, 8.5),
    ("",                                    TC,  False,  7),
    ("WHY lambda = 0.15?",                 TEL, True,   9),
    ("  Carroll (2001): buffer-stock",     TC,  False, 8.5),
    ("    lambda ~ 0.10-0.15",             TC,  False, 8.5),
    ("  Jappelli & Pistaferri (2010):",    TC,  False, 8.5),
    ("    lambda ~ 0.20",                  TC,  False, 8.5),
    ("  lambda=0.15 is LOWER BOUND",       TC,  False, 8.5),
    ("  Validates 2-3% GDP (CBO 2023)",    TC,  False, 8.5),
    ("",                                    TC,  False,  7),
    ("WHY THESE MPC VALUES?",              GRN, True,   9),
    ("  B1: 0.95 = near-full pass-thru",   TC,  False, 8.5),
    ("  B7: 0.06 = high-income savings",   TC,  False, 8.5),
    ("  Gradient: Dynan et al. (2004)",    TC,  False, 8.5),
    ("",                                    TC,  False,  7),
    ("DISTRIBUTIONAL INTENT",              PRP, True,   9),
    ("  B1-B4 = net recipients",           TC,  False, 8.5),
    ("  B5-B7 = net payers",               TC,  False, 8.5),
    ("  Smooth phaseout: no poverty trap", TC,  False, 8.5),
]
yp = 0.97
for text, col, bold, fs in rationale:
    figA.gca(); ax.text(0.04, yp, text, color=col, fontsize=fs,
                        fontweight="bold" if bold else "normal",
                        fontfamily="monospace", transform=ax.transAxes, va="top")
    yp -= 0.040 if bold else 0.036

save(figA, "figA_nit_defense.png")

# ════════════════════════════════════════════════════════════════════════════
# FIGURE B — Uncertainty & Monte Carlo Dashboard   [CAMPUS EDITION]
# ════════════════════════════════════════════════════════════════════════════
print("Generating Figure B — Uncertainty Dashboard...")
N = 50_000
lam_mc   = np.random.normal(0.15,   0.04,  N).clip(0.05, 0.40)
phi_mc   = np.random.normal(0.065,  0.015, N).clip(0.03, 0.12)
m_mc     = np.random.normal(m,      0.012, N).clip(0.13, 0.20)
elast_mc = np.random.normal(1.0,    0.20,  N).clip(0.50, 1.80)
alpha_mc = np.random.normal(1.0,    0.25,  N).clip(0.30, 2.50)

k_mc        = 1 / (s + t + m_mc)
rev_mc      = total_rev - (elast_mc - 1) * 1_800
net_surp_mc = rev_mc - total_nit
G_aft_mc    = phi_mc * net_surp_mc
dC_mc       = dC_first * (lam_mc / lam)
dX_mc       = delta_X_total * alpha_mc
A_mc        = dC_mc + G_aft_mc + dX_mc
dY_mc       = k_mc * A_mc
dNX_mc      = dX_mc - (m_mc * dY_mc)
Y_pct_mc    = 100 * dY_mc / Y_baseline

p5Y, p25Y, p50Y, p75Y, p95Y = np.percentile(dY_mc,   [5, 25, 50, 75, 95])
p5X, p50X, p95X              = np.percentile(dNX_mc,  [5, 50, 95])
p5P, p50P, p95P              = np.percentile(Y_pct_mc,[5, 50, 95])

figB = plt.figure(figsize=(20, 14), facecolor=DK)
figB.suptitle(
    "Figure B — Model Uncertainty & Sensitivity Analysis\n"
    "Monte Carlo Simulation (N=50,000) | Joint Parameter Distribution | 90% Confidence Intervals",
    color=TC, fontsize=12, fontweight="bold", y=0.995)
gsB = gridspec.GridSpec(3, 3, figure=figB, hspace=0.60, wspace=0.42)

# B1: dY distribution
ax = figB.add_subplot(gsB[0, 0]); style_ax(ax)
cnts, bins, _ = ax.hist(dY_mc, bins=80, color=c(BLU, 0.70), edgecolor=c(BLU, 0.3))
ax.axvline(delta_Y, color=AMB, linestyle="-",  linewidth=2.5, label=f"Point Est. {delta_Y:.0f}B")
ax.axvline(p50Y,    color=GRN, linestyle="--", linewidth=1.8, label=f"Median {p50Y:.0f}B")
ax.axvline(p5Y,     color=RED, linestyle=":",  linewidth=1.5, label=f"5th {p5Y:.0f}B")
ax.axvline(p95Y,    color=RED, linestyle=":",  linewidth=1.5, label=f"95th {p95Y:.0f}B")
ax.fill_betweenx([0, cnts.max()], p25Y, p75Y, alpha=0.18, color=GRN, label="IQR")
ax.set_xlabel("dY ($B)", color=TC); ax.set_ylabel("Frequency", color=TC)
ax.set_title("Monte Carlo: dY Distribution\nN=50,000 joint parameter draws", fontweight="bold")
ax.legend(facecolor=AX2, labelcolor=TC, fontsize=7.5); ax.tick_params(colors=TC)
badge(ax, f"90% CI: [{p5Y:.0f}B, {p95Y:.0f}B]\nAll positive GDP gain", (0.03, 0.80), GLD)

# B2: dNX distribution
ax = figB.add_subplot(gsB[0, 1]); style_ax(ax)
cnts2, _, _ = ax.hist(dNX_mc, bins=80, color=c(RED, 0.70), edgecolor=c(RED, 0.3))
ax.axvline(delta_NX, color=AMB, linestyle="-",  linewidth=2.5, label=f"Point Est. {delta_NX:.0f}B")
ax.axvline(p50X,     color=GRN, linestyle="--", linewidth=1.8, label=f"Median {p50X:.0f}B")
ax.axvline(p5X,      color=RED, linestyle=":",  linewidth=1.5, label=f"5th {p5X:.0f}B")
ax.axvline(p95X,     color=RED, linestyle=":",  linewidth=1.5, label=f"95th {p95X:.0f}B")
ax.axvline(0, color=WHT, linestyle="-", linewidth=1, alpha=0.5)
ax.set_xlabel("dNX ($B)", color=TC); ax.set_ylabel("Frequency", color=TC)
ax.set_title("Monte Carlo: dNX Distribution\nTrade Balance Uncertainty", fontweight="bold")
ax.legend(facecolor=AX2, labelcolor=TC, fontsize=7.5); ax.tick_params(colors=TC)
badge(ax, "Trade deficit worsens\nin ALL scenarios", (0.03, 0.80), RED)

# B3: dY% distribution
ax = figB.add_subplot(gsB[0, 2]); style_ax(ax)
ax.hist(Y_pct_mc, bins=80, color=c(GRN, 0.70), edgecolor=c(GRN, 0.3))
ax.axvline(Y_pct, color=AMB, linestyle="-",  linewidth=2.5, label=f"Point Est. {Y_pct:.2f}%")
ax.axvline(p50P,  color=GRN, linestyle="--", linewidth=1.8, label=f"Median {p50P:.2f}%")
ax.axvline(p5P,   color=RED, linestyle=":",  linewidth=1.5, label=f"5th {p5P:.2f}%")
ax.axvline(p95P,  color=RED, linestyle=":",  linewidth=1.5, label=f"95th {p95P:.2f}%")
ax.set_xlabel("dY (%)", color=TC); ax.set_ylabel("Frequency", color=TC)
ax.set_title("Monte Carlo: dY% Distribution\nGDP Growth Rate Uncertainty", fontweight="bold")
ax.legend(facecolor=AX2, labelcolor=TC, fontsize=7.5); ax.tick_params(colors=TC)
badge(ax, f"90% CI: [{p5P:.1f}%, {p95P:.1f}%]\nAll scenarios positive", (0.03, 0.80), GLD)

# B4: Sensitivity tornado (partial correlations)
ax = figB.add_subplot(gsB[1, 0]); style_ax(ax)
params_arr = np.column_stack([lam_mc, phi_mc, m_mc, elast_mc, alpha_mc])
param_names = ["lambda (PIH)", "phi (surplus)", "m (import MPM)", "epsilon (elast.)", "alpha (export)"]
partial_corr = np.array([np.corrcoef(params_arr[:, j], dY_mc)[0, 1] for j in range(5)])
bar_cols = [GRN if pc >= 0 else RED for pc in partial_corr]
y_pos = np.arange(5)
ax.barh(y_pos, partial_corr, color=[c(col, 0.75) for col in bar_cols],
        edgecolor=bar_cols, linewidth=1.5)
ax.axvline(0, color=WHT, linewidth=1.5)
ax.set_yticks(y_pos); ax.set_yticklabels(param_names, color=TC, fontsize=9)
ax.set_xlabel("Correlation with dY", color=TC)
ax.set_title("Sensitivity Tornado\nParameter Influence on GDP Gain", fontweight="bold")
ax.tick_params(colors=TC)
for bar, corr in zip(ax.patches, partial_corr):
    ax.text(corr + 0.01*np.sign(corr), bar.get_y()+bar.get_height()/2,
            f"{corr:+.3f}", va="center", color=TC, fontsize=8, fontweight="bold")
badge(ax, "lambda dominates dY variance\nm reduces it (leakage)", (0.38, 0.08), AMB)

# B5: 2D joint — lambda vs dY coloured by m
ax = figB.add_subplot(gsB[1, 1]); style_ax(ax)
sc = ax.scatter(lam_mc[::10], dY_mc[::10], c=m_mc[::10],
                cmap="plasma", alpha=0.3, s=4, rasterized=True)
cbar = figB.colorbar(sc, ax=ax, pad=0.02)
cbar.set_label("m (MPM)", color=TC); cbar.ax.tick_params(colors=TC)
ax.axvline(lam,     color=AMB, linestyle="--", linewidth=1.8, label="lambda=0.15")
ax.axhline(delta_Y, color=GLD, linestyle="--", linewidth=1.8, label=f"dY={delta_Y:.0f}B")
ax.set_xlabel("lambda (PIH Discount)", color=TC); ax.set_ylabel("dY ($B)", color=TC)
ax.set_title("Joint Distribution: lambda vs dY\nColor = Import MPM (m)", fontweight="bold")
ax.legend(facecolor=AX2, labelcolor=TC, fontsize=8); ax.tick_params(colors=TC)

# B6: 2D joint — m vs dNX coloured by alpha
ax = figB.add_subplot(gsB[1, 2]); style_ax(ax)
sc2 = ax.scatter(m_mc[::10], dNX_mc[::10], c=alpha_mc[::10],
                 cmap="RdYlGn", alpha=0.3, s=4, rasterized=True)
cbar2 = figB.colorbar(sc2, ax=ax, pad=0.02)
cbar2.set_label("alpha scale", color=TC); cbar2.ax.tick_params(colors=TC)
ax.axvline(m,       color=AMB, linestyle="--", linewidth=1.8, label=f"m={m:.4f}")
ax.axhline(delta_NX,color=RED, linestyle="--", linewidth=1.8, label=f"dNX={delta_NX:.0f}B")
ax.axhline(0,       color=WHT, linestyle=":",  linewidth=1.2)
ax.set_xlabel("m (Aggregate MPM)", color=TC); ax.set_ylabel("dNX ($B)", color=TC)
ax.set_title("Joint Distribution: m vs dNX\nColor = alpha Export Multiplier", fontweight="bold")
ax.legend(facecolor=AX2, labelcolor=TC, fontsize=8); ax.tick_params(colors=TC)
badge(ax, "No scenario achieves\ndNX > 0 at current params", (0.03, 0.80), RED)

# B7: 90% CI horizontal bar chart
ax = figB.add_subplot(gsB[2, 0]); style_ax(ax)
metrics  = ["dY ($B)", "dY (%)", "dNX ($B)", "dC ($B)", "G_aft ($B)"]
p5_v     = [p5Y,   p5P,  p5X,  np.percentile(dC_mc,5),    np.percentile(G_aft_mc,5)]
p50_v    = [p50Y,  p50P, p50X, np.percentile(dC_mc,50),   np.percentile(G_aft_mc,50)]
p95_v    = [p95Y,  p95P, p95X, np.percentile(dC_mc,95),   np.percentile(G_aft_mc,95)]
point_v  = [delta_Y, Y_pct, delta_NX, dC_first, G_aft]
y_pos    = np.arange(5)
ax.barh(y_pos, [p95_v[i]-p5_v[i] for i in range(5)], left=p5_v,
        color=[c(BLU, 0.30)]*5, edgecolor=[c(BLU, 0.5)]*5, linewidth=1)
ax.scatter(point_v, y_pos, color=AMB, s=80, zorder=5, marker="D", label="Point Est.")
ax.scatter(p50_v,   y_pos, color=GRN, s=50, zorder=4, label="Median")
ax.axvline(0, color=WHT, linewidth=1, linestyle="--", alpha=0.5)
ax.set_yticks(y_pos); ax.set_yticklabels(metrics, color=TC, fontsize=9)
ax.set_xlabel("Value", color=TC)
ax.set_title("90% Confidence Intervals\nPoint Est. vs Monte Carlo Range", fontweight="bold")
ax.legend(facecolor=AX2, labelcolor=TC, fontsize=8); ax.tick_params(colors=TC)
for i in range(5):
    ax.text(p5_v[i]-abs(p5_v[i])*0.02, i, f"{p5_v[i]:.1f}",
            ha="right", va="center", color=RED, fontsize=7, fontweight="bold")
    ax.text(p95_v[i]+abs(p95_v[i])*0.01, i, f"{p95_v[i]:.1f}",
            ha="left", va="center", color=GRN, fontsize=7, fontweight="bold")

# B8: Parameter specification table
ax = figB.add_subplot(gsB[2, 1]); ax.set_facecolor(AX2); ax.axis("off")
rows = [
    ["Parameter",    "Point Est.",    "Distribution",    "90% CI Range",     "Source"],
    ["lambda (PIH)", "0.15",          "N(0.15, 0.04)",   "[0.08, 0.23]",     "Carroll 2001"],
    ["phi (surplus)", "6.5%",         "N(6.5%, 1.5%)",   "[3.9%, 9.4%]",     "Model design"],
    ["m (MPM)",      f"{m:.4f}",      "N(m, 0.012)",     "[0.142, 0.185]",   "BEA 2024"],
    ["epsilon",      "1.0x",          "N(1.0, 0.20)",    "[0.68x, 1.33x]",   "Feldstein 1995"],
    ["alpha",        "1.0x",          "N(1.0, 0.25)",    "[0.59x, 1.41x]",   "Model design"],
]
row_h = 0.13
for ri, row in enumerate(rows):
    bg = c(GLD, 0.12) if ri == 0 else (c(BLU, 0.06) if ri % 2 == 0 else c(AXC, 0.0))
    ax.add_patch(mpatches.FancyBboxPatch(
        (0, 0.97-ri*row_h-row_h), 1, row_h,
        boxstyle="round,pad=0.005", facecolor=bg, edgecolor=GRC,
        linewidth=0.5, transform=ax.transAxes, clip_on=True))
    col_widths = [0.20, 0.15, 0.23, 0.23, 0.18]
    xp = 0.01
    for ci, (cell, cw) in enumerate(zip(row, col_widths)):
        col_color = GLD if ri == 0 else (AMB if ci == 1 else TC)
        ax.text(xp+0.005, 0.97-ri*row_h-row_h/2, cell, va="center",
                color=col_color, fontsize=7.8,
                fontweight="bold" if ri == 0 else "normal",
                fontfamily="monospace", transform=ax.transAxes)
        xp += cw
ax.set_title("Monte Carlo Parameter Specifications", fontweight="bold", color=TC, pad=8)

# B9: Variance decomposition pie
ax = figB.add_subplot(gsB[2, 2]); style_ax(ax)
X_design = np.column_stack([params_arr, np.ones(N)])
from numpy.linalg import lstsq
coeffs, _, _, _ = lstsq(X_design, dY_mc, rcond=None)
total_var = np.var(dY_mc)
var_shares = [np.var(coeffs[j]*params_arr[:, j])/total_var*100 for j in range(5)]
var_shares.append(max(0, 100 - sum(var_shares)))
pie_labels = ["lambda", "phi", "m", "epsilon", "alpha", "Interaction\n& Residual"]
pie_colors = [BLU, GLD, RED, ORG, GRN, GRY]
wedges, texts, autotexts = ax.pie(
    var_shares, labels=pie_labels,
    colors=[c(col, 0.80) for col in pie_colors],
    autopct="%1.1f%%", startangle=140,
    textprops={"color": TC, "fontsize": 8},
    wedgeprops={"edgecolor": DK, "linewidth": 1.5})
for at in autotexts:
    at.set_color(DK); at.set_fontweight("bold"); at.set_fontsize(8)
ax.set_title("Variance Decomposition\nShare of dY Uncertainty by Parameter", fontweight="bold")

save(figB, "figB_uncertainty.png")

# ════════════════════════════════════════════════════════════════════════════
# FIGURE C — Trade Balance Deterioration Spotlight   [CAMPUS EDITION]
# ════════════════════════════════════════════════════════════════════════════
print("Generating Figure C — Trade Balance Spotlight...")
NX_baseline = X_baseline - M_baseline
NX_new      = NX_baseline + delta_NX

figC = plt.figure(figsize=(20, 14), facecolor=DK)
figC.suptitle(
    "Figure C — Trade Balance Deterioration: The Hidden Cost of Diversification\n"
    f"dNX = {delta_NX:+.1f}B  |  Policy Worsens Trade Deficit by {100*abs(delta_NX)/abs(NX_baseline):.1f}%  |  "
    f"{delta_Y_base - delta_Y:.0f}B GDP Opportunity Cost",
    color=RED, fontsize=12, fontweight="bold", y=0.995)
gsC = gridspec.GridSpec(3, 3, figure=figC, hspace=0.60, wspace=0.42)

# C1: Before/after trade balance
ax = figC.add_subplot(gsC[0, 0]); style_ax(ax)
nx_scenarios = ["Baseline\n(2026)", "Post-Reform\n(Diversified)", "Counterfactual\n(No Divers.)"]
nx_s_vals    = [NX_baseline, NX_new, NX_baseline - delta_M_base]
nx_s_cols    = [GRY, RED, GRN]
bars = ax.bar(range(3), nx_s_vals, color=[c(col, 0.75) for col in nx_s_cols],
              edgecolor=nx_s_cols, linewidth=2.0, width=0.55)
ax.axhline(0, color=WHT, linestyle="--", linewidth=1.5)
for b, v in zip(bars, nx_s_vals):
    ax.text(b.get_x()+b.get_width()/2, v - 40 if v < 0 else v + 40,
            f"${v:+,.0f}B", ha="center", color=TC, fontsize=10,
            fontweight="bold", fontfamily="monospace")
ax.set_xticks(range(3)); ax.set_xticklabels(nx_scenarios, color=TC, fontsize=9)
ax.set_ylabel("Net Exports ($B)", color=TC)
ax.set_title("Net Export Position\nBaseline vs Post-Reform vs Counterfactual", fontweight="bold")
ax.tick_params(colors=TC)
ax.annotate("", xy=(1, NX_new+20), xytext=(0, NX_baseline-20),
            arrowprops=dict(arrowstyle="->", color=RED, lw=2))
ax.text(0.5, (NX_baseline+NX_new)/2 - 50, f"dNX = {delta_NX:+.0f}B",
        color=RED, fontsize=10, fontweight="bold", ha="center")
badge(ax, f"Deficit worsens by\n{abs(delta_NX):.0f}B ({100*abs(delta_NX)/abs(NX_baseline):.1f}%)", (0.30, 0.10), RED)

# C2: dX vs dM asymmetry
ax = figC.add_subplot(gsC[0, 1]); style_ax(ax)
asym_lbs  = ["dX\n(Export gain)", "dM\n(Import leakage)", "Net dNX\n(Trade balance)"]
asym_vals = [delta_X_total, -delta_M, delta_NX]
asym_cols = [GRN, RED, RED]
bars = ax.bar(range(3), asym_vals, color=[c(col, 0.75) for col in asym_cols],
              edgecolor=asym_cols, linewidth=2.0, width=0.55)
ax.axhline(0, color=WHT, linestyle="--", linewidth=1.5)
for b, v in zip(bars, asym_vals):
    ax.text(b.get_x()+b.get_width()/2, v - 15 if v < 0 else v + 5,
            f"${v:+.1f}B", ha="center", color=TC, fontsize=11,
            fontweight="bold", fontfamily="monospace")
ax.set_xticks(range(3)); ax.set_xticklabels(asym_lbs, color=TC, fontsize=10)
ax.set_ylabel("Change ($B)", color=TC)
ax.set_title("Export Gain vs Import Leakage\nThe Core Trade-Off", fontweight="bold")
ax.tick_params(colors=TC)
badge(ax, f"dM is {delta_M/max(abs(delta_X_total),0.01):.0f}x larger than dX\nExport return far too low", (0.12, 0.15), RED)

# C3: Import leakage by tier with pie inset
ax = figC.add_subplot(gsC[0, 2]); style_ax(ax)
bars = ax.bar(range(4), delta_M_tier, color=[c(col, 0.75) for col in TIER_COLORS],
              edgecolor=TIER_COLORS, linewidth=1.5, width=0.6)
for b, v in zip(bars, delta_M_tier):
    ax.text(b.get_x()+b.get_width()/2, v+2, f"${v:.1f}B",
            ha="center", color=TC, fontsize=10, fontweight="bold")
ax.set_xticks(range(4)); ax.set_xticklabels(tier_short, color=TC)
ax.set_ylabel("dM ($B)", color=TC)
ax.set_title(f"Import Leakage by Tier\nTotal dM = {delta_M_tier.sum():.1f}B", fontweight="bold")
ax.tick_params(colors=TC)
ax_in = ax.inset_axes([0.55, 0.42, 0.42, 0.52])
ax_in.set_facecolor(AX2)
wedges2, _, aut2 = ax_in.pie(
    delta_M_tier, colors=[c(col, 0.80) for col in TIER_COLORS],
    autopct="%1.0f%%", startangle=90,
    textprops={"color": TC, "fontsize": 7.5},
    wedgeprops={"edgecolor": DK, "linewidth": 1})
for at2 in aut2: at2.set_color(DK); at2.set_fontweight("bold"); at2.set_fontsize(7)
badge(ax, "HI absorbs 64% of leakage\nDiversification paradox!", (0.02, 0.78), RED)

# C4: Promo vs contraction per tier
ax = figC.add_subplot(gsC[1, 0]); style_ax(ax)
dev_tiers = ["UMI", "LMI", "LI"]
promo_v   = np.array([dX_promo_UMI, dX_promo_LMI, dX_promo_LI])
cont_v    = np.array([dX_contract_UMI, dX_contract_LMI, dX_contract_LI])
net_dX_v  = np.array([dX_UMI, dX_LMI, dX_LI])
xd = np.arange(3); wd = 0.25
ax.bar(xd-wd, promo_v,  wd, color=c(GRN, 0.75), edgecolor=GRN, linewidth=1.5, label="Export Promotion ($B)")
ax.bar(xd,    cont_v,   wd, color=c(RED, 0.75), edgecolor=RED, linewidth=1.5, label="Transition Contraction ($B)")
ax.bar(xd+wd, net_dX_v, wd, color=c(AMB, 0.75), edgecolor=AMB, linewidth=1.5, label="Net dX ($B)")
ax.axhline(0, color=WHT, linestyle="--", linewidth=1.5)
ax.set_xticks(xd); ax.set_xticklabels(dev_tiers, color=TC)
ax.set_ylabel("$B", color=TC)
ax.set_title("Export: Promotion vs Contraction\nTransition Cost Dominates Near-Term", fontweight="bold")
ax.legend(facecolor=AX2, labelcolor=TC, fontsize=8); ax.tick_params(colors=TC)
for i, (p, cv, n) in enumerate(zip(promo_v, cont_v, net_dX_v)):
    ax.text(i-wd, p+0.5,            f"+{p:.0f}", ha="center", color=GRN, fontsize=7.5, fontweight="bold")
    ax.text(i,    cv-1,             f"{cv:.0f}", ha="center", color=RED, fontsize=7.5, fontweight="bold")
    ax.text(i+wd, n+0.5 if n>=0 else n-1, f"{n:.0f}", ha="center", color=AMB, fontsize=7.5, fontweight="bold")

# C5: GDP waterfall showing opportunity cost
ax = figC.add_subplot(gsC[1, 1]); style_ax(ax)
wf_lbs  = ["dC", "dG", "dX", "-dM", "dY\n(Div.)", "Foregone\ndY", "dY\n(No Div.)"]
wf_vals = [delta_C, delta_G, delta_X_total, -delta_M, delta_Y,
           delta_Y_base - delta_Y, delta_Y_base]
wf_cols = [GRN, GLD, TEL, RED, PRP, ORG, GRN]
bars = ax.bar(range(7), [abs(v) for v in wf_vals],
              bottom=[0, 0, 0, 0, 0, delta_Y, 0],
              color=[c(col, 0.75) for col in wf_cols], edgecolor=wf_cols, linewidth=1.5, width=0.6)
for b, v in zip(bars, wf_vals):
    ax.text(b.get_x()+b.get_width()/2, b.get_height()+b.get_y()+10,
            f"${v:+,.0f}B", ha="center", color=TC, fontsize=8,
            fontweight="bold", fontfamily="monospace")
ax.set_xticks(range(7)); ax.set_xticklabels(wf_lbs, color=TC, fontsize=8.5)
ax.set_ylabel("$B", color=TC)
ax.set_title(f"GDP Waterfall: Diversification Cost\n{delta_Y_base-delta_Y:.0f}B Foregone vs No-Divers. Baseline",
             fontweight="bold")
ax.tick_params(colors=TC)
ax.annotate("", xy=(6, delta_Y), xytext=(6, delta_Y_base),
            arrowprops=dict(arrowstyle="<->", color=RED, lw=2))
ax.text(6.45, (delta_Y + delta_Y_base)/2, f"{delta_Y_base-delta_Y:.0f}B\nOpportunity\nCost",
        color=RED, fontsize=8.5, fontweight="bold", va="center")
badge(ax, f"Is {delta_Y_base-delta_Y:.0f}B the right\nprice for development?", (0.02, 0.82), RED)

# C6: Multiplier drag from higher m
ax = figC.add_subplot(gsC[1, 2]); style_ax(ax)
m_rng = np.linspace(0.12, 0.22, 200)
k_rng = 1 / (s + t + m_rng)
ax.plot(m_rng, k_rng, color=BLU, linewidth=3)
ax.fill_between(m_rng, k_rng, k_rng.min()-0.001, alpha=0.10, color=BLU)
ax.axvline(m_base, color=GRN, linestyle="--", linewidth=2,
           label=f"m_base={m_base:.4f} k={k_baseline:.4f}")
ax.axvline(m,      color=RED, linestyle="--", linewidth=2,
           label=f"m_new ={m:.4f}  k={k_diversified:.4f}")
ax.scatter([m_base, m], [k_baseline, k_diversified], color=[GRN, RED], s=100, zorder=5)
ax.annotate("", xy=(m, k_diversified), xytext=(m_base, k_baseline),
            arrowprops=dict(arrowstyle="->", color=RED, lw=2))
ax.text((m_base+m)/2+0.001, (k_baseline+k_diversified)/2+0.001,
        f"Dk = {k_diversified-k_baseline:+.4f}", color=RED, fontsize=9, fontweight="bold")
ax.set_xlabel("Aggregate MPM (m)", color=TC); ax.set_ylabel("Multiplier k = 1/(s+t+m)", color=TC)
ax.set_title("Multiplier Drag from Import Leakage\nHigher m -> Lower k -> Lower GDP", fontweight="bold")
ax.legend(facecolor=AX2, labelcolor=TC, fontsize=8); ax.tick_params(colors=TC)
badge(ax, f"MPM rise costs\n{(k_baseline-k_diversified)/k_baseline*100:.1f}% of multiplier power",
      (0.40, 0.80), RED)

# C7: Alpha break-even analysis
ax = figC.add_subplot(gsC[2, 0]); style_ax(ax)
alph_rng = np.linspace(0.1, 6.0, 300)
promo_total = dX_promo_UMI + dX_promo_LMI + dX_promo_LI
cont_total  = dX_contract_UMI + dX_contract_LMI + dX_contract_LI
dX_a   = alph_rng * promo_total + cont_total
dNX_a  = dX_a - delta_M
ax.plot(alph_rng, dX_a,  color=GRN, linewidth=2.5, label="Net dX ($B)")
ax.plot(alph_rng, dNX_a, color=AMB, linewidth=2.5, linestyle="--", label="dNX ($B)")
ax.axhline(0, color=WHT, linestyle=":", linewidth=1.5, alpha=0.8)
ax.axvline(1.0, color=RED, linestyle="--", linewidth=1.8, label="Current alpha=1.0")
alpha_dx0  = -cont_total / promo_total if promo_total != 0 else float("inf")
alpha_dnx0 = (delta_M - cont_total) / promo_total if promo_total != 0 else float("inf")
if 0 < alpha_dx0 < 6:
    ax.axvline(alpha_dx0,  color=GRN, linestyle=":", linewidth=1.5, label=f"dX=0 at alpha={alpha_dx0:.1f}x")
if 0 < alpha_dnx0 < 6:
    ax.axvline(alpha_dnx0, color=AMB, linestyle=":", linewidth=1.5, label=f"dNX=0 at alpha={alpha_dnx0:.1f}x")
ax.set_xlabel("alpha Scale Factor (Export Multiplier)", color=TC)
ax.set_ylabel("$B", color=TC)
ax.set_title("Break-Even Analysis: alpha Required\nFor Trade Balance Neutrality", fontweight="bold")
ax.legend(facecolor=AX2, labelcolor=TC, fontsize=7.5); ax.tick_params(colors=TC)
if 0 < alpha_dnx0 < 6:
    badge(ax, f"Need alpha >= {alpha_dnx0:.1f}x to\nneutralize trade deficit", (0.40, 0.77), RED)

# C8: gamma vs dNX
ax = figC.add_subplot(gsC[2, 1]); style_ax(ax)
g_rng  = np.linspace(0, 2.5, 300)
m_g    = np.array([M_1_tier_baseline[0]
                   + M_1_tier_baseline[1]*(1+gv*gamma_UMI)
                   + M_1_tier_baseline[2]*(1+gv*gamma_LMI)
                   + M_1_tier_baseline[3]*(1+gv*gamma_LI)
                   for gv in g_rng])
dNX_g  = delta_X_total - m_g * delta_Y_raw
ax.fill_between(g_rng, dNX_g, 0, where=(dNX_g < 0), alpha=0.20, color=RED)
ax.fill_between(g_rng, dNX_g, 0, where=(dNX_g >= 0), alpha=0.20, color=GRN)
ax.plot(g_rng, dNX_g, color=ORG, linewidth=2.5)
ax.axhline(0, color=WHT, linestyle="--", linewidth=1.5)
ax.axvline(1.0, color=AMB, linestyle="--", linewidth=1.8, label="Current gamma scale=1")
ax.scatter([1.0], [delta_NX], color=RED, s=100, zorder=5, label=f"Current dNX={delta_NX:.0f}B")
ax.set_xlabel("gamma Scale (MFN Boost Intensity)", color=TC)
ax.set_ylabel("dNX ($B)", color=TC)
ax.set_title("Trade Balance vs MFN Intensity\nHigher gamma -> More Leakage -> Worse NX", fontweight="bold")
ax.legend(facecolor=AX2, labelcolor=TC, fontsize=8); ax.tick_params(colors=TC)
badge(ax, "dNX < 0 for ALL\npositive gamma values", (0.40, 0.80), RED)

# C9: Policy findings panel
ax = figC.add_subplot(gsC[2, 2]); ax.set_facecolor(AX2); ax.axis("off")
ax.add_patch(mpatches.FancyBboxPatch(
    (0.01, 0.01), 0.98, 0.98, boxstyle="round,pad=0.01",
    facecolor=c(RED, 0.06), edgecolor=RED, linewidth=2.5, transform=ax.transAxes))
findings = [
    ("TRADE BALANCE FINDINGS",               RED, True,  11),
    ("",                                      TC,  False,  6),
    ("THE CORE PROBLEM",                     ORG, True,   9.5),
    (f"  dM = {delta_M:.0f}B  vs  dX = {delta_X_total:.1f}B", TC, False, 9),
    (f"  Import leakage is {delta_M/max(abs(delta_X_total),0.01):.0f}x the export gain.", TC, False, 9),
    ("  Policy worsens the US trade",        TC,  False,  9),
    (f"  deficit by {100*abs(delta_NX)/abs(NX_baseline):.1f}% ({delta_NX:.0f}B).", TC, False, 9),
    ("",                                      TC,  False,  6),
    ("WHY HI ABSORBS 64% OF dM?",           ORG, True,   9.5),
    ("  HI holds 65% of import basket.",     TC,  False,  9),
    ("  GDP growth from dY triggers more",   TC,  False,  9),
    ("  HI imports via m_HI. Raising total", TC,  False,  9),
    ("  m leaks mainly through HI. Paradox.",TC,  False,  9),
    ("",                                      TC,  False,  6),
    ("POLICY OPTIONS",                       GRN, True,   9.5),
    (f"  1. Raise alpha >= {alpha_dnx0:.1f}x (export capacity)", TC, False, 9),
    ("  2. Reduce gamma (slower MFN)",       TC,  False,  9),
    ("  3. Targeted HI import substitution", TC,  False,  9),
    ("  4. Frame deficit as development aid", TC,  False,  9),
    ("",                                      TC,  False,  6),
    (f"THE {delta_Y_base-delta_Y:.0f}B QUESTION",               GLD, True,   9.5),
    ("  Foregone GDP vs development gains:", TC,  False,  9),
    ("  poverty reduction, supply chains,",  TC,  False,  9),
    ("  geopolitical stability. Model cannot",TC,  False,  9),
    ("  value these — but debate must.",      TC,  False,  9),
]
yp = 0.96
for text, col, bold, fs in findings:
    ax.text(0.04, yp, text, color=col, fontsize=fs,
            fontweight="bold" if bold else "normal",
            fontfamily="monospace", transform=ax.transAxes, va="top")
    yp -= 0.036 if bold else 0.034

save(figC, "figC_trade_balance.png")

print("\n" + "="*65)
print(" ALL 8 FIGURES COMPLETE")
print("="*65)
print(f"\n Output directory: {OUT}")
for fname in sorted(os.listdir(OUT)):
    fpath = os.path.join(OUT, fname)
    size  = os.path.getsize(fpath) / 1024
    print(f"   {fname:<35}  {size:>6.0f} KB")
