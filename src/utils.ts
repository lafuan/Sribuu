// Pure utility functions for Sribuu — no D1/CF runtime dependencies
// Extracted for testability. Re-exported by _worker.ts.

// ============================================================
//  BASE64URL
// ============================================================

function base64url(buf: ArrayBuffer): string {
  const bytes = new Uint8Array(buf)
  let binary = ''
  for (let i = 0; i < bytes.length; i++) binary += String.fromCharCode(bytes[i])
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '')
}

function fromBase64url(s: string): Uint8Array {
  s = s.replace(/-/g, '+').replace(/_/g, '/')
  while (s.length % 4) s += '='
  const binary = atob(s)
  const bytes = new Uint8Array(binary.length)
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i)
  return bytes
}

// ============================================================
//  PASSWORD HASHING — PBKDF2-SHA256
// ============================================================

const PBKDF2_ITERATIONS = 100000
const SALT_BYTES = 16
const KEY_LENGTH = 32

export async function hashPassword(password: string): Promise<string> {
  const salt = crypto.getRandomValues(new Uint8Array(SALT_BYTES))
  const key = await crypto.subtle.importKey('raw', new TextEncoder().encode(password), 'PBKDF2', false, ['deriveBits'])
  const hash = await crypto.subtle.deriveBits(
    { name: 'PBKDF2', salt, iterations: PBKDF2_ITERATIONS, hash: 'SHA-256' },
    key,
    KEY_LENGTH * 8
  )
  return `$pbkdf2-sha256$${PBKDF2_ITERATIONS}$${base64url(salt)}$${base64url(hash)}`
}

export async function verifyPassword(password: string, stored: string): Promise<boolean> {
  const parts = stored.split('$')
  if (parts[0] !== '' || parts[1] !== 'pbkdf2-sha256') throw new Error('Unsupported hash format')
  const iterations = parseInt(parts[2], 10)
  const salt = fromBase64url(parts[3])
  const expectedHash = parts[4]
  const key = await crypto.subtle.importKey('raw', new TextEncoder().encode(password), 'PBKDF2', false, ['deriveBits'])
  const hash = await crypto.subtle.deriveBits(
    { name: 'PBKDF2', salt, iterations, hash: 'SHA-256' },
    key,
    KEY_LENGTH * 8
  )
  const hashStr = base64url(hash)
  if (hashStr.length !== expectedHash.length) return false
  let result = 0
  for (let i = 0; i < hashStr.length; i++) result |= hashStr.charCodeAt(i) ^ expectedHash.charCodeAt(i)
  return result === 0
}

// ============================================================
//  JWT — HMAC-SHA256
// ============================================================

function base64urlEncode(obj: any): string {
  return base64url(new TextEncoder().encode(JSON.stringify(obj)))
}

function base64urlDecode<T>(s: string): T {
  return JSON.parse(new TextDecoder().decode(fromBase64url(s)))
}

export async function signJWT(payload: Record<string, any>, secret: string): Promise<string> {
  const header = base64urlEncode({ alg: 'HS256', typ: 'JWT' })
  const body = base64urlEncode(payload)
  const key = await crypto.subtle.importKey('raw', new TextEncoder().encode(secret), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign'])
  const sig = await crypto.subtle.sign('HMAC', key, new TextEncoder().encode(`${header}.${body}`))
  return `${header}.${body}.${base64url(sig)}`
}

export async function verifyJWT(token: string, secret: string): Promise<Record<string, any> | null> {
  const parts = token.split('.')
  if (parts.length !== 3) return null
  const [headerB64, bodyB64, sigB64] = parts
  try {
    const key = await crypto.subtle.importKey('raw', new TextEncoder().encode(secret), { name: 'HMAC', hash: 'SHA-256' }, false, ['verify'])
    const valid = await crypto.subtle.verify('HMAC', key, fromBase64url(sigB64), new TextEncoder().encode(`${headerB64}.${bodyB64}`))
    if (!valid) return null
    const payload = base64urlDecode<any>(bodyB64)
    if (payload.exp && payload.exp < Math.floor(Date.now() / 1000)) return null
    return payload
  } catch { return null }
}

// ============================================================
//  Internal utils (for testing too)
// ============================================================

export { base64url, fromBase64url, base64urlEncode, base64urlDecode }
