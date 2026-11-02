# bold2.sh : second Bold pass -- tails, and the glyphs whose topology the bold changed
T=$(cd "$(dirname "$0")" && pwd); cd "$T/../.."
m() { echo "== $*"; python $T/mfit.py "$@" 2>&1 | tail -1; }
m rs t 120 t_turn:10 t_tail:10 t_tail_y:5 t_bot_dy:4 t_bar_l:6 t_bar_r:6
m rs l 100 l_turn:10 l_tail:10 l_tail_y:5 l_bot_dy:4
m rs a 160 a_turn:8 a_tail:6 a_foot_dy:4 a_bj_y:10 a_bj_dir:5 a_bb_x:8 a_bs_thick:6 a_bs_thin:5 a_bt_y:8 a_bl_x:6 a_stem_x:5 a_term_x:6 a_term_y:6
m rs ring, 80 ring_thick:5 ring_thin:5 ring_w:8
m rs at, 160 at_ring_t:4 at_in_w:10 at_in_h:10 at_in_x:0.02 at_in_y:8 at_root_dy:8 at_w:10 at_h:10 at_pen_k:0.05
m respace; m respace
m score
