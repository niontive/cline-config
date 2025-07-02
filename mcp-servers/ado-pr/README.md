# Azure DevOps PR MCP Server

An MCP (Model Context Protocol) server that provides tools for creating and reviewing Azure DevOps Pull Requests.

## Overview

This MCP server acts as a bridge between Cline and Azure DevOps, providing tools to:
- Check Azure CLI authentication status
- Create new Pull Requests with work item linking
- Get PR details and changed files
- Retrieve file content from repositories
- Post comments to PRs (general or file-specific)

## Prerequisites

1. **Azure CLI**: Must be installed and authenticated
   ```bash
   # Install Azure CLI
   curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
   
   # Login to Azure
   az login
   
   # Install Azure DevOps extension
   az extension add --name azure-devops
   ```

2. **Python Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Installation

1. Copy this directory to your MCP servers location
2. Add to your Cline MCP configuration:
   ```json
   {
     "mcpServers": {
       "ado-pr": {
         "command": "python",
         "args": ["path/to/mcp-servers/ado-pr/server.py"]
       }
     }
   }
   ```

## Available Tools

### `check_az_login`
Check if user is logged into Azure CLI.

### `create_pr`
Create a new Pull Request in Azure DevOps with optional work item linking.
- Parameters: `organization`, `project`, `repository`, `source_branch`, `title`
- Optional: `target_branch` (default: "main"), `description`, `reviewers`, `work_items`, `auto_complete`, `draft`

### `get_pr_info`
Get comprehensive Pull Request information including metadata and commit IDs.
- Parameters: `pr_url`

### `get_pr_files`
Get list of changed files in a Pull Request from PR URL.
- Parameters: `pr_url`

### `get_file_content`
Get content of a specific file from the repository.
- Parameters: `file_path`, `organization`, `project`, `repository`, `commit_id`

### `post_pr_comment`
Post a comment to an Azure DevOps Pull Request (general or file-specific).
- Parameters: `pr_id`, `organization`, `project`, `repository`, `comment`
- Optional: `file_path`, `line_number`

## Usage Examples

Once configured in Cline, you can use commands like:

### Creating Pull Requests
- "Create PR from feature/login-fix to main in myorg/project/repo with title 'Fix login bug'"
- "Create PR from feature/dashboard in myorg/project/repo with title 'New dashboard' and work items 1234,5678"
- "Create draft PR from feature/wip-feature with title 'Work in progress'"

### Reviewing Pull Requests  
- "Check my Azure CLI login status"
- "Get details for PR https://dev.azure.com/myorg/project/_git/repo/pullrequest/1234"
- "Get changed files for PR 1234"
- "Post comment 'LGTM' to PR 1234"

## Authentication

This server uses Azure CLI authentication. Ensure you're logged in with an account that has access to the target Azure DevOps organization and repository.

## Error Handling

The server provides detailed error messages for common issues:
- Azure CLI not logged in
- Invalid PR URLs
- Branch validation failures
- File not found in PR changes
- Permission errors

## New Features

### PR Creation with Work Items
The `create_pr` tool allows you to:
- Create PRs with automatic branch validation
- Link work items during creation
- Add reviewers automatically
- Create draft PRs for work-in-progress
- Set auto-complete options

### Default Target Branch
The target branch defaults to "main" if not specified, making PR creation more convenient for most workflows.

## Version

1.0.0 - Initial release with PR creation and review functionality
