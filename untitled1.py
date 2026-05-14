# ---------------- 5. 메인 UI ----------------
st.markdown("<h1 style='text-align: center;'>우노 스피드 배틀</h1>", unsafe_allow_html=True)

curr_idx = st.session_state.turn
curr_p = st.session_state.players[curr_idx]
is_my_turn = (not curr_p["bot"]) # 내 턴인지 확인

# 상황판 표시
turn_info = "🔥 당신의 차례!" if is_my_turn else f"🤖 {curr_p['name']} 생각 중..."
st.markdown(f"<div class='game-log'>{st.session_state.game_msg}<div class='turn-msg'>{turn_info}</div></div>", unsafe_allow_html=True)

# 봇 상태창
bot_cols = st.columns(3)
for i in range(1, 4):
    p = st.session_state.players[i]
    with bot_cols[i-1]:
        st.markdown(f"""<div style="border: {'3px solid red' if curr_idx == i else '1px solid #ddd'}; padding:10px; border-radius:10px; background:white; text-align:center;">
                        <b>{p['name']}</b><br>카드: {len(p['hand'])}장</div>""", unsafe_allow_html=True)

st.divider()

# 중앙 버린 카드 더미
_, center_col, _ = st.columns([1, 0.5, 1])
with center_col:
    st.markdown(f"<center>색상: <b style='color:{get_color_code(st.session_state.current_color)}'>{st.session_state.current_color}</b></center>", unsafe_allow_html=True)
    st.markdown(render_card_html(st.session_state.discard[-1]), unsafe_allow_html=True)
    if st.session_state.stack > 0: st.error(f"공격 누적: +{st.session_state.stack}")

st.divider()

# ---------------- [핵심: 내 카드 표시 로직] ----------------
me = st.session_state.players[0]
st.write(f"### 🎴 나의 카드 (남은 수: {len(me['hand'])}장)")

# 내 카드는 봇 턴일 때도 "항상" 먼저 그려지도록 조건문 밖으로 배치
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
