Write-Host "AI Control Center - Connection Check" -ForegroundColor Cyan

$envFile = "configs\secrets\api.env"
$hasError = $false

function Load-EnvFile {
    param([string]$Path)

    if (!(Test-Path $Path)) {
        Write-Host "Missing $Path" -ForegroundColor Red
        exit 1
    }

    Get-Content $Path | ForEach-Object {
        $line = $_.Trim()
        if ($line -eq "") { return }
        if ($line.StartsWith("#")) { return }

        $parts = $line -split "=", 2
        if ($parts.Length -eq 2) {
            $key = $parts[0].Trim()
            $value = $parts[1].Trim()
            [Environment]::SetEnvironmentVariable($key, $value, "Process")
        }
    }
}

function Test-EnvValue {
    param([string]$Name, [string]$Value)

    if ([string]::IsNullOrWhiteSpace($Value)) {
        Write-Host "[FAIL] $Name is missing" -ForegroundColor Red
        return $false
    }

    Write-Host "[OK] $Name is set" -ForegroundColor Green
    return $true
}

function Test-OpenAI {
    if (!(Test-EnvValue "OPENAI_API_KEY" $env:OPENAI_API_KEY)) {
        return $false
    }

    try {
        $params = @{
            Uri = "https://api.openai.com/v1/models"
            Method = "Get"
            Headers = @{
                Authorization = "Bearer $env:OPENAI_API_KEY"
            }
            TimeoutSec = 20
        }

        $response = Invoke-RestMethod @params
        Write-Host "[OK] OpenAI connected" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "[FAIL] OpenAI connection failed" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor DarkGray
        return $false
    }
}

function Test-Notion {
    if (!(Test-EnvValue "NOTION_API_KEY" $env:NOTION_API_KEY)) {
        return $false
    }

    try {
        $params = @{
            Uri = "https://api.notion.com/v1/users/me"
            Method = "Get"
            Headers = @{
                Authorization = "Bearer $env:NOTION_API_KEY"
                "Notion-Version" = "2022-06-28"
            }
            TimeoutSec = 20
        }

        $response = Invoke-RestMethod @params
        Write-Host "[OK] Notion connected" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "[FAIL] Notion connection failed" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor DarkGray
        return $false
    }
}

function Test-GitHub {
    if (!(Test-EnvValue "GITHUB_TOKEN" $env:GITHUB_TOKEN)) {
        return $false
    }

    try {
        $params = @{
            Uri = "https://api.github.com/user"
            Method = "Get"
            Headers = @{
                Authorization = "Bearer $env:GITHUB_TOKEN"
                "User-Agent" = "AIControlCenter"
                Accept = "application/vnd.github+json"
            }
            TimeoutSec = 20
        }

        $response = Invoke-RestMethod @params
        Write-Host "[OK] GitHub connected as $($response.login)" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "[FAIL] GitHub connection failed" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor DarkGray
        return $false
    }
}

Load-EnvFile $envFile

Write-Host ""
Write-Host "Checking environment..." -ForegroundColor Cyan

Test-EnvValue "AI_PROVIDER" $env:AI_PROVIDER | Out-Null
Test-EnvValue "OPENAI_MODEL" $env:OPENAI_MODEL | Out-Null
Test-EnvValue "OPENAI_EMBEDDING_MODEL" $env:OPENAI_EMBEDDING_MODEL | Out-Null

Write-Host ""
Write-Host "Checking API connections..." -ForegroundColor Cyan

if (!(Test-OpenAI)) { $hasError = $true }
if (!(Test-Notion)) { $hasError = $true }
if (!(Test-GitHub)) { $hasError = $true }

Write-Host ""

if ($hasError) {
    Write-Host "Connection check completed with errors." -ForegroundColor Yellow
    exit 1
}

Write-Host "Environment Ready." -ForegroundColor Green
exit 0