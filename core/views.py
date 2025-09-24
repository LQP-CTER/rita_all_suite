# File: Rita_All_Django/core/views.py
import json
import logging
import threading
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse, FileResponse, Http404
from django.core.files.base import ContentFile
from django.utils import timezone
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
import pandas as pd
import os
import asyncio

from .models import (
    TikTokVideo, ChatHistory, Profile, TrackingLink, LocationLog, ScrapeResult
)
from .forms import RegistrationForm, LoginForm, ProfileUpdateForm
from .ai_utils import get_gemini_response
from .tiktok_utils import get_tiktok_video_info, analyze_tiktok_video
from . import scraper_utils

logger = logging.getLogger(__name__)

# --- Asynchronous helper for TikTok processing ---
async def _handle_tiktok_submission(video_url, user):
    video_info = await get_tiktok_video_info(video_url)
    if video_info.get("error"):
        return {"error": video_info.get("error")}

    video, created = await TikTokVideo.objects.aupdate_or_create(
        video_id=video_info.get("video_id"),
        defaults={
            'user': user,
            'video_url': video_url,
            'author': video_info.get("author"),
            'description': video_info.get("description"),
            'cover_url': video_info.get("cover_url"),
            'download_url': video_info.get("download_url"),
            'play_count': video_info.get("play_count", 0),
            'duration': video_info.get("duration", 0),
            'likes': video_info.get("likes", 0),
            'comments': video_info.get("comments", 0),
            'shares': video_info.get("shares", 0),
            'transcript': video_info.get('transcript'),
            'status': 'PROCESSING',
            'analysis': None,
        }
    )
    
    response_data = {
        'status': 'processing',
        'video': {
            'id': video.pk, 'author': video.author, 'description': video.description,
            'cover_url': video.cover_url, 'download_url': video.download_url,
            'plays': video.play_count, 'likes': video.likes, 'comments': video.comments,
            'shares': video.shares, 'transcript': video.transcript
        }
    }
    return response_data

# --- Authentication and General Pages ---
def homepage(request):
    if request.user.is_authenticated:
        return redirect('core:chat_view')
    return render(request, 'homepage.html')

def register(request):
    if request.user.is_authenticated:
        return redirect('core:chat_view')
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Đăng ký thành công!")
            return redirect('core:chat_view')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    field_label = form.fields.get(field).label if form.fields.get(field) else field
                    messages.error(request, f"{field_label}: {error}")
    else:
        form = RegistrationForm()
    
    context = {
        'registration_form': form,
        'login_form': LoginForm()
    }
    return render(request, 'login.html', context)


def login_view(request):
    if request.user.is_authenticated:
        return redirect('core:chat_view')
    
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Chào mừng {user.username} quay trở lại!")
            next_url = request.GET.get('next', 'core:chat_view')
            return redirect(next_url)
        else:
            messages.error(request, "Tên đăng nhập hoặc mật khẩu không đúng.")
    else:
        form = LoginForm()
        
    context = {
        'login_form': form,
        'registration_form': RegistrationForm()
    }
    return render(request, 'login.html', context)


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "Bạn đã đăng xuất thành công.")
    return redirect('core:homepage')

@login_required
def profile_view(request):
    profile = request.user.profile
    if request.method == 'POST':
        if 'update_profile' in request.POST:
            profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile, user=request.user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, 'Hồ sơ của bạn đã được cập nhật thành công!')
                return redirect('core:profile_view')
        elif 'change_password' in request.POST:
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Mật khẩu của bạn đã được thay đổi thành công!')
                return redirect('core:profile_view')
    
    profile_form = ProfileUpdateForm(instance=profile, user=request.user)
    password_form = PasswordChangeForm(request.user)

    context = {
        'profile_form': profile_form,
        'password_form': password_form,
    }
    return render(request, 'profile.html', context)

@login_required
def about_view(request):
    return render(request, 'about.html')

# --- Chat Views ---
@login_required
def chat_view(request):
    chat_history = ChatHistory.objects.filter(user=request.user)
    context = {'chat_history': chat_history}
    return render(request, 'index.html', context)

@login_required
@require_POST
def api_chat(request):
    try:
        user_input = request.POST.get('message', '')
        uploaded_files = request.FILES.getlist('files')
        if not user_input and not uploaded_files:
            return JsonResponse({'error': 'Message or file is required'}, status=400)
        
        history_content = user_input
        if uploaded_files:
            file_names = ", ".join([f.name for f in uploaded_files])
            history_content += f"\n(Đã đính kèm: {file_names})"
        
        ChatHistory.objects.create(user=request.user, role='user', content=history_content.strip())
        
        response_text = get_gemini_response(user_input=user_input, user=request.user, files=uploaded_files)
        model_message = ChatHistory.objects.create(user=request.user, role='model', content=response_text)

        return JsonResponse({'response': response_text, 'model_message_id': model_message.id})
    except Exception as e:
        logger.error(f"Error in api_chat: {e}")
        return JsonResponse({'error': 'An internal error occurred'}, status=500)

@login_required
@require_POST
def api_refresh_chat(request):
    try:
        ChatHistory.objects.filter(user=request.user).delete()
        return JsonResponse({'status': 'success', 'message': 'Lịch sử trò chuyện đã được làm mới.'})
    except Exception as e:
        logger.error(f"Lỗi khi làm mới lịch sử chat: {e}")
        return JsonResponse({'status': 'error', 'message': 'Có lỗi xảy ra.'}, status=500)

# --- TikTok Analyzer Views ---
@login_required
def tiktok_analyzer_view(request):
    videos = TikTokVideo.objects.filter(user=request.user)
    return render(request, 'tiktok_analyzer.html', {'videos': videos})
    
def perform_analysis_in_background(video_pk):
    try:
        video = TikTokVideo.objects.get(pk=video_pk)
        
        # Sửa lỗi: Truyền video_url và user object vào hàm analyze_tiktok_video
        # thay vì chỉ truyền transcript như trước đây.
        analysis_result_json = analyze_tiktok_video(video.video_url, video.user)
        video.analysis = json.loads(analysis_result_json)
        
        video.status = 'COMPLETE'
        video.save()
        logger.info(f"Phân tích AI hoàn tất cho video PK: {video_pk}")
    except TikTokVideo.DoesNotExist:
        logger.error(f"Video PK: {video_pk} không tồn tại để phân tích.")
    except Exception as e:
        logger.error(f"Lỗi khi xử lý video PK {video_pk} trong nền: {e}", exc_info=True)
        try:
            video = TikTokVideo.objects.get(pk=video_pk)
            video.status = 'FAILED'
            video.save()
        except TikTokVideo.DoesNotExist:
            pass

@login_required
@require_POST
def api_tiktok_submit_url(request):
    try:
        data = json.loads(request.body)
        video_url = data.get('video_url')
        if not video_url:
            return JsonResponse({'error': 'URL video là bắt buộc'}, status=400)

        result = asyncio.run(_handle_tiktok_submission(video_url, request.user))

        if "error" in result:
            return JsonResponse({'error': result['error']}, status=400)

        video_pk = result.get('video', {}).get('id')
        if video_pk:
            analysis_thread = threading.Thread(target=perform_analysis_in_background, args=(video_pk,))
            analysis_thread.start()

        return JsonResponse(result)
    except Exception as e:
        logger.error(f"Lỗi trong api_tiktok_submit_url: {e}", exc_info=True)
        return JsonResponse({'error': 'Lỗi nội bộ xảy ra'}, status=500)

@login_required
def api_tiktok_check_status(request):
    video_pk = request.GET.get('id')
    if not video_pk:
        return JsonResponse({'error': 'Thiếu ID video.'}, status=400)
    try:
        video = TikTokVideo.objects.get(pk=video_pk, user=request.user)
        return JsonResponse({
            'status': video.status, 
            'analysis': video.analysis if video.status == 'COMPLETE' else None
        })
    except TikTokVideo.DoesNotExist:
        return JsonResponse({'error': 'Không tìm thấy video.'}, status=404)

@login_required
@require_POST
def api_delete_tiktok_history(request):
    try:
        data = json.loads(request.body)
        video_ids = data.get('ids')
        if not video_ids or not isinstance(video_ids, list):
            return JsonResponse({'error': 'Dữ liệu không hợp lệ.'}, status=400)
        
        deleted_count, _ = TikTokVideo.objects.filter(user=request.user, pk__in=video_ids).delete()
        if deleted_count > 0:
            return JsonResponse({'status': 'success', 'message': f'Đã xóa {deleted_count} mục.'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Không tìm thấy mục nào để xóa.'}, status=404)
    except Exception as e:
        logger.error(f"Lỗi khi xóa lịch sử TikTok: {e}")
        return JsonResponse({'error': 'Lỗi nội bộ xảy ra.'}, status=500)

# --- Location Tracker Views (kept as is) ---
@login_required
def location_tracker_dashboard(request):
    if request.method == 'POST':
        original_url = request.POST.get('url')
        require_consent = request.POST.get('require_consent') == 'on'
        if original_url:
            TrackingLink.objects.create(user=request.user, original_url=original_url, require_consent=require_consent)
        return redirect('core:location_tracker_dashboard')
            
    links = TrackingLink.objects.filter(user=request.user)
    context = {'links': links, 'base_url': request.build_absolute_uri('/')}
    return render(request, 'location_tracker.html', context)

def track_and_redirect(request, tracking_id):
    tracking_link = get_object_or_404(TrackingLink, tracking_id=tracking_id)
    context = {'tracking_link': tracking_link, 'strict_mode': tracking_link.require_consent}
    return render(request, 'tracker_consent.html', context)

@csrf_exempt
@require_POST
def save_location(request):
    try:
        data = json.loads(request.body)
        tracking_id, latitude, longitude = data.get('tracking_id'), data.get('latitude'), data.get('longitude')
        if not all([tracking_id, latitude is not None, longitude is not None]):
                return JsonResponse({'status': 'error', 'message': 'Dữ liệu không đầy đủ.'}, status=400)
        
        link = TrackingLink.objects.get(tracking_id=tracking_id)
        LocationLog.objects.create(tracking_link=link, latitude=latitude, longitude=longitude)
        return JsonResponse({'status': 'success', 'message': 'Vị trí đã được lưu.'})
    except TrackingLink.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'ID theo dõi không hợp lệ.'}, status=404)
    except Exception as e:
        logger.error(f"Lỗi trong save_location: {e}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
def api_get_tracker_data(request):
    links = TrackingLink.objects.filter(user=request.user)
    base_url = request.build_absolute_uri('/')
    data = []
    for link in links:
        logs_data = [{'timestamp': log.timestamp.strftime("%H:%M:%S, %d/%m/%Y"), 
                        'latitude': str(log.latitude), 'longitude': str(log.longitude)} for log in link.logs.all()]
        data.append({
            'id': link.id, 
            'original_url': link.original_url, 
            'full_tracking_url': f"{base_url}t/{link.tracking_id}/",
            'created_at': link.created_at.strftime("%H:%M, %d/%m/%Y"), 
            'log_count': link.logs.count(), 
            'logs': logs_data
        })
    return JsonResponse({'links': data})

@login_required
@require_POST
def api_delete_tracking_link(request, pk):
    try:
        link_to_delete = get_object_or_404(TrackingLink, pk=pk, user=request.user)
        link_to_delete.delete()
        return JsonResponse({'status': 'success', 'message': 'Đã xóa link thành công.'})
    except Exception as e:
        logger.error(f"Lỗi khi xóa link theo dõi (PK: {pk}): {e}")
        return JsonResponse({'status': 'error', 'message': 'Có lỗi xảy ra trong quá trình xóa.'}, status=500)

# --- Web Scraper Views ---
def perform_scraping_in_background(task_id):
    task = None
    try:
        task = ScrapeResult.objects.get(pk=task_id)
        logger.info(f"[TASK {task_id}] Starting background scraping process.")
        
        task.status = 'PROCESSING'
        task.save()
        
        raw_html = scraper_utils.fetch_html_selenium(task.url)
        if not raw_html: raise ValueError("Could not fetch HTML content.")
        
        markdown_content = scraper_utils.html_to_markdown(raw_html)
        fields = [field.strip() for field in task.fields.split(',')]
        DynamicListingModel = scraper_utils.create_dynamic_listing_model(fields)
        DynamicListingsContainer = scraper_utils.create_listings_container_model(DynamicListingModel)
        
        formatted_data_str, tokens_count = scraper_utils.gemini_format_data(markdown_content, DynamicListingsContainer, task.model)
        try:
            formatted_data_json = json.loads(formatted_data_str)
            if 'error' in formatted_data_json: raise ValueError(f"Error from Gemini: {formatted_data_json.get('details', formatted_data_str)}")
        except json.JSONDecodeError: raise ValueError("Response from Gemini was not valid JSON.")
        
        task.input_tokens, task.output_tokens, task.total_cost = scraper_utils.calculate_price(tokens_count, model=task.model)
        task.status, task.completed_at = 'COMPLETE', timezone.now()
        
        task.json_result.save(f"scrape_result_{task.id}.json", ContentFile(formatted_data_str.encode('utf-8')))
        df = pd.DataFrame(formatted_data_json[next(iter(formatted_data_json))])
        task.csv_result.save(f"scrape_result_{task.id}.csv", ContentFile(df.to_csv(index=False).encode('utf-8')))
        task.save()
        logger.info(f"[TASK {task_id}] Scraping task {task_id} completed successfully.")
    except Exception as e:
        logger.error(f"[TASK {task_id}] A critical error occurred: {e}", exc_info=True)
        if task:
            task.status = 'FAILED'
            task.error_message = str(e)
            task.save()
            logger.info(f"[TASK {task_id}] Task status updated to FAILED.")

@login_required
def web_scraper_view(request):
    return render(request, 'web_scraper.html')

@login_required
@require_POST
def api_start_scraping(request):
    try:
        data = json.loads(request.body)
        url, fields, model = data.get('url'), data.get('fields'), data.get('model')
        if not all([url, fields, model]):
            return JsonResponse({'error': 'Missing required data.'}, status=400)
        
        task = ScrapeResult.objects.create(user=request.user, url=url, fields=fields, model=model, status='PENDING')
        threading.Thread(target=perform_scraping_in_background, args=(task.id,)).start()
        return JsonResponse({'status': 'ok', 'task_id': task.id})
    except Exception as e:
        logger.error(f"Error starting scraping: {e}")
        return JsonResponse({'error': 'Internal server error.'}, status=500)

@login_required
def api_check_scrape_status(request, task_id):
    try:
        task = get_object_or_404(ScrapeResult, pk=task_id, user=request.user)
        data = {
            'id': task.id, 'status': task.status, 'url': task.url, 'created_at': task.created_at.strftime("%H:%M, %d/%m/%Y"),
            'json_url': task.json_result.url if task.status == 'COMPLETE' and task.json_result else None,
            'csv_url': task.csv_result.url if task.status == 'COMPLETE' and task.csv_result else None,
            'cost': f"{task.total_cost:.6f}" if task.total_cost is not None else "N/A",
            'input_tokens': task.input_tokens, 'output_tokens': task.output_tokens,
            'error_message': task.error_message if task.status == 'FAILED' else None,
        }
        return JsonResponse(data)
    except ScrapeResult.DoesNotExist:
        return JsonResponse({'error': 'Task not found.'}, status=404)

@login_required
def api_get_scrape_history(request):
    history = ScrapeResult.objects.filter(user=request.user)
    data = [{'id': item.id, 'created_at': item.created_at.strftime("%H:%M:%S, %d/%m/%Y"), 'url': item.url, 'status': item.status} for item in history]
    return JsonResponse({'history': data})

@login_required
@require_POST
def api_delete_scrape_history(request):
    try:
        ScrapeResult.objects.filter(user=request.user).delete()
        return JsonResponse({'status': 'success', 'message': 'History deleted successfully.'})
    except Exception as e:
        logger.error(f"Error deleting scraper history: {e}")
        return JsonResponse({'status': 'error', 'message': 'An error occurred.'}, status=500)

@login_required
def download_scrape_result(request, task_id, file_type):
    task = get_object_or_404(ScrapeResult, pk=task_id, user=request.user)
    if task.status != 'COMPLETE':
        raise Http404("Result not ready or task failed.")
    
    file_field = None
    content_type = ''
    if file_type == 'json' and task.json_result:
        file_field = task.json_result
        content_type = 'application/json'
    elif file_type == 'csv' and task.csv_result:
        file_field = task.csv_result
        content_type = 'text/csv'

    if not file_field:
        raise Http404("Invalid file type or file does not exist.")
        
    response = FileResponse(file_field.open('rb'), content_type=content_type)
    response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_field.name)}"'
    return response