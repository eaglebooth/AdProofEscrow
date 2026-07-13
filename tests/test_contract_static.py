import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "contracts" / "AdProofEscrow.py").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)


class AdProofEscrowV2Tests(unittest.TestCase):
    def test_runtime_header(self):
        lines = SOURCE.splitlines()
        self.assertEqual(lines[0], "# v0.2.16")
        self.assertEqual(lines[1], '# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }')
        self.assertEqual(lines[2], "from genlayer import *")

    def test_real_payable_escrow_and_transfers(self):
        self.assertIn("@gl.public.write.payable\n    def create_campaign", SOURCE)
        self.assertIn("reward = gl.message.value", SOURCE)
        self.assertGreaterEqual(SOURCE.count("emit_transfer(value=amount)"), 2)

    def test_sender_authorization(self):
        self.assertIn("NOT_CAMPAIGN_BRAND", SOURCE)
        self.assertIn("NOT_CAMPAIGN_CREATOR", SOURCE)
        self.assertIn("gl.message.sender_address.as_hex", SOURCE)

    def test_semantic_consensus_not_strict_equality(self):
        self.assertIn("gl.eq_principle.prompt_comparative", SOURCE)
        self.assertNotIn("gl.eq_principle.strict_eq", SOURCE)

    def test_current_web_api(self):
        self.assertIn("gl.nondet.web.render", SOURCE)
        self.assertNotIn("gl.nondet.web.get", SOURCE)

    def test_complete_lifecycle_methods(self):
        for method in ["create_campaign", "set_campaign_rules", "submit_proof", "review_proof", "revise_proof", "open_appeal", "resolve_appeal", "accept_rejection", "release_payout", "refund_brand"]:
            self.assertIn(f"def {method}", SOURCE)

    def test_contract_computes_payout_percentage(self):
        self.assertIn('self.proof_payout_percentages[proof_id] = u256(100)', SOURCE)
        self.assertIn('self.proof_payout_percentages[proof_id] = u256(50)', SOURCE)
        self.assertNotIn('data.get("payout_percentage"', SOURCE)

    def test_storage_annotations_are_supported(self):
        contract = next(node for node in TREE.body if isinstance(node, ast.ClassDef) and node.name == "AdProofEscrow")
        allowed = {"TreeMap[u256, str]", "TreeMap[u256, u256]", "u256"}
        for statement in contract.body:
            if isinstance(statement, ast.AnnAssign):
                self.assertIn(ast.unparse(statement.annotation), allowed)

    def test_no_demo_or_script_entrypoint(self):
        self.assertNotIn("Demo", SOURCE)
        self.assertNotIn('__name__ == "__main__"', SOURCE)


if __name__ == "__main__":
    unittest.main()
