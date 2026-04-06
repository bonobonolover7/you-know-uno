import streamlit as st
import random
import time

st.set_page_config(layout="wide", page_title="UNO: Speed Battle")

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
    
    /* 카드 가져오기 버튼 스타일 */
    div.stButton > button[kind="secondary"] {
        width: 100%; height: 50px; font-weight: bold; background-color: #f0f2f6;
    }
    
    /* 우노 버튼 스타일 (빨간색) */
    div.stButton > button[kind="primary"] {
        background-color: #FF0000 !important; color: white !important;
        width: 100%; height: 70px; border-radius: 15px; font-size: 22px !important;
        font-weight: bold; border: 4px solid white; box-shadow: 0 4px 10px rgba(0,0,0,0.3);
        margin-top: 10px;
    }
    
    .game-log {
        background-color: #ffffff; padding: 15px; border-radius: 10px;
        border-left: 5px solid #FF4B4B; margin-bottom: 20px;
        font-size: 18px; font-weight: bold; text-align: center;
    }
    .bot-box {
        background: white; padding: 10px; border-radius: 12px;
        border: 1px solid #ddd; text-align: center; min-width: 120px;
    }
    .wild-bg {
        background: linear-gradient(45deg, #FF4B4B 25%, #F4C542 25%, #F4C542 50%, #4CAF50 50%, #4CAF50 75%, #2196F3 75%);
    }
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

# ---------------- 2. 유틸리티 함수 ----------------
def get_color_code(color):
    return {"Red": "#FF4B4B", "Yellow": "#F4C542", "Green": "#4CAF50", "Blue": "#2196F3", "Wild": "#333333"}.get(color, "#333333")

def render_card_html(card):
    bg = get_color_code(card.color)
    class_name = "card-ui wild-bg" if card.color == "Wild" else "card-ui"
    style = f"background: {bg};" if card.color != "Wild" else ""
    val_map = {"Wild": "🌈", "Wild Draw Four": "+4", "Draw Two": "+2", "Reverse": "🔄", "Skip": "🚫"}
    display_val = val_map.get(card.value, card.value)
    return f"""<div class="{class_name}" style="{style}"><div class="card-type">{card.color.upper()}</div><div class="card-value">{display_val}</div></div>"""

def next_p():
    st.session_state.turn = (st.session_state.turn + st.session_state.direction) % 4
    for p in st.session_state.players:
        if len(p["hand"]) != 1: p["uno_called"] = False

# ---------------- 3. 게임 초기화 ----------------
def init_game():
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

    while True:
        if not deck: break
        first = deck.pop()
        if first.color != "Wild" and first.value.isdigit(): break
        deck.insert(0, first)
        random.shuffle(deck)

    st.session_state.update({
        "deck": deck, "players": players, "discard": [first],
        "current_color": first.color, "turn": 0, "direction": 1,
        "stack": 0, "game_msg": "🎮 게임 시작! 낼 카드가 없으면 자동으로 카드를 가져옵니다.",
        "uno_timer": None, "uno_target": None, "initialized": True,
        "waiting_color": False, "wild_idx": -1
    })

if 'initialized' not in st.session_state:
    init_game()

# ---------------- 4. 액션 로직 ----------------
def call_uno(caller_idx):
    target_idx = st.session_state.get('uno_target')
    if target_idx is not None:
        target = st.session_state.players[target_idx]
        caller = st.session_state.players[caller_idx]
        if caller_idx == target_idx:
            target["uno_called"] = True
            st.session_state.game_msg = f"✨ {caller['name']}: '우노!!!' (방어 성공!)"
        else:
            if st.session_state.deck:
                target["hand"].append(st.session_state.deck.pop())
            st.session_state.game_msg = f"🔔 {caller['name']}님이 먼저 외쳤습니다! {target['name']}님은 벌칙 카드 1장!"
        st.session_state.uno_target = None
        st.session_state.uno_timer = None

def play_action(p_idx, c_idx, chosen_color=None):
    p = st.session_state.players[p_idx]
    card = p["hand"].pop(c_idx)
    st.session_state.discard.append(card)
    st.session_state.current_color = chosen_color if card.color == "Wild" else card.color

    if len(p["hand"]) == 1:
        st.session_state.uno_target = p_idx
        st.session_state.uno_timer = time.time() + random.uniform(0.35, 0.75)
    
    msg = f"📢 {p['name']}님이 {card.value} 카드를 냈습니다."
    if card.value == "Draw Two": st.session_state.stack += 2
    elif card.value == "Wild Draw Four": st.session_state.stack += 4
    if card.value == "Skip": next_p()
    elif card.value == "Reverse": st.session_state.direction *= -1
    
    st.session_state.game_msg = msg
    next_p()

def handle_penalty(p_idx):
    p = st.session_state.players[p_idx]
    s = st.session_state.get('stack', 0)
    for _ in range(s):
        if st.session_state.deck: p["hand"].append(st.session_state.deck.pop())
    st.session_state.stack = 0
    st.session_state.game_msg = f"⚠️ {p['name']}님이 누적된 공격 카드를 모두 받았습니다!"
    next_p()

# ---------------- 5. UI 렌더링 ----------------
st.markdown("<h1 style='text-align: center;'>우노 스피드 배틀</h1>", unsafe_allow_html=True)
st.markdown(f"""<div class="game-log">{st.session_state.get('game_msg', '')}</div>""", unsafe_allow_html=True)

# (1) 봇 정보
bot_cols = st.columns(3)
for i in range(1, 4):
    p = st.session_state.players[i]
    with bot_cols[i-1]:
        border = "3px solid red" if st.session_state.turn == i else "1px solid #ddd"
        is_uno_called = p.get("uno_called", False)
        uno_badge = "❗우노" if len(p["hand"]) == 1 and not is_uno_called else ""
        st.markdown(f"""<div class="bot-box" style="border: {border}"><b>{p['name']}</b><br>보유 카드: {len(p['hand'])}장 <span style='color:red'>{uno_badge}</span></div>""", unsafe_allow_html=True)

st.divider()

# (2) 중앙 영역 (바닥 카드)
_, center_col, _ = st.columns([1, 0.5, 1])
with center_col:
    st.markdown(f"<center><b>현재 색상: {st.session_state.current_color}</b></center>", unsafe_allow_html=True)
    st.markdown(render_card_html(st.session_state.discard[-1]), unsafe_allow_html=True)
    s_val = st.session_state.get('stack', 0)
    if s_val > 0: st.error(f"공격 누적: +{s_val}")

# (3) 봇 우노 타이머 체크
u_timer = st.session_state.get('uno_timer')
if u_timer and time.time() > u_timer:
    call_uno(random.choice([1, 2, 3]))
    st.rerun()

st.divider()

# (4) 내 핸드 처리 & 버튼 배치
curr_p = st.session_state.players[st.session_state.turn]

if st.session_state.get('waiting_color'):
    st.info("색상을 선택하세요!")
    c_cols = st.columns(4)
    for i, c in enumerate(["Red", "Yellow", "Green", "Blue"]):
        if c_cols[i].button(c):
            play_action(0, st.session_state.wild_idx, c)
            st.session_state.waiting_color = False
            st.rerun()

elif not curr_p["bot"]:
    top = st.session_state.discard[-1]
    s = st.session_state.get('stack', 0)
    playable = []
    for i, c in enumerate(curr_p["hand"]):
        if s > 0:
            if c.value == top.value: playable.append(i)
        elif c.color == "Wild" or c.color == st.session_state.current_color or c.value == top.value:
            playable.append(i)

    # [자동 카드 가져오기] 낼 카드가 없으면 즉시 실행
    if not playable:
        st.warning("낼 카드가 없어서 카드를 가져옵니다...")
        time.sleep(1)
        if s > 0: handle_penalty(0)
        else:
            if st.session_state.deck:
                st.session_state.players[0]["hand"].append(st.session_state.deck.pop())
            st.session_state.game_msg = "🃏 낼 카드가 없어 카드 1장을 가져왔습니다."
            next_p()
        st.rerun()

    # 내 카드들 표시
    st.write("### 🎴 나의 카드")
    hand_cols = st.columns(max(len(curr_p["hand"]), 1))
    for i, c in enumerate(curr_p["hand"]):
        with hand_cols[i]:
            st.markdown(render_card_html(c), unsafe_allow_html=True)
            if st.button("내기", key=f"play_{i}", disabled=(i not in playable), use_container_width=True):
                if c.color == "Wild":
                    st.session_state.waiting_color, st.session_state.wild_idx = True, i
                else: play_action(0, i)
                st.rerun()
    
    st.write("")
    # 버튼 영역: 카드 가져오기 버튼 아래에 우노 버튼 배치
    _, btn_col, _ = st.columns([1, 0.6, 1])
    with btn_col:
        if st.button("🃏 카드 가져오기", key="draw_btn", use_container_width=True):
            if s > 0: handle_penalty(0)
            else:
                if st.session_state.deck: st.session_state.players[0]["hand"].append(st.session_state.deck.pop())
                next_p()
            st.rerun()
        
        if st.button("📢 우노!!! (F)", type="primary", key="uno_btn", use_container_width=True):
            call_uno(0)
            st.rerun()

else:
    # 봇 턴
    st.info(f"🤖 {curr_p['name']}가 생각 중...")
    time.sleep(1.2)
    top = st.session_state.discard[-1]
    s = st.session_state.get('stack', 0)
    playable = [i for i, c in enumerate(curr_p["hand"]) if (s > 0 and c.value == top.value) or (s == 0 and (c.color == "Wild" or c.color == st.session_state.current_color or c.value == top.value))]
    
    if playable:
        idx = playable[0]
        c = curr_p["hand"][idx]
        if c.color == "Wild":
            play_action(st.session_state.turn, idx, random.choice(["Red", "Yellow", "Green", "Blue"]))
        else: play_action(st.session_state.turn, idx)
    else:
        if s > 0: handle_penalty(st.session_state.turn)
        else:
            if st.session_state.deck: curr_p["hand"].append(st.session_state.deck.pop())
            st.session_state.game_msg = f"🃏 {curr_p['name']}님이 카드를 가져갔습니다."
            next_p()
    st.rerun()

if st.sidebar.button("게임 다시 시작"):
    st.session_state.clear()
    st.rerun()
