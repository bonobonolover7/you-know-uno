import streamlit as st
import random
import time

st.set_page_config(layout="wide", page_title="우노 모션 배틀")

# ---------------- 1. 애니메이션 & 스타일 (정중앙 합체) ----------------
st.markdown("""
<style>
    /* 효과 레이어: 다른 요소(봇 등)를 밀어내지 않음 */
    .effect-overlay {
        position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%);
        z-index: 9999; pointer-events: none; width: 100%; display: flex; justify-content: center;
    }
    /* +는 왼쪽에서, 숫자는 오른쪽에서 와서 합체 */
    @keyframes mergeLeft {
        0% { transform: translateX(-150%) scale(0.5); opacity: 0; }
        50% { transform: translateX(-50%) scale(1.5); opacity: 1; }
        100% { transform: translateX(-50%) scale(2.2); opacity: 0; }
    }
    @keyframes mergeRight {
        0% { transform: translateX(100%) scale(0.5); opacity: 0; }
        50% { transform: translateX(0%) scale(1.5); opacity: 1; }
        100% { transform: translateX(0%) scale(2.2); opacity: 0; }
    }
    @keyframes symbolRotate {
        0% { transform: scale(0.3) rotate(0deg); opacity: 0; }
        50% { transform: scale(1.5) rotate(180deg); opacity: 1; }
        100% { transform: scale(2) rotate(360deg); opacity: 0; }
    }
    .anim-plus { position: absolute; font-size: 200px; color: white; text-shadow: 4px 4px 10px rgba(0,0,0,0.5); animation: mergeLeft 1s forwards; }
    .anim-num { position: absolute; font-size: 200px; color: white; text-shadow: 4px 4px 10px rgba(0,0,0,0.5); animation: mergeRight 1s forwards; }
    .anim-symbol { font-size: 200px; color: white; text-shadow: 4px 4px 10px rgba(0,0,0,0.5); animation: symbolRotate 1s forwards; }

    .vignette {
        position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
        box-shadow: inset 0 0 150px 50px var(--v-color);
        z-index: 9998; pointer-events: none; animation: vFade 1s forwards;
    }
    @keyframes vFade { 0%, 100% { opacity: 0; } 50% { opacity: 0.6; } }

    .card-ui {
        width: 100px; height: 150px; border-radius: 12px; border: 3px solid white;
        display: flex; flex-direction: column; justify-content: center; align-items: center;
        color: white; font-weight: bold; box-shadow: 0 4px 15px rgba(0,0,0,0.2); margin: auto;
    }
    .wild-bg { background: linear-gradient(45deg, #FF4B4B 25%, #F4C542 25%, #F4C542 50%, #4CAF50 50%, #4CAF50 75%, #2196F3 75%) !important; }
</style>
""", unsafe_allow_html=True)

class Card:
    def __init__(self, color, value):
        self.color, self.value = color, value

# ---------------- 2. 유틸리티 (에러 방지용 변수 처리) ----------------
COLOR_MAP = {"Red": "#FF4B4B", "Yellow": "#F4C542", "Green": "#4CAF50", "Blue": "#2196F3", "Wild": "#333333"}

# ---------------- 3. 초기화 ----------------
if 'initialized' not in st.session_state:
    colors, values = ['Red', 'Yellow', 'Green', 'Blue'], [str(i) for i in range(10)] + ['Skip', 'Reverse', 'Draw Two']
    deck = [Card(c, v) for c in colors for v in values] * 2
    for _ in range(8): deck.append(Card('Wild', 'Wild' if _ < 4 else 'Wild Draw Four'))
    random.shuffle(deck)
    players = [{"name": n, "hand": [deck.pop() for _ in range(7)], "bot": b} for n, b in [("나", False), ("봇 1", True), ("봇 2", True), ("봇 3", True)]]
    first = deck.pop()
    while first.color == "Wild": deck.insert(0, first); random.shuffle(deck); first = deck.pop()
    st.session_state.update({"deck": deck, "players": players, "discard": [first], "current_color": first.color, "turn": 0, "direction": 1, "stack": 0, "game_msg": "🎮 시작!", "initialized": True, "effect": None, "eff_col": None})

# ---------------- 4. 핵심 로직 (즉시 반영) ----------------
def play_card(p_idx, c_idx, chosen_color=None):
    p = st.session_state.players[p_idx]
    card = p["hand"].pop(c_idx)
    st.session_state.discard.append(card)
    st.session_state.current_color = chosen_color if card.color == "Wild" else card.color
    
    if card.value == "Reverse":
        st.session_state.direction *= -1
        st.session_state.effect, st.session_state.eff_col = "🔄", COLOR_MAP.get(card.color)
    elif card.value == "Skip":
        st.session_state.effect, st.session_state.eff_col = "🚫", COLOR_MAP.get(card.color)
        st.session_state.turn = (st.session_state.turn + st.session_state.direction) % 4
    elif "Draw" in card.value:
        st.session_state.effect = "+2" if "Two" in card.value else "+4"
        st.session_state.eff_col = COLOR_MAP.get(card.color)
        st.session_state.stack += (4 if "Four" in card.value else 2)

    st.session_state.game_msg = f"📢 {p['name']}: {card.value}"
    st.session_state.turn = (st.session_state.turn + st.session_state.direction) % 4
    st.rerun()

def get_card(p_idx):
    p = st.session_state.players[p_idx]
    count = st.session_state.stack if st.session_state.stack > 0 else 1
    for _ in range(count):
        if st.session_state.deck: p["hand"].append(st.session_state.deck.pop())
    st.session_state.stack = 0
    st.session_state.game_msg = f"🃏 {p['name']} 카드 수령"
    if p_idx == 0: st.rerun()

# ---------------- 5. 화면 렌더링 ----------------
# 효과 (오버레이 방식 - 봇 복사 안 됨)
eff = st.session_state.get('effect')
if eff:
    st.markdown(f'<div class="vignette" style="--v-color: {st.session_state.eff_col};"></div>', unsafe_allow_html=True)
    st.markdown('<div class="effect-overlay">', unsafe_allow_html=True)
    if "+" in eff:
        st.markdown(f'<div class="anim-plus">+</div><div class="anim-num">{eff[1]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="anim-symbol">{eff}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.session_state.effect = None

st.markdown("<h2 style='text-align:center;'>우노 모션 배틀</h2>", unsafe_allow_html=True)

# 봇 상태 바
cols = st.columns(4)
for i, p in enumerate(st.session_state.players):
    with cols[i]:
        bg = "#FFEBEE" if st.session_state.turn == i else "white"
        st.markdown(f'<div style="background:{bg}; padding:10px; border-radius:10px; border:2px solid #ddd; text-align:center;"><b>{p["name"]}</b><br>{len(p["hand"])}장</div>', unsafe_allow_html=True)

st.divider()

# 바닥 카드 (SyntaxError 해결: 변수 미리 계산)
_, mid, _ = st.columns([1, 0.5, 1])
with mid:
    top = st.session_state.discard[-1]
    curr_col_hex = COLOR_MAP.get(st.session_state.current_color, "#333")
    top_col_hex = COLOR_MAP.get(top.color, "#333")
    st.markdown(f"<center>색상: <b style='color:{curr_col_hex}'>{st.session_state.current_color}</b></center>", unsafe_allow_html=True)
    
    wild_class = "wild-bg" if top.color == "Wild" else ""
    st.markdown(f'<div class="card-ui {wild_class}" style="background:{top_col_hex if not wild_class else ""}; font-size:40px;">{top.value if "Wild" not in top.color else "🌈"}</div>', unsafe_allow_html=True)
    if st.session_state.stack > 0: st.error(f"STACK +{st.session_state.stack}")

st.divider()

# 내 턴 조작
curr_p = st.session_state.players[st.session_state.turn]
if st.session_state.get('waiting_color'):
    st.markdown("<center>🌈 색상을 고르세요</center>", unsafe_allow_html=True)
    cc = st.columns(4)
    for i, c in enumerate(["Red", "Yellow", "Green", "Blue"]):
        if cc[i].button(c, key=f"c_{c}", use_container_width=True):
            play_card(0, st.session_state.wild_idx, c)
            st.session_state.waiting_color = False

elif not curr_p["bot"]:
    top_c, s = st.session_state.discard[-1], st.session_state.stack
    playable = [i for i, c in enumerate(curr_p["hand"]) if (s > 0 and c.value == top_c.value) or (s == 0 and (c.color == "Wild" or c.color == st.session_state.current_color or c.value == top_c.value))]
    
    st.write("### 🎴 내 손패")
    h_cols = st.columns(max(len(curr_p["hand"]), 1))
    for i, c in enumerate(curr_p["hand"]):
        with h_cols[i]:
            c_hex = COLOR_MAP.get(c.color, "#333")
            w_cls = "wild-bg" if c.color == "Wild" else ""
            st.markdown(f'<div class="card-ui {w_cls}" style="background:{c_hex if not w_cls else ""}; height:100px;">{c.value if "Wild" not in c.color else "🌈"}</div>', unsafe_allow_html=True)
            if st.button("내기", key=f"p_{i}", disabled=(i not in playable), use_container_width=True):
                if c.color == "Wild": st.session_state.waiting_color, st.session_state.wild_idx = True, i; st.rerun()
                else: play_card(0, i)

    st.write("")
    _, b_c, _ = st.columns([1, 0.6, 1])
    with b_c:
        if st.button("🃏 카드 가져오기", use_container_width=True):
            get_card(0)
            st.session_state.turn = (st.session_state.turn + st.session_state.direction) % 4
            st.rerun()
else:
    time.sleep(1)
    top_c, s = st.session_state.discard[-1], st.session_state.stack
    playable = [i for i, c in enumerate(curr_p["hand"]) if (s > 0 and c.value == top_c.value) or (s == 0 and (c.color == "Wild" or c.color == st.session_state.current_color or c.value == top_c.value))]
    if playable: play_card(st.session_state.turn, playable[0], random.choice(["Red", "Yellow", "Green", "Blue"]))
    else: 
        get_card(st.session_state.turn)
        st.session_state.turn = (st.session_state.turn + st.session_state.direction) % 4
        st.rerun()
