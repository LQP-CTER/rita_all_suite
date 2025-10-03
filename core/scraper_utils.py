# File: Rita_All_Django/core/scraper_utils.py
import os
import random
import time
import json
import logging
from typing import List, Type

import pandas as pd
from bs4 import BeautifulSoup
from pydantic import BaseModel, create_model
from readability import Document
import html2text

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

import google.generativeai as genai
from django.conf import settings

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Lấy các hằng số
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
]
PRICING = {
    "gemini-1.5-flash": {
        "input": 0.075 / 1_000_000,
        "output": 0.30 / 1_000_000,
    }
}
HEADLESS_OPTIONS = ["--headless=new", "--disable-gpu", "--disable-dev-shm-usage", "--window-size=1920,1080"]
SYSTEM_MESSAGE = """You are an intelligent text extraction and conversion assistant. Your task is to extract structured information 
                        from the given text and convert it into a pure JSON format. The JSON should contain only the structured data extracted from the text, 
                        with no additional commentary, explanations, or extraneous information. 
                        You could encounter cases where you can't find the data of the fields you have to extract or the data will be in a foreign language.
                        Please process the following text and provide the output in pure JSON format with no words before or after the JSON:"""
USER_MESSAGE = "Extract the following information from the provided text:\nPage content:\n\n"

def setup_selenium():
    """Khởi tạo và cấu hình trình duyệt ảo Selenium."""
    options = Options()
    user_agent = random.choice(USER_AGENTS)
    options.add_argument(f"user-agent={user_agent}")
    for option in HEADLESS_OPTIONS:
        options.add_argument(option)
    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def fetch_html_selenium(url):
    """Lấy nội dung HTML của một trang web sử dụng Selenium."""
    driver = setup_selenium()
    try:
        driver.get(url)
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        return driver.page_source
    except Exception as e:
        logger.error(f"Lỗi khi fetch HTML bằng Selenium: {e}")
        return None
    finally:
        driver.quit()

def html_to_markdown(html_content):
    """Chuyển đổi HTML thành Markdown, tập trung vào nội dung chính."""
    doc = Document(html_content)
    cleaned_html = doc.summary()
    markdown_converter = html2text.HTML2Text()
    markdown_converter.ignore_links = False
    return markdown_converter.handle(cleaned_html)

def create_dynamic_listing_model(field_names: List[str]) -> Type[BaseModel]:
    """Tạo một Pydantic model động dựa trên danh sách các trường."""
    sanitized_fields = {field.replace(' ', '_'): (str, ...) for field in field_names}
    return create_model('DynamicListingModel', **sanitized_fields)

def create_listings_container_model(listing_model: Type[BaseModel]) -> Type[BaseModel]:
    """Tạo một Pydantic container model để chứa danh sách các model con."""
    container_key = f"{listing_model.__name__.replace('Model', '').lower()}_listings"
    return create_model('DynamicListingsContainer', **{container_key: (List[listing_model], ...)})

def gemini_format_data(data, DynamicListingsContainer, model="gemini-1.5-flash"):
    """Gửi dữ liệu đến Gemini API và yêu cầu trả về JSON theo schema."""
    token_counts = {}
    try:
        GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
        if not GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY không được cấu hình.")
        genai.configure(api_key=GOOGLE_API_KEY)

        # SỬA LỖI: Truyền thẳng Pydantic Model class vào response_schema
        # Thư viện google-generativeai sẽ tự động chuyển đổi sang schema tương thích.
        model = genai.GenerativeModel(
            model_name=model,
            generation_config={
                "response_mime_type": "application/json",
                "response_schema": DynamicListingsContainer
            }
        )
        
        prompt = f"{SYSTEM_MESSAGE}\n{USER_MESSAGE}\n{data}"
        
        response = model.generate_content(prompt)
        
        token_counts = {
            "input_tokens": response.usage_metadata.prompt_token_count,
            "output_tokens": response.usage_metadata.candidates_token_count
        }
        
        formatted_data_str = response.text
        
        # Kiểm tra lại để chắc chắn chuỗi trả về là JSON hợp lệ
        try:
            json.loads(formatted_data_str)
        except json.JSONDecodeError:
            logger.error(f"Gemini API response is not valid JSON: {formatted_data_str}")
            return json.dumps({"error": "Gemini response is not valid JSON", "details": formatted_data_str}), token_counts

        return formatted_data_str, token_counts

    except Exception as e:
        logger.error(f"Lỗi khi gọi Gemini API: {e}")
        # Trả về một chuỗi JSON chứa thông tin lỗi để xử lý ở view
        return json.dumps({"error": "Lỗi khi gọi Gemini API", "details": str(e)}), token_counts

def calculate_price(token_counts, model="gemini-1.5-flash"):
    """Tính toán chi phí dựa trên số lượng token."""
    input_token_count = token_counts.get("input_tokens", 0)
    output_token_count = token_counts.get("output_tokens", 0)
    input_cost = input_token_count * PRICING[model]["input"]
    output_cost = output_token_count * PRICING[model]["output"]
    total_cost = input_cost + output_cost
    return input_token_count, output_token_count, total_cost

