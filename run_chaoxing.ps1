$ErrorActionPreference = "Stop"

# 用脚本自身所在目录锚定路径，不要用调用者的当前目录。
# 否则从别处（快捷方式、计划任务、%USERPROFILE% 下的 shell）用绝对路径调用时，
# .env 明明存在却检测不到，脚本会转而向你索要真实账号密码。
$root = $PSScriptRoot
$envFile = Join-Path $root ".env"
$mainScript = Join-Path $root "main.py"

if (Test-Path $envFile) {
    python $mainScript @args
    exit $LASTEXITCODE
}

$username = Read-Host "Chaoxing username or phone"
$securePassword = Read-Host "Chaoxing password" -AsSecureString
$passwordPtr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword)

try {
    $env:CX_USERNAME = $username
    $env:CX_PASSWORD = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($passwordPtr)
    python $mainScript @args
}
finally {
    if ($passwordPtr -ne [IntPtr]::Zero) {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($passwordPtr)
    }
    Remove-Item Env:\CX_USERNAME -ErrorAction SilentlyContinue
    Remove-Item Env:\CX_PASSWORD -ErrorAction SilentlyContinue
}
