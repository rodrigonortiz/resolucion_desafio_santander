# Respuestas desafio Santander Tecnologia
En este repo se responderan a todas las preguntas y se adjuntaran los archivos .sql y .py asociados a cada planteo


### Pregunta 1

Tomando como base la tabla de <strong> users_sessions </strong> proveniente de BigQuery considero que una opcion sencilla y practica seria crear las vistas que nos piden <strong> first_user_log </strong> y <strong> daily_users_activity </strong> dentro de BigQuery, ya que nos permite crearlas de una forma secilla y poder consultar las mismas facilmente mediante sentencias SQL estandar y con el plus de que tenemos muchas posibilidades de integrarlas con casi todos los sistemas de reporteria de BI ej: PowerBi, Tableu, Looker, y mas.

En el caso de que nuestro modelo deba ser creado en otro ecosistema diferente al de Google y tengamos que hacer una migracion de la tabla de Bigquery hacia otro lugar recomiendo la siguiente ruta:

● Creamos un claster de spark en DataProc, usaremos el conector que nos brinda acceso a Bigquery y con pyspark haremos las agrupaciones y transformaciones necesarias para crear los dataframes que representaran a las tablas first_user_log y daily_users_activity (esta ultima la particionaremos por dia).

● Enviaremos nuestros dataframes creados a un bucket de Cloud Storage y los guardaremos en formato .parquet.

● Ya fuera del ecosistema de Google nos conectaremos al bucket de Cloud Storage desde Nifi con su correspondiente conector, y en este punto ya estamos listos para ingestar nuestros parquet y enviarlos al lugar que deseemos.

<br><br/>

### Diagrama del esquema propuesto:

<br><br/>

![Untitled Diagram](https://user-images.githubusercontent.com/87278509/134350546-71049f35-7a99-477e-b9ce-e26cfdccd4bb.jpg)


### Creacion del modelo requerido por banca privada.

A fines practicos de realizar el modelo y mostrar el flujo de SQL lo voy a hacer montando una base de datos local MySQL, en donde crearemos las siguientes tablas:

● <strong> SESSIONS_TABLE </strong>  la cual sera la encargada de emular todos los datos de sesiones que va a contener nuestra tabla en Bigquery.

● <strong> FIRST_USER_LOG </strong> contiene los datos del primer logueo de cada usuario.

● <strong> DAILY_USERS_ACTIVITY </strong> contiene la actividad diaria de cada usuario.
