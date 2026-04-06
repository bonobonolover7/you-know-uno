import streamlit as st
import random
import time

st.set_page_config(layout="wide")

# ---------------- 카드 / 덱 ----------------

class Card:
    def __init__(self, color, value):
        self.color = color
        self.value = value

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
        if not self.cards:
            self.__init__()
        return self.cards.pop()


# ---------------- 세션 초기화 ----------------

if 'game_started' not in st.session_state:
    st.session_state.game_started = False

def init_game():

    st.session_state.deck = Deck()

    st.session_state.players = [
        {"name": "Player", "hand": [], "is_bot": False, "uno_called": False},
        {"name": "Bot 1", "hand": [], "is_bot": True, "uno_called": False},
        {"name": "Bot 2", "hand": [], "is_bot": True, "uno_called": False},
        {"name": "Bot 3", "hand": [], "is_bot": True, "uno_called": False},
    ]

    for p in st.session_state.players:
        p["hand"] = [st.session_state.deck.draw() for _ in range(7)]

    # 시작 바닥카드 Wild 금지
    while True:
        first_card = st.session_state.deck.draw()
        if first_card.color != "Wild":
            break

    st.session_state.discard_pile = [first_card]
    st.session_state.current_color = first_card.color

    st.session_state.turn = 0
    st.session_state.direction = 1
    st.session_state.game_over = False
    st.session_state.msg = "게임 시작!"

    st.session_state.game_started = True


# ---------------- 로직 ----------------

def next_turn():
    st.session_state.turn = (st.session_state.turn + st.session_state.direction) % 4


def call_uno(idx):
    player = st.session_state.players[idx]

    if len(player["hand"]) <= 2:
        player["uno_called"] = True
        st.toast(f"{player['name']} : UNO!")
    else:
        st.warning("아직 우노 외칠 수 없음")


def check_uno_penalty(idx):
    player = st.session_state.players[idx]

    if len(player["hand"]) == 1 and not player["uno_called"]:
        st.warning(f"{player['name']} 우노 안 외쳐서 2장 추가")

        player["hand"].append(st.session_state.deck.draw())
        player["hand"].append(st.session_state.deck.draw())

    player["uno_called"] = False


def play_card(player_idx, card_idx):

    player = st.session_state.players[player_idx]
    card = player["hand"].pop(card_idx)

    st.session_state.discard_pile.append(card)
    st.session_state.current_color = card.color

    if card.value == "Skip":
        next_turn()

    elif card.value == "Reverse":
        st.session_state.direction *= -1

    elif card.value == "Draw Two":
        target = (player_idx + st.session_state.direction) % 4
        st.session_state.players[target]["hand"].append(st.session_state.deck.draw())
        st.session_state.players[target]["hand"].append(st.session_state.deck.draw())
        next_turn()

    if len(player["hand"]) == 0:
        st.session_state.game_over = True
        st.success(f"{player['name']} 승리!")
        return

    check_uno_penalty(player_idx)
    next_turn()


# ---------------- 색상 ----------------

color_map = {
    "Red": "#ff4b4b",
    "Yellow": "#f4c542",
    "Green": "#4caf50",
    "Blue": "#2196f3",
    "Wild": "#333"
}


# ---------------- UI ----------------

st.title("UNO Game")

if not st.session_state.game_started:
    if st.button("게임 시작"):
        init_game()
        st.rerun()

else:

    top_card = st.session_state.discard_pile[-1]
    curr_p = st.session_state.players[st.session_state.turn]

    st.markdown("### 바닥 카드")

    st.markdown(f"""
    <div style="
    width:120px;
    height:160px;
    background:{color_map[top_card.color]};
    border-radius:15px;
    display:flex;
    align-items:center;
    justify-content:center;
    font-size:40px;
    color:white;
    margin:auto;
    box-shadow:0 0 20px rgba(0,0,0,0.3);
    ">
    {top_card.value}
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # ---------------- 봇 턴 ----------------

    if curr_p["is_bot"] and not st.session_state.game_over:

        st.subheader(f"{curr_p['name']} 턴")

        cols = st.columns(3)

        for i, bot in enumerate(st.session_state.players):
            with cols[i % 3]:
                st.info(f"{bot['name']}\n카드 {len(bot['hand'])}")

        with st.spinner("생각 중..."):
            time.sleep(1)

            playable = [
                i for i, c in enumerate(curr_p["hand"])
                if c.color == st.session_state.current_color
                or c.value == top_card.value
                or c.color == "Wild"
            ]

            if len(curr_p["hand"]) == 2 and random.random() < 0.8:
                call_uno(st.session_state.turn)

            if playable:
                play_card(st.session_state.turn, playable[0])
            else:
                curr_p["hand"].append(st.session_state.deck.draw())
                next_turn()

            st.rerun()

    # ---------------- 내 턴 ----------------

    elif not st.session_state.game_over:

        st.subheader("당신의 턴")

        hand = curr_p["hand"]
        cols = st.columns(len(hand) + 1)

        for i, c in enumerate(hand):

            is_playable = (
                c.color == st.session_state.current_color
                or c.value == top_card.value
                or c.color == "Wild"
            )

            with cols[i]:

                if st.button(
                    c.value,
                    key=f"card_{i}",
                    disabled=not is_playable,
                    use_container_width=True
                ):
                    play_card(st.session_state.turn, i)
                    st.rerun()

                st.markdown(f"""
                <div style="
                background:{color_map[c.color]};
                height:80px;
                border-radius:10px;
                margin-top:-65px;
                opacity:{1 if is_playable else 0.3};
                ">
                </div>
                """, unsafe_allow_html=True)

        # UNO 버튼 (오른쪽 끝)

        with cols[-1]:
            if st.button("UNO!", use_container_width=True):
                call_uno(0)

        if st.button("카드 뽑기"):
            curr_p["hand"].append(st.session_state.deck.draw())
            next_turn()
            st.rerun()

    if st.button("게임 리셋"):
        init_game()
        st.rerun()
