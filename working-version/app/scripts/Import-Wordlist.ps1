# PowerShell wrapper for import_wordlist.py
param(
    [Parameter(Mandatory=$true)]
    [string]$Language,
    
    [Parameter(Mandatory=$false)]
    [string]$Path
)

# Change to project root directory
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

# Run the Python script
if ($Path) {
    python scripts/import_wordlist.py $Language --path $Path
}
else {
    python scripts/import_wordlist.py $Language
}
