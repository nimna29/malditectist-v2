# Report for period 2026-07-15 to 2026-07-22

**Goals from last meeting:**

- Finish the feature engineering part on the preprocessed opcodes - testing methods like standard frequency counts, N-grams, and Markov
- Have the analyzed dataset fully ready to train some ML, DL models
- Resume drafting the Lit review and start writing the Methodology section

**Activity this period:**

- Finished the feature engineering part for all 260 benign trace files, using the cleaned 287 opcode vocabulary. Built six different representations from the same encoded traces, which are
    - Frequency counts
    - Opcode entropy
    - bigrams, trigrams
    - Markov transition matrices
    - Sliding window phase vectors
- All of this data is stored as files for later use.
- During the data analysis, I noticed that there are damaged opcode code strings, this has been cleaned before the feature engineering.
- Started the model development notebook and trained the first anomaly detection models on the frequency features. And 4 models were tested
    - Isolation Forest
    - One-Class SVM
    - Local Outlier Factor
    - Elliptic Envelope
- All of them are trained on benign data only
- Set up the evaluation using both a hold out split (80/20) and 5 fold cross validation. The k-fold result is used as the main reported number because the dataset is small, so the false positive rate is reported as a mean and standard deviation across the folds.
- The results show that the Isolation Forest performs clearly better than the One-Class SVM. The Isolation Forest gives a false positive rate of about 0.054 and the One Class SVM gives about 0.246 on the same folds.
- Ran a hyperparameter tuning grid on the One-Class SVM to check whether this gap was caused by the parameter settings. But that didn't help.
- Haven’t resumed the document writing because I gave full focus to the development to complete ASAP.

**Goals before next meeting:**

- Write a Python script to generate synthetic anomaly trace files so the trained models can be tested using something that is not benign.
- Score the synthetic anomaly files with the saved models and create a separation results, also some plots.
- Resume the document writing

**Items to discuss:**

- Discuss the progress and next steps.
- Once the current development for the standard frequency counts is finished and I have completed some of the document writing, I can try the other feature engineering method with the same model to see how they perform.
- Discuss the plan for the synthetic anomaly traces.

---

Items discussed with supervisor: (After the meeting)

-