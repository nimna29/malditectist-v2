# Report for period 2026-06-25 to 2026-06-30

**Goals from last meeting:**

- Finished data collection.
- Finish docker environment to just run a jar file inside that env.

**Activity this period:**

- Finished the data collection part and the scraper successfully downloaded 242 executable jar files, then I stopped data collection process. In total now I have 260 jar file.
- Finished the Docker env setup and fully completed the opcode data extraction process.
- Paused for a moment drafting the Lit review this week to give my full focus into getting the extraction environment stable and work for the opcode trace.

**Goals before next meeting:**

- Do the data preprocessing part for the extracted opcodes.
- Start Feature Engineering - testing vectorization or n-gram models on the opcodes
- Resume the Lit review

**Items to discuss:**

- Review a sample of the extracted opcode output, and I already have included one sample in our mail chain.
- Discuss about the feature representation for these opcodes, for example standard frequency counts, opcode N-grams, which I saw in couple of research papers.
- For the Lit review, should I include what I have done for the Docker environment setup, or should that be saved entirely for the Methodology part or I just can discuss the theory about the sandbox environment on Lit review?

---

Items discussed with supervisor: (After the meeting)
- Remove limits and try to extract most of the opcodes from each jar file.
- Take a look at how I can get opcodes with also operands - no need for right now
- This is a platform-specific setup because this setup will only work with the intel systems
- Markov ML models for opcodes - check that for another alternative approach for N-grams
- Just take a look at how the jar programs are working based on the opcodes (could be based on the opcode frequency)
    - Like the phases of the application process
    - Like a timeline
    - For example: startup phase, I/O phase, more processing, accessing something, quitting the program
- Talk about the methodology section - The end goal of the dissertation is to tell the story about how this methodology will help to analyse programs
- This could successfully identify types of programs, it phases, and detect anomalies in those programs, or this could be a total failed approach to do so
