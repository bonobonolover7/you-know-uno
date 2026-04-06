import streamlit as st
import random
import time

st.set_page_config(layout="wide", page_title="우노 스피드 배틀")

# ---------------- 1. 애니메이션 & 스타일 (정중앙 고정) ----------------
st.markdown("""
<style>
    @keyframes cubicOut {
        0% { transform: translate(-50%, -50%) scale(0.3) rotate(0deg); opacity: 0; }
        50% { transform: translate(-50%, -50%) scale(1.5) rotate(180deg); opacity: 1; }
        100% { transform: translate(-50%, -50%) scale(2) rotate(360deg); opacity: 0; }
    }
    /* 효과 전용 레이어: 화면 요소를 건드리지 않고 정중앙에 고정 */
    .effect-overlay {
        position: fixed; top: 50%; left: 50%; z-index: 9999;
        pointer-events: none; font-size: 200px;
        animation: cubicOut 1s cubic-bezier(0.215, 0.61, 0.355, 1) forwards;
    }
    .vignette {
        position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
        box-shadow: inset 0 0 150px 50px var(--v-color);
        z-index: 9998; pointer-events: none;
        animation: vignetteFade 1s ease-in-out forwards;
    }
    @keyframes vignetteFade { 0%, 100% { opacity: 0; } 50% { opacity: 0.5; } }

    /* 카드 이동 애니메이션 */
    .card-move-in { animation: slideIn 0.5s ease-out; }
    @keyframes slideIn { 0% { transform: translateX(300px); opacity: 0; } 100% { transform: translateX(0); opacity: 1; } }
    
    .card-play-move { animation: moveToCenter 0.4s ease-out; }
    @keyframes moveToCenter { 0% { transform: translateY(200px) scale(0.5); opacity: 0; } 100% { transform: translateY(0) scale(1); opacity: 1; } }

    .stApp { background-color: #F9F9F9; }
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
        self.color = color
        self.value = value

# ---------------- 2. 유틸리티 ----------------
def get_color_code(color):
    return {"Red": "#FF4B4B", "Yellow": "#F4C542", "Green": "#4CAF50", "Blue": "#2196F3", "Wild": "#333333"}.get(color, "#333333")

def render_card_html(card, extra_class=""):
    bg = get_color_code(card.color)
    is_wild = (card.color == "Wild")
    class_name = f"card-ui {'wild-bg' if is_wild else ''} {extra_class}"
    style = f"background: {bg};" if not is_wild else ""
    val_map = {"Wild": "🌈", "Wild Draw Four": "+4", "Draw Two": "+2", "Reverse": "🔄", "Skip": "🚫"}
    return f"""<div class="{class_name}" style="{style}"><div class="card-type">{card.color.upper()}</div><div class="card-value" style="font-size:30px;">{val_map.get(card.value, card.value)}</div></div>"""

# ---------------- 3. 게임 상태 ----------------
if 'initialized' not in st.session_state:
    colors, values = ['Red', 'Yellow', 'Green', 'Blue'], [str(i) for i in range(10)] + ['Skip', 'Reverse', 'Draw Two']
    deck = [Card(c, v) for c in colors for v in values] * 2
    for _ in range(8): deck.append(Card('Wild', 'Wild' if _ < 4 else 'Wild Draw Four'))
    random.shuffle(deck)
    players = [{"name": n, "hand": [deck.pop() for _ in range(7)], "bot": b} for n, b in [("나", False), ("봇 1", True), ("봇 2", True), ("봇 3", True)]]
    first = deck.pop()
    while first.color == "Wild": deck.insert(0, first); random.shuffle(deck); first = deck.pop()
    st.session_state.update({"deck": deck, "players": players, "discard": [first], "current_color": first.color, "turn": 0, "direction": 1, "stack": 0, "game_msg": "🎮 우노 시작!", "initialized": True, "effect": None, "vignette_color": None})

# ---------------- 4. 로직 ----------------
def trigger_effect(symbol, color):
    st.session_state.effect = symbol
    st.session_state.vignette_color = get_color_code(color)

def play_card(p_idx, c_idx, chosen_color=None):
    p = st.session_state.players[p_idx]
    card = p["hand"].pop(c_idx)
    st.session_state.discard.append(card)
    st.session_state.current_color = chosen_color if card.color == "Wild" else card.color
    
    if card.value == "Reverse":
        st.session_state.direction *= -1
        trigger_effect("🔄", card.color)
    elif card.value == "Skip":
        trigger_effect("🚫", card.color)
        st.session_state.turn = (st.session_state.turn + st.session_state.direction) % 4
    elif "Draw" in card.value:
        st.session_state.stack += (4 if "Four" in card.value else 2)

    st.session_state.game_msg = f"📢 {p['name']}님이 {card.value}를 냈습니다."
    st.session_state.turn = (st.session_state.turn + st.session_state.direction) % 4

def take_card(p_idx, count=1):
    p = st.session_state.players[p_idx]
    for _ in range(count):
        if st.session_state.deck: p["hand"].append(st.session_state.deck.pop())
    # 턴 넘기기 로직은 밖에서 처리

# ---------------- 5. 화면 렌더링 ----------------
# 효과 오버레이 (정중앙 유지)
eff = st.session_state.get('effect')
v_color = st.session_state.get('vignette_color')
if eff:
    st.markdown(f'<div class="vignette" style="--v-color: {v_color};"></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="effect-overlay">{eff}</div>', unsafe_allow_html=True)
    st.session_state.effect = None

st.markdown("<h1 style='text-align: center;'>우노 모션 배틀</h1>", unsafe_allow_html=True)
curr_p = st.session_state.players[st.session_state.turn]
st.info(f"{st.session_state.game_msg} | {'🔥 당신의 차례' if not curr_p['bot'] else f'🤖 {curr_p['name']} 생각 중'}")

# 봇 상태
b_cols = st.columns(3)
for i in range(1, 4):
    p = st.session_state.players[i]
    with b_cols[i-1]:
        st.markdown(f'<div style="border: {"3px solid red" if st.session_state.turn==i else "1px solid #ddd"}; padding:10px; border-radius:10px; background:white; text-align:center;"><b>{p["name"]}</b><br>카드: {len(p["hand"])}장</div>', unsafe_allow_html=True)

st.divider()

# 바닥 카드
_, center_col, _ = st.columns([1, 0.5, 1])
with center_col:
    st.markdown(f"<center>색상: <b style='color:{get_color_code(st.session_state.current_color)}'>{st.session_state.current_color}</b></center>", unsafe_allow_html=True)
    st.markdown(render_card_html(st.session_state.discard[-1], "card-play-move"), unsafe_allow_html=True)
    if st.session_state.stack > 0: st.error(f"공격 누적: +{st.session_state.stack}")

st.divider()

# 내 카드 조작
if st.session_state.get('waiting_color'):
    st.markdown("<h3 style='text-align: center;'>🌈 색상 선택</h3>", unsafe_allow_html=True)
    c_cols = st.columns(4)
    for i, c in enumerate(["Red", "Yellow", "Green", "Blue"]):
        with c_cols[i]:
            if st.button(f"{c} 확정", key=f"sel_{c}", use_container_width=True):
                play_card(0, st.session_state.wild_idx, c)
                st.session_state.waiting_color = False
                st.rerun() # 색 선택 즉시 반영

elif not curr_p["bot"]:
    top, s = st.session_state.discard[-1], st.session_state.stack
    playable = [i for i, c in enumerate(curr_p["hand"]) if (s > 0 and c.value == top.value) or (s == 0 and (c.color == "Wild" or c.color == st.session_state.current_color or c.value == top.value))]

    if not playable:
        if st.button("🃏 낼 카드 없음 (가져오기)", use_container_width=True):
            take_card(0, s if s > 0 else 1)
            st.session_state.stack = 0
            st.session_state.turn = (st.session_state.turn + st.session_state.direction) % 4
            st.rerun() # 가져오기 즉시 반영

    st.write("### 🎴 나의 카드")
    h_cols = st.columns(max(len(curr_p["hand"]), 1))
    for i, c in enumerate(curr_p["hand"]):
        with h_cols[i]:
            st.markdown(render_card_html(c, "card-move-in"), unsafe_allow_html=True)
            if st.button("내기", key=f"p_{i}", disabled=(i not in playable), use_container_width=True):
                if c.color == "Wild":
                    st.session_state.waiting_color, st.session_state.wild_idx = True, i
                else:
                    play_card(0, i)
                st.rerun() # 내기 즉시 반영
    
    if st.button("📢 우노!!! (F)", type="primary", use_container_width=True):
        st.rerun()

else:
    # 봇 차례 로직
    time.sleep(0.8)
    top, s = st.session_state.discard[-1], st.session_state.stack
    playable = [i for i, c in enumerate(curr_p["hand"]) if (s > 0 and c.value == top.value) or (s == 0 and (c.color == "Wild" or c.color == st.session_state.current_color or c.value == top.value))]
    
    if playable:
        play_card(st.session_state.turn, playable[0], random.choice(["Red", "Yellow", "Green", "Blue"]))
    else:
        take_card(st.session_state.turn, s if s > 0 else 1)
        st.session_state.stack = 0
        st.session_state.turn = (st.session_state.turn + st.session_state.direction) % 4
    st.rerun()
