# Scenario 222 — Large Document Measurement Only

The document-size audit measures tracked documentation and evidence files against a 50,000-byte hot-document threshold. Oversized files produce informational `WARN` rows and a zero exit status; the report never blocks a Gate or archives/moves files. Measurements inform a later Human decision about document layering.
