import os
import sys

# 1. Definer de 100% rene og isolerte stiene på C-disken
pyspark_path = r"C:\spark_temp\pyspark"
hadoop_path = r"C:\spark_temp\Hadoop\hadoop-3.3.1"
java_path = r"C:\Program Files\Microsoft\jdk-17.0.20.101-hotspot"

# 2. Sett miljøvariabler
os.environ["SPARK_HOME"] = pyspark_path
os.environ["JAVA_HOME"] = java_path
os.environ["HADOOP_HOME"] = hadoop_path

# 3. Oppdater PATH slik at Windows og Java finner alt de trenger med en gang
os.environ["PATH"] = os.path.join(java_path, "bin") + ";" + os.path.join(pyspark_path, "bin") + ";" + os.environ["PATH"]

# 4. Bruk den virtuelle Python-tolkeren din som driver
os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

# Fortell Python at den skal importere PySpark fra den rene mappen
sys.path.insert(0, r"C:\spark_temp")

# 5. Start SparkSession
from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .master("local[*]") \
    .appName("Test") \
    .getOrCreate()

print("-" * 40)
print(f"Suksess! Spark-versjon: {spark.version}")
print("-" * 40)

spark.stop()
