import { expect, test } from "@playwright/test";
import type { Page } from "@playwright/test";

type ImageRecord = {
  id: number;
  prompt: string;
  operation: "generate" | "edit" | "variation";
  status: "succeeded" | "failed" | "processing";
  parent_id: number | null;
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

async function mockApi(page: Page, options: { images?: ImageRecord[]; registration?: boolean } = {}) {
  let loggedIn = false;
  let images = [...(options.images ?? [])];
  let nextId = 20;
  let generateCalls = 0;
  let failNextLibrary = false;

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
      if (generateCalls === 2 && (await request.postDataJSON()).prompt === "partial") return json({ detail: "provider unavailable" }, 503);
      const body = await request.postDataJSON();
      const created = image(nextId++, body.prompt);
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

test("detail shows prompt and download link", async ({ page }) => {
  const api = await mockApi(page, { images: [image(7, "Prompt chi tiết")] });
  await page.goto("/");
  await api.login();
  await page.getByRole("button", { name: /Mở hình ảnh: Prompt chi tiết/ }).click();
  await expect(page.getByText("Prompt chi tiết").last()).toBeVisible();
  await expect(page.getByRole("link", { name: /Tải hình ảnh/ })).toHaveAttribute("download", "");
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
