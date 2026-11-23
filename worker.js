const SECURITY_HEADERS = {
  "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https:; style-src 'self' 'unsafe-inline' https:; img-src 'self' data: blob: https:; font-src 'self' data: https:; connect-src 'self' https: wss:; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none';",
  "Strict-Transport-Security": "max-age=63072000; includeSubDomains; preload",
  "X-Frame-Options": "DENY",
  "X-Content-Type-Options": "nosniff",
  "Referrer-Policy": "strict-origin-when-cross-origin",
  "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
};

function withSecurityHeaders(response) {
  const newHeaders = new Headers(response.headers);
  for (const [key, value] of Object.entries(SECURITY_HEADERS)) {
    newHeaders.set(key, value);
  }
  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers: newHeaders,
  });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const pathname = url.pathname;

    // 1. Proxy API requests to backend
    if (pathname.startsWith("/api/v1/")) {
      const backendUrl = env.NEXT_PUBLIC_API_URL || "https://automation-website-pyp9.onrender.com";
      const targetUrl = new URL(pathname + url.search, backendUrl);
      const backendResp = await fetch(new Request(targetUrl, request));
      return withSecurityHeaders(backendResp);
    }

    // 2. Map Next.js static asset URLs (/_next/static/... -> /static/...)
    if (pathname.startsWith("/_next/static/")) {
      const assetPath = pathname.replace(/^\/_next\/static\//, "/static/");
      const assetUrl = new URL(assetPath, url.origin);
      const assetResp = await env.ASSETS.fetch(assetUrl.toString());
      if (assetResp.status === 200) {
        return withSecurityHeaders(assetResp);
      }
    }

    // 3. Serve other static assets directly if they have a recognized file extension
    if (pathname.includes(".")) {
      const resp = await env.ASSETS.fetch(request);
      if (resp.status === 200) {
        return withSecurityHeaders(resp);
      }
    }

    // 4. Clean page routes (e.g. /, /dashboard, /login, /upload, /subscriptions)
    const cleanPath = pathname.length > 1 ? pathname.replace(/\/+$/, "") : pathname;
    const pagePath = cleanPath === "/" ? "/server/app/index.html" : `/server/app${cleanPath}.html`;
    const targetUrl = new URL(pagePath, url.origin);
    const pageResponse = await env.ASSETS.fetch(targetUrl.toString());
    if (pageResponse.status === 200) {
      const headers = new Headers(pageResponse.headers);
      headers.set("Content-Type", "text/html; charset=utf-8");
      return withSecurityHeaders(new Response(pageResponse.body, { status: 200, headers }));
    }

    // 5. Dynamic route fallback (e.g. /documents/[id])
    if (pathname.startsWith("/documents/")) {
      const docDetailUrl = new URL("/server/app/documents/[id].html", url.origin);
      const docResp = await env.ASSETS.fetch(docDetailUrl.toString());
      if (docResp.status === 200) {
        const headers = new Headers(docResp.headers);
        headers.set("Content-Type", "text/html; charset=utf-8");
        return withSecurityHeaders(new Response(docResp.body, { status: 200, headers }));
      }
    }

    // 6. SPA Catch-All Route Rewrite (Fall back all non-static asset routes to /index.html with 200 OK)
    const spaUrl = new URL("/server/app/index.html", url.origin);
    const spaResp = await env.ASSETS.fetch(spaUrl.toString());
    if (spaResp.status === 200) {
      const headers = new Headers(spaResp.headers);
      headers.set("Content-Type", "text/html; charset=utf-8");
      return withSecurityHeaders(new Response(spaResp.body, { status: 200, headers }));
    }

    // Direct root fallback
    const rootIndexUrl = new URL("/index.html", url.origin);
    const rootIndexResp = await env.ASSETS.fetch(rootIndexUrl.toString());
    if (rootIndexResp.status === 200) {
      const headers = new Headers(rootIndexResp.headers);
      headers.set("Content-Type", "text/html; charset=utf-8");
      return withSecurityHeaders(new Response(rootIndexResp.body, { status: 200, headers }));
    }

    // 7. Not Found fallback for missing static assets
    const notFoundUrl = new URL("/server/app/_not-found.html", url.origin);
    const notFoundResp = await env.ASSETS.fetch(notFoundUrl.toString());
    return withSecurityHeaders(new Response(notFoundResp.body, {
      status: 404,
      headers: { "Content-Type": "text/html; charset=utf-8" },
    }));
  },
};
