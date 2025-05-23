# Core Code Review Principles

## General Best Practices

### Code Quality
- **Readability**: Code should be self-documenting and easy to understand
- **Maintainability**: Changes should not increase technical debt
- **Consistency**: Follow established patterns and conventions in the codebase
- **Simplicity**: Prefer simple, clear solutions over complex ones
- **DRY Principle**: Don't repeat yourself - extract common functionality

### Architecture & Design
- **Single Responsibility**: Each function/class should have one clear purpose
- **Separation of Concerns**: Separate business logic from presentation and data layers
- **Dependency Injection**: Avoid tight coupling between components
- **Interface Segregation**: Prefer small, focused interfaces
- **Open/Closed Principle**: Open for extension, closed for modification

### Error Handling
- **Explicit Error Handling**: Handle errors explicitly, don't ignore them
- **Fail Fast**: Detect and report errors as early as possible
- **Graceful Degradation**: System should handle failures gracefully
- **Logging**: Include meaningful error messages and context
- **Recovery**: Provide recovery mechanisms where appropriate

### Testing
- **Test Coverage**: Critical paths should have test coverage
- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test component interactions
- **Edge Cases**: Consider boundary conditions and error scenarios
- **Test Names**: Use descriptive test names that explain the scenario

### Documentation
- **API Documentation**: Public interfaces should be documented
- **Code Comments**: Explain "why" not "what" - focus on business logic
- **README Updates**: Update documentation for new features
- **Change Documentation**: Document breaking changes and migration paths
- **Examples**: Provide usage examples for complex functionality

## Review Focus Areas

### 🔴 Critical Issues (Must Fix)
- Security vulnerabilities
- Data corruption risks
- Memory leaks or resource leaks
- Breaking changes without deprecation
- Race conditions or concurrency issues
- Infinite loops or performance killers

### 🟠 High Priority (Should Fix)
- Performance bottlenecks
- Architectural violations
- Poor error handling
- Missing input validation
- Resource management issues
- Scalability concerns

### 🟡 Medium Priority (Consider Fixing)
- Code duplication
- Complex methods that should be split
- Missing unit tests for new code
- Inconsistent naming conventions
- Overly broad interfaces
- Missing documentation for public APIs

### 🔵 Low Priority (Nice to Have)
- Code style inconsistencies
- Minor performance optimizations
- Better variable names
- Additional comments for clarity
- Refactoring opportunities
- Documentation improvements

### 💡 Suggestions (Optional)
- Alternative implementation approaches
- Library recommendations
- Best practice suggestions
- Code organization improvements
- Future enhancement ideas

## Review Guidelines

### When to Block a PR
- Security vulnerabilities
- Data integrity risks
- Breaking changes without proper versioning
- Missing critical tests
- Code that violates core architectural principles

### When to Approve with Comments
- Minor style issues
- Performance improvements that aren't critical
- Documentation updates needed
- Refactoring suggestions
- Best practice recommendations

### What Makes a Good Review Comment
- **Specific**: Point to exact lines and issues
- **Constructive**: Suggest solutions, not just problems
- **Educational**: Explain the reasoning behind suggestions
- **Respectful**: Maintain a collaborative tone
- **Actionable**: Provide clear next steps

## Common Anti-Patterns to Watch For

### Code Smells
- **God Objects**: Classes/functions that do too much
- **Long Parameter Lists**: Functions with too many parameters
- **Deep Nesting**: Excessive if/else or loop nesting
- **Magic Numbers**: Unexplained numeric literals
- **Dead Code**: Unreachable or unused code

### Security Issues
- **Input Validation**: Missing validation on user inputs
- **SQL Injection**: Unsafe database queries
- **XSS Vulnerabilities**: Unescaped output
- **Hardcoded Secrets**: API keys or passwords in code
- **Insecure Defaults**: Overly permissive default settings

### Performance Issues
- **N+1 Queries**: Inefficient database access patterns
- **Memory Leaks**: Objects not properly disposed
- **Synchronous Blocking**: Blocking operations on main thread
- **Inefficient Algorithms**: Poor algorithmic complexity
- **Resource Waste**: Unnecessary object creation or computation
