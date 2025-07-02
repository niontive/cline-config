# Cline Config

A comprehensive collection of MCP servers and specialized prompts for [Cline](https://github.com/clinebot/cline) - enabling powerful automation for code review, development workflows, and more.

## 🚀 Quick Start

### Prerequisites

- [Cline](https://github.com/clinebot/cline) installed and configured
- Git for cloning the repository
- Python 3.8+ (for MCP servers)

### Setup

1. **Clone this repository:**
   ```bash
   git clone <your-repo-url>
   cd cline-config
   ```

2. **Install Python dependencies:**
   ```bash
   cd mcp-servers/ado-pr
   pip install -r requirements.txt
   ```

3. **Configure Cline MCP servers** (see [MCP Configuration](#mcp-configuration) below)

## 📋 Specialized Review Prompts

### Core PR Review Assistant
**File**: `prompts/pr-review-core.md`

Comprehensive code review guidance covering all aspects of software quality, security, and best practices across multiple languages.

**Usage:**
```
Load prompt: pr-review-core.md
Review PR https://dev.azure.com/org/project/_git/repo/pullrequest/123
```

### Go Code Review Specialist  
**File**: `prompts/pr-review-golang.md`

Deep Go expertise focusing on concurrency, error handling, performance, and Go-specific best practices.

**Usage:**
```
Load prompt: pr-review-golang.md
Review PR https://dev.azure.com/org/project/_git/repo/pullrequest/123 focusing on Go best practices
```

### Security-Focused Review
**File**: `prompts/pr-review-security.md`

Specialized security analysis identifying vulnerabilities, authentication issues, injection attacks, and cryptographic weaknesses.

**Usage:**
```
Load prompt: pr-review-security.md
Review PR https://dev.azure.com/org/project/_git/repo/pullrequest/123 for security vulnerabilities
```

### Performance Optimization Review
**File**: `prompts/pr-review-performance.md`

Expert performance analysis covering algorithmic complexity, memory efficiency, database optimization, and scalability issues.

**Usage:**
```
Load prompt: pr-review-performance.md
Review PR https://dev.azure.com/org/project/_git/repo/pullrequest/123 for performance issues
```

## ✨ Key Features

- 🎯 **Specialized Focus**: Each prompt targets specific review aspects (security, performance, language-specific)
- 🛠️ **MCP Integration**: Seamless integration with Azure DevOps via MCP server tools
- 🔍 **Multi-Language Support**: Go, C#, PowerShell, Bash with language-specific best practices
- 📊 **Severity Levels**: Clear prioritization (🔴 Critical, 🟠 High, 🟡 Medium, 🔵 Low, 💡 Suggestion)
- 📝 **Structured Comments**: Consistent, professional feedback with examples and references
- 🚀 **Ready-to-Use**: No complex workflow setup - just load a prompt and review PRs

## 🛠️ MCP Servers

### Azure DevOps PR Server

Located at `mcp-servers/ado-pr/` - provides Azure DevOps REST API integration tools for creating and reviewing Pull Requests.

**Available Tools:**
- `check_az_login` - Verify Azure CLI authentication
- `create_pr` - Create new Pull Requests with work item linking
- `get_pr_info` - Fetch comprehensive PR information
- `get_pr_files` - List changed files in a PR
- `get_file_content` - Retrieve file content from repository
- `post_pr_comment` - Post comments to PRs (general or file-specific)

See the [MCP Server README](mcp-servers/ado-pr/README.md) for detailed technical documentation.

## ⚙️ MCP Configuration

### Adding MCP Servers to Cline

Add the following to your Cline MCP configuration:

```json
{
  "mcpServers": {
    "ado-pr": {
      "command": "python",
      "args": ["/path/to/cline-config/mcp-servers/ado-pr/server.py"],
      "env": {}
    }
  }
}
```

## 💡 Example Usage with Cline

### Comprehensive PR Review

```
Load prompt: pr-review-core.md
Review PR https://dev.azure.com/org/project/_git/repo/pullrequest/123
Write individual comments for each suggestion for the corresponding files.
Make each comment brief, and only comment if there is a minor issue.
Include line numbers in comments.
```

This instruction will:
1. ✅ Authenticate with Azure DevOps
2. 📥 Fetch PR details and changed files
3. 🔍 Analyze each file using comprehensive review criteria
4. 📝 Generate targeted comments with line numbers
5. 👀 Present findings for your review
6. 💬 Post approved comments to the PR

### Creating Pull Requests

**Simple PR Creation:**
```
Create PR from feature/login-fix in myorg/project/repo with title "Fix login validation bug"
```

**PR with Work Items:**
```
Create PR from feature/dashboard to main in myorg/project/repo with title "New user dashboard" and work items 1234,5678
```

**Draft PR:**
```
Create draft PR from feature/wip-feature in myorg/project/repo with title "Work in progress - new API"
```

### Focused Reviews

**Security Review:**
```
Load prompt: pr-review-security.md
Review PR 1234 for security vulnerabilities only
```

**Performance Review:**
```
Load prompt: pr-review-performance.md
Check PR https://dev.azure.com/myorg/project/_git/repo/pullrequest/5678 for performance issues
```

**Go-Specific Review:**
```
Load prompt: pr-review-golang.md
Analyze Go code quality in PR 9999
```

### Complete Workflow

**Create and Review:**
```
1. Create PR from feature/new-feature with title "Add new authentication system" and work items 1234
2. Load prompt: pr-review-security.md
3. Review the newly created PR for security issues
4. Post comments with recommendations
```

## 🗂️ Repository Structure

```
cline-config/
├── README.md                              # This file
├── prompts/                               # Specialized Cline prompts
│   ├── pr-review-core.md                  # Comprehensive PR review assistant
│   ├── pr-review-golang.md                # Go-specific code review specialist
│   ├── pr-review-security.md              # Security-focused review expert
│   └── pr-review-performance.md           # Performance optimization specialist
└── mcp-servers/                           # Standalone MCP servers
    └── ado-pr/                            # Azure DevOps integration server
        ├── README.md                      # MCP server documentation
        ├── server.py                      # Main server implementation
        └── requirements.txt               # Python dependencies
```

## 🛠️ Architecture

### Separation of Concerns

- **Prompts** (`prompts/`): Specialized review guidance for different focus areas
- **MCP Servers** (`mcp-servers/`): Technical implementations providing tools and APIs

### How It Works

1. **Load Prompt**: Choose a specialized prompt based on review focus
2. **MCP Server**: Provides low-level tools (API calls, data retrieval, comment posting)
3. **Cline Analysis**: Uses prompt guidance to analyze code and generate findings
4. **Structured Output**: Formats findings into consistent, professional comments

## 🛠️ Customization

### Creating Custom Prompts

1. **Create new prompt file:**
   ```bash
   touch prompts/pr-review-python.md
   ```

2. **Follow the prompt structure:**
   ```markdown
   # Python Code Review Specialist
   
   You are a Python expert specializing in...
   
   ## Review Process
   ### 1. Authentication & Setup
   - Use `check_az_login` tool...
   
   ## Review Framework
   ### 🔴 **CRITICAL** Issues
   ...
   ```

### Extending Existing Prompts

- **Add language-specific guidance** to existing prompts
- **Include new security patterns** in the security prompt
- **Add performance optimizations** for specific frameworks
- **Create industry-specific variants** (web, mobile, embedded)

### Organization-Specific Customization

1. **Fork this repository**
2. **Customize prompts** with your organization's standards
3. **Add company-specific security guidelines**
4. **Include internal best practices and coding standards**

## 🤝 Contributing

### Adding New Prompts

1. **Identify the review focus** (language, domain, technology)
2. **Create comprehensive prompt** following existing patterns
3. **Include practical examples** and anti-patterns
4. **Add structured comment templates**
5. **Document usage instructions**

### Adding New MCP Servers

1. **Create server directory:**
   ```bash
   mkdir mcp-servers/my-new-server
   ```

2. **Implement MCP server** following the standard MCP protocol
3. **Add documentation** and requirements

### Enhancing Existing Components

- **Expand language coverage** in existing prompts
- **Add new code analysis patterns**
- **Improve comment templates and formatting**
- **Enhance MCP server capabilities** with new tools

### Submitting Changes

1. **Fork the repository**
2. **Create a feature branch**
3. **Make your changes**
4. **Test thoroughly with real PRs**
5. **Submit a pull request**

## 📚 Prompt Contents Overview

### pr-review-core.md
- **Multi-language support**: Go, C#, PowerShell, Bash
- **Security analysis**: Input validation, authentication, cryptography
- **Performance review**: Algorithmic complexity, memory management
- **Code quality**: Architecture, maintainability, testing
- **Documentation**: API docs, code comments, examples

### pr-review-golang.md
- **Concurrency**: Goroutines, channels, context cancellation
- **Error handling**: Explicit error management, wrapping
- **Performance**: Memory allocation, string building, slice operations
- **Package design**: Interfaces, naming conventions, module structure
- **Testing**: Table-driven tests, benchmarks, coverage

### pr-review-security.md
- **Vulnerability detection**: SQL injection, XSS, CSRF
- **Authentication**: JWT, session management, authorization
- **Cryptography**: Strong algorithms, key management, random generation
- **Input validation**: Sanitization, boundary checks, file uploads
- **Information disclosure**: Error messages, logging, debug info

### pr-review-performance.md
- **Algorithmic analysis**: Time/space complexity, optimization opportunities
- **Database performance**: Query optimization, N+1 problems, indexing
- **Memory management**: Leak detection, resource cleanup, caching
- **Concurrency**: Async patterns, blocking operations, parallelization
- **Profiling guidance**: Benchmarking, monitoring, measurement

## 📚 Additional Resources

- **[Cline Documentation](https://github.com/clinebot/cline)**
- **[MCP Protocol Specification](https://modelcontextprotocol.io/)**
- **[Azure DevOps REST API](https://docs.microsoft.com/en-us/rest/api/azure/devops/)**

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**🎯 Ready to supercharge your code reviews?** Choose a specialized prompt, load it in Cline, and start reviewing PRs with expert-level analysis!
