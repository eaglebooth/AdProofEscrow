"use client";

import { motion } from "framer-motion";
import {
  ArrowRight,
  BadgeCheck,
  Banknote,
  Check,
  ClipboardCheck,
  Gem,
  Hash,
  Loader2,
  Megaphone,
  Play,
  ShieldCheck,
  Sparkles,
  Target,
  Wallet,
} from "lucide-react";
import { useState, useEffect } from "react";
import { connectWallet, readContract, writeContract } from "@/lib/genlayer";

type Tone = "ok" | "warn" | "bad";

type LogEntry = {
  label: string;
  value: string;
  tone: Tone;
};

type ProofView = {
  campaignId: string;
  proofId: string;
  status: string;
  score: string;
  payout: string;
  reason: string;
};

const statusClass: Record<string, string> = {
  DRAFT: "border-white/15 bg-white/5 text-white/70",
  OPEN: "border-emerald-400/40 bg-emerald-400/10 text-emerald-200",
  PENDING: "border-cyan-300/35 bg-cyan-300/10 text-cyan-100",
  APPROVED_FULL: "border-emerald-300/50 bg-emerald-300/15 text-emerald-100",
  APPROVED_PARTIAL: "border-yellow-300/45 bg-yellow-300/12 text-yellow-100",
  NEEDS_REVISION: "border-yellow-300/45 bg-yellow-300/12 text-yellow-100",
  REFUND_BRAND: "border-red-300/45 bg-red-300/12 text-red-100",
  PAID: "border-emerald-300/70 bg-emerald-300 text-[#03140f]",
};

export default function Home() {
  const contractAddress = process.env.NEXT_PUBLIC_CONTRACT_ADDRESS || "";
  const networkName = process.env.NEXT_PUBLIC_NETWORK || "testnetAsimov";
  const contractConfigured = Boolean(contractAddress);
  const [wallet, setWallet] = useState("");
  const [busy, setBusy] = useState("");
  const [logs, setLogs] = useState<LogEntry[]>([
    {
      label: "Ready",
      value: contractConfigured
        ? `Contract ${contractAddress.slice(0, 6)}...${contractAddress.slice(-4)} on ${networkName}.`
        : "Demo mode active. Add NEXT_PUBLIC_CONTRACT_ADDRESS after Studio deploy.",
      tone: contractConfigured ? "ok" : "warn",
    },
  ]);
  const [proof, setProof] = useState<ProofView>({
    campaignId: "-",
    proofId: "-",
    status: "DRAFT",
    score: "0",
    payout: "0",
    reason: "Create a campaign escrow, submit a creator URL, then let GenLayer adjudicate delivery.",
  });

  const [campaignForm, setCampaignForm] = useState({
    brand: "NovaLabs",
    creator: "Mira Studio",
    title: "Launch reel for Nova Card",
    brief:
      "Create one public launch post explaining Nova Card benefits, include clear sponsorship disclosure, avoid guaranteed profit claims, and keep the tone premium but accessible.",
    reward: "1800",
    minScore: "84",
    hashtags: "#NovaCard #Sponsored #CreatorFinance",
    forbidden: "No guaranteed income claims, no fake testimonials, no misleading crypto yield language.",
    deadline: "2026-06-30",
  });

  const [proofForm, setProofForm] = useState({
    creator: "Mira Studio",
    proofUrl: "https://example.com/nova-card-launch-post",
    notes:
      "The campaign page includes the disclosure, all hashtags, and the requested product positioning.",
  });

  function pushLog(entry: LogEntry) {
    setLogs((current) => [entry, ...current].slice(0, 5));
  }

  async function syncState() {
    setBusy("sync");
    try {
      const [campaignCountRes, proofCountRes, payoutCountRes] = await Promise.all([
        readContract("get_campaign_count"),
        readContract("get_proof_count"),
        readContract("get_payout_count"),
      ]);

      if (!campaignCountRes.success || !proofCountRes.success || !payoutCountRes.success) {
        const err = campaignCountRes.error || proofCountRes.error || payoutCountRes.error || "RPC connection failed";
        pushLog({ label: "Sync failed", value: err, tone: "warn" });
        return;
      }

      const cCount = Number(campaignCountRes.data);
      const prCount = Number(proofCountRes.data);
      const pCount = Number(payoutCountRes.data);

      pushLog({
        label: "Sync success",
        value: `Connected to GenLayer. Found ${cCount} campaigns, ${prCount} creator proofs, ${pCount} payouts.`,
        tone: "ok",
      });
    } catch (error) {
      pushLog({
        label: "Sync error",
        value: error instanceof Error ? error.message : "Unknown error during sync",
        tone: "bad",
      });
    } finally {
      setBusy("");
    }
  }

  useEffect(() => {
    if (contractConfigured) {
      syncState();
    }
  }, []);

  async function handleWallet() {
    setBusy("wallet");
    const result = await connectWallet();
    if (result.success && typeof result.data === "string") {
      setWallet(result.data);
      pushLog({ label: "Wallet", value: result.data, tone: "ok" });
    } else {
      pushLog({ label: "Wallet", value: result.error || "No wallet provider found", tone: "warn" });
    }
    setBusy("");
  }

  async function createCampaign() {
    setBusy("campaign");
    if (!contractConfigured) {
      setProof((current) => ({
        ...current,
        campaignId: "0",
        status: "OPEN",
        reason: "Demo campaign escrow opened with 1,800 tokens locked for Mira Studio.",
      }));
      pushLog({ label: "Campaign", value: "Created demo campaign #0.", tone: "ok" });
      setBusy("");
      return;
    }

    const result = await writeContract("create_campaign", [
      campaignForm.brand,
      campaignForm.creator,
      campaignForm.title,
      campaignForm.brief,
      Number(campaignForm.reward || "0"),
      Number(campaignForm.minScore || "0"),
    ]);
    pushLog({
      label: "create_campaign",
      value: result.success ? `Finalized ${String(result.data ?? result.hash)}` : result.error || "Failed",
      tone: result.success ? "ok" : "bad",
    });
    if (result.success) {
      const campaignId =
        typeof result.data === "number" || typeof result.data === "string" ? String(result.data) : "0";
      setProof((current) => ({
        ...current,
        campaignId,
        status: "OPEN",
        reason: `Campaign #${campaignId} was created on GenLayer. Add rules, then submit proof.`,
      }));
    }
    setBusy("");
  }

  async function setRules() {
    setBusy("rules");
    if (!contractConfigured) {
      pushLog({ label: "Rules", value: "Demo rules set: hashtags, forbidden claims, deadline.", tone: "ok" });
      setBusy("");
      return;
    }

    const result = await writeContract("set_campaign_rules", [
      Number(proof.campaignId === "-" ? "0" : proof.campaignId),
      campaignForm.hashtags,
      campaignForm.forbidden,
      campaignForm.deadline,
    ]);
    pushLog({
      label: "set_campaign_rules",
      value: result.success ? `Finalized ${String(result.data ?? result.hash)}` : result.error || "Failed",
      tone: result.success ? "ok" : "bad",
    });
    setBusy("");
  }

  async function submitProof() {
    setBusy("proof");
    if (!contractConfigured) {
      setProof({
        campaignId: "0",
        proofId: "0",
        status: "PENDING",
        score: "0",
        payout: "0",
        reason: "Creator URL submitted. The escrow is ready for GenLayer review.",
      });
      pushLog({ label: "Proof", value: "Submitted demo creator post URL.", tone: "ok" });
      setBusy("");
      return;
    }

    const result = await writeContract("submit_proof", [
      Number(proof.campaignId === "-" ? "0" : proof.campaignId),
      proofForm.creator,
      proofForm.proofUrl,
      proofForm.notes,
    ]);
    pushLog({
      label: "submit_proof",
      value: result.success ? `Finalized ${String(result.data ?? result.hash)}` : result.error || "Failed",
      tone: result.success ? "ok" : "bad",
    });
    if (result.success) {
      const proofId =
        typeof result.data === "number" || typeof result.data === "string" ? String(result.data) : "0";
      setProof((current) => ({
        ...current,
        proofId,
        status: "PENDING",
        score: "0",
        payout: "0",
        reason: `Proof #${proofId} was submitted to the configured GenLayer contract.`,
      }));
    }
    setBusy("");
  }

  async function reviewProof() {
    setBusy("review");
    if (!contractConfigured) {
      await new Promise((resolve) => setTimeout(resolve, 700));
      setProof({
        campaignId: "0",
        proofId: "0",
        status: "APPROVED_FULL",
        score: "92",
        payout: "100",
        reason:
          "The post matches the brief, includes sponsor disclosure and hashtags, and avoids forbidden claims.",
      });
      pushLog({ label: "AI review", value: "RELEASE. Score 92, payout 100%.", tone: "ok" });
      setBusy("");
      return;
    }

    const proofId = Number(proof.proofId === "-" ? "0" : proof.proofId);
    const result = await writeContract("review_proof", [proofId]);
    pushLog({
      label: "review_proof",
      value: result.success ? `AI verdict ${String(result.data ?? result.hash)}` : result.error || "Failed",
      tone: result.success ? "ok" : "bad",
    });
    if (result.success) {
      const read = await readContract("get_proof", [proofId]);
      if (read.success && typeof read.data === "string") {
        const parsed = JSON.parse(read.data);
        setProof({
          campaignId: String(parsed.campaign_id || "0"),
          proofId: String(parsed.proof_id || "0"),
          status: String(parsed.status || "PENDING"),
          score: String(parsed.score || "0"),
          payout: String(parsed.payout_percentage || "0"),
          reason: String(parsed.reason || ""),
        });
      }
    }
    setBusy("");
  }

  async function releasePayout() {
    setBusy("payout");
    if (!contractConfigured) {
      const canPay = proof.status === "APPROVED_FULL" || proof.status === "APPROVED_PARTIAL";
      setProof((current) => ({
        ...current,
        status: canPay ? "PAID" : current.status,
        reason: canPay ? "Demo escrow released 1,800 tokens to Mira Studio." : "Proof must be approved first.",
      }));
      pushLog({ label: "Payout", value: canPay ? "Released demo payout." : "Blocked until approval.", tone: canPay ? "ok" : "warn" });
      setBusy("");
      return;
    }

    const result = await writeContract("release_payout", [Number(proof.proofId === "-" ? "0" : proof.proofId)]);
    pushLog({
      label: "release_payout",
      value: result.success ? `Finalized ${String(result.data ?? result.hash)}` : result.error || "Failed",
      tone: result.success ? "ok" : "bad",
    });
    if (result.success) {
      setProof((current) => ({ ...current, status: "PAID", reason: "Escrow payout was finalized on GenLayer." }));
    }
    setBusy("");
  }

  async function runDemo() {
    document.getElementById("console")?.scrollIntoView({ behavior: "smooth", block: "start" });
    if (!contractConfigured) {
      await createCampaign();
      await setRules();
      await submitProof();
      await reviewProof();
    } else {
      pushLog({
        label: "Live Mode",
        value: "Workspace active. Connect your wallet, then complete Step 1, 2, 3, and 4 below one by one.",
        tone: "ok",
      });
    }
  }

  return (
    <main className="grid-shell min-h-screen overflow-hidden">
      <header className="relative z-10 mx-auto flex max-w-7xl items-center justify-between px-5 py-6">
        <a href="#" className="flex items-center gap-3">
          <div className="grid size-8 place-items-center rounded-[9px] bg-[var(--emerald)] text-[#03140f]">
            <Megaphone size={19} />
          </div>
          <span className="text-xl font-semibold tracking-[-0.03em]">AdProof</span>
        </a>
        <nav className="hidden items-center gap-10 text-sm font-semibold text-[var(--muted)] md:flex">
          <a href="#console">Escrow</a>
          <a href="#review">Review</a>
          <a href="#benefits">Benefits</a>
          <a href="#timeline">Settlement</a>
        </nav>
        <button onClick={handleWallet} className="ghost-button flex h-11 items-center gap-2 rounded-full px-5 text-sm font-semibold">
          {busy === "wallet" ? <Loader2 className="animate-spin" size={16} /> : <Wallet size={16} />}
          {wallet ? `${wallet.slice(0, 6)}...${wallet.slice(-4)}` : "Connect"}
        </button>
      </header>

      <section className="relative mx-auto max-w-7xl px-5 pb-20 pt-20 text-center">
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
          <div className="pill mx-auto inline-flex items-center gap-3 rounded-full px-4 py-2">
            <div className="flex -space-x-2">
              {["N", "M", "K"].map((item) => (
                <span key={item} className="grid size-7 place-items-center rounded-full border border-[#124636] bg-[#d9fff0] text-xs font-bold text-[#063020]">
                  {item}
                </span>
              ))}
            </div>
            <span className="text-[var(--emerald)]">★★★★★</span>
            <span className="text-sm font-semibold">Creator campaigns settle with proof</span>
          </div>
          <h1 className="mx-auto mt-8 max-w-5xl text-5xl font-semibold leading-[1.03] tracking-[-0.06em] md:text-7xl">
            Turn creator delivery into a
            <br />
            <span className="text-[var(--emerald)]">proof-based</span> payout machine
          </h1>
          <p className="mx-auto mt-5 max-w-2xl text-lg leading-8 text-[var(--muted)]">
            AdProof Escrow lets brands lock campaign funds while a GenLayer Intelligent Contract reads public creator
            posts, checks brief compliance, and settles payout or refund.
          </p>
          <div className="mt-8 flex flex-wrap items-center justify-center gap-4">
            <button onClick={runDemo} disabled={Boolean(busy)} className="emerald-button flex h-12 items-center gap-2 rounded-full px-7 font-semibold disabled:opacity-60">
              {busy ? <Loader2 className="animate-spin" size={17} /> : <Sparkles size={17} />}
              Launch campaign audit
              <ArrowRight size={17} />
            </button>
            <a href="#console" className="ghost-button flex h-12 items-center gap-2 rounded-full px-7 font-semibold">
              Review creator proof
              <Play size={17} />
            </a>
          </div>
          <div className="mx-auto mt-8 flex max-w-3xl flex-wrap justify-center gap-7 text-sm font-semibold text-[var(--muted)]">
            <ProofPoint>Brief compliance</ProofPoint>
            <ProofPoint>Brand safety review</ProofPoint>
            <ProofPoint>Escrow payout guard</ProofPoint>
          </div>
        </motion.div>

        <div className="media-card panel mx-auto mt-16 h-[360px] max-w-5xl overflow-hidden rounded-[26px] border-2 border-emerald-300/20">
          <div className="flex h-full items-end justify-center bg-gradient-to-b from-transparent to-[#03140f]/82 p-7">
            <div className="grid size-16 place-items-center rounded-2xl bg-[var(--emerald)] text-[#03140f] shadow-[0_0_40px_var(--glow)]">
              <Play fill="currentColor" size={30} />
            </div>
          </div>
        </div>
      </section>

      <section id="console" className="mx-auto grid max-w-7xl gap-7 px-5 pb-24 lg:grid-cols-[0.95fr_1.05fr]">
        <div className="panel corner-box rounded-[28px] p-6">
          <div className="mb-6 flex items-start justify-between gap-4">
            <div>
              <div className="text-sm font-semibold text-[var(--emerald)]">Escrow console</div>
              <h2 className="mt-2 text-3xl font-semibold tracking-[-0.04em]">Campaign settlement</h2>
            </div>
            <span className={`rounded-full border px-3 py-1 text-xs font-bold ${statusClass[proof.status] || statusClass.DRAFT}`}>
              {proof.status}
            </span>
          </div>

          <div className="grid gap-4">
            <Panel title="1. Create campaign" icon={<Target size={18} />}>
              <div className="grid gap-3 md:grid-cols-2">
                <Field label="Brand" value={campaignForm.brand} onChange={(brand) => setCampaignForm({ ...campaignForm, brand })} />
                <Field label="Creator" value={campaignForm.creator} onChange={(creator) => setCampaignForm({ ...campaignForm, creator })} />
              </div>
              <Field label="Campaign title" value={campaignForm.title} onChange={(title) => setCampaignForm({ ...campaignForm, title })} />
              <Field label="Brief" value={campaignForm.brief} onChange={(brief) => setCampaignForm({ ...campaignForm, brief })} area />
              <div className="grid gap-3 md:grid-cols-2">
                <Field label="Reward" value={campaignForm.reward} onChange={(reward) => setCampaignForm({ ...campaignForm, reward })} />
                <Field label="Min score" value={campaignForm.minScore} onChange={(minScore) => setCampaignForm({ ...campaignForm, minScore })} />
              </div>
              <ActionButton busy={busy === "campaign"} onClick={createCampaign} icon={<ClipboardCheck size={17} />}>
                Create escrow
              </ActionButton>
            </Panel>

            <Panel title="2. Rules & proof" icon={<Hash size={18} />}>
              <Field label="Required hashtags / disclosure" value={campaignForm.hashtags} onChange={(hashtags) => setCampaignForm({ ...campaignForm, hashtags })} />
              <Field label="Forbidden claims" value={campaignForm.forbidden} onChange={(forbidden) => setCampaignForm({ ...campaignForm, forbidden })} area />
              <Field label="Deadline" value={campaignForm.deadline} onChange={(deadline) => setCampaignForm({ ...campaignForm, deadline })} />
              <ActionButton busy={busy === "rules"} onClick={setRules} icon={<ShieldCheck size={17} />}>
                Save rules
              </ActionButton>
              <div className="h-px bg-emerald-200/10" />
              <Field label="Creator proof URL" value={proofForm.proofUrl} onChange={(proofUrl) => setProofForm({ ...proofForm, proofUrl })} />
              <Field label="Creator notes" value={proofForm.notes} onChange={(notes) => setProofForm({ ...proofForm, notes })} area />
              <ActionButton busy={busy === "proof"} onClick={submitProof} icon={<BadgeCheck size={17} />}>
                Submit creator proof
              </ActionButton>
            </Panel>
          </div>
        </div>

        <div id="review" className="grid gap-7">
          <div className="panel corner-box rounded-[28px] p-6">
            <div className="mb-5 flex items-center justify-between">
              <div>
                <div className="text-sm font-semibold text-[var(--emerald)]">GenLayer verdict</div>
                <h2 className="mt-2 text-3xl font-semibold tracking-[-0.04em]">AI review state</h2>
              </div>
              <Gem className="text-[var(--emerald)]" size={34} />
            </div>
            <div className="grid gap-4 md:grid-cols-3">
              <Metric label="Campaign" value={`#${proof.campaignId}`} />
              <Metric label="Score" value={proof.score} />
              <Metric label="Payout %" value={proof.payout} />
            </div>
            <p className="mt-5 rounded-[18px] border border-emerald-200/10 bg-black/20 p-4 text-sm leading-6 text-[var(--muted)]">
              {proof.reason}
            </p>
            <div className="mt-5 grid gap-3 md:grid-cols-2">
              <ActionButton busy={busy === "review"} onClick={reviewProof} icon={<ShieldCheck size={17} />}>
                AI review proof
              </ActionButton>
              <ActionButton busy={busy === "payout"} onClick={releasePayout} icon={<Banknote size={17} />}>
                Release payout
              </ActionButton>
            </div>
          </div>

          <div className="panel rounded-[28px] p-6">
            <div className="mb-4 flex items-center justify-between">
              <span className="text-sm font-semibold text-[var(--emerald)]">Contract telemetry</span>
              <button
                onClick={syncState}
                disabled={Boolean(busy)}
                className="inline-flex h-8 items-center justify-center gap-1.5 rounded-full border border-emerald-500/20 bg-emerald-500/5 hover:bg-emerald-500/10 px-3 text-[10px] font-bold uppercase tracking-wider text-[var(--emerald)] transition-all disabled:opacity-50"
              >
                <Loader2 size={10} className={busy === "sync" ? "animate-spin" : ""} />
                {busy === "sync" ? "Syncing..." : "Sync Contract"}
              </button>
            </div>
            <div className="grid gap-2">
              {logs.map((entry) => (
                <div key={`${entry.label}-${entry.value}`} className={`rounded-[16px] border px-4 py-3 text-sm ${logClass(entry.tone)}`}>
                  <span className="font-bold">{entry.label}:</span>{" "}
                  <span className="text-white/68">{entry.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section id="benefits" className="mx-auto max-w-7xl px-5 pb-24 text-center">
        <div className="pill mx-auto inline-flex rounded-full px-4 py-2 text-sm font-semibold text-[var(--emerald)]">
          Allbound escrow
        </div>
        <h2 className="mt-6 text-5xl font-semibold tracking-[-0.055em]">The creator, campaign revolution</h2>
        <p className="mx-auto mt-4 max-w-2xl text-lg leading-8 text-[var(--muted)]">
          Transform subjective creator delivery into a transparent contract flow that brands and creators can both trust.
        </p>
        <div className="mt-14 grid gap-8 md:grid-cols-3">
          <Feature icon={<Target />} title="Align the brief" points={["Message match", "Disclosure check", "Hashtag proof"]}>
            The brand defines exact deliverables, forbidden claims, quality bar, and deadline before funds move.
          </Feature>
          <Feature icon={<ShieldCheck />} title="Review public proof" points={["Web evidence", "Brand safety", "Low-effort detection"]}>
            GenLayer reads the creator URL and asks AI validators to judge semantic delivery, not only formatting.
          </Feature>
          <Feature icon={<Banknote />} title="Settle fairly" points={["Full payout", "Partial payout", "Refund path"]}>
            The contract stores a verdict and only releases escrow when the proof clears the campaign rules.
          </Feature>
        </div>
      </section>

      <section id="timeline" className="mx-auto max-w-7xl px-5 pb-28">
        <div className="text-center">
          <div className="pill mx-auto inline-flex rounded-full px-4 py-2 text-sm font-semibold text-[var(--emerald)]">
            Settlement path
          </div>
          <h2 className="mt-6 text-5xl font-semibold tracking-[-0.055em]">Why AdProof works better</h2>
        </div>
        <div className="mx-auto mt-16 grid max-w-4xl grid-cols-[1fr_2px_1fr] gap-8">
          <TimelineSide align="right" icon={<Gem />} title="Higher deliverable quality">
            Creators know the brief is evaluated against public proof, not private preference.
          </TimelineSide>
          <div className="relative bg-gradient-to-b from-[var(--emerald)] via-white/70 to-white/20">
            <span className="absolute left-1/2 top-0 size-3 -translate-x-1/2 rounded-full bg-[var(--emerald)]" />
            <span className="absolute left-1/2 top-1/2 size-3 -translate-x-1/2 rounded-full bg-[var(--emerald)]" />
          </div>
          <TimelineSide icon={<Sparkles />} title="Faster payment cycles">
            Brands and creators settle with a repeatable on-chain decision instead of manual back-and-forth.
          </TimelineSide>
        </div>
      </section>
    </main>
  );
}

function ProofPoint({ children }: { children: React.ReactNode }) {
  return (
    <span className="flex items-center gap-2">
      <span className="grid size-5 place-items-center rounded-full bg-[var(--emerald)] text-[#03140f]">
        <Check size={13} />
      </span>
      {children}
    </span>
  );
}

function Panel({ title, icon, children }: { title: string; icon: React.ReactNode; children: React.ReactNode }) {
  return (
    <div className="rounded-[22px] border border-emerald-200/10 bg-black/20 p-4">
      <div className="mb-4 flex items-center gap-3 font-semibold">
        <span className="grid size-9 place-items-center rounded-[10px] border border-emerald-300/20 bg-emerald-300/10 text-[var(--emerald)]">
          {icon}
        </span>
        {title}
      </div>
      <div className="grid gap-3">{children}</div>
    </div>
  );
}

function Field({
  label,
  value,
  onChange,
  area = false,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  area?: boolean;
}) {
  const className = "field rounded-[14px] px-3 py-2.5 text-sm";
  return (
    <label className="grid gap-1.5">
      <span className="text-xs font-semibold text-[var(--dim)]">{label}</span>
      {area ? (
        <textarea className={`${className} min-h-24 resize-none`} value={value} onChange={(event) => onChange(event.target.value)} />
      ) : (
        <input className={className} value={value} onChange={(event) => onChange(event.target.value)} />
      )}
    </label>
  );
}

function ActionButton({
  children,
  icon,
  busy,
  onClick,
}: {
  children: React.ReactNode;
  icon: React.ReactNode;
  busy: boolean;
  onClick: () => void;
}) {
  return (
    <button onClick={onClick} disabled={busy} className="ghost-button flex h-11 items-center justify-center gap-2 rounded-[14px] px-4 text-sm font-bold disabled:opacity-55">
      {busy ? <Loader2 className="animate-spin" size={17} /> : icon}
      {children}
    </button>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[18px] border border-emerald-200/10 bg-black/20 p-4">
      <div className="text-xs font-semibold uppercase tracking-[0.14em] text-[var(--dim)]">{label}</div>
      <div className="mt-2 text-3xl font-semibold tracking-[-0.04em]">{value}</div>
    </div>
  );
}

function Feature({
  icon,
  title,
  children,
  points,
}: {
  icon: React.ReactNode;
  title: string;
  children: React.ReactNode;
  points: string[];
}) {
  return (
    <div className="panel corner-box rounded-[24px] p-7 text-left">
      <div className="grid size-12 place-items-center rounded-[12px] border border-emerald-300/20 bg-emerald-300/10 text-[var(--emerald)]">
        {icon}
      </div>
      <h3 className="mt-8 text-2xl font-semibold tracking-[-0.04em]">{title}</h3>
      <p className="mt-4 min-h-20 text-base leading-7 text-[var(--muted)]">{children}</p>
      <div className="my-6 h-px bg-emerald-200/10" />
      <div className="grid gap-3 text-sm font-semibold text-[var(--muted)]">
        {points.map((point) => (
          <ProofPoint key={point}>{point}</ProofPoint>
        ))}
      </div>
    </div>
  );
}

function TimelineSide({
  align,
  icon,
  title,
  children,
}: {
  align?: "right";
  icon: React.ReactNode;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className={`${align === "right" ? "text-right" : "text-left"} pt-8`}>
      <div className={`mb-8 inline-grid size-14 place-items-center rounded-full bg-emerald-300/10 text-[var(--emerald)] ${align === "right" ? "ml-auto" : ""}`}>
        {icon}
      </div>
      <h3 className="text-2xl font-semibold tracking-[-0.04em]">{title}</h3>
      <p className="mt-4 text-base leading-7 text-[var(--muted)]">{children}</p>
    </div>
  );
}

function logClass(tone: Tone) {
  if (tone === "ok") {
    return "border-emerald-300/20 bg-emerald-300/10 text-emerald-100";
  }
  if (tone === "bad") {
    return "border-red-300/20 bg-red-300/10 text-red-100";
  }
  return "border-yellow-300/20 bg-yellow-300/10 text-yellow-100";
}
