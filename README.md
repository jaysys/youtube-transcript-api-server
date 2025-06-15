# YouTube Transcript API Server

YouTube 동영상의 자막을 추출하는 FastAPI 기반 서버입니다.

## 기능

- YouTube URL 또는 Video ID로 자막 추출
- 다양한 언어 지원 (한국어, 영어 등)
- JSON 및 텍스트 형식 출력
- 사용 가능한 자막 목록 조회
- Docker Compose를 통한 간편한 배포

## 환경 설정

### .env 파일 설정

프로젝트 루트에 `.env` 파일을 생성하여 서버 설정을 변경할 수 있습니다:

```bash
# 서버 포트 설정 (기본값: 8888)
APP_PORT=8888
```

다른 포트를 사용하려면 `.env` 파일에서 APP_PORT 값을 변경하세요:

```bash
# 예: 9000번 포트 사용
APP_PORT=9000
```

## 설치 및 실행

### Docker Compose 사용 (권장)

```bash
# 서비스 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 서비스 중지
docker-compose down
```

### 로컬 개발

```bash
# 의존성 설치
pip install -r requirements.txt

# 서버 실행
python app.py
```

## API 사용법

서버가 실행되면 기본적으로 `http://localhost:8888`에서 접근할 수 있습니다.
(포트는 `.env` 파일의 PORT 설정에 따라 달라집니다)

### 1. 자막 추출 (POST)

```bash
curl -X POST "http://localhost:8888/transcript" \
  -H "Content-Type: application/json" \
  -d '{
    "url_or_id": "https://www.youtube.com/watch?v=VIDEO_ID",
    "languages": ["ko", "en"],
    "format": "json",
    "preserve_formatting": false
  }'
```

### 2. 자막 추출 (GET)

```bash
curl "http://localhost:8888/transcript/VIDEO_ID?languages=ko,en&format=json"
```

### 3. 사용 가능한 자막 목록 조회

```bash
curl "http://localhost:8888/list/VIDEO_ID"
```

### 4. API 문서

브라우저에서 `http://localhost:8888/docs`를 방문하면 Swagger UI를 통해 API 문서를 확인할 수 있습니다.

## 요청 파라미터

### TranscriptRequest (POST)

- `url_or_id` (string, 필수): YouTube URL 또는 Video ID
- `languages` (array, 선택): 언어 코드 배열 (기본값: ["ko", "en"])
- `format` (string, 선택): 출력 형식 "json" 또는 "text" (기본값: "json")
- `preserve_formatting` (boolean, 선택): HTML 포맷팅 유지 여부 (기본값: false)

### GET 파라미터

- `languages` (string): 쉼표로 구분된 언어 코드 (예: "ko,en")
- `format` (string): 출력 형식 "json" 또는 "text"
- `preserve_formatting` (boolean): HTML 포맷팅 유지 여부

## 응답 형식

```json
{
  "video_id": "VIDEO_ID",
  "language": "Korean",
  "language_code": "ko",
  "is_generated": false,
  "transcript": "자막 내용..."
}
```

## 지원하는 URL 형식

- `https://www.youtube.com/watch?v=VIDEO_ID`
- `https://youtu.be/VIDEO_ID`
- `https://www.youtube.com/embed/VIDEO_ID`
- `VIDEO_ID` (직접 입력)

## 환경 변수

다음 환경 변수들을 `.env` 파일에서 설정할 수 있습니다:

- `PORT`: 서버 포트 (기본값: 8888)
- `HOST`: 서버 호스트 (기본값: 0.0.0.0)
- `DEBUG`: 개발 모드 활성화 (기본값: false)
  - `true`로 설정하면 코드 변경 시 자동 재시작됩니다

## 주의사항

- YouTube의 정책에 따라 일부 동영상의 자막을 가져올 수 없을 수 있습니다.
- 자막이 없는 동영상의 경우 오류가 발생합니다.
- 과도한 요청 시 YouTube에서 IP를 차단할 수 있습니다.

## 라이선스

MIT License
