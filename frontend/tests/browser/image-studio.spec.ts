import { expect, test } from "@playwright/test";
import type { Page } from "@playwright/test";

type ImageRecord = {
  id: number;
  prompt: string;
  operation: "generate" | "edit" | "variation";
  status: "succeeded" | "failed" | "processing";
  parent_id: number | null;
  root_id?: number | null;
  mime_type: string | null;
  created_at: string;
  error?: string | null;
};

const date = "2026-11-23T12:00:00Z";
const image = (id: number, prompt = `Ảnh ${id}`): ImageRecord => ({
  id,
  prompt,
  operation: "generate",
  status: "succeeded",
  parent_id: null,
  mime_type: "image/png",
  created_at: date,
});

async function mockApi(page: Page, options: { images?: ImageRecord[]; registration?: boolean; holdFirstGenerate?: boolean; holdDerived?: boolean; failDerived?: boolean } = {}) {
  let loggedIn = false;
  let images = [...(options.images ?? [])];
  let nextId = 20;
  let generateCalls = 0;
  let failNextLibrary = false;
  let releaseGenerate: (() => void) | null = null;
  let releaseDerived: (() => void) | null = null;

  await page.route("**/api/**", async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    const method = request.method();
    const json = (body: unknown, status = 200) => route.fulfill({
      status,
      contentType: "application/json",
      body: JSON.stringify(body),
    });

    if (path === "/api/auth/registration-status" && method === "GET") return json({ enabled: options.registration ?? false });
    if (path === "/api/auth/me" && method === "GET") return loggedIn ? json({ id: 1, email: "user@example.com" }) : json({ detail: "Not authenticated" }, 401);
    if (path === "/api/auth/login" && method === "POST") {
      loggedIn = true;
      return json({ id: 1, email: "user@example.com" });
    }
    if (path === "/api/auth/logout" && method === "POST") {
      loggedIn = false;
      return route.fulfill({ status: 204, body: "" });
    }
    if (path === "/api/images" && method === "GET") {
      if (failNextLibrary) {
        failNextLibrary = false;
        return json({ detail: "library unavailable" }, 503);
      }
      return json(images);
    }
    if (path === "/api/images/generate" && method === "POST") {
      generateCalls += 1;
      if (options.holdFirstGenerate && generateCalls === 1) {
        await new Promise<void>((resolve) => { releaseGenerate = resolve; });
      }
      if (generateCalls === 2 && (await request.postDataJSON()).prompt === "partial") return json({ detail: "provider unavailable" }, 503);
      const body = await request.postDataJSON();
      const created = image(nextId++, body.prompt);
      images = [created, ...images];
      return json(created);
    }
    const derivedMatch = path.match(/^\/api\/images\/(\d+)\/(edit|variations)$/);
    if (derivedMatch && method === "POST") {
      if (options.holdDerived) {
        await new Promise<void>((resolve) => { releaseDerived = resolve; });
      }
      if (options.failDerived) return json({ detail: "provider unavailable" }, 503);
      const body = await request.postDataJSON();
      const operation = derivedMatch[2] === "edit" ? "edit" as const : "variation" as const;
      const created = { ...image(nextId++, body.prompt ?? "Biến thể"), operation, parent_id: Number(derivedMatch[1]), root_id: Number(derivedMatch[1]) };
      images = [created, ...images];
      return json(created);
    }
    const fileMatch = path.match(/^\/api\/images\/(\d+)\/file$/);
    if (fileMatch && method === "GET") return route.fulfill({ status: 200, contentType: "image/png", body: Buffer.from("fake-png") });
    const deleteMatch = path.match(/^\/api\/images\/(\d+)$/);
    if (deleteMatch && method === "DELETE") {
      images = images.filter((item) => item.id !== Number(deleteMatch[1]));
      return route.fulfill({ status: 204, body: "" });
    }
    return route.abort("blockedbyclient");
  });

  return {
    login: async () => {
      await page.getByLabel("Email").fill("user@example.com");
      await page.getByLabel("Mật khẩu").fill("long-enough-password");
      await page.getByRole("button", { name: "Đăng nhập" }).click();
      await expect(page.getByRole("heading", { name: "Thư viện hình ảnh" })).toBeVisible();
    },
    failLibrary: () => { failNextLibrary = true; },
    releaseGenerate: () => { releaseGenerate?.(); },
    releaseDerived: () => { releaseDerived?.(); },
  };
}

test("registration disabled and login opens private library", async ({ page }) => {
  const api = await mockApi(page, { images: [image(1, "Bãi biển lúc hoàng hôn")] });
  await page.goto("/");
  await expect(page.getByRole("button", { name: "Đăng nhập" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Tạo tài khoản" })).toHaveCount(0);
  await page.getByLabel("Email").focus();
  await page.keyboard.press("Tab");
  await expect(page.getByLabel("Mật khẩu")).toBeFocused();
  await api.login();
  await expect(page.getByText("Bãi biển lúc hoàng hôn")).toBeVisible();
});

test("partial six-image creation keeps successful results and reports failure", async ({ page }) => {
  const api = await mockApi(page);
  await page.goto("/");
  await api.login();
  await page.getByRole("button", { name: /Tạo hình ảnh mới/ }).click();
  await page.getByLabel("Mô tả hình ảnh").fill("partial");
  await page.getByLabel("Số ảnh cần tạo").selectOption("6");
  await page.locator('button[type="submit"]').click();
  await expect(page.getByRole("alert")).toContainText("5/6 ảnh đã tạo");
  await expect(page.getByText("partial").first()).toBeVisible();
});

test("creation progress names active request and completed attempts", async ({ page }) => {
  const api = await mockApi(page, { holdFirstGenerate: true });
  await page.goto("/");
  await api.login();
  await page.getByRole("button", { name: /Tạo hình ảnh mới/ }).click();
  await page.getByLabel("Mô tả hình ảnh").fill("progress");
  await page.getByLabel("Số ảnh cần tạo").selectOption("2");
  await page.locator('button[type="submit"]').click();
  await expect(page.getByRole("status")).toContainText("Đang tạo ảnh 1 / 2");
  await expect(page.getByRole("progressbar")).toHaveAttribute("aria-valuenow", "0");
  api.releaseGenerate();
  await expect(page.getByRole("status")).toContainText("Đang tạo ảnh 2 / 2");
});

test("edit progress locks duplicate submit until stored version returns", async ({ page }) => {
  const root = image(40, "Ảnh nguồn");
  const api = await mockApi(page, { images: [root], holdDerived: true });
  await page.goto("/");
  await api.login();
  await page.getByRole("button", { name: /Mở hình ảnh: Ảnh nguồn/ }).click();
  await page.getByLabel("Chỉnh sửa bằng prompt").fill("Thêm ánh sáng ấm");
  const submit = page.locator(".action-form").first().getByRole("button");
  await submit.click();
  await expect(page.getByRole("status")).toContainText("Đang tạo bản chỉnh sửa");
  await expect(page.getByRole("button", { name: /Đang chỉnh sửa/ })).toBeDisabled();
  api.releaseDerived();
  await expect(page.getByRole("button", { name: /V2/ })).toBeVisible();
  await expect(page.getByRole("status")).toHaveCount(0);
});

test("variation progress clears on error and keeps selected source", async ({ page }) => {
  const root = image(41, "Ảnh nguồn biến thể");
  const api = await mockApi(page, { images: [root], holdDerived: true, failDerived: true });
  await page.goto("/");
  await api.login();
  await page.getByRole("button", { name: /Mở hình ảnh: Ảnh nguồn biến thể/ }).click();
  await page.getByLabel(/Tạo biến thể/).fill("Biến thể ánh sáng mềm");
  const submit = page.locator(".variation-form").getByRole("button");
  await submit.click();
  await expect(page.getByRole("status")).toContainText("Đang tạo biến thể");
  await expect(page.getByRole("button", { name: /Đang tạo biến thể/ })).toBeDisabled();
  api.releaseDerived();
  await expect(page.getByRole("alert")).toContainText("provider unavailable");
  await expect(page.getByRole("status")).toHaveCount(0);
  await expect(page.getByText("Ảnh nguồn biến thể").last()).toBeVisible();
});

test("detail shows prompt and download link", async ({ page }) => {
  const api = await mockApi(page, { images: [image(7, "Prompt chi tiết")] });
  await page.goto("/");
  await api.login();
  await page.getByRole("button", { name: /Mở hình ảnh: Prompt chi tiết/ }).click();
  await expect(page.getByText("Prompt chi tiết").last()).toBeVisible();
  await expect(page.getByRole("link", { name: /Tải hình ảnh/ })).toHaveAttribute("download", "");
});

test("groups versions into one card and lets user select and delete a version", async ({ page }) => {
  const root = { ...image(7, "Bản gốc"), created_at: "2026-11-23T11:00:00Z" };
  const edit = { ...image(8, "Bản chỉnh sửa"), operation: "edit" as const, parent_id: 7, root_id: 7, created_at: "2026-11-23T12:00:00Z" };
  const api = await mockApi(page, { images: [edit, { ...root, root_id: 7 }] });
  await page.goto("/");
  await api.login();
  await expect(page.getByRole("button", { name: /Mở hình ảnh: Bản chỉnh sửa/ })).toHaveCount(1);
  await expect(page.getByRole("button", { name: /Mở hình ảnh: Bản chỉnh sửa/ })).toContainText("2 phiên bản");
  await page.getByRole("button", { name: /Mở hình ảnh: Bản chỉnh sửa/ }).click();
  await expect(page.getByRole("button", { name: /V1/ })).toBeVisible();
  await expect(page.getByRole("button", { name: /V2/ })).toBeVisible();
  await page.getByRole("button", { name: /V1/ }).focus();
  await page.keyboard.press("Tab");
  await page.keyboard.press("Enter");
  await expect(page.getByRole("button", { name: /V2/ })).toHaveAttribute("aria-pressed", "true");
  await page.getByRole("button", { name: /V1/ }).click();
  await expect(page.getByRole("heading", { name: "Lịch sử hình ảnh" })).toHaveCount(0);
  await expect(page.getByText("Bản gốc").last()).toBeVisible();
  page.once("dialog", (dialog) => void dialog.accept());
  await page.getByRole("button", { name: "Xóa ảnh" }).click();
  await expect(page.getByText("Bản chỉnh sửa").last()).toBeVisible();
});

test("latest failed version remains visible as failed state", async ({ page }) => {
  const root = image(30, "Bản gốc");
  const failed = { ...image(31, "Lần chỉnh sửa lỗi"), operation: "edit" as const, status: "failed" as const, parent_id: 30, root_id: 30, error: "provider unavailable" };
  const api = await mockApi(page, { images: [failed, root] });
  await page.goto("/");
  await api.login();
  const card = page.getByRole("button", { name: /Mở hình ảnh: Lần chỉnh sửa lỗi/ });
  await expect(card).toContainText("Thất bại");
  await expect(card.locator("img")).toHaveCount(0);
});

test("library error offers retry", async ({ page }) => {
  const api = await mockApi(page);
  api.failLibrary();
  await page.goto("/");
  await api.login();
  await expect(page.getByRole("heading", { name: "Chưa tải được thư viện" })).toBeVisible();
  await page.getByRole("button", { name: "Thử tải lại" }).click();
  await expect(page.getByRole("heading", { name: "Thư viện hình ảnh" })).toBeVisible();
});

test("library search and status filter narrow saved images without API calls", async ({ page }) => {
  const api = await mockApi(page, { images: [image(1, "Bãi biển lúc hoàng hôn"), { ...image(2, "Chân dung studio"), status: "failed" }] });
  await page.goto("/");
  await api.login();
  await expect(page.getByRole("button", { name: /Mở hình ảnh: Bãi biển/ })).toBeVisible();
  await expect(page.getByRole("button", { name: /Mở hình ảnh: Chân dung/ })).toBeVisible();
  await page.getByRole("searchbox", { name: "Tìm theo prompt" }).fill("biển");
  await expect(page.getByRole("button", { name: /Mở hình ảnh: Bãi biển/ })).toBeVisible();
  await expect(page.getByRole("button", { name: /Mở hình ảnh: Chân dung/ })).toHaveCount(0);
  await page.getByRole("searchbox", { name: "Tìm theo prompt" }).fill("không có");
  await expect(page.getByRole("heading", { name: "Không tìm thấy ảnh phù hợp" })).toBeVisible();
  await page.getByRole("button", { name: "Xóa bộ lọc" }).click();
  await page.getByLabel("Lọc theo trạng thái").selectOption("failed");
  await expect(page.getByRole("button", { name: /Mở hình ảnh: Chân dung/ })).toBeVisible();
  await expect(page.getByRole("button", { name: /Mở hình ảnh: Bãi biển/ })).toHaveCount(0);
});

test("logout clears prior library data", async ({ page }) => {
  const api = await mockApi(page, { images: [image(8, "Dữ liệu riêng tư")] });
  await page.goto("/");
  await api.login();
  await expect(page.getByText("Dữ liệu riêng tư")).toBeVisible();
  await page.getByRole("button", { name: "Đăng xuất" }).click();
  await expect(page.getByRole("button", { name: "Đăng nhập" })).toBeVisible();
  await expect(page.getByText("Dữ liệu riêng tư")).toHaveCount(0);
});

test("mobile layout has no horizontal overflow", async ({ page }) => {
  const api = await mockApi(page);
  await page.goto("/");
  await api.login();
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth);
  expect(overflow).toBe(false);
});
