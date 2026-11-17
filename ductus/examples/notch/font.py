"""Ductus Notch -- an ink-trap grotesque, designed by eye (no reference fitted).

A modern grotesque whose crotches carry visible ink traps (``ductus.traps``:
a notch cut into every sharp inner corner by rule) and whose curved stroke
ends are cut level. Low contrast: every thin part is derived from three
design numbers below, so the weight can be re-balanced in one place.

Draft 2, a contemporary neo-grotesque: a medium weight, a big x-height, level
stroke ends, slightly squared bowls, shallow traps. Signatures: branched k and K
(the leg springs from the arm), a straight-tailed y, a looped one-stroke &, an
upright @ whose inner stem runs into the ring. Design log: docs/notch/README.md.
"""
from ductus import Font
from ductus.kits import serif as kit

font = Font("Ductus Notch", upm=1000)

# the design numbers: lowercase stem, thin strokes (horizontals, bowls' tops), capital stem -- a medium weight
S, T, C = 112, 98, 118
weights = dict(
    stem=S, cap_stem=C, fig_stem=S + 4, seven_stem=S, hairline=T, round_gain=1.04,
    arch_contrast=0.1, t_contrast=0.1,
    n_join_thin=74, u_join_thin=74, r_join_thin=78,
    a_bowl_thin=T, a_bowl_thin_b=T, a_bs_thick=S, a_bs_thin=T, a_top_thin=74, a_bot_thin=T,
    a_lobe_thick=S, a_lobe_thin_b=T,
    b_top_thin=74, b_bot_thin=T, b_lobe_thick=S * 1.03, b_lobe_thin_b=T, b_crown_t=T, b_ov_thin=T,
    d_top_thin=74, d_bot_thin=T, d_lobe_thick=S * 1.03, d_lobe_thin_b=T, d_crown_t=T, d_bowl_thin=T,
    e_bar_t=T * 0.9, bar_t=T * 0.9, H_bar_t=C * 0.88, E_arm_t=C * 0.88, z_bar_t=T, B_hair=T,
    v_thick=S + 4, v_thin=T + 4, w_thick=S, w_thin=T, x_thick=S, x_thin=T + 4, k_thick=S, k_thin=T + 4,
    z_thick=S, y_end_w=1.0,
    A_thick=C + 6, A_thin=T + 8, K_thick=C, K_thin=T + 8, M_thick=C, M_thin=T + 8, N_thick=C, N_thin=T + 8,
    U_thick=C, U_thin=T + 8, V_thick=C + 4, V_thin=T + 8, X_thick=C, X_thin=T + 8, Y_thick=C, Y_thin=T + 8,
    Z_thick=C, R_leg_w=C, Q_bar_w=C, AE_thick=C, AE_bar_t=C * 0.88,
    g_loop_t=T, g_loop_top_t=T, g_loop_bot_t=T,
    two_bar_t=T, five_bar_t=T, seven_bar_t=T, four_bar_t=T, four_thin=T, fig_thin_k=1.0,
    quest_w=S, quest_thin=T, paren_w=S * 0.9, slash_w=S * 0.75,
    dash_t=T, ring_thick=T * 0.7, ring_thin=T * 0.6,
)
# a large x-height, compact widths and tight spacing; bowls a little squarer than round (superelliptic)
proportions = dict(
    xheight=560, capheight=720, ascender=760,
    sb_straight=44, sb_round=30,
    n_width=455, m_width=395, u_width=455, o_width=560, e_width=530, c_width=505, b_width=545,
    H_width=640, O_width=760,
    o_full_h=0.66, o_full_v=0.66, o_in_full_h=0.64, o_in_full_v=0.64, e_full_h=0.66, e_full_v=0.66,
)
# shallow, clean ink traps: functional at small sizes, a quiet detail large
traps = dict(trap_depth=30, trap_mouth=24, trap_angle=80)
# the f: a hook with room to arc (its top at the ascender, starting low on the stem), cut square
f_hook = dict(f_top=760, f_root_dy=140, f_hook=240, f_end_dir=-15, f_end_y=0.93, sans_cut_f=0)

# ---- signature glyphs ---------------------------------------------------------
# branched k and K: the leg springs from the arm, away from the stem (two trapped crotches, a Y)
_k_arm, _k_join, _k_at = 400, 130, 0.42
_K_arm, _K_join, _K_at = 470, 200, 0.42
branch = dict(k_arm_x=_k_arm, k_join_y=_k_join, k_leg_x0=_k_arm * _k_at, k_leg_y0=_k_join + (560 - _k_join) * _k_at,
              k_leg_x=410, K_arm_x=_K_arm, K_join_y=_K_join, K_leg_x0=_K_arm * _K_at,
              K_leg_y0=_K_join + (720 - _K_join) * _K_at, K_leg_x=500)
# a straight-tailed y (y_tail="straight") and a plain single-storey g
tails = dict(y_end_y=-200, descender_g=-200, gs_w=260, gs_bot=-40, gs_bot_x=0.45, gs_end_y=-110, gs_end_dir=160,
             j_hook=170, j_end_y=-150, j_end_dir=165, a_bt_tilt=0, a_bb_x=250, a_bj_y=100, a_bj_dir=70, a_bs_t=1.1)
# an upright @ whose inner a's stem runs on into the ring (at_style="hook")
at = dict(at_slant=0, at_w=900, at_h=870, at_bot=-150, at_ring_t=T * 0.8, at_pen_k=1.15, at_in_w=370, at_in_h=430,
          at_in_x=0.27, at_in_y=70, at_stem_dy=120, at_hook_y=10, at_hook_x=0.3, at_in_k=0.92, at_in_tr=0.6,
          at_end_x=0.72, at_end_y=0.1, at_end_dir=25, at_right_x=1.0)
# monoline clean-up of serif-era defaults: no wedge serifs (z, Z, 7), full-weight stroke ends (U, parentheses),
# a J whose hook rounds the baseline, a quiet 8 and 5
clean = dict(z_serif=0, z_wedge=0, z_serif_w=0, Z_serif=0, Z_wedge=0, seven_serif=0, seven_wedge=0, seven_top_w=S,
             J_end_y=150, J_end_dir=100, J_bot=200, J_hook=270, U_end_w=1.0, paren_end_w=0.9, paren_bow=150,
             five_stem_w=S * 0.9, one_arm_t=T,
             eight_sp_x0=0.45, eight_sp_x1=0.55, eight_sp_y0=390, eight_sp_y1=390, eight_sp_w=0.3, eight_overlap=0.5,
             five_lean=6, five_top_l=150, five_start_dir=90, five_stem_bot=360,
             dot_r=58, comma_tail=150, comma_root=0.5, comma_tip_w=46, excl_w=S, excl_tip_w=S * 0.75,
             quote_w=S * 0.9, quote_h=200, quest_bot_w=1.0, amp_pen=S,
             G_bar_y=0.5, G_jaw_dx=8)   # the G's bar a little higher, its jaw clear of the bowl's wall

P = kit.params(**weights, **proportions, **traps, **f_hook, **branch, **tails, **at, **clean)
kit.define(font, P, glyphs="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 "
                           "&@?!.,:;-'\"()/",
           terminals=kit.sans_set(P), face_serifs=False, level_trim=True, dot_style="square", ligatures=False,
           l_style="stem", J_style="base", R_leg="line", Q_style="bar", one_style="arm", d_style="bowl",
           a_style="stroke", b_style="oval", r_style="arch", y_left="poly", j_style="hook", g_style="single",
           g_ear="flag", amp_style="stroke", at_style="hook", seven_style="curve",
           fig_ends="cut", y_tail="straight")

# ink traps by rule (ductus.traps)
font.traps = {"depth": "trap_depth", "mouth": "trap_mouth", "angle": "trap_angle",
              # marks too small to trap (a comma's dot-to-tail joint is no crotch), and the G (its jaw meets the
              # bowl at an acute angle that a trap turns into an arrowhead)
              "skip": ["G", "comma", "semicolon", "quotesingle", "quotedbl", "quoteleft", "quoteright",
                       "quotedblleft", "quotedblright"]}

# side bearings (left, right) on top of sb_straight / sb_round, set by eye
font.spacing.update({
    "f": (-10, -40), "r": (0, -25), "L": (0, -35), "t": (0, -10), "T": (-10, -10), "j": (-10, 0), "J": (40, 0),
})

# optical kerning, measured from these outlines (`ductus kern examples/notch/font.py`)
import json as _json
from pathlib import Path as _Path
_kern = _Path(__file__).with_name("kerning.json")
if _kern.exists():
    for _l, _r, _v in _json.loads(_kern.read_text())["pairs"]:
        font.kern(_l, _r, _v)
