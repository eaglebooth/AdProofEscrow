# v0.2.16
# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *
import typing
import json


class AdProofEscrow(gl.Contract):
    campaign_brands: TreeMap[u256, str]
    campaign_creators: TreeMap[u256, str]
    campaign_titles: TreeMap[u256, str]
    campaign_briefs: TreeMap[u256, str]
    campaign_required_hashtags: TreeMap[u256, str]
    campaign_forbidden_claims: TreeMap[u256, str]
    campaign_deadlines: TreeMap[u256, str]
    campaign_amounts: TreeMap[u256, u256]
    campaign_remaining: TreeMap[u256, u256]
    campaign_min_scores: TreeMap[u256, u256]
    campaign_statuses: TreeMap[u256, str]
    campaign_count: u256

    proof_campaign_ids: TreeMap[u256, u256]
    proof_creators: TreeMap[u256, str]
    proof_urls: TreeMap[u256, str]
    proof_notes: TreeMap[u256, str]
    proof_statuses: TreeMap[u256, str]
    proof_verdicts: TreeMap[u256, str]
    proof_scores: TreeMap[u256, u256]
    proof_payout_percentages: TreeMap[u256, u256]
    proof_reasons: TreeMap[u256, str]
    proof_count: u256

    payout_campaign_ids: DynArray[u256]
    payout_proof_ids: DynArray[u256]
    payout_recipients: DynArray[str]
    payout_amounts: DynArray[u256]
    payout_count: u256

    appeal_proof_ids: DynArray[u256]
    appeal_reasons: DynArray[str]
    appeal_count: u256

    def __init__(self):
        self.campaign_count = u256(0)
        self.proof_count = u256(0)
        self.payout_count = u256(0)
        self.appeal_count = u256(0)

    @gl.public.write
    def create_campaign(
        self,
        brand: str,
        creator: str,
        title: str,
        brief: str,
        reward_amount: u256,
        min_score: u256,
    ) -> typing.Any:
        if len(brand) == 0:
            return "EMPTY_BRAND"
        if len(creator) == 0:
            return "EMPTY_CREATOR"
        if len(title) == 0:
            return "EMPTY_TITLE"
        if len(brief) == 0:
            return "EMPTY_BRIEF"
        if reward_amount == u256(0):
            return "ZERO_REWARD"
        if min_score > u256(100):
            return "BAD_MIN_SCORE"

        campaign_id = self.campaign_count
        self.campaign_brands[campaign_id] = brand
        self.campaign_creators[campaign_id] = creator
        self.campaign_titles[campaign_id] = title
        self.campaign_briefs[campaign_id] = brief
        self.campaign_required_hashtags[campaign_id] = ""
        self.campaign_forbidden_claims[campaign_id] = ""
        self.campaign_deadlines[campaign_id] = ""
        self.campaign_amounts[campaign_id] = reward_amount
        self.campaign_remaining[campaign_id] = reward_amount
        self.campaign_min_scores[campaign_id] = min_score
        self.campaign_statuses[campaign_id] = "OPEN"
        self.campaign_count = campaign_id + u256(1)
        return campaign_id

    @gl.public.write
    def set_campaign_rules(
        self,
        campaign_id: u256,
        required_hashtags: str,
        forbidden_claims: str,
        deadline: str,
    ) -> typing.Any:
        if campaign_id >= self.campaign_count:
            return "CAMPAIGN_NOT_FOUND"
        if self.campaign_statuses[campaign_id] != "OPEN":
            return "CAMPAIGN_NOT_OPEN"

        self.campaign_required_hashtags[campaign_id] = required_hashtags
        self.campaign_forbidden_claims[campaign_id] = forbidden_claims
        self.campaign_deadlines[campaign_id] = deadline
        return "RULES_SET"

    @gl.public.write
    def submit_proof(
        self,
        campaign_id: u256,
        creator: str,
        proof_url: str,
        notes: str,
    ) -> typing.Any:
        if campaign_id >= self.campaign_count:
            return "CAMPAIGN_NOT_FOUND"
        if self.campaign_statuses[campaign_id] != "OPEN":
            return "CAMPAIGN_NOT_OPEN"
        if len(creator) == 0:
            return "EMPTY_CREATOR"
        if len(proof_url) == 0:
            return "EMPTY_PROOF_URL"
        if self.campaign_remaining[campaign_id] == u256(0):
            return "NO_ESCROW_REMAINING"

        proof_id = self.proof_count
        self.proof_campaign_ids[proof_id] = campaign_id
        self.proof_creators[proof_id] = creator
        self.proof_urls[proof_id] = proof_url
        self.proof_notes[proof_id] = notes
        self.proof_statuses[proof_id] = "PENDING"
        self.proof_verdicts[proof_id] = ""
        self.proof_scores[proof_id] = u256(0)
        self.proof_payout_percentages[proof_id] = u256(0)
        self.proof_reasons[proof_id] = "Proof submitted and waiting for GenLayer review."
        self.proof_count = proof_id + u256(1)
        return proof_id

    @gl.public.write
    def review_proof(self, proof_id: u256) -> typing.Any:
        if proof_id >= self.proof_count:
            return "PROOF_NOT_FOUND"
        if self.proof_statuses[proof_id] != "PENDING":
            return "ALREADY_REVIEWED"

        campaign_id = self.proof_campaign_ids[proof_id]
        if campaign_id >= self.campaign_count:
            return "CAMPAIGN_NOT_FOUND"
        if self.campaign_statuses[campaign_id] != "OPEN":
            return "CAMPAIGN_NOT_OPEN"

        brand = self.campaign_brands[campaign_id]
        creator = self.proof_creators[proof_id]
        title = self.campaign_titles[campaign_id]
        brief = self.campaign_briefs[campaign_id]
        hashtags = self.campaign_required_hashtags[campaign_id]
        forbidden = self.campaign_forbidden_claims[campaign_id]
        deadline = self.campaign_deadlines[campaign_id]
        min_score = self.campaign_min_scores[campaign_id]
        proof_url = self.proof_urls[proof_id]
        notes = self.proof_notes[proof_id]

        def run_review() -> str:
            proof_content = ""
            if len(proof_url) > 0:
                response = gl.nondet.web.get(proof_url)
                proof_content = response.body.decode("utf-8")
            if len(proof_content) > 4200:
                proof_content = proof_content[:4200]

            prompt = (
                "You are AdProof Escrow, a GenLayer on-chain adjudicator for influencer marketing escrow. "
                "Review whether the creator's public post or campaign page satisfies the brand brief. "
                "Score each category from 0 to 100: message_match, hashtag_compliance, brand_safety, "
                "quality_effort, deadline_confidence, and authenticity. "
                "Final score is the average of those six scores. "
                "Decision thresholds: RELEASE if final_score >= campaign_min_score and brand_safety >= 75; "
                "PARTIAL_RELEASE if final_score >= 55 and brand_safety >= 60; "
                "NEED_REVISION if final_score >= 45 or evidence is incomplete; "
                "REFUND if final_score < 45, brand_safety < 60, missing required disclosures, or spam/low-effort is clear. "
                "Payout percentage: RELEASE=100, PARTIAL_RELEASE=50, NEED_REVISION=0, REFUND=0. "
                "Check semantic compliance, not just whether JSON fields exist. "
                f"Brand: {brand}\n"
                f"Creator: {creator}\n"
                f"Campaign title: {title}\n"
                f"Campaign brief: {brief}\n"
                f"Required hashtags/disclosures: {hashtags}\n"
                f"Forbidden claims/brand-safety rules: {forbidden}\n"
                f"Deadline: {deadline}\n"
                f"Campaign min score: {min_score}\n"
                f"Creator notes: {notes}\n"
                f"Fetched public proof content: {proof_content}\n"
                "Respond with ONLY strict JSON, no markdown, no prose. "
                "Use this schema exactly: "
                "{{\"verdict\":\"RELEASE|PARTIAL_RELEASE|NEED_REVISION|REFUND\","
                "\"score\":0,\"payout_percentage\":0,\"reason\":\"short reason\","
                "\"message_match\":0,\"hashtag_compliance\":0,\"brand_safety\":0,"
                "\"quality_effort\":0,\"deadline_confidence\":0,\"authenticity\":0}}"
            )
            return gl.nondet.exec_prompt(prompt)

        result = gl.eq_principle.strict_eq(run_review)
        data = json.loads(result)
        verdict = str(data["verdict"])
        score = u256(int(data["score"]))
        payout_percentage = u256(int(data["payout_percentage"]))
        reason = str(data["reason"])

        if score > u256(100):
            return "BAD_SCORE"
        if payout_percentage > u256(100):
            return "BAD_PAYOUT_PERCENTAGE"

        if verdict == "RELEASE":
            if score < min_score:
                return "SCORE_BELOW_MIN"
            self.proof_statuses[proof_id] = "APPROVED_FULL"
        elif verdict == "PARTIAL_RELEASE":
            self.proof_statuses[proof_id] = "APPROVED_PARTIAL"
        elif verdict == "NEED_REVISION":
            self.proof_statuses[proof_id] = "NEEDS_REVISION"
        elif verdict == "REFUND":
            self.proof_statuses[proof_id] = "REFUND_BRAND"
        else:
            return "UNKNOWN_VERDICT"

        self.proof_verdicts[proof_id] = verdict
        self.proof_scores[proof_id] = score
        self.proof_payout_percentages[proof_id] = payout_percentage
        self.proof_reasons[proof_id] = reason
        return result

    @gl.public.write
    def release_payout(self, proof_id: u256) -> typing.Any:
        if proof_id >= self.proof_count:
            return "PROOF_NOT_FOUND"

        status = self.proof_statuses[proof_id]
        if status != "APPROVED_FULL" and status != "APPROVED_PARTIAL":
            return "NOT_APPROVED"

        campaign_id = self.proof_campaign_ids[proof_id]
        remaining = self.campaign_remaining[campaign_id]
        if remaining == u256(0):
            return "NO_ESCROW_REMAINING"

        payout_percentage = self.proof_payout_percentages[proof_id]
        if payout_percentage == u256(0):
            return "ZERO_PAYOUT"
        if payout_percentage > u256(100):
            return "BAD_PAYOUT_PERCENTAGE"

        amount = self.campaign_amounts[campaign_id] * payout_percentage // u256(100)
        if amount == u256(0):
            return "ZERO_AMOUNT"
        if amount > remaining:
            return "INSUFFICIENT_ESCROW"

        new_remaining = remaining - amount
        self.campaign_remaining[campaign_id] = new_remaining
        self.proof_statuses[proof_id] = "PAID"
        if new_remaining == u256(0):
            self.campaign_statuses[campaign_id] = "SETTLED"

        self.payout_campaign_ids.append(campaign_id)
        self.payout_proof_ids.append(proof_id)
        self.payout_recipients.append(self.proof_creators[proof_id])
        self.payout_amounts.append(amount)
        self.payout_count = self.payout_count + u256(1)
        return "PAID"

    @gl.public.write
    def refund_brand(self, campaign_id: u256) -> typing.Any:
        if campaign_id >= self.campaign_count:
            return "CAMPAIGN_NOT_FOUND"
        if self.campaign_statuses[campaign_id] == "SETTLED":
            return "ALREADY_SETTLED"
        if self.campaign_remaining[campaign_id] == u256(0):
            return "NO_ESCROW_REMAINING"

        amount = self.campaign_remaining[campaign_id]
        self.campaign_remaining[campaign_id] = u256(0)
        self.campaign_statuses[campaign_id] = "SETTLED"
        self.payout_campaign_ids.append(campaign_id)
        self.payout_proof_ids.append(u256(0))
        self.payout_recipients.append(self.campaign_brands[campaign_id])
        self.payout_amounts.append(amount)
        self.payout_count = self.payout_count + u256(1)
        return "REFUNDED"

    @gl.public.write
    def appeal_review(self, proof_id: u256, reason: str) -> typing.Any:
        if proof_id >= self.proof_count:
            return "PROOF_NOT_FOUND"
        status = self.proof_statuses[proof_id]
        if status != "NEEDS_REVISION" and status != "REFUND_BRAND":
            return "NOT_APPEALABLE"
        if len(reason) == 0:
            return "EMPTY_APPEAL_REASON"

        self.proof_statuses[proof_id] = "APPEALED"
        self.appeal_proof_ids.append(proof_id)
        self.appeal_reasons.append(reason)
        self.appeal_count = self.appeal_count + u256(1)
        return "APPEALED"

    @gl.public.view
    def get_campaign(self, campaign_id: u256) -> typing.Any:
        if campaign_id >= self.campaign_count:
            return "CAMPAIGN_NOT_FOUND"
        return json.dumps(
            {
                "campaign_id": int(campaign_id),
                "brand": self.campaign_brands[campaign_id],
                "creator": self.campaign_creators[campaign_id],
                "title": self.campaign_titles[campaign_id],
                "brief": self.campaign_briefs[campaign_id],
                "required_hashtags": self.campaign_required_hashtags[campaign_id],
                "forbidden_claims": self.campaign_forbidden_claims[campaign_id],
                "deadline": self.campaign_deadlines[campaign_id],
                "reward_amount": int(self.campaign_amounts[campaign_id]),
                "remaining": int(self.campaign_remaining[campaign_id]),
                "min_score": int(self.campaign_min_scores[campaign_id]),
                "status": self.campaign_statuses[campaign_id],
            },
            sort_keys=True,
            separators=(",", ":"),
        )

    @gl.public.view
    def get_proof(self, proof_id: u256) -> typing.Any:
        if proof_id >= self.proof_count:
            return "PROOF_NOT_FOUND"
        return json.dumps(
            {
                "proof_id": int(proof_id),
                "campaign_id": int(self.proof_campaign_ids[proof_id]),
                "creator": self.proof_creators[proof_id],
                "proof_url": self.proof_urls[proof_id],
                "notes": self.proof_notes[proof_id],
                "status": self.proof_statuses[proof_id],
                "verdict": self.proof_verdicts[proof_id],
                "score": int(self.proof_scores[proof_id]),
                "payout_percentage": int(self.proof_payout_percentages[proof_id]),
                "reason": self.proof_reasons[proof_id],
            },
            sort_keys=True,
            separators=(",", ":"),
        )

    @gl.public.view
    def get_campaign_count(self) -> u256:
        return self.campaign_count

    @gl.public.view
    def get_proof_count(self) -> u256:
        return self.proof_count

    @gl.public.view
    def get_payout_count(self) -> u256:
        return self.payout_count

    @gl.public.view
    def get_payout(self, payout_id: u256) -> typing.Any:
        if payout_id >= self.payout_count:
            return "PAYOUT_NOT_FOUND"
        return json.dumps(
            {
                "payout_id": int(payout_id),
                "campaign_id": int(self.payout_campaign_ids[payout_id]),
                "proof_id": int(self.payout_proof_ids[payout_id]),
                "recipient": self.payout_recipients[payout_id],
                "amount": int(self.payout_amounts[payout_id]),
            },
            sort_keys=True,
            separators=(",", ":"),
        )
