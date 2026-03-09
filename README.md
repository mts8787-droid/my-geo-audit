# GEO Audit Tool

**Generative Engine Optimization(생성 엔진 최적화) 감사 도구**

URL을 입력하면 해당 사이트가 GPT, Gemini, Claude 등 AI 엔진에 얼마나 잘 최적화되어 있는지 즉시 분석합니다.

## 분석 항목

| 항목 | 배점 | 설명 |
|------|------|------|
| `/llms.txt` | 35점 | AI 모델을 위한 사이트 지침 파일 존재 여부 |
| `robots.txt` AI 봇 | 35점 | GPTBot, Gemini, Claude 등 10개 봇의 차단 여부 |
| JSON-LD 구조화 데이터 | 30점 | 스키마 마크업 분석 (Article, Organization 등) |

## 기술 스택

- **Backend**: Python FastAPI + uvicorn
- **Frontend**: HTML + Tailwind CSS (CDN)
- **HTTP 클라이언트**: httpx (비동기)
- **HTML 파싱**: BeautifulSoup4

## 설치 및 실행

### 1. Python 설치

[python.org](https://www.python.org/downloads/) 에서 Python 3.11+ 설치
(설치 시 "Add Python to PATH" 체크 필수)

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

### 3. 서버 실행

```bash
python main.py
```

브라우저에서 http://localhost:8000 접속

## 프로젝트 구조

```
my-geo-project/
├── main.py           # FastAPI 앱 진입점
├── analyzer.py       # GEO 분석 핵심 로직
├── requirements.txt  # Python 의존성
├── static/
│   └── index.html    # Tailwind CSS 프론트엔드
└── README.md
```
