"""
modules/roadmap.py
이수체계도 시각화 — Plotly 기반

본인 유형의 추천 과목을 하이라이트하여 보여줌.
"""

import streamlit as st
import plotly.graph_objects as go

# 학기 순서 (X축 좌표)
SEMESTERS = ["1-1", "1-2", "2-1", "2-2", "3-1", "3-2", "4-1", "4-2"]

# 카테고리 (Y축 좌표)
CATEGORY_Y = {
    "VT": 3,
    "foundational": 1.5,
    "DS": 0,
}

# 카테고리 라벨 (사용자에게 친숙한 풀어쓰기)
CATEGORY_LABELS = {
    "VT": "비주얼테크놀로지",
    "foundational": "공통/기초",
    "DS": "데이터사이언스",
}

# 같은 셀(학기 + 카테고리) 내에서 위→아래 표시 순서.
# foundational 과목 중 VT 친화 과목이 위쪽, DS 친화 과목이 아래쪽에 오도록 정렬.
CELL_ORDER = {
    ("1-1", "foundational"): [
        "프로그래밍기초",
        "인공지능과컴퓨팅사고",
        "대학수학및연습1",
    ],
    ("1-2", "foundational"): [
        "고급C프로그래밍",
        "창의설계입문",
        "이산수학",
        "대학수학및연습2",
    ],
    ("2-1", "foundational"): [
        "오픈소스소프트웨어실습",
        "객체지향프로그래밍",
        "컴퓨터네트워크",
        "AI수학",
    ],
    ("2-2", "foundational"): [
        "모바일프로그래밍",
        "자료구조",
        "선형대수",
    ],
}

def _sort_cell_courses(courses_in_cell: list, semester: str, category: str) -> list:
    """
    셀 내 과목들을 표시 순서대로 정렬.
    CELL_ORDER에 등록된 셀은 그 순서로, 없으면 입력 순서 그대로.
    """
    key = (semester, category)
    if key not in CELL_ORDER:
        return courses_in_cell
    
    order = CELL_ORDER[key]
    name_to_course = {c["name"]: c for c in courses_in_cell}
    
    sorted_courses = []
    for name in order:
        if name in name_to_course:
            sorted_courses.append(name_to_course[name])
    
    # 안전장치: CELL_ORDER에 빠진 과목이 있으면 뒤에 추가
    for course in courses_in_cell:
        if course not in sorted_courses:
            sorted_courses.append(course)
    
    return sorted_courses

def _course_position(course: dict, courses_in_same_cell: list) -> tuple:
    """
    과목의 X, Y 좌표 계산.
    같은 학기·카테고리에 여러 과목이 있으면 Y축으로 살짝씩 분산.
    """
    semester = course["semester"]
    category = course["category"]
    
    x = SEMESTERS.index(semester)
    base_y = CATEGORY_Y[category]
    
    idx = courses_in_same_cell.index(course)
    total = len(courses_in_same_cell)
    
    if total == 1:
        offset = 0
    elif total == 2:
        offset = 0.18 if idx == 0 else -0.18
    elif total == 3:
        offset = 0.4 - (idx / (total - 1)) * 0.8
    elif total == 4:
        offset = 0.55 - (idx / (total - 1)) * 1.1
    elif total == 5:
        offset = 0.75 - (idx / (total - 1)) * 1.5
    else:
        offset = 0.7 - (idx / (total - 1)) * 1.4
    
    y = base_y + offset
    return x, y

def _get_course_priority(course: dict, type_recommendations: dict, user_type: str) -> str:
    """
    과목의 추천 단계를 결정.
    
    Returns:
        "core" | "optional" | "other"
    """
    if user_type is None:
        return "other"
    
    user_recs = type_recommendations.get(user_type, {})
    course_name = course["name"]
    
    if course_name in user_recs.get("core", []):
        return "core"
    if course_name in user_recs.get("optional", []):
        return "optional"
    
    return "other"

@st.cache_data
def build_roadmap_figure(_courses_data: dict, user_type: str = None) -> go.Figure:
    """
    이수체계도 Plotly 차트 생성.
    
    캐싱 이유:
        - 43개 과목 × 셀 그룹화 + 좌표 계산 + Plotly Figure 생성을 매번 반복하지 않기 위함
        - 8유형이 한정되어 있어 같은 유형은 재계산 불필요
        - _courses_data: dict라 해싱 불가, 언더스코어로 캐시 키에서 제외 (user_type만 키)
    
    Args:
        _courses_data: load_courses()로 받은 데이터 (캐시 키에서 제외)
        user_type: 본인 유형 코드 (예: "DPS"). None이면 회색 단색.
    
    Returns:
        Plotly Figure
    """
    courses = _courses_data["courses"]
    type_recommendations = _courses_data.get("type_recommendations", {})
    
    # 셀별 그룹화
    cells = {}
    for course in courses:
        key = (course["semester"], course["category"])
        cells.setdefault(key, []).append(course)
    
    # 셀 내 정렬
    for key, cell_courses in cells.items():
        semester, category = key
        cells[key] = _sort_cell_courses(cell_courses, semester, category)
    
    # 좌표 + 추천 단계 계산
    course_positions = []
    for (semester, category), cell_courses in cells.items():
        for course in cell_courses:
            x, y = _course_position(course, cell_courses)
            priority = _get_course_priority(course, type_recommendations, user_type)
            course_positions.append({
                "course": course,
                "x": x,
                "y": y,
                "priority": priority,
            })
    
    # 추천 단계별 스타일
    priority_styles = {
        "core": {
            "label": "핵심 추천",
            "color": "#FF4B4B",
            "size": 17,
            "line_color": "#CC0000",
            "line_width": 2,
        },
        "optional": {
            "label": "보조 추천",
            "color": "#FFB3B3",
            "size": 15,
            "line_color": "#FF8080",
            "line_width": 1.5,
        },
        "other": {
            "label": "그 외",
            "color": "#D9D9D9",
            "size": 13,
            "line_color": "#BFBFBF",
            "line_width": 1,
        },
    }

    fig = go.Figure()
    
    # 추천 단계별로 trace 추가 (낮은 강조 → 높은 강조 순)
    trace_order = ["other", "optional", "core"]
    
    for priority in trace_order:
        filtered = [cp for cp in course_positions if cp["priority"] == priority]
        if not filtered:
            continue
        
        style = priority_styles[priority]
        
        fig.add_trace(
            go.Scatter(
                x=[cp["x"] for cp in filtered],
                y=[cp["y"] for cp in filtered],
                mode="markers+text",
                marker=dict(
                    size=style["size"],
                    color=style["color"],
                    line=dict(color=style["line_color"], width=style["line_width"]),
                ),
                text=[cp["course"]["name"] for cp in filtered],
                textposition="top center",
                textfont=dict(size=9),
                name=style["label"],
                hovertemplate=(
                    "<b>%{text}</b><br>"
                    + "학기: %{customdata[0]}<br>"
                    + "카테고리: %{customdata[1]}<br>"
                    + "구분: %{customdata[2]}<br>"
                    + "<extra></extra>"
                ),
                customdata=[
                    [
                        cp["course"]["semester"],
                        CATEGORY_LABELS[cp["course"]["category"]],
                        cp["course"]["type"],
                    ]
                    for cp in filtered
                ],
            )
        )
    
    fig.update_layout(
        title="2026 정보융합학부 이수체계도",
        dragmode="pan",
        xaxis=dict(
            title="학기",
            tickmode="array",
            tickvals=list(range(len(SEMESTERS))),
            ticktext=SEMESTERS,
            range=[-0.5, 6.15],
            showgrid=True,
            gridcolor="lightgray",
        ),
        yaxis=dict(
            title="카테고리",
            tickmode="array",
            tickvals=list(CATEGORY_Y.values()),
            ticktext=[CATEGORY_LABELS[k] for k in CATEGORY_Y.keys()],
            range=[-1.0, 4.0],
            showgrid=True,
            gridcolor="lightgray",
        ),
        height=550,
        plot_bgcolor="white",
        showlegend=False,
        margin=dict(t=60, b=60, l=140, r=40),
    )
    
    return fig

def render_roadmap(courses_data: dict, user_type: str = None):
    """이수체계도 렌더링"""
    st.markdown("### ✦ 추천 교과목 (이수체계도)")
    
    if user_type:
        st.caption(
            f"**{user_type}** 유형 기준으로 정보융합학부 2026 이수체계도 위에 추천 과목을 표시했습니다."
        )
    else:
        st.caption("정보융합학부 2026 이수체계도입니다.")
    
    fig = build_roadmap_figure(courses_data, user_type)
    st.plotly_chart(fig, use_container_width=True)
    
    # 범례
    if user_type:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(
                "<span style='color:#FF4B4B; font-size:1.2em;'>●</span> "
                "**핵심 추천** (8과목)",
                unsafe_allow_html=True,
            )
        with col2:
            st.markdown(
                "<span style='color:#FFB3B3; font-size:1.2em;'>●</span> "
                "**보조 추천** (6과목)",
                unsafe_allow_html=True,
            )
        with col3:
            st.markdown(
                "<span style='color:#D9D9D9; font-size:1.2em;'>●</span> "
                "**그 외**",
                unsafe_allow_html=True,
            )

        st.markdown(
            "<small style='color: rgba(49, 51, 63, 0.6);'>"
            "💡 공통/기초의 1·2학년 과목은 앞으로의 전공 학습에 기초가 되므로 전부 수강하는 것을 권장합니다.<br>"
            "<span style='display: inline-block; width: 1.6em;'></span>"
            "각 과목 상세 정보는 "
            "<a href='https://ic.kw.ac.kr/program/guide.php' target='_blank'>"
            "정보융합학부 교과목 소개</a>에서 확인할 수 있습니다."
            "</small>",
            unsafe_allow_html=True,
        )