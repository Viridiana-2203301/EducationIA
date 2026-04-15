import pandas as pd
from app.services.cleaner import clean_dataset

f1 = r'c:\Users\Virid\Desktop\7mo\EducationIA\backend\data\raw\a64c9bce_educacion_media_superior_2024_2025.csv'
f2 = r'c:\Users\Virid\Desktop\7mo\EducationIA\backend\data\raw\0928e6f2_educacion_superior_escolarizada_2024_2025.csv'

try:
    df1 = pd.read_csv(f1, nrows=10).copy()
    filename1 = f1.split('\\')[-1]
    c1, _ = clean_dataset(df1, "ds1", filename1)
    print("Media Superior OK")
    print(f"Tipo educación ds1: {c1['tipo_educacion'].iloc[0]}")
except Exception as e:
    print(f"Media Superior ERROR: {e}")

try:
    df2 = pd.read_csv(f2, nrows=10).copy()
    filename2 = f2.split('\\')[-1]
    c2, _ = clean_dataset(df2, "ds2", filename2)
    print("Superior OK")
    print(f"Tipo educación ds2: {c2['tipo_educacion'].iloc[0]}")
except Exception as e:
    print(f"Superior ERROR: {e}")
