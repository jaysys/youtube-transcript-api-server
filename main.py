from fastapi import FastAPI, HTTPException, Query, Path
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import JSONFormatter, TextFormatter
import re
from typing import Optional, List
import uvicorn
import os
import json
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

app = FastAPI(
    title="YouTube Transcript API",
    description="""
    ## YouTube 동영상 자막 추출 API

    이 API는 YouTube 동영상의 자막/트랜스크립트를 추출하는 서비스를 제공합니다.

    ### 주요 기능
    - YouTube URL 또는 Video ID로 자막 추출
    - 다국어 자막 지원 (한국어, 영어 등)
    - JSON 및 텍스트 형식 출력 지원
    - 사용 가능한 자막 목록 조회
    - 자동 생성 자막 및 수동 생성 자막 구분

    ### 사용 방법
    1. `/transcript` 엔드포인트로 POST 요청하여 자막 추출
    2. `/transcript/{video_id}` 엔드포인트로 GET 요청하여 간편 자막 추출
    3. `/list/{video_id}` 엔드포인트로 사용 가능한 자막 목록 조회

    ### 지원 형식
    - **입력**: YouTube URL (`https://www.youtube.com/watch?v=VIDEO_ID`) 또는 Video ID
    - **출력**: JSON 또는 텍스트 형식
    """,
    version="1.0.0",
    contact={
        "name": "YouTube Transcript API",
        "url": "https://github.com/jianfch/stable-ts",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
)

class TranscriptRequest(BaseModel):
    url_or_id: str = Field(
        ...,
        title="YouTube URL 또는 Video ID",
        description="YouTube 동영상 URL 또는 Video ID",
        example="https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    )
    languages: Optional[List[str]] = Field(
        default=["ko", "en"],
        title="언어 코드 목록",
        description="우선순위에 따른 언어 코드 목록 (ISO 639-1)",
        example=["ko", "en", "ja"]
    )
    format: Optional[str] = Field(
        default="json",
        title="출력 형식",
        description="자막 출력 형식",
        pattern="^(json|text)$",
        example="json"
    )
    preserve_formatting: Optional[bool] = Field(
        default=False,
        title="포맷팅 보존",
        description="HTML 포맷팅 요소 보존 여부 (예: <i>, <b>)",
        example=False
    )

class TranscriptResponse(BaseModel):
    video_id: str = Field(
        ...,
        title="Video ID",
        description="YouTube 동영상 ID",
        example="dQw4w9WgXcQ"
    )
    language: str = Field(
        ...,
        title="언어명",
        description="자막의 언어명",
        example="Korean"
    )
    language_code: str = Field(
        ...,
        title="언어 코드",
        description="자막의 언어 코드 (ISO 639-1)",
        example="ko"
    )
    is_generated: bool = Field(
        ...,
        title="자동 생성 여부",
        description="자막이 자동 생성되었는지 여부",
        example=False
    )
    transcript: str | list = Field(
        ...,
        title="자막 내용",
        description="추출된 자막 내용 (JSON 또는 텍스트 형식)",
        example='[{"text": "안녕하세요", "start": 0.0, "duration": 2.5}]'
    )

class TranscriptInfo(BaseModel):
    language: str = Field(..., title="언어명", example="Korean")
    language_code: str = Field(..., title="언어 코드", example="ko")
    is_generated: bool = Field(..., title="자동 생성 여부", example=False)
    is_translatable: bool = Field(..., title="번역 가능 여부", example=True)
    translation_languages: List[str] = Field(..., title="번역 가능 언어 목록", example=["en", "ja"])

class TranscriptListResponse(BaseModel):
    video_id: str = Field(..., title="Video ID", example="dQw4w9WgXcQ")
    available_transcripts: List[TranscriptInfo] = Field(..., title="사용 가능한 자막 목록")

class ErrorResponse(BaseModel):
    detail: str = Field(..., title="오류 메시지", example="자막을 가져오는데 실패했습니다")

class HealthResponse(BaseModel):
    status: str = Field(..., title="상태", example="healthy")

class RootResponse(BaseModel):
    message: str = Field(..., title="메시지", example="YouTube Transcript API Server")
    version: str = Field(..., title="버전", example="1.0.0")

def extract_video_id(url_or_id: str) -> str:
    """YouTube URL에서 video ID를 추출하거나 ID 그대로 반환"""
    # YouTube URL 패턴들
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
        r'youtube\.com\/watch\?.*v=([^&\n?#]+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)

    # URL이 아닌 경우 그대로 video ID로 간주
    return url_or_id

@app.get("/", response_model=RootResponse, tags=["기본"])
async def root():
    """
    ## API 루트 엔드포인트

    API 서버의 기본 정보를 반환합니다.
    """
    return {"message": "YouTube Transcript API Server", "version": "1.0.0"}

@app.get("/health", response_model=HealthResponse, tags=["기본"])
async def health_check():
    """
    ## 헬스 체크

    API 서버의 상태를 확인합니다.
    """
    return {"status": "healthy"}

@app.post("/transcript",
          response_model=TranscriptResponse,
          responses={
              400: {"model": ErrorResponse, "description": "잘못된 요청"},
              404: {"model": ErrorResponse, "description": "자막을 찾을 수 없음"},
              500: {"model": ErrorResponse, "description": "서버 오류"}
          },
          tags=["자막 추출"],
          summary="자막 추출 (POST)")
async def get_transcript(request: TranscriptRequest):
    """
    ## YouTube 동영상 자막 추출

    YouTube URL 또는 Video ID를 사용하여 동영상의 자막을 추출합니다.

    ### 요청 예시
    ```json
    {
        "url_or_id": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "languages": ["ko", "en"],
        "format": "json",
        "preserve_formatting": false
    }
    ```

    ### 응답 예시
    ```json
    {
        "video_id": "dQw4w9WgXcQ",
        "language": "Korean",
        "language_code": "ko",
        "is_generated": false,
        "transcript": "[{\"text\": \"안녕하세요\", \"start\": 0.0, \"duration\": 2.5}]"
    }
    ```

    ### 지원 언어 코드
    - `ko`: 한국어
    - `en`: 영어
    - `ja`: 일본어
    - `zh`: 중국어
    - `es`: 스페인어
    - `fr`: 프랑스어
    - `de`: 독일어

    ### 출력 형식
    - `json`: JSON 형식 (기본값)
    - `text`: 텍스트 형식
    """
    try:
        # Video ID 추출
        video_id = extract_video_id(request.url_or_id)

        # YouTube Transcript API 인스턴스 생성
        ytt_api = YouTubeTranscriptApi()

        # 자막 가져오기
        fetched_transcript = ytt_api.fetch(
            video_id,
            languages=request.languages,
            preserve_formatting=request.preserve_formatting
        )

        # 포맷에 따라 자막 변환
        if request.format == "text":
            formatter = TextFormatter()
            transcript_text = formatter.format_transcript(fetched_transcript)
        else:  # json
            formatter = JSONFormatter()
            transcript_text = formatter.format_transcript(fetched_transcript)
            transcript_text = json.loads(transcript_text)

        return TranscriptResponse(
            video_id=fetched_transcript.video_id,
            language=fetched_transcript.language,
            language_code=fetched_transcript.language_code,
            is_generated=fetched_transcript.is_generated,
            transcript=transcript_text
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"자막을 가져오는데 실패했습니다: {str(e)}")

@app.get("/transcript/{video_id}",
         response_model=TranscriptResponse,
         responses={
             400: {"model": ErrorResponse, "description": "잘못된 요청"},
             404: {"model": ErrorResponse, "description": "자막을 찾을 수 없음"},
             500: {"model": ErrorResponse, "description": "서버 오류"}
         },
         tags=["자막 추출"],
         summary="자막 추출 (GET)")
async def get_transcript_by_id(
    video_id: str = Path(..., title="Video ID", description="YouTube 동영상 ID", examples=["dQw4w9WgXcQ"]),
    languages: str = Query("ko,en", title="언어 코드", description="쉼표로 구분된 언어 코드 목록", examples=["ko,en"]),
    format: str = Query("json", title="출력 형식", description="자막 출력 형식 (json 또는 text)", pattern="^(json|text)$", examples=["json"]),
    preserve_formatting: bool = Query(False, title="포맷팅 보존", description="HTML 포맷팅 요소 보존 여부", examples=[False])
):
    """
    ## YouTube 동영상 자막 추출 (GET 방식)

    URL 경로와 쿼리 파라미터를 사용하여 간편하게 자막을 추출합니다.

    ### 사용 예시
    ```
    GET /transcript/dQw4w9WgXcQ?languages=ko,en&format=json&preserve_formatting=false
    ```

    ### 파라미터 설명
    - **video_id**: YouTube 동영상 ID (경로 파라미터)
    - **languages**: 쉼표로 구분된 언어 코드 목록 (기본값: "ko,en")
    - **format**: 출력 형식 - "json" 또는 "text" (기본값: "json")
    - **preserve_formatting**: HTML 포맷팅 보존 여부 (기본값: false)
    """
    language_list = [lang.strip() for lang in languages.split(",")]

    request = TranscriptRequest(
        url_or_id=video_id,
        languages=language_list,
        format=format,
        preserve_formatting=preserve_formatting
    )

    return await get_transcript(request)

@app.get("/list/{video_id}",
         response_model=TranscriptListResponse,
         responses={
             400: {"model": ErrorResponse, "description": "잘못된 요청"},
             404: {"model": ErrorResponse, "description": "동영상을 찾을 수 없음"},
             500: {"model": ErrorResponse, "description": "서버 오류"}
         },
         tags=["자막 정보"],
         summary="사용 가능한 자막 목록 조회")
async def list_available_transcripts(
    video_id: str = Path(..., title="Video ID", description="YouTube 동영상 ID", example="dQw4w9WgXcQ")
):
    """
    ## 사용 가능한 자막 목록 조회

    지정된 YouTube 동영상에서 사용 가능한 모든 자막의 정보를 조회합니다.

    ### 사용 예시
    ```
    GET /list/dQw4w9WgXcQ
    ```

    ### 응답 예시
    ```json
    {
        "video_id": "dQw4w9WgXcQ",
        "available_transcripts": [
            {
                "language": "Korean",
                "language_code": "ko",
                "is_generated": false,
                "is_translatable": true,
                "translation_languages": ["en", "ja", "zh"]
            },
            {
                "language": "English",
                "language_code": "en",
                "is_generated": true,
                "is_translatable": true,
                "translation_languages": ["ko", "ja", "zh"]
            }
        ]
    }
    ```

    ### 응답 필드 설명
    - **language**: 자막의 언어명
    - **language_code**: ISO 639-1 언어 코드
    - **is_generated**: 자동 생성 자막 여부 (true: 자동 생성, false: 수동 생성)
    - **is_translatable**: 다른 언어로 번역 가능 여부
    - **translation_languages**: 번역 가능한 언어 코드 목록
    """
    try:
        video_id = extract_video_id(video_id)
        ytt_api = YouTubeTranscriptApi()
        transcript_list = ytt_api.list(video_id)

        transcripts = []
        for transcript in transcript_list:
            transcripts.append({
                "language": transcript.language,
                "language_code": transcript.language_code,
                "is_generated": transcript.is_generated,
                "is_translatable": transcript.is_translatable,
                "translation_languages": transcript.translation_languages
            })

        return {
            "video_id": video_id,
            "available_transcripts": transcripts
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"자막 목록을 가져오는데 실패했습니다: {str(e)}")
