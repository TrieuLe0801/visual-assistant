# Studio ảnh AI — Kế hoạch triển khai

Ngày cập nhật: 2026-11-09
Trạng thái: MVP implementation plan

## Kiến trúc

- Backend: FastAPI, typed request/response contracts và SQLite.
- Frontend: React + TypeScript + Vite; production build được phục vụ cùng
  origin bởi FastAPI, development dùng Vite proxy.
- Auth: email/password và session cookie HttpOnly có chữ ký.
- Lưu trữ: SQLite cho metadata, local volume cho ảnh.
- Provider: interface độc lập provider; OpenAI API và endpoint tự host tương
  thích với Images API contract đã chọn.
- Ngôn ngữ prompt: model ngôn ngữ riêng hiểu tiếng Việt và chuẩn hóa mô tả cho
  provider ảnh; lưu prompt gốc, không lưu bản diễn đạt lại.
- Admin cấu hình provider/model/credential/endpoint bằng biến môi trường ở
  backend, gồm `PROMPT_MODEL`, `PROMPT_API_BASE_URL` và `PROMPT_API_KEY` cho
  model ngôn ngữ. Giao diện không lộ lựa chọn này.

## Contracts và dữ liệu

`users` lưu ID, email chuẩn hóa, password hash và thời điểm tạo.

`images` lưu ID, chủ sở hữu, prompt, operation (`generate`, `edit`,
`variation`), status (`processing`, `succeeded`, `failed`), ID ảnh nguồn nếu
có, vị trí file, MIME type, provider/model metadata, lỗi đã làm sạch và thời
điểm tạo/cập nhật. Không lưu credential vào database.

`prompt` luôn là nội dung do người dùng nhập. Trước mỗi thao tác ảnh, prompt
được gửi tới model ngôn ngữ đã cấu hình để hiểu tiếng Việt và trả về chỉ dẫn
tiếng Anh cho image provider. Bản diễn đạt lại chỉ tồn tại trong request.

Các thao tác chính:

```text
POST /api/auth/register
POST /api/auth/login
POST /api/auth/logout
GET  /api/auth/me
GET  /api/images
GET  /api/images/{id}
GET  /api/images/{id}/file
POST /api/images/generate
DELETE /api/images/{id}
POST /api/images/{id}/edit
POST /api/images/{id}/variations
```

Mỗi truy vấn ảnh, ảnh nguồn và file phải kèm điều kiện owner ID lấy từ phiên
đã xác thực. Không dùng ID ảnh do client gửi làm bằng chứng sở hữu.

## Provider interface

Provider nhận prompt và, với thao tác sửa/biến thể, byte ảnh nguồn cùng MIME
type. Provider trả byte ảnh và metadata an toàn. App kiểm tra định dạng và
kích thước phản hồi trước khi lưu file.

`ImageService` gọi prompt enhancer trước adapter ảnh trong generation, edit và
variation. Nếu prompt enhancer lỗi thì operation được đánh dấu thất bại; không
gửi prompt gốc chưa xử lý sang image provider.

- `generate(prompt)` tạo ảnh mới.
- `edit(source, prompt)` chỉnh ảnh nguồn theo prompt.
- `variation(source, optional_prompt)` tạo biến thể. Provider có thể dùng API
  edit với hướng dẫn biến thể hoặc báo thao tác không hỗ trợ.
- Adapter không tải URL tùy ý từ upstream. Adapter không ghi token, prompt hoặc
  nội dung ảnh vào log.
- Lỗi upstream chuyển thành lỗi người dùng có thể hiểu; chi tiết credential,
  headers và response body không được trả cho client.
- Mỗi operation ghi `processing` trước khi gọi provider. Chỉ ghi `succeeded`
  sau khi ảnh hợp lệ đã được lưu và metadata cập nhật. Mọi failure ghi trạng
  thái `failed`.

## Bảo mật và quyền riêng tư

- Hash mật khẩu 10–128 ký tự bằng password hashing có salt; không lưu plaintext.
- Cookie phiên `HttpOnly`, `SameSite`, thời hạn hữu hạn; production bật
  `Secure` qua cấu hình.
- Kiểm tra quyền sở hữu trước khi trả metadata hoặc file.
- Mọi file name do server sinh; không dùng prompt, email hoặc ID client làm
  đường dẫn file.
- API key và session secret chỉ lấy từ environment/ignored `.env`; không lưu
  vào DB, response, trace hoặc log.
- Prompt được gửi đến model ngôn ngữ diễn giải và image provider; nội dung prompt
  không xuất hiện trong LangSmith trace.
- Giới hạn độ dài prompt và kích thước phản hồi ảnh; lỗi không tạo trạng thái
  thành công.

## Các bước

### 1. Backend, tài khoản và lưu trữ

Tạo typed contracts, SQLite schema, password/session auth, truy vấn owner-scoped,
local volume và endpoint thư viện/file. Hoàn tất khi tài khoản riêng biệt có
thể đăng nhập và không truy cập chéo ảnh.

### 2. Provider và thao tác ảnh

Thêm interface, OpenAI adapter, adapter OpenAI-compatible, generation/edit/
variation, trạng thái thao tác và xử lý lỗi. Hoàn tất khi fake provider chứng
minh flow thành công, thất bại, khả năng không hỗ trợ và lỗi file storage.

### 3. Giao diện và kiểm chứng

Tạo giao diện đăng nhập, thư viện, chi tiết, prompt creation, edit và variation.
Build production vào backend static serving. Hoàn tất khi chạy end-to-end bằng
provider giả lập, lịch sử bền qua login/restart, kiểm tra isolation và ghi rõ
kết quả live provider test hoặc trạng thái chưa chạy.

## Cấu hình dự kiến

```dotenv
IMAGE_PROVIDER=openai
IMAGE_MODEL=gpt-image-2.5-sunburst
PROMPT_MODEL=gpt-6-luna
PROMPT_API_BASE_URL=https://api.openai.com/v1
PROMPT_API_KEY=
PROMPT_TIMEOUT_SECONDS=30
OPENAI_API_KEY=
OPENAI_BASE_URL=https://api.openai.com/v1
IMAGE_API_BASE_URL=http://127.0.0.1:8001/v1
IMAGE_API_KEY=
SESSION_SECRET=development-only-change-this-session-secret
SESSION_TTL_SECONDS=1209600
SESSION_COOKIE_SECURE=false
IMAGE_DATABASE_PATH=var/image-studio.db
IMAGE_STORAGE_PATH=var/images
IMAGE_PROVIDER_TIMEOUT_SECONDS=180
FRONTEND_DIST_PATH=frontend/dist
```

Với `IMAGE_PROVIDER=openai`, app dùng API chính thức và `OPENAI_API_KEY`.
`OPENAI_BASE_URL` cho phép override endpoint. Với
`IMAGE_PROVIDER=openai_compatible`, app dùng `IMAGE_MODEL`,
`IMAGE_API_BASE_URL` và optional `IMAGE_API_KEY`. Đổi `SESSION_SECRET` trước
khi deploy ngoài môi trường phát triển. Prompt model chỉ dùng lại
`OPENAI_API_KEY` khi endpoint prompt trùng `OPENAI_BASE_URL`; endpoint riêng
dùng `PROMPT_API_KEY`. Danh sách active nằm trong `.env.example`.

## Cách chạy local

```bash
uv sync
uv run uvicorn image_studio.app:app --reload --app-dir src
```

Trong terminal khác:

```bash
cd frontend
npm ci
npm run dev
```

Vite proxy `/api` đến backend. Production frontend dùng `npm run build`; FastAPI
phục vụ `frontend/dist` khi thư mục tồn tại.

## Giới hạn

Provider APIs có thể khác nhau về hỗ trợ edit/variation, định dạng và model.
Adapter contract, không phải UI, xử lý khác biệt. Smoke tests thật yêu cầu
credential và model phù hợp. SQLite/local volume chưa cung cấp backup hoặc
multi-host coordination. Synchronous provider calls giữ MVP đơn giản nhưng
request có thể kéo dài; tiền xử lý prompt thêm một lượt gọi model, latency và
chi phí. Queue là phương án mở rộng sau này.
