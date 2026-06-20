$logPath = "D:\Genlayer\AdProofEscrow\frontend\dev-server.log"
"Starting AdProof Escrow dev server at $(Get-Date -Format o)" | Set-Content -LiteralPath $logPath
Set-Location -LiteralPath "D:\Genlayer\AdProofEscrow\frontend"
& "C:\Program Files\nodejs\npm.cmd" run dev -- -p 3033 *>&1 | Tee-Object -FilePath $logPath -Append
