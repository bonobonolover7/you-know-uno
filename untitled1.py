import streamlit as st
import random
import time

st.set_page_config(layout="wide", page_title="UNO: Speed Battle")

# ---------------- 1. 스타일 & 단축키 스크립트 ----------------
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
    
    /* 빨간색 우노 버튼 스타일 */
    .uno-btn-container {
        display: flex; justify-content: center; margin: 20px 0;
    }
    div.stButton > button[kind="primary"] {
        background-color: #FF0000 !important; color: white !important;
        width: 150px; height: 60px; border-radius: 30px; font-size: 20px !important;
        font-weight: bold; border: 4px solid white; box-shadow: 0 4px 10px rgba(0,0,0,0.3);
    }
    .game-log {
        background-color: #ffffff; padding: 15px; border-radius: 10px;
        border-left: 5px solid #FF4B4B; margin-bottom: 20px;
        font-size: 18px; font-weight: bold; text-align: center;
    }
</style>

<script>
// F 키를 누르면 우노 버튼을 클릭하게 하는 스크립트
const doc = window.parent.document;
doc.addEventListener('keydown', function(e) {
    if (e.key.toLowerCase() === 'f') {
        const buttons = doc.querySelectorAll('button');
        for (let btn of buttons) {
            if (btn.innerText.includes('UNO')) {
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

# ---------------- 2. 게임 로직 함수 ----------------
def init_game():
    colors = ['Red', 'Yellow', 'Green', 'Blue']
    values = [str(i) for i in range(10)] + ['Skip', 'Reverse', 'Draw Two']
    deck = [Card(c, v) for c in colors for v in values] * 2
    for _ in range(4):
        deck.append(Card('Wild', 'Wild'))
        deck.append(Card('Wild', 'Wild Draw Four'))
    random.shuffle(deck)

    players = [
        {"name": "YOU", "hand": [], "bot": False, "uno_called": False},
        {"name": "BOT 1", "hand": [], "bot": True, "uno_called": False},
        {"name": "BOT 2", "hand": [], "bot": True, "uno_called": False},
        {"name": "BOT 3", "hand": [], "bot": True, "uno_called": False}
    ]
    for p in players:
        p["hand"] = [deck.pop() for _ in range(7)]

    while True:
        first = deck.pop()
        if first.color != "Wild" and first.value.isdigit(): break
        deck.insert(0, first)
        random.shuffle(deck)

    st.session_state.update({
        "deck": deck, "players": players, "discard": [first],
        "current_color": first.color, "turn": 0, "direction": 1,
        "stack": 0, "game_msg": "🎮 게임 시작! (F키로 우노를 외치세요!)",
        "uno_timer": None, "uno_target": None, "initialized": True
    })

if 'initialized' not in st.session_state:
    init_game()

def next_p():
    st.session_state.turn = (st.session_state.turn + st.session_state.direction) % 4
    # 새로운 턴이 시작될 때마다 우노 상태 초기화 (손패가 1장이 아닐 경우)
    for p in st.session_state.players:
        if len(p["hand"]) != 1: p["uno_called"] = False

def play_action(p_idx, c_idx, chosen_color=None):
    p = st.session_state.players[p_idx]
    card = p["hand"].pop(c_idx)
    st.session_state.discard.append(card)
    st.session_state.current_color = chosen_color if card.color == "Wild" else card.color

    # 우노 체크: 카드를 내고 1장이 남았다면 우노 타이머 발동
    if len(p["hand"]) == 1:
        st.session_state.uno_target = p_idx
        # 인간의 평균 반응 속도를 반영한 봇의 반응 시간 (0.25초 ~ 0.8초 사이)
        st.session_state.uno_timer = time.time() + random.uniform(0.25, 0.8)
    
    msg = f"📢 {p['name']}님이 {card.value}를 냈습니다."
    if card.value == "Draw Two": st.session_state.stack += 2
    elif card.value == "Wild Draw Four": st.session_state.stack += 4
    if card.value == "Skip": next_p()
    elif card.value == "Reverse": st.session_state.direction *= -1
    
    st.session_state.game_msg = msg
    next_p()

# ---------------- 3. 우노 관련 함수 ----------------
def call_uno(caller_idx):
    target_idx = st.session_state.uno_target
    if target_idx is not None:
        target = st.session_state.players[target_idx]
        caller = st.session_state.players[caller_idx]
        
        if caller_idx == target_idx:
            # 본인이 먼저 외침
            target["uno_called"] = True
            st.session_state.game_msg = f"✨ {caller['name']}: 'UNO!!!' (방어 성공)"
        else:
            # 다른 사람이 먼저 외침 (페널티)
            target["hand"].append(st.session_state.deck.pop())
            st.session_state.game_msg = f"🔔 {caller['name']}님이 먼저 외쳤습니다! {target['name']}님은 1장 추가!"
        
        st.session_state.uno_target = None
        st.session_state.uno_timer = None
    else:
        st.warning("지금은 우노를 외칠 때가 아닙니다!")

# ---------------- 4. UI 렌더링 ----------------
st.markdown("<h1 style='text-align: center;'>UNO: SPEED BATTLE</h1>", unsafe_allow_html=True)
st.markdown(f"""<div class="game-log">{st.session_state.game_msg}</div>""", unsafe_allow_html=True)

# (1) 봇 정보
bot_cols = st.columns(3)
for i in range(1, 4):
    p = st.session_state.players[i]
    with bot_cols[i-1]:
        border = "3px solid red" if st.session_state.turn == i else "1px solid #ddd"
        uno_badge = "❗UNO" if len(p["hand"]) == 1 and not p["uno_called"] else ""
        st.markdown(f"""<div class="bot-box" style="border: {border}"><b>{p['name']}</b><br>{len(p['hand'])} cards {uno_badge}</div>""", unsafe_allow_html=True)

st.divider()

# (2) 중앙 영역 & 빨간색 우노 버튼
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    st.markdown(f"<center><b>COLOR: {st.session_state.current_color}</b></center>", unsafe_allow_html=True)
    st.markdown(f"<div style='transform: scale(1.2); margin-bottom:20px;'>{render_card_html(st.session_state.discard[-1])}</div>", unsafe_allow_html=True)
    
    # 빨간 우노 버튼
    if st.button("📢 UNO (F)", type="primary", use_container_width=True):
        call_uno(0)
        st.rerun()

# ---------------- 5. 봇 우노 반응 로직 ----------------
if st.session_state.uno_timer and time.time() > st.session_state.uno_timer:
    # 봇 중 한 명이 랜덤하게 우노를 외침 (플레이어보다 빨랐을 경우)
    bot_callers = [1, 2, 3]
    call_uno(random.choice(bot_callers))
    st.rerun()

st.divider()

# (3) 플레이어 조작
curr_p = st.session_state.players[st.session_state.turn]
if not curr_p["bot"] and not st.session_state.get('waiting_color'):
    st.write("### 🎴 YOUR HAND")
    playable = [i for i, c in enumerate(curr_p["hand"]) if (st.session_state.stack == 0 and (c.color == "Wild" or c.color == st.session_state.current_color or c.value == st.session_state.discard[-1].value)) or (st.session_state.stack > 0 and c.value == st.session_state.discard[-1].value)]
    
    cols = st.columns(len(curr_p["hand"]) + 1)
    for i, c in enumerate(curr_p["hand"]):
        with cols[i]:
            st.markdown(render_card_html(c), unsafe_allow_html=True)
            if st.button("내기", key=f"p_{i}", disabled=(i not in playable)):
                if c.color == "Wild":
                    st.session_state.waiting_color, st.session_state.wild_idx = True, i
                else: play_action(0, i)
                st.rerun()
    with cols[-1]:
        if st.button("DRAW", use_container_width=True):
            if st.session_state.stack > 0: handle_penalty(0)
            else:
                curr_p["hand"].append(st.session_state.deck.pop())
                next_p()
            st.rerun()

elif curr_p["bot"]:
    st.info(f"🤖 {curr_p['name']} 차례...")
    time.sleep(1.2)
    # (봇 카드 내기 로직 생략 - 이전과 동일)
    # ... (생략된 봇 플레이 로직을 수행하도록 코드를 유지하십시오)
    playable = [i for i, c in enumerate(curr_p["hand"]) if (st.session_state.stack == 0 and (c.color == "Wild" or c.color == st.session_state.current_color or c.value == st.session_state.discard[-1].value)) or (st.session_state.stack > 0 and c.value == st.session_state.discard[-1].value)]
    if playable:
        idx = playable[0]
        c = curr_p["hand"][idx]
        if c.color == "Wild": play_action(st.session_state.turn, idx, random.choice(["Red", "Yellow", "Green", "Blue"]))
        else: play_action(st.session_state.turn, idx)
    else:
        if st.session_state.stack > 0: handle_penalty(st.session_state.turn)
        else:
            curr_p["hand"].append(st.session_state.deck.pop())
            next_p()
    st.rerun()

# (필요한 유틸리티 함수 - 이전 답변 참조)
def render_card_html(card):
    # (위의 render_card_html 로직과 동일하게 유지)
    bg = get_color_code(card.color)
    class_name = "card-ui wild-bg" if card.color == "Wild" else "card-ui"
    style = f"background: {bg};" if card.color != "Wild" else ""
    val_map = {"Wild": "🌈", "Wild Draw Four": "+4", "Draw Two": "+2", "Reverse": "🔄", "Skip": "🚫"}
    return f"""<div class="{class_name}" style="{style}"><div class="card-type">{card.color.upper()}</div><div class="card-value">{val_map.get(card.value, card.value)}</div></div>"""

def get_color_code(color):
    return {"Red": "#FF4B4B", "Yellow": "#F4C542", "Green": "#4CAF50", "Blue": "#2196F3", "Wild": "#333333"}.get(color, "#333333")
