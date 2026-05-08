"""
modules/result.py
결과 화면 렌더링 — 유형 코드/요약, 레이더 차트, 상세 설명, 위험 요소, 추천 직무
"""

import streamlit as st
from modules.data_loader import load_courses
from modules.roadmap import render_roadmap

def render_type_header(type_code: str, type_info: dict, user_name: str):
    """1. 유형 코드 + 한줄 요약 + 사용자 인사"""
    st.markdown(f"## {user_name}님의 유형은")
    st.markdown(f"# `{type_code}` 🧑🏻‍💻")
    st.markdown(f"### : _{type_info['name']}_")

def render_axis_bar(axis_name: str, left_label: str, right_label: str,
                    left_pct: int, right_pct: int):
    """축별 가로 바 한 줄 — 좌측 라벨/% + 가운데 축이름 + 우측 라벨/% + 양분 막대"""
    bar_color = "#FF4B4B"
    bg_color = "#E8E8E8"
    
    # 우세한 쪽을 빨강으로 강조
    left_dominant = left_pct >= right_pct
    left_bar = bar_color if left_dominant else bg_color
    right_bar = bg_color if left_dominant else bar_color
    left_text = bar_color if left_dominant else "rgba(49, 51, 63, 0.5)"
    right_text = "rgba(49, 51, 63, 0.5)" if left_dominant else bar_color
    
    st.markdown(
        f"""
        <div style='margin: 1.5rem 0;'>
            <div style='display: flex; justify-content: space-between; 
                        align-items: baseline; margin-bottom: 0.4rem;'>
                <span style='font-size: 0.9rem; color: rgba(49, 51, 63, 0.7);'>
                    {left_label}
                </span>
                <span style='font-size: 1rem; font-weight: 600;'>
                    {axis_name}
                </span>
                <span style='font-size: 0.9rem; color: rgba(49, 51, 63, 0.7);'>
                    {right_label}
                </span>
            </div>
            <div style='display: flex; align-items: center; gap: 0.6rem;'>
                <span style='font-size: 0.9rem; font-weight: 600; 
                             color: {left_text}; min-width: 2.5rem;'>
                    {left_pct}%
                </span>
                <div style='flex: 1; display: flex; height: 14px; 
                            border-radius: 7px; overflow: hidden;'>
                    <div style='width: {left_pct}%; background: {left_bar};'></div>
                    <div style='width: {right_pct}%; background: {right_bar};'></div>
                </div>
                <span style='font-size: 0.9rem; font-weight: 600;
                             color: {right_text}; min-width: 2.5rem; text-align: right;'>
                    {right_pct}%
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_bar_chart(scores: dict):
    """3축 가로 바 차트 — 양극 비교를 직관적으로 표시"""
    st.markdown("### 축별 점수")
    
    render_axis_bar(
        axis_name="관심 영역",
        left_label="D (데이터사이언스)", right_label="V (비주얼테크놀로지)",
        left_pct=scores["D"], right_pct=scores["V"],
    )
    
    render_axis_bar(
        axis_name="문제 접근",
        left_label="A (원리·이론 탐구)", right_label="P (실험·구현 중심)",
        left_pct=scores["A"], right_pct=scores["P"],
    )
    
    render_axis_bar(
        axis_name="선호 환경",
        left_label="R (연구 환경)", right_label="S (서비스 환경)",
        left_pct=scores["R"], right_pct=scores["S"],
    )

def render_description(type_info: dict):
    """3. 상세 설명"""
    st.markdown("### 상세 설명")
    st.markdown(type_info["description"])

def render_risks(type_info: dict):
    """4. 위험 요소 / 약점"""
    st.markdown("### ⚠️ 빠지기 쉬운 함정")
    
    for i, risk in enumerate(type_info["risks"], 1):
        st.warning(f"**{i}.** {risk}")

def render_jobs(type_info: dict):
    """6. 추천 직무"""
    st.markdown("### 💼 추천 직무")
    st.caption("해당 유형에 어울리는 직무 4가지를 소개합니다.")
    
    for job in type_info["jobs"]:
        with st.container():
            st.markdown(f"**✦ {job['name']}**")
            st.caption(job["description"])
            st.markdown("")

def render_result_page(test_result: dict, results_data: dict, user_name: str):
    """
    결과 화면 전체 렌더링.
    
    Args:
        test_result: {"type": "DPS", "scores": {"D": 86, ...}, ...}
        results_data: load_results()로 받은 전체 8유형 데이터
        user_name: 사용자 이름
    """

    type_code = test_result["type"]
    type_info = results_data["types"][type_code]
    scores = test_result["scores"]
    
    # 1. 유형 코드 + 한줄 요약
    render_type_header(type_code, type_info, user_name)
    
    st.markdown("---")
    
    # 2. 축별 점수 가로 바 차트
    render_bar_chart(scores)
    
    st.markdown("---")
    
    # 3. 상세 설명
    render_description(type_info)
    
    st.markdown("---")
    
    # 4. 위험 요소
    render_risks(type_info)
    
    st.markdown("---")
    
    # 5. 이수체계도 맞춤 뷰
    courses_data = load_courses()
    render_roadmap(courses_data, type_code)
    
    st.markdown("---")
    
    # 6. 추천 직무
    render_jobs(type_info)