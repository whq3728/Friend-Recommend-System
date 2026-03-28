/**
 * 开发环境通过 Vite 代理访问 Flask；生产可改为环境变量中的 API 根地址。
 */
export async function api(path, options = {}) {
  const { method = "GET", body, headers: hdr = {}, ...rest } = options;
  const headers = { ...hdr };
  if (body !== undefined && body !== null) {
    headers["Content-Type"] = "application/json";
  }
  const r = await fetch(path, {
    method,
    credentials: "include",
    headers,
    body: body !== undefined && body !== null ? JSON.stringify(body) : undefined,
    ...rest,
  });
  const text = await r.text();
  let data = text;
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      /* 保持字符串 */
    }
  }
  if (!r.ok) {
    const msg =
      typeof data === "object" && data !== null && data.error
        ? data.error
        : typeof data === "string"
          ? data
          : r.statusText;
    throw new Error(msg);
  }
  return data;
}
