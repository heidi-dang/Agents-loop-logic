$ErrorActionPreference = "Stop"

$HeidiCmd = if ($env:HEIDI_CMD) { $env:HEIDI_CMD } else { "heidi" }

function Fail($msg) {
  Write-Error "FAIL: $msg"
  exit 1
}

function Invoke-OrFail([string]$label, [string[]]$cmd) {
  Write-Host ("Command: " + ($cmd -join " "))
  & $cmd[0] $cmd[1..($cmd.Length-1)] | Out-Host
  if ($LASTEXITCODE -ne 0) { Fail "$label (exit=$LASTEXITCODE)" }
}

function Assert-JsonOnly([string]$out) {
  $py = @'
import json
import sys

s = sys.stdin.read()
try:
    json.loads(s)
except Exception as e:
    head = s[:200].replace("\n", "\\n")
    sys.stderr.write(f"Invalid JSON: {e}\n")
    sys.stderr.write(f"First 200 chars: {head}\n")
    sys.exit(1)
'@

  $out | python -c $py | Out-Null
  if ($LASTEXITCODE -ne 0) { Fail "Output is not valid JSON" }

  if ($out -match "\x1b\[") {
    Fail "JSON output contains ANSI escape codes"
  }
}

Write-Host "=========================================="
Write-Host "Heidi CLI Smoke (Render Policy / Plain / JSON)"
Write-Host "=========================================="

Write-Host ""
Write-Host "=== Test 1: plain flag end-to-end (setup) ==="
Write-Host "NOTE: This is interactive; answer prompts or Ctrl+C to exit."
Write-Host "Command: $HeidiCmd --plain setup"
& $HeidiCmd --plain setup | Out-Host

Write-Host ""
Write-Host "=== Test 2: plain flag end-to-end (doctor) ==="
Invoke-OrFail "plain doctor" @($HeidiCmd, "--plain", "doctor")

Write-Host ""
Write-Host "=== Test 3: JSON integrity (paths --json) ==="
$out = ""
try { $out = & $HeidiCmd paths --json 2>$null } catch { Fail "paths --json failed" }
if ([string]::IsNullOrWhiteSpace($out)) { Fail "paths --json produced no output" }
Assert-JsonOnly $out
Write-Host "OK"

Write-Host ""
Write-Host "=== Test 4: JSON integrity (doctor --json) ==="
$out = ""
try { $out = & $HeidiCmd doctor --json 2>$null } catch { Fail "doctor --json failed" }
if ([string]::IsNullOrWhiteSpace($out)) { Fail "doctor --json produced no output" }
Assert-JsonOnly $out
Write-Host "OK"

Write-Host ""
Write-Host "=== Test 5: env still works (HEIDI_PLAIN=1) ==="
$env:HEIDI_PLAIN = "1"
try { & $HeidiCmd setup | Out-Host } catch { }
Remove-Item Env:HEIDI_PLAIN -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "=== Test 6: env still works (NO_COLOR=1) ==="
$env:NO_COLOR = "1"
try { & $HeidiCmd setup | Out-Host } catch { }
Remove-Item Env:NO_COLOR -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "=== Test 7: StreamingUI safety (non-interactive) ==="
python -c "from heidi_cli.streaming import StreamingUI; ui=StreamingUI(disable=False); ui.start('t'); ui.update('ok'); ui.stop('done')" | Out-Host
if ($LASTEXITCODE -ne 0) { Fail "StreamingUI snippet failed" }

Write-Host ""
Write-Host "=========================================="
Write-Host "Smoke checks completed."
Write-Host "Manual Ctrl+C checks to run:"
Write-Host "  - $HeidiCmd setup  (press Ctrl+C during Step 2 spinner)"
Write-Host "  - $HeidiCmd auth device  (press Ctrl+C during polling spinner)"
Write-Host "PASS looks like:"
Write-Host "  - cursor is visible"
Write-Host "  - prompt accepts typing immediately"
Write-Host "  - no stuck styling (colors), no spinner characters left behind"
