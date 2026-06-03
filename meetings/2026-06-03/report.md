# Report for period 2026-06-03 to 2026-06-10

**Goals from last meeting:**

- Finalized Project Scope to go with only benign Java files.

**Activity this period:**

- Project initiation with data collection and literature review

**Goals before next meeting:**

- Start of the Lit Review
- Start of Java file download
- Check Docker setup find out how to execute the Java programs

**Items to discuss:**

- About project start date (according to the Ethics form) ✅
- Project timeline and plan  ✅
- Discuss about setting up a Docker container to run the Java files  ✅
- Discuss about python script to use Maven APIs to download files  ✅

https://maven.apache.org/repository/layout.html

https://octopus.com/blog/maven-repos-explained

Example API Endpoint

```
https://repo1.maven.org/maven2/{groupId}/{artifactId}/{version}/{artifactId}-{version}.jar
```

Tested with this one

```
https://repo1.maven.org/maven2/spring/spring/1.0.2/spring-1.0.2.jar
```

- There is no available documentation to get the names of these groupId and artifactId, is it ok to generate a CSV file from a AI tool.
    - For example, generate a CSV file like the following, which contains the common and well-known groupId and artifactId. Then it can be loaded into a Python script to run and download files.

| group_id | artifact_id | domain |
| --- | --- | --- |
| com.google.guava | guava | utility |
| org.apache.commons | commons-lang3 | utility |
- About Lit Review, right now I have 26 research papers related to ML models, JIT, and opcode ✅

---

Items discussed with supervisor: (After the meeting)

- Discussed about the lit review - the review should be includes followings
    - About malware, malware detection, and etc (no need go too deep)
    - About ML models, techniques have already been used, selected models, advantages/disadvantages
    - About JIT compilation, a little bit of a deep discussion about JIT, Opcode, why this can be helpful, etc.
- You can add tables to the lit to compare the findings, features, limitations, etc.
- Deliverables folder - docs and notes that you have submitted into the LMS
- Docker / Environment setup
    - Use this research paper to find how to run jar files and extract the opcode from it - **Detecting obfuscated malware using reduced opcode set and optimised runtime trace**
    - Opcode Extraction: Host → Docker → Emulator (According to the above Paper) → Java Program
- Write a web scraper to download files from the Maven repo
    - Python script to go through the repo and only download jar files.
    - Can use Gen AI to filter common and simple CLI programs (minimum user interaction, Java program as a start of this project)
    - Once the process is reliable, more CLI and GUI programs can be used to increase the dataset.