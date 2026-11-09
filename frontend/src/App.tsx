import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { FormEvent } from "react";

type User = { id: number | string; email: string };
type ImageRecord = {
  id: number | string;
  prompt: string;
  operation: "generate" | "edit" | "variation";
  status: "processing" | "succeeded" | "failed";
  parent_id: number | string | null;
  mime_type: string | null;
  created_at: string;
  error?: string | null;
};
type View = "library" | "create" | "detail";

const errorMessages: Record<string, string> = {
  "An account with this email already exists.": "Email này đã có tài khoản. Hãy đăng nhập.",
  "Email or password is incorrect.": "Email hoặc mật khẩu không đúng. Vui lòng thử lại.",
  "Enter a valid email address.": "Vui lòng nhập địa chỉ email hợp lệ.",
  "Password must contain between 10 and 128 characters.": "Mật khẩu cần từ 10 đến 128 ký tự.",
  "Image provider credentials are not configured.": "Hệ thống tạo ảnh chưa được cấu hình. Vui lòng liên hệ quản trị viên.",
  "Image provider URL is not configured.": "Hệ thống tạo ảnh chưa được cấu hình. Vui lòng liên hệ quản trị viên.",
  "Image provider timed out.": "Hệ thống tạo ảnh phản hồi quá lâu. Vui lòng thử lại.",
  "Image provider is unavailable.": "Hệ thống tạo ảnh hiện không khả dụng. Vui lòng thử lại sau.",
  "Image provider is temporarily unavailable.": "Hệ thống tạo ảnh tạm thời gián đoạn. Vui lòng thử lại sau.",
  "Image provider is rate limited. Try again later.": "Hệ thống tạo ảnh đang quá tải. Vui lòng thử lại sau.",
  "Image provider rejected this prompt or source image.": "Hệ thống từ chối prompt hoặc ảnh nguồn. Hãy chỉnh nội dung rồi thử lại.",
  "Image provider rejected its configured credentials.": "Hệ thống tạo ảnh bị lỗi cấu hình xác thực. Vui lòng liên hệ quản trị viên.",
  "Configured image provider does not support image edits.": "Hệ thống hiện không hỗ trợ chỉnh sửa ảnh.",
  "Configured image provider does not support editing.": "Hệ thống hiện không hỗ trợ chỉnh sửa ảnh.",
  "Configured image provider does not support variations.": "Hệ thống hiện không hỗ trợ tạo biến thể.",
  "Source image is unavailable.": "Ảnh nguồn hiện không khả dụng.",
  "Image storage is unavailable.": "Không lưu được ảnh. Vui lòng thử lại sau.",
  "Image was not found.": "Ảnh không còn trong thư viện.",
  "An image being created cannot be deleted.": "Ảnh đang được tạo. Hãy thử xóa sau.",
};

function displayError(message: string): string {
  return errorMessages[message] ?? message;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    credentials: "same-origin",
    ...init,
    headers: {
      ...(init?.body ? { "Content-Type": "application/json" } : {}),
      ...init?.headers,
    },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const detail = body?.detail;
    throw new Error(
      typeof detail === "string"
        ? displayError(detail)
        : `Yêu cầu chưa thành công (${response.status}). Vui lòng thử lại.`,
    );
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

function imageFile(id: ImageRecord["id"]): string {
  return `/api/images/${encodeURIComponent(String(id))}/file`;
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("vi-VN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function App() {
  const [user, setUser] = useState<User | null>(null);
  const [authReady, setAuthReady] = useState(false);
  const [images, setImages] = useState<ImageRecord[]>([]);
  const [view, setView] = useState<View>("library");
  const [selectedId, setSelectedId] = useState<ImageRecord["id"] | null>(null);
  const [loadingImages, setLoadingImages] = useState(false);
  const [libraryError, setLibraryError] = useState("");
  const [working, setWorking] = useState(false);
  const [workingAction, setWorkingAction] = useState<"edit" | "variations" | null>(null);
  const [error, setError] = useState("");
  const [authMode, setAuthMode] = useState<"login" | "register">("login");
  const [prompt, setPrompt] = useState("");
  const [imageCount, setImageCount] = useState(1);
  const [completedCount, setCompletedCount] = useState(0);
  const [editPrompt, setEditPrompt] = useState("");
  const [variationPrompt, setVariationPrompt] = useState("");
  const sessionVersion = useRef(0);
  const loadVersion = useRef(0);

  const selected = useMemo(
    () => images.find((image) => String(image.id) === String(selectedId)) ?? null,
    [images, selectedId],
  );
  const related = useMemo(
    () =>
      selected
        ? images.filter(
            (image) =>
              String(image.parent_id) === String(selected.id) ||
              String(selected.parent_id) === String(image.id),
          )
        : [],
    [images, selected],
  );

  const loadImages = useCallback(async () => {
    const session = sessionVersion.current;
    const load = ++loadVersion.current;
    setLoadingImages(true);
    try {
      const result = await request<ImageRecord[]>('/api/images');
      if (sessionVersion.current !== session || loadVersion.current !== load) return;
      setImages(result);
      setLibraryError("");
    } catch (cause) {
      if (sessionVersion.current !== session || loadVersion.current !== load) return;
      setLibraryError(cause instanceof Error ? cause.message : "Không tải được thư viện ảnh.");
    } finally {
      if (sessionVersion.current === session && loadVersion.current === load) {
        setLoadingImages(false);
      }
    }
  }, []);

  useEffect(() => {
    request<User | { user: User }>("/api/auth/me")
      .then((result) => setUser("user" in result ? result.user : result))
      .catch(() => setUser(null))
      .finally(() => setAuthReady(true));
  }, []);

  useEffect(() => {
    if (user) void loadImages();
  }, [user, loadImages]);

  async function authenticate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    const form = new FormData(event.currentTarget);
    const email = String(form.get("email") ?? "").trim();
    const password = String(form.get("password") ?? "");
    setWorking(true);
    try {
      const result = await request<User | { user: User }>(`/api/auth/${authMode === "login" ? "login" : "register"}`, {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      sessionVersion.current += 1;
      setUser("user" in result ? result.user : result);
      setView("library");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Không thể đăng nhập.");
    } finally {
      setWorking(false);
    }
  }

  async function signOut() {
    setError("");
    try {
      await request("/api/auth/logout", { method: "POST" });
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Không thể đăng xuất.");
      return;
    }
    sessionVersion.current += 1;
    loadVersion.current += 1;
    setUser(null);
    setImages([]);
    setLibraryError("");
    setLoadingImages(false);
    setWorking(false);
    setWorkingAction(null);
    setSelectedId(null);
    setView("library");
  }

  async function createImage(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const value = prompt.trim();
    if (!value) return;
    setError("");
    setCompletedCount(0);
    setWorking(true);
    const session = sessionVersion.current;
    try {
      const created: ImageRecord[] = [];
      let firstError = "";
      for (let index = 0; index < imageCount; index += 1) {
        try {
          const image = await request<ImageRecord>("/api/images/generate", {
            method: "POST",
            body: JSON.stringify({ prompt: value }),
          });
          if (sessionVersion.current !== session) return;
          created.push(image);
          setImages((current) => [image, ...current.filter((item) => String(item.id) !== String(image.id))]);
        } catch (cause) {
          if (sessionVersion.current !== session) return;
          if (!firstError) firstError = cause instanceof Error ? cause.message : "Tạo ảnh thất bại.";
        }
        setCompletedCount(index + 1);
      }
      await loadImages();
      if (sessionVersion.current !== session) return;
      if (created.length > 0) {
        setSelectedId(created[0].id);
        setPrompt("");
        setView(imageCount === 1 ? "detail" : "library");
      }
      if (created.length !== imageCount) {
        setError(`${created.length}/${imageCount} ảnh đã tạo. ${firstError}`);
        setView("library");
      }
    } catch (cause) {
      if (sessionVersion.current !== session) return;
      await loadImages();
      if (sessionVersion.current !== session) return;
      setError(cause instanceof Error ? cause.message : "Tạo ảnh thất bại.");
    } finally {
      if (sessionVersion.current === session) setWorking(false);
    }
  }

  async function deleteImage(image: ImageRecord) {
    if (!window.confirm("Xóa ảnh này khỏi thư viện? Thao tác không thể hoàn tác.")) return;
    setError("");
    setWorking(true);
    const session = sessionVersion.current;
    try {
      await request<void>(`/api/images/${encodeURIComponent(String(image.id))}`, { method: "DELETE" });
      if (sessionVersion.current !== session) return;
      setImages((current) => current.filter((item) => String(item.id) !== String(image.id)));
      if (String(selectedId) === String(image.id)) {
        setSelectedId(null);
        setView("library");
      }
    } catch (cause) {
      if (sessionVersion.current !== session) return;
      setError(cause instanceof Error ? cause.message : "Không xóa được ảnh.");
    } finally {
      if (sessionVersion.current === session) setWorking(false);
    }
  }

  async function createDerived(
    event: FormEvent<HTMLFormElement>,
    operation: "edit" | "variations",
  ) {
    event.preventDefault();
    if (!selected) return;
    const value = (operation === "edit" ? editPrompt : variationPrompt).trim();
    if (operation === "edit" && !value) return;
    setError("");
    setWorking(true);
    setWorkingAction(operation);
    const session = sessionVersion.current;
    try {
      const created = await request<ImageRecord>(
        `/api/images/${encodeURIComponent(String(selected.id))}/${operation}`,
        {
          method: "POST",
          body: JSON.stringify({ prompt: value || undefined }),
        },
      );
      if (sessionVersion.current !== session) return;
      setImages((current) => [created, ...current.filter((image) => String(image.id) !== String(created.id))]);
      await loadImages();
      if (sessionVersion.current !== session) return;
      setSelectedId(created.id);
      setEditPrompt("");
      setVariationPrompt("");
    } catch (cause) {
      if (sessionVersion.current !== session) return;
      await loadImages();
      if (sessionVersion.current !== session) return;
      setError(cause instanceof Error ? cause.message : "Không xử lý được ảnh.");
    } finally {
      if (sessionVersion.current === session) {
        setWorking(false);
        setWorkingAction(null);
      }
    }
  }

  function openDetail(image: ImageRecord) {
    setSelectedId(image.id);
    setEditPrompt("");
    setVariationPrompt("");
    setError("");
    setView("detail");
  }

  if (!authReady) {
    return <main className="boot-screen"><span className="loader" />Đang mở Studio…</main>;
  }

  if (!user) {
    return (
      <main className="auth-screen">
        <div className="auth-art" aria-hidden="true">
          <div className="art-orbit orbit-one" />
          <div className="art-orbit orbit-two" />
          <div className="art-sun" />
          <span className="art-caption">Hình dung điều bạn muốn tạo.</span>
        </div>
        <section className="auth-panel">
          <Brand />
          <div className="auth-copy">
            <p className="eyebrow">KHÔNG GIAN SÁNG TẠO CỦA BẠN</p>
            <h1>{authMode === "login" ? "Chào mừng trở lại." : "Bắt đầu sáng tạo."}</h1>
            <p>Biến ý tưởng thành hình ảnh. Mỗi tác phẩm và prompt được lưu trong thư viện riêng của bạn.</p>
          </div>
          <div className="auth-tabs" role="group" aria-label="Chọn hình thức tài khoản">
            <button type="button" className={authMode === "login" ? "active" : ""} onClick={() => { setAuthMode("login"); setError(""); }} aria-pressed={authMode === "login"}>Đăng nhập</button>
            <button type="button" className={authMode === "register" ? "active" : ""} onClick={() => { setAuthMode("register"); setError(""); }} aria-pressed={authMode === "register"}>Tạo tài khoản</button>
          </div>
          <form className="auth-form" onSubmit={authenticate}>
            <label>Email<input autoComplete="email" name="email" type="email" placeholder="ban@email.com" required maxLength={254} /></label>
            <label>Mật khẩu<input autoComplete={authMode === "login" ? "current-password" : "new-password"} name="password" type="password" placeholder="Tối thiểu 10 ký tự" required minLength={10} maxLength={128} /></label>
            {error && <p className="alert error" role="alert">{error}</p>}
            <button className="button primary full" type="submit" disabled={working}>{working ? "Đang xử lý…" : authMode === "login" ? "Đăng nhập" : "Tạo tài khoản"}<span aria-hidden="true">↗</span></button>
          </form>
          <p className="auth-footnote">Tài khoản của bạn chỉ truy cập được ảnh do chính bạn tạo.</p>
        </section>
      </main>
    );
  }

  return (
    <div className="app-shell">
      <aside className="sidebar" aria-label="Điều hướng chính">
        <Brand />
        <button className={`nav-item ${view === "library" || view === "detail" ? "selected" : ""}`} aria-current={view === "library" || view === "detail" ? "page" : undefined} onClick={() => { setView("library"); setError(""); }}>
          <span className="nav-icon grid-icon" aria-hidden="true" />Thư viện
          <span className="nav-count">{images.filter((image) => image.status === "succeeded").length}</span>
        </button>
        <button className={`nav-item ${view === "create" ? "selected" : ""}`} aria-current={view === "create" ? "page" : undefined} onClick={() => { setView("create"); setError(""); }}>
          <span className="nav-icon plus-icon" aria-hidden="true">＋</span>Tạo hình ảnh
        </button>
        <div className="sidebar-bottom">
          <div className="privacy-card"><span className="privacy-mark">✳</span><div><strong>Riêng tư theo thiết kế</strong><p>Chỉ bạn xem được thư viện này.</p></div></div>
          <div className="account-row"><span className="avatar">{user.email.slice(0, 1).toUpperCase()}</span><span className="account-email" title={user.email}>{user.email}</span><button className="icon-button" aria-label="Đăng xuất" title="Đăng xuất" onClick={() => void signOut()}><span aria-hidden="true">⇥</span><span className="mobile-sign-out-label">Đăng xuất</span></button></div>
        </div>
      </aside>

      <main className="main-area">
        <header className="topbar">
          <div className="mobile-brand"><Brand /></div>
          <div className="breadcrumb"><span>Không gian</span><span className="crumb-sep">/</span><strong>{view === "detail" ? "Chi tiết hình ảnh" : view === "create" ? "Tạo hình ảnh" : "Thư viện"}</strong></div>
          <div className="topbar-right"><span className="status-dot" />Thư viện riêng tư</div>
        </header>

        {error && <div className="global-alert alert error" role="alert"><span>{error}</span><button aria-label="Đóng thông báo" onClick={() => setError("")}>×</button></div>}

        {view === "library" && (
          <section className="page-content" aria-busy={loadingImages}>
            <div className="page-heading heading-row">
              <div><p className="eyebrow">GÓC SÁNG TẠO CỦA BẠN</p><h1>Thư viện hình ảnh</h1><p className="subheading">Tất cả hình ảnh và ý tưởng của bạn, ở cùng một nơi.</p></div>
              <button className="button primary" onClick={() => { setView("create"); setError(""); }}>＋ Tạo hình ảnh mới</button>
            </div>
            <div className="library-meta"><span>{images.filter((image) => image.status === "succeeded").length} tác phẩm</span><span className="sort-label">Mới nhất trước</span></div>
            {loadingImages && !images.length ? <div className="loading-state" role="status"><span className="loader" />Đang tải thư viện…</div> : libraryError && !images.length ? (
              <div className="library-error" role="alert"><h2>Chưa tải được thư viện</h2><p>{libraryError}</p><button className="button secondary" onClick={() => void loadImages()}>Thử tải lại</button></div>
            ) : images.length ? (
              <div className="image-grid">
                {images.map((image, index) => <ImageCard key={image.id} image={image} index={index} onOpen={() => openDetail(image)} onDelete={() => void deleteImage(image)} disabled={working} />)}
              </div>
            ) : <EmptyLibrary onCreate={() => setView("create")} />}
            {libraryError && images.length > 0 && <div className="library-retry" role="alert"><span>Chưa cập nhật được thư viện: {libraryError}</span><button className="button secondary" onClick={() => void loadImages()}>Thử lại</button></div>}
          </section>
        )}

        {view === "create" && (
          <section className="page-content create-page">
            <button className="back-link" onClick={() => setView("library")}>← Quay lại thư viện</button>
            <div className="create-layout">
              <div className="create-intro"><p className="eyebrow">BẮT ĐẦU TỪ Ý TƯỞNG</p><h1>Hãy tưởng tượng<br />điều gì đó.</h1><p>Bạn có thể mô tả bằng tiếng Việt. Hệ thống sẽ hiểu ý tưởng và diễn đạt lại thành hướng dẫn cho model tạo ảnh. Càng cụ thể về chủ thể, ánh sáng và cảm xúc, kết quả càng gần với hình dung của bạn.</p><div className="prompt-tip"><span>✳</span><p><strong>Mẹo nhỏ</strong><br />Nêu rõ chủ thể, bối cảnh, phong cách và ánh sáng để có kết quả tốt hơn.</p></div></div>
              <form className="prompt-card" onSubmit={createImage} aria-busy={working}>
                <div className="prompt-card-head"><span className="card-step">01</span><span>HÌNH ẢNH MỚI</span><span className="prompt-count">{prompt.length} / 4.000</span></div>
                <label className="visually-hidden" htmlFor="new-prompt">Mô tả hình ảnh</label>
                <textarea id="new-prompt" autoFocus maxLength={4000} value={prompt} onChange={(event) => setPrompt(event.target.value)} placeholder="Ví dụ: Một căn nhà nhỏ bên bờ biển lúc hoàng hôn, phong cách tranh màu nước…" required />
                <label className="image-count-label" htmlFor="image-count">Số ảnh cần tạo
                  <select id="image-count" value={imageCount} onChange={(event) => setImageCount(Number(event.target.value))} disabled={working}>
                    {[1, 2, 3, 4, 5, 6].map((count) => <option key={count} value={count}>{count} ảnh</option>)}
                  </select>
                </label>
                <div className="prompt-card-foot"><span>✧ Mô tả gốc được lưu cùng hình ảnh.</span><button className="button primary" type="submit" disabled={working || !prompt.trim()}>{working ? <><span className="button-loader" /> Đang tạo ảnh…</> : <>Tạo hình ảnh <span aria-hidden="true">↗</span></>}</button></div>
                {working && <div className="progress-note" role="status">Đã xử lý {completedCount}/{imageCount} ảnh. Mỗi ảnh được lưu riêng; có thể mất vài phút.</div>}
              </form>
            </div>
          </section>
        )}

        {view === "detail" && selected && (
          <section className="page-content detail-page">
            <button className="back-link" onClick={() => setView("library")}>← Quay lại thư viện</button>
            <div className="detail-grid">
              <div className="detail-preview">
                {selected.status === "succeeded" ? <img src={imageFile(selected.id)} alt={selected.prompt} /> : <div className="image-placeholder"><span>{selected.status === "processing" ? "Đang xử lý" : "Tạo ảnh thất bại"}</span></div>}
                {selected.status === "succeeded" && <a className="download-link" href={imageFile(selected.id)} download>↓ Tải hình ảnh</a>}
              </div>
              <div className="detail-info">
                <div className="detail-title-row"><div><p className="eyebrow">{operationLabel(selected.operation)}</p><h1>Chi tiết hình ảnh</h1></div><StatusBadge status={selected.status} /></div>
                <div className="detail-block"><span className="detail-label">PROMPT</span><p className="detail-prompt">{selected.prompt}</p></div>
                <div className="detail-facts"><div><span>Ngày tạo</span><strong>{formatDate(selected.created_at)}</strong></div><div><span>Định dạng</span><strong>{selected.mime_type?.replace("image/", "").toUpperCase() ?? "—"}</strong></div></div>
                {selected.error && <p className="alert error" role="alert">{displayError(selected.error)}</p>}
                {selected.parent_id && <div className="origin-note">↳ Ảnh này được tạo từ một ảnh nguồn.</div>}
                <button className="button danger" type="button" disabled={working} onClick={() => void deleteImage(selected)}>Xóa ảnh</button>
                {selected.status === "succeeded" && <div className="actions-block">
                  <form className="action-form" onSubmit={(event) => void createDerived(event, "edit")}>
                    <label htmlFor="edit-prompt">Chỉnh sửa bằng prompt</label>
                    <textarea id="edit-prompt" maxLength={4000} value={editPrompt} onChange={(event) => setEditPrompt(event.target.value)} placeholder="Ví dụ: Thêm những đám mây hồng ở phía chân trời…" required />
                    <button className="button secondary" type="submit" disabled={working || !editPrompt.trim()}>{workingAction === "edit" ? "Đang chỉnh sửa…" : "Tạo bản chỉnh sửa"}</button>
                  </form>
                  <form className="action-form variation-form" onSubmit={(event) => void createDerived(event, "variations")}>
                    <label htmlFor="variation-prompt">Tạo biến thể <span>Tùy chọn · để trống dùng hướng mặc định</span></label>
                    <textarea id="variation-prompt" maxLength={2000} value={variationPrompt} onChange={(event) => setVariationPrompt(event.target.value)} placeholder="Thêm hướng dẫn cho biến thể bằng tiếng Việt hoặc ngôn ngữ bạn muốn…" />
                    <button className="button secondary" type="submit" disabled={working}>{workingAction === "variations" ? "Đang tạo biến thể…" : "Tạo biến thể"}</button>
                  </form>
                  {workingAction && <p className="progress-note" role="status">{workingAction === "edit" ? "Đang tạo bản chỉnh sửa" : "Đang tạo biến thể"}. Có thể mất một chút thời gian.</p>}
                </div>}
              </div>
            </div>
            {related.length > 0 && <div className="related-section"><h2>Lịch sử hình ảnh</h2><p>Các ảnh liên quan trong thư viện của bạn.</p><div className="related-list">{related.map((image) => <button className="related-item" key={image.id} onClick={() => openDetail(image)}>{image.status === "succeeded" ? <img src={imageFile(image.id)} alt="" /> : <span aria-hidden="true">✳</span>}<span><strong>{operationLabel(image.operation)}</strong><small>{image.prompt}</small></span><span>↗</span></button>)}</div></div>}
          </section>
        )}
        {view === "detail" && !selected && <div className="page-content"><EmptyLibrary onCreate={() => setView("create")} /></div>}
      </main>
    </div>
  );
}

function Brand() {
  return <div className="brand"><span className="brand-mark"><i /><i /><i /><i /></span><span>atelier<span className="brand-dot">.</span></span></div>;
}

function ImageCard({ image, index, onOpen, onDelete, disabled }: { image: ImageRecord; index: number; onOpen: () => void; onDelete: () => void; disabled: boolean }) {
  return (
    <div className="image-card">
      <button className="image-card-open" onClick={onOpen} aria-label={`Mở hình ảnh: ${image.prompt}`}>
        <div className={`image-thumb thumb-tone-${index % 5}`}>
          {image.status === "succeeded" ? <img loading="lazy" src={imageFile(image.id)} alt="" /> : <div className="image-placeholder"><span>{image.status === "processing" ? "Đang xử lý" : "Tạo ảnh thất bại"}</span></div>}
          <span className="card-open" aria-hidden="true">↗</span>
        </div>
        <div className="image-card-copy"><p>{image.prompt}</p><div><span>{formatDate(image.created_at)}</span><StatusBadge status={image.status} /></div></div>
      </button>
      <button className="card-delete" type="button" disabled={disabled} onClick={onDelete} aria-label={`Xóa hình ảnh: ${image.prompt}`}>Xóa</button>
    </div>
  );
}

function StatusBadge({ status }: { status: ImageRecord["status"] }) {
  const label = status === "succeeded" ? "Hoàn tất" : status === "processing" ? "Đang xử lý" : "Thất bại";
  return <span className={`status-badge status-${status}`}><i />{label}</span>;
}

function EmptyLibrary({ onCreate }: { onCreate: () => void }) {
  return <div className="empty-state"><div className="empty-art"><span>✳</span><i /><i /><i /></div><p className="eyebrow">MỌI TÁC PHẨM ĐỀU BẮT ĐẦU TỪ Ý TƯỞNG</p><h2>Thư viện của bạn đang chờ.</h2><p>Tạo hình ảnh đầu tiên và lưu lại prompt để tiếp tục sáng tạo bất cứ lúc nào.</p><button className="button primary" onClick={onCreate}>Tạo hình ảnh đầu tiên <span aria-hidden="true">↗</span></button></div>;
}

function operationLabel(operation: ImageRecord["operation"]): string {
  if (operation === "edit") return "BẢN CHỈNH SỬA";
  if (operation === "variation") return "BIẾN THỂ";
  return "HÌNH ẢNH ĐƯỢC TẠO";
}

export default App;
