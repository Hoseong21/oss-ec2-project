"""
modules/quiz.py
퀴즈 기능 — 문항 진행 + 점수 계산 + 유형 판별

채점 방식: 단순 합산 (모든 문항 동일 가중치 1)
- 축당 7문항 × 3축 = 21문항
- 각 축 점수: 0~7점
- 퍼센트 변환: 점수 / 7 × 100
- 유형 결정: 각 축에서 더 높은 쪽 (D vs V, A vs P, R vs S)
"""

import logging

logger = logging.getLogger(__name__)

def calculate_scores(questions: list, answers: list) -> dict:
    """
    사용자 응답을 받아 3축 점수를 계산.
    
    Args:
        questions: questions.json의 "questions" 리스트 (21개)
        answers: 사용자 응답 인덱스 리스트 (예: [0, 1, 0, 1, ...])
                 0이면 첫 번째 옵션, 1이면 두 번째 옵션 선택
    
    Returns:
        {
            "D": 4, "V": 3,
            "A": 5, "P": 2,
            "R": 3, "S": 4
        }
        각 축의 raw 점수 (0~7)
    """
    scores = {"D": 0, "V": 0, "A": 0, "P": 0, "R": 0, "S": 0}
    
    for question, answer_idx in zip(questions, answers):
        # 사용자가 선택한 옵션의 score (예: "D" 또는 "V")
        selected_score = question["options"][answer_idx]["score"]
        scores[selected_score] += 1
    
    return scores

def determine_type(scores: dict) -> str:
    """
    축별 점수로부터 8유형 코드 결정.
    
    Args:
        scores: {"D": 4, "V": 3, "A": 5, "P": 2, "R": 3, "S": 4}
    
    Returns:
        "DAR", "DAS", "DPR", "DPS", "VAR", "VAS", "VPR", "VPS" 중 하나
    
    동률 처리: 7문항(홀수)이라 동률은 발생하지 않음.
              만약 데이터 오류로 동률이 발생하면 첫 번째 축(D, A, R)을 우선.
    """
    domain = "D" if scores["D"] >= scores["V"] else "V"
    thinking = "A" if scores["A"] >= scores["P"] else "P"
    environment = "R" if scores["R"] >= scores["S"] else "S"
    
    return f"{domain}{thinking}{environment}"


def calculate_percentages(scores: dict, questions_per_axis: int = 7) -> dict:
    """
    raw 점수를 퍼센트로 변환 (0~100).
    
    Args:
        scores: {"D": 4, "V": 3, ...}
        questions_per_axis: 축당 문항 수 (기본 7)
    
    Returns:
        {"D": 57, "V": 43, "A": 71, "P": 29, "R": 43, "S": 57}
    """
    return {
        axis: round(score / questions_per_axis * 100)
        for axis, score in scores.items()
    }

def build_test_result(questions: list, answers: list) -> dict:
    """
    테스트 결과를 종합한 dict 생성. 사용자 이력 저장용.
    
    Returns:
        {
            "type": "DPS",
            "scores": {"D": 60, "V": 40, ...},  # 퍼센트
            "raw_scores": {"D": 4, "V": 3, ...}, # raw 점수
            "answers": [0, 1, 0, ...]
        }
    """
    logger.info("[QUIZ] 점수 계산 시작 — 21문항 응답 처리")
    raw_scores = calculate_scores(questions, answers)
    percentages = calculate_percentages(raw_scores)
    user_type = determine_type(raw_scores)
    
    result = {
        "type": user_type,
        "scores": percentages,
        "raw_scores": raw_scores,
        "answers": answers,
    }
    logger.info(f"[QUIZ] 결과 산출 완료 — {result['type']} 유형")
    
    return result