# v0.2.16
# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *
import typing
import json


@gl.evm.contract_interface
class _Recipient:
    class View:
        pass

    class Write:
        pass


class AdProofEscrow(gl.Contract):
    campaign_count: u256
    proof_count: u256
    settlement_count: u256
    total_locked: u256
    total_creator_paid: u256
    total_brand_refunded: u256

    campaign_brands: TreeMap[u256, str]
    campaign_creators: TreeMap[u256, str]
    campaign_titles: TreeMap[u256, str]
    campaign_briefs: TreeMap[u256, str]
    campaign_required_hashtags: TreeMap[u256, str]
    campaign_forbidden_claims: TreeMap[u256, str]
    campaign_deadlines: TreeMap[u256, str]
    campaign_rewards: TreeMap[u256, u256]
    campaign_remaining: TreeMap[u256, u256]
    campaign_min_scores: TreeMap[u256, u256]
    campaign_statuses: TreeMap[u256, str]
    campaign_has_proof: TreeMap[u256, u256]
    campaign_proof_ids: TreeMap[u256, u256]

    proof_campaign_ids: TreeMap[u256, u256]
    proof_original_urls: TreeMap[u256, str]
    proof_current_urls: TreeMap[u256, str]
    proof_appeal_urls: TreeMap[u256, str]
    proof_notes: TreeMap[u256, str]
    proof_statuses: TreeMap[u256, str]
    proof_verdicts: TreeMap[u256, str]
    proof_scores: TreeMap[u256, u256]
    proof_payout_percentages: TreeMap[u256, u256]
    proof_reasons: TreeMap[u256, str]
    proof_review_counts: TreeMap[u256, u256]
    proof_revision_counts: TreeMap[u256, u256]
    proof_appealed: TreeMap[u256, u256]

    settlement_kinds: TreeMap[u256, str]
    settlement_campaign_ids: TreeMap[u256, u256]
    settlement_proof_ids: TreeMap[u256, u256]
    settlement_recipients: TreeMap[u256, str]
    settlement_amounts: TreeMap[u256, u256]

    def __init__(self):
        self.campaign_count = u256(0)
        self.proof_count = u256(0)
        self.settlement_count = u256(0)
        self.total_locked = u256(0)
        self.total_creator_paid = u256(0)
        self.total_brand_refunded = u256(0)

    def _valid_url(self, value: str) -> bool:
        return value.startswith("https://") and len(value) <= 500

    def _parse_review(self, raw: str) -> typing.Any:
        try:
            data = json.loads(raw)
            verdict = str(data.get("verdict", "NEED_REVISION")).upper()
            score = int(data.get("score", 0))
            reason = str(data.get("reason", "The jury returned no usable reason."))[:900]
        except Exception:
            return None
        if verdict not in ("RELEASE", "PARTIAL_RELEASE", "NEED_REVISION", "REFUND"):
            verdict = "NEED_REVISION"
        if score < 0:
            score = 0
        if score > 100:
            score = 100
        return (verdict, score, reason)

    @gl.public.write.payable
    def create_campaign(self, creator: str, title: str, brief: str, min_score: u256) -> typing.Any:
        creator_address = Address(creator).as_hex
        if creator_address == gl.message.sender_address.as_hex:
            return "BRAND_AND_CREATOR_MUST_DIFFER"
        if len(title) == 0 or len(title) > 120:
            return "INVALID_TITLE"
        if len(brief) == 0 or len(brief) > 1200:
            return "INVALID_BRIEF"
        if min_score < u256(50) or min_score > u256(100):
            return "INVALID_MIN_SCORE"
        reward = gl.message.value
        if reward == u256(0):
            return "ESCROW_VALUE_REQUIRED"

        campaign_id = self.campaign_count
        self.campaign_brands[campaign_id] = gl.message.sender_address.as_hex
        self.campaign_creators[campaign_id] = creator_address
        self.campaign_titles[campaign_id] = title
        self.campaign_briefs[campaign_id] = brief
        self.campaign_required_hashtags[campaign_id] = ""
        self.campaign_forbidden_claims[campaign_id] = ""
        self.campaign_deadlines[campaign_id] = ""
        self.campaign_rewards[campaign_id] = reward
        self.campaign_remaining[campaign_id] = reward
        self.campaign_min_scores[campaign_id] = min_score
        self.campaign_statuses[campaign_id] = "DRAFT"
        self.campaign_has_proof[campaign_id] = u256(0)
        self.campaign_proof_ids[campaign_id] = u256(0)
        self.campaign_count = campaign_id + u256(1)
        self.total_locked = self.total_locked + reward
        return str(campaign_id)

    @gl.public.write
    def set_campaign_rules(self, campaign_id: u256, required_hashtags: str, forbidden_claims: str, deadline: str) -> typing.Any:
        if campaign_id >= self.campaign_count:
            return "CAMPAIGN_NOT_FOUND"
        if self.campaign_brands[campaign_id] != gl.message.sender_address.as_hex:
            return "NOT_CAMPAIGN_BRAND"
        if self.campaign_statuses[campaign_id] != "DRAFT":
            return "RULES_ALREADY_LOCKED"
        if len(required_hashtags) == 0 or len(required_hashtags) > 400:
            return "INVALID_REQUIRED_HASHTAGS"
        if len(forbidden_claims) == 0 or len(forbidden_claims) > 600:
            return "INVALID_FORBIDDEN_CLAIMS"
        if len(deadline) == 0 or len(deadline) > 80:
            return "INVALID_DEADLINE"
        self.campaign_required_hashtags[campaign_id] = required_hashtags
        self.campaign_forbidden_claims[campaign_id] = forbidden_claims
        self.campaign_deadlines[campaign_id] = deadline
        self.campaign_statuses[campaign_id] = "OPEN"
        return "RULES_LOCKED"

    @gl.public.write
    def submit_proof(self, campaign_id: u256, proof_url: str, notes: str) -> typing.Any:
        if campaign_id >= self.campaign_count:
            return "CAMPAIGN_NOT_FOUND"
        if self.campaign_creators[campaign_id] != gl.message.sender_address.as_hex:
            return "NOT_CAMPAIGN_CREATOR"
        if self.campaign_statuses[campaign_id] != "OPEN":
            return "CAMPAIGN_NOT_OPEN"
        if self.campaign_has_proof[campaign_id] != u256(0):
            return "PROOF_ALREADY_SUBMITTED"
        if not self._valid_url(proof_url):
            return "INVALID_PROOF_URL"
        if len(notes) > 800:
            return "NOTES_TOO_LONG"

        proof_id = self.proof_count
        self.proof_campaign_ids[proof_id] = campaign_id
        self.proof_original_urls[proof_id] = proof_url
        self.proof_current_urls[proof_id] = proof_url
        self.proof_appeal_urls[proof_id] = ""
        self.proof_notes[proof_id] = notes
        self.proof_statuses[proof_id] = "PENDING"
        self.proof_verdicts[proof_id] = "PENDING"
        self.proof_scores[proof_id] = u256(0)
        self.proof_payout_percentages[proof_id] = u256(0)
        self.proof_reasons[proof_id] = "Waiting for GenLayer review."
        self.proof_review_counts[proof_id] = u256(0)
        self.proof_revision_counts[proof_id] = u256(0)
        self.proof_appealed[proof_id] = u256(0)
        self.proof_count = proof_id + u256(1)
        self.campaign_has_proof[campaign_id] = u256(1)
        self.campaign_proof_ids[campaign_id] = proof_id
        self.campaign_statuses[campaign_id] = "PROOF_PENDING"
        return str(proof_id)

    @gl.public.write
    def review_proof(self, proof_id: u256) -> typing.Any:
        if proof_id >= self.proof_count:
            return "PROOF_NOT_FOUND"
        status = self.proof_statuses[proof_id]
        if status != "PENDING" and status != "REVISION_PENDING":
            return "PROOF_NOT_REVIEWABLE"
        campaign_id = self.proof_campaign_ids[proof_id]
        proof_url = self.proof_current_urls[proof_id]
        title = self.campaign_titles[campaign_id]
        brief = self.campaign_briefs[campaign_id]
        hashtags = self.campaign_required_hashtags[campaign_id]
        forbidden = self.campaign_forbidden_claims[campaign_id]
        deadline = self.campaign_deadlines[campaign_id]
        min_score = self.campaign_min_scores[campaign_id]
        notes = self.proof_notes[proof_id]

        def run_review() -> str:
            try:
                content = gl.nondet.web.render(proof_url, mode="html")[:4200]
            except Exception:
                return json.dumps({"verdict":"NEED_REVISION","score":0,"reason":"The public creator proof could not be read."}, sort_keys=True, separators=(",", ":"))
            prompt = f"""You are the impartial AdProofEscrow jury. A real GEN escrow settlement depends on this decision.
Campaign: {title}
Brand brief: {brief}
Required hashtags and disclosures: {hashtags}
Forbidden claims and safety rules: {forbidden}
Delivery deadline: {deadline}
Minimum full-release score: {min_score}
Creator notes: {notes}
PUBLIC CREATOR PROOF: {content}
Judge semantic delivery, disclosure compliance, brand safety, authentic effort, and whether the public evidence supports the claimed work. RELEASE only when the score meets the campaign minimum and no material safety or disclosure issue exists. PARTIAL_RELEASE for meaningful but incomplete delivery scoring at least 55. NEED_REVISION for fixable or unreadable evidence. REFUND for clear non-delivery, prohibited claims, manipulation, or a score below 45. Respond with ONLY JSON containing verdict RELEASE|PARTIAL_RELEASE|NEED_REVISION|REFUND, score 0-100, and one concise evidence-based reason."""
            return gl.nondet.exec_prompt(prompt)

        principle = "The escrow verdict must match because it controls real funds. Validators must agree on full release, partial release, revision, or refund and on a compatible score band. Reason wording may differ but must rely on compatible public evidence and campaign rules."
        parsed = self._parse_review(gl.eq_principle.prompt_comparative(run_review, principle))
        if parsed is None:
            return "INVALID_AI_RESPONSE"
        verdict, score_value, reason = parsed
        score = u256(score_value)
        if verdict == "RELEASE" and score < min_score:
            verdict = "PARTIAL_RELEASE" if score >= u256(55) else "NEED_REVISION"
        if verdict == "PARTIAL_RELEASE" and score < u256(55):
            verdict = "NEED_REVISION"

        self.proof_verdicts[proof_id] = verdict
        self.proof_scores[proof_id] = score
        self.proof_reasons[proof_id] = reason
        self.proof_review_counts[proof_id] = self.proof_review_counts[proof_id] + u256(1)
        if verdict == "RELEASE":
            self.proof_statuses[proof_id] = "APPROVED_FULL"
            self.proof_payout_percentages[proof_id] = u256(100)
            self.campaign_statuses[campaign_id] = "PAYOUT_READY"
        elif verdict == "PARTIAL_RELEASE":
            self.proof_statuses[proof_id] = "APPROVED_PARTIAL"
            self.proof_payout_percentages[proof_id] = u256(50)
            self.campaign_statuses[campaign_id] = "PAYOUT_READY"
        elif verdict == "NEED_REVISION":
            self.proof_statuses[proof_id] = "NEEDS_REVISION"
            self.proof_payout_percentages[proof_id] = u256(0)
            self.campaign_statuses[campaign_id] = "REVISION_REQUIRED"
        else:
            self.proof_statuses[proof_id] = "REJECTED"
            self.proof_payout_percentages[proof_id] = u256(0)
            self.campaign_statuses[campaign_id] = "REJECTED_APPEALABLE"
        return self.get_proof(proof_id)

    @gl.public.write
    def revise_proof(self, proof_id: u256, revised_url: str, notes: str) -> typing.Any:
        if proof_id >= self.proof_count:
            return "PROOF_NOT_FOUND"
        campaign_id = self.proof_campaign_ids[proof_id]
        if self.campaign_creators[campaign_id] != gl.message.sender_address.as_hex:
            return "NOT_CAMPAIGN_CREATOR"
        if self.proof_statuses[proof_id] != "NEEDS_REVISION":
            return "REVISION_NOT_REQUESTED"
        if self.proof_revision_counts[proof_id] >= u256(2):
            return "REVISION_LIMIT_REACHED"
        if not self._valid_url(revised_url):
            return "INVALID_REVISION_URL"
        if len(notes) > 800:
            return "NOTES_TOO_LONG"
        self.proof_current_urls[proof_id] = revised_url
        self.proof_notes[proof_id] = notes
        self.proof_revision_counts[proof_id] = self.proof_revision_counts[proof_id] + u256(1)
        self.proof_statuses[proof_id] = "REVISION_PENDING"
        self.campaign_statuses[campaign_id] = "PROOF_PENDING"
        return "REVISION_SUBMITTED"

    @gl.public.write
    def open_appeal(self, proof_id: u256, appeal_url: str) -> typing.Any:
        if proof_id >= self.proof_count:
            return "PROOF_NOT_FOUND"
        campaign_id = self.proof_campaign_ids[proof_id]
        if self.campaign_creators[campaign_id] != gl.message.sender_address.as_hex:
            return "NOT_CAMPAIGN_CREATOR"
        if self.proof_statuses[proof_id] != "REJECTED":
            return "PROOF_NOT_APPEALABLE"
        if self.proof_appealed[proof_id] != u256(0):
            return "APPEAL_ALREADY_USED"
        if not self._valid_url(appeal_url):
            return "INVALID_APPEAL_URL"
        self.proof_appeal_urls[proof_id] = appeal_url
        self.proof_appealed[proof_id] = u256(1)
        self.proof_statuses[proof_id] = "APPEAL_PENDING"
        self.campaign_statuses[campaign_id] = "APPEAL_PENDING"
        return "APPEAL_OPENED"

    @gl.public.write
    def resolve_appeal(self, proof_id: u256) -> typing.Any:
        if proof_id >= self.proof_count:
            return "PROOF_NOT_FOUND"
        if self.proof_statuses[proof_id] != "APPEAL_PENDING":
            return "APPEAL_NOT_PENDING"
        campaign_id = self.proof_campaign_ids[proof_id]
        original_url = self.proof_original_urls[proof_id]
        current_url = self.proof_current_urls[proof_id]
        appeal_url = self.proof_appeal_urls[proof_id]
        original_reason = self.proof_reasons[proof_id]
        brief = self.campaign_briefs[campaign_id]
        rules = self.campaign_required_hashtags[campaign_id] + " | " + self.campaign_forbidden_claims[campaign_id]
        min_score = self.campaign_min_scores[campaign_id]

        def run_appeal() -> str:
            try:
                original = gl.nondet.web.render(original_url, mode="html")[:2400]
                current = gl.nondet.web.render(current_url, mode="html")[:2400]
                appeal = gl.nondet.web.render(appeal_url, mode="html")[:2800]
            except Exception:
                return json.dumps({"verdict":"NEED_REVISION","score":0,"reason":"The complete appeal evidence could not be read."}, sort_keys=True, separators=(",", ":"))
            prompt = f"""You are the AdProofEscrow appeal jury. Review the complete record independently because real GEN is at stake.
Brief: {brief}
Rules: {rules}
Minimum full-release score: {min_score}
Original rejection: {original_reason}
ORIGINAL PROOF: {original}
CURRENT PROOF: {current}
NEW APPEAL EVIDENCE: {appeal}
Return RELEASE only for complete compliant delivery, PARTIAL_RELEASE for meaningful delivery scoring at least 55, NEED_REVISION only if a concrete fix remains possible, or REFUND when non-delivery or material violation remains proven. Respond ONLY with JSON containing verdict, score 0-100, and one concise reason."""
            return gl.nondet.exec_prompt(prompt)

        principle = "Appeal validators must agree on the same fund-controlling verdict and compatible score band after considering original, current, and new evidence. Wording may differ; the substantive evidence basis may not."
        parsed = self._parse_review(gl.eq_principle.prompt_comparative(run_appeal, principle))
        if parsed is None:
            return "INVALID_AI_RESPONSE"
        verdict, score_value, reason = parsed
        score = u256(score_value)
        if verdict == "RELEASE" and score < min_score:
            verdict = "PARTIAL_RELEASE" if score >= u256(55) else "REFUND"
        if verdict == "PARTIAL_RELEASE" and score < u256(55):
            verdict = "REFUND"
        self.proof_verdicts[proof_id] = verdict
        self.proof_scores[proof_id] = score
        self.proof_reasons[proof_id] = reason
        self.proof_review_counts[proof_id] = self.proof_review_counts[proof_id] + u256(1)
        if verdict == "RELEASE":
            self.proof_statuses[proof_id] = "APPROVED_FULL"
            self.proof_payout_percentages[proof_id] = u256(100)
            self.campaign_statuses[campaign_id] = "PAYOUT_READY"
        elif verdict == "PARTIAL_RELEASE":
            self.proof_statuses[proof_id] = "APPROVED_PARTIAL"
            self.proof_payout_percentages[proof_id] = u256(50)
            self.campaign_statuses[campaign_id] = "PAYOUT_READY"
        elif verdict == "NEED_REVISION":
            self.proof_statuses[proof_id] = "NEEDS_REVISION"
            self.proof_payout_percentages[proof_id] = u256(0)
            self.campaign_statuses[campaign_id] = "REVISION_REQUIRED"
        else:
            self.proof_statuses[proof_id] = "FINAL_REJECTED"
            self.proof_payout_percentages[proof_id] = u256(0)
            self.campaign_statuses[campaign_id] = "FINAL_REFUND"
        return self.get_proof(proof_id)

    @gl.public.write
    def accept_rejection(self, proof_id: u256) -> typing.Any:
        if proof_id >= self.proof_count:
            return "PROOF_NOT_FOUND"
        campaign_id = self.proof_campaign_ids[proof_id]
        if self.campaign_creators[campaign_id] != gl.message.sender_address.as_hex:
            return "NOT_CAMPAIGN_CREATOR"
        if self.proof_statuses[proof_id] != "REJECTED":
            return "REJECTION_NOT_OPEN"
        self.proof_statuses[proof_id] = "FINAL_REJECTED"
        self.campaign_statuses[campaign_id] = "FINAL_REFUND"
        return "REJECTION_ACCEPTED"

    @gl.public.write
    def release_payout(self, proof_id: u256) -> typing.Any:
        if proof_id >= self.proof_count:
            return "PROOF_NOT_FOUND"
        status = self.proof_statuses[proof_id]
        if status != "APPROVED_FULL" and status != "APPROVED_PARTIAL":
            return "PROOF_NOT_APPROVED"
        campaign_id = self.proof_campaign_ids[proof_id]
        remaining = self.campaign_remaining[campaign_id]
        percentage = self.proof_payout_percentages[proof_id]
        amount = self.campaign_rewards[campaign_id] * percentage // u256(100)
        if amount == u256(0) or amount > remaining:
            return "INSUFFICIENT_ESCROW"
        self.campaign_remaining[campaign_id] = remaining - amount
        self.total_locked = self.total_locked - amount
        self.total_creator_paid = self.total_creator_paid + amount
        self.proof_statuses[proof_id] = "PAID"
        self.campaign_statuses[campaign_id] = "SETTLED" if amount == remaining else "PARTIAL_PAID"
        settlement_id = self.settlement_count
        recipient = self.campaign_creators[campaign_id]
        self.settlement_kinds[settlement_id] = "CREATOR_PAYOUT"
        self.settlement_campaign_ids[settlement_id] = campaign_id
        self.settlement_proof_ids[settlement_id] = proof_id
        self.settlement_recipients[settlement_id] = recipient
        self.settlement_amounts[settlement_id] = amount
        self.settlement_count = settlement_id + u256(1)
        _Recipient(Address(recipient)).emit_transfer(value=amount)
        return str(settlement_id)

    @gl.public.write
    def refund_brand(self, campaign_id: u256) -> typing.Any:
        if campaign_id >= self.campaign_count:
            return "CAMPAIGN_NOT_FOUND"
        brand = self.campaign_brands[campaign_id]
        if brand != gl.message.sender_address.as_hex:
            return "NOT_CAMPAIGN_BRAND"
        status = self.campaign_statuses[campaign_id]
        if status != "DRAFT" and status != "OPEN" and status != "FINAL_REFUND" and status != "PARTIAL_PAID":
            return "REFUND_NOT_AVAILABLE"
        amount = self.campaign_remaining[campaign_id]
        if amount == u256(0):
            return "NO_ESCROW_REMAINING"
        self.campaign_remaining[campaign_id] = u256(0)
        self.campaign_statuses[campaign_id] = "SETTLED"
        self.total_locked = self.total_locked - amount
        self.total_brand_refunded = self.total_brand_refunded + amount
        settlement_id = self.settlement_count
        proof_id = self.campaign_proof_ids[campaign_id]
        self.settlement_kinds[settlement_id] = "BRAND_REFUND"
        self.settlement_campaign_ids[settlement_id] = campaign_id
        self.settlement_proof_ids[settlement_id] = proof_id
        self.settlement_recipients[settlement_id] = brand
        self.settlement_amounts[settlement_id] = amount
        self.settlement_count = settlement_id + u256(1)
        _Recipient(Address(brand)).emit_transfer(value=amount)
        return str(settlement_id)

    @gl.public.view
    def get_system_state(self) -> str:
        return json.dumps({"campaign_count":str(self.campaign_count),"proof_count":str(self.proof_count),"settlement_count":str(self.settlement_count),"total_brand_refunded":str(self.total_brand_refunded),"total_creator_paid":str(self.total_creator_paid),"total_locked":str(self.total_locked)}, sort_keys=True, separators=(",", ":"))

    @gl.public.view
    def get_campaign(self, campaign_id: u256) -> str:
        if campaign_id >= self.campaign_count:
            return json.dumps({"error":"CAMPAIGN_NOT_FOUND"}, sort_keys=True, separators=(",", ":"))
        return json.dumps({"brand":self.campaign_brands[campaign_id],"brief":self.campaign_briefs[campaign_id],"campaign_id":str(campaign_id),"creator":self.campaign_creators[campaign_id],"deadline":self.campaign_deadlines[campaign_id],"forbidden_claims":self.campaign_forbidden_claims[campaign_id],"has_proof":str(self.campaign_has_proof[campaign_id]),"min_score":str(self.campaign_min_scores[campaign_id]),"proof_id":str(self.campaign_proof_ids[campaign_id]),"remaining":str(self.campaign_remaining[campaign_id]),"required_hashtags":self.campaign_required_hashtags[campaign_id],"reward":str(self.campaign_rewards[campaign_id]),"status":self.campaign_statuses[campaign_id],"title":self.campaign_titles[campaign_id]}, sort_keys=True, separators=(",", ":"))

    @gl.public.view
    def get_proof(self, proof_id: u256) -> str:
        if proof_id >= self.proof_count:
            return json.dumps({"error":"PROOF_NOT_FOUND"}, sort_keys=True, separators=(",", ":"))
        return json.dumps({"appeal_url":self.proof_appeal_urls[proof_id],"appealed":str(self.proof_appealed[proof_id]),"campaign_id":str(self.proof_campaign_ids[proof_id]),"current_url":self.proof_current_urls[proof_id],"notes":self.proof_notes[proof_id],"original_url":self.proof_original_urls[proof_id],"payout_percentage":str(self.proof_payout_percentages[proof_id]),"proof_id":str(proof_id),"reason":self.proof_reasons[proof_id],"review_count":str(self.proof_review_counts[proof_id]),"revision_count":str(self.proof_revision_counts[proof_id]),"score":str(self.proof_scores[proof_id]),"status":self.proof_statuses[proof_id],"verdict":self.proof_verdicts[proof_id]}, sort_keys=True, separators=(",", ":"))

    @gl.public.view
    def get_settlement(self, settlement_id: u256) -> str:
        if settlement_id >= self.settlement_count:
            return json.dumps({"error":"SETTLEMENT_NOT_FOUND"}, sort_keys=True, separators=(",", ":"))
        return json.dumps({"amount":str(self.settlement_amounts[settlement_id]),"campaign_id":str(self.settlement_campaign_ids[settlement_id]),"kind":self.settlement_kinds[settlement_id],"proof_id":str(self.settlement_proof_ids[settlement_id]),"recipient":self.settlement_recipients[settlement_id],"settlement_id":str(settlement_id)}, sort_keys=True, separators=(",", ":"))
