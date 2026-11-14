# Atelier — Studio ảnh AI

Webapp tạo ảnh từ prompt, chỉnh ảnh đã lưu và tạo biến thể. Ảnh cùng prompt
được lưu trong thư viện riêng của tài khoản.

## MVP

- Đăng nhập bằng email và mật khẩu. Đăng ký tài khoản mới đang tạm tắt; chỉ
  các tài khoản đã có trong hệ thống đăng nhập được.
- Tạo 1–6 ảnh từ một prompt, chỉnh sửa ảnh, tạo biến thể, xóa ảnh và mở lịch
  sử ảnh dẫn xuất.
- SQLite lưu tài khoản và metadata; local volume lưu tệp ảnh.
- FastAPI backend và React + TypeScript frontend.
- OpenAI API hoặc endpoint OpenAI-compatible tự host, cấu hình ở server.
- Mô tả tiếng Việt được model ngôn ngữ phía server hiểu và chuyển thành chỉ
  dẫn cho model tạo ảnh; lịch sử vẫn lưu mô tả gốc.
- Giao diện không cho chọn provider/model hoặc thông số ảnh.

Xem [product charter](docs/project-charter.md),
[implementation plan](docs/implementation-plan.md) và
[ADR 0005](docs/adr/0005-ai-image-studio.md).

## Cấu hình

Sao chép `.env.example` thành `.env` rồi đặt session secret và thông tin
provider phù hợp. `.env` đã được Git ignore. Không đặt credential trong source,
database hoặc log.

Đăng ký bị khóa mặc định bằng `REGISTRATION_ENABLED=false` ở cả giao diện và
API. Đặt `true` trong `.env` để mở lại trang và API đăng ký.

- Provider OpenAI dùng `IMAGE_PROVIDER=openai` và `OPENAI_API_KEY`.
- Provider tự host dùng `IMAGE_PROVIDER=openai_compatible`,
  `IMAGE_API_BASE_URL`, `IMAGE_MODEL` và có thể đặt `IMAGE_API_KEY`.
- Model hiểu prompt dùng `PROMPT_MODEL`, `PROMPT_API_BASE_URL` và
  `PROMPT_API_KEY`. Mặc định là `gpt-6-luna` qua OpenAI Chat Completions;
  nếu endpoint prompt trùng `OPENAI_BASE_URL`, khóa `PROMPT_API_KEY` để trống
  sẽ dùng `OPENAI_API_KEY`. Endpoint tự host riêng dùng khóa `PROMPT_API_KEY`
  của endpoint đó, hoặc để trống nếu endpoint không yêu cầu khóa.
- `IMAGE_STORAGE_PATH` và `IMAGE_DATABASE_PATH` mặc định nằm trong `var/`.

Server gửi mô tả tới model ngôn ngữ để hiểu yêu cầu tiếng Việt, rồi gửi prompt
được diễn đạt lại tới model tạo ảnh. Mô tả gốc vẫn hiển thị và được lưu trong
thư viện. Vì có thêm một lần gọi model, tạo ảnh có thể tốn thêm thời gian và chi
phí. Nếu model ngôn ngữ lỗi hoặc thiếu credential, thao tác báo lỗi thay vì gửi
mô tả tiếng Việt thô sang model ảnh. Khóa và endpoint cần được cấu hình trước
khi chạy; xem [.env.example](.env.example).

Để quản lý nhiều model, đặt `IMAGE_MODEL_CATALOG` thành JSON ánh xạ alias tới
`provider` và `model`, rồi đặt `IMAGE_ACTIVE_MODEL` bằng alias cần chạy. Ví dụ:

```env
IMAGE_MODEL_CATALOG={"cloud":{"provider":"openai","model":"gpt-image-1"},"local":{"provider":"openai_compatible","model":"local-image-model"}}
IMAGE_ACTIVE_MODEL=local
```

LangChain Core chọn model trong catalog cho cả tạo, chỉnh sửa và biến thể.
Ứng dụng đọc cấu hình khi khởi động; đổi alias cần khởi động lại backend.
Endpoint và credential vẫn lấy từ `OPENAI_BASE_URL`/`OPENAI_API_KEY` hoặc
`IMAGE_API_BASE_URL`/`IMAGE_API_KEY`. Model thiếu thao tác trả lỗi rõ ràng.
Không có API hoặc giao diện để người dùng chọn model.

Để bật LangSmith, đặt `LANGSMITH_TRACING=true`, `LANGSMITH_API_KEY` và
`LANGSMITH_PROJECT` trong `.env` bị ignore hoặc secret store của môi trường
triển khai. Trace chứa operation, trạng thái, ID ảnh, provider và model;
không chứa prompt, ảnh nguồn hoặc ảnh kết quả. Nếu không cấu hình, tracing tắt.
Chưa có xác nhận gửi trace thật tới LangSmith; test hiện tại chỉ kiểm tra
trace cục bộ, không gọi mạng.

Chi tiết biến môi trường: [.env.example](.env.example).

## Cấu trúc backend

- `src/image_studio/app.py`: route FastAPI, xác thực request và ánh xạ response.
- `src/image_studio/ai/`: hợp đồng provider, adapter OpenAI-compatible, factory
  và service điều phối thao tác ảnh. `model_router.py` dùng LangChain Core để
  chọn model phía server.
- `src/image_studio/database/settings.py`: cấu hình SQLite từ môi trường.
- `src/image_studio/database/connection.py`: kết nối và transaction SQLite.
- `src/image_studio/database/models.py`, `schema.py`, `repository.py`: bản ghi,
  schema và truy vấn dữ liệu theo chủ sở hữu.
- `src/image_studio/storage.py`: lưu tệp ảnh trên local volume.
- `src/image_studio/utils/`: session và mật khẩu, kiểm tra ảnh, thời gian UTC.

## Chạy local

Yêu cầu Python `>=3.11`, `uv`, Node.js và npm. Cài dependencies Python:

```bash
uv sync
```

Terminal 1 — backend:

```bash
uv run uvicorn image_studio.app:create_app --factory --reload --app-dir src
```

Set a unique `SESSION_SECRET` in an ignored `.env` before starting the backend.
For local HTTP only, also set `SESSION_COOKIE_SECURE=false`. Docker Compose uses
its existing `.secrets/session_secret` file and Secure cookies.

Terminal 2 — frontend:

```bash
cd frontend
npm ci
npm run dev
```

Mở địa chỉ Vite in ra terminal. Vite chuyển `/api` đến backend ở
`http://127.0.0.1:8000`.

Build frontend production bằng `cd frontend && npm ci && npm run build`. FastAPI
phục vụ `frontend/dist` khi build tồn tại.

## Docker Compose và Cloudflare Tunnel

Dockerfile tạo image backend và frontend. Compose chạy container `database`
để khởi tạo SQLite rồi thoát, backend FastAPI và frontend Nginx. SQLite/ảnh
nằm trong một Docker volume; cổng frontend mặc định `8088` chỉ mở trên localhost.
Đặt `FRONTEND_PORT` trong `.env` để đổi port nếu cần. Named Cloudflare Tunnel
chạy trong container riêng khi bật profile `publish`, phục vụ `aliter.app`.
Token connector nằm trong file bị ignore `.secrets/cloudflare_tunnel_token`.

Chạy `python3 scripts/init-deployment-secrets.py`, rồi
`docker compose build app frontend` và `docker compose up -d --wait`.
Sau đó chạy `docker compose --profile publish up -d cloudflared` và kiểm tra
`https://aliter.app/api/health`. Domain công khai trang đăng nhập nếu chưa có
chính sách Cloudflare Access; app vẫn yêu cầu đăng nhập.

Xem [hướng dẫn triển khai, backup và restore](docs/deployment-compose-cloudflare.md).
Không nhập credentials vào source hay Compose file.

## Kiểm tra

```bash
uv run pytest
uv run isort --check-only . .codex/hooks/format_python.py
uv run black --check . .codex/hooks/format_python.py
uv run flake8 . .codex/hooks/format_python.py
uv run ruff check . .codex/hooks/format_python.py
cd frontend && npm ci && npm run build
```

Unit tests dùng provider giả lập và không gọi mạng/model. Live test cần
credential thật và provider endpoint đang hoạt động; kết quả được ghi riêng.

## Hồ sơ dự án

- [Trạng thái](PROJECT_STATUS.md)
- [Roadmap](docs/roadmap.html) và [progress JSON](docs/progress/roadmap-progress.json)
- [UI plan](docs/ui-plan.md)
- [Learning log hiện tại](docs/learning-log/2026-11-08-image-studio.md)
- [Codex workflow](docs/codex-workflow.md)
- [Compose + Cloudflare Tunnel deployment](docs/deployment-compose-cloudflare.md)
- [Hồ sơ du lịch lịch sử](docs/archive/2026-10-14/README.md)
