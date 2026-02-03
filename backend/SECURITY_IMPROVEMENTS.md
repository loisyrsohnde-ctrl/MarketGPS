# Security Improvements Roadmap

## Recently Implemented (This Update)

### ✅ CORS Configuration Hardening
- **Status**: COMPLETED
- **Changes**: Replaced wildcard `allow_headers=["*"]` with explicit header list
- **Headers Added**: Content-Type, Authorization, Accept, Origin, X-Requested-With, X-CSRF-Token, Stripe-Signature
- **Methods Added**: PUT, PATCH (in addition to GET, POST, DELETE, OPTIONS)
- **Preflight Caching**: Added 1-hour cache for CORS preflight requests
- **Location**: `/backend/main.py` (lines 259-267)

### ✅ Security Headers Middleware
- **Status**: COMPLETED
- **Middleware**: `SecurityHeadersMiddleware` in `/backend/main.py`
- **Headers Added**:
  1. X-Content-Type-Options: nosniff
  2. X-Frame-Options: DENY
  3. X-XSS-Protection: 1; mode=block
  4. Strict-Transport-Security: max-age=31536000; includeSubDomains
  5. Content-Security-Policy: Comprehensive policy
  6. Referrer-Policy: strict-origin-when-cross-origin
  7. Permissions-Policy: Disables unnecessary features

### ✅ Configuration Management
- **Status**: COMPLETED
- **File**: New `/backend/security_config.py`
- **Benefits**:
  - Centralized configuration
  - Easy updates without modifying main.py
  - Environment variable support for custom origins
  - Better code organization

### ✅ Documentation & Testing
- **Status**: COMPLETED
- **Files Created**:
  1. `/backend/SECURITY_CONFIGURATION.md` - Comprehensive guide
  2. `/backend/test_security_headers.py` - Validation script

---

## Recommended Future Improvements

### Priority 1: Critical (Implement ASAP)

#### 1.1 Environment-Specific HSTS
**Description**: Make HSTS duration configurable based on environment
**Current**: Hardcoded to 1 year for all environments
**Recommendation**: Use shorter duration in development
```python
# In security_config.py
HSTS_MAX_AGE = int(os.getenv("HSTS_MAX_AGE", "31536000"))  # 1 year default
```

#### 1.2 CSP Violation Reporting
**Description**: Add CSP reporting endpoint to monitor violations
**Implementation**:
```python
CSP_HEADER = (
    "default-src 'self'; "
    # ... other directives ...
    "report-uri https://api.marketgps.online/api/csp-report"
)
```
**Endpoint**: Create `/api/csp-report` to log violations for analysis

#### 1.3 HTTPS Enforcement in Production
**Description**: Add middleware to redirect HTTP to HTTPS in production
```python
class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.headers.get("x-forwarded-proto") == "http":
            return RedirectResponse(
                url=request.url.replace("http://", "https://"),
                status_code=301
            )
        return await call_next(request)
```

#### 1.4 CORS Origins Rotation
**Description**: Implement origin rotation for environment variables
**Current Issue**: Origins are loaded at startup
**Solution**: Support dynamic origin updates (requires restart)
```python
@app.post("/admin/cors-origins")
async def update_cors_origins(origins: List[str]):
    """Update allowed CORS origins (admin only)"""
    # Requires authentication
```

---

### Priority 2: High (Implement in next sprint)

#### 2.1 Rate Limiting
**Description**: Implement rate limiting per origin/IP
**Package**: `slowapi`
```bash
pip install slowapi
```
**Implementation**:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.get("/health")
@limiter.limit("30/minute")
async def health_check(request: Request):
    return {"status": "healthy"}
```

#### 2.2 Input Validation & Sanitization
**Description**: Implement strict input validation on all endpoints
**Current**: Basic validation with Pydantic
**Enhancement**: Add request schema validation middleware
```python
class InputValidationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Validate request body size
        if request.headers.get("content-length"):
            size = int(request.headers["content-length"])
            if size > 1_000_000:  # 1MB limit
                return JSONResponse(
                    {"error": "Request too large"},
                    status_code=413
                )
        return await call_next(request)
```

#### 2.3 Security Headers Testing in CI/CD
**Description**: Add automated security header validation to pipeline
**File**: `.github/workflows/security.yml`
```yaml
- name: Test Security Headers
  run: python backend/test_security_headers.py https://staging-api.marketgps.online
```

#### 2.4 CORS Origin Validation
**Description**: Add logging for CORS rejections
**Implementation**:
```python
@app.middleware("http")
async def log_cors_rejections(request: Request, call_next):
    origin = request.headers.get("origin")
    if origin and origin not in ALLOWED_ORIGINS:
        logger.warning(f"CORS rejection: {origin}")
    return await call_next(request)
```

---

### Priority 3: Medium (Implement within 2 sprints)

#### 3.1 CSP Nonce for Inline Scripts
**Description**: Replace 'unsafe-inline' with nonce-based CSP
**Current**: Using 'unsafe-inline' for Streamlit compatibility
**Solution**: Generate nonce for each request
```python
import secrets

@app.middleware("http")
async def add_csp_nonce(request: Request, call_next):
    nonce = secrets.token_urlsafe(16)
    request.state.csp_nonce = nonce
    response = await call_next(request)
    # Update CSP header with nonce
    return response
```

#### 3.2 Subresource Integrity (SRI) for External Resources
**Description**: Add SRI hashes for external CDN resources
**Implementation**:
```html
<script
  src="https://cdn.example.com/library.js"
  integrity="sha384-HASH_HERE"
  crossorigin="anonymous">
</script>
```

#### 3.3 API Key Rotation Policy
**Description**: Implement automatic API key rotation
**Location**: Billing/Stripe keys
**Frequency**: Every 90 days
**Implementation**: Use AWS Secrets Manager or similar

#### 3.4 Authentication Header Validation
**Description**: Strict Bearer token validation
**Current**: Basic validation in `get_current_user_id_safe`
**Enhancement**: Add token expiration, signature validation, replay protection

---

### Priority 4: Low (Nice to have)

#### 4.1 HSTS Preload Submission
**Description**: Submit domain to HSTS preload list
**Requirement**: HSTS enabled with proper configuration
**Benefits**: Browser-level protection against HTTPS downgrade
**Process**:
1. Ensure HSTS header: `max-age=31536000; includeSubDomains; preload`
2. Visit https://hstspreload.org
3. Submit your domain

#### 4.2 Security.txt Implementation
**Description**: Add `.well-known/security.txt`
**RFC**: 9110
**Content**:
```
Contact: security@marketgps.online
Expires: 2025-02-01T00:00:00.000Z
Preferred-Languages: en
```

#### 4.3 Public Key Pinning (HPKP) - Optional
**Description**: Pin SSL certificate public keys
**Warning**: Can break site if misconfigured
**Current Status**: Generally not recommended (use HSTS preload instead)

#### 4.4 Frontend Security Headers Validation
**Description**: Validate security headers on frontend during development
**Tool**: Script in frontend repo to verify backend headers
```javascript
async function validateSecurityHeaders() {
  const response = await fetch('https://api.marketgps.online/health');
  const requiredHeaders = [
    'X-Content-Type-Options',
    'X-Frame-Options',
    'Strict-Transport-Security'
  ];
  // Check headers...
}
```

---

## Testing & Validation

### Manual Testing
```bash
# Test local development server
python backend/test_security_headers.py http://localhost:8501

# Test staging environment
python backend/test_security_headers.py https://staging-api.marketgps.online

# Test production
python backend/test_security_headers.py https://api.marketgps.online
```

### Online Security Scanners
1. **Security Headers Project**: https://securityheaders.com
2. **Mozilla Observatory**: https://observatory.mozilla.org
3. **CSP Evaluator**: https://csp-evaluator.withgoogle.com
4. **SSL Labs**: https://www.ssllabs.com/ssltest/

### Expected Grades
- **Before Changes**: C or D (CORS issues, missing headers)
- **After Implementation**: A or A+ (all security headers)

---

## Configuration Checklist

### Development Environment
- [ ] CORS configured for localhost:3000, localhost:8501
- [ ] HSTS duration set to 3600 (1 hour) for quick iteration
- [ ] CSP allows 'unsafe-inline' and 'unsafe-eval' for dev tools
- [ ] Logging enabled for CORS/security header issues

### Staging Environment
- [ ] CORS configured for staging domains only
- [ ] HSTS duration set to 86400 (1 day) for testing
- [ ] CSP in report-only mode to catch violations
- [ ] Rate limiting disabled or set to permissive limits
- [ ] Full security header validation enabled

### Production Environment
- [ ] CORS configured for production domains only
- [ ] HSTS duration set to 31536000 (1 year) with preload
- [ ] CSP in enforce mode with report endpoint
- [ ] Rate limiting enabled and configured
- [ ] Security headers validated with online tools
- [ ] HTTPS enforced with 301 redirects
- [ ] HTTPS certificate pinning (optional, advanced)

---

## Monitoring & Maintenance

### Log Monitoring
```python
# Monitor for CORS rejections
grep "CORS rejection" /var/log/marketgps-backend.log

# Monitor for CSP violations
grep "CSP violation" /var/log/marketgps-backend.log

# Monitor for security exceptions
grep "SecurityException" /var/log/marketgps-backend.log
```

### Regular Review
- **Monthly**: Check security header validation results
- **Quarterly**: Review CORS origins, update as needed
- **Quarterly**: Rotate API keys and credentials
- **Annual**: Submit for external security audit
- **Annual**: Update CSP policy based on new features

### Alerts
Set up alerts for:
- Increased CORS rejections (potential attack)
- CSP violations from legitimate sources (misconfiguration)
- Unusual API patterns (potential abuse)

---

## References & Resources

### Security Standards
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP Secure Headers](https://owasp.org/www-project-secure-headers/)
- [NIST Security Controls](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5)

### Implementation Guides
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [MDN Web Docs - HTTP Headers](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers)
- [Web Security Academy](https://portswigger.net/web-security)

### Tools
- [OWASP ZAP](https://www.zaproxy.org/) - Free security scanner
- [Burp Suite Community](https://portswigger.net/burp/communitydownload) - Web vulnerability scanner
- [Security Headers](https://securityheaders.com) - Header validation

### HTTP Headers Reference
- [RFC 7231: HTTP Semantics and Content](https://tools.ietf.org/html/rfc7231)
- [RFC 6797: HSTS](https://tools.ietf.org/html/rfc6797)
- [CSP Level 3](https://www.w3.org/TR/CSP3/)
- [CORS Specification](https://fetch.spec.whatwg.org/#cors-protocol)
