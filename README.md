# MalDitectist V2
**A Hybrid Malware Detection Utilising Just-in-Time (JIT) Compilation Traces and Unsupervised Anomaly Detection**

MalDitectist V2 is an MSc research project that studies whether the low level x86 opcodes a Java program produces at runtime can be used to model "normal" program behaviour, so that anything that deviates from it can be flagged as an anomaly. Instead of reading the Java bytecode, each JAR file is executed inside an isolated Docker sandbox while Intel PIN records every native instruction the JVM executes, including the code produced by the JIT compiler. Those opcode traces are then turned into features and used to train unsupervised anomaly detection models on benign data only.

The core experiment is a **four environment controlled study** that tests whether the detector still holds up when the two things an attacker can most easily change, JIT compilation and code obfuscation, are changed.

---

## Table of Contents

- [Research Overview](#research-overview)
- [Pipeline](#pipeline)
- [The Four Environments](#the-four-environments)
- [Results](#results)
- [Key Findings](#key-findings)
- [Repository Structure](#repository-structure)
- [Getting Started](#getting-started)
- [Limitations](#limitations)
- [Future Work](#future-work)
- [Project Timeline](#project-timeline)

---

## Research Overview

| | |
| --- | --- |
| **Scope** | Benign, executable Java (JAR) programs only |
| **Data source** | Maven Central repository (`repo1.maven.org`) |
| **Tracing** | Intel PIN 3.30 Pintool attached to OpenJDK 17 inside Docker (Ubuntu 22.04) |
| **Opcode vocabulary** | 287 confirmed x86/x64 opcode mnemonics |
| **Final dataset** | 100 validated JAR files, traced in all four environments |
| **Trace volume** | Around 53.4 billion opcodes captured in the original 260 file run |
| **Models** | Isolation Forest, Local Outlier Factor, One-Class SVM, Elliptic Envelope |
| **Evaluation** | 80/20 hold out sanity check plus 5 fold cross validation, reported as false positive rate (mean and std) |

Because no real malware is used, there is no "anomaly" class to test against. The study therefore measures how well each model learns the benign baseline (how rarely it wrongly flags a benign file), and how stable that baseline stays as the execution environment changes.

---

## Pipeline

```
Maven Central
     |
     v
1. Data Collection     scraper.py walks the repo, downloads JARs, keeps only ones with a Main-Class
     |
     v
2. File Validation     check the main class really exists, the program actually runs,
     |                 and it still launches after obfuscation  (260 files -> 100 files)
     v
3. Obfuscation         ProGuard 7.6.1 (E3 / E4 only)
     |
     v
4. Opcode Tracing      Docker + Xvfb + Intel PIN + JVM  ->  raw opcode trace per file
     |
     v
5. Preprocessing       log parsing -> manifest, EDA, vocabulary cleaning, int16 encoding
     |
     v
6. Feature Engineering frequency, entropy, bigram, trigram, Markov, sliding window phases
     |
     v
7. Model Training      4 unsupervised anomaly detectors, benign only, k-fold evaluation
     |
     v
8. Cross Environment   compare E1 to E4 and isolate the effect of JIT and obfuscation
   Analysis
```

### 1. Data Collection (`src/data_collection`)

- `scraper.py` crawls the Maven Central directory tree, keeps only the latest version of each artifact, downloads the JAR and uses `manifest_checker.py` to keep only files that declare a `Main-Class` in `META-INF/MANIFEST.MF`. Progress is saved to a JSON file so a run can be resumed, and it handles the Maven rate limit.
- `get_latest.py` keeps only the newest version of each selected artifact.
- `queue_cleanup.py` is a one time tool that cleans the crawler queue using the same subdirectory filters.
- `logger.py` provides a shared logger (terminal plus a rotating log file) used by every script.

The scraper collected 260 executable JAR files in total.

### 2. File Validation (`src/sandbox`)

During obfuscation it turned out that many of the 260 files never actually ran their program. The manifest declared a main class, but the class was missing or a dependency was absent, so the trace only captured the JVM starting up, failing and exiting. To keep the comparison fair, the dataset was validated in three stages:

1. `check_launch.py` and `main_class_present.ipynb` check whether the declared main class actually exists inside the archive.
2. `exit_1_troubleshoot.py` re-runs every file that exited with an error inside the same Docker image, to separate files that genuinely executed program logic from files that failed at startup.
3. `build_keep_list.py` and `check_keep_work.py` combine the results, remove files that ProGuard could not process or that no longer launch after obfuscation, and write the final `keep_list.csv`.

The result is a common set of **100 files** used by all four environments.

### 3. Obfuscation (`src/sandbox/obfuscate.py`)

Each JAR is obfuscated with ProGuard using an aggressive config (`scripts/proguard_obfuscation.pro`) first. If the optimiser aborts because of an incomplete class hierarchy, it falls back to a config with optimisation turned off (`scripts/proguard_fallback.pro`). The config used for every file is recorded in `obfuscation_config_used.csv`.

### 4. Opcode Tracing (`src/sandbox`)

- `Dockerfile` builds the `malditectist-tracer` image: Ubuntu 22.04, OpenJDK 17, Intel PIN 3.30 and Xvfb (a virtual display so GUI programs can also run).
- `pintool/opcode_tracer.cpp` is a custom Pintool that logs the short opcode name (`OPCODE_StringShort()`) of every executed instruction.
- `scripts/run_trace.sh` runs inside the container. It starts Xvfb, attaches PIN to the JVM, watches the output size, and stops the trace at the timeout (1 hour) or the size limit (1 GB). The `-Xint` flag turns JIT off for E2 and E4.
- `tracer.py` orchestrates the run on the host, starting a fresh container for every file (1 CPU core, 1 GB RAM), feeding an optional generic stdin input for interactive CLI programs, and tracking progress so it can resume.

### 5. Preprocessing (`src/data_analysis*`)

- **`data_preprocess.ipynb`** parses the tracer log into a `manifest.csv` (duration, opcode count, exit reason, exit code, size limit hit) for every file.
- **`eda_encoding.ipynb`** streams the multi GB raw traces line by line, builds the vocabulary, checks the opcode counts against the manifest, and compares raw text streaming with an encoded NumPy array approach.
- **`vocab_fix_encoding.ipynb`** fixes a vocabulary problem found during EDA. The raw vocabulary had over a million distinct entries, which is impossible for real x86 code. The cause was multiple PIN threads writing to the same output stream at once, which mixed opcode names together (for example `MOVMOV` or `AADDCALL_NEAR`). A whitelist of real opcodes (`x86_opcode_whitelist.py`, built from the Intel SDM and PIN docs) reduced the vocabulary to **287 real opcodes** while removing only **0.215%** of the opcode stream. With the clean vocabulary the traces fit in `int16`, which roughly halves the storage compared to the raw text.
- **`utils.py`** holds the shared helpers (log parser, streaming reader, encoding functions).

### 6. Feature Engineering (`feature_engineering.ipynb`)

Six representations are built from the same encoded traces:

| Feature | What it captures |
| --- | --- |
| Frequency (bag of opcodes) | Normalised share of each opcode, ignoring order |
| Opcode entropy | How varied the instruction mix is |
| Bigrams | Pairs of consecutive opcodes (sparse, about 82K columns) |
| Trigrams | Triples of consecutive opcodes (sparse, about 23.6M possible columns) |
| Markov transition matrix | Probability that one opcode follows another |
| Sliding window phases | Frequency vectors per window over time, showing execution phases such as startup, I/O and compute |

### 7. Model Training (`model_train.ipynb`)

Four unsupervised detectors are trained on the standardised frequency features of the 100 benign files. A hold out split is used as a quick sanity check, and 5 fold cross validation is the main reported result because the dataset is small. A hyperparameter grid was run on the One-Class SVM to check whether its weaker result came from the parameter settings. The notebook also includes per fold FPR charts, anomaly score distributions, a One-Class SVM sensitivity heatmap, a PCA projection of the benign feature space and a list of the files flagged most often. The final models, scaler and opcode column order are saved as `.joblib` files.

### 8. Cross Environment Analysis (`src/cross_analysis/env_crosss_analysis.ipynb`)

Loads the saved comparison table from every environment and builds the combined tables, grouped bar chart, heatmap, Isolation Forest generalisation plot, factor effect plot and a mean vs std stability view. The outputs are saved in `src/sandbox/cross_env_results`.

---

## The Four Environments

The same 100 files and the same 287 opcode vocabulary are used everywhere. Only two controlled factors change:

| Environment | JIT Compilation | Obfuscation | Data folder | Notebooks |
| --- | --- | --- | --- | --- |
| **E1** (baseline) | On | Clean | `src/sandbox/data` | `src/data_analysis` |
| **E2** | Off (`-Xint`) | Clean | `src/sandbox/data-e2` | `src/data_analysis_e2` |
| **E3** | On | ProGuard | `src/sandbox/data-e3` | `src/data_analysis_e3` |
| **E4** | Off (`-Xint`) | ProGuard | `src/sandbox/data-e4` | `src/data_analysis_e4` |

Each pair of environments differs by exactly one factor, so its effect can be isolated:

- **JIT effect:** E1 vs E2 (clean) and E3 vs E4 (obfuscated)
- **Obfuscation effect:** E1 vs E3 (JIT) and E2 vs E4 (No-JIT)

---

## Results

Mean false positive rate on benign files, 5 fold cross validation (lower is better):

| Model | E1 | E2 | E3 | E4 |
| --- | --- | --- | --- | --- |
| **Isolation Forest** | **0.060 ± 0.073** | **0.080 ± 0.081** | **0.070 ± 0.068** | **0.060 ± 0.073** |
| Local Outlier Factor | 0.110 ± 0.086 | 0.080 ± 0.051 | 0.150 ± 0.071 | 0.120 ± 0.068 |
| One-Class SVM | 0.440 ± 0.107 | 0.430 ± 0.201 | 0.420 ± 0.181 | 0.420 ± 0.121 |
| Elliptic Envelope | 0.890 ± 0.073 | 0.930 ± 0.060 | 0.910 ± 0.037 | 0.880 ± 0.093 |

Change in mean FPR when each factor is applied (positive means more false positives):

| Model | JIT off (clean) E2-E1 | JIT off (obf) E4-E3 | Obfuscation (JIT) E3-E1 | Obfuscation (No-JIT) E4-E2 |
| --- | --- | --- | --- | --- |
| Isolation Forest | +0.02 | -0.01 | +0.01 | -0.02 |
| Local Outlier Factor | -0.03 | -0.03 | +0.04 | +0.04 |
| One-Class SVM | -0.01 | 0.00 | -0.02 | -0.01 |
| Elliptic Envelope | +0.04 | -0.03 | +0.02 | -0.05 |

---

## Key Findings

- **Isolation Forest is the strongest and most stable model in every environment**, with a false positive rate between 0.06 and 0.08, close to the 5% contamination level it was configured with. Neither JIT nor obfuscation moves it by more than 0.02, so it does not depend on the two factors an attacker can most easily change.
- **Local Outlier Factor is a reasonable second choice**, but it is a little more sensitive to obfuscation (+0.04 in both obfuscation comparisons).
- **One-Class SVM and Elliptic Envelope are not suitable** for this feature space. They wrongly flag around 42% to 93% of benign files, and tuning the One-Class SVM did not close the gap.
- The PCA projection shows that the files Isolation Forest flags sit at the edge of the benign cluster, so the model behaves sensibly. The files flagged by all four models are large bundled JARs (the `hudi` and `oak` distributions), which are genuine outliers inside the benign set.
- Vocabulary coverage in the No-JIT environment was about 99.79%, almost the same as E1, so the same 287 opcode feature space works for both interpreted and JIT compiled execution.
- Validating that each program really runs is essential. A manifest `Main-Class` entry alone is not enough, and without this check a large part of the original data was JVM startup noise rather than program behaviour.

---

## Repository Structure

```
malditectist-v2/
├── deliverables/                 Submitted documents (ethics form, risk assessment, etc.)
├── meetings/                     Weekly supervisor meeting reports (before and after each meeting)
└── src/
    ├── requirements.txt
    ├── data_collection/          Maven scraper, manifest checker, logger
    ├── sandbox/
    │   ├── Dockerfile            Tracer image (Ubuntu, OpenJDK 17, Intel PIN, Xvfb)
    │   ├── pintool/              Custom PIN opcode tracer (C++)
    │   ├── scripts/              run_trace.sh, ProGuard configs, generic stdin input
    │   ├── tracer.py             Host side trace orchestrator
    │   ├── obfuscate.py          Batch ProGuard obfuscation
    │   ├── check_launch.py       File validation scripts
    │   ├── exit_1_troubleshoot.py
    │   ├── build_keep_list.py
    │   ├── check_keep_work.py
    │   ├── keep_list.csv         Final 100 file set
    │   ├── data/                 E1 manifest, features, models, outputs
    │   ├── data-e2/              E2
    │   ├── data-e3/              E3
    │   ├── data-e4/              E4
    │   └── cross_env_results/    Four environment comparison tables
    ├── data_analysis/            E1 notebooks (preprocess, EDA, vocab fix, features, training)
    ├── data_analysis_e2/         E2 notebooks
    ├── data_analysis_e3/         E3 notebooks
    ├── data_analysis_e4/         E4 notebooks
    └── cross_analysis/           Cross environment analysis notebook
```

The raw and encoded trace files are not in the repository because each raw trace can be up to 1 GB. Only the manifests, features, trained models and result tables are committed.

---

## Getting Started

### Requirements

- An **Intel x86-64** machine (Intel PIN does not support other architectures)
- Docker
- Python 3.11 or newer
- Java 17 and [ProGuard 7.6.1](https://github.com/Guardsquare/proguard) (only for obfuscation in E3 / E4)

### Setup

```bash
git clone https://github.com/nimna29/malditectist-v2.git
cd malditectist-v2/src
pip install -r requirements.txt
```

### 1. Collect JAR files

```bash
cd src/data_collection
python scraper.py
python get_latest.py
```

### 2. Build the tracer image

```bash
cd src/sandbox
docker build -t malditectist-tracer .
```

### 3. Obfuscate (E3 / E4 only)

Place ProGuard in `src/sandbox/proguard-7.6.1` and run:

```bash
python obfuscate.py
```

### 4. Trace

Set `INPUT_DIR`, `OUTPUT_DIR` and `PROGRESS_FILE` at the top of `tracer.py` for the environment you want to run. For E2 and E4, make sure the JVM is launched with `-Xint` in `scripts/run_trace.sh` (rebuild the image after changing it).

```bash
python tracer.py
```

### 5. Analyse

Run the notebooks of the matching environment folder in this order:

1. `data_preprocess.ipynb`
2. `eda_encoding.ipynb`
3. `vocab_fix_encoding.ipynb`
4. `feature_engineering.ipynb`
5. `model_train.ipynb`

Then run `src/cross_analysis/env_crosss_analysis.ipynb` to compare all four environments.

---

## Limitations

- **No real malware.** The models are trained and evaluated on benign files only, so the study reports false positive rates and robustness, not a malware detection rate.
- **Small dataset.** 100 files with 5 fold cross validation means only 20 files per fold, although every file contributes a very large number of opcodes.
- **Platform specific.** The tracer relies on Intel PIN, so it only works on Intel x86-64 systems.
- **Tracer output corruption.** The Pintool writes from several threads without synchronisation, which mixed some opcode names. This was fixed afterwards with the whitelist (0.215% of opcodes removed), not at the source.
- **Uneven obfuscation.** Some files only worked with the fallback ProGuard config that turns optimisation off, so not every file received the same level of obfuscation.
- **Scraper check.** The original scraper only looked at the manifest, not whether the main class really exists, which is why the dataset had to be reduced from 260 to 100 files.
- **One feature type modelled.** Models were trained on the frequency features only. The n-gram, Markov and sliding window features were built but not yet compared across the four environments.

---

## Future Work

- Train and compare models on the n-gram, Markov and sliding window features across all four environments.
- Generate synthetic anomaly traces, and later use real malware samples, to measure actual detection performance.
- Add thread safe writing to the Pintool and capture operands as well as opcodes.
- Improve the scraper so it validates that the main class exists and the program runs before a file is selected.
- Build a working application where a user can upload a file and check whether it is malicious before running it, and later a desktop version.

---

## Project Timeline

Weekly progress is documented in the [`meetings`](meetings) folder.

| Period | Milestone |
| --- | --- |
| June 2026 | Project scope, literature review start, Maven scraper |
| Late June 2026 | Docker and Intel PIN sandbox completed, 260 JARs traced |
| Early July 2026 | Manifest, EDA, vocabulary fix and int16 encoding |
| Mid July 2026 | Feature engineering and first anomaly detection models (E1) |
| Late July 2026 | E2 traced, dataset validation (260 to 100 files), ProGuard obfuscation |
| Early August 2026 | E3 and E4 traced, all environments retrained, cross environment analysis |
| August 2026 | Dissertation writing (Introduction, Literature Review, Methodology) |

---

