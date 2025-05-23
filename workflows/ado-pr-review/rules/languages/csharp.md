# C# Code Review Guidelines

## C#-Specific Best Practices

### Naming Conventions
- **Classes/Interfaces**: PascalCase (UserService, IUserRepository)
- **Methods/Properties**: PascalCase (GetUser, FirstName)
- **Fields**: camelCase with underscore prefix for private (_userName)
- **Local Variables**: camelCase (userCount, isValid)
- **Constants**: PascalCase (MaxRetryCount)
- **Parameters**: camelCase (userId, connectionString)

### SOLID Principles Application
- **Single Responsibility**: Each class should have one reason to change
- **Open/Closed**: Open for extension, closed for modification
- **Liskov Substitution**: Derived classes must be substitutable for base classes
- **Interface Segregation**: Clients shouldn't depend on interfaces they don't use
- **Dependency Inversion**: Depend on abstractions, not concretions

### Async/Await Best Practices
```csharp
// ✅ Good: Proper async method signature
public async Task<User> GetUserAsync(int userId)
{
    var user = await _repository.GetByIdAsync(userId);
    return user;
}

// ❌ Bad: Blocking async call
public User GetUser(int userId)
{
    return _repository.GetByIdAsync(userId).Result; // Deadlock risk
}

// ✅ Good: ConfigureAwait(false) in libraries
public async Task<User> GetUserAsync(int userId)
{
    var user = await _repository.GetByIdAsync(userId).ConfigureAwait(false);
    return user;
}
```

## Review Checklist

### 🔴 Critical Issues

#### Memory Management
- [ ] IDisposable objects are properly disposed (using statements)
- [ ] Event handlers are unsubscribed to prevent memory leaks
- [ ] Large objects are not kept in memory unnecessarily
- [ ] Weak references are used appropriately for cache scenarios

#### Async/Await
- [ ] Async methods return Task or Task<T>, not void (except event handlers)
- [ ] No mixing of .Result/.Wait() with async code
- [ ] ConfigureAwait(false) used in library code
- [ ] CancellationToken passed through async call chains

#### Exception Handling
- [ ] Specific exceptions are caught, not general Exception
- [ ] Exceptions are not swallowed without logging
- [ ] using statements or try-finally used for resource cleanup
- [ ] Custom exceptions inherit from appropriate base classes

#### Security
- [ ] Input validation on all public methods
- [ ] SQL injection protection (parameterized queries)
- [ ] Cross-site scripting (XSS) prevention
- [ ] Sensitive data is not logged or exposed

### 🟠 High Priority

#### Performance
- [ ] No unnecessary boxing/unboxing
- [ ] StringBuilder used for multiple string concatenations
- [ ] LINQ queries are efficient (no unnecessary ToList() calls)
- [ ] Database queries are optimized (no N+1 problems)

#### Architecture
- [ ] Dependency injection used instead of direct instantiation
- [ ] Interfaces used for abstraction
- [ ] Separation of concerns maintained
- [ ] Single responsibility principle followed

#### Error Handling
- [ ] Meaningful exception messages with context
- [ ] Proper logging levels used
- [ ] Exception details don't leak sensitive information
- [ ] Retry logic implemented where appropriate

### 🟡 Medium Priority

#### Code Quality
- [ ] Methods are reasonably sized (<50 lines)
- [ ] Classes have single responsibility
- [ ] Magic numbers replaced with named constants
- [ ] Code is DRY (Don't Repeat Yourself)

#### Testing
- [ ] Unit tests for new functionality
- [ ] Test methods have descriptive names
- [ ] Arrange-Act-Assert pattern followed
- [ ] Edge cases and error scenarios tested

#### Documentation
- [ ] XML documentation for public APIs
- [ ] Complex business logic documented
- [ ] Breaking changes documented
- [ ] Examples provided for complex APIs

### 🔵 Low Priority

#### Style
- [ ] Consistent formatting (use EditorConfig)
- [ ] Meaningful variable and method names
- [ ] Consistent using statement organization
- [ ] Proper accessibility modifiers

## Common C# Anti-Patterns

### Async Anti-Patterns
```csharp
// ❌ Bad: Async void (except event handlers)
public async void ProcessData()
{
    await DoSomethingAsync();
}

// ❌ Bad: Blocking on async code
public void ProcessData()
{
    DoSomethingAsync().Wait();
}

// ❌ Bad: Fire and forget without error handling
public void StartProcess()
{
    _ = ProcessDataAsync(); // Potential silent failures
}

// ✅ Good: Proper async method
public async Task ProcessDataAsync()
{
    await DoSomethingAsync();
}
```

### LINQ Anti-Patterns
```csharp
// ❌ Bad: Multiple enumeration
var users = GetUsers().Where(u => u.IsActive);
var count = users.Count();
var list = users.ToList();

// ✅ Good: Single enumeration
var users = GetUsers().Where(u => u.IsActive).ToList();
var count = users.Count;

// ❌ Bad: Unnecessary ToList() in LINQ chain
var result = items.Where(x => x.IsValid)
                 .ToList()
                 .Select(x => x.Name)
                 .ToList();

// ✅ Good: ToList() only at the end if needed
var result = items.Where(x => x.IsValid)
                 .Select(x => x.Name)
                 .ToList();
```

### Exception Handling Anti-Patterns
```csharp
// ❌ Bad: Catching and rethrowing
try
{
    DoSomething();
}
catch (Exception ex)
{
    throw ex; // Loses stack trace
}

// ✅ Good: Preserve stack trace
try
{
    DoSomething();
}
catch (Exception ex)
{
    _logger.LogError(ex, "Failed to do something");
    throw; // Preserves stack trace
}

// ❌ Bad: Empty catch block
try
{
    DoSomething();
}
catch
{
    // Silent failure
}
```

## .NET-Specific Patterns

### Dependency Injection
```csharp
// ✅ Good: Constructor injection
public class UserService
{
    private readonly IUserRepository _repository;
    private readonly ILogger<UserService> _logger;

    public UserService(IUserRepository repository, ILogger<UserService> logger)
    {
        _repository = repository ?? throw new ArgumentNullException(nameof(repository));
        _logger = logger ?? throw new ArgumentNullException(nameof(logger));
    }
}

// Registration in Startup.cs or Program.cs
services.AddScoped<IUserRepository, UserRepository>();
services.AddScoped<UserService>();
```

### Configuration Pattern
```csharp
// ✅ Good: Options pattern
public class DatabaseOptions
{
    public string ConnectionString { get; set; }
    public int TimeoutSeconds { get; set; }
}

// Registration
services.Configure<DatabaseOptions>(configuration.GetSection("Database"));

// Usage
public class UserRepository
{
    private readonly DatabaseOptions _options;

    public UserRepository(IOptions<DatabaseOptions> options)
    {
        _options = options.Value;
    }
}
```

### Resource Management
```csharp
// ✅ Good: Using statement
using var connection = new SqlConnection(connectionString);
connection.Open();
// Connection automatically disposed

// ✅ Good: Using declaration (C# 8+)
using var fileStream = new FileStream("file.txt", FileMode.Open);
// Stream automatically disposed at end of scope

// ✅ Good: Async disposal
await using var asyncResource = new AsyncDisposableResource();
```

## Entity Framework Best Practices

### Query Optimization
```csharp
// ❌ Bad: N+1 query problem
var users = await context.Users.ToListAsync();
foreach (var user in users)
{
    var orders = await context.Orders.Where(o => o.UserId == user.Id).ToListAsync();
}

// ✅ Good: Include related data
var users = await context.Users
    .Include(u => u.Orders)
    .ToListAsync();

// ✅ Good: Projection for read-only scenarios
var userSummaries = await context.Users
    .Select(u => new UserSummary
    {
        Name = u.Name,
        OrderCount = u.Orders.Count()
    })
    .ToListAsync();
```

### Change Tracking
```csharp
// ✅ Good: Disable change tracking for read-only queries
var users = await context.Users
    .AsNoTracking()
    .Where(u => u.IsActive)
    .ToListAsync();

// ✅ Good: Bulk operations
await context.Users
    .Where(u => u.LastLogin < cutoffDate)
    .ExecuteUpdateAsync(u => u.SetProperty(x => x.IsActive, false));
```

## Security Best Practices

### Input Validation
```csharp
public async Task<User> GetUserAsync(int userId)
{
    if (userId <= 0)
        throw new ArgumentException("User ID must be positive", nameof(userId));

    return await _repository.GetByIdAsync(userId);
}

// ✅ Good: Data annotations for validation
public class CreateUserRequest
{
    [Required]
    [StringLength(100, MinimumLength = 2)]
    public string Name { get; set; }

    [Required]
    [EmailAddress]
    public string Email { get; set; }
}
```

### SQL Injection Prevention
```csharp
// ❌ Bad: String concatenation
var sql = $"SELECT * FROM Users WHERE Name = '{userName}'";

// ✅ Good: Parameterized query
var sql = "SELECT * FROM Users WHERE Name = @userName";
var parameter = new SqlParameter("@userName", userName);

// ✅ Good: Entity Framework (automatically parameterized)
var user = await context.Users
    .FirstOrDefaultAsync(u => u.Name == userName);
```

## Testing Best Practices

### Unit Testing Structure
```csharp
[TestClass]
public class UserServiceTests
{
    private Mock<IUserRepository> _mockRepository;
    private Mock<ILogger<UserService>> _mockLogger;
    private UserService _userService;

    [TestInitialize]
    public void Setup()
    {
        _mockRepository = new Mock<IUserRepository>();
        _mockLogger = new Mock<ILogger<UserService>>();
        _userService = new UserService(_mockRepository.Object, _mockLogger.Object);
    }

    [TestMethod]
    public async Task GetUserAsync_ValidId_ReturnsUser()
    {
        // Arrange
        var userId = 1;
        var expectedUser = new User { Id = userId, Name = "John" };
        _mockRepository.Setup(r => r.GetByIdAsync(userId))
                      .ReturnsAsync(expectedUser);

        // Act
        var result = await _userService.GetUserAsync(userId);

        // Assert
        Assert.AreEqual(expectedUser.Id, result.Id);
        Assert.AreEqual(expectedUser.Name, result.Name);
    }

    [TestMethod]
    public async Task GetUserAsync_InvalidId_ThrowsArgumentException()
    {
        // Arrange & Act & Assert
        await Assert.ThrowsExceptionAsync<ArgumentException>(
            () => _userService.GetUserAsync(-1));
    }
}
```

### Integration Testing
```csharp
[TestClass]
public class UserControllerIntegrationTests
{
    private WebApplicationFactory<Program> _factory;
    private HttpClient _client;

    [TestInitialize]
    public void Setup()
    {
        _factory = new WebApplicationFactory<Program>();
        _client = _factory.CreateClient();
    }

    [TestMethod]
    public async Task GetUser_ValidId_ReturnsOk()
    {
        // Arrange
        var userId = 1;

        // Act
        var response = await _client.GetAsync($"/api/users/{userId}");

        // Assert
        Assert.AreEqual(HttpStatusCode.OK, response.StatusCode);
    }

    [TestCleanup]
    public void Cleanup()
    {
        _client?.Dispose();
        _factory?.Dispose();
    }
}
