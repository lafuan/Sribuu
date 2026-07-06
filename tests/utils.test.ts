import { describe, it, expect } from 'vitest'
import {
  hashPassword,
  verifyPassword,
  signJWT,
  verifyJWT,
  base64url,
  fromBase64url,
  base64urlEncode,
  base64urlDecode,
} from '../src/utils'

// ============================================================
//  BASE64URL
// ============================================================

describe('base64url', () => {
  it('encodes a simple string', () => {
    const buf = new TextEncoder().encode('hello')
    const result = base64url(buf)
    expect(result).toBe('aGVsbG8')
  })

  it('encodes with padding removed', () => {
    const buf = new TextEncoder().encode('h')
    const result = base64url(buf)
    // 'h' in base64 = 'aA==' -> without padding = 'aA'
    expect(result).toBe('aA')
    expect(result).not.toContain('=')
  })

  it('uses URL-safe characters', () => {
    // Encode 3 bytes that produce 6-bit values 0, 62(+), 63(/) in standard base64
    // 000000|111110|111111 = 0x03, 0xBF, 0xC0? No, let me just verify with a known case
    const buf = new Uint8Array([0x00, 0x00, 0x3f, 0xc0])
    // 000000|000000|001111|111111|000000 → 0 0 15 63 0 → "AAP/A"
    // URL-safe: '-' for '+'(62), '_' for '/'(63) — but we don't have 62 here
    // Let me pick simpler bytes: encode then decode roundtrip is already tested above
    // We just need to verify: no '+' or '/' in output for random bytes
    const bytes = crypto.getRandomValues(new Uint8Array(64))
    const encoded = base64url(bytes)
    const decoded = fromBase64url(encoded)
    expect(new Uint8Array(decoded)).toEqual(bytes)
    expect(encoded).not.toContain('+')
    expect(encoded).not.toContain('/')
    // At least one '-' or '_' should appear for 64 random bytes (high probability)
    const hasUrlSafeChar = encoded.includes('-') || encoded.includes('_')
    expect(hasUrlSafeChar).toBe(true)
  })

  it('roundtrips with fromBase64url', () => {
    const original = new Uint8Array([0, 1, 2, 255, 128, 64, 32, 16])
    const encoded = base64url(original)
    const decoded = fromBase64url(encoded)
    expect(new Uint8Array(decoded)).toEqual(original)
  })
})

describe('fromBase64url', () => {
  it('decodes a basic string', () => {
    const result = fromBase64url('aGVsbG8')
    expect(new TextDecoder().decode(result)).toBe('hello')
  })

  it('handles padding restoration', () => {
    const result = fromBase64url('aA')
    expect(new TextDecoder().decode(result)).toBe('h')
  })

  it('handles URL-safe chars back to standard', () => {
    const result = fromBase64url('Pj-_')
    const expected = new Uint8Array([0x3e, 0x3f, 0xbf])
    expect(new Uint8Array(result)).toEqual(expected)
  })
})

// ============================================================
//  PASSWORD HASHING
// ============================================================

describe('hashPassword / verifyPassword', () => {
  it('hashes a password successfully', async () => {
    const hash = await hashPassword('test123')
    expect(hash).toMatch(/^\$pbkdf2-sha256\$100000\$.+\$.+$/)
  })

  it('produces different hashes for same password (different salts)', async () => {
    const hash1 = await hashPassword('password')
    const hash2 = await hashPassword('password')
    expect(hash1).not.toBe(hash2)
  })

  it('verifies correct password', async () => {
    const hash = await hashPassword('mySecret!')
    const valid = await verifyPassword('mySecret!', hash)
    expect(valid).toBe(true)
  })

  it('rejects incorrect password', async () => {
    const hash = await hashPassword('mySecret!')
    const valid = await verifyPassword('wrongPassword', hash)
    expect(valid).toBe(false)
  })

  it('rejects empty password against real hash', async () => {
    const hash = await hashPassword('mySecret!')
    const valid = await verifyPassword('', hash)
    expect(valid).toBe(false)
  })

  it('throws on unsupported hash format', async () => {
    await expect(verifyPassword('pass', 'invalid$format')).rejects.toThrow('Unsupported hash format')
  })
})

// ============================================================
//  JWT
// ============================================================

describe('signJWT / verifyJWT', () => {
  const secret = 'test-secret-key-12345'

  it('signs a payload successfully', async () => {
    const token = await signJWT({ userId: 1, email: 'test@test.com' }, secret)
    expect(token.split('.')).toHaveLength(3)
  })

  it('verifies a valid token', async () => {
    const token = await signJWT({ userId: 42, email: 'user@test.com' }, secret)
    const payload = await verifyJWT(token, secret)
    expect(payload).not.toBeNull()
    expect(payload!.userId).toBe(42)
    expect(payload!.email).toBe('user@test.com')
  })

  it('rejects token with wrong secret', async () => {
    const token = await signJWT({ userId: 1 }, secret)
    const payload = await verifyJWT(token, 'different-secret')
    expect(payload).toBeNull()
  })

  it('rejects tampered token', async () => {
    const token = await signJWT({ userId: 1 }, secret)
    const parts = token.split('.')
    // Use a clearly different header: {"alg":"HS256","typ":"JWT","extra":"hack"}
    const fakeHeader = base64url(new TextEncoder().encode(JSON.stringify({ alg: 'HS256', typ: 'JWT', extra: 'hack' })))
    const tampered = `${fakeHeader}.${parts[1]}.${parts[2]}`
    const payload = await verifyJWT(tampered, secret)
    expect(payload).toBeNull()
  })

  it('rejects expired token', async () => {
    const token = await signJWT({ userId: 1, exp: Math.floor(Date.now() / 1000) - 3600 }, secret)
    const payload = await verifyJWT(token, secret)
    expect(payload).toBeNull()
  })

  it('rejects malformed tokens', async () => {
    expect(await verifyJWT('not-a-valid-token', secret)).toBeNull()
    expect(await verifyJWT('a.b.c.d', secret)).toBeNull()
    expect(await verifyJWT('', secret)).toBeNull()
  })

  it('accepts token with future expiry', async () => {
    const exp = Math.floor(Date.now() / 1000) + 3600
    const token = await signJWT({ userId: 1, exp }, secret)
    const payload = await verifyJWT(token, secret)
    expect(payload).not.toBeNull()
    expect(payload!.userId).toBe(1)
  })
})

// ============================================================
//  base64urlEncode / base64urlDecode
// ============================================================

describe('base64urlEncode / base64urlDecode', () => {
  it('encodes and decodes an object', () => {
    const obj = { foo: 'bar', num: 42, nested: { a: 1 } }
    const encoded = base64urlEncode(obj)
    const decoded = base64urlDecode<typeof obj>(encoded)
    expect(decoded).toEqual(obj)
  })

  it('handles empty object', () => {
    const encoded = base64urlEncode({})
    const decoded = base64urlDecode<Record<string, unknown>>(encoded)
    expect(decoded).toEqual({})
  })
})
