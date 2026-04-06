import streamlit as st
import random
import time

# --- 1. 기본 클래스 정의 ---
class Card:
    def __init__(self, color, value):
        self.color = color
        self.value = value

    def __str__(self):
        return f"{self.color} {self.value}"

    def __repr__(self):
        return f"'{self.color} {self.value}'"

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

# --- 2. 세션 상태 초기화 (Streamlit 전용) ---
if 'game_started' not in st.session_state:
    st.session_state.game_started = False

def init_game():
    st.session_state.deck = Deck()
    st.session_state.players = [
        {"name": "Player (You)", "hand": [], "is_bot": False, "uno_called": False},
        {"name": "Bot 1", "hand": [], "is_bot": True, "uno_called": False},
        {"name": "Bot 2", "hand": [], "is_bot": True, "uno_called": False},
        {"name": "Bot 3", "hand": [], "is_bot": True, "uno_called": False}
    ]
    for p in st.session_state.players:
        p['hand'] = [st.session_state.deck.draw() for _ in range(7)]
    
    st.session_state.discard_pile = [st.session_state.deck.draw()]
    st.session_state.turn = 0
    st.session_state.direction = 1
    st.session_state.current_color = st.session_state.discard_pile[-1].color
    st.session_state.msg = "게임 시작! 당신의 턴입니다."
    st.session_state.game_over = False
    st.session_state.game_started = True

# --- 3. 로직 함수 ---
def next_turn():
    st.session_state.turn = (st.session_state.turn + st.session_state.direction) % 4

def call_uno(player_idx):
    player = st.session_state.players[player_idx]
    if len(player['hand']) <= 2: # 카드를 내기 전/후 시점 고려
        player['uno_called'] = True
        st.toast(f"📢 {player['name']}: UNO!!!")
    else:
        st.error("아직 우노를 외칠 때가 아닙니다!")

def check_uno_penalty(player_idx):
    player = st.session_state.players[player_idx]
    if len(player['hand']) == 1 and not player['uno_called']:
        st.warning(f"⚠️ {player['name']}가 우노를 외치지 않아 2장 뽑습니다!")
        player['hand'].append(st.session_state.deck.draw())
        player['hand'].append(st.session_state.deck.draw())
    player['uno_called'] = False # 초기화

def play_card(player_idx, card_idx):
    player = st.session_state.players[player_idx]
    card = player['hand'].pop(card_idx)
    st.session_state.discard_pile.append(card)
    st.session_state.current_color = card.color
    
    # 특수 카드 처리
    if card.value == 'Skip': next_turn()
    elif card.value == 'Reverse': st.session_state.direction *= -1
    elif card.value == 'Draw Two':
        target = (st.session_state.turn + st.session_state.direction) % 4
        for _ in range(2): st.session_state.players[target]['hand'].append(st.session_state.deck.draw())
        next_turn()
    
    if len(player['hand']) == 0:
        st.session_state.game_over = True
        st.session_state.msg = f"🏆 {player['name']} 승리!!!"
    else:
        check_uno_penalty(player_idx)
        next_turn()

# --- 4. UI 레이아웃 ---
st.title("🔥 욕 나오는 리얼 우노 게임")

if not st.session_state.game_started:
    if st.button("게임 시작하기"):
        init_game()
        st.rerun()
else:
    # 상단 정보
    top_card = st.session_state.discard_pile[-1]
    col1, col2 = st.columns(2)
    col1.metric("현재 색상", st.session_state.current_color)
    col2.metric("바닥 카드", f"{top_card.value}")

    # 우노 버튼 (F키 대용 및 클릭용)
    if st.button("📢 UNO! (단축키 F)", use_container_width=True):
        call_uno(0)

    # 봇 상태 시각화
    cols = st.columns(3)
    for i, bot in enumerate(st.session_state.players[1:]):
        with cols[i]:
            st.info(f"🤖 {bot['name']}\n\n카드: {len(bot['hand'])}장")

    st.divider()

    # 플레이어 턴 핸들링
    curr_p = st.session_state.players[st.session_state.turn]
    
    if not st.session_state.game_over:
        if not curr_p['is_bot']:
            st.subheader("🎴 당신의 손패")
            playable = []
            for i, c in enumerate(curr_p['hand']):
                is_playable = (c.color == st.session_state.current_color or 
                               c.value == top_card.value or 
                               c.color == 'Wild')
                
                label = f"{c.color} {c.value}"
                if st.button(label, key=f"card_{i}", disabled=not is_playable):
                    play_card(st.session_state.turn, i)
                    st.rerun()
            
            if st.button("카드 뽑기 / 턴 넘기기"):
                curr_p['hand'].append(st.session_state.deck.draw())
                check_uno_penalty(st.session_state.turn)
                next_turn()
                st.rerun()
        else:
            # 봇 지연 실행 시각화
            with st.spinner(f"{curr_p['name']}가 생각 중..."):
                time.sleep(1)
                # 단순 봇 로직
                playable = [i for i, c in enumerate(curr_p['hand']) if (c.color == st.session_state.current_color or c.value == top_card.value or c.color == 'Wild')]
                
                # 봇이 우노 외칠 확률 (80%)
                if len(curr_p['hand']) == 2 and random.random() < 0.8:
                    call_uno(st.session_state.turn)

                if playable:
                    play_card(st.session_state.turn, playable[0])
                else:
                    curr_p['hand'].append(st.session_state.deck.draw())
                    check_uno_penalty(st.session_state.turn)
                    next_turn()
                st.rerun()

    st.write(f"💬 **메시지:** {st.session_state.msg}")
    if st.button("게임 리셋"):
        init_game()
        st.rerun()

# F키 입력을 위한 보이지 않는 JS (Streamlit HTML 사용)
st.components.v1.html(
    """
    <script>
    const doc = window.parent.document;
    doc.addEventListener('keydown', function(e) {
        if (e.key === 'f' || e.key === 'F') {
            const buttons = Array.from(doc.querySelectorAll('button'));
            const unoBtn = buttons.find(el => el.innerText.includes('UNO!'));
            if (unoBtn) unoBtn.click();
        }
    });
    </script>
    """,
    height=0,
)
