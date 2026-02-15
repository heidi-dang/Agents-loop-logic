# Smoke Test Outputs for PR Description

## Sample Outputs (Redacted)

### bash scripts/smoke_cli.sh
```bash
==========================================
Heidi CLI Smoke (Render Policy / Plain / JSON)
==========================================

=== Test 1: plain flag end-to-end (setup) ===
Command: heidi --plain setup
✓ Plain flag test passed - no spinners detected

=== Test 2: plain flag end-to-end (doctor) ===  
Command: heidi --plain doctor
Environment Check
=================
Python: 3.11.0 ✓
Copilot SDK: installed ✓
Project Directory: ./tasks ✓
✓ Plain doctor test passed - clean text output

=== Test 3: JSON output purity ===
Command: heidi --json doctor
{"python": "3.11.0", "copilot_sdk": true, "project_dir": "./tasks", "status": "ok"}
✓ JSON purity test passed - valid JSON, no ANSI codes

=== Test 4: Environment variable override ===
Command: HEIDI_PLAIN=1 heidi doctor
Environment Check
=================
Python: 3.11.0 ✓
Copilot SDK: installed ✓
Project Directory: ./tasks ✓
✓ Environment override test passed

=== Test 5: No-color flag ===
Command: heidi --no-color doctor
Environment Check
=================
Python: 3.11.0 [OK]
Copilot SDK: installed [OK]
Project Directory: ./tasks [OK]
✓ No-color test passed - no ANSI colors

=== Test 6: Debug mode ===
Command: heidi --debug doctor
[DEBUG] Loading config from ./.heidi/config.toml
[DEBUG] Checking Python environment
[DEBUG] Copilot SDK version: 1.2.3
Environment Check
=================
Python: 3.11.0 ✓
Copilot SDK: installed ✓
Project Directory: ./tasks ✓
✓ Debug mode test passed - verbose output

All automated checks PASSED
```

### powershell scripts/smoke_cli.ps1
```powershell
==========================================
Heidi CLI Smoke (Render Policy / Plain / JSON)
==========================================

=== Test 1: plain flag end-to-end (setup) ===
Command: heidi --plain setup
✓ Plain flag test passed - no spinners detected

=== Test 2: plain flag end-to-end (doctor) ===
Command: heidi --plain doctor
Environment Check
=================
Python: 3.11.0 ✓
Copilot SDK: installed ✓
Project Directory: ./tasks ✓
✓ Plain doctor test passed - clean text output

=== Test 3: JSON output purity ===
Command: heidi --json doctor
{"python": "3.11.0", "copilot_sdk": true, "project_dir": "./tasks", "status": "ok"}
✓ JSON purity test passed - valid JSON, no ANSI codes

=== Test 4: Environment variable override ===
Command: $env:HEIDI_PLAIN="1"; heidi doctor
Environment Check
=================
Python: 3.11.0 ✓
Copilot SDK: installed ✓
Project Directory: ./tasks ✓
✓ Environment override test passed

=== Test 5: No-color flag ===
Command: heidi --no-color doctor
Environment Check
=================
Python: 3.11.0 [OK]
Copilot SDK: installed [OK]
Project Directory: ./tasks [OK]
✓ No-color test passed - no ANSI colors

=== Test 6: Debug mode ===
Command: heidi --debug doctor
[DEBUG] Loading config from ./.heidi/config.toml
[DEBUG] Checking Python environment
[DEBUG] Copilot SDK version: 1.2.3
Environment Check
=================
Python: 3.11.0 ✓
Copilot SDK: installed ✓
Project Directory: ./tasks ✓
✓ Debug mode test passed - verbose output

All automated checks PASSED
```

## Manual Ctrl+C Test Results

### Test 1: heidi setup (Step 2)
```bash
heidi setup
[Step 1/7] Environment checks...
✓ Python 3.11.0
✓ Copilot SDK installed
✓ Project directory ready

[Step 2/7] Initialize project...
^C
Setup interrupted by user.
```
**PASS**: Clean exit, cursor visible, no traceback, terminal restored

### Test 2: heidi auth device polling
```bash
heidi auth gh
Opening browser for GitHub authorization...
Waiting for authorization... (Press Ctrl+C to cancel)
^C
Authentication cancelled by user.
```
**PASS**: Clean exit, cursor visible, no traceback, terminal restored

### Test 3: heidi chat thinking status
```bash
heidi chat
> hello
Copilot is thinking...
^C
Chat session ended.
```
**PASS**: Clean exit, cursor visible, no traceback, terminal restored

All manual Ctrl+C tests PASS as defined - terminal returns to normal state with visible cursor and clean prompt, no traceback unless --debug is used.
