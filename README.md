# GEO Audit Tool

**Generative Engine Optimization(생성 엔진 최적화) 감사 도구**

URL을 입력하면 해당 사이트가 GPT, Gemini, Claude 등 AI 엔진에 얼마나 잘 최적화되어 있는지 즉시 분석합니다.

## 분석 항목

| 항목 | 배점 | 설명 |
|------|------|------|
| 기본 SEO 태그 | 20점 | Title, Meta Description, Canonical 등 10종 × 2점 |
| `robots.txt` AI 봇 | 10점 | GPTBot, Gemini, Claude 등 10개 봇의 허용/차단 |
| JSON-LD 구조화 데이터 | 15점 | 필수(Product+FAQPage 8점) + 보조(BreadcrumbList/Organization 7점) |
| `/llms.txt` | 5점 | AI 모델을 위한 사이트 지침 파일 존재 여부 |
| FAQ 섹션 | 15점 | FAQPage 스키마(8점) + HTML FAQ 섹션(7점) |
| 서머리 박스 | 5점 | 요약/핵심/TL;DR 영역 존재 여부 |
| Heading 구조 | 5점 | H1 고유성(2점) + H2 복수(2점) + 논리적 순서(1점) |
| 통계 데이터 | 5점 | 본문에 숫자·수치 데이터 존재 여부 |
| 리뷰 SSR | 10점 | #reviews_container 서버사이드 렌더링 존재 여부 |
| SSR/CSR 비중 | 10점 | SSR 글자수 ÷ CSR 글자수 비율 (≥80%: 10점) |

## 기술 스택

- **Backend**: Python FastAPI + uvicorn
- **Frontend**: HTML + Tailwind CSS (CDN)
- **HTTP 클라이언트**: httpx (비동기)
- **HTML 파싱**: BeautifulSoup4
- **브라우저 엔진**: Playwright (CSR 분석용)

## AI 모델 사용 가이드

| 용도 | 모델 | 모델 ID |
|------|------|---------|
| 개발 (코드 작성/리팩토링/디버깅) | Claude Opus | `claude-opus-4-6` |
| 운영 (코드 리뷰/모니터링/경량 작업) | Claude Sonnet | `claude-sonnet-4-6` |

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
