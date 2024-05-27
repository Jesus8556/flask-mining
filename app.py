from flask import Flask, request, jsonify
import requests
import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)

# Función para obtener datos de la API de películas
def obtener_peliculas():
    url_peliculas = "http://localhost:5283/api/pelicula"
    response = requests.get(url_peliculas)
    if response.status_code == 200:
        return json.loads(response.text)
    else:
        return None

# Función para obtener datos de la API de géneros
def obtener_generos():
    url_generos = "http://localhost:5283/api/genero"
    response = requests.get(url_generos)
    if response.status_code == 200:
        return json.loads(response.text)
    else:
        return None

# Función para obtener datos de la API de calificaciones
def obtener_calificaciones():
    url_calificaciones = "http://localhost:5283/api/rating"
    response = requests.get(url_calificaciones)
    if response.status_code == 200:
        return json.loads(response.text)
    else:
        return None

# Codificación de los géneros de las películas usando one-hot encoding
def codificar_generos(peliculas, generos):
    genero_dict = {genero['nombre']: i for i, genero in enumerate(generos)}
    for pelicula in peliculas:
        generos_pelicula = pelicula['generos']
        generos_encoded = [0] * len(generos)
        for genero in generos_pelicula:
            genero_nombre = genero['nombre']
            if genero_nombre in genero_dict:
                genero_index = genero_dict[genero_nombre]
                generos_encoded[genero_index] = 1
        pelicula['generos_encoded'] = generos_encoded

# Función para calcular la similitud entre películas
def calcular_similitud_entre_peliculas(pelicula_1, pelicula_2):
    return cosine_similarity([pelicula_1], [pelicula_2])[0][0]

# Función para recomendar películas similares a una película dada
def recomendar_peliculas_similares(pelicula_referencia, peliculas, calificaciones, usuario_id, n=5):
    similitudes = []
    for otra_pelicula in peliculas:
        if otra_pelicula['id'] != pelicula_referencia['id']:  # Excluir la película de referencia
            similitud = calcular_similitud_entre_peliculas(pelicula_referencia['generos_encoded'], otra_pelicula['generos_encoded'])
            similitudes.append((otra_pelicula, similitud))
    similitudes.sort(key=lambda x: x[1], reverse=True)

    # Filtrar películas ya calificadas por el usuario
    peliculas_calificadas_por_usuario = {calificacion['peliculaId'] for calificacion in calificaciones if calificacion['usuarioId'] == usuario_id}
    peliculas_recomendadas = []
    for pelicula, similitud in similitudes:
        if pelicula['id'] not in peliculas_calificadas_por_usuario:
            peliculas_recomendadas.append((pelicula, similitud))
            if len(peliculas_recomendadas) == n:
                break

    return peliculas_recomendadas

@app.route('/recomendar/<usuario_id>', methods=['GET'])
def recomendar_peliculas(usuario_id):
    # Obtener datos de las APIs
    peliculas = obtener_peliculas()
    generos = obtener_generos()
    calificaciones = obtener_calificaciones()

    if peliculas and generos and calificaciones:
        # Codificar los géneros de las películas utilizando one-hot encoding
        codificar_generos(peliculas, generos)

        # Recomendar películas similares al usuario
        peliculas_similares = []
        peliculas_recomendadas_set = set()
        for pelicula_referencia in peliculas:
            recomendaciones = recomendar_peliculas_similares(pelicula_referencia, peliculas, calificaciones, usuario_id)
            for recomendacion, _ in recomendaciones:
                if recomendacion['id'] not in peliculas_recomendadas_set:
                    peliculas_similares.append(recomendacion)
                    peliculas_recomendadas_set.add(recomendacion['id'])
        
        # Formatear las recomendaciones como JSON con título y URL de video
        peliculas_json = []
        for pelicula in peliculas_similares:
            pelicula_data = {
                'titulo': pelicula['titulo'],
                'videoUrl': pelicula['videoUrl']
            }
            peliculas_json.append(pelicula_data)

        return jsonify({'peliculas_recomendadas': peliculas_json})
    else:
        return jsonify({'error': 'No se pudieron obtener datos de las APIs'})

if __name__ == '__main__':
    app.run(debug=True,port=4000)
