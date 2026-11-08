# UI Plan — Studio ảnh AI

Last updated: 2026-11-08
Status: MVP interface

## Navigation and screens

- Auth screen: đăng nhập và đăng ký bằng email/mật khẩu.
- Thư viện: ảnh theo thứ tự mới nhất, trạng thái và prompt tóm tắt.
- Tạo ảnh: một prompt văn bản và nút tạo. Không có lựa chọn provider, model,
  tỉ lệ, kích thước hoặc số lượng ảnh.
- Chi tiết ảnh: ảnh, prompt đầy đủ, trạng thái, thời điểm, liên kết tải, ảnh
  nguồn/ảnh liên quan, form chỉnh sửa và form tạo biến thể.

## Behavior

- Hiển thị đang tải/đang xử lý và khóa nút khi có request đang chạy.
- Thành công chỉ hiện sau response đã lưu của server.
- Lỗi auth, provider, model capability, response hoặc storage được trình bày rõ;
  không render ảnh nguồn như kết quả vừa tạo.
- Khi người dùng chuyển giữa ảnh dẫn xuất, hiển thị prompt và quan hệ đúng.
- Logout xóa dữ liệu trên giao diện hiện tại. Login mới tải lại thư viện từ API.
- Responsive cho desktop và mobile; nhãn, trạng thái và form có accessible
  name, focus state, keyboard control.

## Verification targets

Kiểm tra đăng ký/đăng nhập, create, edit, variation, detail/download, owner
isolation, lỗi provider/storage, refresh/login lại và backend restart.
