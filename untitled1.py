import streamlit as st
import random
import time

# ---------------- 1. 설정 & 스타일 ----------------
st.set_page_config(layout="wide", page_title="우노 스피드 배틀")

st.markdown("""
<style>
    .stApp { background-color: #F0F2F6; }
    .card-ui {
        width: 100px; height: 140px; border-radius: 12px;
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
        background-color: white; padding: 15px; border-radius: 15px;
        border-left: 8px solid #FF4B4B; margin: 10px 0;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1); text-align: center;
    }
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
        {"name": "나", "hand": [], "bot": False},
        {"name": "봇 1", "hand": [], "bot": True},
        {"name": "봇 2", "hand": [], "bot": True},
        {"name": "봇 3", "hand": [], "bot": True}
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
        "stack": 0, "game_msg": "🎮 당신의 차례입니다!", "initialized": True,
        "waiting_color": False, "wild_idx": -1
    })

# ---------------- 4. 게임 로직 함수 ----------------
def next_turn():
    st.session_state.turn = (st.session_state.turn + st.session_state.direction) % 4

def play_action(p_idx, c_idx, chosen_color=None):
    p = st.session_state.players[p_idx]
    card = p["hand"].pop(c_idx)
    st.session_state.discard.append(card)
    st.session_state.current_color = chosen_color if card.color == "Wild" else card.color
    
    st.session_state.game_msg = f"📢 {p['name']}님이 {card.value}를 냈습니다."
    
    if card.value == "Draw Two": st.session_state.stack += 2
    elif card.value == "Wild Draw Four": st.session_state.stack += 4
    elif card.value == "Skip": next_turn()
    elif card.value == "Reverse": st.session_state.direction *= -1
    
    next_turn()

# ---------------- 5. 화면 렌더링 ----------------
st.title("🃏 우노 스피드 배틀")

# 상단 봇 정보
bot_cols = st.columns(3)
for i in range(1, 4):
    p = st.session_state.players[i]
    with bot_cols[i-1]:
        active = "border: 4px solid #FF4B4B;" if st.session_state.turn == i else "border: 1px solid #ccc;"
        st.markdown(f"<div style='{active} padding:10px; border-radius:10px; background:white; text-align:center;'><b>{p['name']}</b><br>카드: {len(p['hand'])}장</div>", unsafe_allow_html=True)

st.markdown(f"<div class='game-log'><b>{st.session_state.game_msg}</b></div>", unsafe_allow_html=True)

# 중앙 버린 카드
_, mid, _ = st.columns([1, 0.6, 1])
with mid:
    top = st.session_state.discard[-1]
    st.markdown(f"<center>현재 색상: <b style='color:{get_color_code(st.session_state.current_color)}'>{st.session_state.current_color}</b></center>", unsafe_allow_html=True)
    st.markdown(render_card_html(top), unsafe_allow_html=True)
    if st.session_state.stack > 0:
        st.error(f"공격 누적: +{st.session_state.stack}장")

st.divider()

# ---------------- 6. 플레이어 컨트롤 ----------------
me = st.session_state.players[0]
st.write(f"### 🎴 나의 카드 ({len(me['hand'])}장)")

# 내기 가능 여부 체크
def can_play(card, top_card, stack):
    if stack > 0:
        return card.value == top_card.value or (card.color == "Wild" and "Draw Four" in card.value)
    return card.color == "Wild" or card.color == st.session_state.current_color or card.value == top_card.value

# 카드 가로로 배치
hand_cols = st.columns(max(len(me["hand"]), 1))
for i, c in enumerate(me["hand"]):
    with hand_cols[i]:
        st.markdown(render_card_html(c), unsafe_allow_html=True)
        if st.session_state.turn == 0 and not st.session_state.waiting_color:
            playable = can_play(c, top, st.session_state.stack)
            if st.button("내기", key=f"play_{i}", disabled=not playable, use_container_width=True):
                if c.color == "Wild":
                    st.session_state.waiting_color, st.session_state.wild_idx = True, i
                else:
                    play_action(0, i)
                st.rerun()

# 색상 선택 대기
if st.session_state.waiting_color:
    st.info("🌈 와일드카드 색상을 선택하세요!")
    c_cols = st.columns(4)
    for i, color_name in enumerate(["Red", "Yellow", "Green", "Blue"]):
        if c_cols[i].button(color_name, key=f"sel_{color_name}", use_container_width=True):
            play_action(0, st.session_state.wild_idx, color_name)
            st.session_state.waiting_color = False
            st.rerun()

# 낼 카드 없을 때 드로우
if st.session_state.turn == 0 and not st.session_state.waiting_color:
    if st.button("🃏 낼 카드 없음 (카드 가져오기)", type="primary"):
        num = max(st.session_state.stack, 1)
        for _ in range(num):
            if st.session_state.deck: me["hand"].append(st.session_state.deck.pop())
        st.session_state.stack = 0
        st.session_state.game_msg = f"🃏 카드를 {num}장 가져왔습니다."
        next_turn()
        st.rerun()

# ---------------- 7. 봇 차례 실행 (여기서 딜레이를 줌) ----------------
if st.session_state.turn != 0:
    time.sleep(2.5) # 봇 생각 시간
    bot_idx = st.session_state.turn
    bot_p = st.session_state.players[bot_idx]
    
    playable_idxs = [i for i, c in enumerate(bot_p["hand"]) if can_play(c, top, st.session_state.stack)]
    
    if playable_idxs:
        idx = playable_idxs[0]
        c = bot_p["hand"][idx]
        play_action(bot_idx, idx, random.choice(["Red", "Yellow", "Green", "Blue"]) if c.color == "Wild" else None)
    else:
        num = max(st.session_state.stack, 1)
        for _ in range(num):
            if st.session_state.deck: bot_p["hand"].append(st.session_state.deck.pop())
        st.session_state.stack = 0
        st.session_state.game_msg = f"🃏 {bot_p['name']}님이 카드를 {num}장 가져갔습니다."
        next_turn()
    
    st.rerun()
