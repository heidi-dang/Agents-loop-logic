# OpenCode OpenAI Smoke Test for Windows
# Run: .\scripts\smoke_opencode_openai.ps1

$ErrorActionPreference = "Continue"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "OpenCode OpenAI Smoke Test (Windows)" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

$BACKEND_URL = if ($env:BACKEND_URL) { $env:BACKEND_URL } else { "http://127.0.0.1:7777" }
$FAILED = 0

Write-Host ""
Write-Host "=== Test 1: Check heidi version ===" -ForegroundColor Yellow
try {
    heidi --version
    Write-Host "OK: heidi installed" -ForegroundColor Green
} catch {
    Write-Host "FAIL: heidi not found" -ForegroundColor Red
    $FAILED = 1
}

Write-Host ""
Write-Host "=== Test 2: Check OpenCode version ===" -ForegroundColor Yellow
try {
    opencode --version
    Write-Host "OK: OpenCode installed" -ForegroundColor Green
} catch {
    Write-Host "FAIL: OpenCode not found" -ForegroundColor Red
    $FAILED = 1
}

Write-Host ""
Write-Host "=== Test 3: heidi connect opencode openai --verify --json ===" -ForegroundColor Yellow
$OUTPUT = heidi connect opencode openai --verify --json 2>&1 | Out-String
Write-Host $OUTPUT
if ($OUTPUT -match '"ok":true') {
    Write-Host "OK: Verify shows connected" -ForegroundColor Green
} else {
    Write-Host "INFO: Not connected (expected if not OAuth'd yet)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== Test 4: Backend status endpoint ===" -ForegroundColor Yellow
try {
    $STATUS = Invoke-RestMethod -Uri "$BACKEND_URL/api/connect/opencode/openai/status" -UseBasicParsing -ErrorAction SilentlyContinue
    $STATUS | ConvertTo-Json -Depth 3
    if ($STATUS.connected -eq $true) {
        Write-Host "OK: Backend status shows connected" -ForegroundColor Green
    } else {
        Write-Host "INFO: Not connected" -ForegroundColor Yellow
    }
} catch {
    Write-Host "FAIL: Could not reach backend" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== Test 5: Backend test endpoint ===" -ForegroundColor Yellow
try {
    $TEST = Invoke-RestMethod -Uri "$BACKEND_URL/api/connect/opencode/openai/test" -Method Post -UseBasicParsing -ErrorAction SilentlyContinue
    $TEST | ConvertTo-Json -Depth 3
    if ($TEST.pass -eq $true) {
        Write-Host "OK: Test endpoint works" -ForegroundColor Green
    } else {
        Write-Host "INFO: Test endpoint (may need OAuth)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "FAIL: Could not reach test endpoint" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== Test 6: opencode models openai ===" -ForegroundColor Yellow
$MODELS = opencode models openai 2>&1 | Out-String
if ($MODELS) {
    Write-Host "OK: opencode models openai returns output" -ForegroundColor Green
    Write-Host $MODELS
} else {
    Write-Host "INFO: No models (needs OAuth)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Smoke test complete" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
