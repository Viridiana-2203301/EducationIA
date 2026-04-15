# ============================================================================
# PREDICCIÓN DE ABANDONO ESCOLAR CON INTELIGENCIA ARTIFICIAL
# ============================================================================
#
# INSTRUCCIONES DE EJECUCIÓN:
# 1. Activar el entorno virtual:
#       .\EducationIA\Scripts\activate
#
# 2. Instalar dependencias necesarias (si no están instaladas):
#       pip install matplotlib seaborn xgboost joblib
#
# 3. Ejecutar el script:
#       python prediccion_abandono_escolar.py
#
# NOTA: El script busca el dataset en 'backend/data/raw/' y fusiona
#       automáticamente los archivos CSV. Si ya existe
#       'dataset_completo_35_archivos.csv', lo cargará directamente.
# ============================================================================

import os
import sys
import warnings
import time
from pathlib import Path

# Configurar salida a UTF-8 para soportar emojis en terminales Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

import numpy as np
import pandas as pd

# --- Configuración de matplotlib para entorno sin GUI ---
import matplotlib
matplotlib.use('Agg')  # Backend no interactivo para evitar errores de display
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, roc_curve, confusion_matrix, classification_report
)
import joblib

# Intentar importar XGBoost
try:
    from xgboost import XGBClassifier
    XGBOOST_DISPONIBLE = True
    print("✅ XGBoost disponible - se usará XGBClassifier")
except ImportError:
    XGBOOST_DISPONIBLE = False
    print("⚠️  XGBoost no disponible - se usará GradientBoostingClassifier como alternativa")

warnings.filterwarnings('ignore')
sns.set_style('whitegrid')
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 12

# ============================================================================
# CONFIGURACIÓN DE RUTAS
# ============================================================================
BASE_DIR = Path(__file__).resolve().parent
DATA_RAW_DIR = BASE_DIR / 'backend' / 'data' / 'raw'
DATASET_PATH = BASE_DIR / 'dataset_completo_35_archivos.csv'
OUTPUT_DIR = BASE_DIR / 'resultados_abandono'
MODELOS_DIR = OUTPUT_DIR / 'modelos'
GRAFICAS_DIR = OUTPUT_DIR / 'graficas'

# Crear directorios de salida
OUTPUT_DIR.mkdir(exist_ok=True)
MODELOS_DIR.mkdir(exist_ok=True)
GRAFICAS_DIR.mkdir(exist_ok=True)

print("=" * 70)
print("   SISTEMA DE PREDICCIÓN DE ABANDONO ESCOLAR CON IA")
print("=" * 70)
print()


# ============================================================================
# PASO 1: CARGA DEL DATASET
# ============================================================================
def cargar_dataset():
    """
    Carga el dataset completo. Si no existe 'dataset_completo_35_archivos.csv',
    fusiona todos los archivos CSV del directorio raw, reduce su dimensionalidad
    filtrando solo las variables importantes, y lo guarda.
    """
    print("📂 PASO 1: Cargando dataset...")
    print("-" * 50)

    if DATASET_PATH.exists():
        print(f"   Archivo encontrado: {DATASET_PATH.name}")
        df = pd.read_csv(DATASET_PATH, encoding='latin1', low_memory=False)
        print(f"   ✅ Dataset cargado: {df.shape[0]:,} filas × {df.shape[1]} columnas")
        return df

    # Si no existe, fusionar archivos CSV del directorio raw
    print(f"   Archivo '{DATASET_PATH.name}' no encontrado.")
    print(f"   Buscando archivos CSV en: {DATA_RAW_DIR}")

    if not DATA_RAW_DIR.exists():
        print("   ❌ ERROR: No se encontró el directorio de datos raw.")
        print(f"       Ruta esperada: {DATA_RAW_DIR}")
        sys.exit(1)

    csv_files = sorted(DATA_RAW_DIR.glob('*.csv'))
    print(f"   📁 Encontrados {len(csv_files)} archivos CSV")

    if len(csv_files) == 0:
        print("   ❌ ERROR: No hay archivos CSV en el directorio raw.")
        sys.exit(1)

    # Fusionar todos los archivos
    dfs = []
    errores = 0
    for i, csv_file in enumerate(csv_files):
        try:
            temp_df = pd.read_csv(csv_file, encoding='latin1', low_memory=False)
            dfs.append(temp_df)
            if (i + 1) % 50 == 0:
                print(f"      Procesados {i + 1}/{len(csv_files)} archivos...")
        except Exception as e:
            errores += 1
            if errores <= 5:
                print(f"      ⚠️  Error al leer {csv_file.name}: {e}")

    print(f"   Fusionando {len(dfs)} dataframes...")
    df = pd.concat(dfs, ignore_index=True, sort=False)

    print(f"   Dimensiones originales: {df.shape[0]:,} filas × {df.shape[1]} columnas")
    print(f"   📉 Reduciendo dimensionalidad (filtrando variables importantes)...")
    
    # ------------------------------------------------------------------------
    # DEFINIR COLUMNAS IMPORTANTES A CONSERVAR
    # ------------------------------------------------------------------------
    columnas_importantes = [
        # Variables objetivo / cálculo de abandono
        'alumnos_01', 'alumnos_2', 'egresados',
        
        # Variables académicas
        'alumnos_3', 'alumnos_4', 'alumnos_5',
        
        # Variables de rezago
        'repetidores', 'repetidores_01', 'repetidores_2', 
        'repetidores_3', 'repetidores_4', 'repetidores_5',
        
        # Variables de ingreso
        'nvo_ing', 'nvo_ing_01', 'nvo_ing_2', 
        'nvo_ing_3', 'nvo_ing_4', 'nvo_ing_5',
        
        # Institucionales numéricas
        'docentes', 'grupos', 'alumnos', 'escuelas',
        
        # Institucionales categóricas
        'modalidad', 'control', 'nivel',
        
        # Demográficas
        'mujeres', 'hombres',
        
        # Contexto
        'titulados', 'existentes',
        
        # Grupos
        'grupos_01', 'grupos_2', 'grupos_3', 'grupos_4', 'grupos_5',
        
        # Entidad / Ubicación
        'c_nom_ent', 'c_nom_ent_etq', 'entidad'
    ]
    
    # Filtrar solo las columnas que realmente existen en el dataframe fusionado
    columnas_a_mantener = [col for col in columnas_importantes if col in df.columns]
    
    # Aplicar reducción de variables
    df = df[columnas_a_mantener]

    # Guardar el dataset fusionado para uso futuro
    print(f"   💾 Guardando dataset reducido en: {DATASET_PATH.name}")
    df.to_csv(DATASET_PATH, index=False, encoding='latin1')

    print(f"   ✅ Dataset procesado y reducido: {df.shape[0]:,} filas × {df.shape[1]} columnas")
    if errores > 0:
        print(f"   ⚠️  {errores} archivos no pudieron ser leídos")

    return df


# ============================================================================
# PASO 2: CREAR VARIABLE OBJETIVO - ABANDONO
# ============================================================================
def crear_variable_abandono(df):
    """
    Crea la variable objetivo 'abandono'.
    Lógica: un plantel/registro presenta abandono si tenía alumnos en grado 01
    (alumnos_01 > 0) pero NO tiene alumnos en grado 02 (alumnos_2 == 0)
    y NO tiene egresados (egresados == 0).
    """
    print("\n🎯 PASO 2: Creando variable objetivo 'abandono'...")
    print("-" * 50)

    # Verificar que las columnas necesarias existan
    columnas_necesarias = ['alumnos_01', 'alumnos_2', 'egresados']
    columnas_faltantes = [c for c in columnas_necesarias if c not in df.columns]

    if columnas_faltantes:
        print(f"   ⚠️  Columnas faltantes: {columnas_faltantes}")
        # Crear columnas faltantes con valor 0
        for col in columnas_faltantes:
            df[col] = 0
            print(f"      → Columna '{col}' creada con valor 0")

    # Rellenar nulos en las columnas clave con 0
    for col in columnas_necesarias:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # Crear variable de abandono
    df['abandono'] = (
        (df['alumnos_01'] > 0) &
        (df['alumnos_2'] == 0) &
        (df['egresados'] == 0)
    ).astype(int)

    # Calcular y mostrar estadísticas
    total = len(df)
    abandonos = df['abandono'].sum()
    tasa_abandono = (abandonos / total) * 100

    print(f"\n   📊 Estadísticas de abandono:")
    print(f"      Total de registros:     {total:,}")
    print(f"      Registros con abandono: {abandonos:,}")
    print(f"      Registros sin abandono: {total - abandonos:,}")
    print(f"      Tasa de abandono:       {tasa_abandono:.2f}%")

    return df, tasa_abandono


# ============================================================================
# PASO 3: SELECCIÓN DE VARIABLES PREDICTORAS (FEATURES)
# ============================================================================
def seleccionar_features(df):
    """
    Selecciona las mejores variables predictoras que existan en el dataset.
    Verifica la existencia de cada columna antes de incluirla.
    """
    print("\n📋 PASO 3: Seleccionando variables predictoras...")
    print("-" * 50)

    # Definir variables candidatas por categoría
    variables_candidatas = {
        'Académicas': ['alumnos_01', 'alumnos_2', 'alumnos_3', 'alumnos_4', 'alumnos_5'],
        'Rezago': ['repetidores', 'repetidores_01', 'repetidores_2',
                    'repetidores_3', 'repetidores_4', 'repetidores_5'],
        'Ingreso': ['nvo_ing', 'nvo_ing_01', 'nvo_ing_2',
                     'nvo_ing_3', 'nvo_ing_4', 'nvo_ing_5'],
        'Institucionales_num': ['docentes', 'grupos', 'alumnos', 'escuelas'],
        'Institucionales_cat': ['modalidad', 'control', 'nivel'],
        'Demográficas': ['mujeres', 'hombres'],
        'Contexto': ['egresados', 'titulados', 'existentes'],
        'Grupos': ['grupos_01', 'grupos_2', 'grupos_3', 'grupos_4', 'grupos_5'],
    }

    features_numericas = []
    features_categoricas = []

    for categoria, columnas in variables_candidatas.items():
        existentes = [c for c in columnas if c in df.columns]
        faltantes = [c for c in columnas if c not in df.columns]

        if categoria == 'Institucionales_cat':
            features_categoricas.extend(existentes)
        else:
            features_numericas.extend(existentes)

        status = f"✅ {len(existentes)}/{len(columnas)} disponibles"
        if faltantes:
            status += f" (faltan: {', '.join(faltantes)})"
        print(f"   {categoria:25s}: {status}")

    print(f"\n   📌 Total features numéricas:   {len(features_numericas)}")
    print(f"   📌 Total features categóricas: {len(features_categoricas)}")
    print(f"   📌 Total features:             {len(features_numericas) + len(features_categoricas)}")

    return features_numericas, features_categoricas


# ============================================================================
# PASO 4: PREPROCESAMIENTO
# ============================================================================
def preprocesar_datos(df, features_numericas, features_categoricas):
    """
    Realiza el preprocesamiento completo:
    - Codifica variables categóricas con LabelEncoder
    - Rellena valores nulos con 0
    - Escala variables numéricas con StandardScaler
    """
    print("\n🔧 PASO 4: Preprocesamiento de datos...")
    print("-" * 50)

    # Crear copia del DataFrame con solo las features necesarias
    todas_features = features_numericas + features_categoricas
    df_modelo = df[todas_features + ['abandono']].copy()

    # --- Manejar valores nulos ---
    nulos_antes = df_modelo.isnull().sum().sum()
    print(f"   Valores nulos antes del procesamiento: {nulos_antes:,}")

    # Rellenar nulos en numéricas con 0
    for col in features_numericas:
        df_modelo[col] = pd.to_numeric(df_modelo[col], errors='coerce').fillna(0)

    # --- Codificar variables categóricas ---
    label_encoders = {}
    for col in features_categoricas:
        df_modelo[col] = df_modelo[col].fillna('DESCONOCIDO').astype(str)
        le = LabelEncoder()
        df_modelo[col] = le.fit_transform(df_modelo[col])
        label_encoders[col] = le
        n_categorias = len(le.classes_)
        print(f"   Codificada '{col}': {n_categorias} categorías únicas")

    nulos_despues = df_modelo.isnull().sum().sum()
    print(f"   Valores nulos después del procesamiento: {nulos_despues:,}")

    # --- Separar X e y ---
    X = df_modelo[todas_features].values
    y = df_modelo['abandono'].values

    # --- Escalar variables numéricas ---
    scaler = StandardScaler()
    n_num = len(features_numericas)
    X[:, :n_num] = scaler.fit_transform(X[:, :n_num])

    print(f"\n   ✅ Preprocesamiento completado")
    print(f"      Forma de X: {X.shape}")
    print(f"      Forma de y: {y.shape}")
    print(f"      Distribución de y: 0={np.sum(y==0):,}, 1={np.sum(y==1):,}")

    return X, y, scaler, label_encoders, todas_features


# ============================================================================
# PASO 5: DIVISIÓN DE DATOS
# ============================================================================
def dividir_datos(X, y):
    """
    Divide los datos en conjuntos de entrenamiento (70%) y prueba (30%),
    estratificando por la variable objetivo para mantener proporciones.
    """
    print("\n✂️  PASO 5: División de datos (70% entrenamiento / 30% prueba)...")
    print("-" * 50)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.30, random_state=42, stratify=y
    )

    print(f"   Entrenamiento: {X_train.shape[0]:,} muestras ({X_train.shape[0]/len(y)*100:.1f}%)")
    print(f"   Prueba:        {X_test.shape[0]:,} muestras ({X_test.shape[0]/len(y)*100:.1f}%)")
    print(f"   Distribución en entrenamiento: 0={np.sum(y_train==0):,}, 1={np.sum(y_train==1):,}")
    print(f"   Distribución en prueba:        0={np.sum(y_test==0):,}, 1={np.sum(y_test==1):,}")

    return X_train, X_test, y_train, y_test


# ============================================================================
# PASO 6: ENTRENAMIENTO DE MODELOS
# ============================================================================
def entrenar_modelos(X_train, y_train):
    """
    Entrena tres modelos de clasificación:
    1. Regresión Logística
    2. Random Forest
    3. XGBoost (o Gradient Boosting como alternativa)
    """
    print("\n🤖 PASO 6: Entrenamiento de modelos...")
    print("-" * 50)

    modelos = {}

    # --- Modelo 1: Regresión Logística ---
    print("\n   📌 Entrenando Regresión Logística...", end=" ")
    t0 = time.time()
    lr = LogisticRegression(
        max_iter=1000,
        random_state=42,
        class_weight='balanced',  # Para manejar desbalance de clases
        solver='lbfgs',
        n_jobs=-1
    )
    lr.fit(X_train, y_train)
    t1 = time.time()
    modelos['Regresión Logística'] = lr
    print(f"({t1-t0:.1f}s)")

    # --- Modelo 2: Random Forest ---
    print("   📌 Entrenando Random Forest...", end=" ")
    t0 = time.time()
    rf = RandomForestClassifier(
        n_estimators=200,
        max_depth=15,
        min_samples_split=10,
        min_samples_leaf=5,
        random_state=42,
        class_weight='balanced',
        n_jobs=-1
    )
    rf.fit(X_train, y_train)
    t1 = time.time()
    modelos['Random Forest'] = rf
    print(f"({t1-t0:.1f}s)")

    # --- Modelo 3: XGBoost o Gradient Boosting ---
    if XGBOOST_DISPONIBLE:
        print("   📌 Entrenando XGBoost...", end=" ")
        t0 = time.time()

        # Calcular scale_pos_weight para desbalance
        n_neg = np.sum(y_train == 0)
        n_pos = np.sum(y_train == 1)
        scale_ratio = n_neg / max(n_pos, 1)

        xgb = XGBClassifier(
            n_estimators=200,
            max_depth=8,
            learning_rate=0.1,
            scale_pos_weight=scale_ratio,
            random_state=42,
            eval_metric='logloss',
            use_label_encoder=False,
            n_jobs=-1
        )
        xgb.fit(X_train, y_train)
        t1 = time.time()
        modelos['XGBoost'] = xgb
        print(f"({t1-t0:.1f}s)")
    else:
        print("   📌 Entrenando Gradient Boosting...", end=" ")
        t0 = time.time()
        gb = GradientBoostingClassifier(
            n_estimators=200,
            max_depth=8,
            learning_rate=0.1,
            random_state=42
        )
        gb.fit(X_train, y_train)
        t1 = time.time()
        modelos['Gradient Boosting'] = gb
        print(f"({t1-t0:.1f}s)")

    print(f"\n   ✅ {len(modelos)} modelos entrenados exitosamente")
    return modelos


# ============================================================================
# PASO 7: EVALUACIÓN DE MODELOS
# ============================================================================
def evaluar_modelos(modelos, X_test, y_test):
    """
    Evalúa cada modelo con múltiples métricas:
    Accuracy, Precision, Recall, F1-Score, AUC-ROC.
    """
    print("\n📊 PASO 7: Evaluación de modelos...")
    print("-" * 50)

    resultados = {}

    for nombre, modelo in modelos.items():
        y_pred = modelo.predict(X_test)
        y_proba = modelo.predict_proba(X_test)[:, 1]

        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, zero_division=0)
        rec = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        auc = roc_auc_score(y_test, y_proba)
        cm = confusion_matrix(y_test, y_pred)

        resultados[nombre] = {
            'accuracy': acc,
            'precision': prec,
            'recall': rec,
            'f1_score': f1,
            'auc_roc': auc,
            'confusion_matrix': cm,
            'y_pred': y_pred,
            'y_proba': y_proba
        }

        print(f"\n   ┌─── {nombre} ───")
        print(f"   │ Accuracy:  {acc:.4f}")
        print(f"   │ Precision: {prec:.4f}")
        print(f"   │ Recall:    {rec:.4f}")
        print(f"   │ F1-Score:  {f1:.4f}")
        print(f"   │ AUC-ROC:   {auc:.4f}")
        print(f"   │ Matriz de Confusión:")
        print(f"   │   Pred→     No Aband.  Abandono")
        print(f"   │   Real↓")
        print(f"   │   No Aband.  {cm[0][0]:>7,}   {cm[0][1]:>7,}")
        print(f"   │   Abandono   {cm[1][0]:>7,}   {cm[1][1]:>7,}")
        print(f"   └{'─' * 40}")

    # Identificar el mejor modelo por AUC
    mejor_modelo_nombre = max(resultados, key=lambda x: resultados[x]['auc_roc'])
    mejor_auc = resultados[mejor_modelo_nombre]['auc_roc']
    print(f"\n   🏆 MEJOR MODELO: {mejor_modelo_nombre} (AUC = {mejor_auc:.4f})")

    return resultados, mejor_modelo_nombre


# ============================================================================
# PASO 8: VISUALIZACIONES
# ============================================================================
def generar_visualizaciones(df, resultados, modelos, mejor_modelo_nombre,
                            todas_features, X_test, y_test):
    """
    Genera todas las visualizaciones solicitadas y las guarda como PNG.
    """
    print("\n📈 PASO 8: Generando visualizaciones...")
    print("-" * 50)

    # -----------------------------------------------------------------------
    # 8a) Gráfico de barras comparando rendimiento de los 3 modelos
    # -----------------------------------------------------------------------
    print("   📊 8a) Comparación de rendimiento de modelos...")
    fig, ax = plt.subplots(figsize=(12, 6))

    nombres = list(resultados.keys())
    auc_vals = [resultados[n]['auc_roc'] for n in nombres]
    f1_vals = [resultados[n]['f1_score'] for n in nombres]
    acc_vals = [resultados[n]['accuracy'] for n in nombres]
    rec_vals = [resultados[n]['recall'] for n in nombres]

    x = np.arange(len(nombres))
    width = 0.2

    bars1 = ax.bar(x - 1.5*width, auc_vals, width, label='AUC-ROC', color='#2196F3', edgecolor='white')
    bars2 = ax.bar(x - 0.5*width, f1_vals, width, label='F1-Score', color='#4CAF50', edgecolor='white')
    bars3 = ax.bar(x + 0.5*width, acc_vals, width, label='Accuracy', color='#FF9800', edgecolor='white')
    bars4 = ax.bar(x + 1.5*width, rec_vals, width, label='Recall', color='#9C27B0', edgecolor='white')

    # Añadir etiquetas de valor sobre las barras
    for bars in [bars1, bars2, bars3, bars4]:
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f'{height:.3f}',
                       xy=(bar.get_x() + bar.get_width() / 2, height),
                       xytext=(0, 3), textcoords="offset points",
                       ha='center', va='bottom', fontsize=8, fontweight='bold')

    ax.set_xlabel('Modelo', fontsize=13)
    ax.set_ylabel('Valor de la Métrica', fontsize=13)
    ax.set_title('Comparación de Rendimiento de los Modelos de ML', fontsize=15, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(nombres, fontsize=11)
    ax.legend(loc='lower right', fontsize=10)
    ax.set_ylim(0, 1.15)
    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(GRAFICAS_DIR / '8a_comparacion_modelos.png', dpi=150, bbox_inches='tight')
    plt.close()

    # -----------------------------------------------------------------------
    # 8b) Matriz de confusión del mejor modelo
    # -----------------------------------------------------------------------
    print("   📊 8b) Matriz de confusión del mejor modelo...")
    fig, ax = plt.subplots(figsize=(8, 7))
    cm = resultados[mejor_modelo_nombre]['confusion_matrix']

    sns.heatmap(cm, annot=True, fmt=',d', cmap='Blues', ax=ax,
                xticklabels=['No Abandona', 'Abandona'],
                yticklabels=['No Abandona', 'Abandona'],
                annot_kws={'size': 16, 'fontweight': 'bold'},
                linewidths=2, linecolor='white')
    ax.set_xlabel('Predicción', fontsize=13)
    ax.set_ylabel('Valor Real', fontsize=13)
    ax.set_title(f'Matriz de Confusión - {mejor_modelo_nombre}', fontsize=15, fontweight='bold')
    plt.tight_layout()
    plt.savefig(GRAFICAS_DIR / '8b_matriz_confusion.png', dpi=150, bbox_inches='tight')
    plt.close()

    # -----------------------------------------------------------------------
    # 8c) Top 10 variables más importantes
    # -----------------------------------------------------------------------
    print("   📊 8c) Top 10 variables más importantes...")
    # Buscar el modelo basado en árboles para importancias
    modelo_importancias = None
    nombre_modelo_imp = None
    for nombre in ['Random Forest', 'XGBoost', 'Gradient Boosting']:
        if nombre in modelos:
            modelo_importancias = modelos[nombre]
            nombre_modelo_imp = nombre
            break

    if modelo_importancias is not None and hasattr(modelo_importancias, 'feature_importances_'):
        importancias = modelo_importancias.feature_importances_
        indices = np.argsort(importancias)[::-1][:10]

        fig, ax = plt.subplots(figsize=(12, 7))
        top_features = [todas_features[i] for i in indices]
        top_importancias = importancias[indices]

        colors = plt.cm.RdYlGn_r(np.linspace(0.2, 0.8, 10))
        bars = ax.barh(range(9, -1, -1), top_importancias, color=colors, edgecolor='white', height=0.7)

        # Añadir valores
        for i, (bar, val) in enumerate(zip(bars, top_importancias)):
            ax.text(val + 0.002, bar.get_y() + bar.get_height()/2,
                   f'{val:.4f}', va='center', fontsize=10, fontweight='bold')

        ax.set_yticks(range(9, -1, -1))
        ax.set_yticklabels(top_features, fontsize=11)
        ax.set_xlabel('Importancia', fontsize=13)
        ax.set_title(f'Top 10 Variables Más Importantes ({nombre_modelo_imp})',
                     fontsize=15, fontweight='bold')
        ax.grid(axis='x', alpha=0.3)
        plt.tight_layout()
        plt.savefig(GRAFICAS_DIR / '8c_importancia_variables.png', dpi=150, bbox_inches='tight')
        plt.close()
    else:
        print("      ⚠️  No se pudo generar gráfico de importancias (modelo no disponible)")

    # -----------------------------------------------------------------------
    # 8d) Curva ROC comparativa
    # -----------------------------------------------------------------------
    print("   📊 8d) Curva ROC comparativa...")
    fig, ax = plt.subplots(figsize=(10, 8))

    colores_roc = {'Regresión Logística': '#2196F3', 'Random Forest': '#4CAF50',
                   'XGBoost': '#FF5722', 'Gradient Boosting': '#FF5722'}

    for nombre in resultados:
        y_proba = resultados[nombre]['y_proba']
        fpr, tpr, _ = roc_curve(y_test, y_proba)
        auc_val = resultados[nombre]['auc_roc']
        color = colores_roc.get(nombre, '#999999')
        ax.plot(fpr, tpr, color=color, lw=2.5,
                label=f'{nombre} (AUC = {auc_val:.4f})')

    ax.plot([0, 1], [0, 1], 'k--', lw=1.5, alpha=0.5, label='Clasificador aleatorio')
    ax.fill_between([0, 1], [0, 1], alpha=0.05, color='gray')
    ax.set_xlabel('Tasa de Falsos Positivos (FPR)', fontsize=13)
    ax.set_ylabel('Tasa de Verdaderos Positivos (TPR)', fontsize=13)
    ax.set_title('Curva ROC Comparativa de los Modelos', fontsize=15, fontweight='bold')
    ax.legend(loc='lower right', fontsize=11, framealpha=0.9)
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(GRAFICAS_DIR / '8d_curva_roc.png', dpi=150, bbox_inches='tight')
    plt.close()

    # -----------------------------------------------------------------------
    # 8e) Perfil comparativo: abandona vs continúa
    # -----------------------------------------------------------------------
    print("   📊 8e) Perfil comparativo: abandona vs continúa...")
    # Variables numéricas clave para el perfil
    vars_perfil = [v for v in ['alumnos_01', 'alumnos_2', 'repetidores',
                                'nvo_ing', 'docentes', 'grupos', 'mujeres', 'hombres']
                   if v in df.columns]

    if vars_perfil:
        fig, ax = plt.subplots(figsize=(14, 7))

        # Calcular promedios por grupo
        promedios_no_abandona = df[df['abandono'] == 0][vars_perfil].mean()
        promedios_abandona = df[df['abandono'] == 1][vars_perfil].mean()

        x = np.arange(len(vars_perfil))
        width = 0.35

        bars1 = ax.bar(x - width/2, promedios_no_abandona, width,
                       label='No Abandona', color='#4CAF50', edgecolor='white', alpha=0.85)
        bars2 = ax.bar(x + width/2, promedios_abandona, width,
                       label='Abandona', color='#F44336', edgecolor='white', alpha=0.85)

        # Etiquetas de valor
        for bar in bars1:
            h = bar.get_height()
            ax.annotate(f'{h:.1f}', xy=(bar.get_x() + bar.get_width()/2, h),
                       xytext=(0, 3), textcoords="offset points",
                       ha='center', va='bottom', fontsize=8)
        for bar in bars2:
            h = bar.get_height()
            ax.annotate(f'{h:.1f}', xy=(bar.get_x() + bar.get_width()/2, h),
                       xytext=(0, 3), textcoords="offset points",
                       ha='center', va='bottom', fontsize=8)

        ax.set_xlabel('Variable', fontsize=13)
        ax.set_ylabel('Promedio', fontsize=13)
        ax.set_title('Perfil Comparativo: Estudiantes que Abandonan vs Continúan',
                     fontsize=15, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(vars_perfil, rotation=30, ha='right', fontsize=11)
        ax.legend(fontsize=12)
        ax.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        plt.savefig(GRAFICAS_DIR / '8e_perfil_comparativo.png', dpi=150, bbox_inches='tight')
        plt.close()

    # -----------------------------------------------------------------------
    # 8f) Tasa de abandono por entidad (top 10)
    # -----------------------------------------------------------------------
    print("   📊 8f) Tasa de abandono por entidad (Top 10)...")
    col_entidad = None
    for col in ['c_nom_ent', 'c_nom_ent_etq', 'entidad']:
        if col in df.columns:
            col_entidad = col
            break

    if col_entidad and 'abandono' in df.columns:
        tasa_por_entidad = df.groupby(col_entidad)['abandono'].mean() * 100
        top_10_entidades = tasa_por_entidad.sort_values(ascending=False).head(10)

        fig, ax = plt.subplots(figsize=(14, 7))
        colors = plt.cm.Reds(np.linspace(0.4, 0.9, 10))
        bars = ax.barh(range(9, -1, -1), top_10_entidades.values, color=colors,
                       edgecolor='white', height=0.7)

        for bar, val in zip(bars, top_10_entidades.values):
            ax.text(val + 0.3, bar.get_y() + bar.get_height()/2,
                   f'{val:.1f}%', va='center', fontsize=10, fontweight='bold')

        ax.set_yticks(range(9, -1, -1))
        ax.set_yticklabels(top_10_entidades.index, fontsize=10)
        ax.set_xlabel('Tasa de Abandono (%)', fontsize=13)
        ax.set_title('Top 10 Entidades con Mayor Tasa de Abandono Escolar',
                     fontsize=15, fontweight='bold')
        ax.grid(axis='x', alpha=0.3)
        plt.tight_layout()
        plt.savefig(GRAFICAS_DIR / '8f_abandono_por_entidad.png', dpi=150, bbox_inches='tight')
        plt.close()

    # -----------------------------------------------------------------------
    # 8g) Mapa de calor de correlaciones
    # -----------------------------------------------------------------------
    print("   📊 8g) Mapa de calor de correlaciones...")
    vars_corr = [v for v in ['alumnos_01', 'alumnos_2', 'alumnos_3',
                              'repetidores', 'repetidores_01',
                              'nvo_ing', 'nvo_ing_01',
                              'docentes', 'grupos',
                              'mujeres', 'hombres',
                              'egresados', 'abandono']
                 if v in df.columns]

    if len(vars_corr) > 2:
        # Asegurar que todas las columnas sean numéricas
        df_corr = df[vars_corr].apply(pd.to_numeric, errors='coerce').fillna(0)
        corr_matrix = df_corr.corr()

        fig, ax = plt.subplots(figsize=(14, 11))
        mask = np.triu(np.ones_like(corr_matrix, dtype=bool), k=1)
        sns.heatmap(corr_matrix, mask=mask, annot=True, fmt='.2f',
                    cmap='coolwarm', center=0, ax=ax,
                    square=True, linewidths=0.5,
                    annot_kws={'size': 9},
                    vmin=-1, vmax=1,
                    cbar_kws={'label': 'Correlación', 'shrink': 0.8})
        ax.set_title('Mapa de Calor: Correlaciones entre Variables y Abandono',
                     fontsize=15, fontweight='bold', pad=20)
        ax.tick_params(axis='both', labelsize=10)
        plt.tight_layout()
        plt.savefig(GRAFICAS_DIR / '8g_correlaciones.png', dpi=150, bbox_inches='tight')
        plt.close()

    print(f"\n   ✅ Todas las visualizaciones guardadas en: {GRAFICAS_DIR}")


# ============================================================================
# PASO 9: FUNCIÓN DE PREDICCIÓN
# ============================================================================
def crear_funcion_prediccion(mejor_modelo, todas_features, scaler,
                              label_encoders, features_numericas):
    """
    Crea y retorna una función de predicción que recibe datos de un estudiante
    o plantel y devuelve probabilidad de abandono, nivel de riesgo y factores.
    """
    print("\n🔮 PASO 9: Creando función de predicción...")
    print("-" * 50)

    # Obtener importancias de features si están disponibles
    if hasattr(mejor_modelo, 'feature_importances_'):
        importancias = dict(zip(todas_features, mejor_modelo.feature_importances_))
    elif hasattr(mejor_modelo, 'coef_'):
        importancias = dict(zip(todas_features, np.abs(mejor_modelo.coef_[0])))
    else:
        importancias = {f: 0 for f in todas_features}

    def predecir_abandono(datos_estudiante):
        """
        Predice el riesgo de abandono para un estudiante o plantel.

        Parámetros:
        -----------
        datos_estudiante : dict
            Diccionario con los valores de las variables del estudiante/plantel.
            Ejemplo: {'alumnos_01': 150, 'repetidores': 10, 'docentes': 20, ...}

        Retorna:
        --------
        dict con:
            - probabilidad: float (0-1)
            - nivel_riesgo: str ('Bajo', 'Medio', 'Alto')
            - factores_riesgo: list de los factores más influyentes
            - recomendaciones: list de intervenciones sugeridas
        """
        # Preparar datos de entrada
        datos_input = []
        for feature in todas_features:
            valor = datos_estudiante.get(feature, 0)

            # Codificar si es categórica
            if feature in label_encoders:
                le = label_encoders[feature]
                if str(valor) in le.classes_:
                    valor = le.transform([str(valor)])[0]
                else:
                    valor = 0  # Valor por defecto si categoría desconocida

            datos_input.append(float(valor))

        datos_input = np.array(datos_input).reshape(1, -1)

        # Escalar variables numéricas
        n_num = len(features_numericas)
        datos_input[:, :n_num] = scaler.transform(datos_input[:, :n_num])

        # Predecir
        probabilidad = mejor_modelo.predict_proba(datos_input)[0][1]

        # Determinar nivel de riesgo
        if probabilidad < 0.30:
            nivel_riesgo = "🟢 BAJO"
            color = "verde"
        elif probabilidad < 0.60:
            nivel_riesgo = "🟡 MEDIO"
            color = "amarillo"
        else:
            nivel_riesgo = "🔴 ALTO"
            color = "rojo"

        # Identificar factores de riesgo más influyentes
        factores = sorted(importancias.items(), key=lambda x: x[1], reverse=True)
        top_factores = [(f, round(imp, 4)) for f, imp in factores[:5]]

        # Recomendaciones basadas en los datos
        recomendaciones = []
        if datos_estudiante.get('repetidores', 0) > 0:
            recomendaciones.append("📘 Implementar programa de tutorías para repetidores")
        if datos_estudiante.get('docentes', 0) < 5:
            recomendaciones.append("👨‍🏫 Incrementar plantilla docente")
        if probabilidad >= 0.60:
            recomendaciones.append("🚨 Activar protocolo de intervención temprana")
            recomendaciones.append("📞 Contactar a tutores/padres de familia")
        if probabilidad >= 0.30:
            recomendaciones.append("📋 Realizar seguimiento académico mensual")
        if datos_estudiante.get('nvo_ing', 0) == 0 and datos_estudiante.get('alumnos_01', 0) > 0:
            recomendaciones.append("🔍 Revisar proceso de nuevo ingreso")

        return {
            'probabilidad': round(probabilidad, 4),
            'probabilidad_porcentaje': f"{probabilidad * 100:.2f}%",
            'nivel_riesgo': nivel_riesgo,
            'factores_riesgo': top_factores,
            'recomendaciones': recomendaciones
        }

    # Demostración de la función
    print("\n   🧪 Demostración de la función de predicción:")
    print("   " + "─" * 45)

    ejemplo_alto = {
        'alumnos_01': 200, 'alumnos_2': 0, 'alumnos_3': 0,
        'repetidores': 50, 'repetidores_01': 30,
        'nvo_ing': 100, 'nvo_ing_01': 80,
        'docentes': 3, 'grupos': 2,
        'mujeres': 100, 'hombres': 100,
        'modalidad': 'ESCOLARIZADA', 'control': 'PUBLICO', 'nivel': 'MEDIO SUPERIOR'
    }

    resultado = predecir_abandono(ejemplo_alto)
    print(f"   Ejemplo (plantel con indicadores de riesgo):")
    print(f"      Probabilidad de abandono: {resultado['probabilidad_porcentaje']}")
    print(f"      Nivel de riesgo: {resultado['nivel_riesgo']}")
    print(f"      Top factores de riesgo:")
    for factor, imp in resultado['factores_riesgo'][:3]:
        print(f"         • {factor}: {imp}")
    print(f"      Recomendaciones:")
    for rec in resultado['recomendaciones']:
        print(f"         {rec}")

    print(f"\n   ✅ Función de predicción creada exitosamente")

    return predecir_abandono


# ============================================================================
# PASO 10: GUARDAR MODELO
# ============================================================================
def guardar_modelo(modelos, mejor_modelo_nombre, scaler, label_encoders,
                    todas_features, features_numericas):
    """
    Guarda el mejor modelo entrenado y los objetos de preprocesamiento.
    """
    print("\n💾 PASO 10: Guardando modelo...")
    print("-" * 50)

    mejor_modelo = modelos[mejor_modelo_nombre]

    # Guardar modelo
    modelo_path = MODELOS_DIR / 'mejor_modelo_abandono.joblib'
    joblib.dump(mejor_modelo, modelo_path)
    print(f"   Modelo guardado en: {modelo_path}")

    # Guardar scaler
    scaler_path = MODELOS_DIR / 'scaler.joblib'
    joblib.dump(scaler, scaler_path)
    print(f"   Scaler guardado en: {scaler_path}")

    # Guardar label encoders
    le_path = MODELOS_DIR / 'label_encoders.joblib'
    joblib.dump(label_encoders, le_path)
    print(f"   Label encoders guardados en: {le_path}")

    # Guardar metadatos del modelo
    metadata = {
        'nombre_modelo': mejor_modelo_nombre,
        'todas_features': todas_features,
        'features_numericas': features_numericas,
        'fecha_entrenamiento': time.strftime('%Y-%m-%d %H:%M:%S'),
    }
    metadata_path = MODELOS_DIR / 'modelo_metadata.joblib'
    joblib.dump(metadata, metadata_path)
    print(f"   Metadatos guardados en: {metadata_path}")

    print(f"\n   ✅ Todos los archivos del modelo guardados en: {MODELOS_DIR}")

    return mejor_modelo


# ============================================================================
# PASO 11: RESUMEN EJECUTIVO
# ============================================================================
def generar_resumen_ejecutivo(tasa_abandono, resultados, mejor_modelo_nombre,
                               modelos, todas_features):
    """
    Genera y muestra un resumen ejecutivo completo del análisis.
    """
    print("\n" + "=" * 70)
    print("   📋 RESUMEN EJECUTIVO - PREDICCIÓN DE ABANDONO ESCOLAR")
    print("=" * 70)

    mejor_auc = resultados[mejor_modelo_nombre]['auc_roc']
    mejor_f1 = resultados[mejor_modelo_nombre]['f1_score']
    mejor_recall = resultados[mejor_modelo_nombre]['recall']

    # Obtener top 3 factores de riesgo
    mejor_modelo = modelos[mejor_modelo_nombre]
    if hasattr(mejor_modelo, 'feature_importances_'):
        importancias = dict(zip(todas_features, mejor_modelo.feature_importances_))
    elif hasattr(mejor_modelo, 'coef_'):
        importancias = dict(zip(todas_features, np.abs(mejor_modelo.coef_[0])))
    else:
        importancias = {}

    top_3_factores = sorted(importancias.items(), key=lambda x: x[1], reverse=True)[:3]

    print(f"""
   ┌──────────────────────────────────────────────────────────────┐
   │                                                              │
   │  📊 TASA DE ABANDONO ENCONTRADA:  {tasa_abandono:>6.2f}%                   │
   │                                                              │
   │  🏆 MEJOR MODELO:  {mejor_modelo_nombre:<30s}          │
   │     • AUC-ROC:   {mejor_auc:.4f}                                     │
   │     • F1-Score:  {mejor_f1:.4f}                                     │
   │     • Recall:    {mejor_recall:.4f}                                     │
   │                                                              │
   │  🔑 TOP 3 FACTORES DE RIESGO:                                │""")

    for i, (factor, imp) in enumerate(top_3_factores, 1):
        print(f"   │     {i}. {factor:<25s} (importancia: {imp:.4f})     │")

    print(f"""   │                                                              │
   │  📌 COMPARACIÓN DE MODELOS:                                  │""")

    for nombre, res in resultados.items():
        marcador = "⭐" if nombre == mejor_modelo_nombre else "  "
        print(f"   │   {marcador} {nombre:<25s} AUC={res['auc_roc']:.4f}  F1={res['f1_score']:.4f}  │")

    print(f"""   │                                                              │
   └──────────────────────────────────────────────────────────────┘

   📝 RECOMENDACIONES DE INTERVENCIÓN:
   ────────────────────────────────────
   1. 🎯 DETECCIÓN TEMPRANA: Implementar un sistema de alerta usando
      este modelo para identificar planteles/estudiantes en riesgo
      al inicio de cada ciclo escolar.

   2. 📘 TUTORÍAS FOCALIZADAS: Priorizar programas de tutoría en
      planteles con alta tasa de repetidores (factor clave de abandono).

   3. 👨‍🏫 FORTALECIMIENTO DOCENTE: Aumentar la plantilla docente en
      planteles con ratio alumno/docente elevado.

   4. 📊 MONITOREO CONTINUO: Establecer dashboards de seguimiento
      mensual con las variables más predictivas identificadas.

   5. 🤝 VINCULACIÓN FAMILIAR: Activar protocolos de comunicación
      con familias de estudiantes en riesgo medio-alto.

   6. 💰 BECAS Y APOYOS: Focalizar programas de becas y apoyos
      económicos en las entidades con mayor tasa de abandono.
    """)

    # Guardar resumen en archivo de texto
    resumen_path = OUTPUT_DIR / 'resumen_ejecutivo.txt'
    with open(resumen_path, 'w', encoding='utf-8') as f:
        f.write("=" * 70 + "\n")
        f.write("   RESUMEN EJECUTIVO - PREDICCIÓN DE ABANDONO ESCOLAR\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"Fecha: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"Tasa de abandono encontrada: {tasa_abandono:.2f}%\n")
        f.write(f"Mejor modelo: {mejor_modelo_nombre}\n")
        f.write(f"AUC-ROC: {mejor_auc:.4f}\n")
        f.write(f"F1-Score: {mejor_f1:.4f}\n")
        f.write(f"Recall: {mejor_recall:.4f}\n\n")
        f.write("Top 3 Factores de Riesgo:\n")
        for i, (factor, imp) in enumerate(top_3_factores, 1):
            f.write(f"  {i}. {factor} (importancia: {imp:.4f})\n")
        f.write("\nResultados por modelo:\n")
        for nombre, res in resultados.items():
            f.write(f"  {nombre}: AUC={res['auc_roc']:.4f}, F1={res['f1_score']:.4f}, "
                   f"Acc={res['accuracy']:.4f}, Rec={res['recall']:.4f}\n")

    print(f"   💾 Resumen guardado en: {resumen_path}")


# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================
def main():
    """
    Función principal que orquesta todo el pipeline de predicción.
    """
    inicio = time.time()

    # Paso 1: Cargar datos
    df = cargar_dataset()

    # Paso 2: Crear variable objetivo
    df, tasa_abandono = crear_variable_abandono(df)

    # Paso 3: Seleccionar features
    features_numericas, features_categoricas = seleccionar_features(df)

    # Paso 4: Preprocesamiento
    X, y, scaler, label_encoders, todas_features = preprocesar_datos(
        df, features_numericas, features_categoricas
    )

    # Paso 5: División de datos
    X_train, X_test, y_train, y_test = dividir_datos(X, y)

    # Paso 6: Entrenamiento
    modelos = entrenar_modelos(X_train, y_train)

    # Paso 7: Evaluación
    resultados, mejor_modelo_nombre = evaluar_modelos(modelos, X_test, y_test)

    # Paso 8: Visualizaciones
    generar_visualizaciones(df, resultados, modelos, mejor_modelo_nombre,
                            todas_features, X_test, y_test)

    # Paso 9: Función de predicción
    predecir_abandono = crear_funcion_prediccion(
        modelos[mejor_modelo_nombre], todas_features, scaler,
        label_encoders, features_numericas
    )

    # Paso 10: Guardar modelo
    mejor_modelo = guardar_modelo(modelos, mejor_modelo_nombre, scaler,
                                   label_encoders, todas_features, features_numericas)

    # Paso 11: Resumen ejecutivo
    generar_resumen_ejecutivo(tasa_abandono, resultados, mejor_modelo_nombre,
                              modelos, todas_features)

    # Tiempo total
    tiempo_total = time.time() - inicio
    print(f"\n⏱️  Tiempo total de ejecución: {tiempo_total:.1f} segundos")
    print(f"\n📁 Todos los resultados guardados en: {OUTPUT_DIR}")
    print("\n" + "=" * 70)
    print("   ✅ PIPELINE DE PREDICCIÓN COMPLETADO EXITOSAMENTE")
    print("=" * 70)

    return modelos, resultados, predecir_abandono


# ============================================================================
# EJECUCIÓN
# ============================================================================
if __name__ == '__main__':
    modelos, resultados, predecir_abandono = main()
