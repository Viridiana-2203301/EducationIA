import pandas as pd
from datetime import datetime
from app.services.cleaner import clean_dataset
from app.services.matcher import find_relationships
from app.services.storage import storage
from app.schemas.schemas import DatasetInfo, DatasetStatus

f1 = r'c:\Users\Virid\Desktop\7mo\EducationIA\backend\data\raw\a64c9bce_educacion_media_superior_2024_2025.csv'
f2 = r'c:\Users\Virid\Desktop\7mo\EducationIA\backend\data\raw\0928e6f2_educacion_superior_escolarizada_2024_2025.csv'

# Load just a few rows to test
df1 = pd.read_csv(f1, nrows=100)
df2 = pd.read_csv(f2, nrows=100)

# Clean
cleaned_df1, stats1 = clean_dataset(df1, "ds1")
cleaned_df2, stats2 = clean_dataset(df2, "ds2")

# Setup storage for matcher
ds_info1 = DatasetInfo(id="ds1", filename="media.csv", status=DatasetStatus.UPLOADED, uploaded_at=datetime.utcnow(), row_count=100, column_count=len(df1.columns), file_size_mb=1.0)
ds_info2 = DatasetInfo(id="ds2", filename="superior.csv", status=DatasetStatus.UPLOADED, uploaded_at=datetime.utcnow(), row_count=100, column_count=len(df2.columns), file_size_mb=1.0)

storage.store_dataset_info("ds1", ds_info1)
storage.store_dataset_info("ds2", ds_info2)
storage.store_dataframe("ds1", cleaned_df1)
storage.store_dataframe("ds2", cleaned_df2)

# Find relationships
print("\nFinding relationships...")
rels = find_relationships([ds_info1, ds_info2])

with open("verify_out.txt", "w") as f:
    f.write(f"Raw Media Superior cols: {df1.columns.tolist()[:10]}\n")
    f.write(f"Raw Superior cols: {df2.columns.tolist()[:10]}\n\n")
    f.write(f"Cleaned Media Superior cols: {cleaned_df1.columns.tolist()[:10]}\n")
    f.write(f"Cleaned Superior cols: {cleaned_df2.columns.tolist()[:10]}\n\n")
    f.write("Finding relationships...\n")
    for rel in rels:
        f.write(f"Match between {rel.source_dataset_id}:{rel.source_column} and {rel.target_dataset_id}:{rel.target_column} (Confidence: {rel.confidence}, Type: {rel.relationship_type})\n")
