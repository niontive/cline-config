# Dependency Review Guidelines

## Dependency Security and Management

### Dependency Analysis Checklist

#### 🔴 Critical Issues

##### Security Vulnerabilities
- [ ] No known high/critical CVEs in dependencies
- [ ] Dependencies are from trusted sources
- [ ] No dependencies with malicious code history
- [ ] Supply chain attacks are mitigated
- [ ] Package integrity can be verified

##### License Compliance
- [ ] All dependency licenses are compatible
- [ ] No GPL licenses in proprietary code (unless intended)
- [ ] License obligations are documented
- [ ] Commercial license fees are accounted for
- [ ] Attribution requirements are met

##### Version Management
- [ ] Dependencies are pinned to specific versions
- [ ] No wildcard version specifications in production
- [ ] Breaking changes are documented
- [ ] Rollback strategy exists for upgrades
- [ ] Version conflicts are resolved

#### 🟠 High Priority Issues

##### Maintenance Status
- [ ] Dependencies are actively maintained
- [ ] Last update was within reasonable timeframe
- [ ] Security patches are available
- [ ] Community support exists
- [ ] Migration path available if deprecated

##### Performance Impact
- [ ] Bundle size impact is acceptable
- [ ] Runtime performance is not degraded
- [ ] Memory usage is reasonable
- [ ] Startup time impact is minimal
- [ ] Network requests are optimized

## Language-Specific Dependency Patterns

### Go Modules (go.mod)
```go
// ✅ Good: Pinned versions with checksums
module myapp

go 1.21

require (
    github.com/gin-gonic/gin v1.9.1
    github.com/go-sql-driver/mysql v1.7.1
    golang.org/x/crypto v0.13.0
)

// Indirect dependencies with checksums in go.sum
```

**Go Dependency Review Points:**
- [ ] go.mod uses specific versions (not latest)
- [ ] go.sum file includes checksums for integrity
- [ ] No dependencies with known vulnerabilities
- [ ] Minimal dependency tree (avoid bloat)
- [ ] Regular updates with security patches

### C# NuGet Packages
```xml
<!-- ✅ Good: Pinned versions with security considerations -->
<PackageReference Include="Microsoft.AspNetCore.Authentication.JwtBearer" Version="7.0.11" />
<PackageReference Include="Microsoft.EntityFrameworkCore" Version="7.0.11" />
<PackageReference Include="Serilog.AspNetCore" Version="7.0.0" />

<!-- ❌ Bad: Wildcard versions -->
<PackageReference Include="SomePackage" Version="*" />
<PackageReference Include="OtherPackage" Version="1.*" />
```

**C# Dependency Review Points:**
- [ ] PackageReference uses exact versions
- [ ] No outdated Microsoft packages
- [ ] Security updates are applied promptly
- [ ] Unused packages are removed
- [ ] License compatibility verified

### PowerShell Modules
```powershell
# ✅ Good: Specify minimum versions and trusted repositories
#Requires -Modules @{ ModuleName="Az.Accounts"; ModuleVersion="2.12.1" }
#Requires -Modules @{ ModuleName="Microsoft.Graph"; ModuleVersion="2.4.0" }

# In module manifest (.psd1)
RequiredModules = @(
    @{ ModuleName='Az.Accounts'; ModuleVersion='2.12.1' }
    @{ ModuleName='Microsoft.Graph'; ModuleVersion='2.4.0' }
)
```

**PowerShell Dependency Review Points:**
- [ ] Modules are from PowerShell Gallery or trusted sources
- [ ] Minimum version requirements specified
- [ ] Module signatures are verified when possible
- [ ] Execution policy considerations documented
- [ ] Module compatibility tested

### Bash/Shell Dependencies
```bash
#!/bin/bash

# ✅ Good: Check for required commands
check_dependencies() {
    local missing_deps=()
    
    command -v curl >/dev/null 2>&1 || missing_deps+=("curl")
    command -v jq >/dev/null 2>&1 || missing_deps+=("jq")
    command -v git >/dev/null 2>&1 || missing_deps+=("git")
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        echo "Error: Missing required dependencies: ${missing_deps[*]}" >&2
        echo "Please install missing dependencies and try again." >&2
        exit 1
    fi
}

# Verify specific versions when critical
verify_versions() {
    local curl_version
    curl_version=$(curl --version | head -n1 | cut -d' ' -f2)
    
    if [[ "$(printf '%s\n' "7.50.0" "$curl_version" | sort -V | head -n1)" != "7.50.0" ]]; then
        echo "Warning: curl version $curl_version may not support required features" >&2
    fi
}
```

**Bash Dependency Review Points:**
- [ ] All external commands are checked for availability
- [ ] Version requirements documented
- [ ] Installation instructions provided
- [ ] Fallback options considered
- [ ] Platform compatibility addressed

## Vulnerability Management

### Automated Scanning
```yaml
# Example: GitHub Actions dependency scanning
name: Dependency Check
on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - name: Run Snyk to check for vulnerabilities
      uses: snyk/actions/node@master
      env:
        SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
```

### Manual Review Process
1. **New Dependency Assessment**
   - Research package maintainer reputation
   - Review package source code for red flags
   - Check dependency tree for suspicious packages
   - Verify package signatures when available

2. **Regular Audits**
   - Monthly vulnerability scans
   - Quarterly dependency updates
   - Annual license compliance review
   - Security advisory monitoring

3. **Incident Response**
   - Immediate assessment of critical vulnerabilities
   - Emergency patching procedures
   - Communication plan for security issues
   - Rollback procedures if needed

## Dependency Policies

### Approval Process
- [ ] New dependencies require security team approval
- [ ] Major version updates need architecture review
- [ ] License changes require legal review
- [ ] Critical dependencies have backup plans

### Update Strategy
- [ ] Patch updates applied automatically (after testing)
- [ ] Minor updates reviewed monthly
- [ ] Major updates planned quarterly
- [ ] Security updates prioritized

### Removal Process
- [ ] Unused dependencies removed regularly
- [ ] Deprecation timeline for removing dependencies
- [ ] Impact assessment before removal
- [ ] Alternative solutions evaluated

## Common Dependency Anti-Patterns

### Version Management Anti-Patterns
```go
// ❌ Bad: Using latest or wildcard versions
require (
    github.com/some/package latest
    github.com/other/package v1.*
)

// ❌ Bad: Not tracking indirect dependencies
// Missing go.sum file or outdated checksums
```

```xml
<!-- ❌ Bad: Ranges that can introduce breaking changes -->
<PackageReference Include="SomePackage" Version="[1.0,2.0)" />
<PackageReference Include="OtherPackage" Version="1.*" />
```

### Security Anti-Patterns
```bash
# ❌ Bad: Installing packages without verification
curl -sSL https://get.docker.com/ | sh

# ❌ Bad: Using pip/npm with --trusted-host
pip install --trusted-host=untrusted.example.com package

# ✅ Good: Verify before installing
curl -sSL https://get.docker.com/ -o get-docker.sh
# Verify checksum or signature
sha256sum get-docker.sh
# Review script before execution
less get-docker.sh
bash get-docker.sh
```

### Bloat Anti-Patterns
```go
// ❌ Bad: Including entire frameworks for simple tasks
import "github.com/massive/framework" // Just for one utility function

// ✅ Good: Use specific, minimal packages
import "github.com/specific/utility"
```

## Dependency Documentation

### Required Documentation
- [ ] Dependency rationale (why this package?)
- [ ] Security considerations
- [ ] Performance impact assessment
- [ ] Alternatives considered
- [ ] Migration plan (if replacing existing dependency)

### Maintenance Documentation
- [ ] Update schedule and process
- [ ] Known issues and workarounds
- [ ] Configuration requirements
- [ ] Monitoring and alerting setup
- [ ] Rollback procedures

## Tools and Automation

### Security Scanning Tools
- **Snyk**: Vulnerability scanning and monitoring
- **OWASP Dependency Check**: Free security scanner
- **GitHub Dependabot**: Automated dependency updates
- **WhiteSource/Mend**: Enterprise dependency management

### License Scanning Tools
- **FOSSA**: License compliance and vulnerability management
- **Black Duck**: Open source security and license compliance
- **License Finder**: Ruby gem for license detection

### Version Management Tools
- **Renovate**: Automated dependency updates
- **Dependabot**: GitHub's dependency update bot
- **Greenkeeper**: Automated dependency updates for npm

## Best Practices Summary

### Security First
1. Scan for vulnerabilities before adding dependencies
2. Pin versions to prevent supply chain attacks
3. Verify package integrity with checksums
4. Monitor security advisories for dependencies
5. Have incident response plan for compromised packages

### Minimal Dependencies
1. Evaluate if functionality can be implemented internally
2. Prefer smaller, focused packages over large frameworks
3. Regularly audit and remove unused dependencies
4. Consider the full dependency tree, not just direct dependencies
5. Balance functionality vs. complexity

### Maintenance Planning
1. Establish update schedules and processes
2. Test updates in staging environments
3. Plan for dependency deprecation and migration
4. Document dependency decisions and rationale
5. Monitor dependency health and community activity
