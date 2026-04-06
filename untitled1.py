import streamlit as st
import random
import time

st.set_page_config(layout="wide", page_title="우노 모션 배틀")

# ---------------- 1. 애니메이션 (합체 모션 & 오버레이) ----------------
st.markdown("""
<style>
    /* 합체 애니메이션 (+는 왼쪽, 2는 오른쪽) */
    @keyframes mergeLeft {
        0% { transform: translate(-200%, -50%) scale(0.5); opacity: 0; }
        100% { transform: translate(-100%, -50%) scale(1.5); opacity: 1; }
    }
    @keyframes mergeRight {
        0% { transform: translate(100%, -50%) scale(0.5); opacity: 0; }
        100% { transform: translate(0%, -50%) scale(1.5); opacity: 1; }
    }
    @keyframes fadeOutSpecial {
        0% { opacity: 1; scale: 1.5; }
        100% { opacity: 0; scale: 2; }
    }
    @keyframes cubicOutEffect {
        0% { transform: translate(-50%, -50%) scale(0.3) rotate(0deg); opacity: 0; }
        50% { transform: translate(-50%, -50%) scale(1.5) rotate(180deg); opacity: 1; }
        100% { transform: translate(-50%, -50%) scale(2) rotate(360deg); opacity: 0; }
    }
    @keyframes slideInHand {
        0% { transform: translateX(100px); opacity: 0; }
        100% { transform: translateX(0); opacity: 1; }
    }

    /* 화면 전체를 덮는 고정 레이어 (다른 요소 방해 안 함) */
    .overlay-container {
        position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
        z-index: 9999; pointer-events: none; display: flex; align-items: center; justify-content: center;
    }
    .effect-text { font-size: 180px; font-weight: bold; position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); }
    
    .plus-part { animation: mergeLeft 0.6s ease-out forwards, fadeOutSpecial 0.4s 0.6s forwards; color: white; text-shadow: 4px 4px 10px rgba(0,0,0,0.5); }
    .two-part { animation: mergeRight 0.6s ease-out forwards, fadeOutSpecial 0.4s 0.6s forwards; color: white; text-shadow: 4px 4px 10px rgba(0,0,0,0.5); }
    .normal-effect { animation: cubicOutEffect 1s cubic-bezier(0.215, 0.61, 0.355, 1) forwards; }

    .vignette {
        position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
        box-shadow: inset 0 0 150px 60px var(--v-color); z-index: 9998;
        animation: vignetteFade 1s ease-in-out forwards; pointer-events: none;
    }
    @keyframes vignetteFade { 0%, 100% { opacity: 0; } 50% { opacity: 0.6; } }

    .card-new { animation: slideInHand 0.4s ease-out; }
    .wild-bg { background: linear-gradient(45deg, #FF4B4B 25%, #F4C542 25%, #F4C542 50%, #4CAF50 50%, #4CAF50 75%, #2196F3 75%) !important; }
</style>
""", unsafe_allow_html=True)

class Card:
    def __init__(self, color, value):
        self.color, self.value = color, value

def get_color_code(color):
    return {"Red": "#FF4B4B", "Yellow": "#F4C542", "Green": "#4CAF50", "Blue": "#2196F3", "Wild": "#333333"}.get(color, "#333333")

def render_card_html(card, extra_class=""):
    bg = get_color_code(card.color)
    cls = f"card-ui {'wild-bg' if card.color == 'Wild' else ''} {extra_class}"
    val_map = {"Wild": "🌈", "Wild Draw Four": "+4", "Draw Two": "+2", "Reverse": "🔄", "Skip": "🚫"}
    return f"""<div class="{cls}" style="background:{bg if card.color != 'Wild' else ''}; width:100px; height:150px; border-radius:12px; border:3px solid white; display:flex; flex-direction:column; justify-content:center; align-items:center; color:white; font-weight:bold; box-shadow:0 4px 10px rgba(0,0,0,0.2); margin:auto;">
    <div style="font-size:10px;">{card.color.upper()}</div><div style="font-size:30px;">{val_map.get(card.value, card.value)}</div></div>"""

# ---------------- 2. 상태 초기화 ----------------
if 'initialized' not in st.session_state:
    colors, values = ['Red', 'Yellow', 'Green', 'Blue'], [str(i) for i in range(10)] + ['Skip', 'Reverse', 'Draw Two']
    deck = [Card(c, v) for c in colors for v in values] * 2
    for _ in range(8): deck.append(Card('Wild', 'Wild' if _ < 4 else 'Wild Draw Four'))
    random.shuffle(deck)
    players = [{"name": n, "hand": [deck.pop() for _ in range(7)], "bot": b} for n, b in [("나", False), ("봇 1", True), ("봇 2", True), ("봇 3", True)]]
    first = deck.pop()
    while first.color == "Wild": deck.insert(0, first); random.shuffle(deck); first = deck.pop()
    st.session_state.update({"deck": deck, "players": players, "discard": [first], "current_color": first.color, "turn": 0, "direction": 1, "stack": 0, "game_msg": "🎮 우노 배틀!", "initialized": True, "effect": None, "v_color": None})

# ---------------- 3. 액션 로직 ----------------
def trigger_effect(symbol, color):
    st.session_state.effect = symbol
    st.session_state.v_color = get_color_code(color)

def play_card(p_idx, c_idx, chosen_color=None):
    p = st.session_state.players[p_idx]
    card = p["hand"].pop(c_idx)
    st.session_state.discard.append(card)
    st.session_state.current_color = chosen_color if card.color == "Wild" else card.color
    
    if card.value == "Reverse": trigger_effect("🔄", card.color); st.session_state.direction *= -1
    elif card.value == "Skip": trigger_effect("🚫", card.color); st.session_state.turn = (st.session_state.turn + st.session_state.direction) % 4
    elif "Draw" in card.value:
        trigger_effect("+2" if "Two" in card.value else "+4", card.color)
        st.session_state.stack += (4 if "Four" in card.value else 2)

    st.session_state.game_msg = f"📢 {p['name']}님이 {card.value}를 냈습니다."
    st.session_state.turn = (st.session_state.turn + st.session_state.direction) % 4

def take_card_and_stay(p_idx):
    # 나한테 추가를 먼저 하고 나서 턴을 넘기기 위해 count 계산
    p = st.session_state.players[p_idx]
    count = st.session_state.stack if st.session_state.stack > 0 else 1
    for _ in range(count):
        if st.session_state.deck: p["hand"].append(st.session_state.deck.pop())
    st.session_state.stack = 0
    st.session_state.game_msg = f"🃏 {p['name']}님이 카드를 가져왔습니다."
    # 턴 넘기기는 여기서 즉시 안 하고 rerun 후에 판단하게 할 수도 있지만, 
    # 흐름상 여기서 넘겨야 다음 rerun 때 봇 차례가 됨.
    st.session_state.turn = (st.session_state.turn + st.session_state.direction) % 4

# ---------------- 4. UI 렌더링 ----------------
# 효과 오버레이 (독립 레이어)
eff = st.session_state.get('effect')
v_col = st.session_state.get('v_color')
if eff:
    st.markdown(f'<div class="vignette" style="--v-color: {v_col};"></div>', unsafe_allow_html=True)
    st.markdown('<div class="overlay-container">', unsafe_allow_html=True)
    if "+" in eff: # 플러스 합체 효과
        st.markdown(f'<div class="effect-text plus-part" style="left:50%;">+</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="effect-text two-part" style="left:50%;">{eff[1:]}</div>', unsafe_allow_html=True)
    else: # 리버스, 금지 효과
        st.markdown(f'<div class="effect-text normal-effect">{eff}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.session_state.effect = None

st.markdown("<h1 style='text-align:center;'>우노 모션 배틀</h1>", unsafe_allow_html=True)
curr_p = st.session_state.players[st.session_state.turn]
st.info(f"{st.session_state.game_msg} | 현재: {'🔥 당신의 차례' if not curr_p['bot'] else f'🤖 {curr_p['name']} 차례'}")

# 봇/플레이어 요약
cols = st.columns(4)
for i, p in enumerate(st.session_state.players):
    with cols[i]:
        bg = "#FFEBEE" if st.session_state.turn == i else "white"
        st.markdown(f'<div style="background:{bg}; padding:10 thumb; border-radius:10px; border:2px solid #ddd; text-align:center;"><b>{p["name"]}</b><br>{len(p["hand"])}장</div>', unsafe_allow_html=True)

st.divider()
_, center, _ = st.columns([1, 0.5, 1])
with center:
    st.markdown(f"<center>색상: <b style='color:{get_color_code(st.session_state.current_color)}'>{st.session_state.current_color}</b></center>", unsafe_allow_html=True)
    st.markdown(render_card_html(st.session_state.discard[-1]), unsafe_allow_html=True)
    if st.session_state.stack > 0: st.error(f"STACK +{st.session_state.stack}")

st.divider()

# 내 조작 영역
if st.session_state.get('waiting_color'):
    st.markdown("<h3 style='text-align:center;'>🌈 색상 선택</h3>", unsafe_allow_html=True)
    cc = st.columns(4)
    for i, c in enumerate(["Red", "Yellow", "Green", "Blue"]):
        if cc[i].button(c, use_container_width=True):
            play_card(0, st.session_state.wild_idx, c); st.session_state.waiting_color = False; st.rerun()

elif not curr_p["bot"]:
    top, s = st.session_state.discard[-1], st.session_state.stack
    playable = [i for i, c in enumerate(curr_p["hand"]) if (s > 0 and c.value == top.value) or (s == 0 and (c.color == "Wild" or c.color == st.session_state.current_color or c.value == top.value))]
    
    if not playable:
        st.warning("낼 카드가 없습니다. 자동으로 가져옵니다...")
        time.sleep(1); take_card_and_stay(0); st.rerun()

    st.write("### 🎴 나의 카드")
    h_cols = st.columns(max(len(curr_p["hand"]), 1))
    for i, c in enumerate(curr_p["hand"]):
        with h_cols[i]:
            st.markdown(render_card_html(c, "card-new"), unsafe_allow_html=True)
            if st.button("내기", key=f"p_{i}", disabled=(i not in playable), use_container_width=True):
                if c.color == "Wild": st.session_state.waiting_color, st.session_state.wild_idx = True, i
                else: play_card(0, i)
                st.rerun()
    
    _, btn_c, _ = st.columns([1, 0.6, 1])
    with btn_c:
        if st.button("🃏 카드 가져오기", use_container_width=True):
            take_card_and_stay(0); st.rerun()
        if st.button("📢 우노!!! (F)", type="primary", use_container_width=True):
            st.rerun()
else:
    time.sleep(1.5); top, s = st.session_state.discard[-1], st.session_state.stack
    playable = [i for i, c in enumerate(curr_p["hand"]) if (s > 0 and c.value == top.value) or (s == 0 and (c.color == "Wild" or c.color == st.session_state.current_color or c.value == top.value))]
    if playable: play_card(st.session_state.turn, playable[0], random.choice(["Red", "Yellow", "Green", "Blue"]))
    else: take_card_and_stay(st.session_state.turn)
    st.rerun()
