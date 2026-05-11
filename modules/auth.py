"""
modules/auth.py
로그인 기능 — 학번(unique key) + 이름(표시용) + JSON 파일로 이력 관리
"""

import json
import re
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# 사용자 데이터 저장 디렉토리
USERS_DIR = Path("users")

def ensure_users_dir():
    """users/ 디렉토리가 없으면 생성"""
    USERS_DIR.mkdir(exist_ok=True)

def is_valid_student_id(student_id: str) -> tuple[bool, str]:
    """학번 유효성 검사"""
    if not student_id or not student_id.strip():
        return False, "학번을 입력해주세요."
    
    student_id = student_id.strip()
    
    if not student_id.isdigit():
        return False, "학번은 숫자만 입력해주세요."
    
    if len(student_id) != 10:
        return False, "학번은 10자리여야 합니다."
    
    return True, ""

def is_valid_name(name: str) -> tuple[bool, str]:
    """이름 유효성 검사"""
    if not name or not name.strip():
        return False, "이름을 입력해주세요."
    
    name = name.strip()
    
    if len(name) < 2:
        return False, "이름은 2자 이상이어야 합니다."
    
    if len(name) > 10:
        return False, "이름은 10자 이하여야 합니다."
    
    # 한글 또는 영문만 허용
    if not re.match(r"^[a-zA-Z가-힣]+$", name):
        return False, "이름은 한글 또는 영문만 사용 가능합니다."
    
    return True, ""

def get_user_file(student_id: str) -> Path:
    """학번으로 JSON 파일 경로 반환 (이름이 바뀌어도 학번 unique)"""
    return USERS_DIR / f"{student_id}.json"

def user_exists(student_id: str) -> bool:
    """사용자 파일 존재 여부 확인"""
    return get_user_file(student_id).exists()

def load_user(student_id: str) -> dict:
    """
    사용자 데이터 로드. 없으면 빈 구조 반환.
    
    Returns:
        {"student_id": str, "name": str, "tests": [...]}
    """
    user_file = get_user_file(student_id)
    if user_file.exists():
        with open(user_file, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return {"student_id": student_id, "name": "", "tests": []}

def save_user(user_data: dict) -> None:
    """사용자 데이터 저장"""
    ensure_users_dir()
    student_id = user_data["student_id"]
    user_file = get_user_file(student_id)
    with open(user_file, "w", encoding="utf-8") as f:
        json.dump(user_data, f, ensure_ascii=False, indent=2)

def login(student_id: str, name: str) -> tuple[bool, str, dict]:
    """
    로그인 처리.
    신규 사용자는 파일 저장하지 않고 dict만 반환 (사용자 확정 후 register_new_user 호출 필요).
    
    Args:
        student_id: 학번 (unique key)
        name: 이름 (표시용)
    
    Returns:
        (success, message, user_data)
        user_data에 "is_new" 키 추가 — True면 신규(파일 저장 안 됨), False면 기존
    """
    # 유효성 검사 1: 학번
    valid_id, err_id = is_valid_student_id(student_id)
    if not valid_id:
        logger.info(f"[LOGIN] 입력 검증 실패 — {err_id}")
        return False, err_id, {}
    
    # 유효성 검사 2: 이름
    valid_name, err_name = is_valid_name(name)
    if not valid_name:
        logger.info(f"[LOGIN] 입력 검증 실패 — {err_name}")
        return False, err_name, {}
    
    student_id = student_id.strip()
    name = name.strip()
    
    # 사용자 존재 여부에 따라 분기
    if user_exists(student_id):
        user_data = load_user(student_id)
        existing_name = user_data.get("name", "")
        test_count = len(user_data.get("tests", []))
        
        # 같은 학번에 다른 이름 입력 시 — 이름 갱신 (오타 정정 가능)
        if existing_name and existing_name != name:
            user_data["name"] = name
            save_user(user_data)
            message = f"안녕하세요, {name}님! 이전 테스트 기록 {test_count}개 있음. (이름 정보가 갱신되었습니다)"
            logger.info(f"[LOGIN] 로그인 성공 — {name} (기록 {test_count}개, 이름 갱신)")
        else:
            user_data["name"] = name
            save_user(user_data)
            message = f"안녕하세요, {name}님! 이전 테스트 기록 {test_count}개 있음."
            logger.info(f"[LOGIN] 로그인 성공 — {name} (기록 {test_count}개)")
        
        user_data["is_new"] = False
        return True, message, user_data
    else:
        # 신규 사용자 — 파일 저장 보류, dict만 반환
        logger.info(f"[LOGIN] 신규 사용자 식별 — 학번 {student_id}, 이름 {name}")
        user_data = {
            "student_id": student_id,
            "name": name,
            "tests": [],
            "is_new": True,
        }
        return True, "", user_data   # 메시지 비워둠 (모달이 안내 담당)

def add_test_record(student_id: str, test_result: dict) -> None:
    """
    테스트 결과를 사용자 이력에 추가.
    
    Args:
        student_id: 학번
        test_result: {
            "type": "DPS",
            "scores": {"D": 60, "V": 40, ...},
            "answers": [0, 1, 0, ...]
        }
    """
    user_data = load_user(student_id)
    
    # 타임스탬프 자동 추가
    test_result["timestamp"] = datetime.now().isoformat()
    
    user_data["tests"].append(test_result)
    save_user(user_data)

def register_new_user(user_data: dict) -> None:
    """
    신규 사용자 등록 — 사용자가 모달에서 확정한 후 호출.
    파일 저장 + is_new 플래그 제거.
    """
    user_data.pop("is_new", None)
    save_user(user_data)

def delete_user(student_id: str) -> bool:
    """
    사용자 JSON 파일 삭제 — 신규 사용자가 등록 취소 시 호출.
    
    Returns:
        삭제 성공 여부
    """
    user_file = get_user_file(student_id)
    if user_file.exists():
        user_file.unlink()
        return True
    return False

def delete_test_record(student_id: str, test_idx: int) -> bool:
    """
    특정 테스트 기록 삭제.
    
    Args:
        student_id: 학번
        test_idx: 삭제할 테스트의 인덱스 (tests 배열 기준)
    
    Returns:
        삭제 성공 여부
    """
    user_data = load_user(student_id)
    tests = user_data.get("tests", [])
    
    if 0 <= test_idx < len(tests):
        tests.pop(test_idx)
        user_data["tests"] = tests
        save_user(user_data)
        return True
    return False