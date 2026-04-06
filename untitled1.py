import streamlit as st
import random
import time

st.set_page_config(layout="wide", page_title="우노 모션 배틀")

# ---------------- 1. 애니메이션 & 레이어 (완전 독립) ----------------
st.markdown("""
<style>
    .effect-layer {
        position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
        z-index: 9999; pointer-events: none;
        display: flex; align-items: center; justify-content: center;
    }
    @keyframes mergePlus {
        0% { transform: translateX(-150%) scale(0.5); opacity: 0; }
        50% { transform: translateX(-50%) scale(1.5); opacity: 1; }
        100% { transform: translateX(-50%) scale(2); opacity: 0; }
    }
    @keyframes mergeNum {
        0% { transform: translateX(100%) scale(0.5); opacity: 0; }
        50% { transform: translateX(0%) scale(1.5); opacity: 1; }
        100% { transform: translateX(0%) scale(2); opacity: 0; }
    }
    @keyframes cubicRotate {
        0% { transform: scale(0.3) rotate(0deg); opacity: 0; }
        50% { transform: scale(1.5) rotate(180deg); opacity: 1; }
        100% { transform: scale(2) rotate(360deg); opacity: 0; }
    }
    .plus-anim { position: absolute; font-size: 200px; color: white; text-shadow: 5px 5px 15px rgba(0,0,0,0.5); animation: mergePlus 1s cubic-bezier(0.215, 0.61, 0.355, 1) forwards; }
    .num-anim { position: absolute; font-size: 200px; color: white; text-shadow: 5px 5px 15px rgba(0,0,0,0.5); animation: mergeNum 1s cubic-bezier(0.215, 0.61, 0.355, 1) forwards; }
    .symbol-anim { font-size: 200px; color: white; text-shadow: 5px 5px 15px rgba(0,0,0,0.5); animation: cubicRotate 1s cubic-bezier(0.215, 0.61, 0.355, 1) forwards; }
    .vignette {
        position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
        box-shadow: inset 0 0 150px 60px var(--v-color); z-index: 9998;
        pointer-events: none; animation: vFade 1s forwards;
    }
    @keyframes vFade { 0%, 100% { opacity: 0; } 50% { opacity: 0.7; } }
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

# ---------------- 3. 로직 ----------------
def play_card(p_idx, c_idx, chosen_color=None):
    p = st.session_state.players[p_idx]
    card = p["hand"].pop(c_idx)
    st.session_state.discard.append(card)
    st.session_state.current_color = chosen_color if card.color == "Wild" else card.color
    
    if card.value == "Reverse":
        st.session_state.direction *= -1
        st.session_state.effect, st.session_state.v_color = "🔄", card.color
    elif card.value == "Skip":
        st.session_state.effect, st.session_state.v_color = "🚫", card.color
        st.session_state.turn = (st.session_state.turn + st.session_state.direction) % 4
    elif "Draw" in card.value:
        st.session_state.effect = "+2" if "Two" in card.value else "+4"
        st.session_state.v_color = card.color
        st.session_state.stack += (4 if "Four" in card.value else 2)

    st.session_state.game_msg = f"📢 {p['name']}님이 {card.value}를 냈습니다."
    st.session_state.turn = (st.session_state.turn + st.session_state.direction) % 4

def draw_to_hand(p_idx):
    p = st.session_state.players[p_idx]
    count = st.session_state.stack if st.session_state.stack > 0 else 1
    for _ in range(count):
        if st.session_state.deck: p["hand"].append(st.session_state.deck.pop())
    st.session_state.stack = 0
    st.session_state.game_msg = f"🃏 {p['name']}님이 카드를 가져왔습니다."
    # 턴 넘기기 전 강제 갱신으로 카드 들어오는 모션 먼저 보여줌
    st.rerun()

# ---------------- 4. UI 렌더링 ----------------
# [에러 해결] 복잡한 딕셔너리 연산을 변수로 미리 빼서 에러 방지
eff = st.session_state.get('effect')
v_color_name = st.session_state.get('v_color')
color_map = {"Red":"#FF4B4B","Yellow":"#F4C542","Green":"#4CAF50","Blue":"#2196F3"}
v_hex = color_map.get(v_color_name, "#333333")

if eff:
    # 비네트와 효과 레이어를 분리하여 화면 방해 방지
    st.markdown(f'<div class="vignette" style="--v-color: {v_hex};"></div>', unsafe_allow_html=True)
    st.markdown('<div class="effect-layer">', unsafe_allow_html=True)
    if "+" in eff:
        st.markdown(f'<div class="plus-anim">+</div><div class="num-anim">{eff[1]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="symbol-anim">{eff}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.session_state.effect = None

st.markdown("<h2 style='text-align:center;'>우노 모션 배틀</h2>", unsafe_allow_html=True)
curr_p = st.session_state.players[st.session_state.turn]

# 상태 바 (내 카드가 항상 보이도록 고정)
cols = st.columns(4)
for i, p in enumerate(st.session_state.players):
    with cols[i]:
        border = "4px solid #FF4B4B" if st.session_state.turn == i else "1px solid #ddd"
        st.markdown(f'<div style="border:{border}; padding:10px; border-radius:10px; text-align:center; background:white;"><b>{p["name"]}</b><br>{len(p["hand"])}장</div>', unsafe_allow_html=True)

st.divider()

# 중앙 카드 판
_, mid, _ = st.columns([1, 0.6, 1])
with mid:
    top_card = st.session_state.discard[-1]
    t_hex = color_map.get(top_card.color, "#333333")
    st.markdown(f"<center>색상: <b style='color:{t_hex}'>{st.session_state.current_color}</b></center>", unsafe_allow_html=True)
    st.markdown(f"""<div style="background:{t_hex}; width:120px; height:180px; border-radius:15px; border:4px solid white; margin:auto; display:flex; align-items:center; justify-content:center; color:white; font-size:40px; font-weight:bold; box-shadow:0 10px 20px rgba(0,0,0,0.2);">{top_card.value if "Wild" not in top_card.color else "🌈"}</div>""", unsafe_allow_html=True)
    if st.session_state.stack > 0: st.error(f"공격 누적: +{st.session_state.stack}")

st.divider()

# 조작 영역
if st.session_state.get('waiting_color'):
    st.markdown("<h3 style='text-align:center;'>🌈 색상 선택</h3>", unsafe_allow_html=True)
    cc = st.columns(4)
    for i, c in enumerate(["Red", "Yellow", "Green", "Blue"]):
        if cc[i].button(c, use_container_width=True, key=f"btn_{c}"):
            play_card(0, st.session_state.wild_idx, c); st.session_state.waiting_color = False; st.rerun()

elif not curr_p["bot"]:
    top, s = st.session_state.discard[-1], st.session_state.stack
    playable = [i for i, c in enumerate(curr_p["hand"]) if (s > 0 and c.value == top.value) or (s == 0 and (c.color == "Wild" or c.color == st.session_state.current_color or c.value == top.value))]
    
    st.write("### 🎴 내 카드")
    h_cols = st.columns(len(curr_p["hand"]) if len(curr_p["hand"]) > 0 else 1)
    for i, c in enumerate(curr_p["hand"]):
        with h_cols[i]:
            c_hex = color_map.get(c.color, "#333")
            st.markdown(f'<div style="background:{c_hex}; height:100px; border-radius:8px; border:2px solid white; display:flex; align-items:center; justify-content:center; color:white; font-weight:bold;">{c.value if "Wild" not in c.color else "🌈"}</div>', unsafe_allow_html=True)
            if st.button("내기", key=f"p_{i}", disabled=(i not in playable), use_container_width=True):
                if c.color == "Wild": st.session_state.waiting_color, st.session_state.wild_idx = True, i
                else: play_card(0, i)
                st.rerun()

    _, b_c, _ = st.columns([1, 0.6, 1])
    with b_c:
        if st.button("🃏 카드 가져오기", use_container_width=True):
            draw_to_hand(0) # 카드 먼저 들어오고 rerun
            st.session_state.turn = (st.session_state.turn + st.session_state.direction) % 4
            st.rerun()
else:
    # 봇 자동화
    time.sleep(1.2)
    top, s = st.session_state.discard[-1], st.session_state.stack
    playable = [i for i, c in enumerate(curr_p["hand"]) if (s > 0 and c.value == top.value) or (s == 0 and (c.color == "Wild" or c.color == st.session_state.current_color or c.value == top.value))]
    if playable: play_card(st.session_state.turn, playable[0], random.choice(["Red", "Yellow", "Green", "Blue"]))
    else: draw_to_hand(st.session_state.turn); st.session_state.turn = (st.session_state.turn + st.session_state.direction) % 4
    st.rerun()
