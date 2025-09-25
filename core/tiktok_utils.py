import requests
import logging
import json
import google.generativeai as genai

# Lấy logger được cấu hình sẵn trong Django
logger = logging.getLogger(__name__)

# End-point của API trung gian để lấy thông tin video TikTok
API_ENDPOINT = "https://www.tikwm.com/api/"

def get_gemini_tiktok_analysis(video_info: dict) -> str:
    """
    Sử dụng Gemini để phân tích thông tin video TikTok và trả về kết quả dưới dạng JSON.
    Hàm này giờ là một phần của tiktok_utils.

    Args:
        video_info (dict): Một dictionary chứa thông tin video đã được trích xuất.

    Returns:
        str: Một chuỗi JSON chứa kết quả phân tích.
    """
    try:
        # Cấu hình model để trả về JSON
        model = genai.GenerativeModel(
            'gemini-1.5-flash-latest',
            generation_config={"response_mime_type": "application/json"}
        )
        
        # Xây dựng prompt chi tiết để hướng dẫn AI
        prompt = f"""
        Với vai trò là một chuyên gia phân tích mạng xã hội, hãy phân tích video TikTok sau đây dựa trên các thông tin được cung cấp.
        
        Thông tin video:
        - Tác giả: {video_info.get('author', 'Không rõ')}
        - Mô tả / Tiêu đề: {video_info.get('description', 'Không có')}
        - Lượt xem: {video_info.get('play_count', 0)}
        - Lượt thích: {video_info.get('likes', 0)}
        - Lượt bình luận: {video_info.get('comments', 0)}
        - Lượt chia sẻ: {video_info.get('shares', 0)}

        Hãy cung cấp phân tích của bạn dưới dạng một đối tượng JSON với các key sau:
        - "summary": (string) Một bản tóm tắt ngắn gọn (2-3 câu) về nội dung và mục đích của video.
        - "sentiment": (string) Cảm xúc tổng thể của video (ví dụ: Tích cực, Tiêu cực, Hài hước, Truyền cảm hứng).
        - "potential_virality": (string) Đánh giá khả năng lan truyền của video (Thấp, Trung bình, Cao) dựa trên các chỉ số tương tác và nội dung.
        - "positive_points": (list of strings) Một danh sách các điểm mạnh hoặc yếu tố tích cực của video.
        - "negative_points": (list of strings) Một danh sách các điểm yếu hoặc những gì có thể được cải thiện.
        - "suggestions": (list of strings) Một danh sách các đề xuất cụ thể để cải thiện video.

        Hãy đảm bảo câu trả lời chỉ là một đối tượng JSON hợp lệ.
        """

        response = model.generate_content(prompt)
        json.loads(response.text) # Xác thực JSON
        return response.text

    except Exception as e:
        logger.error(f"Lỗi khi gọi Gemini API để phân tích TikTok: {e}", exc_info=True)
        error_response = {
            "summary": "Không thể phân tích video do lỗi từ hệ thống AI.",
            "sentiment": "Không xác định", "potential_virality": "Không xác định",
            "positive_points": [], "negative_points": [f"Chi tiết lỗi: {str(e)}"],
            "suggestions": ["Vui lòng thử lại sau."]
        }
        return json.dumps(error_response, ensure_ascii=False)

def get_tiktok_video_info(video_url: str):
    """
    Lấy thông tin chi tiết của video TikTok thông qua một API trung gian.
    """
    try:
        params = {'url': video_url}
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(API_ENDPOINT, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()

        if data.get("code") != 0 or "data" not in data:
            error_message = data.get("msg", "Phản hồi không hợp lệ từ API TikTok.")
            logger.error(f"Lỗi API TikTok: {error_message} cho URL: {video_url}")
            return {"error": error_message}
            
        video_data = data["data"]
        author_info = video_data.get("author", {})

        # CẬP NHẬT: Thay đổi cách lấy thông tin thống kê để khớp với API mới
        formatted_data = {
            "video_id": video_data.get("id"),
            "author": author_info.get("nickname", author_info.get("unique_id")),
            "description": video_data.get("title"),
            "cover_url": video_data.get("cover"),
            "download_url": video_data.get("play"),
            "play_count": video_data.get("play_count", 0),
            "duration": video_data.get("duration", 0),
            "likes": video_data.get("digg_count", 0),
            "comments": video_data.get("comment_count", 0),
            "shares": video_data.get("share_count", 0),
            "transcript": None,
        }
        
        if not formatted_data["video_id"]:
            return {"error": "Không thể lấy ID video. Video có thể là riêng tư hoặc đã bị xóa."}

        logger.info(f"Lấy thông tin thành công cho video ID: {formatted_data['video_id']}")
        return formatted_data

    except requests.exceptions.RequestException as e:
        logger.error(f"Lỗi mạng khi lấy dữ liệu TikTok: {e}", exc_info=True)
        return {"error": f"Lỗi mạng: {e}"}
    except Exception as e:
        logger.error(f"Lỗi không xác định trong get_tiktok_video_info: {e}", exc_info=True)
        return {"error": "Lỗi máy chủ không mong muốn khi xử lý video."}

def analyze_tiktok_video(video_url: str, user):
    """
    Thực hiện phân tích video TikTok bằng AI.
    """
    logger.info(f"Bắt đầu phân tích AI cho video: {video_url} bởi người dùng: {user.username}")
    
    video_info = get_tiktok_video_info(video_url)
    
    if 'error' in video_info:
        logger.error(f"Không thể phân tích video do không lấy được thông tin: {video_info['error']}")
        error_response = {
            "summary": "Không thể phân tích do không lấy được thông tin ban đầu của video.",
            "sentiment": "Không xác định", "potential_virality": "Không xác định",
            "positive_points": [], "negative_points": [f"Lỗi: {video_info['error']}"],
            "suggestions": ["Hãy chắc chắn URL video là công khai và hợp lệ."]
        }
        return json.dumps(error_response, ensure_ascii=False)
        
    analysis_json_string = get_gemini_tiktok_analysis(video_info)
    
    return analysis_json_string