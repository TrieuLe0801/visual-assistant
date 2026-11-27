# UI Plan — Studio ảnh AI

Last updated: 2026-11-27
Status: Studio redesign implemented in frontend

## Navigation and screens

- Auth screen: đăng nhập bằng email/mật khẩu. Form đăng ký chỉ hiện khi server
  bật `REGISTRATION_ENABLED`.
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

## Temporary registration pause — 2026-11-10

- Hide the registration tab while the server reports registration disabled.
- Keep the login form available for existing accounts.

## Visual refresh — 2026-11-23

- Keep image content as the visual focus: three-column desktop gallery, two-column tablet gallery, and two-column phone gallery with larger thumbnails and clearer metadata.
- Use warmer neutral surfaces, translucent navigation chrome, restrained green gradient actions, and editorial headline sizing. This follows current bold typography and human, organic visual direction without adding decorative content to the workflow.
- Keep primary controls at least 44px high, visible keyboard focus, readable prompt text, and reduced-motion handling. Layout remains usable at 320px without horizontal overflow.
- Research references: [Figma web design trends](https://www.figma.com/resource-library/web-design-trends/), [Adobe Creative Trends 2026](https://business.adobe.com/uk/resources/creative-trends-report.html), and [WCAG 2.2](https://www.w3.org/TR/WCAG22/).
- Browser automation could not attach to the local app host in this session; HTTP availability and production build remain separate evidence.

## Studio redesign — 2026-11-24

Coding goal: make the existing studio feel like a calm editorial workspace.
The library now gives image scanning more space, the create view gives the
prompt one clear stage, and detail keeps source, status and next actions close
to the selected image. The redesign uses warm neutral surfaces, deep green
actions, pill controls and restrained depth. It keeps existing React/CSS
architecture and all API behavior.

Research applied: Figma's 2026 web report emphasizes immediacy and fluid
product flow; Adobe's 2026 forecast emphasizes human, sensory and authentic
visual work; WCAG 2.2 remains the accessibility baseline. Sources:
[Figma](https://www.figma.com/resource-library/web-development-trends/),
[Adobe](https://business.adobe.com/uk/resources/creative-trends-report.html),
[WCAG 2.2](https://www.w3.org/TR/WCAG22/).

Acceptance mapping:

- Auth, registration gating and errors: achieved; JSX behavior unchanged,
  panel hierarchy and focus treatment refreshed.
- Library image-first scan, CTA, loading/empty/error states: achieved; cards,
  spacing and toolbar hierarchy refreshed.
- Create prompt and 1–6 selector with per-image progress: achieved; prompt
  stage enlarged and selector remains the only user generation choice.
- Detail metadata, download, delete, edit, variation and related history:
  achieved; image and action hierarchy refreshed.
- Keyboard focus, touch targets, reduced motion and 320px reflow: achieved in
  CSS; browser verification remains required.
- Stored-output success and server-controlled provider settings: achieved by
  preserving existing handlers and API contracts; no backend changes.

### Library rediscovery — 2026-11-24 correction

The library now has a client-side prompt search and status filter for all,
completed, processing and failed records. Filtering happens on loaded records,
so retry/loading behavior and owner-scoped API calls remain unchanged. A
distinct no-match state avoids confusing an empty account with a filtered
result. Controls retain accessible labels and stack at 320px.

## Version groups — 2026-11-27

- Library presents one card per image lineage. Card shows newest version and
  version count; prompt search and status filtering inspect every version.
- Detail includes keyboard-friendly chronological V1/V2 selector with current
  selection, status and timestamp. Each version keeps prompt, download,
  edit/variation source and delete action.
- Deleting selected version moves selection to another version in same lineage;
  deleting final version returns to library. Storage remains one file per result.

## Progress and action clarity — 2026-11-27

- Create 1–6 now runs up to two requests concurrently and reports completed
  attempts, successful stored images and active requests. Active requests use
  an indeterminate sweep;
  the UI does not invent provider phases or percentage progress.
- Edit and variation show an explicit saving state, lock duplicate submits and
  keep the selected version as source. Create/edit/variation/download controls
  use stronger visual hierarchy and task-specific labels; delete remains a
  separate destructive action.
- After generation requests settle, the UI labels the library refresh phase
  while it reloads stored results.
