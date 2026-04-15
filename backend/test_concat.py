import pandas as pd
from app.services.cleaner import clean_dataset
from app.services.fusion import auto_concat_datasets

f1 = r'c:\Users\Virid\Desktop\7mo\EducationIA\backend\data\raw\a64c9bce_educacion_media_superior_2024_2025.csv'
f2 = r'c:\Users\Virid\Desktop\7mo\EducationIA\backend\data\raw\0928e6f2_educacion_superior_escolarizada_2024_2025.csv'
# Si tienes 2 del mismo tipo o similares en columnas
# Pero asumimos que estos dos tienen una similitud en columnas y podemos probar.

try:
    df1 = pd.read_csv(f1, nrows=100).copy()
    filename1 = f1.split('\\')[-1]
    c1, _ = clean_dataset(df1, "ds1", filename1)
    
    df2 = pd.read_csv(f2, nrows=100).copy()
    filename2 = f2.split('\\')[-1]
    c2, _ = clean_dataset(df2, "ds2", filename2)
    
    # Let's create a ds3 with the exact same columns as ds1 to verify concat
    c3 = c1.copy()
    c3['tipo_educacion'] = "otro state"
    
    # Check if they share enough columns
    cols1 = set(c1.columns)
    cols3 = set(c3.columns)
    overlap = len(cols1 & cols3) / max(len(cols1), len(cols3))
    print(f"Overlap Ratio between ds1 and ds3: {overlap:.2f}")

    # Concatenate
    datasets = {"ds1": c1, "ds3": c3, "ds2": c2} # ds2 won't be concatenated with ds1/ds3
    names = {"ds1": filename1, "ds3": "another_media_superior.csv", "ds2": filename2}
    
    result = auto_concat_datasets(datasets, names)
    print(f"Resulting fused datasets: {list(result.keys())}")
    
    for k, v in result.items():
        print(f"Dataset '{k}' has {len(v)} rows and {len(v.columns)} columns.")
        print("Tipos de educación presentes:", v['tipo_educacion'].unique())

except Exception as e:
    import traceback
    traceback.print_exc()
