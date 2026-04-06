import streamlit as st
import random
import time

st.set_page_config(layout="wide", page_title="우노 모션 배틀")

# ---------------- 1. 스타일 (효과 레이어 독립 고정) ----------------
st.markdown("""
<style>
    /* 효과가 뜰 때 기존 화면(봇, 카드)을 건드리지 않도록 절대 위치 고정 */
    .effect-container {
        position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%);
        z-index: 9999; pointer-events: none; width: 100%; text-align: center;
    }
    @keyframes cubicOut {
        0% { transform: scale(0.3) rotate(0deg); opacity: 0; }
        50% { transform: scale(1.5) rotate(180deg); opacity: 1; }
        100% { transform: scale(2) rotate(360deg); opacity: 0; }
    }
    .effect-symbol {
        font-size: 200px; display: inline-block;
        animation: cubicOut 1s cubic-bezier(0.215, 0.61, 0.355, 1) forwards;
    }
    .vignette {
        position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
        box-shadow: inset 0 0 150px 50px var(--v-color);
        z-index: 9998; pointer-events: none; opacity: 0.5;
    }
    .card-ui {
        width: 100px; height: 150px; border-radius: 12px;
        display: flex; flex-direction: column; justify-content: center; align-items: center;
        color: white; font-weight: bold; box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        border: 3px solid white; text-align: center; margin: auto;
    }
    .wild-bg { background: linear-gradient(45deg, #FF4B4B 25%, #F4C542 25%, #F4C542 50%, #4CAF50 50%, #4CAF50 75%, #2196F3 75%) !important; }
</style>
""", unsafe_allow_html=True)

class Card:
    def __init__(self, color, value):
        self.color, self.value = color, value

# ---------------- 2. 초기화 ----------------
if 'initialized' not in st.session_state:
    colors, values = ['Red', 'Yellow', 'Green', 'Blue'], [str(i) for i in range(10)] + ['Skip', 'Reverse', 'Draw Two']
    deck = [Card(c, v) for c in colors for v in values] * 2
    for _ in range(8): deck.append(Card('Wild', 'Wild' if _ < 4 else 'Wild Draw Four'))
    random.shuffle(deck)
    players = [{"name": n, "hand": [deck.pop() for _ in range(7)], "bot": b} for n, b in [("나", False), ("봇 1", True), ("봇 2", True), ("봇 3", True)]]
    first = deck.pop()
    while first.color == "Wild": deck.insert(0, first); random.shuffle(deck); first = deck.pop()
    st.session_state.update({"deck": deck, "players": players, "discard": [first], "current_color": first.color, "turn": 0, "direction": 1, "stack": 0, "game_msg": "🎮 게임 시작!", "initialized": True, "effect": None, "v_color": None})

# ---------------- 3. 핵심 함수 (즉시 반영) ----------------
def play_card(p_idx, c_idx, chosen_color=None):
    p = st.session_state.players[p_idx]
    card = p["hand"].pop(c_idx)
    st.session_state.discard.append(card)
    st.session_state.current_color = chosen_color if card.color == "Wild" else card.color
    
    if card.value == "Reverse":
        st.session_state.direction *= -1
        st.session_state.effect, st.session_state.v_color = "🔄", {"Red":"#FF4B4B","Yellow":"#F4C542","Green":"#4CAF50","Blue":"#2196F3"}.get(card.color, "#333")
    elif card.value == "Skip":
        st.session_state.effect, st.session_state.v_color = "🚫", {"Red":"#FF4B4B","Yellow":"#F4C542","Green":"#4CAF50","Blue":"#2196F3"}.get(card.color, "#333")
        st.session_state.turn = (st.session_state.turn + st.session_state.direction) % 4
    elif "Draw" in card.value:
        st.session_state.stack += (4 if "Four" in card.value else 2)

    st.session_state.game_msg = f"📢 {p['name']}님이 {card.value}를 냈습니다."
    st.session_state.turn = (st.session_state.turn + st.session_state.direction) % 4
    st.rerun()

def draw_card(p_idx):
    p = st.session_state.players[p_idx]
    count = st.session_state.stack if st.session_state.stack > 0 else 1
    for _ in range(count):
        if st.session_state.deck: p["hand"].append(st.session_state.deck.pop())
    st.session_state.stack = 0
    st.session_state.game_msg = f"🃏 {p['name']}님이 카드를 가져왔습니다."
    # 봇 차례로 넘기기 전에 내 손패 갱신을 위해 즉시 rerun
    if p_idx == 0:
        st.rerun()

# ---------------- 4. 화면 구성 ----------------
# 효과 오버레이 (독립 레이어라 봇 복사 안 됨)
if st.session_state.effect:
    st.markdown(f'<div class="vignette" style="--v-color: {st.session_state.v_color};"></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="effect-container"><div class="effect-symbol">{st.session_state.effect}</div></div>', unsafe_allow_html=True)
    st.session_state.effect = None

st.markdown("<h2 style='text-align: center;'>우노 모션 배틀</h2>", unsafe_allow_html=True)
curr_p = st.session_state.players[st.session_state.turn]

# 상태 바
cols = st.columns(4)
for i, p in enumerate(st.session_state.players):
    with cols[i]:
        border = "4px solid #FF4B4B" if st.session_state.turn == i else "1px solid #ddd"
        st.markdown(f'<div style="border:{border}; padding:10px; border-radius:10px; text-align:center; background:white;"><b>{p["name"]}</b><br>{len(p["hand"])}장</div>', unsafe_allow_html=True)

st.divider()

# 바닥 카드
_, mid, _ = st.columns([1, 0.5, 1])
with mid:
    top = st.session_state.discard[-1]
    color_hex = {"Red":"#FF4B4B","Yellow":"#F4C542","Green":"#4CAF50","Blue":"#2196F3"}.get(st.session_state.current_color, "#333")
    st.markdown(f"<center>색상: <b style='color:{color_hex}'>{st.session_state.current_color}</b></center>", unsafe_allow_html=True)
    is_w = (top.color == "Wild")
    st.markdown(f'<div class="card-ui {"wild-bg" if is_w else ""}" style="background:{{"Red":"#FF4B4B","Yellow":"#F4C542","Green":"#4CAF50","Blue":"#2196F3"}.get(top.color, "#333") if not is_w else ""}; font-size:30px;">{top.value if not is_w else "🌈"}</div>', unsafe_allow_html=True)
    if st.session_state.stack > 0: st.error(f"공격 누적: +{st.session_state.stack}")

st.divider()

# 내 조작
if st.session_state.get('waiting_color'):
    st.markdown("<h3 style='text-align: center;'>🌈 색상 선택</h3>", unsafe_allow_html=True)
    cc = st.columns(4)
    for i, c in enumerate(["Red", "Yellow", "Green", "Blue"]):
        if cc[i].button(c, key=f"sel_{c}", use_container_width=True):
            play_card(0, st.session_state.wild_idx, c)
            st.session_state.waiting_color = False
            st.rerun()

elif not curr_p["bot"]:
    top_c, s = st.session_state.discard[-1], st.session_state.stack
    playable = [i for i, c in enumerate(curr_p["hand"]) if (s > 0 and c.value == top_c.value) or (s == 0 and (c.color == "Wild" or c.color == st.session_state.current_color or c.value == top_c.value))]
    
    st.write("### 🎴 내 카드")
    h_cols = st.columns(len(curr_p["hand"]) if len(curr_p["hand"]) > 0 else 1)
    for i, c in enumerate(curr_p["hand"]):
        with h_cols[i]:
            c_hex = {"Red":"#FF4B4B","Yellow":"#F4C542","Green":"#4CAF50","Blue":"#2196F3"}.get(c.color, "#333")
            st.markdown(f'<div style="background:{c_hex if "Wild" not in c.color else ""}; height:100px; border-radius:8px; border:2px solid white; display:flex; align-items:center; justify-content:center; color:white; font-weight:bold;" class="{"wild-bg" if "Wild" in c.color else ""}">{c.value if "Wild" not in c.color else "🌈"}</div>', unsafe_allow_html=True)
            if st.button("내기", key=f"p_{i}", disabled=(i not in playable), use_container_width=True):
                if c.color == "Wild": st.session_state.waiting_color, st.session_state.wild_idx = True, i; st.rerun()
                else: play_card(0, i)

    st.write("")
    _, b_c, _ = st.columns([1, 0.6, 1])
    with b_c:
        if st.button("🃏 카드 가져오기", use_container_width=True):
            draw_card(0)
            st.session_state.turn = (st.session_state.turn + st.session_state.direction) % 4
            st.rerun()
else:
    # 봇 차례
    time.sleep(1)
    top_c, s = st.session_state.discard[-1], st.session_state.stack
    playable = [i for i, c in enumerate(curr_p["hand"]) if (s > 0 and c.value == top_c.value) or (s == 0 and (c.color == "Wild" or c.color == st.session_state.current_color or c.value == top_c.value))]
    if playable:
        play_card(st.session_state.turn, playable[0], random.choice(["Red", "Yellow", "Green", "Blue"]))
    else:
        draw_card(st.session_state.turn)
        st.session_state.turn = (st.session_state.turn + st.session_state.direction) % 4
        st.rerun()
