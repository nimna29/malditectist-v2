# Report for period 2026-06-03 to 2026-06-10

**Goals from last meeting:**

- Finalized Project Scope to go with only benign Java files.

**Activity this period:**

- Project initiation with data collection and literature review

**Goals before next meeting:**

- Start of the Lit Review
- Start of Java file download

**Items to discuss:**

- About project start date (according to the Ethics form)
- Project timeline and plan
- Discuss about setting up a Docker container to run the Java files
- Discuss about python script to use Maven APIs to download files

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
- About Lit Review, right now I have 26 research papers related to ML models, JIT, and opcodes

---

Items agreed with supervisor: (After the meeting)

- Results of discussion
- New tasks