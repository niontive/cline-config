# Cline Config

A comprehensive collection of MCP servers, rules, and workflows for [Cline](https://github.com/clinebot/cline) - enabling powerful automation for code review, development workflows, and more.

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
   cd workflows/ado-pr-review/mcp-server
   pip install -r requirements.txt
   ```

3. **Configure Cline MCP servers** (see [MCP Configuration](#mcp-configuration) below)

## 📋 Available Workflows

### Azure DevOps PR Review

Comprehensive code review automation for Azure DevOps Pull Requests with intelligent analysis and automated commenting.

**Features:**
- 🔍 **Multi-language support**: Go, C#, PowerShell, Bash
- 🛡️ **Security analysis**: Identifies vulnerabilities and best practices
- ⚡ **Performance insights**: Spots optimization opportunities  
- 📝 **Documentation checks**: Ensures proper code documentation
- 🎯 **Targeted commenting**: File-specific comments with line numbers
- 🔄 **Interactive approval**: Review and modify comments before posting

**Quick Setup:**
```bash
# Install Azure CLI and login
az login
az extension add --name azure-devops

# Install Python dependencies
cd workflows/ado-pr-review/mcp-server
pip install -r requirements.txt
```

**Usage Examples:**

```
Review PR https://msazure.visualstudio.com/One/_git/myrepo/pullrequest/12345 using ado-pr-review mcp tool. Please write individual comments for each suggestion for the corresponding files. Make each comment brief, and only comment if there is a minor issue. Include line numbers in comments.
```

```
Review PR 1234 in myorg/myproject/myrepo for security issues only
```

```
Focus on performance issues in PR https://dev.azure.com/myorg/project/_git/repo/pullrequest/5678
```

See the [ADO PR Review README](workflows/ado-pr-review/README.md) for detailed documentation.

## ⚙️ MCP Configuration

### Adding MCP Servers to Cline

Add the following to your Cline MCP configuration:

```json
{
  "mcpServers": {
    "ado-pr-review": {
      "command": "python",
      "args": ["/path/to/cline-config/workflows/ado-pr-review/mcp-server/server.py"],
      "env": {}
    }
  }
}
```

### Server Configuration

Update `workflows/ado-pr-review/mcp-server/config.json` with your defaults:

```json
{
  "default_organization": "your-org",
  "default_project": "your-project",
  "max_comments_per_pr": 25,
  "severity_levels": ["critical", "high", "medium", "low", "suggestion"]
}
```

## 📖 Rules and Templates

### Language-Specific Rules

The repository includes comprehensive review rules for:

- **[Go](workflows/ado-pr-review/rules/languages/golang.md)**: Concurrency, error handling, performance
- **[C#](workflows/ado-pr-review/rules/languages/csharp.md)**: .NET best practices, async/await, LINQ
- **[PowerShell](workflows/ado-pr-review/rules/languages/powershell.md)**: Security, cmdlet usage, modules
- **[Bash](workflows/ado-pr-review/rules/languages/bash.md)**: Security, portability, error handling

### Core Review Principles

- **[Security Review](workflows/ado-pr-review/rules/security-review.md)**: Common vulnerabilities and secure coding
- **[Dependencies](workflows/ado-pr-review/rules/dependencies.md)**: Package management and version control
- **[Core Principles](workflows/ado-pr-review/rules/core-principles.md)**: General code quality guidelines

### Comment Templates

Pre-built templates for consistent feedback:

- **[Security Issues](workflows/ado-pr-review/templates/security-issue.md)**
- **[Performance Suggestions](workflows/ado-pr-review/templates/performance-suggestion.md)**
- **[Code Quality](workflows/ado-pr-review/templates/code-quality.md)**
- **[Documentation](workflows/ado-pr-review/templates/documentation-improvement.md)**

## 💡 Example Usage with Cline

### Comprehensive PR Review

```
Review PR https://msazure.visualstudio.com/One/_git/azlocal-overlay/pullrequest/12479934 using ado-pr-review mcp tool. Please write individual comments for each suggestion for the corresponding files. Make each comment brief, and only comment if there is a minor issue. Include line numbers in comments.
```

This instruction will:
1. ✅ Authenticate with Azure DevOps
2. 📥 Fetch PR details and changed files
3. 🔍 Analyze each file using language-specific rules
4. 📝 Generate targeted comments with line numbers
5. 👀 Present findings for your review
6. 💬 Post approved comments to the PR

### Focused Reviews

```
Review PR 1234 for security vulnerabilities only
```

```
Check PR https://dev.azure.com/myorg/project/_git/repo/pullrequest/5678 for performance issues
```

```
Analyze documentation quality in PR 9999
```

### Batch Operations

```
Review PRs 1001, 1002, 1003 in myorg/myproject/myrepo
```

## 🗂️ Repository Structure

```
cline-config/
├── README.md                              # This file
└── workflows/                             # Workflow implementations
    └── ado-pr-review/                     # Azure DevOps PR Review
        ├── README.md                      # Detailed workflow documentation
        ├── mcp-server/                    # MCP server implementation
        │   ├── server.py                  # Main server code
        │   ├── config.json                # Server configuration
        │   └── requirements.txt           # Python dependencies
        ├── rules/                         # Review rules and guidelines
        │   ├── core-principles.md         # General principles
        │   ├── security-review.md         # Security guidelines
        │   ├── dependencies.md            # Dependency management
        │   └── languages/                 # Language-specific rules
        │       ├── golang.md              # Go best practices
        │       ├── csharp.md              # C# guidelines
        │       ├── powershell.md          # PowerShell standards
        │       └── bash.md                # Bash scripting rules
        └── templates/                     # Comment templates
            ├── security-issue.md          # Security findings
            ├── performance-suggestion.md  # Performance improvements
            ├── code-quality.md            # Code quality issues
            ├── documentation-improvement.md # Documentation gaps
            └── suggestion.md              # General suggestions
```

## 🛠️ Customization

### Adding Custom Rules

1. **Create language-specific rules:**
   ```bash
   # Add new language support
   touch workflows/ado-pr-review/rules/languages/python.md
   ```

2. **Update file extensions in config:**
   ```json
   {
     "file_extensions": {
       "python": [".py", ".pyw"]
     }
   }
   ```

### Custom Comment Templates

Create new templates in `workflows/ado-pr-review/templates/`:

```markdown
# Custom Template: API Design Review

## Issue Category: API Design

**Severity:** Medium

**Description:**
{description}

**Suggestion:**
{suggestion}

**Best Practice Reference:**
{reference_link}
```

### Organization-Specific Rules

1. **Fork this repository**
2. **Customize rules** in `workflows/ado-pr-review/rules/`
3. **Update templates** for your organization's standards
4. **Configure default settings** in `config.json`

## 🤝 Contributing

### Adding New Workflows

1. **Create workflow directory:**
   ```bash
   mkdir workflows/my-new-workflow
   ```

2. **Follow the structure:**
   ```
   workflows/my-new-workflow/
   ├── README.md              # Workflow documentation
   ├── mcp-server/            # MCP server implementation
   └── config/                # Configuration files
   ```

3. **Implement MCP server** following the ADO PR Review example

### Extending Existing Workflows

- **Add new rules** in appropriate `rules/` directories
- **Create new templates** for consistent messaging
- **Update language support** by extending file type mappings
- **Enhance server capabilities** by adding new tools

### Submitting Changes

1. **Fork the repository**
2. **Create a feature branch**
3. **Make your changes**
4. **Test thoroughly**
5. **Submit a pull request**

## 📚 Additional Resources

- **[Cline Documentation](https://github.com/clinebot/cline)**
- **[MCP Protocol Specification](https://modelcontextprotocol.io/)**
- **[Azure DevOps REST API](https://docs.microsoft.com/en-us/rest/api/azure/devops/)**

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**🎯 Ready to supercharge your code reviews?** Start with the Azure DevOps PR Review workflow and customize it for your team's needs!
