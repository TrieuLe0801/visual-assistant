import { useCallback, useEffect, useMemo, useState } from "react";
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
        ? detail
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
  const [working, setWorking] = useState(false);
  const [error, setError] = useState("");
  const [authMode, setAuthMode] = useState<"login" | "register">("login");
  const [prompt, setPrompt] = useState("");
  const [editPrompt, setEditPrompt] = useState("");
  const [variationPrompt, setVariationPrompt] = useState("");

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
    setLoadingImages(true);
    try {
      const result = await request<ImageRecord[]>('/api/images');
      setImages(result);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Không tải được thư viện ảnh.");
    } finally {
      setLoadingImages(false);
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
    setUser(null);
    setImages([]);
    setSelectedId(null);
    setView("library");
  }

  async function createImage(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const value = prompt.trim();
    if (!value) return;
    setError("");
    setWorking(true);
    try {
      const created = await request<ImageRecord>("/api/images/generate", {
        method: "POST",
        body: JSON.stringify({ prompt: value }),
      });
      await loadImages();
      setSelectedId(created.id);
      setPrompt("");
      setView("detail");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Tạo ảnh thất bại.");
      await loadImages();
    } finally {
      setWorking(false);
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
    try {
      const created = await request<ImageRecord>(
        `/api/images/${encodeURIComponent(String(selected.id))}/${operation}`,
        {
          method: "POST",
          body: JSON.stringify({ prompt: value || undefined }),
        },
      );
      await loadImages();
      setSelectedId(created.id);
      setEditPrompt("");
      setVariationPrompt("");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Không xử lý được ảnh.");
      await loadImages();
    } finally {
      setWorking(false);
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
          <div className="auth-tabs" role="tablist" aria-label="Tài khoản">
            <button className={authMode === "login" ? "active" : ""} onClick={() => { setAuthMode("login"); setError(""); }} role="tab" aria-selected={authMode === "login"}>Đăng nhập</button>
            <button className={authMode === "register" ? "active" : ""} onClick={() => { setAuthMode("register"); setError(""); }} role="tab" aria-selected={authMode === "register"}>Tạo tài khoản</button>
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
      <aside className="sidebar">
        <Brand />
        <button className={`nav-item ${view === "library" || view === "detail" ? "selected" : ""}`} onClick={() => { setView("library"); setError(""); }}>
          <span className="nav-icon grid-icon" aria-hidden="true" />Thư viện
          <span className="nav-count">{images.filter((image) => image.status === "succeeded").length}</span>
        </button>
        <button className={`nav-item ${view === "create" ? "selected" : ""}`} onClick={() => { setView("create"); setError(""); }}>
          <span className="nav-icon plus-icon" aria-hidden="true">＋</span>Tạo hình ảnh
        </button>
        <div className="sidebar-bottom">
          <div className="privacy-card"><span className="privacy-mark">✳</span><div><strong>Riêng tư theo thiết kế</strong><p>Chỉ bạn xem được thư viện này.</p></div></div>
          <div className="account-row"><span className="avatar">{user.email.slice(0, 1).toUpperCase()}</span><span className="account-email" title={user.email}>{user.email}</span><button className="icon-button" aria-label="Đăng xuất" title="Đăng xuất" onClick={() => void signOut()}>↗</button></div>
        </div>
      </aside>

      <main className="main-area">
        <header className="topbar">
          <div className="breadcrumb"><span>Không gian</span><span className="crumb-sep">/</span><strong>{view === "detail" ? "Chi tiết hình ảnh" : view === "create" ? "Tạo hình ảnh" : "Thư viện"}</strong></div>
          <div className="topbar-right"><span className="status-dot" />Đã lưu tự động</div>
        </header>

        {error && <div className="global-alert alert error" role="alert"><span>{error}</span><button aria-label="Đóng thông báo" onClick={() => setError("")}>×</button></div>}

        {view === "library" && (
          <section className="page-content">
            <div className="page-heading heading-row">
              <div><p className="eyebrow">GÓC SÁNG TẠO CỦA BẠN</p><h1>Thư viện hình ảnh</h1><p className="subheading">Tất cả hình ảnh và ý tưởng của bạn, ở cùng một nơi.</p></div>
              <button className="button primary" onClick={() => { setView("create"); setError(""); }}>＋ Tạo hình ảnh mới</button>
            </div>
            <div className="library-meta"><span>{images.filter((image) => image.status === "succeeded").length} tác phẩm</span><span className="sort-label">Mới nhất trước <span aria-hidden="true">⌄</span></span></div>
            {loadingImages ? <div className="loading-state"><span className="loader" />Đang tải thư viện…</div> : images.length ? (
              <div className="image-grid">
                {images.map((image, index) => <ImageCard key={image.id} image={image} index={index} onOpen={() => openDetail(image)} />)}
              </div>
            ) : <EmptyLibrary onCreate={() => setView("create")} />}
          </section>
        )}

        {view === "create" && (
          <section className="page-content create-page">
            <button className="back-link" onClick={() => setView("library")}>← Quay lại thư viện</button>
            <div className="create-layout">
              <div className="create-intro"><p className="eyebrow">BẮT ĐẦU TỪ Ý TƯỞNG</p><h1>Hãy tưởng tượng<br />điều gì đó.</h1><p>Bạn có thể mô tả bằng tiếng Việt. Hệ thống sẽ hiểu ý tưởng và diễn đạt lại thành hướng dẫn cho model tạo ảnh. Càng cụ thể về chủ thể, ánh sáng và cảm xúc, kết quả càng gần với hình dung của bạn.</p><div className="prompt-tip"><span>✳</span><p><strong>Mẹo nhỏ</strong><br />Nêu rõ chủ thể, bối cảnh, phong cách và ánh sáng để có kết quả tốt hơn.</p></div></div>
              <form className="prompt-card" onSubmit={createImage}>
                <div className="prompt-card-head"><span className="card-step">01</span><span>HÌNH ẢNH MỚI</span><span className="prompt-count">{prompt.length} / 4.000</span></div>
                <label className="visually-hidden" htmlFor="new-prompt">Mô tả hình ảnh</label>
                <textarea id="new-prompt" autoFocus maxLength={4000} value={prompt} onChange={(event) => setPrompt(event.target.value)} placeholder="Ví dụ: Một căn nhà nhỏ bên bờ biển lúc hoàng hôn, phong cách tranh màu nước…" required />
                <div className="prompt-card-foot"><span>✧ Mô tả gốc được lưu cùng hình ảnh.</span><button className="button primary" type="submit" disabled={working || !prompt.trim()}>{working ? <><span className="button-loader" /> Đang tạo ảnh…</> : <>Tạo hình ảnh <span aria-hidden="true">↗</span></>}</button></div>
                {working && <div className="progress-note" role="status">Đang xử lý mô tả và tạo hình ảnh. Có thể mất một chút thời gian.</div>}
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
                {selected.error && <p className="alert error">{selected.error}</p>}
                {selected.parent_id && <div className="origin-note">↳ Ảnh này được tạo từ một ảnh trong thư viện.</div>}
                {selected.status === "succeeded" && <div className="actions-block">
                  <form className="action-form" onSubmit={(event) => void createDerived(event, "edit")}>
                    <label htmlFor="edit-prompt">Chỉnh sửa bằng prompt</label>
                    <textarea id="edit-prompt" maxLength={4000} value={editPrompt} onChange={(event) => setEditPrompt(event.target.value)} placeholder="Ví dụ: Thêm những đám mây hồng ở phía chân trời…" required />
                    <button className="button secondary" type="submit" disabled={working || !editPrompt.trim()}>{working ? "Đang xử lý…" : "Tạo bản chỉnh sửa"}</button>
                  </form>
                  <form className="action-form variation-form" onSubmit={(event) => void createDerived(event, "variations")}>
                    <label htmlFor="variation-prompt">Tạo biến thể <span>Tùy chọn · để trống dùng hướng mặc định</span></label>
                    <textarea id="variation-prompt" maxLength={2000} value={variationPrompt} onChange={(event) => setVariationPrompt(event.target.value)} placeholder="Thêm hướng dẫn cho biến thể bằng tiếng Việt hoặc ngôn ngữ bạn muốn…" />
                    <button className="button secondary" type="submit" disabled={working}>{working ? "Đang xử lý…" : "Tạo biến thể"}</button>
                  </form>
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

function ImageCard({ image, index, onOpen }: { image: ImageRecord; index: number; onOpen: () => void }) {
  return (
    <button className="image-card" onClick={onOpen} aria-label={`Mở hình ảnh: ${image.prompt}`}>
      <div className={`image-thumb thumb-tone-${index % 5}`}>
        {image.status === "succeeded" ? <img loading="lazy" src={imageFile(image.id)} alt="" /> : <div className="image-placeholder"><span>{image.status === "processing" ? "Đang xử lý" : "Tạo ảnh thất bại"}</span></div>}
        <span className="card-open" aria-hidden="true">↗</span>
      </div>
      <div className="image-card-copy"><p>{image.prompt}</p><div><span>{formatDate(image.created_at)}</span><StatusBadge status={image.status} /></div></div>
    </button>
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
