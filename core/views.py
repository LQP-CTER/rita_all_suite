import json
import logging
import threading
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import TikTokVideo, ChatHistory, Profile, TrackingLink, LocationLog
from .forms import RegistrationForm, LoginForm, ProfileUpdateForm
from django.contrib.auth import login, logout, update_session_auth_hash, authenticate
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from .ai_utils import get_gemini_response
from .tiktok_utils import get_tiktok_video_info, analyze_tiktok_video

logger = logging.getLogger(__name__)

# --- Các view xác thực và trang chung ---
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
            Profile.objects.create(user=user) # Tạo profile cho người dùng mới
            login(request, user)
            messages.success(request, "Đăng ký thành công!")
            return redirect('core:chat_view')
        else:
            # Gửi lỗi của form ra message để hiển thị
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form.fields[field].label}: {error}")
    
    # Nếu là GET request hoặc form không hợp lệ, render lại trang
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
            # Nếu form không hợp lệ, gửi thông báo lỗi chung
            messages.error(request, "Tên đăng nhập hoặc mật khẩu không đúng. Vui lòng thử lại.")
    
    # Nếu là GET request hoặc đăng nhập thất bại, render lại trang
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
    profile, created = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        if 'form_type' in request.POST and request.POST['form_type'] == 'update_profile':
            profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile, user=request.user)
            password_form = PasswordChangeForm(request.user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, 'Hồ sơ của bạn đã được cập nhật thành công!')
                return redirect('core:profile_view')
        elif 'form_type' in request.POST and request.POST['form_type'] == 'change_password':
            password_form = PasswordChangeForm(request.user, request.POST)
            profile_form = ProfileUpdateForm(instance=profile, user=request.user)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Mật khẩu của bạn đã được thay đổi thành công!')
                return redirect('core:profile_view')
    else:
        profile_form = ProfileUpdateForm(instance=profile, user=request.user)
        password_form = PasswordChangeForm(request.user)

    context = {
        'profile_form': profile_form,
        'password_form': password_form,
        'profile': profile,
        'user': request.user
    }
    return render(request, 'profile.html', context)

@login_required
def chat_view(request):
    chat_history = ChatHistory.objects.filter(user=request.user).order_by('timestamp')
    return render(request, 'index.html', {'chat_history': chat_history})

@login_required
def about_view(request):
    return render(request, 'about.html')

@login_required
def tiktok_analyzer_view(request):
    videos = TikTokVideo.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'tiktok_analyzer.html', {'videos': videos})
    
# --- Logic xử lý nền cho TikTok ---
def perform_analysis_in_background(video_pk):
    try:
        video = TikTokVideo.objects.get(pk=video_pk)
        video_info = {'transcript': video.transcript}
        
        analysis_result_json = analyze_tiktok_video(video_info)
        
        video.analysis = json.loads(analysis_result_json)
        video.status = 'COMPLETE'
        video.save()
        logger.info(f"Phân tích hoàn tất cho video PK: {video_pk}")

    except TikTokVideo.DoesNotExist:
        logger.error(f"Video PK: {video_pk} không tồn tại để phân tích.")
    except Exception as e:
        logger.error(f"Lỗi khi phân tích video PK {video_pk} trong nền: {e}")
        try:
            video = TikTokVideo.objects.get(pk=video_pk)
            video.status = 'FAILED'
            video.save()
        except TikTokVideo.DoesNotExist:
            pass

# --- API Endpoints ---
@login_required
@require_POST
def api_chat(request):
    try:
        data = json.loads(request.body)
        user_input = data.get('message')
        search_web = data.get('search_web', True)
        if not user_input:
            return JsonResponse({'error': 'Message is required'}, status=400)
        ChatHistory.objects.create(user=request.user, role='user', content=user_input)
        response_text = get_gemini_response(user_input, user=request.user, search_web=search_web)
        ChatHistory.objects.create(user=request.user, role='model', content=response_text)
        return JsonResponse({'response': response_text})
    except Exception as e:
        logger.error(f"Lỗi trong api_chat: {e}")
        return JsonResponse({'error': 'An internal error occurred'}, status=500)

@login_required
@require_POST
def delete_chat_history(request):
    try:
        ChatHistory.objects.filter(user=request.user).delete()
        return JsonResponse({'status': 'success', 'message': 'Lịch sử trò chuyện đã được xóa.'})
    except Exception as e:
        logger.error(f"Lỗi khi xóa lịch sử chat: {e}")
        return JsonResponse({'status': 'error', 'message': 'Có lỗi xảy ra.'}, status=500)

@login_required
@require_POST
def api_tiktok_submit_url(request):
    try:
        data = json.loads(request.body)
        video_url = data.get('video_url')
        if not video_url:
            return JsonResponse({'error': 'URL video là bắt buộc'}, status=400)

        video_info = get_tiktok_video_info(video_url, request.user.username)
        if video_info.get("error"):
            return JsonResponse({'error': video_info.get("error")}, status=400)

        video, created = TikTokVideo.objects.update_or_create(
            user=request.user, video_id=video_info.get("video_id"),
            defaults={
                'video_url': video_url,
                'author': video_info.get("author"),
                'description': video_info.get("description"),
                'cover_url': video_info.get("cover_url"),
                'download_url': video_info.get("download_url"),
                'play_count': video_info.get("play_count"),
                'likes': video_info.get("likes"),
                'comments': video_info.get("comments"),
                'shares': video_info.get("shares"),
                'transcript': video_info.get('transcript'),
                'status': 'PROCESSING',
                'analysis': None
            }
        )
        
        analysis_thread = threading.Thread(target=perform_analysis_in_background, args=(video.pk,))
        analysis_thread.start()

        return JsonResponse({
            'status': 'processing',
            'message': 'Đã nhận yêu cầu, đang phân tích AI trong nền.',
            'video': {
                'id': video.pk,
                'author': video.author,
                'description': video.description,
                'cover_url': video.cover_url,
                'download_url': video.download_url,
                'plays': video.play_count,
                'likes': video.likes,
                'comments': video.comments,
                'shares': video.shares,
                'transcript': video.transcript,
            }
        })
    except Exception as e:
        logger.error(f"Lỗi trong api_tiktok_submit_url: {e}")
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

@login_required
def location_tracker_dashboard(request):
    if request.method == 'POST':
        original_url = request.POST.get('url')
        if original_url:
            TrackingLink.objects.create(user=request.user, original_url=original_url)
            return redirect('core:location_tracker_dashboard')
            
    links = TrackingLink.objects.filter(user=request.user).order_by('-created_at').prefetch_related('logs')
    
    for link in links:
        for log in link.logs.all():
            log.lat_str = format(log.latitude, '.5f')
            log.lon_str = format(log.longitude, '.5f')

    context = {
        'links': links,
        'base_url': request.build_absolute_uri('/')
    }
    return render(request, 'location_tracker.html', context)

def track_and_redirect(request, tracking_id):
    link = get_object_or_404(TrackingLink, tracking_id=tracking_id)
    return render(request, 'tracker_page.html', {'link': link})

@csrf_exempt
@require_POST
def save_location(request):
    try:
        data = json.loads(request.body)
        tracking_id = data.get('tracking_id')
        lat = data.get('lat')
        lon = data.get('lon')

        if not all([tracking_id, lat, lon]):
             return JsonResponse({'status': 'error', 'message': 'Dữ liệu không đầy đủ.'}, status=400)

        link = TrackingLink.objects.get(tracking_id=tracking_id)
        LocationLog.objects.create(tracking_link=link, latitude=lat, longitude=lon)
                 
        return JsonResponse({'status': 'success', 'message': 'Vị trí đã được lưu.'})
    except TrackingLink.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'ID theo dõi không hợp lệ.'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
def api_get_tracker_data(request):
    links = TrackingLink.objects.filter(user=request.user).order_by('-created_at').prefetch_related('logs')
    data = []
    for link in links:
        logs_data = []
        for log in link.logs.all():
            logs_data.append({
                'timestamp': log.timestamp.strftime("%H:%M:%S, %d/%m/%Y"),
                'latitude': log.latitude,
                'longitude': log.longitude,
            })
        
        data.append({
            'id': link.id,
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
