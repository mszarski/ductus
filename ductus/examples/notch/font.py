"""Ductus Notch -- an ink-trap grotesque, designed by eye (no reference fitted).

A modern grotesque whose crotches carry visible ink traps (``ductus.traps``:
a notch cut into every sharp inner corner by rule) and whose curved stroke
ends are cut on a slant. Low contrast: every thin part is derived from three
design numbers below, so the weight can be re-balanced in one place.

Signatures: flat-footed g, j and y; branched k and K (the leg springs from the
arm); an R whose leg springs from the stem; the e's bar and the a's top
angled; the t's top cut on a slant; a looped one-stroke &; an upright @ whose
inner stem runs into the ring. Design log: docs/notch/README.md.
"""
from ductus import Font
from ductus.kits import serif as kit
from ductus.terminals import flat

font = Font("Ductus Notch", upm=1000)

# the design numbers: lowercase stem, thin strokes (horizontals, bowls' tops), capital stem
S, T, C = 92, 78, 98
weights = dict(
    stem=S, cap_stem=C, fig_stem=S + 4, seven_stem=S, hairline=T, round_gain=1.06,
    arch_contrast=0.12, t_contrast=0.12,
    n_join_thin=56, u_join_thin=56, r_join_thin=60,
    a_bowl_thin=T, a_bowl_thin_b=T, a_bs_thick=S, a_bs_thin=T, a_top_thin=58, a_bot_thin=T,
    a_lobe_thick=S, a_lobe_thin_b=T,
    b_top_thin=56, b_bot_thin=T, b_lobe_thick=S * 1.04, b_lobe_thin_b=T, b_crown_t=T, b_ov_thin=T,
    d_top_thin=56, d_bot_thin=T, d_lobe_thick=S * 1.04, d_lobe_thin_b=T, d_crown_t=T, d_bowl_thin=T,
    e_bar_t=T * 0.92, bar_t=T * 0.92, H_bar_t=C * 0.86, E_arm_t=C * 0.86, z_bar_t=T, B_hair=T,
    v_thick=S + 4, v_thin=T + 4, w_thick=S, w_thin=T, x_thick=S, x_thin=T + 4, k_thick=S, k_thin=T + 4,
    z_thick=S, y_end_w=1.0,
    A_thick=C + 6, A_thin=T + 6, K_thick=C, K_thin=T + 6, M_thick=C, M_thin=T + 6, N_thick=C, N_thin=T + 6,
    U_thick=C, U_thin=T + 6, V_thick=C + 4, V_thin=T + 6, X_thick=C, X_thin=T + 6, Y_thick=C, Y_thin=T + 6,
    Z_thick=C, R_leg_w=C, Q_bar_w=C, AE_thick=C, AE_bar_t=C * 0.86,
    g_loop_t=T, g_loop_top_t=T, g_loop_bot_t=T,
    two_bar_t=T, five_bar_t=T, seven_bar_t=T, four_bar_t=T, four_thin=T, fig_thin_k=1.0,
    quest_w=S, quest_thin=T, paren_w=S * 0.9, slash_w=S * 0.75,
    dash_t=T, ring_thick=T * 0.7, ring_thin=T * 0.6,
)
proportions = dict(
    xheight=548, capheight=712, ascender=752,
    sb_straight=46, sb_round=34,
    n_width=440, m_width=380, u_width=440, o_width=530, e_width=500, c_width=480, b_width=520,
    H_width=600, O_width=720,
)
# stroke ends cut on a slant (the cut's normal, degrees: 90 = level)
cuts = dict(sans_cut_s1=60, sans_cut_s2=60, sans_cut_hood=60, sans_cut_r=60, sans_cut_t=60,
            sans_cut_ear=30, sans_cut_g=30, sans_cut_ced=110)  # (the f's cut is with its hook below)
traps = dict(trap_depth=44, trap_mouth=26, trap_angle=80)
# the f: a hook with room to arc (its top at the ascender, starting low on the stem), cut on a slant
f_hook = dict(f_top=752, f_root_dy=130, f_hook=230, f_end_dir=-35, f_end_y=0.92, sans_cut_f=125)

# monoline clean-up of serif-era defaults: no wedge serifs (z, Z, 7), full-weight stroke ends (U, parentheses),
# a J whose hook ends on the baseline, equal stems in M and N, a full-weight 5
clean = dict(z_serif=0, z_wedge=0, z_serif_w=0, Z_serif=0, Z_wedge=0, seven_serif=0, seven_wedge=0, seven_top_w=S,
             J_end_y=150, J_end_dir=100, J_bot=200, J_hook=260, U_end_w=1.0, paren_end_w=0.9, paren_bow=150, five_stem_w=S * 0.9,
             one_arm_t=T,
             # the 8 without the serif's diagonal spine stroke (a stub hidden in the waist), its bowls sharing one
             # wall; the 5's stem nearly upright off its bar
             eight_sp_x0=0.45, eight_sp_x1=0.55, eight_sp_y0=390, eight_sp_y1=390, eight_sp_w=0.3, eight_overlap=0.5,
             five_lean=8, five_top_l=150, five_start_dir=90, five_stem_bot=360,
             # punctuation: square dots sized to the stem, short square-rooted commas; a ? and & at full weight
             dot_r=50, comma_tail=150, comma_root=0.5, comma_tip_w=40, excl_w=S, excl_tip_w=S * 0.7, quote_w=S * 0.9, quote_h=200,
             quest_bot_w=1.0, amp_pen=S)

# ---- signature glyphs ---------------------------------------------------------
# flat-footed descenders: g, j and y turn a tight corner into a level flag to the left (g_tail / y_tail "foot")
feet = dict(descender_g=-190, gs_w=230, gs_bot_x=0.35, y_end_y=-190, y_end_x=20, y_foot_r=40)
# branched k and K: the leg springs from the arm, away from the stem (two trapped crotches, a Y)
_k_arm, _k_join, _k_at = 380, 120, 0.42
_K_arm, _K_join, _K_at = 440, 190, 0.42
branch = dict(k_arm_x=_k_arm, k_join_y=_k_join, k_leg_x0=_k_arm * _k_at, k_leg_y0=_k_join + (548 - _k_join) * _k_at,
              k_leg_x=390, K_arm_x=_K_arm, K_join_y=_K_join, K_leg_x0=_K_arm * _K_at,
              K_leg_y0=_K_join + (712 - _K_join) * _K_at, K_leg_x=480)
# an R whose leg springs from the stem under the bowl, not from the bowl (a trapped crotch at the stem)
r_leg = dict(R_leg_x0=110, R_leg_x=450)
# the angled bar: the e's rises 12 degrees, the a's straight top rises to match; the t's top is cut on a slant
angled = dict(e_bar_tilt=12, a_bt_tilt=12, sans_cut_ttop=50)
# an upright @ whose inner a's stem runs on into the ring (at_style="hook")
at = dict(at_slant=0, at_w=880, at_h=860, at_bot=-150, at_ring_t=T * 0.8, at_pen_k=1.2, at_in_w=360, at_in_h=420,
          at_in_x=0.27, at_in_y=70, at_stem_dy=120, at_hook_y=10, at_hook_x=0.3, at_in_k=0.95, at_in_tr=0.6,
          at_end_x=0.72, at_end_y=0.1, at_end_dir=25, at_right_x=1.0)

P = kit.params(**weights, **proportions, **cuts, **traps, **f_hook, **feet, **branch, **r_leg, **angled, **at, **clean)
terminals = kit.sans_set(P)
terminals.by_tag["t_top"] = flat(P.sans_cut_ttop)
kit.define(font, P, glyphs="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 "
                           "&@?!.,:;-'\"()/",
           terminals=terminals, face_serifs=False, level_trim=True, dot_style="square", ligatures=False,
           l_style="tail", J_style="base", R_leg="line", Q_style="bar", one_style="arm", d_style="bowl",
           a_style="stroke", b_style="oval", r_style="arch", y_left="poly", j_style="foot", g_style="single",
           g_ear="flag", amp_style="stroke", at_style="hook", ec_aperture="vertical", seven_style="curve",
           fig_ends="cut", g_tail="foot", y_tail="foot")

# ink traps by rule (ductus.traps)
font.traps = {"depth": "trap_depth", "mouth": "trap_mouth", "angle": "trap_angle",
              # marks too small to trap: a comma's dot-to-tail joint is no crotch
              "skip": ["comma", "semicolon", "quotesingle", "quotedbl", "quoteleft", "quoteright",
                       "quotedblleft", "quotedblright"]}

# side bearings (left, right) on top of sb_straight / sb_round, set by eye
font.spacing.update({
    "f": (-10, -45), "r": (0, -30), "L": (0, -40), "t": (0, -15), "T": (-10, -10), "j": (-15, 0), "J": (45, 0),
})

# optical kerning, measured from these outlines (`ductus kern examples/notch/font.py`)
import json as _json
from pathlib import Path as _Path
_kern = _Path(__file__).with_name("kerning.json")
if _kern.exists():
    for _l, _r, _v in _json.loads(_kern.read_text())["pairs"]:
        font.kern(_l, _r, _v)
