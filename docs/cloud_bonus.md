# Cloud Bonus

## AWS

A production mapping can be:

```text
IoT devices
   |
AWS IoT Core
   |
Kinesis / Kinesis Data Firehose
   |
S3 data lake
   |
Glue / EMR / Spark
   |
Athena / Redshift
   |
CloudWatch / SNS alerts
```

## GCP

```text
IoT gateway
   |
Pub/Sub
   |
Dataflow
   |
Cloud Storage / BigQuery
   |
Vertex AI / Looker
```

## Azure

```text
IoT devices
   |
Azure IoT Hub
   |
Event Hubs / Stream Analytics
   |
ADLS Gen2
   |
Databricks / Synapse
   |
Power BI / Azure Monitor
```

The local implementation deliberately keeps the same conceptual stages so the storage and processing layers can be replaced by cloud services later.
