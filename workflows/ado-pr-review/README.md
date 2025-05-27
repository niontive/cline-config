# Azure DevOps PR Review Workflow

This workflow enables Cline to perform comprehensive code reviews on Azure DevOps Pull Requests using best practices and automated analysis.

## Features

- **Comprehensive Analysis**: Reviews code quality, security, performance, documentation, and dependencies
- **Language-Specific Rules**: Tailored analysis for Go, C#, PowerShell, and Bash
- **Interactive Approval**: Review and modify comments before posting to ADO
- **Azure DevOps REST API**: Uses official REST API for reliable PR interaction and commenting
- **Multi-Organization Support**: Works across different ADO organizations and projects

## Prerequisites

1. **Azure CLI**: Install and configure Azure CLI
   ```bash
   # Install Azure CLI (if not already installed)
   curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
   
   # Login to Azure
   az login
   
   # Install Azure DevOps extension
   az extension add --name azure-devops
   ```

2. **MCP Server**: Install the ADO PR Review MCP server (see `../../mcp-servers/ado-pr-review/README.md`)

3. **Cline Configuration**: Add the MCP server to your Cline config

## Setup

1. **Configure Workflow**: Update `config.json` with your default ADO settings
2. **Test Authentication**: Run `az account show` to verify login status
3. **Set Default Organization**: Configure your primary ADO organization

## Usage

### Basic PR Review
```
"Review PR 1234 in myorg/myproject/myrepo"
```

### Review with Specific Focus
```
"Review PR 1234 for security issues only"
"Focus on performance issues in PR 1234"
```

### Cross-Organization Review
```
"Review PR 1234 in different-org/project/repo"
```

### Comment Posting
The workflow supports two types of comments:

**General PR Comments** (not tied to specific files):
```
"Post a general comment: 'Overall the PR looks good, just a few minor suggestions'"
```

**File-Specific Comments** (with optional line numbers):
```
"Comment on file src/main.go: 'Consider adding error handling here'"
"Comment on line 25 of src/main.go: 'This function could be optimized'"
```

## Workflow Process

1. **Authentication Check**: Verifies Azure CLI login status
2. **PR Fetching**: Retrieves PR details and changed files
3. **File Analysis**: Applies language-specific and general review rules
4. **Report Generation**: Creates categorized findings with severity levels
5. **Interactive Review**: Present findings for user approval/modification
6. **Comment Posting**: Posts approved comments to the ADO PR

## Review Categories

- 🔴 **Critical**: Security vulnerabilities, breaking changes
- 🟠 **High**: Performance issues, architectural concerns
- 🟡 **Medium**: Code quality, maintainability
- 🔵 **Low**: Style, documentation improvements
- 💡 **Suggestion**: Optional enhancements

## Supported File Types

- **Go**: `.go`, `go.mod`, `go.sum`
- **C#**: `.cs`, `.csproj`, `.sln`
- **PowerShell**: `.ps1`, `.psm1`, `.psd1`
- **Bash**: `.sh`, `Dockerfile`, `Makefile`
- **Config**: `.yml`, `.yaml`, `.json`, `.xml`
- **Documentation**: `.md`, `.rst`, `.txt`

## Configuration

### Workflow Settings
Edit `config.json`:
```json
{
  "default_organization": "your-org",
  "default_project": "your-project",
  "comment_templates": "templates/",
  "rules_directory": "rules/",
  "max_comments_per_pr": 25,
  "severity_levels": ["critical", "high", "medium", "low", "suggestion"]
}
```

### Custom Rules
Add custom review rules in the `rules/` directory following the existing pattern.

## Troubleshooting

- **Authentication Issues**: Run `az login` and ensure the Azure DevOps extension is installed
- **Permission Errors**: Verify you have contributor access to the target repository
- **Large PRs**: For PRs with many files, the workflow may take longer to complete

## Advanced Usage

### Batch Review
Review multiple PRs in sequence by providing a list of PR IDs.

### Custom Comment Templates
Modify templates in `templates/` directory to customize comment formatting.

### Rule Customization
Add organization-specific rules by creating new files in `rules/languages/` or `rules/`.

## File Structure

```
workflows/ado-pr-review/
├── README.md          # This file - workflow usage guide
├── config.json        # Workflow configuration
├── rules/             # Code review rules for Cline
│   ├── core-principles.md
│   ├── dependencies.md
│   ├── security-review.md
│   └── languages/     # Language-specific rules
└── templates/         # Comment templates
    ├── code-quality.md
    ├── documentation-improvement.md
    ├── performance-suggestion.md
    ├── security-issue.md
    └── suggestion.md
```

The MCP server is located separately at `../../mcp-servers/ado-pr-review/`.
