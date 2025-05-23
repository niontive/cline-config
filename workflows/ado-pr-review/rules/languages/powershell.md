# PowerShell Code Review Guidelines

## PowerShell-Specific Best Practices

### Naming Conventions
- **Functions**: Use approved verbs (Get-, Set-, New-, Remove-) with PascalCase nouns
- **Variables**: Use camelCase ($userName, $connectionString)
- **Parameters**: Use PascalCase (-UserName, -ConnectionString)
- **Constants**: Use UPPER_CASE ($MAX_RETRY_COUNT)
- **Modules**: Use PascalCase (UserManagement.psm1)

### PowerShell Approved Verbs
```powershell
# ✅ Good: Using approved verbs
function Get-UserData { }
function Set-UserProperty { }
function New-UserAccount { }
function Remove-UserAccount { }
function Test-UserExists { }

# ❌ Bad: Using non-approved verbs
function Retrieve-UserData { }  # Use Get-
function Create-UserAccount { } # Use New-
function Delete-UserAccount { } # Use Remove-
```

### Parameter Best Practices
```powershell
# ✅ Good: Proper parameter definition
function Get-UserInfo {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true, ValueFromPipeline = $true)]
        [ValidateNotNullOrEmpty()]
        [string]$UserName,
        
        [Parameter()]
        [ValidateSet('Active', 'Inactive', 'All')]
        [string]$Status = 'Active',
        
        [Parameter()]
        [switch]$IncludeGroups
    )
    
    process {
        # Function logic here
    }
}
```

## Review Checklist

### 🔴 Critical Issues

#### Security
- [ ] No hardcoded credentials or API keys
- [ ] Sensitive data is handled securely (SecureString, PSCredential)
- [ ] Input validation prevents injection attacks
- [ ] Execution policy considerations documented
- [ ] No unsafe .NET method calls without validation

#### Error Handling
- [ ] Try-catch blocks used for error-prone operations
- [ ] Meaningful error messages provided
- [ ] $ErrorActionPreference set appropriately
- [ ] Terminating vs non-terminating errors handled correctly
- [ ] Clean resource disposal in finally blocks

#### Performance & Resource Management
- [ ] Large datasets processed efficiently (streaming, chunking)
- [ ] COM objects properly released
- [ ] File handles and connections closed
- [ ] Memory usage optimized for large operations
- [ ] No infinite loops or runaway processes

### 🟠 High Priority

#### Function Design
- [ ] Functions follow single responsibility principle
- [ ] [CmdletBinding()] attribute used for advanced functions
- [ ] Parameters have proper validation attributes
- [ ] Pipeline input supported where appropriate
- [ ] Return objects, not formatted text

#### Module Structure
- [ ] Module manifest (.psd1) properly configured
- [ ] Functions exported explicitly
- [ ] Dependencies clearly declared
- [ ] Version information maintained
- [ ] Module follows PowerShell naming conventions

#### Script Organization
- [ ] Requires statements at top of script
- [ ] Parameters defined with param block
- [ ] Functions defined before usage
- [ ] Main script logic clearly separated
- [ ] Exit codes used appropriately

### 🟡 Medium Priority

#### Code Quality
- [ ] Variables have meaningful names
- [ ] Functions are reasonably sized (<100 lines)
- [ ] Code follows PowerShell style guidelines
- [ ] Comments explain complex business logic
- [ ] No unused variables or parameters

#### Testing
- [ ] Pester tests for functions
- [ ] Mock external dependencies
- [ ] Test both success and failure scenarios
- [ ] Integration tests for complete workflows
- [ ] Performance tests for critical operations

### 🔵 Low Priority

#### Documentation
- [ ] Comment-based help for functions
- [ ] Examples provided in help
- [ ] Parameter descriptions clear
- [ ] Module documentation exists
- [ ] Change log maintained

## Common PowerShell Anti-Patterns

### Variable and Parameter Anti-Patterns
```powershell
# ❌ Bad: Inconsistent naming
$userName = "john"
$user_id = 123
$USERACTIVE = $true

# ✅ Good: Consistent camelCase
$userName = "john"
$userId = 123
$userActive = $true

# ❌ Bad: No parameter validation
function Get-User {
    param($Name)
    Get-ADUser $Name
}

# ✅ Good: Proper parameter validation
function Get-User {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [ValidateNotNullOrEmpty()]
        [string]$Name
    )
    
    try {
        Get-ADUser $Name -ErrorAction Stop
    }
    catch {
        Write-Error "Failed to get user '$Name': $($_.Exception.Message)"
    }
}
```

### Error Handling Anti-Patterns
```powershell
# ❌ Bad: Silent error suppression
Get-Process NonExistentProcess 2>$null

# ❌ Bad: Generic error handling
try {
    Get-Process $ProcessName
}
catch {
    Write-Host "Error occurred"
}

# ✅ Good: Specific error handling
try {
    Get-Process $ProcessName -ErrorAction Stop
}
catch [Microsoft.PowerShell.Commands.ProcessCommandException] {
    Write-Warning "Process '$ProcessName' not found"
}
catch {
    Write-Error "Unexpected error getting process: $($_.Exception.Message)"
    throw
}
```

### Output Anti-Patterns
```powershell
# ❌ Bad: Outputting formatted text
function Get-UserSummary {
    param($UserName)
    $user = Get-ADUser $UserName
    Write-Output "User: $($user.Name), Email: $($user.EmailAddress)"
}

# ✅ Good: Outputting objects
function Get-UserSummary {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$UserName
    )
    
    $user = Get-ADUser $UserName -Properties EmailAddress
    [PSCustomObject]@{
        Name = $user.Name
        Email = $user.EmailAddress
        SamAccountName = $user.SamAccountName
    }
}
```

## Security Best Practices

### Credential Management
```powershell
# ✅ Good: Using SecureString
$securePassword = Read-Host "Enter password" -AsSecureString
$credential = New-Object System.Management.Automation.PSCredential($username, $securePassword)

# ✅ Good: Using credential parameter
function Connect-ToService {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [PSCredential]$Credential,
        
        [Parameter(Mandatory = $true)]
        [string]$ServerName
    )
    
    # Use credential safely
}

# ❌ Bad: Hardcoded credentials
$password = "MyPassword123"
$username = "admin"
```

### Input Validation
```powershell
# ✅ Good: Comprehensive input validation
function Set-UserProperty {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [ValidatePattern('^[a-zA-Z0-9._-]+$')]
        [string]$UserName,
        
        [Parameter(Mandatory = $true)]
        [ValidateSet('Title', 'Department', 'Manager')]
        [string]$Property,
        
        [Parameter(Mandatory = $true)]
        [ValidateLength(1, 256)]
        [string]$Value
    )
    
    # Safe to use parameters
}
```

### Safe Execution
```powershell
# ✅ Good: Using -WhatIf support
function Remove-UserAccount {
    [CmdletBinding(SupportsShouldProcess)]
    param(
        [Parameter(Mandatory = $true)]
        [string]$UserName
    )
    
    if ($PSCmdlet.ShouldProcess($UserName, "Remove User Account")) {
        Remove-ADUser $UserName -Confirm:$false
    }
}

# ✅ Good: Validating paths
function Process-LogFile {
    param(
        [Parameter(Mandatory = $true)]
        [ValidateScript({Test-Path $_ -PathType Leaf})]
        [string]$LogPath
    )
    
    $resolvedPath = Resolve-Path $LogPath
    # Process file safely
}
```

## Performance Optimization

### Efficient Data Processing
```powershell
# ❌ Bad: Processing one item at a time
function Get-UserDetails {
    param([string[]]$UserNames)
    
    foreach ($user in $UserNames) {
        Get-ADUser $user
    }
}

# ✅ Good: Batch processing
function Get-UserDetails {
    param([string[]]$UserNames)
    
    Get-ADUser -Filter * | Where-Object { $_.SamAccountName -in $UserNames }
}

# ✅ Good: Pipeline processing
function Process-Users {
    [CmdletBinding()]
    param(
        [Parameter(ValueFromPipeline = $true)]
        [string]$UserName
    )
    
    process {
        Get-ADUser $UserName
    }
}
```

### Memory Efficient Operations
```powershell
# ❌ Bad: Loading entire dataset into memory
$allUsers = Get-ADUser -Filter * -Properties *
$inactiveUsers = $allUsers | Where-Object { $_.LastLogonDate -lt (Get-Date).AddDays(-90) }

# ✅ Good: Server-side filtering
$inactiveUsers = Get-ADUser -Filter "LastLogonDate -lt '$((Get-Date).AddDays(-90))'" -Properties LastLogonDate
```

## Testing Best Practices

### Pester Test Structure
```powershell
# UserManagement.Tests.ps1
Describe "Get-UserInfo" {
    BeforeAll {
        # Import module
        Import-Module "$PSScriptRoot\UserManagement.psm1" -Force
    }
    
    Context "When user exists" {
        BeforeEach {
            Mock Get-ADUser { 
                [PSCustomObject]@{
                    Name = "John Doe"
                    SamAccountName = "jdoe"
                    EmailAddress = "john.doe@company.com"
                }
            }
        }
        
        It "Should return user object" {
            $result = Get-UserInfo -UserName "jdoe"
            $result.Name | Should -Be "John Doe"
            $result.SamAccountName | Should -Be "jdoe"
        }
        
        It "Should call Get-ADUser with correct parameters" {
            Get-UserInfo -UserName "jdoe"
            Assert-MockCalled Get-ADUser -ParameterFilter { $Identity -eq "jdoe" }
        }
    }
    
    Context "When user does not exist" {
        BeforeEach {
            Mock Get-ADUser { throw "Cannot find an object with identity: 'nonexistent'" }
        }
        
        It "Should throw meaningful error" {
            { Get-UserInfo -UserName "nonexistent" } | Should -Throw "*Cannot find user*"
        }
    }
}
```

### Mock External Dependencies
```powershell
# Mock Active Directory cmdlets
Mock Get-ADUser { 
    [PSCustomObject]@{
        Name = "Test User"
        SamAccountName = $Identity
    }
} -ParameterFilter { $Identity -eq "testuser" }

# Mock REST API calls
Mock Invoke-RestMethod {
    @{
        Status = "Success"
        Data = @{ Id = 123; Name = "Test" }
    }
} -ParameterFilter { $Uri -like "*api.example.com*" }

# Mock file operations
Mock Get-Content { "line1", "line2", "line3" } -ParameterFilter { $Path -eq "test.txt" }
```

## Module Development

### Module Manifest Best Practices
```powershell
# UserManagement.psd1
@{
    RootModule = 'UserManagement.psm1'
    ModuleVersion = '1.0.0'
    GUID = '12345678-1234-1234-1234-123456789012'
    Author = 'Your Name'
    CompanyName = 'Your Company'
    Copyright = '(c) 2024 Your Company. All rights reserved.'
    Description = 'Module for managing user accounts'
    
    PowerShellVersion = '5.1'
    RequiredModules = @('ActiveDirectory')
    
    FunctionsToExport = @('Get-UserInfo', 'Set-UserProperty', 'New-UserAccount')
    CmdletsToExport = @()
    VariablesToExport = @()
    AliasesToExport = @()
    
    PrivateData = @{
        PSData = @{
            Tags = @('ActiveDirectory', 'Users', 'Management')
            LicenseUri = 'https://opensource.org/licenses/MIT'
            ProjectUri = 'https://github.com/yourorg/usermanagement'
            ReleaseNotes = 'Initial release'
        }
    }
}
```

### Comment-Based Help
```powershell
function Get-UserInfo {
    <#
    .SYNOPSIS
    Retrieves user information from Active Directory.
    
    .DESCRIPTION
    This function retrieves detailed user information from Active Directory
    based on the provided username or email address.
    
    .PARAMETER UserName
    The username (SamAccountName) of the user to retrieve.
    
    .PARAMETER EmailAddress
    The email address of the user to retrieve. Alternative to UserName.
    
    .PARAMETER IncludeGroups
    Include group membership information in the output.
    
    .EXAMPLE
    Get-UserInfo -UserName "jdoe"
    Retrieves information for user with username "jdoe".
    
    .EXAMPLE
    Get-UserInfo -EmailAddress "john.doe@company.com" -IncludeGroups
    Retrieves user information including group membership by email address.
    
    .INPUTS
    String. You can pipe usernames to this function.
    
    .OUTPUTS
    PSCustomObject. Returns user information object.
    
    .NOTES
    Requires ActiveDirectory module and appropriate permissions.
    
    .LINK
    https://docs.microsoft.com/powershell/module/activedirectory/get-aduser
    #>
    
    [CmdletBinding(DefaultParameterSetName = 'ByUserName')]
    param(
        [Parameter(ParameterSetName = 'ByUserName', Mandatory = $true, ValueFromPipeline = $true)]
        [ValidateNotNullOrEmpty()]
        [string]$UserName,
        
        [Parameter(ParameterSetName = 'ByEmail', Mandatory = $true)]
        [ValidatePattern('^[^\s@]+@[^\s@]+\.[^\s@]+$')]
        [string]$EmailAddress,
        
        [Parameter()]
        [switch]$IncludeGroups
    )
    
    process {
        # Function implementation
    }
}
```

## DSC (Desired State Configuration) Best Practices

### Configuration Structure
```powershell
Configuration WebServerConfig {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$ComputerName,
        
        [Parameter()]
        [PSCredential]$Credential
    )
    
    Import-DscResource -ModuleName PSDesiredStateConfiguration
    Import-DscResource -ModuleName xWebAdministration
    
    Node $ComputerName {
        WindowsFeature IIS {
            Ensure = "Present"
            Name = "IIS-WebServerRole"
        }
        
        WindowsFeature AspNet45 {
            Ensure = "Present"
            Name = "IIS-AspNet45"
            DependsOn = "[WindowsFeature]IIS"
        }
        
        xWebsite DefaultSite {
            Ensure = "Present"
            Name = "Default Web Site"
            State = "Stopped"
            DependsOn = "[WindowsFeature]IIS"
        }
    }
}
```

## Common PowerShell Security Issues

### Execution Policy Bypass
```powershell
# ❌ Bad: Bypassing execution policy unsafely
powershell -ExecutionPolicy Bypass -File "untrusted.ps1"

# ✅ Good: Using signed scripts or proper policy
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
# Or use code signing for production scripts
```

### Script Injection Prevention
```powershell
# ❌ Bad: Using Invoke-Expression with user input
$userInput = Read-Host "Enter command"
Invoke-Expression $userInput

# ✅ Good: Validate and sanitize input
$allowedCommands = @('Get-Process', 'Get-Service', 'Get-EventLog')
if ($userInput -in $allowedCommands) {
    & $userInput
} else {
    Write-Error "Command not allowed"
}
```

### Logging Security Events
```powershell
# ✅ Good: Secure logging practices
function Write-SecurityLog {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Message,
        
        [Parameter()]
        [string]$User = $env:USERNAME,
        
        [Parameter()]
        [ValidateSet('Information', 'Warning', 'Error')]
        [string]$Level = 'Information'
    )
    
    $logEntry = @{
        Timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
        User = $User
        Level = $Level
        Message = $Message
        Computer = $env:COMPUTERNAME
    }
    
    # Log to event log (avoid logging sensitive data)
    Write-EventLog -LogName Application -Source "MyApplication" -EventId 1001 -EntryType $Level -Message ($logEntry | ConvertTo-Json)
}
