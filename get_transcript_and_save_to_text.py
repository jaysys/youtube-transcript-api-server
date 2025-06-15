import requests
import json
from typing import List, Dict, Any

# 상수 정의
API_BASE_URL = "http://localhost:8888"  # API 서버 주소

VIDEO_ID = "eeh6S6qv-oQ"  # <--- 예시) 추출할 동영상 ID YOUTUBE 검색창에서 보이는 video ID

OUTPUT_FILE = f"transcript_{VIDEO_ID}.txt"  # 저장될 자막 내용 파일명

def get_transcript() -> Dict[str, Any]:
    """API를 호출하여 자막 데이터를 가져옵니다."""
    url = f"{API_BASE_URL}/transcript/{VIDEO_ID}"
    params = {
        "languages": "ko,en",  # 한국어, 영어 우선
        "format": "json",
        "preserve_formatting": False
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # HTTP 오류가 발생하면 예외 발생
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API 요청 중 오류 발생: {e}")
        return None

def extract_text(transcript_data: Dict[str, Any]) -> str:
    """자막 데이터에서 텍스트만 추출합니다."""
    if not transcript_data or 'transcript' not in transcript_data:
        return ""
    
    # 텍스트만 추출하여 리스트로 만듦
    texts = [entry['text'] for entry in transcript_data['transcript']]
    # 리스트를 개행문자로 연결하여 하나의 문자열로 변환
    return '\n'.join(texts)

def save_to_file(text: str, filename: str):
    """텍스트를 파일로 저장합니다."""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"자막이 성공적으로 저장되었습니다: {filename}")
    except IOError as e:
        print(f"파일 저장 중 오류 발생: {e}")

if __name__ == "__main__":
    # 자막 데이터 가져오기
    print(f"동영상 ID {VIDEO_ID}의 자막을 가져오는 중...")
    transcript_data = get_transcript()
    
    if transcript_data:
        # 텍스트 추출
        text_content = extract_text(transcript_data)
        
        if text_content:
            # 파일로 저장
            save_to_file(text_content, OUTPUT_FILE)
        else:
            print("추출할 텍스트가 없습니다.")
    else:
        print("자막을 가져오지 못했습니다.")
