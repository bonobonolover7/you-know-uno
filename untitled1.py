import streamlit as st
import random
import time

# ---------------- 1. 설정 & 스타일 ----------------
st.set_page_config(layout="wide", page_title="우노 스피드 배틀")

st.markdown("""
<style>
    .stApp { background-color: #F0F2F6; }
    .card-ui {
        width: 100px; height: 150px; border-radius: 12px;
        display: flex; flex-direction: column; justify-content: center; align-items: center;
        color: white; font-weight: bold; box-shadow: 0 4px 10px rgba(0,0,0,0.2);
        border: 2px solid white; text-align: center; margin: auto;
    }
    .card-value { font-size: 22px; }
    .card-type { font-size: 10px; opacity: 0.8; margin-bottom: 5px; }
    .wild-bg {
        background: linear-gradient(45deg, #f44336 25%, #ffeb3b 25%, #ffeb3b 50%, #4caf50 50%, #4caf50 75%, #2196f3 75%) !important;
    }
    .game-log {
        background-color: white; padding: 20px; border-radius: 15px;
        border-left: 8px solid #FF4B4B; margin-bottom: 20px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1); text-align: center;
    }
    .turn-msg { color: #FF4B4B; font-size: 24px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

class Card:
    def __init__(self, color, value):
        self.color = color
        self.value = value

# ---------------- 2. 유틸리티 ----------------
def get_color_code(color):
    return {"Red": "#f44336", "Yellow": "#fbc02d", "Green": "#4caf50", "Blue": "#2196f3", "Wild": "#333333"}.get(color, "#333333")

def render_card_html(card):
    bg = get_color_code(card.color)
    is_wild = (card.color == "Wild")
    class_name = "card-ui wild-bg" if is_wild else "card-ui"
    style = f"background: {bg};" if not is_wild else ""
    val_map = {"Wild": "🌈", "Wild Draw Four": "+4", "Draw Two": "+2", "Reverse": "🔄", "Skip": "🚫"}
    display_val = val_map.get(card.value, card.value)
    return f"""<div class="{class_name}" style="{style}"><div class="card-type">{card.color.upper()}</div><div class="card-value">{display_val}</div></div>"""

def next_turn():
    st.session_state.turn = (st.session_state.turn + st.session_state.direction) % 4
    # 우노 체크 초기화
    for p in st.session_state.players:
        if len(p["hand"]) != 1: p["uno_called"] = False

# ---------------- 3. 게임 초기화 ----------------
if 'initialized' not in st.session_state:
    colors = ['Red', 'Yellow', 'Green', 'Blue']
    values = [str(i) for i in range(10)] + ['Skip', 'Reverse', 'Draw Two']
    deck = [Card(c, v) for c in colors for v in values] * 2
    for _ in range(4):
        deck.append(Card('Wild', 'Wild'))
        deck.append(Card('Wild', 'Wild Draw Four'))
    random.shuffle(deck)

    players = [
        {"name": "나", "hand": [], "bot": False, "uno_called": False},
        {"name": "봇 1", "hand": [], "bot": True, "uno_called": False},
        {"name": "봇 2", "hand": [], "bot": True, "uno_called": False},
        {"name": "봇 3", "hand": [], "bot": True, "uno_called": False}
    ]
    for p in players:
        p["hand"] = [deck.pop() for _ in range(7)]

    first = deck.pop()
    while first.color == "Wild":
        deck.insert(0, first)
        random.shuffle(deck)
        first = deck.pop()

    st.session_state.update({
        "deck": deck, "players": players, "discard": [first],
        "current_color": first.color, "turn": 0, "direction": 1,
        "stack": 0, "game_msg": "🎮 게임 시작! 당신의 차례입니다.", "initialized": True,
        "waiting_color": False, "wild_idx": -1, "uno_timer": None, "uno_target": None
    })

# ---------------- 4. 액션 함수 ----------------
def play_card(p_idx, c_idx, chosen_color=None):
    p = st.session_state.players[p_idx]
    card = p["hand"].pop(c_idx)
    st.session_state.discard.append(card)
    st.session_state.current_color = chosen_color if card.color == "Wild" else card.color

    # 우노 타이머 설정
    if len(p["hand"]) == 1:
        st.session_state.uno_target = p_idx
        st.session_state.uno_timer = time.time() + 1.5
    
    msg = f"📢 {p['name']}님이 {card.value} 카드를 냈습니다."
    if card.value == "Draw Two": st.session_state.stack += 2
    elif card.value == "Wild Draw Four": st.session_state.stack += 4
    elif card.value == "Skip": next_turn()
    elif card.value == "Reverse": st.session_state.direction *= -1
    
    st.session_state.game_msg = msg
    next_turn()

# ---------------- 5. 메인 레이아웃 ----------------
st.title("🃏 우노 스피드 배틀")

# 게임 상황판
curr_idx = st.session_state.turn
curr_p = st.session_state.players[curr_idx]
is_my_turn = (curr_idx == 0)

status_text = "🔥 당신의 차례!" if is_my_turn else f"🤖 {curr_p['name']}님이 생각 중..."
st.markdown(f"""
<div class='game-log'>
    <div style='font-size: 18px;'>{st.session_state.game_msg}</div>
    <div class='turn-msg'>{status_text}</div>
</div>
""", unsafe_allow_html=True)

# 봇 정보
cols = st.columns(3)
for i in range(1, 4):
    p = st.session_state.players[i]
    with cols[i-1]:
        active = "border: 4px solid #FF4B4B;" if curr_idx == i else "border: 1px solid #ccc;"
        st.markdown(f"""
        <div style='{active} padding:10px; border-radius:10px; background:white; text-align:center;'>
            <b>{p['name']}</b><br>카드: {len(p['hand'])}장
        </div>
        """, unsafe_allow_html=True)

st.divider()

# 중앙 카드 더미
_, mid, _ = st.columns([1, 0.6, 1])
with mid:
    top = st.session_state.discard[-1]
    st.markdown(f"<center>현재 색상: <b style='color:{get_color_code(st.session_state.current_color)}'>{st.session_state.current_color}</b></center>", unsafe_allow_html=True)
    st.markdown(render_card_html(top), unsafe_allow_html=True)
    if st.session_state.stack > 0:
        st.error(f"⚠️ 공격 누적: +{st.session_state.stack}장 (대응 카드가 없으면 드로우!)")

st.divider()

# ---------------- 6. 내 카드 UI (무조건 상시 표시) ----------------
me = st.session_state.players[0]
st.write("### 🎴 나의 카드")

# 낼 수 있는 카드 판단 로직
def can_play(card, top_card, stack):
    if stack > 0:
        return card.value == top_card.value or card.value == "Wild Draw Four"
    return card.color == "Wild" or card.color == st.session_state.current_color or card.value == top_card.value

playable_idxs = [i for i, c in enumerate(me["hand"]) if can_play(c, top, st.session_state.stack)]

hand_cols = st.columns(max(len(me["hand"]), 1))
for i, c in enumerate(me["hand"]):
    with hand_cols[i]:
        st.markdown(render_card_html(c), unsafe_allow_html=True)
        # 내 턴일 때만 버튼 활성화
        if is_my_turn and not st.session_state.waiting_color:
            btn_label = "내기" if i in playable_idxs else "불가"
            if st.button(btn_label, key=f"btn_{i}", disabled=(i not in playable_idxs), use_container_width=True):
                if c.color == "Wild":
                    st.session_state.waiting_color, st.session_state.wild_idx = True, i
                else:
                    play_card(0, i)
                st.rerun()

# ---------------- 7. 게임 진행 로직 ----------------

# 1. 색상 선택 팝업 (내 턴일 때만)
if st.session_state.waiting_color:
    st.info("🌈 바꿀 색상을 선택하세요!")
    c_cols = st.columns(4)
    for i, color_name in enumerate(["Red", "Yellow", "Green", "Blue"]):
        if c_cols[i].button(color_name, use_container_width=True):
            play_card(0, st.session_state.wild_idx, color_name)
            st.session_state.waiting_color = False
            st.rerun()

# 2. 내 턴인데 낼 게 없을 때 드로우 버튼
elif is_my_turn:
    st.write("")
    c1, c2, c3 = st.columns([1,1,1])
    if c2.button("🃏 카드 가져오기 / 넘기기", use_container_width=True, type="primary"):
        s = st.session_state.stack
        num = max(s, 1)
        for _ in range(num):
            if st.session_state.deck: me["hand"].append(st.session_state.deck.pop())
        st.session_state.stack = 0
        st.session_state.game_msg = f"🃏 카드를 {num}장 가져왔습니다."
        next_turn()
        st.rerun()

# 3. 봇의 턴 (여유있게 2.5초 대기)
else:
    time.sleep(2.5) # 봇이 생각하는 시간 (2.5초)
    bot_hand = curr_p["hand"]
    bot_playable = [i for i, c in enumerate(bot_hand) if can_play(c, top, st.session_state.stack)]
    
    if bot_playable:
        idx = bot_playable[0]
        c = bot_hand[idx]
        play_card(curr_idx, idx, random.choice(["Red", "Yellow", "Green", "Blue"]) if c.color == "Wild" else None)
    else:
        s = st.session_state.stack
        num = max(s, 1)
        for _ in range(num):
            if st.session_state.deck: bot_hand.append(st.session_state.deck.pop())
        st.session_state.stack = 0
        st.session_state.game_msg = f"🃏 {curr_p['name']}님이 카드가 없어 {num}장을 가져갔습니다."
        next_turn()
    st.rerun()
