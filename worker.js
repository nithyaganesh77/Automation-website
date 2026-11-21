export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const pathname = url.pathname;

    // 1. Proxy API requests to backend
    if (pathname.startsWith("/api/v1/")) {
      const backendUrl = env.NEXT_PUBLIC_API_URL || "https://automation-website-pyp9.onrender.com";
      const targetUrl = new URL(pathname + url.search, backendUrl);
      return fetch(new Request(targetUrl, request));
    }

    // 2. Serve static assets directly (_next/static/...)
    if (pathname.startsWith("/_next/") || pathname.includes(".")) {
      return env.ASSETS.fetch(request);
    }

    // 3. Clean page routes (e.g. /, /dashboard, /login, /upload, /subscriptions)
    const pagePath = pathname === "/" ? "/server/app/index.html" : `/server/app${pathname}.html`;
    const targetUrl = new URL(pagePath, url.origin);
    const pageResponse = await env.ASSETS.fetch(targetUrl.toString());
    if (pageResponse.status === 200) {
      const headers = new Headers(pageResponse.headers);
      headers.set("Content-Type", "text/html; charset=utf-8");
      return new Response(pageResponse.body, { status: 200, headers });
    }

    // 4. Dynamic route fallback (e.g. /documents/[id])
    if (pathname.startsWith("/documents/")) {
      const docDetailUrl = new URL("/server/app/documents/[id].html", url.origin);
      const docResp = await env.ASSETS.fetch(docDetailUrl.toString());
      if (docResp.status === 200) {
        const headers = new Headers(docResp.headers);
        headers.set("Content-Type", "text/html; charset=utf-8");
        return new Response(docResp.body, { status: 200, headers });
      }
    }

    // 5. 404 Fallback
    const notFoundUrl = new URL("/server/app/_not-found.html", url.origin);
    const notFoundResp = await env.ASSETS.fetch(notFoundUrl.toString());
    return new Response(notFoundResp.body, {
      status: 404,
      headers: { "Content-Type": "text/html; charset=utf-8" },
    });
  },
};
