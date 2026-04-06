import streamlit as st
import random
import time

st.set_page_config(layout="wide", page_title="UNO Stack Edition")

# ---------------- 1. 스타일 ----------------
st.markdown("""
<style>
    .stApp { background-color: #F9F9F9; }
    .card-ui {
        width: 110px; height: 160px; border-radius: 12px;
        display: flex; flex-direction: column; justify-content: center; align-items: center;
        color: white; font-weight: bold; box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        border: 3px solid white; text-align: center; margin: auto;
    }
    .card-value { font-size: 26px; }
    .card-type { font-size: 11px; opacity: 0.9; margin-bottom: 5px; }
    div.stButton > button[kind="primary"] {
        background-color: #FF0000 !important; color: white !important;
        border-radius: 10px; font-weight: bold; border: none; height: 50px;
    }
    .bot-box {
        background: white; padding: 10px; border-radius: 12px;
        border: 1px solid #ddd; text-align: center; min-width: 120px;
    }
    .wild-bg {
        background: linear-gradient(45deg, #FF4B4B 25%, #F4C542 25%, #F4C542 50%, #4CAF50 50%, #4CAF50 75%, #2196F3 75%);
    }
    /* 알림 텍스트 스타일 */
    .game-log {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #FF4B4B;
        margin-bottom: 20px;
        font-size: 18px;
        font-weight: bold;
        text-align: center;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

class Card:
    def __init__(self, color, value):
        self.color = color
        self.value = value

# ---------------- 2. 게임 초기화 ----------------
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

    st.session_state.deck = deck
    st.session_state.players = players
    st.session_state.discard = [first]
    st.session_state.current_color = first.color
    st.session_state.turn = 0
    st.session_state.direction = 1
    st.session_state.stack = 0
    st.session_state.game_msg = "🎮 게임이 시작되었습니다!" # 메시지 초기화
    st.session_state.initialized = True

if 'initialized' not in st.session_state:
    init_game()

# ---------------- 3. 유틸리티 ----------------
def get_color_code(color):
    codes = {"Red": "#FF4B4B", "Yellow": "#F4C542", "Green": "#4CAF50", "Blue": "#2196F3", "Wild": "#333333"}
    return codes.get(color, "#333333")

def render_card_html(card):
    bg = get_color_code(card.color)
    class_name = "card-ui wild-bg" if card.color == "Wild" else "card-ui"
    style = f"background: {bg};" if card.color != "Wild" else ""
    val_map = {"Wild": "🌈", "Wild Draw Four": "+4", "Draw Two": "+2", "Reverse": "🔄", "Skip": "🚫"}
    display_val = val_map.get(card.value, card.value)
    return f"""<div class="{class_name}" style="{style}"><div class="card-type">{card.color.upper()}</div><div class="card-value">{display_val}</div></div>"""

def next_p():
    st.session_state.turn = (st.session_state.turn + st.session_state.direction) % 4

def play_action(p_idx, c_idx, chosen_color=None):
    p = st.session_state.players[p_idx]
    card = p["hand"].pop(c_idx)
    
    # 알림 메시지 생성
    msg = f"📢 {p['name']}님이 {card.color} {card.value} 카드를 냈습니다!"
    if chosen_color:
        msg = f"🌈 {p['name']}님이 와일드 카드를 내고 색상을 {chosen_color}로 바꿨습니다!"
    
    st.session_state.discard.append(card)
    st.session_state.current_color = chosen_color if card.color == "Wild" else card.color

    if card.value == "Draw Two": st.session_state.stack += 2
    elif card.value == "Wild Draw Four": st.session_state.stack += 4
    
    if card.value == "Skip":
        msg += " 🚫 다음 플레이어는 건너뜁니다!"
        st.session_state.game_msg = msg
        next_p()
    elif card.value == "Reverse":
        st.session_state.direction *= -1
        msg += " 🔄 게임 방향이 반대로 바뀝니다!"
    
    st.session_state.game_msg = msg
    next_p()

def handle_penalty(p_idx):
    p = st.session_state.players[p_idx]
    count = st.session_state.stack
    for _ in range(count):
        if st.session_state.deck: p["hand"].append(st.session_state.deck.pop())
    st.session_state.game_msg = f"⚠️ {p['name']}님이 공격을 방어하지 못해 {count}장의 카드를 뽑았습니다!"
    st.session_state.stack = 0
    next_p()

# ---------------- 4. UI 렌더링 ----------------
st.markdown("<h1 style='text-align: center;'>UNO STACK GAME</h1>", unsafe_allow_html=True)

# 상단 알림 메시지 영역
st.markdown(f"""<div class="game-log">{st.session_state.game_msg}</div>""", unsafe_allow_html=True)

# (1) 봇 정보
bot_cols = st.columns(3)
for i in range(1, 4):
    p = st.session_state.players[i]
    with bot_cols[i-1]:
        border = "3px solid red" if st.session_state.turn == i else "1px solid #ddd"
        st.markdown(f"""<div class="bot-box" style="border: {border}"><b>{p['name']}</b><br>{len(p['hand'])} cards</div>""", unsafe_allow_html=True)

st.divider()

# (2) 중앙 바닥 카드
_, center_col, _ = st.columns([1, 0.4, 1])
with center_col:
    top_card = st.session_state.discard[-1]
    st.markdown(f"<center><b>현재 색상: {st.session_state.current_color}</b></center>", unsafe_allow_html=True)
    st.markdown(render_card_html(top_card), unsafe_allow_html=True)
    curr_stack = st.session_state.get('stack', 0)
    if curr_stack > 0: st.error(f"누적 공격: +{curr_stack}")

st.divider()

# (3) 플레이어 조작
curr_p = st.session_state.players[st.session_state.turn]

if st.session_state.get('waiting_color', False):
    st.info("변경할 색상을 선택하세요!")
    c_cols = st.columns(4)
    for i, c in enumerate(["Red", "Yellow", "Green", "Blue"]):
        if c_cols[i].button(c):
            play_action(0, st.session_state.wild_idx, c)
            st.session_state.waiting_color = False
            st.rerun()

elif not curr_p["bot"]:
    st.write("### 🎴 당신의 차례")
    playable = []
    top = st.session_state.discard[-1]
    curr_stack = st.session_state.get('stack', 0)
    for i, c in enumerate(curr_p["hand"]):
        if curr_stack > 0:
            if top.value in ["Draw Two", "Wild Draw Four"] and c.value == top.value: playable.append(i)
        elif c.color == "Wild" or c.color == st.session_state.current_color or c.value == top.value: playable.append(i)

    cols = st.columns(len(curr_p["hand"]) + 1)
    for i, c in enumerate(curr_p["hand"]):
        with cols[i]:
            st.markdown(render_card_html(c), unsafe_allow_html=True)
            if st.button("내기", key=f"p_{i}", disabled=(i not in playable)):
                if c.color == "Wild":
                    st.session_state.waiting_color = True
                    st.session_state.wild_idx = i
                else: play_action(0, i)
                st.rerun()
    
    with cols[-1]:
        if st.button("카드 뽑기", type="primary"):
            if curr_stack > 0: handle_penalty(0)
            else:
                st.session_state.players[0]["hand"].append(st.session_state.deck.pop())
                st.session_state.game_msg = "🃏 당신이 카드 1장을 뽑았습니다."
                next_p()
            st.rerun()
else:
    # 봇 턴
    st.info(f"🤖 {curr_p['name']}가 생각 중...")
    time.sleep(1.5)
    top = st.session_state.discard[-1]
    curr_stack = st.session_state.get('stack', 0)
    playable = [i for i, c in enumerate(curr_p["hand"]) if (curr_stack > 0 and c.value == top.value) or (curr_stack == 0 and (c.color == "Wild" or c.color == st.session_state.current_color or c.value == top.value))]
    
    if playable:
        idx = playable[0]
        c = curr_p["hand"][idx]
        if c.color == "Wild":
            best_color = max(set([h.color for h in curr_p["hand"] if h.color != "Wild"]), default=random.choice(["Red", "Yellow", "Green", "Blue"]))
            play_action(st.session_state.turn, idx, best_color)
        else: play_action(st.session_state.turn, idx)
    else:
        if curr_stack > 0: handle_penalty(st.session_state.turn)
        else:
            curr_p["hand"].append(st.session_state.deck.pop())
            st.session_state.game_msg = f"🃏 {curr_p['name']}가 낼 카드가 없어 1장을 뽑았습니다."
            next_p()
    st.rerun()

if st.sidebar.button("게임 리셋"):
    st.session_state.clear()
    st.rerun()
