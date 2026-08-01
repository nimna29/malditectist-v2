# Whitelist of confirmed real x86/x64 opcode strings which based on the
# Intel PIN's OPCODE_StringShort() API

# Purpose Of This Whitelist
# The opcode tracer (opcode_tracer.cpp) writes from multiple PIN
# threads to a shared std::ofstream without synchronisation. Concurrent
# writes interleave at the byte level, producing corrupted strings like
# MOVMOV, OV, AADDCALL_NEAR in the raw trace files. 

# These corrupted strings cannot be reliably split back into the original opcodes because the
# interleave position is arbitrary (random).so the only correct fix is to keep
# strings that match known real opcode names and discard the rest.

# Sources used to build this list are follows
# - Intel Corporation (2024) Intel 64 and IA-32 Architectures Software
#   Developer's Manual, Combined Volumes Vol 2 instruction set reference
#   https://www.intel.com/content/www/us/en/developer/articles/technical/intel-sdm.html

# - Intel Corporation, Pin: A Dynamic Binary Instrumentation Tool,
#   OPCODE_StringShort() API documentation.
#   https://software.intel.com/sites/landingpage/pintool/docs/98830/Pin/doc/html/index.html

# - Crossvalidated against the top frequency entries of the actual traced
#   dataset (global_opcode_freq.csv), where every entry above 
#   1M occurrences was manually classified as real or corrupted


X86_OPCODE_WHITELIST = {
    # Data movement
    "MOV", "MOVZX", "MOVSX", "MOVSXD", "MOVAPS", "MOVUPS", "MOVDQU", "MOVDQA",
    "MOVQ", "MOVD", "MOVSD_XMM", "MOVSS", "MOVHPS", "MOVLPS", "MOVHPD", "MOVLPD",
    "MOVAPD", "MOVUPD", "MOVNTDQ", "MOVNTPS", "MOVNTPD", "MOVNTDQA", "MOVNTQ",
    "MOVNTI", "MOVBE", "MOVMSKPS", "MOVMSKPD", "MOVHLPS", "MOVLHPS",
    "MOVSB", "MOVSW", "MOVSD", "MOVSQ", "MOVSHDUP", "MOVSLDUP", "MOVDDUP",

    # Stack operations
    "PUSH", "POP", "PUSHA", "POPA", "PUSHF", "POPF", "PUSHFQ", "POPFQ",

    # Arithmetic
    "ADD", "SUB", "MUL", "IMUL", "DIV", "IDIV", "ADC", "SBB", "NEG",
    "INC", "DEC", "CMP", "TEST",

    # Logic
    "AND", "OR", "XOR", "NOT",

    # Shifts and rotates
    "SHL", "SHR", "SAR", "ROL", "ROR", "RCL", "RCR", "SHLD", "SHRD",
    "SHLX", "SHRX", "SARX", "RORX",

    # Control flow
    "JMP", "JMP_FAR", "CALL_NEAR", "CALL_FAR", "RET_NEAR", "RET_FAR",
    "JZ", "JNZ", "JL", "JLE", "JNL", "JNLE", "JB", "JBE", "JNB", "JNBE",
    "JS", "JNS", "JO", "JNO", "JP", "JNP", "JCXZ", "JECXZ", "JRCXZ",
    "LOOP", "LOOPE", "LOOPNE",

    # Set byte on condition
    "SETZ", "SETNZ", "SETL", "SETLE", "SETNL", "SETNLE", "SETB", "SETBE",
    "SETNB", "SETNBE", "SETS", "SETNS", "SETO", "SETNO", "SETP", "SETNP",

    # Conditional moves
    "CMOVZ", "CMOVNZ", "CMOVL", "CMOVLE", "CMOVNL", "CMOVNLE", "CMOVB",
    "CMOVBE", "CMOVNB", "CMOVNBE", "CMOVS", "CMOVNS", "CMOVO", "CMOVNO",
    "CMOVP", "CMOVNP",

    # String operations
    "STOSB", "STOSW", "STOSD", "STOSQ", "LODSB", "LODSW", "LODSD", "LODSQ",
    "SCASB", "SCASW", "SCASD", "SCASQ", "CMPSB", "CMPSW", "CMPSQ",
    "REP_STOSB", "REP_STOSW", "REP_STOSD", "REP_STOSQ",
    "REP_MOVSB", "REP_MOVSW", "REP_MOVSD", "REP_MOVSQ",
    "REPE_CMPSB", "REPE_CMPSD", "REPNE_SCASB", "REPNE_SCASD",

    # Bit manipulation
    "BT", "BTS", "BTR", "BTC", "BSF", "BSR", "TZCNT", "LZCNT", "POPCNT",
    "BSWAP", "XCHG", "XADD", "CMPXCHG", "CMPXCHG8B", "CMPXCHG16B",
    "BZHI", "BEXTR", "BLSI", "BLSR", "BLSMSK", "ANDN", "PDEP", "PEXT",

    # Atomic lock variants (PIN appends _LOCK for locked instructions)
    "ADD_LOCK", "SUB_LOCK", "INC_LOCK", "DEC_LOCK", "AND_LOCK", "OR_LOCK",
    "XOR_LOCK", "NOT_LOCK", "NEG_LOCK", "BTC_LOCK", "BTS_LOCK", "BTR_LOCK",
    "XADD_LOCK", "XCHG_LOCK", "CMPXCHG_LOCK", "CMPXCHG8B_LOCK", "CMPXCHG16B_LOCK",

    # Address calculation and no-ops
    "LEA", "NOP", "PAUSE", "LEAVE", "ENTER",

    # System instructions
    "SYSCALL", "SYSRET", "SYSENTER", "SYSEXIT", "INT", "INT1", "INT3",
    "IRET", "IRETD", "IRETQ", "HLT", "UD2", "CPUID", "RDTSC", "RDTSCP",
    "RDPMC", "RDRAND", "RDSEED", "XGETBV", "XSETBV", "XSAVE", "XSAVEC",
    "XSAVEOPT", "XRSTOR", "LFENCE", "MFENCE", "SFENCE", "CLFLUSH",
    "CLFLUSHOPT", "CLWB", "PREFETCHT0", "PREFETCHT1", "PREFETCHT2",
    "PREFETCHNTA", "PREFETCHW",

    # Sign extension
    "CDQE", "CDQ", "CQO", "CBW", "CWDE", "CWD",

    # x87 and scalar floating point
    "ADDSD", "SUBSD", "MULSD", "DIVSD", "SQRTSD", "COMISD", "UCOMISD",
    "ADDSS", "SUBSS", "MULSS", "DIVSS", "SQRTSS", "COMISS", "UCOMISS",
    "MINSD", "MAXSD", "MINSS", "MAXSS", "ANDPD", "ANDPS", "ORPD", "ORPS",
    "XORPD", "XORPS", "ANDNPD", "ANDNPS",
    "CVTSI2SD", "CVTSD2SI", "CVTTSD2SI", "CVTSI2SS", "CVTSS2SI", "CVTTSS2SI",
    "CVTSS2SD", "CVTSD2SS", "CVTDQ2PD", "CVTDQ2PS", "CVTPD2DQ", "CVTPS2DQ",
    "CVTTPD2DQ", "CVTTPS2DQ",
    "SHUFPD", "SHUFPS", "UNPCKLPD", "UNPCKLPS", "UNPCKHPD", "UNPCKHPS",

    # SSE integer (MMX/SSE2+)
    "PXOR", "PAND", "POR", "PANDN",
    "PCMPEQB", "PCMPEQW", "PCMPEQD", "PCMPEQQ",
    "PCMPGTB", "PCMPGTW", "PCMPGTD", "PCMPGTQ",
    "PSUBB", "PSUBW", "PSUBD", "PSUBQ",
    "PADDB", "PADDW", "PADDD", "PADDQ",
    "PMOVMSKB", "PSHUFB", "PSHUFD", "PSHUFLW", "PSHUFHW",
    "PUNPCKLBW", "PUNPCKLWD", "PUNPCKLDQ", "PUNPCKLQDQ",
    "PUNPCKHBW", "PUNPCKHWD", "PUNPCKHDQ", "PUNPCKHQDQ",
    "PMINUB", "PMAXUB", "PMINUD", "PMAXUD", "PMINSW", "PMAXSW",
    "PALIGNR", "PSLLDQ", "PSRLDQ",
    "PSLLW", "PSLLD", "PSLLQ", "PSRLW", "PSRLD", "PSRLQ", "PSRAW", "PSRAD",
    "PACKUSWB", "PACKSSWB", "PACKSSDW", "PACKUSDW",
    "PMULLW", "PMULLD", "PMULHW", "PMULHUW", "PMULUDQ", "PMADDWD",
    "PCMPESTRI", "PCMPESTRM", "PCMPISTRI", "PCMPISTRM",
    "PTEST", "PINSRB", "PINSRW", "PINSRD", "PINSRQ",
    "PEXTRB", "PEXTRW", "PEXTRD", "PEXTRQ",

    # AVX/AVX2 (V-prefixed forms)
    "VPXOR", "VPAND", "VPOR", "VPANDN",
    "VPCMPEQB", "VPCMPEQW", "VPCMPEQD", "VPCMPEQQ",
    "VPCMPGTB", "VPCMPGTW", "VPCMPGTD", "VPCMPGTQ",
    "VPSUBB", "VPSUBW", "VPSUBD", "VPSUBQ",
    "VPADDB", "VPADDW", "VPADDD", "VPADDQ",
    "VPMOVMSKB", "VPSHUFB", "VPSHUFD",
    "VPBROADCASTB", "VPBROADCASTW", "VPBROADCASTD", "VPBROADCASTQ",
    "VPMINUB", "VPMAXUB", "VPMINUD", "VPMAXUD",
    "VPALIGNR", "VPSLLDQ", "VPSRLDQ",
    "VPSLLW", "VPSLLD", "VPSLLQ", "VPSRLW", "VPSRLD", "VPSRLQ",
    "VZEROUPPER", "VZEROALL",
    "VMOVDQU", "VMOVDQA", "VMOVQ", "VMOVD",
    "VMOVAPS", "VMOVUPS", "VMOVAPD", "VMOVUPD", "VMOVSD", "VMOVSS",
    "VMOVHPS", "VMOVLPS", "VMOVHPD", "VMOVLPD",
    "VPCLMULQDQ", "PCLMULQDQ",
    "VPCMPESTRI", "VPCMPESTRM", "VPCMPISTRI", "VPCMPISTRM",
    "VPUNPCKLBW", "VPUNPCKLWD", "VPUNPCKLDQ", "VPUNPCKLQDQ",
    "VPUNPCKHBW", "VPUNPCKHWD", "VPUNPCKHDQ", "VPUNPCKHQDQ",
    "VINSERTI128", "VEXTRACTI128", "VINSERTF128", "VEXTRACTF128",
    "VPERM2I128", "VPERM2F128", "VPERMQ", "VPERMD",
    "VPTEST", "VPSADBW", "PSADBW",

    # MXCSR control register load/store (SSE and VEX-encoded AVX forms)
    # Added after threshold review caught these appearing 100K+ times each
    "LDMXCSR", "STMXCSR", "VLDMXCSR", "VSTMXCSR",

    # Non-temporal stores (VEX-encoded AVX forms of the SSE non-temporal ops)
    "VMOVNTDQ", "VMOVNTPS", "VMOVNTPD", "VMOVNTDQA",

    # AES and crypto extensions (common in Java crypto libraries)
    "AESENC", "AESENCLAST", "AESDEC", "AESDECLAST", "AESKEYGENASSIST", "AESIMC",
    "SHA1RNDS4", "SHA1NEXTE", "SHA1MSG1", "SHA1MSG2",
    "SHA256RNDS2", "SHA256MSG1", "SHA256MSG2",
    "CRC32",
}