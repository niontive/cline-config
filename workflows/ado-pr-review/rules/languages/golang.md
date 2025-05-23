# Go Code Review Guidelines

## Go-Specific Best Practices

### Naming Conventions
- **Package Names**: Short, lowercase, single words (avoid underscores)
- **Variable Names**: Use camelCase, be descriptive
- **Constants**: Use CamelCase for exported, camelCase for unexported
- **Functions**: Exported functions start with capital letter
- **Interfaces**: Single-method interfaces should end with "-er" (Reader, Writer)

### Error Handling
```go
// ✅ Good: Explicit error handling
result, err := doSomething()
if err != nil {
    return fmt.Errorf("failed to do something: %w", err)
}

// ❌ Bad: Ignoring errors
result, _ := doSomething()
```

### Goroutines and Concurrency
- **Context Usage**: Always pass context.Context as first parameter
- **Channel Closing**: Close channels in the sender, not receiver
- **WaitGroups**: Use sync.WaitGroup for coordinating goroutines
- **Avoid Shared State**: Prefer channels over shared variables
- **Race Conditions**: Check for data races with `go run -race`

### Memory Management
- **Slice Capacity**: Be mindful of slice capacity to avoid unnecessary allocations
- **String Concatenation**: Use strings.Builder for multiple concatenations
- **Defer Cleanup**: Use defer for resource cleanup
- **Pointer Usage**: Use pointers judiciously, prefer value types when possible

## Review Checklist

### 🔴 Critical Issues

#### Error Handling
- [ ] All errors are handled explicitly (no `_` for error returns)
- [ ] Error messages provide context using `fmt.Errorf` with `%w` verb
- [ ] Custom errors implement the error interface properly
- [ ] No panic() in library code (except for truly unrecoverable situations)

#### Concurrency Safety
- [ ] Shared data is protected by mutexes or channels
- [ ] No data races (run with -race flag)
- [ ] Goroutines have proper lifecycle management
- [ ] Context cancellation is respected

#### Resource Management
- [ ] Files, network connections, and other resources are closed
- [ ] defer statements are used for cleanup
- [ ] No goroutine leaks

### 🟠 High Priority

#### Performance
- [ ] No unnecessary allocations in hot paths
- [ ] Slice operations don't cause unnecessary copying
- [ ] String operations use efficient methods (strings.Builder)
- [ ] Database queries are optimized

#### Package Structure
- [ ] Package names are descriptive and follow conventions
- [ ] Cyclic dependencies are avoided
- [ ] Internal packages are used appropriately
- [ ] Public APIs are minimal and well-designed

### 🟡 Medium Priority

#### Code Style
- [ ] gofmt has been run
- [ ] golint warnings are addressed
- [ ] Variable names are descriptive
- [ ] Functions are reasonably sized (<50 lines)

#### Testing
- [ ] Unit tests cover main functionality
- [ ] Table-driven tests are used where appropriate
- [ ] Test names follow TestXxx pattern and are descriptive
- [ ] Benchmark tests for performance-critical code

### 🔵 Low Priority

#### Documentation
- [ ] Public functions have doc comments
- [ ] Package has package doc comment
- [ ] Examples are provided for complex APIs
- [ ] README is updated for new features

## Common Go Anti-Patterns

### Error Handling Anti-Patterns
```go
// ❌ Bad: Ignoring errors
data, _ := json.Marshal(obj)

// ❌ Bad: Generic error messages
if err != nil {
    return errors.New("something went wrong")
}

// ✅ Good: Descriptive error with context
if err != nil {
    return fmt.Errorf("failed to marshal user data: %w", err)
}
```

### Goroutine Anti-Patterns
```go
// ❌ Bad: Goroutine without cleanup
go func() {
    for {
        select {
        case data := <-ch:
            process(data)
        }
    }
}()

// ✅ Good: Goroutine with context cancellation
go func() {
    for {
        select {
        case data := <-ch:
            process(data)
        case <-ctx.Done():
            return
        }
    }
}()
```

### Interface Anti-Patterns
```go
// ❌ Bad: Large interface
type UserService interface {
    CreateUser(user User) error
    UpdateUser(user User) error
    DeleteUser(id string) error
    GetUser(id string) (User, error)
    ListUsers() ([]User, error)
    ValidateUser(user User) error
    SendEmail(user User, message string) error
}

// ✅ Good: Small, focused interfaces
type UserRepository interface {
    Create(user User) error
    Update(user User) error
    Delete(id string) error
    Get(id string) (User, error)
    List() ([]User, error)
}

type UserValidator interface {
    Validate(user User) error
}

type EmailSender interface {
    Send(to string, message string) error
}
```

## Go-Specific Security Considerations

### Input Validation
- Validate all inputs, especially from HTTP requests
- Use strconv package for type conversions
- Sanitize inputs used in SQL queries or shell commands
- Check slice/map bounds before access

### Crypto Usage
- Use crypto/rand for random number generation
- Use proper key sizes (AES-256, RSA-2048+)
- Don't implement custom cryptographic algorithms
- Use constant-time comparison for secrets

### Web Security
- Use HTTPS in production
- Validate and sanitize all user inputs
- Use proper session management
- Implement CSRF protection
- Set appropriate HTTP security headers

## Module and Dependency Management

### go.mod Best Practices
- Use semantic versioning for releases
- Keep dependencies up to date
- Use `go mod tidy` to clean up unused dependencies
- Pin dependencies for reproducible builds
- Use `replace` directives sparingly and document why

### Vendor Management
- Consider vendoring for production applications
- Document the vendoring strategy
- Keep vendor directory out of version control if using go.mod
- Regularly audit dependencies for security vulnerabilities

## Performance Considerations

### Allocation Optimization
- Use object pooling for frequently allocated objects
- Prefer value types over pointer types when possible
- Use slice capacity hints when size is known
- Avoid string concatenation in loops

### Benchmark Guidelines
- Write benchmarks for performance-critical code
- Use `testing.B.ReportAllocs()` to track allocations
- Profile code using `go tool pprof`
- Set up continuous benchmarking for regressions

## Testing Best Practices

### Test Structure
```go
func TestUserCreation(t *testing.T) {
    tests := []struct {
        name     string
        input    User
        expected error
    }{
        {
            name:     "valid user",
            input:    User{Name: "John", Email: "john@example.com"},
            expected: nil,
        },
        {
            name:     "missing email",
            input:    User{Name: "John"},
            expected: ErrMissingEmail,
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            err := CreateUser(tt.input)
            if err != tt.expected {
                t.Errorf("expected %v, got %v", tt.expected, err)
            }
        })
    }
}
```

### Mock Usage
- Use interfaces for testability
- Generate mocks with tools like gomock
- Keep mocks simple and focused
- Test both success and failure scenarios
