# Bash Code Review Guidelines

## Bash-Specific Best Practices

### Shebang and Shell Selection
```bash
#!/bin/bash
# ✅ Good: Use specific shell, not /bin/sh for bash features

#!/usr/bin/env bash
# ✅ Good: Portable shebang for environments where bash may not be in /bin

#!/bin/sh
# ✅ Good: For POSIX-compliant scripts only
```

### Script Safety Settings
```bash
#!/bin/bash
set -euo pipefail
# -e: Exit on any command failure
# -u: Exit on undefined variables
# -o pipefail: Exit on pipe failures

# ✅ Alternative: Enable individually where needed
set -e  # Exit on error
set -u  # Exit on undefined variable
set -o pipefail  # Pipe failures cause script to fail
```

### Variable Naming and Usage
```bash
# ✅ Good: Use descriptive names and proper quoting
readonly USER_NAME="john_doe"
readonly CONFIG_FILE="/etc/myapp/config.conf"
local temp_dir="/tmp/myapp_$$"

# ✅ Good: Always quote variables
echo "User: ${USER_NAME}"
cp "${source_file}" "${destination_dir}/"

# ❌ Bad: Unquoted variables (vulnerable to word splitting)
echo "User: $USER_NAME"
cp $source_file $destination_dir/
```

## Review Checklist

### 🔴 Critical Issues

#### Security
- [ ] No hardcoded passwords or API keys
- [ ] Input validation prevents injection attacks
- [ ] File permissions set appropriately (chmod/umask)
- [ ] Temporary files created securely (mktemp)
- [ ] No eval or command injection vulnerabilities

#### Error Handling
- [ ] Script uses `set -e` or explicit error checking
- [ ] Exit codes are meaningful and documented
- [ ] Cleanup functions for temporary resources
- [ ] Error messages are informative
- [ ] Critical operations have error handling

#### File Operations
- [ ] File existence checked before operations
- [ ] Proper quoting to handle spaces in filenames
- [ ] Atomic operations for critical file updates
- [ ] Backup strategies for destructive operations
- [ ] Proper file permission handling

### 🟠 High Priority

#### Portability
- [ ] Shebang line specifies correct shell
- [ ] POSIX compliance for portable scripts
- [ ] No bashisms in scripts marked as sh
- [ ] External command availability checked
- [ ] Path assumptions avoided

#### Performance
- [ ] Efficient loops and conditionals
- [ ] Avoid unnecessary command substitutions
- [ ] Use built-in commands when possible
- [ ] Minimize subprocess creation
- [ ] Efficient text processing

#### Resource Management
- [ ] Temporary files cleaned up
- [ ] Background processes properly managed
- [ ] File descriptors closed appropriately
- [ ] Memory usage considered for large operations
- [ ] Process cleanup on script termination

### 🟡 Medium Priority

#### Code Quality
- [ ] Functions are reasonably sized (<50 lines)
- [ ] Variables have meaningful names
- [ ] Code is properly indented (2 or 4 spaces)
- [ ] Complex logic is commented
- [ ] Magic numbers replaced with variables

#### Documentation
- [ ] Script purpose documented in header
- [ ] Function documentation provided
- [ ] Usage examples included
- [ ] Dependencies documented
- [ ] Command-line options documented

### 🔵 Low Priority

#### Style
- [ ] Consistent indentation
- [ ] Proper spacing around operators
- [ ] Consistent quoting style
- [ ] Function naming conventions followed
- [ ] Line length reasonable (<120 characters)

## Common Bash Anti-Patterns

### Quoting Anti-Patterns
```bash
# ❌ Bad: Unquoted variables
if [ $USER = "root" ]; then
    echo $HOME is the home directory
fi

# ✅ Good: Proper quoting
if [[ "${USER}" == "root" ]]; then
    echo "${HOME} is the home directory"
fi

# ❌ Bad: Unquoted command substitution
files=$(ls *.txt)
for file in $files; do
    echo $file
done

# ✅ Good: Array handling
files=(*.txt)
for file in "${files[@]}"; do
    echo "${file}"
done
```

### Error Handling Anti-Patterns
```bash
# ❌ Bad: Ignoring errors
command_that_might_fail
continue_anyway

# ❌ Bad: Silent failures
command_that_might_fail > /dev/null 2>&1

# ✅ Good: Explicit error handling
if ! command_that_might_fail; then
    echo "Error: Command failed" >&2
    exit 1
fi

# ✅ Good: Using trap for cleanup
cleanup() {
    rm -f "${temp_file}"
    exit
}
trap cleanup EXIT INT TERM
```

### Variable Anti-Patterns
```bash
# ❌ Bad: Global variables without declaration
function process_data() {
    result="processed"  # Pollutes global scope
}

# ✅ Good: Local variables
function process_data() {
    local result="processed"
    echo "${result}"
}

# ❌ Bad: Modifying script arguments
shift  # Loses original $1
set -- "new" "arguments"  # Overwrites $@

# ✅ Good: Preserve original arguments
readonly ORIGINAL_ARGS=("$@")
process_args "$@"
```

## Security Best Practices

### Input Validation
```bash
# ✅ Good: Validate input parameters
validate_username() {
    local username="$1"
    
    if [[ -z "${username}" ]]; then
        echo "Error: Username cannot be empty" >&2
        return 1
    fi
    
    if [[ ! "${username}" =~ ^[a-zA-Z0-9_-]+$ ]]; then
        echo "Error: Username contains invalid characters" >&2
        return 1
    fi
    
    return 0
}

# ✅ Good: Validate file paths
validate_file_path() {
    local file_path="$1"
    
    # Check for directory traversal
    if [[ "${file_path}" =~ \.\. ]]; then
        echo "Error: Path traversal not allowed" >&2
        return 1
    fi
    
    # Ensure file is within allowed directory
    local real_path
    real_path=$(realpath "${file_path}")
    if [[ ! "${real_path}" =~ ^/allowed/directory/ ]]; then
        echo "Error: File outside allowed directory" >&2
        return 1
    fi
    
    return 0
}
```

### Secure Temporary Files
```bash
# ✅ Good: Secure temporary file creation
create_temp_file() {
    local temp_file
    temp_file=$(mktemp) || {
        echo "Error: Failed to create temporary file" >&2
        exit 1
    }
    
    # Set restrictive permissions
    chmod 600 "${temp_file}"
    
    # Ensure cleanup
    trap "rm -f '${temp_file}'" EXIT
    
    echo "${temp_file}"
}

# ✅ Good: Secure temporary directory
create_temp_dir() {
    local temp_dir
    temp_dir=$(mktemp -d) || {
        echo "Error: Failed to create temporary directory" >&2
        exit 1
    }
    
    chmod 700 "${temp_dir}"
    trap "rm -rf '${temp_dir}'" EXIT
    
    echo "${temp_dir}"
}
```

### Command Injection Prevention
```bash
# ❌ Bad: Command injection vulnerability
user_input="$1"
eval "echo ${user_input}"  # Dangerous!

# ❌ Bad: Unvalidated input in commands
filename="$1"
rm "/tmp/${filename}"  # What if filename is "../../../etc/passwd"?

# ✅ Good: Validate and sanitize input
safe_remove_temp_file() {
    local filename="$1"
    
    # Validate filename
    if [[ ! "${filename}" =~ ^[a-zA-Z0-9_.-]+$ ]]; then
        echo "Error: Invalid filename" >&2
        return 1
    fi
    
    # Use full path and verify it exists in temp directory
    local full_path="/tmp/${filename}"
    if [[ -f "${full_path}" ]]; then
        rm "${full_path}"
    else
        echo "Warning: File ${full_path} does not exist" >&2
        return 1
    fi
}
```

## Performance Optimization

### Efficient Text Processing
```bash
# ❌ Bad: Multiple external commands
count=0
while IFS= read -r line; do
    if echo "${line}" | grep -q "pattern"; then
        count=$((count + 1))
    fi
done < file.txt

# ✅ Good: Single grep command
count=$(grep -c "pattern" file.txt)

# ❌ Bad: Inefficient string operations
result=""
for word in "${words[@]}"; do
    result="${result}${word} "
done

# ✅ Good: Use arrays and printf
printf '%s ' "${words[@]}"
```

### Minimizing Subprocess Creation
```bash
# ❌ Bad: Multiple command substitutions
if [ "$(whoami)" = "root" ] && [ "$(id -u)" = "0" ]; then
    echo "Running as root"
fi

# ✅ Good: Store result and reuse
current_user=$(whoami)
current_uid=$(id -u)
if [[ "${current_user}" == "root" ]] && [[ "${current_uid}" == "0" ]]; then
    echo "Running as root"
fi

# ✅ Good: Use built-in variables when available
if [[ "${USER}" == "root" ]] && [[ "${EUID}" == "0" ]]; then
    echo "Running as root"
fi
```

### Loop Optimization
```bash
# ❌ Bad: Reading file line by line with cat
cat file.txt | while read line; do
    process_line "${line}"
done

# ✅ Good: Direct file redirection
while IFS= read -r line; do
    process_line "${line}"
done < file.txt

# ❌ Bad: Inefficient array processing
for i in $(seq 0 $((${#array[@]} - 1))); do
    process_item "${array[i]}"
done

# ✅ Good: Direct array iteration
for item in "${array[@]}"; do
    process_item "${item}"
done
```

## Function Best Practices

### Function Structure
```bash
# ✅ Good: Well-structured function
process_user_data() {
    local username="$1"
    local output_file="$2"
    
    # Input validation
    if [[ $# -ne 2 ]]; then
        echo "Usage: process_user_data <username> <output_file>" >&2
        return 1
    fi
    
    if [[ -z "${username}" ]]; then
        echo "Error: Username cannot be empty" >&2
        return 1
    fi
    
    # Main logic
    local user_info
    user_info=$(getent passwd "${username}") || {
        echo "Error: User '${username}' not found" >&2
        return 1
    }
    
    # Output
    echo "${user_info}" > "${output_file}" || {
        echo "Error: Failed to write to '${output_file}'" >&2
        return 1
    }
    
    return 0
}
```

### Error Handling in Functions
```bash
# ✅ Good: Comprehensive error handling
backup_file() {
    local source_file="$1"
    local backup_dir="$2"
    
    # Validate arguments
    [[ $# -eq 2 ]] || {
        echo "Usage: backup_file <source> <backup_dir>" >&2
        return 1
    }
    
    # Check source file exists
    [[ -f "${source_file}" ]] || {
        echo "Error: Source file '${source_file}' does not exist" >&2
        return 1
    }
    
    # Create backup directory if needed
    [[ -d "${backup_dir}" ]] || {
        mkdir -p "${backup_dir}" || {
            echo "Error: Failed to create backup directory '${backup_dir}'" >&2
            return 1
        }
    }
    
    # Perform backup with timestamp
    local backup_file="${backup_dir}/$(basename "${source_file}").$(date +%Y%m%d_%H%M%S)"
    cp "${source_file}" "${backup_file}" || {
        echo "Error: Failed to create backup '${backup_file}'" >&2
        return 1
    }
    
    echo "Backup created: ${backup_file}"
    return 0
}
```

## Testing and Debugging

### Debugging Techniques
```bash
# ✅ Good: Debug mode
if [[ "${DEBUG:-}" == "1" ]]; then
    set -x  # Enable debug output
fi

# ✅ Good: Logging function
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    echo "[${timestamp}] [${level}] ${message}" >&2
}

# Usage
log "INFO" "Starting processing"
log "ERROR" "Failed to process file: ${filename}"
```

### Test Functions
```bash
# ✅ Good: Simple test framework
run_tests() {
    local tests_passed=0
    local tests_failed=0
    
    echo "Running tests..."
    
    # Test function exists
    if command -v validate_username > /dev/null; then
        echo "✓ validate_username function exists"
        ((tests_passed++))
    else
        echo "✗ validate_username function missing"
        ((tests_failed++))
    fi
    
    # Test validation logic
    if validate_username "valid_user"; then
        echo "✓ Valid username accepted"
        ((tests_passed++))
    else
        echo "✗ Valid username rejected"
        ((tests_failed++))
    fi
    
    if ! validate_username "invalid user"; then
        echo "✓ Invalid username rejected"
        ((tests_passed++))
    else
        echo "✗ Invalid username accepted"
        ((tests_failed++))
    fi
    
    echo "Tests completed: ${tests_passed} passed, ${tests_failed} failed"
    return $((tests_failed > 0))
}
```

## Script Organization

### Script Template
```bash
#!/bin/bash
#
# Script Name: my_script.sh
# Description: Brief description of what this script does
# Author: Your Name
# Date: $(date)
# Version: 1.0
#
# Usage: ./my_script.sh [options] arguments
#
# Dependencies: 
#   - command1: Used for X
#   - command2: Used for Y
#
# Exit Codes:
#   0 - Success
#   1 - General error
#   2 - Invalid arguments
#   3 - Missing dependencies

set -euo pipefail

# Global variables
readonly SCRIPT_NAME="$(basename "$0")"
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly TEMP_DIR="$(mktemp -d)"

# Cleanup function
cleanup() {
    local exit_code=$?
    rm -rf "${TEMP_DIR}"
    exit $exit_code
}
trap cleanup EXIT INT TERM

# Usage function
usage() {
    cat << EOF
Usage: ${SCRIPT_NAME} [OPTIONS] ARGUMENTS

Description:
    Brief description of script functionality

OPTIONS:
    -h, --help      Show this help message
    -v, --verbose   Enable verbose output
    -d, --debug     Enable debug mode

EXAMPLES:
    ${SCRIPT_NAME} --verbose input_file
    ${SCRIPT_NAME} --debug --output result.txt

EOF
}

# Main function
main() {
    local verbose=false
    local debug=false
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                usage
                exit 0
                ;;
            -v|--verbose)
                verbose=true
                shift
                ;;
            -d|--debug)
                debug=true
                set -x
                shift
                ;;
            --)
                shift
                break
                ;;
            -*)
                echo "Error: Unknown option $1" >&2
                usage >&2
                exit 2
                ;;
            *)
                break
                ;;
        esac
    done
    
    # Validate arguments
    if [[ $# -eq 0 ]]; then
        echo "Error: No arguments provided" >&2
        usage >&2
        exit 2
    fi
    
    # Main script logic here
    echo "Script execution completed successfully"
}

# Only run main if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
