\# Token Usage and Cost Report



\## 1. Overview



This report documents the language-model usage and estimated cost of the current shipment cost anomaly detection pipeline.



The current implementation uses Python, pandas, deterministic baseline calculations, and keyword-based context-note matching.



\## 2. LLM Usage



| Metric | Current Usage |

|---|---:|

| LLM API calls | 0 |

| Input tokens | 0 |

| Output tokens | 0 |

| LLM API cost | ₹0 |

| Vector database calls | 0 |



These figures describe the current implementation only. They do not include development conversations or any external services used separately.



\## 3. Processing Summary



\- Weekly route records processed: 728

\- Anomalies detected: 90

\- Justified anomalies: 2

\- Unexplained anomalies: 88

\- Records not flagged: 638



\## 4. Cost Calculation



No LLM API was called during the current pipeline execution. Therefore, LLM token usage and LLM API cost were zero.



The Python processing and local file operations may still consume computing resources. Those costs have not been measured.



\## 5. Limitations and Future Work



The current context-note matching component uses deterministic keyword rules. It does not use an LLM, embeddings, or a vector database.



If an LLM or retrieval-augmented generation (RAG) component is added later, its API calls, input tokens, output tokens, and estimated cost should be measured and reported separately.

