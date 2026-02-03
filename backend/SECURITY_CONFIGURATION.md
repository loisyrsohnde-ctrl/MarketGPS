# Security Configuration Guide

## Overview

This document describes the security configuration for the MarketGPS backend, including CORS (Cross-Origin Resource Sharing) settings and HTTP security headers.

## Files Modified/Created

1. **main.py** - Updated FastAPI application with corrected CORS configuration and security headers middleware
2. **security_config.py** - New centralized configuration file for all security settings

## CORS Configuration

### What Changed

The CORS configuration has been updated to follow security best practices:

#### Before (Insecure)
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],  # ❌ Allows ANY header - security risk!
)
```

#### After (Secure)
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "Accept",
        "Origin",
        "X-Requested-With",
        "X-CSRF-Token",
        "Stripe-Signature",
    ],
    expose_headers=[
        "Content-Range",
        "X-Content-Range",
        "X-Total-Count",
    ],
    max_age=3600,  # Cache preflight for 1 hour
)
```

### Key Improvements

1. **Explicit allow_headers**: Instead of `["*"]`, only necessary headers are allowed
   - `Content-Type`: For request body parsing
   - `Authorization`: For Bearer token authentication
   - `Accept`: For content negotiation
   - `Origin`: Required for CORS
   - `X-Requested-With`: Legacy header for AJAX detection
   - `X-CSRF-Token`: For CSRF protection
   - `Stripe-Signature`: For webhook signature verification

2. **Added HTTP methods**: PUT and PATCH for more complete REST support

3. **Exposed headers**: Explicitly declare which response headers clients can access

4. **Preflight caching**: Reduces unnecessary preflight requests (1 hour cache)

### Allowed Origins

The following origins are allowed:

**Production:**
- https://marketgps.online
- https://app.marketgps.online
- https://api.marketgps.online
- https://afristocks.eu
- https://app.afristocks.eu

**Development:**
- http://localhost:8501
- http://127.0.0.1:8501
- http://localhost:3000
- http://127.0.0.1:3000
- http://localhost:3001
- http://127.0.0.1:3001

**Custom Origins**: Additional origins can be added via the `CORS_ORIGINS` environment variable (comma-separated).

## HTTP Security Headers

A new middleware `SecurityHeadersMiddleware` adds the following security headers to all responses:

### 1. X-Content-Type-Options: nosniff
**Purpose**: Prevents MIME type sniffing attacks

**How it works**: Tells browsers to respect the Content-Type header and not try to guess the actual content type

**Value**: `nosniff`

### 2. X-Frame-Options: DENY
**Purpose**: Prevents clickjacking attacks

**How it works**: Prevents the page from being embedded in an iframe on any domain

**Value**: `DENY`
- `DENY`: Page cannot be framed at all
- `SAMEORIGIN`: Only same-origin frames allowed
- `ALLOW-FROM [URI]`: Only specific origin allowed

### 3. X-XSS-Protection: 1; mode=block
**Purpose**: Legacy XSS protection for older browsers

**How it works**: Enables XSS filter in older browsers and blocks page if XSS detected

**Value**: `1; mode=block`
- `1`: Enable XSS filter
- `mode=block`: Block page instead of sanitizing

### 4. Strict-Transport-Security: max-age=31536000; includeSubDomains
**Purpose**: Forces HTTPS connections and prevents downgrade attacks

**How it works**: Tells browsers to only connect via HTTPS for the next 31536000 seconds (1 year)

**Parameters**:
- `max-age=31536000`: Enforce for 1 year
- `includeSubDomains`: Apply to all subdomains
- Optional: `preload` for HSTS preload list inclusion

### 5. Content-Security-Policy (CSP)
**Purpose**: Comprehensive XSS and injection attack prevention

**Current Policy**:
```
default-src 'self';
script-src 'self' 'unsafe-inline' 'unsafe-eval';
style-src 'self' 'unsafe-inline';
img-src 'self' data: https:;
font-src 'self' data:;
connect-src 'self' https:;
frame-ancestors 'none';
base-uri 'self';
form-action 'self'
```

**Directives Explained**:
- `default-src 'self'`: Default to same-origin for all resources
- `script-src 'unsafe-inline' 'unsafe-eval'`: Allows scripts (includes unsafe for Streamlit compatibility)
- `style-src 'unsafe-inline'`: Allows inline styles
- `img-src data: https:`: Allows images from data URIs and HTTPS
- `connect-src 'self' https:`: Allows API calls to same-origin and HTTPS
- `frame-ancestors 'none'`: Cannot be embedded in frames
- `form-action 'self'`: Form submissions only to same origin
- `base-uri 'self'`: Limits base URL changes

**Note**: The `'unsafe-inline'` and `'unsafe-eval'` are included to support Streamlit compatibility. For maximum security, these should be restricted in production.

### 6. Referrer-Policy: strict-origin-when-cross-origin
**Purpose**: Controls what referrer information is sent

**How it works**:
- Same-site requests: Send full referrer
- Cross-site requests: Send only origin

**Values**:
- `strict-origin-when-cross-origin`: Current setting
- `no-referrer`: Never send referrer
- `same-origin`: Only send for same-origin
- `strict-origin`: Only send origin

### 7. Permissions-Policy
**Purpose**: Disable unnecessary browser features

**Current Disabled Features**:
- `accelerometer`: Motion sensor
- `camera`: Webcam access
- `geolocation`: GPS location
- `gyroscope`: Rotation sensor
- `magnetometer`: Compass
- `microphone`: Audio input
- `payment`: Payment Request API
- `usb`: USB access

## Configuration Management

### Using security_config.py

The `security_config.py` file centralizes all security settings:

```python
from security_config import (
    get_allowed_origins,
    ALLOWED_METHODS,
    ALLOWED_REQUEST_HEADERS,
    EXPOSED_HEADERS,
    CORS_MAX_AGE,
    CONTENT_TYPE_OPTIONS,
    FRAME_OPTIONS,
    XSS_PROTECTION,
    HSTS_HEADER,
    CSP_HEADER,
    REFERRER_POLICY,
    PERMISSIONS_POLICY,
)
```

### Environment Variables

**CORS_ORIGINS**: Add custom origins
```bash
export CORS_ORIGINS="https://custom.domain.com,https://another.domain.com"
```

### Modifying Security Settings

To modify security headers:

1. Edit `backend/security_config.py`
2. Update the corresponding constant
3. Restart the application

Example: To change CSP policy
```python
CSP_HEADER: str = "your-new-csp-policy"
```

## Testing Security Headers

### Using curl
```bash
curl -I https://api.marketgps.online/health
```

### Check headers
```bash
curl -I https://api.marketgps.online/health | grep -i "x-content-type-options\|x-frame-options\|strict-transport-security"
```

### Using online tools
- https://securityheaders.com
- https://csp-evaluator.withgoogle.com
- https://observatory.mozilla.org

## Security Checklist

- [x] CORS allows specific origins only
- [x] CORS allows specific headers (not wildcard)
- [x] CORS credentials properly configured
- [x] X-Content-Type-Options set to nosniff
- [x] X-Frame-Options set to DENY
- [x] X-XSS-Protection enabled
- [x] HSTS enabled (1 year, includeSubDomains)
- [x] CSP policy implemented
- [x] Referrer-Policy configured
- [x] Permissions-Policy configured
- [ ] HTTPS enforced in production
- [ ] Security headers validated with online tools
- [ ] CSP policy tested for compatibility
- [ ] HSTS preload submission (optional, for max security)

## Troubleshooting

### CORS Issues
If you see CORS errors:

1. Check that the origin is in the allowed list
2. Verify the origin URL format (protocol, domain, port)
3. Check that credentials are properly configured
4. Review preflight requests in browser DevTools

### CSP Violations
If resources fail to load:

1. Check browser console for CSP violation details
2. Update CSP_HEADER in security_config.py
3. Use `report-uri` or `report-to` for CSP violation reporting (optional)

### HSTS Issues
If you switch from HTTPS to HTTP:

1. HSTS will still enforce HTTPS for 1 year
2. Solution: Clear browser cache or use new domain
3. In development, consider reducing HSTS duration

## Best Practices

1. **Keep HSTS duration high** (1 year recommended) for production
2. **Review CSP policy regularly** for compatibility
3. **Monitor CSP violations** in production
4. **Test security headers** before deploying
5. **Update headers** when adding new features
6. **Document custom headers** for your team

## References

- [OWASP Secure Headers Project](https://owasp.org/www-project-secure-headers/)
- [MDN: CORS](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)
- [MDN: Content-Security-Policy](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Security-Policy)
- [NIST: Guidelines for HTTPS](https://csrc.nist.gov/publications/detail/sp/800-52/rev-2)
- [Mozilla Observatory](https://observatory.mozilla.org/)
