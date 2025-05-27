# Azure DevOps PR Review MCP Server

An MCP (Model Context Protocol) server that provides tools for interacting with Azure DevOps Pull Requests.

## Overview

This MCP server acts as a bridge between Cline and Azure DevOps, providing tools to:
- Check Azure CLI authentication status
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
       "ado-pr-review": {
         "command": "python",
         "args": ["path/to/mcp-servers/ado-pr-review/server.py"]
       }
     }
   }
   ```

## Available Tools

### `check_az_login`
Check if user is logged into Azure CLI.

### `get_pr_details`
Get details of an Azure DevOps Pull Request.
- Parameters: `pr_id`, `organization`

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

### `debug_pr_iteration_info`
Debug tool to get PR iteration information for troubleshooting.
- Parameters: `pr_id`, `organization`, `project`, `repository`

## Usage Example

Once configured in Cline, you can use commands like:
- "Check my Azure CLI login status"
- "Get details for PR 1234 in myorg"
- "Get changed files for https://dev.azure.com/myorg/project/_git/repo/pullrequest/1234"
- "Post comment 'LGTM' to PR 1234"

## Authentication

This server uses Azure CLI authentication. Ensure you're logged in with an account that has access to the target Azure DevOps organization and repository.

## Error Handling

The server provides detailed error messages for common issues:
- Azure CLI not logged in
- Invalid PR URLs
- File not found in PR changes
- Permission errors

## Version

1.0.0 - Initial release with core Azure DevOps PR functionality
