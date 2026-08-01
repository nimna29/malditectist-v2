# Report for period 2026-07-22 to 2026-07-29

**Goals from last meeting:**

- Execute the E2 environment (No-JIT, clean traces) and run it through the full pipeline to trained models. (E1 - default environment)
- Set up the obfuscation for E3 and E4 using ProGuard, and obfuscate all 260 files.
- Begin tracing the obfuscated files for E3 and E4.
- Resume the document writing on the Lit review and Methodology

**Activity this period:**

- Completed the E2 environment fully. I changed the JVM launch to `Xint` in `run_trace.sh` so the JIT compilation is turned off, then traced all the files into a separate `data-e2` folder. This means that E2 now captures the raw interpreter opcode traces, which is the second controlled environment in the study.
- Checked the vocabulary coverage for E2 against the fixed 287 opcode vocabulary. The coverage came out at about 99.79%, which is almost the same as E1. This is because the interpreter still runs as native code, so the same opcode set covers it well.
- Set up ProGuard to obfuscate the files for E3 and E4. This required to installing a Java runtime on my machine, because ProGuard is a Java program and until now everything was running inside Docker. I matched the Java version to the one inside the tracer container so the obfuscated files stay compatible with the tracing environment.
- While obfuscating, I found that many of the files could not be processed by ProGuard. When I looked into why, I discovered a huge important issue with the dataset itself.

---

**The dataset issue I found this week:**

- When I checked the files that ProGuard rejected, I found that a large number of the original 260 files never actually ran their program. The manifest inside the file declared a main class, so the scraper had selected them as executable, but for many files that main class was either not present inside the file or a required dependency was missing. This means that when these files were traced, the trace captured only the Java virtual machine starting up, failing to find the program, and exiting, rather than the actual program running.
- I confirmed this by running one of the files directly, and it reported that it could not find or load the main class that the manifest pointed to. This is because these files were packaging artifacts, source-only archives, or test bundles, not runnable programs.
- I think this matters for the whole study, because the same file set is planned to be used across all four environments. If a file never ran, its trace is just startup noise, and that noise was being fed into the models in E1 and E2 as if it were program behaviour.
- Because of this, I spent time for validating the whole files properly instead of moving directly into E3 and E4 tracing. I wrote scripts to check, for every file, whether the declared main class actually exists inside the archive, and to run the files that exited with an error so I could separate the ones that genuinely ran from the ones that failed at startup.
- After this validation I confirmed a common set of 100 files (surprisingly, this was the initially planned JAR file amount) that actually execute their program, that ProGuard can obfuscate, and that still launch correctly after obfuscation. All four environments will use this same 100 file set so the comparison stays fair.

---

**Goals before next meeting:**

- Trace the E3 environment (JIT, obfuscated) using the validated 100 files.
- Trace the E4 environment (No-JIT, obfuscated) using the same 100 files.
- Re-run the E1 and E2 pipelines restricted to the same 100 files, so all four environments match. This only needs the feature engineering and model training to run again because the traces already exist.
- **Build the four environment comparison tables and plots and start conducting the analysis and I can be start the report writing with the findings.**
- **Resume the document writing, and add the file validation and the four environment design into the Methodology.**

**Items to discuss:**

- Discuss this file validation finding and confirm the plan to report the file count reduction from 260 down to 100, explained in three clear stages for all four environments.
- The final study will run on 100 files across all four environments. I want to confirm this is acceptable, and discuss how to frame the smaller file count in the Limitations, since each file still contributes a very large number of opcodes.
- During obfuscation some files only worked with a weaker ProGuard setting, so I had to turn off the optimisation step. I want to note this as a small inconsistency in the obfuscation and confirm it is fine to report it as a limitation.
- The scraper's original executable check only looked at the manifest, not whether the class really exists. This is worth noting as future work for building a cleaner dataset and a clear explanation in the document as well.

---

Items discussed with supervisor: (After the meeting)

- Go with this plan, and once finished, start writing the document
- First, do the background sections and the literature review section, then send them to the supervisor for review and feedback. I can start with the Methodology section as well.