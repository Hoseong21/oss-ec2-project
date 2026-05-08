"""
modules/data_loader.py
JSON 데이터 파일 로더 — Streamlit 캐싱 활용

캐싱 이유:
- JSON 파일은 매번 디스크 I/O가 발생하므로 메모리 캐시로 성능 향상
- 21문항/8유형/43과목 데이터는 앱 실행 중 변하지 않으므로 캐싱이 안전
- 사용자가 테스트 진행 중 매 클릭마다 파일을 다시 읽으면 응답 지연 발생
"""

import json
from pathlib import Path

import streamlit as st

# 데이터 파일 경로
DATA_DIR = Path("data")

@st.cache_data
def load_questions() -> dict:
    """
    21문항 + 축 매핑 로드.
    
    Returns:
        {
            "meta": {...},
            "questions": [{"id": 1, "axis": "D_V", "text": "...", "options": [...]}, ...]
        }
    """
    file_path = DATA_DIR / "questions.json"
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

@st.cache_data
def load_results() -> dict:
    """
    8유형 콘텐츠 로드 (한줄 요약, 상세 설명, 위험 요소, 추천 직무).
    
    Returns:
        {
            "meta": {...},
            "types": {"DPS": {...}, "DAR": {...}, ...}
        }
    """
    file_path = DATA_DIR / "results.json"
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

@st.cache_data
def load_courses() -> dict:
    """
    2026 이수체계도 + 8유형별 추천 매핑 로드.
    
    Returns:
        {
            "meta": {...},
            "courses": [...],            # 43과목
            "type_recommendations": {...} # 8유형별 추천
        }
    """
    file_path = DATA_DIR / "courses.json"
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)