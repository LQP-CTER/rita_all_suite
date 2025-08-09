import os
import requests
import google.generativeai as genai
from dotenv import load_dotenv
import logging
import json
from django.conf import settings

logger = logging.getLogger(__name__)
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
else:
    logger.warning("Cảnh báo: GOOGLE_API_KEY không được tìm thấy.")

TIKTOK_API_KEY = os.getenv("TIKTOK_API_KEY")
TIKTOK_API_URL = "https://tiktok-video-no-watermark2.p.rapidapi.com/"

def get_tiktok_video_info(video_url: str, username: str) -> dict:
    if not TIKTOK_API_KEY:
        return {"error": "TikTok API key chưa được cấu hình."}

    querystring = {"url": video_url, "hd": "1"}
    headers = {
        "X-RapidAPI-Key": TIKTOK_API_KEY,
        "X-RapidAPI-Host": "tiktok-video-no-watermark2.p.rapidapi.com"
    }
    
    try:
        response = requests.get(TIKTOK_API_URL, headers=headers, params=querystring, timeout=30)
        response.raise_for_status()
        api_data = response.json()

        if api_data.get('code') != 0 or 'data' not in api_data:
            return {"error": api_data.get('msg', 'Lỗi không xác định từ TikTok API')}

        video_data = api_data['data']
        music_url = video_data.get('music')
        transcript = "Không có audio hoặc không thể phiên âm."

        if music_url and GOOGLE_API_KEY:
            user_media_path = os.path.join(settings.MEDIA_ROOT, username)
            os.makedirs(user_media_path, exist_ok=True)
            audio_filename = f"temp_audio_{os.urandom(8).hex()}.mp3"
            audio_filepath = os.path.join(user_media_path, audio_filename)
            try:
                with requests.get(music_url, stream=True, timeout=30) as r:
                    r.raise_for_status()
                    with open(audio_filepath, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                audio_file = genai.upload_file(path=audio_filepath)
                model = genai.GenerativeModel(model_name='gemini-1.5-flash')
                response = model.generate_content(["Phiên âm nội dung file âm thanh sau:", audio_file])
                transcript = response.text
            except Exception as e:
                logger.error(f"Lỗi xử lý audio: {e}")
            finally:
                if os.path.exists(audio_filepath):
                    os.remove(audio_filepath)

        return {
            "video_id": video_data.get('id'),
            "author": video_data.get('author', {}).get('unique_id'),
            "description": video_data.get('title'),
            "cover_url": video_data.get('cover'),
            "download_url": video_data.get('play'),
            "play_count": video_data.get('play_count', 0),
            "likes": video_data.get('digg_count', 0),
            "comments": video_data.get('comment_count', 0),
            "shares": video_data.get('share_count', 0),
            "transcript": transcript,
            "error": None
        }
    except Exception as e:
        logger.error(f"Lỗi trong get_tiktok_video_info: {e}")
        return {"error": f"Lỗi không xác định: {e}"}

def analyze_tiktok_video(video_info: dict) -> str:
    transcript = video_info.get("transcript", "Không có nội dung để phân tích.")
    if not GOOGLE_API_KEY: return json.dumps({"error": "Google API key chưa được cấu hình."})
    if "Không có audio" in transcript: return json.dumps({"summary": "Video không có lời thoại.", "main_topics": []})
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""Phân tích văn bản sau và trả về JSON có khóa "summary" và "main_topics".\n\nVăn bản: {transcript}\n\nJSON output:"""
        response = model.generate_content(prompt)
        json_string = response.text.strip().replace('```json', '').replace('```', '')
        json.loads(json_string)
        return json_string
    except Exception as e:
        logger.error(f"Lỗi khi phân tích bằng Gemini: {e}")
        return json.dumps({"summary": "Không thể phân tích nội dung.", "main_topics": []})
