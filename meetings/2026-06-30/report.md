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

- Do experiments in every possible way, even if it takes more time and resources to process, just need to look at what I can do with this data, and make a comparison with the results.
    - Like raw opcode traces vs numpy encoded traces
- Try any possible way to do the preprocessing and feature engineering, see the benefits and limitations, and determine whether it is worth doing it.
- And also note down everything you do.
- Next meeting 15th of July
