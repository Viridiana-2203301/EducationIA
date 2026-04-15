import pandas as pd

f1 = r'c:\Users\Virid\Desktop\7mo\EducationIA\backend\data\raw\a64c9bce_educacion_media_superior_2024_2025.csv'
f2 = r'c:\Users\Virid\Desktop\7mo\EducationIA\backend\data\raw\0928e6f2_educacion_superior_escolarizada_2024_2025.csv'

cols1 = pd.read_csv(f1, nrows=0).columns.tolist()
cols2 = pd.read_csv(f2, nrows=0).columns.tolist()

print("Media Superior:")
print(cols1)
print("\nSuperior Escolarizada:")
print(cols2)
