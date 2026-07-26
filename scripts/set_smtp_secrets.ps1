[CmdletBinding()]
param(
    [string]$Repository = "KoreaSon-polymer/VS-cord"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Read-RequiredValue {
    param(
        [Parameter(Mandatory)]
        [string]$Prompt,

        [string]$DefaultValue = ""
    )

    while ($true) {
        $suffix = if ($DefaultValue) { " [$DefaultValue]" } else { "" }
        $value = Read-Host "$Prompt$suffix"
        if (-not $value) {
            $value = $DefaultValue
        }
        if (-not [string]::IsNullOrWhiteSpace($value)) {
            return $value.Trim()
        }
        Write-Warning "$Prompt is required."
    }
}

function Set-RepositorySecret {
    param(
        [Parameter(Mandatory)]
        [string]$Name,

        [Parameter(Mandatory)]
        [AllowEmptyString()]
        [string]$Value
    )

    $Value | & gh secret set $Name --repo $Repository | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to set repository secret: $Name"
    }
}

& gh auth status | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "GitHub CLI is not authenticated. Run: gh auth login"
}

$smtpHost = Read-RequiredValue -Prompt "SMTP_HOST" -DefaultValue "smtp.gmail.com"
$smtpPort = Read-RequiredValue -Prompt "SMTP_PORT" -DefaultValue "587"
$parsedPort = 0
if (
    -not [int]::TryParse($smtpPort, [ref]$parsedPort) -or
    $parsedPort -lt 1 -or
    $parsedPort -gt 65535
) {
    throw "SMTP_PORT must be an integer from 1 to 65535."
}

$smtpUsername = Read-RequiredValue -Prompt "SMTP_USERNAME"
$smtpPassword = Read-Host "SMTP_PASSWORD (input hidden)" -AsSecureString
if ($smtpPassword.Length -eq 0) {
    throw "SMTP_PASSWORD is required."
}
$smtpFrom = Read-RequiredValue -Prompt "SMTP_FROM" -DefaultValue $smtpUsername
$monitorEmailTo = Read-RequiredValue -Prompt "MONITOR_EMAIL_TO"

Set-RepositorySecret -Name "SMTP_HOST" -Value $smtpHost
Set-RepositorySecret -Name "SMTP_PORT" -Value $smtpPort
Set-RepositorySecret -Name "SMTP_USERNAME" -Value $smtpUsername
Set-RepositorySecret -Name "SMTP_FROM" -Value $smtpFrom
Set-RepositorySecret -Name "MONITOR_EMAIL_TO" -Value $monitorEmailTo

$passwordPointer = [IntPtr]::Zero
$plainPassword = $null
try {
    $passwordPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR(
        $smtpPassword
    )
    $plainPassword = [Runtime.InteropServices.Marshal]::PtrToStringBSTR(
        $passwordPointer
    )
    Set-RepositorySecret -Name "SMTP_PASSWORD" -Value $plainPassword
}
finally {
    $plainPassword = $null
    if ($passwordPointer -ne [IntPtr]::Zero) {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($passwordPointer)
    }
}

Write-Output "Configured GitHub Actions secret names:"
& gh secret list --repo $Repository --app actions --json name --jq ".[].name"
if ($LASTEXITCODE -ne 0) {
    throw "Secrets were set, but verification failed."
}
