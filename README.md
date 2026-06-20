# AdProof Escrow

AI-reviewed creator campaign escrow on GenLayer.

One-line pitch: AdProof Escrow dies without GenLayer because its core product is an on-chain judgment about whether a creator's public campaign post truly satisfied a brand brief before escrow funds are released.

## Submission Links

- Live app: https://adproof-escrow.vercel.app
- GitHub repo: https://github.com/eaglebooth/AdProofEscrow
- GenLayer Studio contract: `0x3CD68598436dFa32D71dEE3DB966b99DeFfBc668`

## Why GenLayer

Influencer marketing payouts often turn into subjective disputes: did the creator follow the brief, include required hashtags and disclosures, avoid forbidden claims, keep the content brand-safe, and deliver enough quality to deserve full payment?

AdProof Escrow puts that adjudication into a GenLayer Intelligent Contract:

- A brand creates a campaign escrow with a reward amount, creator, brief, and minimum score.
- The brand adds campaign rules: required hashtags/disclosures, forbidden claims, and deadline.
- The creator submits a public post or campaign page URL.
- The contract reads the public URL through `gl.nondet.web.get`.
- An AI prompt scores message match, hashtag compliance, brand safety, quality, timing, and authenticity.
- `gl.eq_principle.strict_eq` wraps the nondeterministic review.
- The contract stores a deterministic verdict: `RELEASE`, `PARTIAL_RELEASE`, `NEED_REVISION`, or `REFUND`.
- Escrow only releases payout after an approved verdict.

## Project Structure

```text
AdProofEscrow/
  contracts/AdProofEscrow.py
  frontend/
  tests/test_contract_static.py
  scripts/deploy/deploy.ps1
  docs/design-guidelines/aurivus-extracted-design.md
```

## Builder Program Score Path

| Axis | Target | Evidence |
|---|---:|---|
| GenLayer fit | 5 | Core escrow settlement depends on subjective AI review of web evidence. |
| Contract quality | 4-5 | Guarded campaign lifecycle, semantic verdicts, partial payout/refund path, explicit error codes. |
| Engineering | 4 | Separate contract, frontend, tests, deploy script, README, design documentation. |
| Frontend / UX | 4 | Full flow for campaign creation, rule setup, proof submission, AI review, and payout release. |

## Pre-Deploy Verification

```powershell
python -m unittest discover -s tests
python -c "import ast; ast.parse(open('contracts/AdProofEscrow.py', encoding='utf-8').read())"
genlayer lint contracts/AdProofEscrow.py
```

## Deploy Contract

```powershell
genlayer deploy contracts/AdProofEscrow.py --name AdProofEscrow
```

After deploy, set:

```text
NEXT_PUBLIC_CONTRACT_ADDRESS=<deployed address>
NEXT_PUBLIC_NETWORK=testnetAsimov
NEXT_PUBLIC_GENLAYER_RPC=
```

## Frontend

```powershell
cd frontend
npm install
npm run dev
```

The frontend is in English and follows the provided Aurivus-inspired direction: deep emerald grid, large centered hero, glowing CTAs, bordered dark panels, operational logs, and a settlement timeline.
