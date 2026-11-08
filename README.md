# Atelier — Studio ảnh AI

Webapp tạo ảnh từ prompt, chỉnh ảnh đã lưu và tạo biến thể. Ảnh cùng prompt
được lưu trong thư viện riêng của tài khoản.

## MVP

- Đăng ký/đăng nhập bằng email và mật khẩu.
- Tạo ảnh mới, chỉnh sửa ảnh, tạo biến thể và mở lịch sử ảnh dẫn xuất.
- SQLite lưu tài khoản và metadata; local volume lưu tệp ảnh.
- FastAPI backend và React + TypeScript frontend.
- OpenAI API hoặc endpoint OpenAI-compatible tự host, cấu hình ở server.
- Giao diện không cho chọn provider/model hoặc thông số ảnh.

Xem [product charter](docs/project-charter.md),
[implementation plan](docs/implementation-plan.md) và
[ADR 0005](docs/adr/0005-ai-image-studio.md).

## Cấu hình

Sao chép `.env.example` thành `.env` rồi đặt session secret và thông tin
provider phù hợp. `.env` đã được Git ignore. Không đặt credential trong source,
database hoặc log.

- Provider OpenAI dùng `IMAGE_PROVIDER=openai` và `OPENAI_API_KEY`.
- Provider tự host dùng `IMAGE_PROVIDER=openai_compatible`,
  `IMAGE_API_BASE_URL`, `IMAGE_MODEL` và có thể đặt `IMAGE_API_KEY`.
- `IMAGE_STORAGE_DIR` và `APP_DATABASE_PATH` mặc định nằm trong `var/`.

Chi tiết biến môi trường: [.env.example](.env.example).

## Chạy local

Yêu cầu Python `>=3.10`, `uv`, Node.js và npm. Cài dependencies Python:

```bash
uv sync
```

Terminal 1 — backend:

```bash
uv run uvicorn image_studio.app:app --reload --app-dir src
```

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
- [Hồ sơ du lịch lịch sử](docs/archive/2026-10-14/README.md)
