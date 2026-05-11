# 실습 3 - EC2 배포 과제

## 기본 정보

| 항목 | 내용 |
|---|---|
| 학번 | 2021603038 |
| 이름 | 송호성 |
| 소속 | 광운대학교 수학과 (정보융합학부 복수전공) |

---

## 과제 소개

정보융합학부 학생을 위한 진로 성향 테스트 Streamlit 앱입니다.  
21문항의 2지선다 테스트를 통해 학생의 진로 성향을 진단하고, 추천 교과목을 제공합니다.  
AWS Learner Lab의 EC2 환경에서 Streamlit 앱을 배포하고 외부 접속을 확인합니다.

---

## 실행 방법

### 요구 사항
- Python 3.9+
- Streamlit

### 설치 및 실행

```bash
# 저장소 클론
git clone https://github.com/Hoseong21/oss-ec2-project.git
cd oss-ec2-project

# 가상환경 생성 및 활성화 (권장)
python -m venv .venv
source .venv/bin/activate  # macOS/Linux

# 의존성 설치
pip install -r requirements.txt

# Streamlit 앱 실행
streamlit run app.py