"use client";
import { ArrowLeft } from "lucide-react";
import { useRouter } from "next/navigation";
import { Reveal } from "./Reveal";
export function PageIntro({index,title,copy}:{index:string;title:string;copy:string}){const router=useRouter();return <Reveal className="page-intro"><button className="back" onClick={()=>router.back()}><ArrowLeft/>Back</button><span>{index}</span><h1>{title}</h1><p>{copy}</p></Reveal>}
