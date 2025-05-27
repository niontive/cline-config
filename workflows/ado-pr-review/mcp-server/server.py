#!/usr/bin/env python3
"""
Azure DevOps Pull Request Review MCP Server

Provides tools for reviewing Azure DevOps Pull Requests through Cline.
"""

import json
import subprocess
import sys
import os
import requests
import base64
import re
import urllib.parse
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel,
    ServerCapabilities
)
from pydantic import BaseModel, Field

# Load configuration
config_path = Path(__file__).parent / "config.json"
with open(config_path, 'r') as f:
    CONFIG = json.load(f)

class PRInfo(BaseModel):
    id: int
    title: str
    description: str
    source_branch: str
    target_branch: str
    author: str
    status: str
    created_date: str
    repository: str
    organization: str
    project: str

class FileChange(BaseModel):
    path: str
    change_type: str
    original_path: Optional[str] = None

class ReviewComment(BaseModel):
    file_path: str
    line_number: int
    comment: str
    severity: str
    category: str
    suggestion: Optional[str] = None

def run_command(cmd: List[str], cwd: Optional[str] = None) -> tuple[bool, str, str]:
    """Execute command and return success, stdout, stderr."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            cwd=cwd
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def run_az_command(cmd: List[str]) -> tuple[bool, str, str]:
    """Execute Azure CLI command and return success, stdout, stderr."""
    return run_command(cmd)

def parse_pr_url(pr_url: str) -> tuple[bool, Dict[str, str]]:
    """Parse Azure DevOps PR URL to extract components."""
    # Handle both formats:
    # https://msazure.visualstudio.com/One/_git/azlocal-overlay/pullrequest/12479934
    # https://dev.azure.com/msazure/One/_git/azlocal-overlay/pullrequest/12479934
    
    patterns = [
        # visualstudio.com format
        r'https://([^.]+)\.visualstudio\.com/([^/]+)/_git/([^/]+)/pullrequest/(\d+)',
        # dev.azure.com format
        r'https://dev\.azure\.com/([^/]+)/([^/]+)/_git/([^/]+)/pullrequest/(\d+)'
    ]
    
    for pattern in patterns:
        match = re.match(pattern, pr_url)
        if match:
            if 'visualstudio.com' in pattern:
                org, project, repo, pr_id = match.groups()
                return True, {
                    'organization': org,
                    'project': project,
                    'repository': repo,
                    'pr_id': pr_id,
                    'base_url': 'https://dev.azure.com'  # Always use dev.azure.com for API
                }
            else:
                org, project, repo, pr_id = match.groups()
                return True, {
                    'organization': org,
                    'project': project,
                    'repository': repo,
                    'pr_id': pr_id,
                    'base_url': 'https://dev.azure.com'
                }
    
    return False, {}

def get_access_token() -> tuple[bool, str]:
    """Get Azure DevOps access token from Azure CLI."""
    success, stdout, stderr = run_az_command(["az", "account", "get-access-token", "--resource", "499b84ac-1321-427f-aa17-267ca6975798", "--output", "json"])
    if success:
        try:
            token_data = json.loads(stdout)
            return True, token_data["accessToken"]
        except (json.JSONDecodeError, KeyError):
            return False, "Failed to parse access token"
    else:
        return False, f"Failed to get access token: {stderr}"

def check_az_login() -> tuple[bool, str]:
    """Check if user is logged into Azure CLI."""
    success, stdout, stderr = run_az_command(["az", "account", "show"])
    if success:
        try:
            account = json.loads(stdout)
            return True, f"Logged in as {account.get('user', {}).get('name', 'Unknown')}"
        except json.JSONDecodeError:
            return False, "Invalid response from az account show"
    else:
        return False, f"Not logged in: {stderr}"

def get_pr_details(pr_id: str, organization: str) -> tuple[bool, Union[PRInfo, str]]:
    """Get PR details from Azure DevOps."""
    cmd = [
        "az", "repos", "pr", "show",
        "--id", pr_id,
        "--organization", organization,
        "--output", "json"
    ]
    
    success, stdout, stderr = run_az_command(cmd)
    if not success:
        return False, f"Failed to get PR details: {stderr}"
    
    try:
        pr_data = json.loads(stdout)
        pr_info = PRInfo(
            id=pr_data["pullRequestId"],
            title=pr_data["title"],
            description=pr_data.get("description", ""),
            source_branch=pr_data["sourceRefName"].replace("refs/heads/", ""),
            target_branch=pr_data["targetRefName"].replace("refs/heads/", ""),
            author=pr_data["createdBy"]["displayName"],
            status=pr_data["status"],
            created_date=pr_data["creationDate"],
            repository=pr_data["repository"]["name"],
            organization=organization,
            project=pr_data["repository"]["project"]["name"]
        )
        return True, pr_info
    except (json.JSONDecodeError, KeyError) as e:
        return False, f"Failed to parse PR data: {e}"

def get_pr_files(pr_url: str) -> tuple[bool, Union[List[FileChange], str]]:
    """Get list of changed files in PR using REST API from PR URL."""
    # Parse the PR URL
    success, url_parts = parse_pr_url(pr_url)
    if not success:
        return False, f"Invalid PR URL format. Expected format: https://msazure.visualstudio.com/One/_git/repo/pullrequest/123 or https://dev.azure.com/org/project/_git/repo/pullrequest/123"
    
    # Get access token
    token_success, token = get_access_token()
    if not token_success:
        return False, f"Failed to get access token: {token}"
    
    organization = url_parts['organization']
    project = url_parts['project']
    repository = url_parts['repository']
    pr_id = url_parts['pr_id']
    
    # Build API URL according to Microsoft docs
    api_url = f"https://dev.azure.com/{organization}/{project}/_apis/git/repositories/{repository}/pullRequests/{pr_id}/iterations?api-version=7.1"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        iterations_data = response.json()
        
        if not iterations_data.get("value"):
            return False, "No iterations found in PR"
        
        # Get the latest iteration
        latest_iteration = iterations_data["value"][-1]["id"]
        
        # Get changed files for this iteration
        changes_url = f"https://dev.azure.com/{organization}/{project}/_apis/git/repositories/{repository}/pullRequests/{pr_id}/iterations/{latest_iteration}/changes?api-version=7.1"
        changes_response = requests.get(changes_url, headers=headers)
        changes_response.raise_for_status()
        changes_data = changes_response.json()
        
        changes = []
        for change_item in changes_data.get("changeEntries", []):
            item = change_item.get("item", {})
            change_type = change_item.get("changeType", "").lower()

            # Handle deleted files (where path is null but originalPath exists)
            if change_type == "delete":
                original_path = change_item.get("originalPath")
                if original_path:
                    change = FileChange(
                        path=original_path,
                        change_type="delete",
                        original_path=original_path
                    )
                    changes.append(change)
            # Handle added or edited files
            elif item.get("path"):
                change = FileChange(
                    path=item["path"],
                    change_type=change_type or "edit",
                    original_path=change_item.get("originalPath")
                )
                changes.append(change)
        
        return True, changes
    except requests.RequestException as e:
        return False, f"Failed to get PR files: {str(e)}. URL attempted: {api_url}"
    except (json.JSONDecodeError, KeyError) as e:
        return False, f"Failed to parse PR files data: {e}"

def get_file_content(file_path: str, organization: str, project: str, repository: str, commit_id: str) -> tuple[bool, str]:
    """Get content of a specific file from the repository using REST API."""
    success, token = get_access_token()
    if not success:
        return False, f"Failed to get access token: {token}"
    
    # Extract organization name from URL and clean it up
    if organization.startswith('https://'):
        org_name = organization.split('/')[-1]
        org_name = org_name.replace('.visualstudio.com', '')
    else:
        org_name = organization
    
    # Clean up repository name
    clean_repo = repository.replace('_git/', '').replace('_git', '')
    
    # Clean up commit_id - remove any trailing backslashes or special characters
    clean_commit_id = commit_id.rstrip('\\').strip()
    
    # Properly encode the file path for URL
    encoded_path = urllib.parse.quote(file_path, safe='')
    
    # Azure DevOps REST API endpoint for file content
    # Use proper URL construction with encoded parameters
    base_url = f"https://dev.azure.com/{org_name}/{project}/_apis/git/repositories/{clean_repo}/items"
    params = {
        'path': file_path,
        'version': clean_commit_id,
        'api-version': '7.0'
    }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        # Use requests with params to properly encode URL parameters
        response = requests.get(base_url, headers=headers, params=params)
        
        # Log the actual URL for debugging
        actual_url = response.url
        
        if response.status_code == 404:
            return False, f"File not found: {file_path}. URL attempted: {actual_url}"
        
        response.raise_for_status()
        
        # Check if content is base64 encoded
        content_type = response.headers.get('content-type', '')
        if 'application/json' in content_type:
            # If JSON response, it might contain base64 encoded content
            data = response.json()
            if 'content' in data:
                try:
                    # Try to decode base64 content
                    content = base64.b64decode(data['content']).decode('utf-8')
                    return True, content
                except Exception:
                    return True, data['content']
            else:
                return False, "No content found in response"
        else:
            # Direct text content
            return True, response.text
            
    except requests.RequestException as e:
        # Include the attempted URL in error message for debugging
        return False, f"Failed to get file content: {str(e)}. URL attempted: {response.url if 'response' in locals() else 'URL not constructed'}"
    except Exception as e:
        return False, f"Failed to process file content: {str(e)}"

def post_pr_comment_rest(organization: str, project: str, repository: str, pr_id: str, 
                        comment: str, file_path: Optional[str] = None, 
                        line_number: Optional[int] = None) -> tuple[bool, str]:
    """Post a comment to a PR using REST API.
    
    Args:
        organization: Azure DevOps organization name
        project: Project name
        repository: Repository name  
        pr_id: Pull Request ID
        comment: Comment text
        file_path: Optional file path for file-specific comments
        line_number: Optional line number (requires file_path)
    
    Returns:
        Tuple of (success, message)
    """
    # Validate parameters
    if line_number is not None and file_path is None:
        return False, "line_number requires file_path to be specified"
    
    # Get access token
    success, token = get_access_token()
    if not success:
        return False, f"Failed to get access token: {token}"
    
    # Clean organization name if it contains URL
    if organization.startswith('https://'):
        org_name = organization.split('/')[-1]
        org_name = org_name.replace('.visualstudio.com', '')
    else:
        org_name = organization
    
    # Build API URL
    api_url = f"https://dev.azure.com/{org_name}/{project}/_apis/git/repositories/{repository}/pullRequests/{pr_id}/threads?api-version=7.1"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Build payload
    payload = {
        "comments": [
            {
                "parentCommentId": 0,
                "content": comment,
                "commentType": 1  # Text comment
            }
        ],
        "status": 1  # Active status
    }
    
    # Add thread context for file-specific comments
    if file_path:
        thread_context = {
            "filePath": file_path
        }
        
        # Add line-specific context if line number provided
        if line_number is not None:
            thread_context["rightFileStart"] = {
                "line": line_number,
                "offset": 1
            }
            thread_context["rightFileEnd"] = {
                "line": line_number,
                "offset": 1
            }
        
        payload["threadContext"] = thread_context
    
    try:
        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()
        
        # Parse response to get comment details
        result = response.json()
        thread_id = result.get("id", "unknown")
        
        if file_path:
            if line_number:
                return True, f"File comment posted successfully on {file_path}:{line_number} (Thread ID: {thread_id})"
            else:
                return True, f"File comment posted successfully on {file_path} (Thread ID: {thread_id})"
        else:
            return True, f"General PR comment posted successfully (Thread ID: {thread_id})"
            
    except requests.RequestException as e:
        return False, f"Failed to post comment: {str(e)}. URL: {api_url}"
    except (json.JSONDecodeError, KeyError) as e:
        return False, f"Failed to parse response: {e}"

# Initialize MCP Server
server = Server("ado-pr-review")

@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List available tools."""
    return [
        Tool(
            name="check_az_login",
            description="Check if user is logged into Azure CLI",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_pr_details",
            description="Get details of an Azure DevOps Pull Request",
            inputSchema={
                "type": "object",
                "properties": {
                    "pr_id": {
                        "type": "string",
                        "description": "Pull Request ID"
                    },
                    "organization": {
                        "type": "string",
                        "description": "Azure DevOps organization URL (e.g., https://dev.azure.com/MyOrganization)"
                    }
                },
                "required": ["pr_id", "organization"]
            }
        ),
        Tool(
            name="get_pr_files",
            description="Get list of changed files in a Pull Request from PR URL",
            inputSchema={
                "type": "object",
                "properties": {
                    "pr_url": {
                        "type": "string",
                        "description": "Full PR URL (e.g., https://msazure.visualstudio.com/One/_git/azlocal-overlay/pullrequest/12479934)"
                    }
                },
                "required": ["pr_url"]
            }
        ),
        Tool(
            name="get_file_content",
            description="Get content of a specific file from the repository using REST API",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file"
                    },
                    "organization": {
                        "type": "string",
                        "description": "Azure DevOps organization URL (e.g., https://dev.azure.com/MyOrganization)"
                    },
                    "project": {
                        "type": "string",
                        "description": "Project name"
                    },
                    "repository": {
                        "type": "string",
                        "description": "Repository name"
                    },
                    "commit_id": {
                        "type": "string",
                        "description": "Commit ID to get file content from"
                    }
                },
                "required": ["file_path", "organization", "project", "repository", "commit_id"]
            }
        ),
        Tool(
            name="post_pr_comment",
            description="Post a comment to an Azure DevOps Pull Request (general or file-specific)",
            inputSchema={
                "type": "object",
                "properties": {
                    "pr_id": {
                        "type": "string",
                        "description": "Pull Request ID"
                    },
                    "organization": {
                        "type": "string",
                        "description": "Azure DevOps organization name or URL (e.g., 'myorg' or 'https://dev.azure.com/myorg')"
                    },
                    "project": {
                        "type": "string",
                        "description": "Project name"
                    },
                    "repository": {
                        "type": "string",
                        "description": "Repository name"
                    },
                    "comment": {
                        "type": "string",
                        "description": "Comment text"
                    },
                    "file_path": {
                        "type": "string",
                        "description": "Optional: Path to the file to comment on (for file-specific comments)"
                    },
                    "line_number": {
                        "type": "integer",
                        "description": "Optional: Line number to comment on (requires file_path)"
                    }
                },
                "required": ["pr_id", "organization", "project", "repository", "comment"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls."""
    
    if name == "check_az_login":
        success, message = check_az_login()
        status = "✅ Azure CLI Login Status" if success else "❌ Azure CLI Login Status"
        return [TextContent(type="text", text=f"{status}\n\n{message}")]
    
    elif name == "get_pr_details":
        pr_id = arguments["pr_id"]
        organization = arguments["organization"]
        
        success, result = get_pr_details(pr_id, organization)
        if success:
            pr_info = result
            details = f"""## Pull Request Details

**ID:** {pr_info.id}
**Title:** {pr_info.title}
**Author:** {pr_info.author}
**Status:** {pr_info.status}
**Created:** {pr_info.created_date}

**Branches:**
- Source: `{pr_info.source_branch}`
- Target: `{pr_info.target_branch}`

**Repository:** {pr_info.organization}/{pr_info.project}/{pr_info.repository}

**Description:**
{pr_info.description or 'No description provided'}
"""
            return [TextContent(type="text", text=details)]
        else:
            return [TextContent(type="text", text=f"❌ Error: {result}")]
    
    elif name == "get_pr_files":
        pr_url = arguments["pr_url"]
        
        success, result = get_pr_files(pr_url)
        if success:
            changes = result
            files_list = "## Changed Files\n\n"
            for change in changes:
                emoji = {"add": "➕", "edit": "✏️", "delete": "❌"}.get(change.change_type.lower(), "📝")
                files_list += f"{emoji} `{change.path}` ({change.change_type})\n"
            
            files_list += f"\n**Total files changed:** {len(changes)}"
            return [TextContent(type="text", text=files_list)]
        else:
            return [TextContent(type="text", text=f"❌ Error: {result}")]
    
    elif name == "get_file_content":
        file_path = arguments["file_path"]
        organization = arguments["organization"]
        project = arguments["project"]
        repository = arguments["repository"]
        commit_id = arguments["commit_id"]
        
        success, content = get_file_content(file_path, organization, project, repository, commit_id)
        if success:
            return [TextContent(type="text", text=f"## File Content: {file_path}\n\n```\n{content}\n```")]
        else:
            return [TextContent(type="text", text=f"❌ Error: {content}")]
    
    elif name == "post_pr_comment":
        pr_id = arguments["pr_id"]
        organization = arguments["organization"]
        project = arguments["project"]
        repository = arguments["repository"]
        comment = arguments["comment"]
        file_path = arguments.get("file_path")
        line_number = arguments.get("line_number")
        
        success, message = post_pr_comment_rest(organization, project, repository, pr_id, comment, file_path, line_number)
        status = "✅" if success else "❌"
        return [TextContent(type="text", text=f"{status} {message}")]
    
    else:
        return [TextContent(type="text", text=f"❌ Unknown tool: {name}")]

async def main():
    """Main entry point for the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="ado-pr-review",
                server_version="1.0.0",
                capabilities=ServerCapabilities(
                    tools={}
                ),
            ),
        )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
