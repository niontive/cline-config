# Security Code Review Guidelines

## Security Review Principles

### Threat Modeling
- **Identify Attack Vectors**: Consider how an attacker might exploit the code
- **Data Flow Analysis**: Track sensitive data through the system
- **Trust Boundaries**: Identify where data crosses security boundaries
- **Privilege Escalation**: Check for unnecessary elevated permissions
- **Defense in Depth**: Ensure multiple layers of security controls

### Security by Design
- **Principle of Least Privilege**: Grant minimum necessary permissions
- **Fail Securely**: Ensure failures don't compromise security
- **Complete Mediation**: Check every access to protected resources
- **Open Design**: Security shouldn't depend on secrecy of implementation
- **Separation of Duties**: Divide critical operations among multiple actors

## Common Security Vulnerabilities

### 🔴 Critical Security Issues

#### Input Validation
```go
// ❌ Bad: No input validation
func getUserById(id string) (*User, error) {
    query := "SELECT * FROM users WHERE id = " + id
    // SQL injection vulnerability
}

// ✅ Good: Parameterized queries
func getUserById(id string) (*User, error) {
    if !isValidUUID(id) {
        return nil, errors.New("invalid user ID format")
    }
    query := "SELECT * FROM users WHERE id = ?"
    // Use parameterized query
}
```

#### Authentication & Authorization
```csharp
// ❌ Bad: No authorization check
[HttpGet("admin/users")]
public ActionResult<List<User>> GetAllUsers()
{
    return _userService.GetAllUsers();
}

// ✅ Good: Proper authorization
[HttpGet("admin/users")]
[Authorize(Roles = "Admin")]
public ActionResult<List<User>> GetAllUsers()
{
    return _userService.GetAllUsers();
}
```

#### Cryptographic Issues
```go
// ❌ Bad: Weak cryptography
password := md5.Sum([]byte(plaintext)) // MD5 is broken

// ❌ Bad: Hardcoded cryptographic keys
key := []byte("mysecretkey12345")

// ✅ Good: Strong cryptography
hashedPassword, err := bcrypt.GenerateFromPassword([]byte(plaintext), bcrypt.DefaultCost)

// ✅ Good: Key from secure source
key := os.Getenv("ENCRYPTION_KEY")
if len(key) != 32 {
    return errors.New("invalid key length")
}
```

### 🟠 High Priority Security Issues

#### Secrets Management
```bash
# ❌ Bad: Hardcoded credentials
API_KEY="sk-1234567890abcdef"
curl -H "Authorization: Bearer ${API_KEY}" https://api.example.com

# ✅ Good: Environment variables or secret management
if [[ -z "${API_KEY}" ]]; then
    echo "Error: API_KEY environment variable not set" >&2
    exit 1
fi
curl -H "Authorization: Bearer ${API_KEY}" https://api.example.com
```

#### Session Management
```csharp
// ❌ Bad: Insecure session handling
public void Login(string username, string password)
{
    if (ValidateUser(username, password))
    {
        Session["UserId"] = GetUserId(username);
        // No session expiration, regeneration, or secure flags
    }
}

// ✅ Good: Secure session management
public async Task<IActionResult> Login(LoginModel model)
{
    if (await ValidateUserAsync(model.Username, model.Password))
    {
        var claims = new List<Claim>
        {
            new Claim(ClaimTypes.Name, model.Username),
            new Claim(ClaimTypes.NameIdentifier, GetUserId(model.Username).ToString())
        };
        
        var identity = new ClaimsIdentity(claims, CookieAuthenticationDefaults.AuthenticationScheme);
        await HttpContext.SignInAsync(new ClaimsPrincipal(identity));
        
        return RedirectToAction("Dashboard");
    }
    
    return View("Login");
}
```

#### File Upload Security
```go
// ❌ Bad: Unrestricted file upload
func uploadFile(w http.ResponseWriter, r *http.Request) {
    file, header, err := r.FormFile("upload")
    if err != nil {
        http.Error(w, err.Error(), http.StatusBadRequest)
        return
    }
    
    // Save file without validation
    dst, _ := os.Create("uploads/" + header.Filename)
    io.Copy(dst, file)
}

// ✅ Good: Secure file upload
func uploadFile(w http.ResponseWriter, r *http.Request) {
    file, header, err := r.FormFile("upload")
    if err != nil {
        http.Error(w, err.Error(), http.StatusBadRequest)
        return
    }
    defer file.Close()
    
    // Validate file type
    allowedTypes := map[string]bool{
        "image/jpeg": true,
        "image/png":  true,
        "image/gif":  true,
    }
    
    buffer := make([]byte, 512)
    _, err = file.Read(buffer)
    if err != nil {
        http.Error(w, "Error reading file", http.StatusBadRequest)
        return
    }
    
    contentType := http.DetectContentType(buffer)
    if !allowedTypes[contentType] {
        http.Error(w, "File type not allowed", http.StatusBadRequest)
        return
    }
    
    // Generate safe filename
    safeFilename := generateSafeFilename(header.Filename)
    
    // Save to secure location with size limits
    file.Seek(0, 0) // Reset file pointer
    limited := io.LimitReader(file, 10*1024*1024) // 10MB limit
    
    dst, err := os.Create(filepath.Join("uploads", safeFilename))
    if err != nil {
        http.Error(w, "Error creating file", http.StatusInternalServerError)
        return
    }
    defer dst.Close()
    
    _, err = io.Copy(dst, limited)
    if err != nil {
        http.Error(w, "Error saving file", http.StatusInternalServerError)
        return
    }
}
```

## Language-Specific Security Patterns

### Go Security Patterns
```go
// ✅ Good: Input validation
func validateEmail(email string) error {
    if len(email) > 254 {
        return errors.New("email too long")
    }
    
    matched, err := regexp.MatchString(`^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`, email)
    if err != nil {
        return err
    }
    
    if !matched {
        return errors.New("invalid email format")
    }
    
    return nil
}

// ✅ Good: Secure random generation
func generateSecureToken() (string, error) {
    bytes := make([]byte, 32)
    _, err := rand.Read(bytes)
    if err != nil {
        return "", err
    }
    return base64.URLEncoding.EncodeToString(bytes), nil
}

// ✅ Good: Context timeout for external calls
func makeAPICall(ctx context.Context, url string) (*Response, error) {
    ctx, cancel := context.WithTimeout(ctx, 30*time.Second)
    defer cancel()
    
    req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
    if err != nil {
        return nil, err
    }
    
    client := &http.Client{
        Timeout: 30 * time.Second,
    }
    
    resp, err := client.Do(req)
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()
    
    return parseResponse(resp)
}
```

### C# Security Patterns
```csharp
// ✅ Good: Secure password hashing
public class PasswordService
{
    public string HashPassword(string password)
    {
        return BCrypt.Net.BCrypt.HashPassword(password, BCrypt.Net.BCrypt.GenerateSalt(12));
    }
    
    public bool VerifyPassword(string password, string hash)
    {
        return BCrypt.Net.BCrypt.Verify(password, hash);
    }
}

// ✅ Good: SQL injection prevention
public async Task<User> GetUserByEmailAsync(string email)
{
    const string sql = "SELECT Id, Email, Name FROM Users WHERE Email = @Email";
    
    using var connection = new SqlConnection(_connectionString);
    return await connection.QuerySingleOrDefaultAsync<User>(sql, new { Email = email });
}

// ✅ Good: XSS prevention
public IActionResult DisplayUserContent(string userContent)
{
    var sanitized = HttpUtility.HtmlEncode(userContent);
    ViewBag.Content = sanitized;
    return View();
}

// ✅ Good: CSRF protection
[HttpPost]
[ValidateAntiForgeryToken]
public async Task<IActionResult> UpdateProfile(ProfileModel model)
{
    // Action implementation
}
```

### PowerShell Security Patterns
```powershell
# ✅ Good: Input validation
function Test-SafeFilePath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )
    
    # Check for path traversal
    if ($Path -match '\.\.') {
        throw "Path traversal not allowed: $Path"
    }
    
    # Ensure path is within allowed directory
    $allowedBase = "C:\AllowedDirectory"
    $resolvedPath = [System.IO.Path]::GetFullPath($Path)
    
    if (-not $resolvedPath.StartsWith($allowedBase)) {
        throw "Path outside allowed directory: $Path"
    }
    
    return $true
}

# ✅ Good: Secure credential handling
function Connect-SecureService {
    param(
        [Parameter(Mandatory = $true)]
        [PSCredential]$Credential,
        
        [Parameter(Mandatory = $true)]
        [string]$ServiceUrl
    )
    
    # Don't log credentials
    Write-Verbose "Connecting to service at $ServiceUrl"
    
    try {
        # Use credential securely
        $secureConnection = New-Object SecureConnection -ArgumentList $ServiceUrl, $Credential
        return $secureConnection
    }
    catch {
        # Don't expose credential details in error messages
        Write-Error "Failed to connect to service"
        throw
    }
}

# ✅ Good: Safe command execution
function Invoke-SafeCommand {
    param(
        [Parameter(Mandatory = $true)]
        [ValidateSet('Get-Process', 'Get-Service', 'Get-EventLog')]
        [string]$Command,
        
        [Parameter()]
        [hashtable]$Parameters = @{}
    )
    
    # Use splatting with validated commands
    & $Command @Parameters
}
```

### Bash Security Patterns
```bash
# ✅ Good: Input validation
validate_input() {
    local input="$1"
    local pattern="$2"
    
    if [[ -z "${input}" ]]; then
        echo "Error: Input cannot be empty" >&2
        return 1
    fi
    
    if [[ ! "${input}" =~ ${pattern} ]]; then
        echo "Error: Input does not match required pattern" >&2
        return 1
    fi
    
    return 0
}

# ✅ Good: Secure file operations
secure_file_operation() {
    local source_file="$1"
    local dest_file="$2"
    
    # Validate inputs
    validate_input "${source_file}" '^[a-zA-Z0-9._/-]+$' || return 1
    validate_input "${dest_file}" '^[a-zA-Z0-9._/-]+$' || return 1
    
    # Check file exists and is readable
    if [[ ! -r "${source_file}" ]]; then
        echo "Error: Cannot read source file: ${source_file}" >&2
        return 1
    fi
    
    # Use temporary file for atomic operation
    local temp_file
    temp_file=$(mktemp) || {
        echo "Error: Failed to create temporary file" >&2
        return 1
    }
    
    # Set up cleanup
    trap "rm -f '${temp_file}'" EXIT
    
    # Perform operation
    if cp "${source_file}" "${temp_file}" && mv "${temp_file}" "${dest_file}"; then
        echo "File operation completed successfully"
        return 0
    else
        echo "Error: File operation failed" >&2
        return 1
    fi
}

# ✅ Good: Privilege dropping
drop_privileges() {
    if [[ "${EUID}" -eq 0 ]]; then
        # Running as root, drop to safer user
        local safe_user="nobody"
        local safe_group="nogroup"
        
        if command -v sudo >/dev/null 2>&1; then
            exec sudo -u "${safe_user}" -g "${safe_group}" "$0" "$@"
        else
            echo "Warning: Running as root without ability to drop privileges" >&2
        fi
    fi
}
```

## Security Review Checklist

### 🔴 Critical Security Checks

#### Authentication & Authorization
- [ ] All endpoints require appropriate authentication
- [ ] Authorization checks are performed at the right level
- [ ] Privilege escalation is not possible
- [ ] Session management is secure
- [ ] Password policies are enforced

#### Input Validation
- [ ] All user inputs are validated
- [ ] SQL injection prevention is in place
- [ ] XSS prevention is implemented
- [ ] Command injection is prevented
- [ ] File upload validation exists

#### Cryptography
- [ ] Strong cryptographic algorithms are used
- [ ] Keys are managed securely
- [ ] Random number generation is cryptographically secure
- [ ] Encryption is applied to sensitive data
- [ ] Hash functions are appropriate for use case

#### Data Protection
- [ ] Sensitive data is not logged
- [ ] Database connections are secure
- [ ] Data transmission is encrypted
- [ ] Backup data is protected
- [ ] Data retention policies are followed

### 🟠 High Priority Security Checks

#### Error Handling
- [ ] Error messages don't leak sensitive information
- [ ] Stack traces are not exposed to users
- [ ] Logging doesn't include sensitive data
- [ ] Error handling doesn't bypass security controls
- [ ] Failures fail securely

#### Configuration Security
- [ ] Default credentials are changed
- [ ] Unnecessary services are disabled
- [ ] Security headers are configured
- [ ] HTTPS is enforced
- [ ] CORS policies are restrictive

#### Dependency Security
- [ ] Dependencies are up to date
- [ ] Known vulnerable packages are not used
- [ ] Package integrity is verified
- [ ] License compliance is maintained
- [ ] Supply chain security is considered

### 🟡 Medium Priority Security Checks

#### Logging & Monitoring
- [ ] Security events are logged
- [ ] Log integrity is protected
- [ ] Monitoring for suspicious activity exists
- [ ] Audit trails are maintained
- [ ] Incident response procedures are documented

#### Business Logic Security
- [ ] Business rules are enforced server-side
- [ ] Race conditions are prevented
- [ ] State management is secure
- [ ] Workflow integrity is maintained
- [ ] Data consistency is ensured

## Security Testing

### Static Analysis
- Use tools like SonarQube, CodeQL, or Semgrep
- Check for common vulnerability patterns
- Enforce security coding standards
- Scan for hardcoded secrets
- Analyze dependency vulnerabilities

### Dynamic Testing
- Perform penetration testing
- Use security scanners (OWASP ZAP, Burp Suite)
- Test authentication and authorization
- Validate input handling
- Check for injection vulnerabilities

### Security Code Review Process
1. **Threat Modeling**: Identify potential attack vectors
2. **Code Analysis**: Review code for security issues
3. **Dependency Review**: Check third-party libraries
4. **Configuration Review**: Verify security settings
5. **Testing Validation**: Ensure security tests pass
6. **Documentation**: Document security considerations

## Compliance Considerations

### Data Privacy (GDPR, CCPA)
- [ ] Personal data is identified and protected
- [ ] Data processing purposes are documented
- [ ] User consent mechanisms exist
- [ ] Data retention policies are implemented
- [ ] Data deletion capabilities exist

### Industry Standards (SOC 2, PCI DSS)
- [ ] Access controls meet requirements
- [ ] Audit logging is comprehensive
- [ ] Encryption standards are followed
- [ ] Change management processes exist
- [ ] Incident response procedures are documented

### Security Frameworks (NIST, ISO 27001)
- [ ] Security controls are mapped to frameworks
- [ ] Risk assessments are conducted
- [ ] Security policies are defined
- [ ] Training and awareness programs exist
- [ ] Continuous monitoring is implemented
