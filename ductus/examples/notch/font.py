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
    n_join_thin=74, r_join_thin=78,
    a_bowl_thin=T, a_bowl_thin_b=T, a_top_thin=74, a_bot_thin=T,
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
    dash_t=T, ring_thick=T * 0.7,
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
             j_hook=170, j_end_y=-150, j_end_dir=165,
             # the a (a_style="bowl", a_hood="one"): a round bowl under an even, level-pen hood that runs on into the stem
             # as one stroke (untrapped: a trap at its bowl's crotch cut a needle up the stem)
             a_bowl_t=370, a_stem_x=445, a_bowl_l=30, a_term_y=430, a_term_x=95,
             a_term_dir=95, a_top_x=0.5, a_stem_bot=-6)
# an upright @ whose inner a's stem runs on into the ring (at_style="hook")
at = dict(at_slant=0, at_w=900, at_h=870, at_bot=-150, at_ring_t=T * 0.8, at_pen_k=1.15, at_in_w=370, at_in_h=430,
          at_in_x=0.27, at_in_y=70, at_stem_dy=120, at_hook_y=10, at_hook_x=0.3, at_in_k=0.92, at_in_tr=0.6,
          at_end_x=0.72, at_end_y=0.1, at_end_dir=25, at_right_x=1.0)
# monoline clean-up of serif-era defaults: no wedge serifs (z, Z, 7), full-weight stroke ends (U, parentheses),
# a J whose hook rounds the baseline, a quiet 8 and 5
clean = dict(z_serif=0, z_wedge=0, z_serif_w=0, Z_serif=0, Z_wedge=0, seven_serif=0, seven_wedge=0, seven_top_w=S,
             J_end_y=150, J_end_dir=100, J_bot=200, J_hook=270, U_end_w=1.0, paren_end_w=0.9, paren_bow=150,
             five_stem_w=S * 0.9,
             eight_sp_x0=0.45, eight_sp_x1=0.55, eight_sp_y0=390, eight_sp_y1=390, eight_sp_w=0.3, eight_overlap=0.5,
             five_lean=6, five_top_l=120, five_start_dir=90, five_stem_bot=360,
             dot_r=58, comma_tail=150, comma_root=0.5, comma_tip_w=46, excl_w=S, excl_tip_w=S * 0.75,
             quote_w=S * 0.9, quote_h=200, quest_bot_w=1.0, amp_pen=S,
             G_bar_y=0.5, G_jaw_dx=8,
             e_bar_rin=-20,   # the e's bar runs into the bowl's wall (stopping short left a hairline slit)
             # joins that left rough edges at this weight: the N's diagonal no wider than its stem at the top, the
             # W's middle apex trimmed level (its thin stroke's square end poked above the cap line), the C's
             # lower cut clear of its heavier bottom wall, the 3's and 5's lower ends cut level
             N_dx0=24, W_apex_trim=120,
             # the m's second arch set onto the first one's leg below its still-curving shoulder (the first arch's
             # outer curve poked into the second counter as a hairline)
             m_join_dx=-20,
             # the n, h, m and u legs start where their arch has turned upright (higher, the leg's square corner
             # stood out past the still-curving arch as a shelf)
             n_leg_top=0.7, u_leg_top=0.7,
             # the &'s upper loop wide enough to keep its counter open at this weight
             amp_loop_w=340, amp_w=670, amp_loop_y=600,
             # a short level t tail with a square end, the 1's arm at full weight, a sturdier u join, the 9's hook
             # leaving its bowl lower
             t_tail=130, t_tail_y=30, t_end_dir=0, t_end_w=1.0, sans_cut_t=0, t_turn=130, one_arm_t=S, one_arm_y=590,
             u_join_thin=90, u_join_at=0.75, nine_root_y=0.4, nine_root_x=0.5,
             # monoline s, S, 6 and 9: an even spine (the serif's spine thins its ends to 60%) and hooks at full
             # weight to their ends; the 5's bar reaching past its stem
             # the c's and e's lower terminals ending blunt (the cut clear of the heavier bottom wall)
             e_cut_y=140, e_term_y=200, c_cut_y=130, c_term_y=190, e_cut_h1=0.5, e_cut_h2=0.4, c_cut_angle=200,
             c_cut_h1=0.5, c_cut_h2=0.4,
             s_ends=0.9, s_swell=0.95, s_width=430, S_width=540, six_hook_w=0.7, nine_hook_w=0.7,
             C_cut_y=150, C_term_y=230, C_cut_angle=200, C_cut_h1=0.5, C_cut_h2=0.4, sans_cut_fig_low=90)   # the G's bar a little higher, its jaw clear of the bowl's wall

# marks and symbols at the face's weight (the kit's defaults are a high-contrast serif's hairlines)
marks = dict(acute_bot_w=70, acute_top_w=112, circ_leg_w=T * 0.8, circ_top_w=124, circ_in=52, tilde_w=T * 0.8,
             diaer_r=48, diaer_gap=200, ring_thin=T * 0.6, ring_w=190, ring_h=180,
             ced_w=S * 0.75, ced_thin=T * 0.7, ced_root_dx=30, ced_neck=-55, ced_len=130, ced_drop=210,
             ced_curl_dy=-20, ced_bot_x=0.15, ced_end_x=0.5, ced_end_dy=55, ced_end_dir=100, sans_cut_ced=100)
symbols = dict(math_t=T * 0.85, eq_t=T * 0.8, lt_t=T * 0.85, under_t=T * 0.85, bar_w=S * 0.75, brk_stem=S * 0.85,
               brk_arm=T * 0.85, brace_pen=S * 0.85, hash_t=T * 0.85, hash_bar_t=T * 0.8, pct_thick=S * 0.8,
               pct_slash_w=T * 0.8, deg_t=T * 0.6, dollar_bar=S * 0.6, caret_t=T * 0.85, tl_w=T * 0.85,
               ast_tip_w=80, ast_root_w=30,
               math_w=470, tl_len=380, tl_amp=90,
               guil_w=220, guil_h=460, guil_t=S * 0.85, guil_y=290, guil_gap=55)   # math signs and ~ sized to the large x-height

P = kit.params(**weights, **proportions, **traps, **f_hook, **branch, **tails, **at, **clean, **marks, **symbols)
kit.define(font, P, glyphs="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 "
                           "ÀÁÂÃÄÅÇÈÉÊËÌÍÎÏÑÒÓÔÕÖÙÚÛÜÝàáâãäåçèéêëìíîïñòóôõöùúûüýÿı´`¨¸˚ÆŒØæœøß"
                           "&*%·#$+<=>@[\\]^_{|}~…•°×€£¢.,:;-–—'\"‘’“”!?¿¡()/«»‹›",
           terminals=kit.sans_set(P), face_serifs=False, level_trim=True, dot_style="square", ligatures=False,
           l_style="stem", J_style="base", R_leg="line", Q_style="bar", one_style="arm", d_style="bowl",
           a_style="bowl", a_hood="one", b_style="oval", r_style="arch", y_left="poly", j_style="hook", g_style="single",
           g_ear="flag", amp_style="stroke", at_style="hook", seven_style="curve",
           fig_ends="cut", y_tail="straight", ced_style="tick2")

# ink traps by rule (ductus.traps)
# overlap leftovers (steps, nubs, spikes under 16 units) tidied by rule first (ductus.tidy)
font.tidy = {"step": 16, "spike": 150, "hole": 120}
font.traps = {"depth": "trap_depth", "mouth": "trap_mouth", "angle": "trap_angle", "min_angle": 30,
              # marks too small to trap (a comma's dot-to-tail joint is no crotch); A (its crossbar corners
              # made it busy), G, e, 8 and Q, whose acute
              # corners are a counter's or a tail's, not two strokes' crotch (a trap there cuts a sliver into
              # a thin bar or turns the G's jaw into an arrowhead)
              "skip": ["A", "G", "a", "agrave", "aacute", "acircumflex", "atilde", "adieresis", "aring", "e", "f", "eight", "Q", "comma", "semicolon", "quotesingle", "quotedbl", "quoteleft", "quoteright",
                       "quotedblleft", "quotedblright"]}

# side bearings (left, right) on top of sb_straight / sb_round, set by eye
font.spacing.update({
    "f": (-10, -40), "r": (0, -25), "L": (0, -35), "t": (0, -10), "T": (-10, -10), "j": (-10, 0), "J": (40, 0),
    # the guillemets sit apart from the word they mark
    "guillemotleft": (0, 20), "guillemotright": (20, 0), "guilsinglleft": (0, 20), "guilsinglright": (20, 0),
})

# optical kerning, measured from these outlines (`ductus kern examples/notch/font.py`)
import json as _json
from pathlib import Path as _Path
_kern = _Path(__file__).with_name("kerning.json")
if _kern.exists():
    for _l, _r, _v in _json.loads(_kern.read_text())["pairs"]:
        font.kern(_l, _r, _v)

# ---- a weight axis (wght 300-700) ---------------------------------------------------------
# The Bold is the Regular with its stroke thicknesses scaled by kit.weight_master (stems x k, horizontals and
# thin parts x kh, so counters stay open), then its own values below: deeper ink traps (a heavier crotch fills
# in sooner) and a little more width where the heavier stems would crowd the counters. Kerning per master
# (`ductus kern examples/notch/font.py --master 700`).
_bold = dict(
    trap_depth=34, trap_mouth=26, space_add=-80,   # the word space at the Regular's share of an n
    # wider letters, so the heavier stems leave the counters open; slightly tighter side bearings
    n_width=490, m_width=425, u_width=490, o_width=605, e_width=575, c_width=545, b_width=585, s_width=470,
    a_stem_x=485, H_width=690, O_width=815, S_width=580, sb_straight=46, sb_round=32,
    # counters kept open: the e's eye larger (its bar lower and lighter), the a's bowl wider, lower and lighter at top and bottom,
    # the %'s rings wider and lighter; the ? stem stopping clear of its heavier dot, with a shorter hook end;
    # the t's longer bar and tail
    e_bar_y=0.5, e_bar_t=100, a_term_y=440, a_term_x=90, a_bowl_l=10, a_bowl_t=340, a_bowl_thin=105, a_bowl_thin_b=105,
    pct_ring_w=330, pct_ring_h=360, pct_thick=105, quest_end_y=540, quest_bot=225,
    t_tail=160, t_turn=160, t_tail_y=45, t_end_dir=10, t_bar_l=110, t_bar_r=180,
    # the e's and c's lower terminals cut lower and flatter: the heavier bottom wall otherwise closes the aperture
    e_cut_y=100, e_term_y=190, c_cut_y=100, c_term_y=185, e_cut_angle=188, c_cut_angle=188,
    # no counter may close at the heavier weight (a variable font interpolates outlines of the same structure):
    # the ss's lower stroke ends clear of the stem, the @'s ring a little larger around its hook, the &'s loop wider
    ss_end_x=200, ss_end_y=70, ss_waist_x=210, ss_lr_x=470, at_bot=-180, at_h=920, at_w=960,
    amp_loop_w=440, amp_loop_y=590,
    ring_w=230, ring_h=210, ring_thick=78, ring_thin=68, ring_y0=600,   # the ring mark's counter stays open, clear of the a
)


# the Light: thinner strokes with the thins following less (kh), so it stays monolinear; shallower traps (a thin
# crotch hardly fills in: they become a quiet detail) and a little narrower
_light = dict(
    trap_depth=20, trap_mouth=18, space_add=30,
)
# ...and narrower: every letter's and figure's width (and the x positions that don't follow them) x 0.94
_NARROW = [n for n in kit.DEFAULTS if n.endswith("_width")] + [
    "zero_w", "two_w", "three_w", "five_w", "six_w", "seven_w", "eight_w", "nine_w", "a_stem_x",
    "k_arm_x", "k_leg_x0", "k_leg_x", "K_arm_x", "K_leg_x0", "K_leg_x", "amp_w", "at_w", "gs_w"]


def _master(params, setting):
    ov = kit.weight_master(params, setting["k"], setting.get("kh"))
    if "narrow" in setting:
        ov.update({n: float(params[n]) * setting["narrow"] for n in _NARROW if n in params})
    ov.update(setting.get("params", {}))
    return ov


font.variable = {
    "tag": "wght", "name": "Weight", "default": 400,
    "masters": {300: {"k": 0.7, "kh": 0.78, "narrow": 0.94, "params": _light}, 700: {"k": 1.32, "kh": 1.2, "params": _bold}},
    "params": _master,
    "instances": {"Light": 300, "Regular": 400, "Medium": 500, "SemiBold": 600, "Bold": 700},
    "kerning": {_loc: {(_l, _r): _v for _l, _r, _v in _json.loads(_p.read_text())["pairs"]}
                for _loc in (300, 700) if (_p := _Path(__file__).with_name(f"kerning_{_loc}.json")).exists()},
}
