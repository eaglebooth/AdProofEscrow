"use client";
import { motion } from "framer-motion";
export function Reveal({children,className="",delay=0}:{children:React.ReactNode;className?:string;delay?:number}){return <motion.div className={className} initial={{opacity:0,y:22}} whileInView={{opacity:1,y:0}} viewport={{once:true,amount:.14}} transition={{duration:.48,delay,ease:[.22,1,.36,1]}}>{children}</motion.div>}
