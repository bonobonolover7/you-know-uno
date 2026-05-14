import streamlit as st
import random
import time

# ---------------- 1. 설정 ----------------
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
    .game-log {
        background-color: white; padding: 15px; border-radius: 15px;
        border-left: 8px solid #FF4B4B; margin-bottom: 20px;
        text-align: center;
    }
    .turn-msg { color: #FF4B4B; font-size: 22px; font-weight: bold; }
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
    val_map = {"Wild": "🌈", "Wild Draw Four": "+4", "Draw Two": "+2", "Reverse": "🔄", "Skip": "🚫"}
    display_val = val_map.get(card.value, card.value)
    return f"""<div class="card-ui {'wild-bg' if card.color=='Wild' else ''}" style="background: {bg};">
                <div style="font-size:10px;">{card.color.upper()}</div>
                <div style="font-size:24px;">{display_val}</div>
              </div>"""

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
        {"name": "나", "hand": [deck.pop() for _ in range(7)], "bot": False},
        {"name": "봇 1", "hand": [deck.pop() for _ in range(7)], "bot": True},
        {"name": "봇 2", "hand": [deck.pop() for _ in range(7)], "bot": True},
        {"name": "봇 3", "hand": [deck.pop() for _ in range(7)], "bot": True}
    ]

    first = deck.pop()
    while first.color == "Wild": first = deck.pop()

    st.session_state.update({
        "deck": deck, "players": players, "discard": [first],
        "current_color": first.color, "turn": 0, "direction": 1,
        "stack": 0, "game_msg": "🎮 게임 시작!", "initialized": True,
        "waiting_color": False, "wild_idx": -1
    })

# ---------------- 4. 핵심 로직 ----------------
def play_action(p_idx, c_idx, chosen_color=None):
    p = st.session_state.players[p_idx]
    card = p["hand"].pop(c_idx) # 여기서 카드가 손에서 빠집니다 (내는 동작)
    
    st.session_state.discard.append(card)
    st.session_state.current_color = chosen_color if card.color == "Wild" else card.color
    
    # 특수 카드 효과
    if card.value == "Draw Two": st.session_state.stack += 2
    elif card.value == "Wild Draw Four": st.session_state.stack += 4
    elif card.value == "Reverse": st.session_state.direction *= -1
    
    # Skip 카드의 경우 턴을 두 번 넘겨야 다음 사람 차례가 됩니다.
    step = 2 if card.value == "Skip" else 1
    st.session_state.turn = (st.session_state.turn + (st.session_state.direction * step)) % 4
    
    st.session_state.game_msg = f"📢 {p['name']}님이 {card.value}를 냈습니다."

# ---------------- 5. 화면 표시 ----------------
st.title("🃏 우노 스피드 배틀")

curr_idx = st.session_state.turn
curr_p = st.session_state.players[curr_idx]

# 상단 상황판
st.markdown(f"""
<div class='game-log'>
    <div>{st.session_state.game_msg}</div>
    <div class='turn-msg'>{"🔥 당신의 차례!" if curr_idx==0 else f"🤖 {curr_p['name']} 생각 중..."}</div>
</div>
""", unsafe_allow_html=True)

# 봇 상태 (한 줄로)
b_cols = st.columns(3)
for i in range(1, 4):
    p = st.session_state.players[i]
    with b_cols[i-1]:
        st.markdown(f"<div style='text-align:center; padding:5px; border-radius:10px; background:white; border:{'3px solid red' if curr_idx==i else '1px solid #ccc'}'><b>{p['name']}</b>: {len(p['hand'])}장</div>", unsafe_allow_html=True)

st.divider()

# 중앙 카드
_, mid, _ = st.columns([1, 0.6, 1])
with mid:
    top = st.session_state.discard[-1]
    st.markdown(f"<center>색상: <b style='color:{get_color_code(st.session_state.current_color)}'>{st.session_state.current_color}</b></center>", unsafe_allow_html=True)
    st.markdown(render_card_html(top), unsafe_allow_html=True)
    if st.session_state.stack > 0: st.error(f"공격 누적: +{st.session_state.stack}장")

st.divider()

# ---------------- 6. 플레이어 컨트롤 ----------------
me = st.session_state.players[0]
st.write(f"### 🎴 나의 카드 (남은 수: {len(me['hand'])}장)")

# 낼 수 있는 카드 체크
def can_play(c):
    top = st.session_state.discard[-1]
    if st.session_state.stack > 0:
        return c.value == top.value or c.value == "Wild Draw Four"
    return c.color == "Wild" or c.color == st.session_state.current_color or c.value == top.value

# 내 카드 렌더링
hand_cols = st.columns(max(len(me["hand"]), 1))
for i, c in enumerate(me["hand"]):
    with hand_cols[i]:
        st.markdown(render_card_html(c), unsafe_allow_html=True)
        if curr_idx == 0 and not st.session_state.waiting_color:
            if st.button("내기", key=f"btn_{i}", disabled=not can_play(c), use_container_width=True):
                if c.color == "Wild":
                    st.session_state.waiting_color, st.session_state.wild_idx = True, i
                else:
                    play_action(0, i)
                st.rerun()

# 색상 선택 / 드로우 버튼
if st.session_state.waiting_color:
    st.info("🌈 변경할 색상 선택!")
    cols = st.columns(4)
    for i, color in enumerate(["Red", "Yellow", "Green", "Blue"]):
        if cols[i].button(color, use_container_width=True):
            play_action(0, st.session_state.wild_idx, color)
            st.session_state.waiting_color = False
            st.rerun()
elif curr_idx == 0:
    if st.button("🃏 낼 카드 없음 (카드 가져오기)", use_container_width=True):
        num = max(st.session_state.stack, 1)
        for _ in range(num):
            if st.session_state.deck: me["hand"].append(st.session_state.deck.pop())
        st.session_state.stack = 0
        st.session_state.turn = (st.session_state.turn + st.session_state.direction) % 4
        st.session_state.game_msg = f"🃏 카드를 {num}장 가져왔습니다."
        st.rerun()

# ---------------- 7. 봇 AI (느긋하게 2.5초) ----------------
if curr_idx != 0:
    time.sleep(2.5)
    playable = [i for i, c in enumerate(curr_p["hand"]) if can_play(c)]
    
    if playable:
        idx = playable[0]
        c = curr_p["hand"][idx]
        play_action(curr_idx, idx, random.choice(["Red", "Yellow", "Green", "Blue"]) if c.color == "Wild" else None)
    else:
        num = max(st.session_state.stack, 1)
        for _ in range(num):
            if st.session_state.deck: curr_p["hand"].append(st.session_state.deck.pop())
        st.session_state.stack = 0
        st.session_state.turn = (st.session_state.turn + st.session_state.direction) % 4
        st.session_state.game_msg = f"🃏 {curr_p['name']}님이 카드를 가져갔습니다."
    st.rerun()
