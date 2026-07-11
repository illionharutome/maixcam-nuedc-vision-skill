param(
    [Parameter(Mandatory = $true)][string]$Message
)

$ErrorActionPreference = 'Stop'
git add -A
git diff --cached --quiet
if ($LASTEXITCODE -eq 0) { throw 'No staged changes to checkpoint.' }
git commit -m $Message
if ((git remote) -contains 'origin') {
    git push
} else {
    Write-Warning 'No origin remote; record this in docs/git_remote_todo.md.'
}

