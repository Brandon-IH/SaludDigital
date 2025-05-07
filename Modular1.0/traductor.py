# PAQUETES
import spacy
import numpy as np
import pandas as pd
import psycopg2
import json
import matplotlib.pyplot as plt
import os
import psycopg2
from sklearn.model_selection import train_test_split
from sklearn.utils.class_weight import compute_class_weight
from sklearn.metrics import classification_report

from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Embedding, Bidirectional, LSTM, Dropout, Dense
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import ReduceLROnPlateau, EarlyStopping
from tensorflow.keras import regularizers  # Regularización L2

# CONEXIÓN A LA BASE DE DATOS (PostgreSQL)
# Obtener la URL de la base de datos desde las variables de entorno en Railway
DATABASE_URL = os.getenv("DATABASE_URL")  # Railway proporciona esta URL

# Conectar a PostgreSQL en Railway
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()


# CREAR TABLA SI NO EXISTE
cur.execute(""" 
    CREATE TABLE IF NOT EXISTS comentarios (
        id SERIAL PRIMARY KEY,
        comentario TEXT,
        sentimiento VARCHAR(20),
        resultado JSONB
    );
""")
conn.commit()

# CARGAR MODELO DE PROCESAMIENTO DE TEXTO (spacy)
nlp = spacy.load("es_dep_news_trf")

def procesamiento_texto(texto):
    """Lematiza y limpia el texto eliminando stopwords y puntuación."""
    doc = nlp(texto.lower())
    tokens = [token.lemma_ for token in doc if not token.is_stop and not token.is_punct]
    return " ".join(tokens)

# CARGAR Y PREPROCESAR DATOS DE ENTRENAMIENTO
df = pd.read_csv('D:/Brandon/Modular1.0/datos_entrenamiento.csv')
comentarios = df['comentario'].tolist()
etiquetas = df['etiqueta'].tolist()

# Preprocesar el texto
texto_procesado = [procesamiento_texto(c) for c in comentarios]

# Dividir en conjunto de entrenamiento y prueba
X_train, X_test, y_train, y_test = train_test_split(
    texto_procesado, etiquetas, stratify=etiquetas, test_size=0.2, random_state=42
)

# Configurar Tokenizer y convertir textos a secuencias
tokenizer = Tokenizer(num_words=5000, oov_token="<OOV>")
tokenizer.fit_on_texts(X_train)
texts_sequences_train = tokenizer.texts_to_sequences(X_train)
texts_sequences_test = tokenizer.texts_to_sequences(X_test)

# Padding a las secuencias (maxlen=15)
sequences_train = pad_sequences(texts_sequences_train, maxlen=15, padding='post')
sequences_test = pad_sequences(texts_sequences_test, maxlen=15, padding='post')

# One-hot encoding de las etiquetas
categorical_train = np.array(pd.get_dummies(y_train))
categorical_test = np.array(pd.get_dummies(y_test))

# Calcular pesos de clase para balancear los datos
class_weights = compute_class_weight('balanced', classes=np.unique(y_train), y=y_train)
weights_dict = dict(enumerate(class_weights))

# DEFINICIÓN DEL MODELO CON AJUSTES PARA REDUCIR SOBREAJUSTE
model = Sequential([
    # Capa de Embedding: salida de dimensión 128.
    Embedding(input_dim=len(tokenizer.word_index) + 1, output_dim=128),
    # Capa LSTM bidireccional con 32 unidades, dropout y recurrent_dropout para mejorar estabilidad.
    Bidirectional(LSTM(32, dropout=0.6, recurrent_dropout=0.3)),
    # Primera capa densa con regularización L2.
    Dense(64, activation="relu", kernel_regularizer=regularizers.l2(0.01)),
    Dropout(0.4),
    # Segunda capa densa con regularización L2.
    Dense(32, activation="relu", kernel_regularizer=regularizers.l2(0.01)),
    # Capa de salida con regularización L2 para mejorar la generalización.
    Dense(3, activation="softmax", kernel_regularizer=regularizers.l2(0.01))
])

model.compile(loss='categorical_crossentropy', optimizer=Adam(learning_rate=0.0005), metrics=['accuracy'])

# Forzar la construcción del modelo especificando la forma de entrada para obtener el resumen completo.
model.build(input_shape=(None, 15))
model.summary()

# Callbacks: ReduceLROnPlateau y EarlyStopping para ajustar el entrenamiento.
reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=3, min_lr=0.00001)
early_stopping = EarlyStopping(monitor='val_loss', patience=3, restore_best_weights=True)

# ENTRENAMIENTO
history = model.fit(
    np.array(sequences_train), categorical_train,
    epochs=20, batch_size=32, verbose=1,
    validation_data=(sequences_test, categorical_test),
    class_weight=weights_dict,
    callbacks=[reduce_lr, early_stopping]
)

# VISUALIZAR LAS CURVAS DE PÉRDIDA
plt.figure(figsize=(10, 5))
plt.plot(history.history['loss'], label='Pérdida entrenamiento')
plt.plot(history.history['val_loss'], label='Pérdida validación')
plt.xlabel('Épocas')
plt.ylabel('Pérdida')
plt.title('Evolución de la pérdida durante el entrenamiento')
plt.legend()
plt.show()

# EVALUACIÓN DEL MODELO EN EL CONJUNTO DE PRUEBA
y_pred = model.predict(sequences_test)
y_pred_classes = np.argmax(y_pred, axis=1)

print("Evaluación del modelo:")
print(classification_report(y_test, y_pred_classes, target_names=["Negativo", "Neutral", "Positivo"]))

# RECUPERAR Y CLASIFICAR COMENTARIOS DESDE LA BASE DE DATOS
cur.execute("SELECT id, comentario FROM comentarios WHERE sentimiento IS NULL;")
comentarios_bd = cur.fetchall()

for id_comentario, texto in comentarios_bd:
    texto_proc = procesamiento_texto(texto)
    texts_sequence = tokenizer.texts_to_sequences([texto_proc])
    sequence = pad_sequences(texts_sequence, maxlen=15, padding='post')
    predict = model.predict(sequence)
    
    resultado = ["Negativo", "Neutral", "Positivo"][np.argmax(predict)]
    resultado_json = json.dumps({
        "Negativo": float(predict[0][0]),
        "Neutral": float(predict[0][1]),
        "Positivo": float(predict[0][2])
    })
    
    # Actualizar la base de datos con el sentimiento clasificado.
    cur.execute(""" 
        UPDATE comentarios 
        SET sentimiento = %s, resultado = %s 
        WHERE id = %s;
    """, (resultado, resultado_json, id_comentario))
    conn.commit()
    print(f"Comentario ID {id_comentario}: {texto} -> Sentimiento: {resultado}")

# CERRAR CONEXIÓN A LA BASE DE DATOS
cur.close()
conn.close()
