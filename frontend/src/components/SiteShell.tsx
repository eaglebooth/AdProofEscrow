"use client";
import Link from "next/link";
import { ExternalLink, Menu, Megaphone, Wallet, X } from "lucide-react";
import { useState } from "react";
import { useWallet } from "./WalletProvider";
const nav=[["How it works","/how-it-works"],["Campaigns","/campaigns"],["Proofs","/proofs"],["Settlements","/settlements"]];
const short=(s:string)=>s?`${s.slice(0,6)}...${s.slice(-4)}`:"V2 pending";
export function SiteShell({children}:{children:React.ReactNode}){const[open,setOpen]=useState(false);const{address,busy,message,connect}=useWallet();const contract=process.env.NEXT_PUBLIC_CONTRACT_ADDRESS||"";return <main><header className="header"><Link className="logo" href="/"><span><Megaphone/></span><strong>ADPROOF</strong><i>ESCROW</i></Link><nav>{nav.map(([l,h])=><Link key={h} href={h}>{l}</Link>)}</nav><div className="head-actions"><a className="address" href={contract?`https://explorer-studio.genlayer.com/address/${contract}`:"https://explorer-studio.genlayer.com/contracts"} target="_blank" rel="noreferrer">{short(contract)}<ExternalLink/></a><button onClick={connect} disabled={busy}><Wallet/>{address?short(address):busy?"Connecting":"Connect wallet"}</button></div><button className="menu" onClick={()=>setOpen(!open)}>{open?<X/>:<Menu/>}</button></header>{open&&<div className="mobile-menu">{nav.map(([l,h])=><Link key={h} href={h} onClick={()=>setOpen(false)}>{l}</Link>)}</div>}{message&&<div className="wallet-error">{message}</div>}{children}<footer><strong>ADPROOF / V2</strong><span>Funded delivery. Public evidence. Direct settlement.</span></footer></main>}
