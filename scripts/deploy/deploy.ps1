Set-Location -LiteralPath "$PSScriptRoot\..\.."
python -m unittest discover -s tests
python -c "import ast; ast.parse(open('contracts/AdProofEscrow.py', encoding='utf-8').read())"
genlayer lint contracts/AdProofEscrow.py
genlayer deploy contracts/AdProofEscrow.py --name AdProofEscrow
