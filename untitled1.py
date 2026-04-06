import streamlit as st
import random
import time

st.set_page_config(layout="wide", page_title="Professional UNO")

# ---------------- 1. 스타일 (디자인 & 배경색) ----------------
st.markdown("""
<style>
    /* 전체 배경: 아주 미세한 회색 */
    .stApp {
        background-color: #F9F9F9;
    }

    /* 카드 디자인 */
    .card-container {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 15px;
        padding: 20px;
    }
    
    .card-ui {
        width: 100px;
        height: 150px;
        border-radius: 12px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        color: white;
        font-weight: bold;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
        border: 3px solid white;
        text-align: center;
        position: relative;
    }

    .card-value { font-size: 24px; }
    .card-type { font-size: 12px; opacity: 0.8; }

    /* 우노 버튼 전용 스타일 (빨간색) */
    div.stButton > button[kind="primary"] {
        background-color: #FF0000 !important;
        color: white !important;
        width: 100%;
        border-radius: 20px;
        font-weight: bold;
        height: 50px;
        border: none;
    }

    /* 봇 영역 스타일 */
    .bot-area {
        background: white;
        padding: 15px;
        border-radius: 15px;
        border: 1px solid #eee;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# ---------------- 2. 로직 클래스 ----------------
class Card:
    def __init__(self, color, value):
        self.color = color # Red, Yellow, Green, Blue, Wild
        self.value = value # 0-9, Skip, Reverse, Draw Two, Wild, Wild Draw Four

class Deck:
    def __init__(self):
        colors = ['Red', 'Yellow', 'Green', 'Blue']
        values = [str(i) for i in range(10)] + ['Skip', 'Reverse', 'Draw Two']
        self.cards = [Card(c, v) for c in colors for v in values] * 2
        for _ in range(4):
            self.cards.append(Card('Wild', 'Wild'))
            self.cards.append(Card('Wild', 'Wild Draw Four'))
        random.shuffle(self.cards)

    def draw(self):
        if not self.cards: self.__init__()
        return self.cards.pop()

# ---------------- 3. 유틸리티 함수 ----------------
def get_color_code(color):
    codes = {"Red": "#FF4B4B", "Yellow": "#F4C542", "Green": "#4CAF50", "Blue": "#2196F3", "Wild": "#333333"}
    return codes.get(color, "#333333")

def render_card(card):
    # 와일드 카드면 4색 아이콘 표시 느낌
    bg = get_color_code(card.color)
    val = card.value
    if val == "Wild": val = "🌈"
    elif val == "Wild Draw Four": val = "+4"
    elif val == "Draw Two": val = "+2"
    elif val == "Reverse": val = "🔄"
    elif val == "Skip": val = "🚫"
    
    return f"""
    <div class="card-ui" style="background: {bg};">
        <div class="card-type">{card.color if card.color != 'Wild' else 'WILD'}</div>
        <div class="card-value">{val}</div>
    </div>
    """

# ---------------- 4. 세션 관리 ----------------
if 'init' not in st.session_state:
    st.session_state.deck = Deck()
    st.session_state.players = [
        {"name": "YOU", "hand": [], "bot": False, "uno": False},
        {"name": "BOT 1", "hand": [], "bot": True, "uno": False},
        {"name": "BOT 2", "hand": [], "bot": True, "uno": False},
        {"name": "BOT 3", "hand": [], "bot": True, "uno": False}
    ]
    for p in st.session_state.players:
        p["hand"] = [st.session_state.deck.draw() for _ in range(7)]
    
    # 첫 카드는 무조건 색상 있는 숫자로
    while True:
        first = st.session_state.deck.draw()
        if first.color != "Wild" and first.value.isdigit(): break
    st.session_state.discard = [first]
    st.session_state.current_color = first.color
    st.session_state.turn = 0
    st.session_state.direction = 1
    st.session_state.waiting_for_color = False
    st.session_state.init = True

# ---------------- 5. 게임 액션 ----------------
def next_player():
    st.session_state.turn = (st.session_state.turn + st.session_state.direction) % 4

def play_card(p_idx, c_idx, chosen_color=None):
    p = st.session_state.players[p_idx]
    card = p["hand"].pop(c_idx)
    st.session_state.discard.append(card)
    
    # 색상 결정
    if card.color == "Wild":
        st.session_state.current_color = chosen_color
    else:
        st.session_state.current_color = card.color

    # 특수 능력
    if card.value == "Skip": next_player()
    elif card.value == "Reverse": st.session_state.direction *= -1
    elif card.value == "Draw Two":
        target = (st.session_state.turn + st.session_state.direction) % 4
        for _ in range(2): st.session_state.players[target]["hand"].append(st.session_state.deck.draw())
        next_player()
    elif card.value == "Wild Draw Four":
        target = (st.session_state.turn + st.session_state.direction) % 4
        for _ in range(4): st.session_state.players[target]["hand"].append(st.session_state.deck.draw())
        next_player()

    next_player()

# ---------------- 6. UI 배치 ----------------
st.write(f"### 🎨 현재 유효 색상: :{st.session_state.current_color}[{st.session_state.current_color}]")

# 상단: 봇들 정보
bot_cols = st.columns(3)
for i in range(1, 4):
    with bot_cols[i-1]:
        p = st.session_state.players[i]
        is_turn = "🔔" if st.session_state.turn == i else ""
        st.markdown(f"""<div class="bot-area"><h4>{is_turn} {p['name']}</h4>카드를 숨기고 있음...<br><b>{len(p['hand'])}장 보유</b></div>""", unsafe_allow_html=True)

st.divider()

# 중앙: 바닥 카드
mid_col1, mid_col2, mid_col3 = st.columns([1, 1, 1])
with mid_col2:
    st.markdown("<center><b>바닥 카드</b></center>", unsafe_allow_html=True)
    st.markdown(render_card(st.session_state.discard[-1]), unsafe_allow_html=True)

st.divider()

# 하단: 플레이어 턴
curr_p = st.session_state.players[st.session_state.turn]

if st.session_state.waiting_for_color:
    st.warning("내야 할 와일드카드의 색상을 선택하세요!")
    cols = st.columns(4)
    colors_list = ["Red", "Yellow", "Green", "Blue"]
    for i, c in enumerate(colors_list):
        if cols[i].button(c):
            play_card(0, st.session_state.last_wild_idx, c)
            st.session_state.waiting_for_color = False
            st.rerun()

elif not curr_p["bot"]:
    st.write("### 🎴 당신의 차례")
    
    # 우노 버튼 (빨간색)
    if st.button("📢 UNO!", type="primary"):
        st.toast("우노를 외쳤습니다!")
        curr_p["uno"] = True

    # 내 카드들 시각화 및 클릭
    playable_indices = []
    card_cols = st.columns(len(curr_p["hand"]) + 1)
    
    for i, card in enumerate(curr_p["hand"]):
        is_playable = (card.color == st.session_state.current_color or 
                       card.value == st.session_state.discard[-1].value or 
                       card.color == "Wild")
        
        with card_cols[i]:
            st.markdown(render_card(card), unsafe_allow_html=True)
            if st.button("내기", key=f"play_{i}", disabled=not is_playable):
                if card.color == "Wild":
                    st.session_state.waiting_for_color = True
                    st.session_state.last_wild_idx = i
                else:
                    play_card(0, i)
                st.rerun()
    
    with card_cols[-1]:
        if st.button("➕\n뽑기"):
            curr_p["hand"].append(st.session_state.deck.draw())
            next_player()
            st.rerun()

else:
    # 봇의 턴
    st.info(f"🤖 {curr_p['name']}가 생각 중입니다...")
    time.sleep(1.5) # 봇 속도 조절
    
    playable = [i for i, c in enumerate(curr_p['hand']) if (c.color == st.session_state.current_color or c.value == st.session_state.discard[-1].value or c.color == "Wild")]
    
    if playable:
        idx = playable[0]
        chosen_card = curr_p['hand'][idx]
        if chosen_card.color == "Wild":
            # 봇 지능: 자신이 가장 많이 가진 색 선택
            colors_in_hand = [c.color for c in curr_p['hand'] if c.color != "Wild"]
            best_color = max(set(colors_in_hand), key=colors_in_hand.count) if colors_in_hand else random.choice(["Red", "Yellow", "Green", "Blue"])
            play_card(st.session_state.turn, idx, best_color)
        else:
            play_card(st.session_state.turn, idx)
    else:
        curr_p["hand"].append(st.session_state.deck.draw())
        next_player()
    st.rerun()

if st.sidebar.button("게임 초기화"):
    st.session_state.clear()
    st.rerun()
