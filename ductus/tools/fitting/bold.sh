# bold.sh : fit the sans's Bold master to Geist Sans Bold (results in examples/sans/master_bold.json)
T=$(cd "$(dirname "$0")" && pwd); cd "$T/../.."
m() { echo "== $*"; python $T/mfit.py "$@" 2>&1 | tail -1; }
# 1. global weights and proportions on the core letters
m cd nohHOaesv stem:4 hairline:4 cap_stem:4 round_gain:0.02 xheight:2 overshoot:2 n_width:6 o_width:6 H_width:6 O_width:6 e_width:6
# 2. each glyph's width (and the pairs that share one)
for gw in n:n_width u:u_width m:m_width o:o_width e:e_width c:c_width s:s_width x:x_width w:w_width v:v_width y:y_width z:z_width r:r_width \
          E:E_width H:H_width O:O_width Y:Y_width X:X_width V:V_width A:A_width U:U_width N:N_width M:M_width Z:Z_width C:C_width S:S_width \
          G:G_width F:F_width L:L_width T:T_width W:W_width; do
  g=${gw%%:*}; p=${gw##*:}; m cd $g $p:6
done
for gw in zero:zero_w two:two_w three:three_w five:five_w seven:seven_w six:six_w eight:eight_w nine:nine_w; do
  g=${gw%%:*}; p=${gw##*:}; m cd $g, $p:6
done
# 3. dots, marks and quotes
m cd period,colon,exclam,question,ellipsis, dot_r:4 colon_dy:4
m cd i,j i_dot_r:3 i_dot_y:4
m cd dieresis,idieresis diaer_r:3 diaer_gap:6
m cd acute,grave acute_top_w:6 acute_bot_w:4
m cd quotedblleft,quotedblright,quoteleft,quoteright quote_w:4 quote_gap:6 quote_tip_w:3
m score
# 4. spacing
m respace; m respace
m score
