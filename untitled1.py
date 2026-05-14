import streamlit as st
import random
import time

st.set_page_config(layout="wide", page_title="우노 스피드 배틀")

# ---------------- 1. 스타일 & 단축키 (F키) ----------------
st.markdown("""
<style>
    .stApp { background-color: #F9F9F9; }
    .card-ui {
        width: 100px; height: 150px; border-radius: 12px;
        display: flex; flex-direction: column; justify-content: center; align-items: center;
        color: white; font-weight: bold; box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        border: 3px solid white; text-align: center; margin: auto;
    }
    .card-value { font-size: 24px; }
    .card-type { font-size: 10px; opacity: 0.9; margin-bottom: 5px; }
    .wild-bg {
        background: linear-gradient(45deg, #FF4B4B 25%, #F4C542 25%, #F4C542 50%, #4CAF50 50%, #4CAF50 75%, #2196F3 75%) !important;
    }
    .color-card-btn {
        height: 100px; border-radius: 10px; border: 3px solid white;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2); cursor: pointer;
    }
    div.stButton > button[kind="primary"] {
        background-color: #FF0000 !important; color: white !important;
        width: 100%; height: 70px; border-radius: 15px; font-size: 22px !important;
        font-weight: bold; border: 4px solid white; box-shadow: 0 4px 10px rgba(0,0,0,0.3);
    }
    .game-log {
        background-color: #ffffff; padding: 15px; border-radius: 10px;
        border-left: 10px solid #FF4B4B; margin-bottom: 20px;
        font-size: 20px; font-weight: bold; text-align: center;
    }
    .turn-msg { color: #FF4B4B; font-size: 22px; margin-top: 5px; }
</style>
<script>
const doc = window.parent.document;
doc.addEventListener('keydown', function(e) {
    if (e.key.toLowerCase() === 'f') {
        const buttons = doc.querySelectorAll('button');
        for (let btn of buttons) {
            if (btn.innerText.includes('우노')) {
                btn.click();
                break;
            }
        }
    }
});
</script>
""", unsafe_allow_html=True)

class Card:
    def __init__(self, color, value):
        self.color = color
        self.value = value

# ---------------- 2. 유틸리티 ----------------
def get_color_code(color):
    return {"Red": "#FF4B4B", "Yellow": "#F4C542", "Green": "#4CAF50", "Blue": "#2196F3", "Wild": "#333333"}.get(color, "#333333")

def render_card_html(card):
    bg = get_color_code(card.color)
    is_wild = (card.color == "Wild")
    class_name = "card-ui wild-bg" if is_wild else "card-ui"
    style = f"background: {bg};" if not is_wild else ""
    val_map = {"Wild": "🌈", "Wild Draw Four": "+4", "Draw Two": "+2", "Reverse": "🔄", "Skip": "🚫"}
    display_val = val_map.get(card.value, card.value)
    return f"""<div class="{class_name}" style="{style}"><div class="card-type">{card.color.upper()}</div><div class="card-value">{display_val}</div></div>"""

def next_p():
    st.session_state.turn = (st.session_state.turn + st.session_state.direction) % 4
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
        "stack": 0, "game_msg": "🎮 우노 배틀 시작!", "initialized": True,
        "waiting_color": False, "wild_idx": -1, "uno_timer": None, "uno_target": None
    })

# ---------------- 4. 액션 로직 ----------------
def call_uno(caller_idx):
    target_idx = st.session_state.get('uno_target')
    if target_idx is not None:
        target = st.session_state.players[target_idx]
        caller = st.session_state.players[caller_idx]
        if caller_idx == target_idx:
            target["uno_called"] = True
            st.session_state.game_msg = f"✨ {caller['name']}: '우노!!!' (세이프)"
        else:
            if st.session_state.deck: target["hand"].append(st.session_state.deck.pop())
            st.session_state.game_msg = f"🔔 {caller['name']}님이 가로채기! {target['name']}님 1장 추가!"
        st.session_state.uno_target = None
        st.session_state.uno_timer = None

def play_action(p_idx, c_idx, chosen_color=None):
    p = st.session_state.players[p_idx]
    card = p["hand"].pop(c_idx)
    st.session_state.discard.append(card)
    st.session_state.current_color = chosen_color if card.color == "Wild" else card.color

    if len(p["hand"]) == 1:
        st.session_state.uno_target = p_idx
        st.session_state.uno_timer = time.time() + random.uniform(0.3, 0.6)
    
    msg = f"📢 {p['name']}님이 {card.value} 카드를 냈습니다."
    if card.value == "Draw Two": st.session_state.stack += 2
    elif card.value == "Wild Draw Four": st.session_state.stack += 4
    if card.value == "Skip": next_p()
    elif card.value == "Reverse": st.session_state.direction *= -1
    
    st.session_state.game_msg = msg
    next_p()

# ---------------- 5. 메인 UI ----------------
st.markdown("<h1 style='text-align: center;'>우노 스피드 배틀</h1>", unsafe_allow_html=True)

curr_idx = st.session_state.turn
curr_p = st.session_state.players[curr_idx]
turn_info = "🔥 당신의 차례!" if not curr_p["bot"] else f"🤖 {curr_p['name']} 생각 중..."
st.markdown(f"<div class='game-log'>{st.session_state.game_msg}<div class='turn-msg'>{turn_info}</div></div>", unsafe_allow_html=True)

bot_cols = st.columns(3)
for i in range(1, 4):
    p = st.session_state.players[i]
    with bot_cols[i-1]:
        is_turn = (curr_idx == i)
        st.markdown(f"""<div style="border: {'3px solid red' if is_turn else '1px solid #ddd'}; padding:10px; border-radius:10px; background:white; text-align:center;">
                        <b>{p['name']}</b><br>카드: {len(p['hand'])}장 {'<span style="color:red">❗우노</span>' if len(p['hand'])==1 and not p.get('uno_called') else ''}</div>""", unsafe_allow_html=True)

st.divider()

_, center_col, _ = st.columns([1, 0.5, 1])
with center_col:
    st.markdown(f"<center>색상: <b style='color:{get_color_code(st.session_state.current_color)}'>{st.session_state.current_color}</b></center>", unsafe_allow_html=True)
    st.markdown(render_card_html(st.session_state.discard[-1]), unsafe_allow_html=True)
    if st.session_state.stack > 0: st.error(f"공격 누적: +{st.session_state.stack}")

u_timer = st.session_state.get('uno_timer')
if u_timer and time.time() > u_timer:
    call_uno(random.choice([1, 2, 3]))
    st.rerun()

st.divider()

# ---------------- 6. 플레이어 컨트롤 (수정됨) ----------------
me = st.session_state.players[0]
is_my_turn = (curr_idx == 0)

# ---------------- [수정된 내 카드 표시 섹션] ----------------
me = st.session_state.players[0]
st.write(f"### 🎴 나의 카드 (남은 수: {len(me['hand'])}장)")

# 카드가 밑으로 툭 떨어지는 현상을 방지하기 위해 
# columns 생성 시 너비를 균등하게 배분합니다.
num_cards = len(me["hand"])
if num_cards > 0:
    hand_cols = st.columns(num_cards) # 카드 개수만큼 정확히 칸 생성
    
    top = st.session_state.discard[-1]
    s = st.session_state.stack
    
    # 내 턴일 때 낼 수 있는 카드 계산
    playable = [i for i, c in enumerate(me["hand"]) if (s > 0 and c.value == top.value) or (s == 0 and (c.color == "Wild" or c.color == st.session_state.current_color or c.value == top.value))]

    for i, c in enumerate(me["hand"]):
        with hand_cols[i]:
            # 카드 이미지 출력
            st.markdown(render_card_html(c), unsafe_allow_html=True)
            
            # 버튼이 카드 바로 밑에 고정되도록 함
            if is_my_turn and not st.session_state.waiting_color:
                if st.button("내기", key=f"p_{i}", disabled=(i not in playable), use_container_width=True):
                    if c.color == "Wild":
                        st.session_state.waiting_color, st.session_state.wild_idx = True, i
                    else: 
                        play_action(0, i)
                    st.rerun()
else:
    st.write("낼 카드가 없습니다!")

# ---------------- 봇 실행 로직 (이 부분이 있어야 게임이 돌아갑니다) ----------------
if not is_my_turn:
    time.sleep(1.0) # 봇 생각하는 시간
    bot_playable = [i for i, c in enumerate(curr_p["hand"]) if (s > 0 and c.value == top.value) or (s == 0 and (c.color == "Wild" or c.color == st.session_state.current_color or c.value == top.value))]
    
    if bot_playable:
        idx = bot_playable[0]
        c = curr_p["hand"][idx]
        play_action(curr_idx, idx, random.choice(["Red", "Yellow", "Green", "Blue"]) if c.color == "Wild" else None)
    else:
        # 낼 카드 없으면 드로우
        for _ in range(max(s, 1)):
            if st.session_state.deck: curr_p["hand"].append(st.session_state.deck.pop())
        st.session_state.stack = 0
        st.session_state.game_msg = f"🃏 {curr_p['name']}님이 드로우했습니다."
        next_p()
    
    st.rerun() # 중요: 봇이 행동한 뒤 화면을 갱신해야 내 턴으로 넘어옵니다.
