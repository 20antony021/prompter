/**
 * API 客户端工厂
 * 用于创建带有认证的 API 调用函数
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v2";

/**
 * 创建 API 客户端
 * @param getToken - 获取认证 token 的函数
 */
export function createApiClient(getToken: () => Promise<string | null>) {
  async function fetchWithAuth(url: string, options: RequestInit = {}) {
    const token = await getToken();
    
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...((options.headers as Record<string, string>) || {}),
    };
    
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }
    
    const response = await fetch(`${API_BASE_URL}${url}`, {
      ...options,
      headers,
    });
    
    return response;
  }
  
  return {
    get: (url: string) => fetchWithAuth(url, { method: "GET", cache: "no-store" }),
    post: (url: string, data?: any) =>
      fetchWithAuth(url, {
        method: "POST",
        body: data ? JSON.stringify(data) : undefined,
      }),
    patch: (url: string, data?: any) =>
      fetchWithAuth(url, {
        method: "PATCH",
        body: data ? JSON.stringify(data) : undefined,
      }),
    delete: (url: string) => fetchWithAuth(url, { method: "DELETE" }),
  };
}

/**
 * 默认 API 客户端（用于客户端组件）
 * 使用 window.__clerk 获取 token
 */
export const defaultApiClient = createApiClient(async () => {
  if (typeof window !== "undefined" && (window as any).__clerk) {
    try {
      const clerk = (window as any).__clerk;
      const session = clerk.session;
      if (session) {
        return await session.getToken();
      }
    } catch (error) {
      console.error("Failed to get Clerk token:", error);
    }
  }
  return null;
});
