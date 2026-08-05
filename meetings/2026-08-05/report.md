# Report for period 2026-07-29 to 2026-08-05

**Goals from last meeting:**

- Trace the E3 environment (JIT, obfuscated) using the validated 100 files.
- Trace the E4 environment (No-JIT, obfuscated) using the same 100 files.
- Rerun the E1 and E2 pipelines restricted to the same 100 files, so all four environments match.
- Build the four environment comparison tables and plots and start conducting the analysis.
- Resume the document writing, and add the file validation and the four environment design into the Methodology.

**Activity this period:**

- Completed the tracing for both E3 and E4 using the validated 100 file set.
- Reran the E1 and E2 pipelines restricted to the same 100 files. Only the feature engineering and the model training needed to run again because the traces already existed from the earlier sessions.
- Built a separate cross environment analysis notebook that reads the four saved model comparison tables and connect them into one place.
- Completed the analysis of the four environment results.
- On the document side I completed the Introduction and the Lit Review fully. I have also started working on the Methodology, only just started.

---

**The four environment results:**

- The mean false positive rate for each model across the four environments

```
Mean False Positive Rate across all four environments (lower is better)

Environment             E1    E2    E3    E4
Model                                       
Isolation Forest     0.060 0.080 0.070 0.060
Local Outlier Factor 0.110 0.080 0.150 0.120
One-Class SVM        0.440 0.430 0.420 0.420
Elliptic Envelope    0.890 0.930 0.910 0.880

Mean ± Std False Positive Rate across all four environments

Environment                      E1             E2             E3             E4
Model                                                                           
Isolation Forest      0.060 ± 0.073  0.080 ± 0.081  0.070 ± 0.068  0.060 ± 0.073
Local Outlier Factor  0.110 ± 0.086  0.080 ± 0.051  0.150 ± 0.071  0.120 ± 0.068
One-Class SVM         0.440 ± 0.107  0.430 ± 0.201  0.420 ± 0.181  0.420 ± 0.121
Elliptic Envelope     0.890 ± 0.073  0.930 ± 0.060  0.910 ± 0.037  0.880 ± 0.093
```

---

**Goals before next meeting:**

- Finish writing the Methodology, including the tracing environment, the file validation parts, and the four environment design process.
- Start writing the Results and Discussion part using the tables and plots from the notebooks.

**Items to discuss:**

- Whether I should try to do the n-gram and Markov feature comparison across the four environments, maybe tarin models, or leave it as future work. I’m not sure I will have time to do that as well.
- How about the already written sections of documents

---

Items discussed with supervisor: (After the meeting)

-