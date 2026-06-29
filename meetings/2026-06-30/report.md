# Report for period 2026-06-30 to 2026-07-TBA

**Goals from last meeting:**

- Remove limits on the tracer and try to extract most of the opcodes from each jar file.
- Do the data preprocessing part for the extracted opcodes.
- Start feature engineering - testing vectorization or N-gram models on the opcodes.
- Resume the Lit review

**Activity this period:**

- Managed to do some modifications to the tracer code and able to capture the jar file opcodes without limits. Only added file size limit to manage storage space, which is about 1 GB for each file.
- Already started the data preprocessing part to handle these large files. Working on a tokenization function to encode these huge opcode text strings into a shorter and compressed integer format, which will be save as a numpy format.
- Also start to create python code to create a manifest for each file which contains some info about this output files.

**Goals before next meeting:**

- Finish the feature engineering part on the preprocessed opcodes - testing methods like standard frequency counts, N-grams, and Markov
- Have the analyzed dataset fully ready to train some ML, DL models
- Resume drafting the Lit review and start writing the Methodology section

**Items to discuss:**

- Discuss the progress on this period
- And discuss whether that tokenization method is a better way to analyze this huge opcode data.
- Because we are not going to meet next week, confirm that this plan is okay to proceed.

---

Items discussed with supervisor: (After the meeting)

-