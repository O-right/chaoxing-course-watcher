$ErrorActionPreference = "Stop"

if (Test-Path .\.env) {
    python main.py @args
    exit $LASTEXITCODE
}

$username = Read-Host "Chaoxing username or phone"
$securePassword = Read-Host "Chaoxing password" -AsSecureString
$passwordPtr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword)

try {
    $env:CX_USERNAME = $username
    $env:CX_PASSWORD = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($passwordPtr)
    python main.py @args
}
finally {
    if ($passwordPtr -ne [IntPtr]::Zero) {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($passwordPtr)
    }
    Remove-Item Env:\CX_USERNAME -ErrorAction SilentlyContinue
    Remove-Item Env:\CX_PASSWORD -ErrorAction SilentlyContinue
}
