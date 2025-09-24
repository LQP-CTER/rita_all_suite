document.addEventListener('DOMContentLoaded', function() {
    // Lấy các element cần thiết từ DOM
    const editProfileBtn = document.getElementById('edit-profile-btn');
    const cancelEditBtn = document.getElementById('cancel-edit-btn');
    const viewProfileInfo = document.getElementById('view-profile-info');
    const editProfileForm = document.getElementById('edit-profile-form');

    // Kiểm tra xem các element có tồn tại không trước khi gán sự kiện
    if (editProfileBtn && viewProfileInfo && editProfileForm) {
        // Bắt sự kiện khi nhấn nút "Chỉnh sửa"
        editProfileBtn.addEventListener('click', () => {
            // Ẩn phần hiển thị thông tin
            viewProfileInfo.classList.add('hidden');
            // Hiện form chỉnh sửa
            editProfileForm.classList.remove('hidden');
        });
    }

    if (cancelEditBtn && viewProfileInfo && editProfileForm) {
        // Bắt sự kiện khi nhấn nút "Hủy"
        cancelEditBtn.addEventListener('click', () => {
            // Hiện lại phần hiển thị thông tin
            viewProfileInfo.classList.remove('hidden');
            // Ẩn lại form chỉnh sửa
            editProfileForm.classList.add('hidden');
            // Bạn có thể thêm lệnh editProfileForm.reset() ở đây nếu muốn xóa các thay đổi chưa lưu
        });
    }
});
