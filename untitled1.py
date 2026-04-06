import streamlit as st
import random
import time

st.set_page_config(layout="wide", page_title="UNO Stack Edition")

# ---------------- 1. 스타일 (배경 및 중앙 정렬 UI) ----------------
st.markdown("""
<style>
    .stApp { background-color: #F9F9F9; }
    
    .main-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }

    .card-ui {
        width: 110px;
        height: 160px;
        border-radius: 12px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        color: white;
        font-weight: bold;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        border: 3px solid white;
        text-align: center;
        margin: auto;
    }

    .card-value { font-size: 26px; }
    .card-type { font-size: 11px; opacity: 0.9; margin-bottom: 5px; }

    /* 우노 버튼 스타일 */
    div.stButton > button[kind="primary"] {
        background-color: #FF0000 !important;
        color: white !important;
        border-radius: 10px;
        font-weight: bold;
        border: none;
    }

    .bot-box {
        background: white;
        padding: 10px;
        border-radius: 12px;
        border: 1px solid #ddd;
        text-align: center;
        min-width: 120px;
    }
    
    /* 와일드 카드 4색 표현을 위한 배경 */
    .wild-bg {
        background: linear-gradient(45deg, #FF4B4B 25%, #F4C542 25%, #F4C542 50%, #4CAF50 50%, #4CAF50 75%, #2196F3 75%);
    }
</style>
""", unsafe_allow_html=True)

# ---------------- 2. 로직 및 세션 초기화 ----------------
class Card:
    def __init__(self, color, value):
        self.color = color # Red, Yellow, Green, Blue, Wild
        self.value = value # 0-9, Skip, Reverse, Draw Two, Wild, Wild Draw Four

def init_game():
    colors = ['Red', 'Yellow', 'Green', 'Blue']
    values = [str(i) for i in range(10)] + ['Skip', 'Reverse', 'Draw Two']
    deck = [Card(c, v) for c in colors for v in values] * 2
    for _ in range(4):
        deck.append(Card('Wild', 'Wild'))
        deck.append(Card('Wild', 'Wild Draw Four'))
    random.shuffle(deck)

    players = [
        {"name": "YOU", "hand": [], "bot": False},
        {"name": "BOT 1", "hand": [], "bot": True},
        {"name": "BOT 2", "hand": [], "bot": True},
        {"name": "BOT 3", "hand": [], "bot": True}
    ]
    for p in players:
        p["hand"] = [deck.pop() for _ in range(7)]

    while True:
        first = deck.pop()
        if first.color != "Wild" and first.value.isdigit(): break
        deck.insert(0, first)
        random.shuffle(deck)

    st.session_state.update({
        "deck": deck, "players": players, "discard": [first],
        "current_color": first.color, "turn": 0, "direction": 1,
        "stack": 0, "game_over": False, "waiting_color": False
    })

if 'deck' not in st.session_state:
    init_game()

# ---------------- 3. 유틸리티 ----------------
def get_color_code(color):
    codes = {"Red": "#FF4B4B", "Yellow": "#F4C542", "Green": "#4CAF50", "Blue": "#2196F3", "Wild": "#333333"}
    return codes.get(color, "#333333")

def render_card_html(card):
    bg = get_color_code(card.color)
    style = f"background: {bg};"
    if card.color == "Wild":
        style = ""
        class_name = "card-ui wild-bg"
    else:
        class_name = "card-ui"
    
    val_map = {"Wild": "🌈", "Wild Draw Four": "+4", "Draw Two": "+2", "Reverse": "🔄", "Skip": "🚫"}
    display_val = val_map.get(card.value, card.value)
    
    return f"""<div class="{class_name}" style="{style}">
                <div class="card-type">{card.color.upper()}</div>
                <div class="card-value">{display_val}</div>
              </div>"""

def next_p():
    st.session_state.turn = (st.session_state.turn + st.session_state.direction) % 4

# ---------------- 4. 게임 핵심 로직 (스택/누적 포함) ----------------
def play_action(p_idx, c_idx, chosen_color=None):
    p = st.session_state.players[p_idx]
    card = p["hand"].pop(c_idx)
    st.session_state.discard.append(card)
    st.session_state.current_color = chosen_color if card.color == "Wild" else card.color

    # 스택 누적 로직
    if card.value == "Draw Two":
        st.session_state.stack += 2
    elif card.value == "Wild Draw Four":
        st.session_state.stack += 4
    
    # 일반 특수카드 처리
    if card.value == "Skip":
        next_p() # 한 명 건너뜀
    elif card.value == "Reverse":
        st.session_state.direction *= -1
    
    next_p()

def handle_penalty(p_idx):
    p = st.session_state.players[p_idx]
    for _ in range(st.session_state.stack):
        p["hand"].append(st.session_state.deck.pop())
    st.session_state.stack = 0
    next_p()

# ---------------- 5. UI 렌더링 ----------------
st.markdown("<h1 style='text-align: center;'>UNO STACK GAME</h1>", unsafe_allow_html=True)

# (1) 봇 정보 표시
bot_cols = st.columns(3)
for i in range(1, 4):
    with bot_cols[i-1]:
        p = st.session_state.players[i]
        border = "3px solid red" if st.session_state.turn == i else "1px solid #ddd"
        st.markdown(f"""<div class="bot-box" style="border: {border}">
                        <b>{p['name']}</b><br>{len(p['hand'])} cards</div>""", unsafe_allow_html=True)

st.divider()

# (2) 중앙 바닥 카드 (정중앙 배치)
_, center_col, _ = st.columns([1, 0.4, 1])
with center_col:
    top_card = st.session_state.discard[-1]
    st.markdown(f"<center><b>CURRENT COLOR: {st.session_state.current_color}</b></center>", unsafe_allow_html=True)
    st.markdown(render_card_html(top_card), unsafe_allow_html=True)
    if st.session_state.stack > 0:
        st.error(f"WARNING: STACK +{st.session_state.stack}")

st.divider()

# (3) 플레이어 조작 영역
curr_p = st.session_state.players[st.session_state.turn]

if st.session_state.waiting_color:
    st.info("Choose a color for your Wild card!")
    c1, c2, c3, c4 = st.columns(4)
    for i, c in enumerate(["Red", "Yellow", "Green", "Blue"]):
        if [c1, c2, c3, c4][i].button(c):
            play_action(0, st.session_state.wild_idx, c)
            st.session_state.waiting_color = False
            st.rerun()

elif not curr_p["bot"]:
    st.write("### 🎴 YOUR TURN")
    
    # 낼 수 있는 카드 필터링 (스택 상황 고려)
    playable_indices = []
    top = st.session_state.discard[-1]
    
    for i, c in enumerate(curr_p["hand"]):
        can_play = False
        if st.session_state.stack > 0:
            # 공격 누적 시에는 동일한 공격 카드만 내서 방어 가능
            if top.value in ["Draw Two", "Wild Draw Four"] and c.value == top.value:
                can_play = True
        else:
            # 일반 상황
            if c.color == "Wild" or c.color == st.session_state.current_color or c.value == top.value:
                can_play = True
        if can_play: playable_indices.append(i)

    # 카드 출력
    cols = st.columns(len(curr_p["hand"]) + 1)
    for i, c in enumerate(curr_p["hand"]):
        with cols[i]:
            st.markdown(render_card_html(c), unsafe_allow_html=True)
            if st.button("Play", key=f"p_{i}", disabled=(i not in playable_indices)):
                if c.color == "Wild":
                    st.session_state.waiting_color = True
                    st.session_state.wild_idx = i
                else:
                    play_action(0, i)
                st.rerun()
    
    # 뽑기/페널티 받기 버튼
    with cols[-1]:
        btn_label = f"Take +{st.session_state.stack}" if st.session_state.stack > 0 else "Draw Card"
        if st.button(btn_label, type="primary"):
            if st.session_state.stack > 0:
                handle_penalty(0)
            else:
                curr_p["hand"].append(st.session_state.deck.pop())
                next_p()
            st.rerun()

else:
    # 봇 AI 턴
    st.info(f"🤖 {curr_p['name']} is thinking...")
    time.sleep(1.5)
    
    top = st.session_state.discard[-1]
    playable = []
    for i, c in enumerate(curr_p["hand"]):
        if st.session_state.stack > 0:
            if c.value == top.value: playable.append(i)
        else:
            if c.color == "Wild" or c.color == st.session_state.current_color or c.value == top.value:
                playable.append(i)
    
    if playable:
        idx = playable[0]
        c = curr_p["hand"][idx]
        if c.color == "Wild":
            # 봇은 손에 가장 많은 색상 선택
            hand_colors = [h.color for h in curr_p["hand"] if h.color != "Wild"]
            best = max(set(hand_colors), key=hand_colors.count) if hand_colors else "Red"
            play_action(st.session_state.turn, idx, best)
        else:
            play_action(st.session_state.turn, idx)
    else:
        if st.session_state.stack > 0:
            handle_penalty(st.session_state.turn)
        else:
            curr_p["hand"].append(st.session_state.deck.pop())
            next_p()
    st.rerun()

if st.sidebar.button("RESET GAME"):
    st.session_state.clear()
    st.rerun()
