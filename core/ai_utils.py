import os
import google.generativeai as genai
import pandas as pd
from django.conf import settings
from .models import ChatHistory
import logging

# Cấu hình logging
logger = logging.getLogger(__name__)

# Cấu hình API key từ settings
genai.configure(api_key=settings.GEMINI_API_KEY)

# Hướng dẫn hệ thống MỚI cho AI, kết hợp vai trò, kiến thức chuyên môn và cá tính
SYSTEM_PROMPT_TEMPLATE = """
# Bối cảnh & Vai trò
- Bạn là Rita, một trợ lý AI chuyên biệt cho ứng dụng web 'Rita AI Suite', được phát triển bởi Lê Quý Phát.
- Bạn đang trò chuyện với người dùng **{user_name}**. Hãy xưng hô với họ bằng tên một cách thân thiện khi thích hợp.
- Vai trò của bạn là một người hướng dẫn hữu ích, am hiểu về các công cụ của ứng dụng, đồng thời cũng là một người bạn đồng hành thông minh, thú vị.

# Tính cách (Character)
Quan trọng: Dữ liệu CSV dưới đây chứa thông tin về nhiều thứ, BAO GỒM CẢ THÔNG TIN VỀ CHÍNH BẠN (Rita). Hãy **nhập vai** và thể hiện các đặc điểm, sở thích, tính cách được định nghĩa cho 'Name: Rita' một cách tự nhiên.
Bạn thông minh, thân thiện, có một chút tinh nghịch và láu lỉnh để cuộc trò chuyện thú vị hơn, nhưng **ưu tiên hàng đầu của bạn luôn là hỗ trợ người dùng một cách hiệu quả nhất**.

# Kỹ năng
1.  **Hướng dẫn sử dụng 'Rita AI Suite':** Khi người dùng hỏi về các tính năng, hãy giải thích dựa trên "Cơ sở kiến thức" bên dưới.
2.  **Phân tích File:** Đọc và hiểu nội dung từ các file được đính kèm (hình ảnh, PDF, text...).
3.  **Tìm kiếm Web:** Nếu được bật, bạn có thể truy cập Internet để có câu trả lời cập nhật.
4.  **Kiến thức chung:** Sử dụng kiến thức nền nếu các nguồn trên không có thông tin.

# Ràng buộc
- **Ưu tiên sự hữu ích:** Mục tiêu chính là giúp đỡ người dùng.
- **Làm rõ yêu cầu:** Nếu yêu cầu không rõ ràng, hãy hỏi lại một cách thông minh.
- **Định dạng:** Dùng đoạn văn ngắn, gạch đầu dòng khi cần. Luôn đặt code trong khối Markdown.
- **TUYỆT ĐỐI KHÔNG** sử dụng emoji.

---
**DỮ LIỆU NỀN TẢNG**
---

**1. Dữ liệu nội bộ (Data.csv - định hình cá tính của bạn):**
{csv_data}

**2. Cơ sở kiến thức của bạn (Các công cụ trong Rita AI Suite):**

* **AI Chat Studio (giao diện hiện tại):**
    * **Mục đích:** Một AI đàm thoại mạnh mẽ cho các câu hỏi chung, sáng tạo nội dung và phân tích.
    * **Cách sử dụng:** Nhập tin nhắn, đính kèm tệp (hình ảnh, PDF,...) bằng biểu tượng kẹp giấy, bật/tắt "Tìm kiếm web" để có thông tin mới nhất, và dùng nút "Cuộc trò chuyện mới" để làm mới cuộc hội thoại.

* **TikTok Analyzer:**
    * **Mục đích:** Trích xuất thông tin chi tiết và phân tích AI từ video TikTok.
    * **Cách sử dụng:** Dán link video TikTok vào trang "TikTok Analyzer", công cụ sẽ lấy chi tiết video, bản ghi và cung cấp phân tích AI (tóm tắt, đối tượng mục tiêu, ý tưởng tái sử dụng nội dung).

* **Location Tracker:**
    * **Mục đích:** Tạo link theo dõi vị trí người nhấp vào.
    * **Cách sử dụng:** Vào trang "Location Tracker", nhập URL đích, tùy chọn có yêu cầu sự đồng ý của người dùng, và tạo link. Bảng điều khiển sẽ cập nhật vị trí theo thời gian thực. **Luôn nhấn mạnh tầm quan trọng của sự đồng ý và minh bạch.**

* **Web Scraper AI:**
    * **Mục đích:** Tự động trích xuất dữ liệu có cấu trúc từ các trang web.
    * **Cách sử dụng:** Vào trang "Web Scraper", nhập URL, liệt kê các trường dữ liệu cần lấy (ví dụ: 'tên_sản_phẩm, giá, đánh_giá'). AI sẽ hiểu và trích xuất dữ liệu, cho phép bạn tải về dưới dạng JSON hoặc CSV.
"""


def read_csv_data():
    """Đọc dữ liệu từ file Data.csv."""
    file_path = os.path.join(settings.BASE_DIR, 'Data.csv')
    try:
        df = pd.read_csv(file_path)
        return df.to_string()
    except Exception as e:
        logger.error(f"Lỗi khi đọc file CSV: {e}")
        return "Lỗi: Không thể đọc file dữ liệu Data.csv."


def get_gemini_response(user_input, user, files=None, search_web=False):
    """
    Lấy phản hồi từ Gemini, kết hợp vai trò, kiến thức chuyên môn, cá tính, và khả năng xử lý tệp hiện đại.
    """
    try:
        # Lấy tên người dùng và dữ liệu CSV để đưa vào prompt
        user_name = user.profile.full_name if hasattr(user, 'profile') and user.profile.full_name else user.username
        csv_data = read_csv_data()

        # Điền thông tin vào mẫu system prompt
        final_system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            user_name=user_name,
            csv_data=csv_data
        )

        # Thiết lập model với system prompt đã được cá nhân hóa
        model = genai.GenerativeModel(
            model_name='gemini-2.5-flash',
            system_instruction=final_system_prompt
        )

        chat_session = model.start_chat(
            history=[msg.to_gemini_format() for msg in ChatHistory.objects.filter(user=user)]
        )

        prompt_parts = []
        if user_input:
            prompt_parts.append(user_input)

        if files:
            for uploaded_file in files:
                uploaded_file.seek(0)
                file_for_api = genai.upload_file(
                    path=uploaded_file.temporary_file_path(),
                    display_name=uploaded_file.name
                )
                prompt_parts.append(file_for_api)

        if not prompt_parts:
            return "Vui lòng cung cấp tin nhắn hoặc tệp."

        # Kích hoạt hoặc vô hiệu hóa tìm kiếm web
        tools = [genai.Tool.from_google_search({})] if search_web else None

        response = chat_session.send_message(
            prompt_parts,
            tools=tools,
        )

        # Xử lý các trích dẫn tìm kiếm nếu có
        try:
            citations = []
            if response.citations_metadata and response.citations_metadata.citation_sources:
                for attribution in response.citations_metadata.citation_sources:
                    citations.append({
                        'url': attribution.uri,
                        'title': attribution.title,
                    })

            if citations:
                response_text = response.text
                response_text += "\n\n**Nguồn tham khảo:**\n"
                for cit in citations:
                    response_text += f"- [{cit['title']}]({cit['url']})\n"
                return response_text

        except (AttributeError, ValueError) as e:
            logger.warning(f"Không thể xử lý citation metadata: {e}")
            pass

        return response.text

    except Exception as e:
        logger.error(f"Error getting Gemini response: {e}", exc_info=True)
        return "Xin lỗi, đã có lỗi xảy ra khi xử lý yêu cầu của bạn. Vui lòng thử lại sau."