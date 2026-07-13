"use client";
import { createContext, useContext, useState } from "react";
import { connectWallet } from "@/lib/genlayer";
type WalletContext = { address: string; busy: boolean; message: string; connect: () => Promise<void> };
const Context = createContext<WalletContext>({ address: "", busy: false, message: "", connect: async () => {} });
export function WalletProvider({children}:{children:React.ReactNode}){const[address,setAddress]=useState("");const[busy,setBusy]=useState(false);const[message,setMessage]=useState("");async function connect(){setBusy(true);const r=await connectWallet();setBusy(false);if(r.success){setAddress(String(r.data));setMessage("")}else setMessage(r.error||"Wallet connection failed")}return <Context.Provider value={{address,busy,message,connect}}>{children}</Context.Provider>}
export const useWallet=()=>useContext(Context);
