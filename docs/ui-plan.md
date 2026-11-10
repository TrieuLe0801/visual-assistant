# UI Plan — Studio ảnh AI

Last updated: 2026-11-09
Status: MVP interface

## Navigation and screens

- Auth screen: đăng nhập và đăng ký bằng email/mật khẩu.
- Thư viện: ảnh theo thứ tự mới nhất, trạng thái và prompt tóm tắt.
- Tạo ảnh: một prompt văn bản, hỗ trợ mô tả bằng tiếng Việt, và nút tạo. Không
  chỉ có lựa chọn số lượng 1–6 ảnh; không có lựa chọn provider, model, tỉ lệ,
  kích thước hoặc tham số ảnh khác.
- Chi tiết ảnh: ảnh, prompt đầy đủ, trạng thái, thời điểm, liên kết tải, ảnh
  nguồn/ảnh liên quan, form chỉnh sửa và form tạo biến thể.

## Behavior

- Hiển thị đang tải/đang xử lý và khóa nút khi có request đang chạy.
- Giữ prompt gốc trong lịch sử; model ngôn ngữ diễn đạt yêu cầu cho model ảnh.
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

## UX refinement — 2026-11-09

- Giữ giao diện xanh trung tính hiện có; tăng cỡ chữ nội dung, độ tương phản,
  kích thước vùng bấm và focus ring. Tôn trọng `prefers-reduced-motion`.
- Mobile dùng điều hướng dưới màn hình có nhãn cho thư viện, tạo ảnh và đăng
  xuất. Chừa khoảng trống để nội dung không bị thanh điều hướng che.
- Lỗi tải thư viện có nút thử lại. Lỗi tạo ảnh giữ prompt đã nhập và hiện thông
  báo tiếng Việt cho các lỗi API thường gặp. Trạng thái đang xử lý phân biệt
  chỉnh sửa với biến thể.
- Các phản hồi thư viện hoặc tạo ảnh thuộc phiên đã đăng xuất không được đưa
  vào giao diện của phiên tiếp theo.
