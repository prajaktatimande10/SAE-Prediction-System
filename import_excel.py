import pandas as pd
import mysql.connector
from mysql.connector import Error

# ============================================================
# 1. EXCEL FILE
# ============================================================

EXCEL_FILE = "data/patients.xlsx"


# ============================================================
# 2. MYSQL CONFIGURATION
# ============================================================

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Prajakta@2005",
    "database": "sae_prediction_system"
}


# ============================================================
# 3. READ EXCEL FILE
# ============================================================

print("\n========================================")
print("   SAE PREDICTION SYSTEM")
print("   EXCEL → MYSQL IMPORT")
print("========================================")

print("\nReading Excel file...")

try:
    df = pd.read_excel(EXCEL_FILE)

except FileNotFoundError:
    print("\nERROR: Excel file not found.")
    print("Expected location:")
    print(EXCEL_FILE)
    exit()

except Exception as error:
    print("\nERROR while reading Excel:")
    print(error)
    exit()


# ============================================================
# 4. SHOW EXCEL INFORMATION
# ============================================================

print("\nExcel columns found:")
print(df.columns.tolist())

print("\nTotal records:", len(df))


# ============================================================
# 5. CLEAN COLUMN NAMES
# ============================================================

df.columns = (
    df.columns
    .str.strip()
    .str.lower()
)


# ============================================================
# 6. REQUIRED COLUMNS
# ============================================================

required_columns = [
    "subject_id",
    "hadm_id",
    "stay_id",
    "gender",
    "age",
    "intime",
    "outtime",
    "icu_los_hours"
]


for column in required_columns:

    if column not in df.columns:

        print("\nERROR:")
        print(f"Missing required column: {column}")

        print("\nAvailable columns:")
        print(df.columns.tolist())

        exit()


# ============================================================
# 7. CLEAN DATA TYPES
# ============================================================

print("\nCleaning dataset...")

df["subject_id"] = pd.to_numeric(
    df["subject_id"],
    errors="coerce"
)

df["hadm_id"] = pd.to_numeric(
    df["hadm_id"],
    errors="coerce"
)

df["stay_id"] = pd.to_numeric(
    df["stay_id"],
    errors="coerce"
)

df["age"] = pd.to_numeric(
    df["age"],
    errors="coerce"
)

df["icu_los_hours"] = pd.to_numeric(
    df["icu_los_hours"],
    errors="coerce"
)

df["intime"] = pd.to_datetime(
    df["intime"],
    errors="coerce"
)

df["outtime"] = pd.to_datetime(
    df["outtime"],
    errors="coerce"
)


# ============================================================
# 8. REMOVE INVALID ROWS
# ============================================================

before = len(df)

df = df.dropna(
    subset=[
        "subject_id",
        "hadm_id",
        "stay_id"
    ]
)

after = len(df)

print("\nValid records:", after)
print("Removed invalid records:", before - after)


# ============================================================
# 9. CONNECT TO MYSQL
# ============================================================

print("\nConnecting to MySQL...")

try:

    connection = mysql.connector.connect(
        host=DB_CONFIG["host"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        database=DB_CONFIG["database"]
    )

    if connection.is_connected():

        print("MySQL connected successfully.")


except Error as error:

    print("\nMYSQL CONNECTION ERROR:")
    print(error)

    print("\nPlease check:")
    print("1. MySQL Server is running")
    print("2. Username is correct")
    print("3. Password is correct")
    print("4. Database 'sae_prediction_system' exists")

    exit()


# ============================================================
# 10. CREATE CURSOR
# ============================================================

cursor = connection.cursor()


# ============================================================
# 11. CREATE TABLE IF IT DOES NOT EXIST
# ============================================================

print("\nChecking MySQL table...")

create_table_query = """
CREATE TABLE IF NOT EXISTS icu_patients (

    id INT AUTO_INCREMENT PRIMARY KEY,

    subject_id BIGINT NOT NULL,

    hadm_id BIGINT NOT NULL,

    stay_id BIGINT NOT NULL UNIQUE,

    gender VARCHAR(20),

    age DECIMAL(6,2),

    intime DATETIME,

    outtime DATETIME,

    icu_los_hours DECIMAL(10,2)

)
"""

try:

    cursor.execute(create_table_query)

    connection.commit()

    print("Table 'icu_patients' is ready.")

except Error as error:

    print("\nTABLE CREATION ERROR:")
    print(error)

    cursor.close()
    connection.close()

    exit()


# ============================================================
# 12. INSERT QUERY
# ============================================================

insert_query = """
INSERT IGNORE INTO icu_patients
(
    subject_id,
    hadm_id,
    stay_id,
    gender,
    age,
    intime,
    outtime,
    icu_los_hours
)
VALUES
(
    %s,
    %s,
    %s,
    %s,
    %s,
    %s,
    %s,
    %s
)
"""


# ============================================================
# 13. IMPORT DATA
# ============================================================

print("\n========================================")
print("Importing Excel records...")
print("Please wait...")
print("========================================\n")

success = 0
skipped = 0

total_records = len(df)


for index, row in df.iterrows():

    try:

        values = (

            int(row["subject_id"]),

            int(row["hadm_id"]),

            int(row["stay_id"]),

            None
            if pd.isna(row["gender"])
            else str(row["gender"]),

            None
            if pd.isna(row["age"])
            else float(row["age"]),

            None
            if pd.isna(row["intime"])
            else row["intime"].to_pydatetime(),

            None
            if pd.isna(row["outtime"])
            else row["outtime"].to_pydatetime(),

            None
            if pd.isna(row["icu_los_hours"])
            else float(row["icu_los_hours"])

        )

        cursor.execute(
            insert_query,
            values
        )

        success += 1


    except Exception as error:

        skipped += 1

        print(
            f"Skipped row {index + 1}: {error}"
        )


    # Show progress every 5,000 records

    if (index + 1) % 5000 == 0:

        connection.commit()

        percentage = (
            (index + 1) / total_records
        ) * 100

        print(
            f"Progress: {index + 1:,} / "
            f"{total_records:,} "
            f"({percentage:.1f}%)"
        )


# ============================================================
# 14. FINAL COMMIT
# ============================================================

connection.commit()


# ============================================================
# 15. CHECK DATABASE COUNT
# ============================================================

cursor.execute(
    "SELECT COUNT(*) FROM icu_patients"
)

database_count = cursor.fetchone()[0]


# ============================================================
# 16. CLOSE MYSQL
# ============================================================

cursor.close()

connection.close()


# ============================================================
# 17. FINAL RESULT
# ============================================================

print("\n")
print("========================================")
print("       EXCEL IMPORT COMPLETED")
print("========================================")

print(
    f"Excel records       : {total_records:,}"
)

print(
    f"Processed records   : {success:,}"
)

print(
    f"Skipped records     : {skipped:,}"
)

print(
    f"MySQL total records: {database_count:,}"
)

print("----------------------------------------")

print("Database : sae_prediction_system")
print("Table    : icu_patients")

print("========================================")

print("\nExcel → MySQL connection successful!")