"""
Career Compass — 정보융합학부 진로 나침반 앱
메인 실행 파일

실행: streamlit run app.py
"""

import logging
import os

import time
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components

from modules.auth import login, add_test_record, load_user, delete_test_record, register_new_user, delete_user
from modules.data_loader import load_questions, load_results, load_courses
from modules.quiz import build_test_result
from modules.result import render_result_page
from modules.roadmap import build_roadmap_figure

# 로깅 설정
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename="logs/app.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    encoding="utf-8",
)
logger = logging.getLogger(__name__)

# 페이지 설정
st.set_page_config(
    page_title="Career Compass — 정보융합학부 진로 나침반",
    page_icon="🧭",
    layout="centered",
)

# 제출자 정보
STUDENT_ID = "2021603038"
STUDENT_NAME = "송호성"

def scroll_to_top():
    """페이지 진입 시 화면 최상단으로 스크롤"""
    components.html(
        """
        <script>
            window.parent.document.querySelector('[data-testid="stMain"]').scrollTo(0, 0);
        </script>
        """,
        height=0,
    )

def scroll_to_cache_demo():
    """캐싱 시연 expander 위치로 스크롤"""
    components.html(
        """
        <script>
            setTimeout(() => {
                const expanders = window.parent.document.querySelectorAll('[data-testid="stExpander"]');
                if (expanders.length > 0) {
                    expanders[expanders.length - 1].scrollIntoView({behavior: 'smooth', block: 'start'});
                }
            }, 100);
        </script>
        """,
        height=0,
    )

# 첫 화면 전용 — 제출자 정보 박스
def render_submitter_info():
    """제출자(앱 개발자) 학번/이름 표시 — 첫 화면에서만 노출 (요강 필수)"""
    st.caption(
        f"**앱 개발자**: {STUDENT_NAME} ({STUDENT_ID}) | "
        f"광운대학교 수학과 (정보융합학부 복수전공) "
    )

# 첫 화면
def render_home():
    """첫 화면 — 앱 소개 + 시작 버튼"""
    logger.info("[PAGE] 홈 화면 진입")
    st.title("🧭 Career Compass")
    st.subheader("정보융합학부 진로 나침반")
    
    st.markdown("---")
    
    st.markdown(
        """
        <style>
        .tooltip {
            position: relative;
            border-bottom: 1px dotted #888;
            cursor: help;
        }
        .tooltip:hover::after {
            content: attr(data-tip);
            position: absolute;
            bottom: 125%;
            left: 50%;
            transform: translateX(-50%);
            background: #333;
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.85em;
            white-space: nowrap;
            z-index: 1000;
        }
        </style>
        
        **이 앱은 광운대학교 정보융합학부 학생을 위한 진로 성향 테스트입니다.**
        
        - 21문항 2지선다 테스트로 본인의 진로 성향을 3축(<span class="tooltip" data-tip="Data vs Visual — 데이터사이언스 vs 비주얼테크놀로지">D/V</span>, <span class="tooltip" data-tip="Analytical vs Practical — 원리·이론 탐구 vs 실험·구현 중심">A/P</span>, <span class="tooltip" data-tip="Research vs Service — 연구 환경 vs 서비스 환경">R/S</span>)으로 분석합니다
        - 8가지 유형 중 본인의 정체성을 찾고, 2026 이수체계도 위에 맞춤 교과목 로드맵을 받습니다
        - 본인 유형에 어울리는 직무와 함께 빠지기 쉬운 함정도 함께 안내합니다
        """,
        unsafe_allow_html=True,
    )
    
    st.markdown("---")
    
    if st.button("테스트 시작하기 →", type="primary", use_container_width=True):
        logger.info("[CLICK] 테스트 시작 버튼 → 로그인 페이지로 이동")
        st.session_state.page = "login"
        st.rerun()
    
    st.caption(
        "💡 이 테스트는 진로 탐색을 돕기 위한 참고 도구이며, 실제 진로 결정은 "
        "교과목 수강과 프로젝트 경험을 통해 이루어집니다."
    )

# 로그인 화면
def render_login():
    """로그인 화면 — 학번 + 이름 입력 + 검증"""
    logger.info("[PAGE] 로그인 화면 진입")
    st.title("🔐 로그인")
    st.markdown(
        "테스트 결과를 저장하고 이전 기록과 비교하기 위해 학번과 이름을 입력해주세요. "
        "학번이 같다면 동일 사용자로 식별됩니다."
    )
    
    st.markdown("---")
    
    student_id = st.text_input(
        "학번",
        placeholder="예: 2027204010",
        help="학번 10자리 (숫자)",
        max_chars=10,
    )
    
    name = st.text_input(
        "이름",
        placeholder="예: 홍길동",
        help="한글 또는 영문 (2~10자)",
        max_chars=10,
    )
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        if st.button("← 이전", use_container_width=True):
            st.session_state.page = "home"
            st.rerun()
    
    with col2:
        if st.button("로그인 →", type="primary", use_container_width=True):
            success, message, user_data = login(student_id, name)
            
            if success:
                if user_data.get("is_new"):
                    # 신규 사용자 — 모달 띄움 (페이지 이동 X)
                    confirm_new_user(user_data)
                else:
                    # 기존 사용자 — 바로 history로
                    st.session_state.student_id = user_data["student_id"]
                    st.session_state.name = user_data["name"]
                    st.session_state.user_data = user_data
                    st.session_state.current_part_idx = 0
                    st.session_state.part_answers = {}
                    st.session_state.viewing_history = False
                    st.session_state.show_all_history = False
                    st.success(message)
                    st.session_state.page = "history"
                    st.session_state.scroll_to_top = True
                    st.rerun()
            else:
                st.error(message)

@st.dialog("로그아웃 확인")
def confirm_logout():
    """로그아웃 확인 모달 다이얼로그"""
    st.markdown("정말 로그아웃하시겠습니까?")
    st.caption("로그아웃하면 다시 학번/이름을 입력해야 합니다.")
    
    st.markdown("")  # 간격
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("아니오", use_container_width=True, key="logout_cancel"):
            st.rerun()  # 다이얼로그 닫기
    
    with col2:
        if st.button("예, 로그아웃", type="primary", use_container_width=True, key="logout_confirm"):
            # session_state 초기화
            for key in [
                "student_id", "name", "user_data",
                "current_part_idx", "part_answers",
                "viewing_history", "show_all_history",
                "selected_test_idx", "test_result",
            ]:
                if key in st.session_state:
                    del st.session_state[key]
            st.session_state.page = "home"
            st.rerun()

@st.dialog("테스트 기록 삭제")
def confirm_delete_test(test_idx: int, type_code: str, type_name: str):
    """테스트 기록 삭제 확인 모달"""
    st.markdown(f"**{type_code}** — _{type_name}_ 기록을 삭제하시겠습니까?")
    st.caption("⚠️ 삭제된 기록은 복구할 수 없습니다.")
    
    st.markdown("")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("아니오", use_container_width=True, key="delete_cancel"):
            st.rerun()
    
    with col2:
        if st.button("예, 삭제", type="primary", use_container_width=True, key="delete_confirm"):
            clear_cache_demo()
            student_id = st.session_state.get("student_id")
            if delete_test_record(student_id, test_idx):
                st.session_state.user_data = load_user(student_id)
                st.session_state.viewing_history = False
                st.session_state.page = "history"
                st.session_state.scroll_to_top = True
            st.rerun()

@st.dialog("신규 사용자 확인")
def confirm_new_user(user_data: dict):
    """신규 사용자 확인 모달 — 학번 표시 + 시작 여부 묻기"""
    student_id = user_data["student_id"]
    name = user_data["name"]
    
    st.markdown(f"입력한 학번 **{student_id}**으로 등록된 정보가 없습니다.")
    st.markdown(f"**{name}**님으로 바로 테스트를 시작할까요?")
    st.caption("💡 학번에 오타가 있다면 '다시 시도'를 눌러 확인해주세요.")
    
    st.markdown("")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("다시 시도", use_container_width=True, key="newuser_cancel"):
            st.rerun()  # 모달 닫고 login 화면 그대로
    
    with col2:
        if st.button("예, 시작", type="primary", use_container_width=True, key="newuser_confirm"):
            logger.info(f"[CLICK] 신규 사용자 등록 확인 → {user_data['name']} ({user_data['student_id']})")
            # 신규 사용자 등록 (파일 저장)
            register_new_user(user_data)
            
            # session_state 설정
            st.session_state.student_id = user_data["student_id"]
            st.session_state.name = user_data["name"]
            st.session_state.user_data = user_data
            st.session_state.current_part_idx = 0
            st.session_state.part_answers = {}
            st.session_state.viewing_history = False
            st.session_state.show_all_history = False
            
            # quiz로 이동
            st.session_state.page = "quiz"
            st.session_state.scroll_to_top = True
            st.rerun()

# 이전 기록 화면
def render_history():
    """이전 테스트 기록 페이지 — 카드 + 새로 테스트하기 + 로그아웃"""
    user_name = st.session_state.get("name", "사용자")
    tests_count = len(st.session_state.get("user_data", {}).get("tests", []))
    logger.info(f"[PAGE] 기록 화면 진입 — {user_name}님 (기록 {tests_count}개)")
    
    if st.session_state.get("scroll_to_top", False):
        scroll_to_top()
        st.session_state.scroll_to_top = False

    user_name = st.session_state.get("name", "사용자")
    user_data = st.session_state.get("user_data", {})
    tests = user_data.get("tests", [])
    
    # 상단 — 제목 + 로그아웃 버튼
    col_title, col_logout = st.columns([4, 1])
    with col_title:
        st.title(f"📋 {user_name}님의 테스트 기록")
    with col_logout:
        st.markdown("")
        if st.button("로그아웃", use_container_width=True):
            confirm_logout()  # 모달 다이얼로그 호출
    
    st.caption(f"총 {len(tests)}회의 테스트 기록이 있습니다.")
    
    st.markdown("---")
    
    if st.button("✨ 새로 테스트하기", type="primary", use_container_width=True):
        logger.info("[CLICK] 새로 테스트하기 → 퀴즈 시작")
        st.session_state.current_part_idx = 0
        st.session_state.part_answers = {}
        st.session_state.viewing_history = False
        st.session_state.page = "quiz"
        st.session_state.scroll_to_top = True
        st.rerun()
    
    st.markdown("---")
    
    results_data = load_results()
    
    sorted_tests = sorted(
        enumerate(tests),
        key=lambda x: x[1].get("timestamp", ""),
        reverse=True,
    )
    
    show_all = st.session_state.get("show_all_history", False)
    display_tests = sorted_tests if show_all else sorted_tests[:3]
    
    st.markdown("### 이전 기록")
    
    for original_idx, test in display_tests:
        type_code = test.get("type", "?")
        type_name = results_data["types"].get(type_code, {}).get("name", "")
        timestamp = test.get("timestamp", "")
        
        try:
            dt = datetime.fromisoformat(timestamp)
            date_str = dt.strftime("%Y/%m/%d")
        except (ValueError, TypeError):
            date_str = timestamp
        
        nth = original_idx + 1
        
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**{type_code}** — _{type_name}_")
                st.caption(f"📅 {date_str} · {nth}번째 테스트")
            
            with col2:
                if st.button(
                    "보기 →",
                    key=f"view_test_{original_idx}",
                    use_container_width=True,
                ):
                    st.session_state.selected_test_idx = original_idx
                    st.session_state.viewing_history = True
                    st.session_state.page = "result"
                    st.session_state.scroll_to_top = True
                    st.rerun()
    
    if not show_all and len(sorted_tests) > 3:
        st.markdown("")
        if st.button(
            f"📂 더 보기 ({len(sorted_tests) - 3}개)",
            use_container_width=True,
        ):
            st.session_state.show_all_history = True
            st.rerun()
    elif show_all and len(sorted_tests) > 3:
        st.markdown("")
        if st.button("📁 접기 (최근 3개만)", use_container_width=True):
            st.session_state.show_all_history = False
            st.rerun()

# 테스트 화면
def render_quiz():
    """
    테스트 화면 — 3개 Part로 나뉜 7문항 단위 진행
    Part 1: 관심 영역 (D_V축 7문항)
    Part 2: 문제 접근 방식 (A_P축 7문항)
    Part 3: 선호하는 환경 (R_S축 7문항)
    """
    part_idx = st.session_state.get("current_part_idx", 0)
    axis_names = {0: "D_V (관심 영역)", 1: "A_P (문제 접근)", 2: "R_S (선호 환경)"}
    axis_label = axis_names.get(part_idx, "완료")
    logger.info(f"[PAGE] 퀴즈 화면 진입 — Part {part_idx + 1}/3 ({axis_label})")

    data = load_questions()
    questions = data["questions"]
    
    axis_groups = {
        "D_V": [q for q in questions if q["axis"] == "D_V"],
        "A_P": [q for q in questions if q["axis"] == "A_P"],
        "R_S": [q for q in questions if q["axis"] == "R_S"],
    }
    
    parts = [
        {
            "axis": "D_V",
            "title": "Part 1. 관심 영역",
            "subtitle": "어떤 분야에 더 끌리는지 알아봅니다.",
        },
        {
            "axis": "A_P",
            "title": "Part 2. 문제 접근 방식",
            "subtitle": "문제를 마주했을 때의 사고 흐름을 알아봅니다.",
        },
        {
            "axis": "R_S",
            "title": "Part 3. 선호하는 환경",
            "subtitle": "어떤 환경에서 가장 활발하게 움직이는지 알아봅니다.",
        },
    ]
    
    if part_idx >= len(parts):
        ordered_answers = [
            st.session_state.part_answers[q["id"]]
            for q in questions
        ]
        
        result = build_test_result(questions, ordered_answers)
        st.session_state.test_result = result
        
        add_test_record(st.session_state.student_id, result)
        
        st.session_state.user_data = load_user(st.session_state.student_id)
        
        st.session_state.viewing_history = False
        
        st.session_state.scroll_to_top = True
        st.session_state.page = "result"
        st.rerun()
        return
    
    current_part = parts[part_idx]
    current_questions = axis_groups[current_part["axis"]]

    if st.session_state.get("scroll_to_top", False):
        scroll_to_top()
        st.session_state.scroll_to_top = False
    
    # Part 1에서만 — 상단 좌측에 "이전" 버튼
    if part_idx == 0:
        has_history = bool(st.session_state.get("user_data", {}).get("tests"))
        col_back, _ = st.columns([2, 5])
        with col_back:
            if has_history:
                # 기존 사용자 — 기록 페이지로 돌아가기
                if st.button("← 이전", key="quiz_back_top", use_container_width=False):
                    st.session_state.current_part_idx = 0
                    st.session_state.part_answers = {}
                    st.session_state.page = "history"
                    st.session_state.scroll_to_top = True
                    st.rerun()
            else:
                # 신규 사용자 — 등록 취소하고 종료
                if st.button("종료", key="quiz_back_top", use_container_width=False):
                    student_id = st.session_state.get("student_id")
                    if student_id:
                        delete_user(student_id)
                    
                    # session_state 초기화
                    for key in [
                        "student_id", "name", "user_data",
                        "current_part_idx", "part_answers",
                        "viewing_history", "show_all_history",
                        "selected_test_idx", "test_result",
                    ]:
                        if key in st.session_state:
                            del st.session_state[key]
                    
                    st.session_state.page = "home"
                    st.session_state.scroll_to_top = True
                    st.rerun()
        st.markdown("")
    
    st.progress(
        part_idx / len(parts),
        text=f"진행률: Part {part_idx + 1} / {len(parts)}",
    )
    
    st.markdown(f"### {current_part['title']}")
    st.markdown(f"_{current_part['subtitle']}_")
    
    st.markdown("---")
    
    if "part_answers" not in st.session_state:
        st.session_state.part_answers = {}
    
    for q in current_questions:
        st.markdown(f"**Q{q['id']}.** {q['text']}")
        
        previous_answer = st.session_state.part_answers.get(q["id"])
        option_texts = [opt["text"] for opt in q["options"]]
        
        selected = st.radio(
            label=f"문항 {q['id']}",
            options=range(len(option_texts)),
            format_func=lambda i: option_texts[i],
            key=f"radio_q{q['id']}",
            index=previous_answer if previous_answer is not None else None,
            label_visibility="collapsed",
        )
        
        if selected is not None:
            st.session_state.part_answers[q["id"]] = selected
        
        st.markdown("")
    
    st.markdown("---")
    
    answered_in_this_part = sum(
        1 for q in current_questions
        if q["id"] in st.session_state.part_answers
    )
    total_in_this_part = len(current_questions)
    all_answered = answered_in_this_part == total_in_this_part
    
    st.caption(f"해당 Part 답변 완료 현황: {answered_in_this_part} / {total_in_this_part}")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        if part_idx > 0:
            if st.button("← 이전 Part", use_container_width=True):
                logger.info(f"[CLICK] Part {part_idx + 1} → 이전 Part로 돌아감")
                st.session_state.current_part_idx -= 1
                st.session_state.scroll_to_top = True
                st.rerun()
    
    with col2:
        next_label = "결과 보기 →" if part_idx == len(parts) - 1 else "다음 Part →"
        
        if all_answered:
            if st.button(next_label, type="primary", use_container_width=True):
                logger.info(f"[CLICK] Part {part_idx + 1} 완료 → 다음 단계로 이동")
                st.session_state.current_part_idx += 1
                st.session_state.scroll_to_top = True
                st.rerun()
        else:
            st.button(
                next_label,
                disabled=True,
                use_container_width=True,
                help=f"아직 {total_in_this_part - answered_in_this_part}개 문항이 남았습니다.",
            )
            st.warning(
                f"⚠️ 모든 문항({total_in_this_part}개)에 답해주세요. "
                f"현재 {answered_in_this_part}개 답변됨."
            )

def render_cache_demo():
    """캐싱 시연 섹션 — 4개 함수의 캐싱 ON/OFF 실행 시간 비교"""

    # 연결 문구
    st.markdown("바로 **'캐싱'** 기술이에요! 어떻게 쓰였는지 알아볼까요?")
    
    st.markdown("")
    
    # 캐시 소개 + Streamlit 특징
    st.markdown("##### 캐시란?")
    st.markdown(
        "자주 사용하는 데이터나 값을 미리 복사해놓는 임시 장소를 뜻해요."
    )
    
    st.markdown("")
    
    st.markdown(
        "Streamlit에서는 사용자 입력마다 전체 스크립트를 재실행하므로 "
        "이러한 간단한 앱에서도 한 사이클 당 수십번 이상의 rerun이 발생해요. "
        "따라서 캐싱을 활용해 시간이 오래 걸리는 함수 호출 결과를 저장하고 재사용하여 "
        "앱의 성능을 향상시킬 수 있어요. "
        "아래 버튼을 눌러 캐싱의 효과를 직접 측정해보세요!"
    )
    
    st.markdown("")
    
    # 측정 대상 함수 4개
    user_type = st.session_state.get("test_result", {}).get("type") or "DPS"
    courses_data = load_courses()
    
    targets = [
        ("load_questions()", "JSON 파일 로딩 (21문항)", load_questions, ()),
        ("load_results()", "JSON 파일 로딩 (8유형)", load_results, ()),
        ("load_courses()", "JSON 파일 로딩 (43과목)", load_courses, ()),
        ("build_roadmap_figure()", "Plotly 차트 생성 (이수체계도)", build_roadmap_figure, (courses_data, user_type)),
    ]
    
    if st.button("⚡ 측정 시작", type="primary", use_container_width=True, key="cache_demo_run"):
        logger.info("[CACHE] 측정 시작 — 4개 함수 캐싱 ON/OFF 비교")
        results = []
        for name, desc, func, args in targets:
            func.clear()
            start = time.perf_counter()
            func(*args)
            off_ms = (time.perf_counter() - start) * 1000
            
            start = time.perf_counter()
            func(*args)
            on_ms = (time.perf_counter() - start) * 1000
            
            speedup = off_ms / max(on_ms, 0.0001)
            results.append((name, desc, off_ms, on_ms, speedup))
        
        st.session_state["cache_demo_results"] = results
        st.rerun()
    
    # 결과 표시 (측정 후에만)
    results = st.session_state.get("cache_demo_results")
    if results:
        st.markdown("")
        st.markdown("##### 측정 결과")
        
        table_lines = [
            "| 함수 | 설명 | 캐싱 OFF | 캐싱 ON | 속도 향상 |",
            "|---|---|:---:|:---:|---:|",
        ]
        for name, desc, off_ms, on_ms, speedup in results:
            table_lines.append(
                f"| `{name}` | {desc} | {off_ms:.4f} ms | {on_ms:.4f} ms | **{speedup:.0f}배** |"
            )
        st.markdown("\n".join(table_lines))
        
        # 누적 효과 — 슬라이더로 횟수 조절
        st.markdown("")
        st.markdown("##### 누적 효과")
        st.markdown(
            "아래의 슬라이더를 조정하여 누적 횟수 변화에 따른 성능의 변화를 직접 확인해보세요!"
        )
        
        rerun_count = st.slider(
            "rerun 횟수",
            min_value=1,
            max_value=200,
            value=50,
            step=10,
            key="cache_demo_rerun_count",
        )
        
        total_off = sum(off_ms for _, _, off_ms, _, _ in results) * rerun_count
        total_on = sum(on_ms for _, _, _, on_ms, _ in results) * rerun_count
        saved = total_off - total_on
        
        col1, col2, col3 = st.columns(3)
        col1.metric("캐싱 OFF (누적)", f"{total_off:.2f} ms")
        col2.metric("캐싱 ON (누적)", f"{total_on:.2f} ms")
        col3.metric("절약 시간", f"{saved:.2f} ms", delta=f"-{saved:.0f} ms", delta_color="inverse")

def clear_cache_demo():
    """결과 페이지 떠날 때 캐싱 시연 결과 초기화"""
    if "cache_demo_results" in st.session_state:
        del st.session_state["cache_demo_results"]

# 결과 화면
def render_result():
    """결과 화면 렌더링 + viewing_history에 따라 다른 버튼 제공"""
    viewing_history = st.session_state.get("viewing_history", False)
    
    if viewing_history:
        idx = st.session_state.get("selected_test_idx", 0)
        tests = st.session_state.get("user_data", {}).get("tests", [])
        type_code = tests[idx].get("type", "?") if 0 <= idx < len(tests) else "?"
        logger.info(f"[PAGE] 결과 화면 진입 (과거 기록 #{idx+1}) — {type_code} 유형")
    else:
        type_code = st.session_state.get("test_result", {}).get("type", "?")
        logger.info(f"[PAGE] 결과 화면 진입 (신규 테스트) — {type_code} 유형")
    
    if st.session_state.get("scroll_to_top", False):
        scroll_to_top()
        st.session_state.scroll_to_top = False

    # 캐싱 시연 결과로 스크롤
    if st.session_state.get("scroll_to_cache_demo", False):
        scroll_to_cache_demo()
        st.session_state.scroll_to_cache_demo = False
    
    if viewing_history:
        idx = st.session_state.get("selected_test_idx", 0)
        tests = st.session_state.get("user_data", {}).get("tests", [])
        
        if not tests or idx >= len(tests):
            st.error("선택한 테스트 기록을 찾을 수 없습니다.")
            if st.button("← 이전 기록으로"):
                st.session_state.page = "history"
                st.rerun()
            return
        
        result = tests[idx]
        
        try:
            dt = datetime.fromisoformat(result.get("timestamp", ""))
            date_str = dt.strftime("%Y년 %m월 %d일 %H:%M")
        except (ValueError, TypeError):
            date_str = ""
        
        # 상단 — 좌측 이전 버튼 + 우측 날짜 표시
        col_back, col_date = st.columns([2, 5])
        with col_back:
            if st.button("← 이전", key="result_back_top", use_container_width=False):
                clear_cache_demo()
                st.session_state.viewing_history = False
                st.session_state.page = "history"
                st.session_state.scroll_to_top = True
                st.rerun()
        with col_date:
            if date_str:
                # 버튼 높이에 맞추기 위한 빈 줄
                st.markdown("")
                # 우측 정렬을 위해 markdown + HTML
                st.markdown(
                    f"<div style='text-align: right; color: gray; font-size: 0.875em;'>"
                    f"📅 {date_str}에 진행한 테스트 결과"
                    f"</div>",
                    unsafe_allow_html=True,
                )
        
        st.markdown("")
        
        st.markdown("")
    else:
        result = st.session_state.get("test_result", {})
    
    if not result:
        st.error("테스트 결과가 없습니다. 처음부터 다시 시작해주세요.")
        if st.button("처음으로"):
            st.session_state.page = "home"
            st.rerun()
        return
    
    results_data = load_results()
    user_name = st.session_state.get("name", "사용자")
    
    render_result_page(result, results_data, user_name)
    
    st.markdown("---")
    
    if viewing_history:
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("결과 목록으로 ⏎", key="result_back_bottom", use_container_width=True):
                clear_cache_demo()
                st.session_state.viewing_history = False
                st.session_state.page = "history"
                st.session_state.scroll_to_top = True
                st.rerun()
        
        with col2:
            if st.button("해당 결과 삭제", key="result_delete", type="primary", use_container_width=True):
                idx = st.session_state.get("selected_test_idx", 0)
                tests = st.session_state.get("user_data", {}).get("tests", [])
                if 0 <= idx < len(tests):
                    test = tests[idx]
                    type_code = test.get("type", "?")
                    results_data = load_results()
                    type_name = results_data["types"].get(type_code, {}).get("name", "")
                    confirm_delete_test(idx, type_code, type_name)
    else:
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("다시 테스트하기 ⏎", use_container_width=True):
                clear_cache_demo()
                st.session_state.current_part_idx = 0
                st.session_state.part_answers = {}
                st.session_state.page = "quiz"
                st.session_state.scroll_to_top = True
                st.rerun()
        
        with col2:
            if st.button("결과 목록 보기", use_container_width=True):
                clear_cache_demo()
                st.session_state.page = "history"
                st.session_state.scroll_to_top = True
                st.rerun()
    
    # 캐싱 시연
    st.markdown("---")
    
    st.markdown(
        "<div style='line-height: 1.6;'>"
        "💡 Career Compass에서는 정보융합학부 선배가 여러분에게 쾌적한 테스트 환경을 제공하기 위해 노력했어요.<br>"
        "<span style='display: inline-block; width: 1.55em;'></span>"
        "어떤 기술이 숨어있는지 아래에서 직접 확인해보세요!"
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown("")

    expander_open = bool(st.session_state.get("cache_demo_results"))
    
    with st.expander("직접 확인해보기", expanded=expander_open):
        render_cache_demo()

# 라우팅
def main():
    if "page" not in st.session_state:
        st.session_state.page = "home"
    
    if st.session_state.page == "home":
        render_submitter_info()
        render_home()
    elif st.session_state.page == "login":
        render_login()
    elif st.session_state.page == "history":
        render_history()
    elif st.session_state.page == "quiz":
        render_quiz()
    elif st.session_state.page == "result":
        render_result()

if __name__ == "__main__":
    main()