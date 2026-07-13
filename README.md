# AdProofEscrow V2

Funded creator campaigns settled by public proof and semantic GenLayer consensus.

**Pitch:** AdProofEscrow cannot operate without GenLayer because its core product is a shared on-chain judgment about whether a public creator deliverable satisfied a locked brand brief before real escrow funds move.

## V2 Lifecycle

1. The brand calls payable `create_campaign` and locks the complete GEN reward while assigning one creator wallet.
2. The brand locks disclosures, forbidden claims, deadline, and minimum full-release score.
3. Only the assigned creator can submit the public proof URL.
4. Validators read the URL with `gl.nondet.web.render` and use `prompt_comparative` to agree on `RELEASE`, `PARTIAL_RELEASE`, `NEED_REVISION`, or `REFUND`.
5. Fixable work can be revised twice. A rejected proof retains one evidence-backed appeal.
6. The contract computes the payout percentage from the verdict: 100% or 50%. The frontend and LLM cannot choose an arbitrary amount.
7. Creator payout and brand refund execute real value transfers and are recorded in the settlement registry.

## Safety Properties

- Payable escrow custody instead of a simulated reward ledger.
- Brand and creator roles bound to transaction sender identity.
- Campaign rules immutable before proof submission.
- One proof per campaign, bounded revisions, and one appeal.
- Semantic equivalence checks the fund-controlling outcome while allowing harmless reason wording differences.
- Original proof remains immutable when a revision is submitted.
- Brand cannot refund while creator review or appeal rights remain open.
- Deterministic JSON views for system, campaign, proof, and settlement state.

## Frontend

The Next.js interface uses `genlayer-js` on Studionet and has separate pages for each contract action:

- Campaign registry, funding, rules, detail, and eligible refund
- Proof registry, submission, review, revision, appeal, appeal resolution, rejection acceptance, and payout
- Settlement ledger and full How it works guide

There is no demo verdict or static fallback. The frontend is connected to the deployed V2 contract on Studionet.

## Verify Locally

```powershell
python -m unittest discover -s tests
python -c "import ast; ast.parse(open('contracts/AdProofEscrow.py', encoding='utf-8').read())"
cd frontend
npm install
npm run lint
npm run build
```

After V2 deployment, set the same address in `.env.local`, `.env.example`, and `.env.production`:

```text
NEXT_PUBLIC_CONTRACT_ADDRESS=0x8A5cD60b41259137b6aaF2C8Bc847c6a7e81C7Ef
NEXT_PUBLIC_NETWORK=studionet
NEXT_PUBLIC_GENLAYER_RPC=
```

V2 contract: `0x8A5cD60b41259137b6aaF2C8Bc847c6a7e81C7Ef`
