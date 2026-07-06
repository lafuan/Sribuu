// Cloudflare Pages Functions - Catch-all handler
export async function onRequest(context) {
  return new Response('Hello from Sribuu on Cloudflare Pages!', {
    headers: { 'content-type': 'text/plain' },
  });
}
