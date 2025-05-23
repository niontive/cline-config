#!/usr/bin/env python3
"""
Azure DevOps Pull Request Review MCP Server

Provides tools for reviewing Azure DevOps Pull Requests through Cline.
"""

import json
import subprocess
import sys
import os
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

def run_az_command(cmd: List[str]) -> tuple[bool, str, str]:
    """Execute Azure CLI command and return success, stdout, stderr."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

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

def get_pr_details(pr_id: str, organization: str, project: str, repository: str) -> tuple[bool, Union[PRInfo, str]]:
    """Get PR details from Azure DevOps."""
    cmd = [
        "az", "repos", "pr", "show",
        "--id", pr_id,
        "--organization", f"https://dev.azure.com/{organization}",
        "--project", project,
        "--repository", repository,
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
            repository=repository,
            organization=organization,
            project=project
        )
        return True, pr_info
    except (json.JSONDecodeError, KeyError) as e:
        return False, f"Failed to parse PR data: {e}"

def get_pr_files(pr_id: str, organization: str, project: str, repository: str) -> tuple[bool, Union[List[FileChange], str]]:
    """Get list of changed files in PR."""
    cmd = [
        "az", "repos", "pr", "list-files",
        "--id", pr_id,
        "--organization", f"https://dev.azure.com/{organization}",
        "--project", project,
        "--repository", repository,
        "--output", "json"
    ]
    
    success, stdout, stderr = run_az_command(cmd)
    if not success:
        return False, f"Failed to get PR files: {stderr}"
    
    try:
        files_data = json.loads(stdout)
        changes = []
        for file_data in files_data:
            change = FileChange(
                path=file_data["path"],
                change_type=file_data["changeType"],
                original_path=file_data.get("originalPath")
            )
            changes.append(change)
        return True, changes
    except (json.JSONDecodeError, KeyError) as e:
        return False, f"Failed to parse files data: {e}"

def get_file_content(file_path: str, organization: str, project: str, repository: str, commit_id: str) -> tuple[bool, str]:
    """Get content of a specific file from the repository."""
    cmd = [
        "az", "repos", "item", "show",
        "--path", file_path,
        "--organization", f"https://dev.azure.com/{organization}",
        "--project", project,
        "--repository", repository,
        "--version-type", "commit",
        "--version", commit_id
    ]
    
    success, stdout, stderr = run_az_command(cmd)
    if not success:
        return False, f"Failed to get file content: {stderr}"
    
    return True, stdout

def post_pr_comment(pr_id: str, organization: str, project: str, repository: str, 
                   file_path: str, line: int, comment: str) -> tuple[bool, str]:
    """Post a comment to a PR."""
    cmd = [
        "az", "repos", "pr", "create-comment",
        "--id", pr_id,
        "--organization", f"https://dev.azure.com/{organization}",
        "--project", project,
        "--repository", repository,
        "--content", comment,
        "--path", file_path,
        "--position", str(line)
    ]
    
    success, stdout, stderr = run_az_command(cmd)
    if not success:
        return False, f"Failed to post comment: {stderr}"
    
    return True, "Comment posted successfully"

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
                        "description": "Azure DevOps organization name"
                    },
                    "project": {
                        "type": "string",
                        "description": "Project name"
                    },
                    "repository": {
                        "type": "string",
                        "description": "Repository name"
                    }
                },
                "required": ["pr_id", "organization", "project", "repository"]
            }
        ),
        Tool(
            name="get_pr_files",
            description="Get list of changed files in a Pull Request",
            inputSchema={
                "type": "object",
                "properties": {
                    "pr_id": {
                        "type": "string",
                        "description": "Pull Request ID"
                    },
                    "organization": {
                        "type": "string",
                        "description": "Azure DevOps organization name"
                    },
                    "project": {
                        "type": "string",
                        "description": "Project name"
                    },
                    "repository": {
                        "type": "string",
                        "description": "Repository name"
                    }
                },
                "required": ["pr_id", "organization", "project", "repository"]
            }
        ),
        Tool(
            name="get_file_content",
            description="Get content of a specific file from the repository",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file"
                    },
                    "organization": {
                        "type": "string",
                        "description": "Azure DevOps organization name"
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
            description="Post a comment to an Azure DevOps Pull Request",
            inputSchema={
                "type": "object",
                "properties": {
                    "pr_id": {
                        "type": "string",
                        "description": "Pull Request ID"
                    },
                    "organization": {
                        "type": "string",
                        "description": "Azure DevOps organization name"
                    },
                    "project": {
                        "type": "string",
                        "description": "Project name"
                    },
                    "repository": {
                        "type": "string",
                        "description": "Repository name"
                    },
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file to comment on"
                    },
                    "line": {
                        "type": "integer",
                        "description": "Line number to comment on"
                    },
                    "comment": {
                        "type": "string",
                        "description": "Comment text"
                    }
                },
                "required": ["pr_id", "organization", "project", "repository", "file_path", "line", "comment"]
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
        project = arguments["project"]
        repository = arguments["repository"]
        
        success, result = get_pr_details(pr_id, organization, project, repository)
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
        pr_id = arguments["pr_id"]
        organization = arguments["organization"]
        project = arguments["project"]
        repository = arguments["repository"]
        
        success, result = get_pr_files(pr_id, organization, project, repository)
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
        file_path = arguments["file_path"]
        line = arguments["line"]
        comment = arguments["comment"]
        
        success, message = post_pr_comment(pr_id, organization, project, repository, file_path, line, comment)
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
