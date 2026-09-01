from pathlib import Path
from pyspark.sql import SparkSession, Window
from pyspark.sql import functions as F

ROOT = Path(__file__).resolve().parents[1]
src = str(ROOT / "data" / "cleaned" / "sensor_readings_cleaned.parquet")
out = str(ROOT / "data" / "curated" / "pyspark_windows")

spark = (
    SparkSession.builder
    .appName("IoTSensorSlidingWindows")
    .master("local[*]")
    .getOrCreate()
)

df = spark.read.parquet(src)
w = Window.partitionBy("sensor_id").orderBy("timestamp").rowsBetween(-29, 0)

result = (
    df.withColumn("spark_rolling_avg", F.avg("reading_value").over(w))
      .withColumn("spark_moving_std", F.stddev("reading_value").over(w))
      .withColumn("spark_max", F.max("reading_value").over(w))
      .withColumn("spark_min", F.min("reading_value").over(w))
      .withColumn(
          "spark_rate_of_change",
          F.col("reading_value") -
          F.lag("reading_value", 1).over(Window.partitionBy("sensor_id").orderBy("timestamp"))
      )
)

result.write.mode("overwrite").parquet(out)
print(f"PySpark output: {out}")
spark.stop()
