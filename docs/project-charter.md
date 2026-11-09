# Studio ảnh AI — Product Charter

Ngày cập nhật: 2026-11-09
Trạng thái: MVP scope đã chốt

## Mục tiêu

Xây webapp cá nhân để người dùng tạo ảnh từ prompt, chỉnh sửa ảnh đã lưu bằng
prompt, tạo biến thể và mở lại ảnh cùng lịch sử prompt trong thư viện riêng.

## Người dùng và luồng chính

1. Người dùng đăng ký hoặc đăng nhập bằng email và mật khẩu.
2. Người dùng nhập prompt để tạo ảnh mới.
3. App lưu ảnh, prompt, trạng thái và metadata vào thư viện của tài khoản.
4. Người dùng mở ảnh đã lưu, nhập prompt để chỉnh ảnh hoặc tạo biến thể.
5. App lưu mỗi kết quả thành một mục lịch sử có quan hệ tới ảnh nguồn.
6. Người dùng có thể xem lại prompt, trạng thái, thời gian tạo và tải ảnh.
7. Sau khi đăng xuất, mở phiên khác hoặc khởi động lại app, người dùng đăng
   nhập lại và tiếp tục xem thư viện của mình.

## Yêu cầu chức năng

- Đăng ký, đăng nhập và đăng xuất bằng email và mật khẩu.
- Tạo ảnh mới từ prompt văn bản.
- Nhận prompt tiếng Việt; model ngôn ngữ được cấu hình ở server hiểu và diễn
  đạt yêu cầu cho model ảnh. Lưu prompt gốc do người dùng nhập.
- Chỉnh sửa ảnh đã lưu bằng prompt.
- Tạo biến thể từ ảnh đã lưu; prompt hướng dẫn biến thể là không bắt buộc.
- Hiển thị thư viện riêng, trang chi tiết, prompt, trạng thái, quan hệ ảnh gốc
  và ảnh dẫn xuất, cùng liên kết tải ảnh.
- Lưu ảnh trên local volume; lưu tài khoản, prompt, metadata, trạng thái thao
  tác và quan hệ ảnh trong SQLite.
- Giới hạn mọi truy vấn ảnh và tệp theo chủ sở hữu.
- Cấu hình provider mặc định ở phía máy chủ qua biến môi trường. Giao diện
  người dùng không cho chọn provider, model, kích thước, tỉ lệ, số lượng hoặc
  tham số ảnh.
- Hỗ trợ OpenAI API và endpoint model tự host tương thích với hợp đồng API ảnh
  đã chọn. Provider thiếu thao tác phải trả lỗi rõ ràng.

## Product invariants

- Ảnh, prompt và metadata chỉ xuất hiện trong thư viện đúng tài khoản.
- Ảnh không được báo thành công nếu provider trả lỗi, phản hồi không có ảnh
  hợp lệ hoặc lưu tệp thất bại.
- Lỗi thao tác được lưu với trạng thái thất bại; lỗi không được che bằng ảnh
  nguồn hoặc ảnh trước đó.
- Ảnh dẫn xuất tham chiếu đúng ảnh nguồn; prompt lưu đúng với yêu cầu người
  dùng hoặc prompt mặc định được công bố cho biến thể không có hướng dẫn.
- API key, session secret và thông tin xác thực không lưu trong DB hoặc log.
- Không tải ảnh từ URL tùy ý do provider trả về; adapter nhận nội dung ảnh theo
  hợp đồng đã chọn và lưu vào local volume.
- Người dùng không tự thay đổi provider, model hoặc thông số sinh ảnh.

## Phạm vi MVP

- Một webapp responsive, giao diện tiếng Việt.
- Email và mật khẩu 10–128 ký tự; không có OAuth, quên mật khẩu hoặc vai trò
  admin trong UI.
- OpenAI image adapter và adapter endpoint OpenAI-compatible tự host.
- SQLite, local volume, lịch sử ảnh bền qua phiên và lần khởi động lại.
- Provider calls có thể chạy đồng bộ trong request ở MVP; giao diện báo trạng
  thái đang xử lý và lỗi rõ ràng.
- Automated tests dùng provider giả lập. Smoke test thật chạy riêng khi có
  credential và endpoint phù hợp.

## Ngoài phạm vi

- Chia sẻ ảnh, thanh toán, quota, moderation dashboard hoặc quản trị tài khoản.
- Người dùng tự chọn provider/model hoặc điều khiển kích thước, tỉ lệ, số lượng
  ảnh và thông số nâng cao.
- Công cụ chỉnh ảnh thủ công, upload ảnh tùy ý, chat, tạo nhóm hoặc album.
- Triển khai nhiều máy, object storage hoặc cam kết backup/khôi phục dữ liệu.

## Tình huống nghiệm thu

1. Người dùng đăng ký, đăng nhập và đăng xuất được; mật khẩu không được lưu
   dưới dạng rõ.
2. Tạo ảnh thành công lưu được file, prompt, provider/model metadata, trạng thái
   và thời điểm; ảnh xuất hiện trong đúng thư viện.
3. Chỉnh ảnh đã lưu dùng đúng tệp nguồn và prompt mới; kết quả ghi nhận ảnh
   nguồn và prompt chỉnh sửa.
4. Tạo biến thể dùng đúng tệp nguồn; prompt hướng dẫn được lưu hoặc prompt
   mặc định được ghi rõ trong lịch sử.
5. Người dùng mở ảnh chi tiết, xem prompt/trạng thái/quan hệ và tải tệp.
6. Người dùng A không đọc, tải, sửa hoặc tạo ảnh dựa trên ảnh của người dùng B.
7. Prompt và ảnh vẫn mở được sau khi đăng xuất, đăng nhập lại và khởi động lại
   app.
8. Mô tả tiếng Việt được model ngôn ngữ diễn đạt lại cho thao tác tạo, chỉnh sửa
   và tạo biến thể; thư viện vẫn hiển thị prompt gốc.
9. Thiếu credential, provider không khả dụng, model thiếu thao tác, phản hồi
   lỗi/không hợp lệ hoặc lưu tệp thất bại không được hiển thị như thành công.
10. Provider/model và tham số ảnh không xuất hiện như lựa chọn cho người dùng.
11. Offline tests bao phủ luồng chính và lỗi bằng provider giả lập. Live provider
    checks được ghi riêng, không suy ra từ offline tests.

## Giới hạn vận hành

Local volume phù hợp cho MVP một máy. Cần backup volume và SQLite theo chính
sách vận hành riêng. Triển khai nhiều instance hoặc yêu cầu độ bền cao cần
đánh giá object storage và chiến lược migration. Prompt được gửi tới cả model
ngôn ngữ diễn giải và provider tạo ảnh; mỗi dịch vụ xử lý dữ liệu theo điều
khoản tương ứng.
