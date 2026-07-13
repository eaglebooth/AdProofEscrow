import { createClient } from "genlayer-js";
import { localnet, studionet } from "genlayer-js/chains";
import { ExecutionResult, TransactionStatus } from "genlayer-js/types";

type NetworkName = "localnet" | "studionet";
declare global { interface Window { ethereum?: { request: (args: { method: string; params?: unknown[] }) => Promise<unknown> } } }
const network: NetworkName = process.env.NEXT_PUBLIC_NETWORK === "localnet" ? "localnet" : "studionet";
const endpoint = process.env.NEXT_PUBLIC_GENLAYER_RPC;
const chainMap = { localnet, studionet };
const client = createClient({ chain: chainMap[network], ...(endpoint ? { endpoint } : {}) });

type RuntimeClient = {
  connect?: (networkName: NetworkName) => Promise<unknown>;
  readContract: (args: { address: unknown; functionName: string; args: unknown[] }) => Promise<unknown>;
  writeContract: (args: { address: unknown; functionName: string; args: unknown[]; value: bigint }) => Promise<string>;
  waitForTransactionReceipt: (args: { hash: `0x${string}`; status: string }) => Promise<{ statusName?: string; txExecutionResultName?: string; txDataDecoded?: unknown }>;
};
export type ContractResult = { success: boolean; data?: unknown; hash?: string; status?: string; error?: string };
const contract = (value?: string) => value || process.env.NEXT_PUBLIC_CONTRACT_ADDRESS || "";

export async function readContract(functionName: string, args: unknown[] = [], contractAddress?: string): Promise<ContractResult> {
  try {
    const address = contract(contractAddress);
    if (!address) return { success: false, error: "AdProofEscrow V2 contract is not configured" };
    const data = await (client as unknown as RuntimeClient).readContract({ address, functionName, args });
    return { success: true, data };
  } catch (error) { return { success: false, error: error instanceof Error ? error.message : "Read failed" }; }
}

export async function connectWallet(): Promise<ContractResult> {
  if (typeof window === "undefined" || !window.ethereum) return { success: false, error: "Wallet provider not found" };
  try {
    const accounts = await window.ethereum.request({ method: "eth_requestAccounts", params: [] }) as string[];
    return accounts[0] ? { success: true, data: accounts[0] } : { success: false, error: "No wallet account selected" };
  } catch (error) { return { success: false, error: error instanceof Error ? error.message : "Wallet connection failed" }; }
}

export async function writeContract(functionName: string, args: unknown[] = [], contractAddress?: string, value: bigint = BigInt(0)): Promise<ContractResult> {
  if (typeof window === "undefined" || !window.ethereum) return { success: false, error: "Wallet provider not found" };
  try {
    const address = contract(contractAddress);
    if (!address) return { success: false, error: "AdProofEscrow V2 contract is not configured" };
    const accounts = await window.ethereum.request({ method: "eth_requestAccounts", params: [] }) as string[];
    if (!accounts[0]) return { success: false, error: "No wallet account selected" };
    const writeClient = createClient({ chain: chainMap[network], ...(endpoint ? { endpoint } : {}), provider: window.ethereum, account: accounts[0] as `0x${string}` });
    const runtime = writeClient as unknown as RuntimeClient;
    if (runtime.connect) await runtime.connect(network);
    const hash = await runtime.writeContract({ address, functionName, args, value });
    const receipt = await runtime.waitForTransactionReceipt({ hash: hash as `0x${string}`, status: TransactionStatus.FINALIZED });
    if (receipt.txExecutionResultName !== ExecutionResult.FINISHED_WITH_RETURN) return { success: false, hash, status: receipt.statusName, error: `Contract execution failed: ${receipt.txExecutionResultName || "UNKNOWN"}` };
    return { success: true, hash, status: receipt.statusName, data: receipt.txDataDecoded };
  } catch (error) { return { success: false, error: error instanceof Error ? error.message : "Write failed" }; }
}
