st.divider()

# ========================== [수정할 부분 시작] ==========================
me = st.session_state.players[0] # 내 정보
is_my_turn = (st.session_state.turn == 0)
top = st.session_state.discard[-1]
s = st.session_state.stack

# 1. 내 카드 UI 항상 표시 (봇 턴일 때도 변화가 즉시 보이게 밖으로 뺌)
st.write("### 🎴 나의 카드")
hand_cols = st.columns(max(len(me["hand"]), 1))

# 낼 수 있는 카드 계산 (내 턴일 때만 계산)
playable = []
if is_my_turn:
    playable = [i for i, c in enumerate(me["hand"]) if (s > 0 and c.value == top.value) or (s == 0 and (c.color == "Wild" or c.color == st.session_state.current_color or c.value == top.value))]

# 카드 렌더링
for i, c in enumerate(me["hand"]):
    with hand_cols[i]:
        st.markdown(render_card_html(c), unsafe_allow_html=True)
        # 내 턴이면서 와일드카드 색상 선택 중이 아닐 때만 버튼 활성화
        if is_my_turn and not st.session_state.waiting_color:
            if st.button("내기", key=f"p_{i}", disabled=(i not in playable), use_container_width=True):
                if c.color == "Wild":
                    st.session_state.waiting_color, st.session_state.wild_idx = True, i
                else: 
                    play_action(0, i)
                st.rerun()

# 2. 색상 선택 화면 또는 내 턴 전용 액션 처리
if st.session_state.waiting_color:
    st.markdown("<h3 style='text-align: center;'>🌈 바꿀 색상을 선택하세요!</h3>", unsafe_allow_html=True)
    c_cols = st.columns(4)
    for i, c in enumerate(["Red", "Yellow", "Green", "Blue"]):
        with c_cols[i]:
            st.markdown(f"<div class='color-card-btn' style='background:{get_color_code(c)}'></div>", unsafe_allow_html=True)
            if st.button(f"{c} 확정", key=f"c_{c}", use_container_width=True):
                play_action(0, st.session_state.wild_idx, c)
                st.session_state.waiting_color = False 
                st.rerun()

elif is_my_turn:
    # 낼 카드가 없을 때 자동 드로우
    if not playable:
        st.warning("낼 카드가 없어 자동으로 가져옵니다...")
        time.sleep(0.8)
        if s > 0:
            for _ in range(s):
                if st.session_state.deck: me["hand"].append(st.session_state.deck.pop())
            st.session_state.stack = 0
        else:
            if st.session_state.deck: me["hand"].append(st.session_state.deck.pop())
        st.session_state.game_msg = "🃏 카드를 가져오고 턴을 넘깁니다."
        next_p()
        st.rerun()

    # 카드 가져오기 및 우노 버튼
    st.write("")
    _, btn_col, _ = st.columns([1, 0.6, 1])
    with btn_col:
        if st.button("🃏 카드 가져오기", use_container_width=True):
            if s > 0:
                for _ in range(s):
                    if st.session_state.deck: me["hand"].append(st.session_state.deck.pop())
                st.session_state.stack = 0
            else:
                if st.session_state.deck: me["hand"].append(st.session_state.deck.pop())
            next_p()
            st.rerun()
        if st.button("📢 우노!!! (F)", type="primary", use_container_width=True):
            call_uno(0)
            st.rerun()

# 3. 봇 턴 처리 로직
elif curr_p["bot"]:
    time.sleep(1.2)
    top = st.session_state.discard[-1]
    s = st.session_state.stack
    playable = [i for i, c in enumerate(curr_p["hand"]) if (s > 0 and c.value == top.value) or (s == 0 and (c.color == "Wild" or c.color == st.session_state.current_color or c.value == top.value))]
    if playable:
        idx = playable[0]
        c = curr_p["hand"][idx]
        play_action(st.session_state.turn, idx, random.choice(["Red", "Yellow", "Green", "Blue"]) if c.color == "Wild" else None)
    else:
        for _ in range(max(s, 1)):
            if st.session_state.deck: curr_p["hand"].append(st.session_state.deck.pop())
        st.session_state.stack = 0
        st.session_state.game_msg = f"🃏 {curr_p['name']}님이 카드를 가져갔습니다."
        next_p()
    st.rerun()
# ========================== [수정할 부분 끝] ==========================
