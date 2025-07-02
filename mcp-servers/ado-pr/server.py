#!/usr/bin/env python3
"""
Azure DevOps Pull Request MCP Server

Provides tools for creating and reviewing Azure DevOps Pull Requests through Cline.
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

def clean_organization_name(organization: str) -> str:
    """Clean organization name from URL format."""
    if organization.startswith('https://'):
        org_name = organization.split('/')[-1]
        org_name = org_name.replace('.visualstudio.com', '')
    else:
        org_name = organization
    return org_name

def validate_branch_exists(organization: str, project: str, repository: str, branch_name: str) -> tuple[bool, str]:
    """Validate that a branch exists in the repository."""
    success, token = get_access_token()
    if not success:
        return False, f"Failed to get access token: {token}"
    
    org_name = clean_organization_name(organization)
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        # Get branch information
        api_url = f"https://dev.azure.com/{org_name}/{project}/_apis/git/repositories/{repository}/refs?filter=heads/{branch_name}&api-version=7.1"
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        if not data.get("value"):
            return False, f"Branch '{branch_name}' not found in repository"
        
        return True, f"Branch '{branch_name}' exists"
        
    except requests.RequestException as e:
        return False, f"Failed to validate branch: {str(e)}"

def resolve_reviewers(organization: str, project: str, reviewers: List[str]) -> tuple[bool, Union[List[Dict], str]]:
    """Resolve reviewer emails/usernames to Azure DevOps user IDs."""
    if not reviewers:
        return True, []
    
    success, token = get_access_token()
    if not success:
        return False, f"Failed to get access token: {token}"
    
    org_name = clean_organization_name(organization)
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    resolved_reviewers = []
    
    for reviewer in reviewers:
        try:
            # Try to find user by email or display name
            # First try by email
            api_url = f"https://dev.azure.com/{org_name}/_apis/graph/users?subjectDescriptor={reviewer}&api-version=7.1-preview.1"
            response = requests.get(api_url, headers=headers)
            
            if response.status_code == 404:
                # If not found by descriptor, try searching by display name or email
                search_url = f"https://dev.azure.com/{org_name}/_apis/identities?searchFilter=General&filterValue={reviewer}&api-version=7.1"
                search_response = requests.get(search_url, headers=headers)
                
                if search_response.status_code == 200:
                    search_data = search_response.json()
                    if search_data.get("value"):
                        user_id = search_data["value"][0]["id"]
                        resolved_reviewers.append({"id": user_id})
                    else:
                        # If user not found, add as display name (Azure DevOps will handle resolution)
                        resolved_reviewers.append({"displayName": reviewer})
                else:
                    resolved_reviewers.append({"displayName": reviewer})
            else:
                response.raise_for_status()
                user_data = response.json()
                resolved_reviewers.append({"id": user_data["principalName"]})
                
        except requests.RequestException:
            # If resolution fails, add as display name
            resolved_reviewers.append({"displayName": reviewer})
    
    return True, resolved_reviewers

def create_pull_request(organization: str, project: str, repository: str, source_branch: str, 
                       target_branch: str, title: str, description: Optional[str] = None,
                       reviewers: Optional[List[str]] = None, work_items: Optional[List[str]] = None,
                       auto_complete: bool = False, draft: bool = False) -> tuple[bool, str]:
    """Create a new Pull Request in Azure DevOps."""
    
    # Get access token
    success, token = get_access_token()
    if not success:
        return False, f"Failed to get access token: {token}"
    
    org_name = clean_organization_name(organization)
    
    # Validate source branch exists
    success, message = validate_branch_exists(organization, project, repository, source_branch)
    if not success:
        return False, f"Source branch validation failed: {message}"
    
    # Validate target branch exists
    success, message = validate_branch_exists(organization, project, repository, target_branch)
    if not success:
        return False, f"Target branch validation failed: {message}"
    
    # Resolve reviewers
    success, resolved_reviewers = resolve_reviewers(organization, project, reviewers or [])
    if not success:
        return False, f"Failed to resolve reviewers: {resolved_reviewers}"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Build PR payload
    payload = {
        "sourceRefName": f"refs/heads/{source_branch}",
        "targetRefName": f"refs/heads/{target_branch}",
        "title": title,
        "description": description or "",
        "isDraft": draft
    }
    
    # Add reviewers if provided
    if resolved_reviewers:
        payload["reviewers"] = resolved_reviewers
    
    # Add work items if provided
    if work_items:
        payload["workItemRefs"] = [{"id": str(item_id)} for item_id in work_items]
    
    # Add auto-complete settings if requested
    if auto_complete:
        payload["completionOptions"] = {
            "deleteSourceBranch": True,
            "mergeCommitMessage": f"Merge pull request: {title}",
            "squashMerge": False
        }
    
    try:
        # Create the PR
        api_url = f"https://dev.azure.com/{org_name}/{project}/_apis/git/repositories/{repository}/pullrequests?api-version=7.1"
        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()
        
        pr_data = response.json()
        pr_id = pr_data["pullRequestId"]
        pr_url = pr_data["url"].replace("_apis/git/repositories/", "_git/").replace("/pullrequests/", "/pullrequest/")
        
        # Build success message
        status_text = "draft " if draft else ""
        work_items_text = f" with work items {', '.join(work_items)}" if work_items else ""
        reviewers_text = f" and reviewers {', '.join(reviewers)}" if reviewers else ""
        
        success_message = f"""✅ Pull Request created successfully!

**PR #{pr_id}**: {title}
**URL**: {pr_url}
**Branches**: `{source_branch}` → `{target_branch}`
**Status**: {status_text}Pull Request{work_items_text}{reviewers_text}

The PR is ready for review and can be accessed at the URL above."""
        
        return True, success_message
        
    except requests.RequestException as e:
        return False, f"Failed to create PR: {str(e)}"
    except (json.JSONDecodeError, KeyError) as e:
        return False, f"Failed to parse PR creation response: {e}"

class PRInfoExtended(BaseModel):
    """Extended PR information including iteration data for subsequent tool calls."""
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
    latest_commit_id: str
    source_commit_id: str

def get_pr_info(pr_url: str) -> tuple[bool, Union[PRInfoExtended, str]]:
    """Get comprehensive PR information from Azure DevOps using PR URL."""
    # Parse the PR URL
    success, url_parts = parse_pr_url(pr_url)
    if not success:
        return False, f"Invalid PR URL format. Expected format: https://msazure.visualstudio.com/One/_git/repo/pullrequest/123 or https://dev.azure.com/org/project/_git/repo/pullrequest/123"
    
    organization = url_parts['organization']
    project = url_parts['project']
    repository = url_parts['repository']
    pr_id = url_parts['pr_id']
    
    # Get basic PR details using Azure CLI
    org_url = f"https://dev.azure.com/{organization}"
    cmd = [
        "az", "repos", "pr", "show",
        "--id", pr_id,
        "--organization", org_url,
        "--output", "json"
    ]
    
    success, stdout, stderr = run_az_command(cmd)
    if not success:
        return False, f"Failed to get PR details: {stderr}"
    
    try:
        pr_data = json.loads(stdout)
    except (json.JSONDecodeError, KeyError) as e:
        return False, f"Failed to parse PR data: {e}"
    
    # Get iteration information for commit IDs using REST API
    token_success, token = get_access_token()
    if not token_success:
        return False, f"Failed to get access token: {token}"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        # Get PR iterations to find latest commit IDs
        api_url = f"https://dev.azure.com/{organization}/{project}/_apis/git/repositories/{repository}/pullRequests/{pr_id}/iterations?api-version=7.1"
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        iterations_data = response.json()
        
        if not iterations_data.get("value"):
            return False, "No iterations found in PR"
        
        # Get the latest iteration for commit IDs
        latest_iteration = iterations_data["value"][-1]
        latest_commit_id = latest_iteration.get("targetRefCommit", {}).get("commitId", "")
        source_commit_id = latest_iteration.get("sourceRefCommit", {}).get("commitId", "")
        
        if not latest_commit_id:
            return False, "Could not determine latest commit ID from PR iterations"
        
        # Build comprehensive PR info
        pr_info = PRInfoExtended(
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
            project=project,
            latest_commit_id=latest_commit_id,
            source_commit_id=source_commit_id
        )
        return True, pr_info
        
    except requests.RequestException as e:
        return False, f"Failed to get PR iteration info: {str(e)}"
    except (json.JSONDecodeError, KeyError) as e:
        return False, f"Failed to parse PR iteration data: {e}"

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

def get_file_content(file_path: str, pr_url: str) -> tuple[bool, str]:
    """Get content of a specific file from the latest iteration of a Pull Request.
    
    This function automatically uses the source commit from the PR's latest iteration,
    ensuring you always get the file content from the PR changes, not the target branch.
    """
    # Parse the PR URL to extract components
    success, url_parts = parse_pr_url(pr_url)
    if not success:
        return False, f"Invalid PR URL format. Expected format: https://msazure.visualstudio.com/One/_git/repo/pullrequest/123 or https://dev.azure.com/org/project/_git/repo/pullrequest/123"
    
    # Get access token
    success, token = get_access_token()
    if not success:
        return False, f"Failed to get access token: {token}"
    
    organization = url_parts['organization']
    project = url_parts['project']
    repository = url_parts['repository']
    pr_id = url_parts['pr_id']
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        # Step 1: Get PR iterations to find the latest source commit ID
        iterations_url = f"https://dev.azure.com/{organization}/{project}/_apis/git/repositories/{repository}/pullRequests/{pr_id}/iterations?api-version=7.1"
        iterations_response = requests.get(iterations_url, headers=headers)
        iterations_response.raise_for_status()
        iterations_data = iterations_response.json()
        
        if not iterations_data.get("value"):
            return False, "No iterations found in PR"
        
        # Get the latest iteration's source commit ID
        latest_iteration = iterations_data["value"][-1]
        source_commit_id = latest_iteration.get("sourceRefCommit", {}).get("commitId")
        
        if not source_commit_id:
            return False, "Could not find source commit ID from PR's latest iteration"
        
        # Step 2: Get the commit to find the tree ID
        commit_url = f"https://dev.azure.com/{organization}/{project}/_apis/git/repositories/{repository}/commits/{source_commit_id}?api-version=7.1"
        commit_response = requests.get(commit_url, headers=headers)
        
        if commit_response.status_code == 404:
            return False, f"Source commit not found: {source_commit_id}"
        
        commit_response.raise_for_status()
        commit_data = commit_response.json()
        tree_id = commit_data.get("treeId")
        
        if not tree_id:
            return False, f"Could not find tree ID for source commit {source_commit_id}"
        
        # Step 3: Get the tree to find the file's blob ID
        tree_url = f"https://dev.azure.com/{organization}/{project}/_apis/git/repositories/{repository}/trees/{tree_id}?recursive=true&api-version=7.1"
        tree_response = requests.get(tree_url, headers=headers)
        tree_response.raise_for_status()
        tree_data = tree_response.json()
        
        # Find the specific file in the tree
        file_blob_id = None
        for tree_entry in tree_data.get("treeEntries", []):
            if tree_entry.get("relativePath") == file_path.lstrip('/'):
                if tree_entry.get("gitObjectType") == "blob":
                    file_blob_id = tree_entry.get("objectId")
                    break
        
        if not file_blob_id:
            return False, f"File not found in PR source commit: {file_path}"
        
        # Step 4: Get the actual file content using the blob ID
        blob_url = f"https://dev.azure.com/{organization}/{project}/_apis/git/repositories/{repository}/blobs/{file_blob_id}?api-version=7.1"
        blob_response = requests.get(blob_url, headers=headers)
        blob_response.raise_for_status()
        
        # Handle different response formats
        content_type = blob_response.headers.get('content-type', '')
        
        if 'application/json' in content_type:
            # Sometimes the response is JSON with base64 content
            blob_data = blob_response.json()
            if 'content' in blob_data:
                try:
                    # Decode base64 content
                    content = base64.b64decode(blob_data['content']).decode('utf-8')
                    return True, content
                except Exception as e:
                    return False, f"Failed to decode file content: {e}"
            else:
                return False, "No content found in blob response"
        else:
            # Direct text content
            try:
                return True, blob_response.text
            except UnicodeDecodeError:
                # If it's a binary file, return base64 encoded content
                content_b64 = base64.b64encode(blob_response.content).decode('utf-8')
                return True, f"[Binary file - base64 encoded]\n{content_b64}"
            
    except requests.RequestException as e:
        error_msg = f"Failed to get file content from PR: {str(e)}"
        if hasattr(e, 'response') and e.response is not None:
            error_msg += f". Status: {e.response.status_code}"
            if hasattr(e.response, 'url'):
                error_msg += f". URL attempted: {e.response.url}"
        return False, error_msg
    except (json.JSONDecodeError, KeyError) as e:
        return False, f"Failed to parse API response: {e}"
    except Exception as e:
        return False, f"Unexpected error: {e}"

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
    org_name = clean_organization_name(organization)
    
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
    
    # For file-specific comments, we need to find the file in the latest iteration
    if file_path:
        try:
            # Get PR iterations to find the latest one
            iterations_url = f"https://dev.azure.com/{org_name}/{project}/_apis/git/repositories/{repository}/pullRequests/{pr_id}/iterations?api-version=7.1"
            iterations_response = requests.get(iterations_url, headers=headers)
            iterations_response.raise_for_status()
            iterations_data = iterations_response.json()
            
            if not iterations_data.get("value"):
                return False, "No iterations found in PR"
            
            # Get the latest iteration
            latest_iteration = iterations_data["value"][-1]
            latest_iteration_id = latest_iteration["id"]
            
            # Get changes for the latest iteration to verify file exists
            changes_url = f"https://dev.azure.com/{org_name}/{project}/_apis/git/repositories/{repository}/pullRequests/{pr_id}/iterations/{latest_iteration_id}/changes?api-version=7.1"
            changes_response = requests.get(changes_url, headers=headers)
            changes_response.raise_for_status()
            changes_data = changes_response.json()
            
            # Find the specific file in the changes
            file_found = False
            change_item = None
            
            for change in changes_data.get("changeEntries", []):
                item = change.get("item", {})
                if item.get("path") == file_path:
                    file_found = True
                    change_item = change
                    break
                # Also check originalPath for renamed files
                elif change.get("originalPath") == file_path:
                    file_found = True
                    change_item = change
                    break
            
            if not file_found:
                return False, f"File '{file_path}' not found in the latest PR iteration. Please verify the file path exists in the current PR changes."
            
            # Build thread context using the exact iteration and change information
            thread_context = {
                "filePath": file_path,
                "iterationContext": {
                    "firstComparingIteration": latest_iteration_id,
                    "secondComparingIteration": latest_iteration_id
                }
            }
            
            # Add line positioning if specified
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
            
        except requests.RequestException as e:
            return False, f"Failed to get PR iteration info: {str(e)}"
        except Exception as e:
            return False, f"Error processing PR iteration data: {str(e)}"
    
    # Build API URL and post the comment
    api_url = f"https://dev.azure.com/{org_name}/{project}/_apis/git/repositories/{repository}/pullRequests/{pr_id}/threads?api-version=7.1"
    
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
server = Server("ado-pr")

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
            name="create_pr",
            description="Create a new Pull Request in Azure DevOps with optional work item linking",
            inputSchema={
                "type": "object",
                "properties": {
                    "organization": {
                        "type": "string",
                        "description": "Azure DevOps organization name or URL"
                    },
                    "project": {
                        "type": "string",
                        "description": "Project name"
                    },
                    "repository": {
                        "type": "string",
                        "description": "Repository name"
                    },
                    "source_branch": {
                        "type": "string",
                        "description": "Source branch name"
                    },
                    "target_branch": {
                        "type": "string",
                        "description": "Target branch name (default: main)"
                    },
                    "title": {
                        "type": "string",
                        "description": "PR title"
                    },
                    "description": {
                        "type": "string",
                        "description": "PR description"
                    },
                    "reviewers": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of reviewer emails/usernames"
                    },
                    "work_items": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of work item IDs to link"
                    },
                    "auto_complete": {
                        "type": "boolean",
                        "description": "Enable auto-complete when policies pass (default: false)"
                    },
                    "draft": {
                        "type": "boolean",
                        "description": "Create as draft PR (default: false)"
                    }
                },
                "required": ["organization", "project", "repository", "source_branch", "title"]
            }
        ),
        Tool(
            name="get_pr_info",
            description="Get comprehensive Pull Request information including metadata and commit IDs for subsequent tool calls",
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
            description="Get content of a specific file from the latest iteration of a Pull Request",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file in the PR"
                    },
                    "pr_url": {
                        "type": "string",
                        "description": "Full PR URL (e.g., https://msazure.visualstudio.com/One/_git/azlocal-overlay/pullrequest/12479934)"
                    }
                },
                "required": ["file_path", "pr_url"]
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
    
    elif name == "create_pr":
        organization = arguments["organization"]
        project = arguments["project"]
        repository = arguments["repository"]
        source_branch = arguments["source_branch"]
        target_branch = arguments.get("target_branch", "main")  # Default to "main"
        title = arguments["title"]
        description = arguments.get("description")
        reviewers = arguments.get("reviewers")
        work_items = arguments.get("work_items")
        auto_complete = arguments.get("auto_complete", False)
        draft = arguments.get("draft", False)
        
        success, message = create_pull_request(
            organization, project, repository, source_branch, target_branch,
            title, description, reviewers, work_items, auto_complete, draft
        )
        
        return [TextContent(type="text", text=message)]
    
    elif name == "get_pr_info":
        pr_url = arguments["pr_url"]
        
        success, result = get_pr_info(pr_url)
        if success:
            pr_info = result
            details = f"""## Pull Request Information

**ID:** {pr_info.id}
**Title:** {pr_info.title}
**Author:** {pr_info.author}
**Status:** {pr_info.status}
**Created:** {pr_info.created_date}

**Branches:**
- Source: `{pr_info.source_branch}`
- Target: `{pr_info.target_branch}`

**Repository:** {pr_info.organization}/{pr_info.project}/{pr_info.repository}

**Commit IDs:**
- Latest: `{pr_info.latest_commit_id}`
- Source: `{pr_info.source_commit_id}`

**Description:**
{pr_info.description or 'No description provided'}

---
**For subsequent tool calls:**
- Organization: `{pr_info.organization}`
- Project: `{pr_info.project}`
- Repository: `{pr_info.repository}`
- Use Latest Commit ID: `{pr_info.latest_commit_id}` for `get_file_content`
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
        pr_url = arguments["pr_url"]
        
        success, content = get_file_content(file_path, pr_url)
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
                server_name="ado-pr",
                server_version="1.0.0",
                capabilities=ServerCapabilities(
                    tools={}
                ),
            ),
        )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
