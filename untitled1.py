import streamlit as st
import random
import time

st.set_page_config(layout="centered")

# ---------------- 스타일 ----------------

st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@400;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Pretendard', sans-serif;
}

.card {
    width:120px;
    height:170px;
    border-radius:15px;
    color:white;
    display:flex;
    flex-direction:column;
    justify-content:center;
    align-items:center;
    font-size:28px;
    font-weight:bold;
    box-shadow:0 8px 20px rgba(0,0,0,0.25);
    transition:0.2s;
    margin:10px;
}

.card:hover {
    transform:scale(1.05);
}

.uno {
    background:#ff0000;
    color:white;
    font-size:20px;
    border-radius:15px;
    padding:15px;
    text-align:center;
    box-shadow:0 5px 15px rgba(0,0,0,0.3);
}

</style>
""", unsafe_allow_html=True)

# ---------------- 카드 ----------------

class Card:
    def __init__(self, color, value):
        self.color = color
        self.value = value

class Deck:
    def __init__(self):
        colors = ['Red','Yellow','Green','Blue']
        values = [str(i) for i in range(10)] + ['Skip','Reverse','Draw Two']

        self.cards = [Card(c,v) for c in colors for v in values]*2

        for _ in range(4):
            self.cards.append(Card('Wild','Wild'))
            self.cards.append(Card('Wild','Wild Draw Four'))

        random.shuffle(self.cards)

    def draw(self):
        if not self.cards:
            self.__init__()
        return self.cards.pop()

# ---------------- 세션 ----------------

if 'start' not in st.session_state:
    st.session_state.start = False

def init_game():

    st.session_state.deck = Deck()

    st.session_state.players = [
        {"name":"You","hand":[], "bot":False, "uno":False},
        {"name":"Bot1","hand":[], "bot":True, "uno":False},
        {"name":"Bot2","hand":[], "bot":True, "uno":False},
        {"name":"Bot3","hand":[], "bot":True, "uno":False},
    ]

    for p in st.session_state.players:
        p["hand"] = [st.session_state.deck.draw() for _ in range(7)]

    # 시작 Wild 금지
    while True:
        first = st.session_state.deck.draw()
        if first.color != "Wild":
            break

    st.session_state.discard = [first]
    st.session_state.color = first.color
    st.session_state.turn = 0
    st.session_state.dir = 1
    st.session_state.over = False

    st.session_state.start = True


# ---------------- 로직 ----------------

def next_turn():
    st.session_state.turn = (st.session_state.turn + st.session_state.dir) % 4


def call_uno(idx):
    p = st.session_state.players[idx]

    if len(p["hand"]) == 2:
        p["uno"] = True
        st.toast("UNO!")
    else:
        st.warning("잘못 외쳐서 카드 1장 추가")
        p["hand"].append(st.session_state.deck.draw())


def play_card(p_idx, c_idx):

    p = st.session_state.players[p_idx]
    card = p["hand"][c_idx]

    top = st.session_state.discard[-1]

    if not (card.color == st.session_state.color
            or card.value == top.value
            or card.color == "Wild"):
        return

    p["hand"].pop(c_idx)
    st.session_state.discard.append(card)
    st.session_state.color = card.color

    if card.value == "Skip":
        next_turn()

    elif card.value == "Reverse":
        st.session_state.dir *= -1

    elif card.value == "Draw Two":
        target = (p_idx + st.session_state.dir) % 4
        st.session_state.players[target]["hand"].append(st.session_state.deck.draw())
        st.session_state.players[target]["hand"].append(st.session_state.deck.draw())
        next_turn()

    if len(p["hand"]) == 0:
        st.session_state.over = True
        st.success("승리!")
        return

    next_turn()


# ---------------- 색 ----------------

colors = {
    "Red":"#ff4b4b",
    "Yellow":"#f4c542",
    "Green":"#4caf50",
    "Blue":"#2196f3",
    "Wild":"#333"
}

# ---------------- UI ----------------

st.title("UNO")

if not st.session_state.start:

    if st.button("게임 시작"):
        init_game()
        st.rerun()

else:

    top = st.session_state.discard[-1]
    curr = st.session_state.players[st.session_state.turn]

    # 바닥 카드

    st.markdown("### 바닥 카드")

    st.markdown(f"""
    <div class="card" style="background:{colors[top.color]}; margin:auto;">
        {top.color}
        <div style="font-size:40px">{top.value}</div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # 봇 상태

    for p in st.session_state.players[1:]:
        st.info(f"{p['name']} : {len(p['hand'])}장")

    st.divider()

    # ---------------- 봇 턴 ----------------

    if curr["bot"] and not st.session_state.over:

        st.subheader(f"{curr['name']} 턴")

        with st.spinner("생각 중..."):
            time.sleep(1)

            playable = [
                i for i,c in enumerate(curr["hand"])
                if c.color == st.session_state.color
                or c.value == top.value
                or c.color == "Wild"
            ]

            if playable:
                play_card(st.session_state.turn, playable[0])
            else:
                curr["hand"].append(st.session_state.deck.draw())
                next_turn()

            st.rerun()

    # ---------------- 내 턴 ----------------

    elif not st.session_state.over:

        st.subheader("내 카드")

        for i,c in enumerate(curr["hand"]):

            if st.button(f"{c.color} {c.value}", key=i):

                play_card(0, i)
                st.rerun()

        st.markdown("")

        if st.button("UNO"):
            call_uno(0)
            st.rerun()

        if st.button("카드 뽑기"):
            curr["hand"].append(st.session_state.deck.draw())
            next_turn()
            st.rerun()

    if st.button("리셋"):
        init_game()
        st.rerun()
