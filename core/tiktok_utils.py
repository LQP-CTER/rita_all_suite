import os
import requests
import logging
from bs4 import BeautifulSoup
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_tiktok_video_info(video_url):
    """
    Scrapes a TikTok video page to get the video download link, cover image,
    and transcript from the video description.
    """
    headers = {
        'User-Agent': 'Mozilla/V.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        logging.info(f"Requesting TikTok URL: {video_url}")
        response = requests.get(video_url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the script tag containing the JSON data
        script_tag = soup.find('script', id='__UNIVERSAL_DATA_FOR_REHYDRATION__')
        if not script_tag:
            logging.error("Could not find the universal data script tag.")
            return {"error": "Could not find data script tag. The page structure might have changed."}

        json_data = json.loads(script_tag.string)
        
        # Navigate through the JSON structure to find the required data
        # The path might need adjustments if TikTok changes its page structure
        item_module = json_data.get('__DEFAULT_SCOPE__', {}).get('webapp.video-detail', {}).get('itemInfo', {}).get('itemModule', {})

        if not item_module:
            logging.error("Could not find 'itemModule' in the JSON data.")
            return {"error": "Could not find item details in JSON. The page structure might have changed."}

        video_data = {
            "download_url": item_module.get("video", {}).get("playAddr"),
            "cover_url": item_module.get("video", {}).get("cover"),
            "transcript": item_module.get("desc"),
            "author": item_module.get("author", {}).get("uniqueId"),
        }

        if not all(video_data.values()):
            logging.warning("Some video information is missing.")
            # We can still proceed if we have a transcript
            if not video_data["transcript"]:
                 return {"error": "Could not extract all required video information."}


        logging.info(f"Successfully extracted video info for author: {video_data['author']}")
        return video_data

    except requests.exceptions.RequestException as e:
        logging.error(f"Network error while fetching TikTok URL: {e}")
        return {"error": f"Network error: {e}"}
    except (json.JSONDecodeError, AttributeError, KeyError) as e:
        logging.error(f"Error parsing page data: {e}")
        return {"error": "Failed to parse page data. TikTok's structure may have changed."}
    except Exception as e:
        logging.error(f"An unexpected error occurred in get_tiktok_video_info: {e}", exc_info=True)
        return {"error": "An unexpected error occurred."}


def analyze_tiktok_video(video_url, user):
    """
    Analyzes a TikTok video by getting its transcript and then using an AI model
    to summarize it and determine its sentiment.
    """
    # Import moved inside function to avoid circular dependency at startup
    from .ai_utils import get_ai_response

    logging.info(f"Starting analysis for TikTok video: {video_url}")
    try:
        # Get video info, including transcript
        video_info = get_tiktok_video_info(video_url)
        
        if video_info.get("error"):
            logging.error(f"Error getting video info: {video_info['error']}")
            return json.dumps(video_info)

        transcript = video_info.get("transcript")
        if not transcript:
            logging.warning("Could not retrieve transcript for the video.")
            return json.dumps({"error": "Could not retrieve transcript."})

        # Prepare the prompt for the AI model
        prompt = (
            "Please analyze the following TikTok video transcript. Provide a concise, "
            "one-sentence summary and determine the overall sentiment (Positive, Negative, or Neutral). "
            "Format your response as a JSON object with two keys: 'summary' and 'sentiment'.\n\n"
            f"Transcript: \"{transcript}\""
        )
        
        # Get completion from the AI model
        logging.info("Sending transcript to AI for analysis.")
        # Pass the user object as required by get_ai_response
        response = get_ai_response(prompt, user)
        logging.info(f"Received AI response: {response}")

        # Assuming response is a JSON string like '{"summary": "...", "sentiment": "..."}'
        try:
            # Attempt to parse the AI's response as JSON
            json_response = json.loads(response)
            # Ensure the response has the expected keys
            if "summary" in json_response and "sentiment" in json_response:
                logging.info("AI response is valid JSON with required keys.")
                return response  # Return the valid JSON string
            else:
                # If JSON is valid but keys are missing, return an error JSON
                logging.warning("AI response is valid JSON but missing required keys.")
                error_data = {
                    "summary": "Incomplete AI response.", 
                    "error": "Missing required keys in AI response."
                }
                return json.dumps(error_data)
        except json.JSONDecodeError:
            # If the response is not valid JSON, clean it up and return an error JSON
            logging.warning("AI response was not in valid JSON format. Cleaning up.")
            cleaned_text = response.strip().replace('\n', ' ')
            
            # The corrected and more robust way
            error_data = {
                "summary": cleaned_text.replace("\"", "'"),
                "error": "AI response was not in valid JSON format."
            }
            return json.dumps(error_data)
    except Exception as e:
        logging.error(f"An unexpected error occurred in analyze_tiktok_video: {e}", exc_info=True)
        # It's better to escape the error message to avoid breaking the JSON structure.
        error_data = {
            "error": f"An unexpected error occurred: {str(e)}"
        }
        return json.dumps(error_data)