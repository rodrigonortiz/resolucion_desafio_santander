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


### Ejercicio 1

### Creacion del modelo requerido por banca privada.

A fines practicos de realizar el modelo y mostrar el flujo de SQL lo voy a hacer montando una base de datos local MySQL en donde crearemos las siguientes tablas:

● <strong> SESSIONS_TABLE </strong>  la cual sera la encargada de emular todos los datos de sesiones que va a contener nuestra tabla en Bigquery.

● <strong> FIRST_USER_LOG </strong> contiene los datos del primer logueo de cada usuario.

● <strong> DAILY_USERS_ACTIVITY </strong> contiene la actividad diaria de cada usuario.

Nuestro diagrama entidad-relacion quedaria de la siguiente manera:


![image](https://user-images.githubusercontent.com/87278509/134666751-afdc36f2-e4f5-4e73-ba69-1e1177c71f5b.png)


### Ejercicio 2

#### Creamos la primera tabla llamada SESSIONS_TABLE, la cual va a tener la informacion cruda sobre los usuarios y sus sesiones, la misma tendra como PRIMARY KEY los campos <strong>USER_ID</strong> y <strong>SESSION_ID</strong>

<code> 
  CREATE TABLE SESSIONS_TABLE (
    USER_ID  NUMERIC(38,0) NOT NULL,
    SESSION_ID NUMERIC(38,0) NOT NULL,
    SEGMENT_ID NUMERIC(10,0),
    SEGMENT_DESCRIPTION VARCHAR(100),
    USER_CITY VARCHAR(50),
    SERVER_TIME TIMESTAMP,
    DEVICE_BROWSER VARCHAR(10),
    DEVICE_OS VARCHAR(5),
    DEVICE_MOBILE VARCHAR(10),
    TIME_SPENT NUMERIC(38,0),
    EVENT_ID NUMERIC(38,0),
    EVENT_DESCRIPTION VARCHAR(50),
    CRASH_DETECTION VARCHAR(100),
    PRIMARY KEY (USER_ID, SESSION_ID)
);
</code>

<br></br>

#### Seguido creamos la tabla para mostrar primer logueo de cada usuario con los mismos PRIMARY KEY que SESSIONS_TABLE

<code>
  CREATE TABLE  FIRST_USER_LOG (
    USER_ID NUMERIC(38,0) NOT NULL,
    SESSION_ID NUMERIC(38,0) NOT NULL,
    FIRST_DATE TIMESTAMP,
    PRIMARY KEY (USER_ID, SESSION_ID),
    FOREIGN KEY (USER_ID, SESSION_ID) REFERENCES SESSIONS_TABLE(USER_ID, SESSION_ID) ON DELETE CASCADE
);
</code>


<br></br>

#### Por ultimo creamos la tabla de actividad diaria para cada usuario

<code>
  CREATE TABLE DAILY_USERS_ACTIVITY (
    ACTIVITY_DATE TIMESTAMP,
    USER_ID NUMERIC(38) NOT NULL,
    SESSION_ID NUMERIC(38,0) NOT NULL,
    EVENT_ID NUMERIC(38,0),
    TIME_SPENT NUMERIC(38,0),
    PRIMARY KEY (USER_ID, SESSION_ID),
    FOREIGN KEY (USER_ID, SESSION_ID) REFERENCES SESSIONS_TABLE(USER_ID, SESSION_ID) ON DELETE CASCADE
);
</code>

<br></br>

#### Ahora generamos los insert correspondientes para poblar las tablas:
Aclaracion: Para poblar la tabla SESSIONS_USER se insertaran multiples registros, el codigo esta adjunto en el repo.

<br></br>
FIRST_USER_LOG se construira agrupando por cada usuario y extrayendo la minima fecha de logueo.

<code>
INSERT INTO FIRST_USER_LOG (USER_ID, SESSION_ID, FIRST_DATE)
SELECT A.USER_ID, A.SESSION_ID, B.FECHA_PRIMER_LOGUEO 
FROM SESSIONS_TABLE A
INNER JOIN 
(
SELECT 
    USER_ID, MIN(SERVER_TIME) AS FECHA_PRIMER_LOGUEO FROM SESSIONS_TABLE WHERE EVENT_ID = 01
GROUP BY USER_ID
) B
ON A.SERVER_TIME = B.FECHA_PRIMER_LOGUEO
</code>  
  
<br></br>

En DAILY_USERS_ACTIVITY se agrupara por dia, usuario, sesion y evento y se sumara su TIME_SPENT.

<code>
INSERT INTO DAILY_USERS_ACTIVITY (ACTIVITY_DATE, USER_ID, SESSION_ID, EVENT_ID, TIME_SPENT)
SELECT DATE(SERVER_TIME) AS DIA, USER_ID, SESSION_ID, EVENT_ID,  SUM(TIME_SPENT) AS TIME_SPENT
FROM SESSIONS_TABLE
GROUP BY DIA, USER_ID, SESSION_ID, EVENT_ID
</code> 

<br></br>

### Ejercicio 3

Para obtener el KPI de retención de clientes para los 10 clientes que mas veces se hayan logueado en el último mes calcularemos la diferencia entre fechas de logueo para cada usuario y nos quedaremos con aquellos en los que esta diferencia sea >=1 lo que nos dice que ha pasado un dia desde el logueo anterior filtrando aquellas sesiones con time_spent >= 300, luego uniremos con join este resultado con la lista de top 10 clientes que mas se loguearon, por ultimo para calular el kpi en porcentaje queda la siguiente operacion: cantidad de usuarios frecuentes / cantidad de usuarios top 10 que se loguean.

<code>
SELECT SUM(COALESCE(freq_users.FREQUENT_USER,0)) / COUNT(*) AS PORCENTAJE_FREC_TOP 
FROM 
(SELECT USER_ID, COUNT(*) AS CANT FROM SESSIONS_TABLE WHERE EVENT_ID = 01
GROUP BY USER_ID ORDER BY CANT DESC LIMIT 10) top_users
LEFT JOIN 
(SELECT DISTINCT(b.USER_ID) as USER_ID, 1 AS FREQUENT_USER
FROM
(
SELECT t.USER_ID,
t.SERVER_TIME, 
DATEDIFF(t.SERVER_TIME, LAG(t.SERVER_TIME, 1) OVER (PARTITION BY t.USER_ID  ORDER BY t.SERVER_TIME )) as DIFF
FROM SESSIONS_TABLE t 
WHERE t.EVENT_ID <> 01 
AND TIME_SPENT >= 300
) b
WHERE b.DIFF >=1)  freq_users
on top_users.USER_ID = freq_users.USER_ID
</code> 
  
 <br></br>
  
  ### Pregunta 2
  
  En una ingesta con spark cosidero necesario prestar atencion a los siguientes parametros:
  
  ● <strong> num-executors </strong>: Este parámetro se usa para establecer el número total de procesos executor usados por el job de Spark, si no está configurado solo arrancaran una poca cantidad de procesos executor de forma predeterminada y la velocidad de ejecución del proceso puede ser bastante lenta.
  
   ● <strong> executor-memory </strong>: Se utiliza para configurar la memoria de cada proceso executor, esta memoria es determinante en el rendimiento del proceso y si es insuficiente nos va a dar errores de JVM.
  
  ● <strong> executor-cores </strong>: Se utiliza para establecer el número de núcleos para cada proceso executor. Este parámetro determina la capacidad de cada proceso executor para ejecutar tareas en paralelo.
  
  #### Formato de compresion recomendado:
  
  Parquet es una opcion que elegiria ya que nos permite ser flexibles a la hora de agregar campos a nuestro set de datos a futuro, es una buena opcion si los datos los consumiran los data scientist del equipo ya que las consultas al mismo son rapidas, otra cosa a tener en cuenta es que nos permite particionar los datos por ejemple para nuestro caso seria ideal que los .parquet de la actividad de cada usuario esten particionados en fechas con un campo cutoff_date.
  
 ### Pregunta 3
  
  #### Implementaciones que pueden mejorar la calidad de nuestros datos:
  
  ● <strong>Identificar los requisitos comerciales</strong>: Diseñar el modelo de datos en conjunto con el area en particular que lo requiere, esto nos ayudara a que el alcance del proyecto este bien definido de antemano, documentado y entendido sobre los datos que tenemos que construir.
  
  ● <strong>Validar las fuentes de datos</strong>: Verificar que el tipo de datos de la tabla y las columnas cumplan con las especificaciones del modelo de datos, chequear si existen datos duplicados o errores en claves importates que puedan repercutir en el futuro del proceso de ETL.
  
  ● <strong>Diseñar casos de prueba (qa)</strong>: IMPORTANTISIMO, nuestro codigo se va a ver mejor modularizado y ademas esto va a ayudarnos a que podamos crear casos de prueba para transformaciones que tengan cierta complejidad, por ejemplo en python hay frameworks que pueden ayudarnos con esto.
  
  ● <strong>Chequear el destino final de los datos</strong>: Es importante hacer un recuento de la cantidad de datos en nuestra tabla destino, es necesario realizar agrupaciones y agregaciones sobre los mismos para chequear que los valores sean los correctos en cada campo, cada periodo de fechas, etc.
  

  ### PREGUNTAS:

  #### En qué requerimiento implementarías una cola de mensajes en una solución orientada a datos? Que lenguaje utilizarías y porque? 
  
  ● Una cola de mensajes es una solucion para un desarrollo cuando tenemos que trabajar con datos en real time, va muy de la mano con el concepto de topico, pueden existir muchos flujos de datos que vengan al mismo tiempo pero en topicos diferentes de acuerdo a la tematica de cada uno, por ejemplo tenemos que trabajar con datos en tiempo real sobre transacciones de tarjeta de debito y credito que los usuarios del banco estan realizando en todo momento, en un topico pondriamos transacciones de debito y en otro las de credito, asi podemos diferenciar los dos flujos de datos y moverlos en canalizaciones diferentes, la tecnologia que prefiero es KAFKA ya que contiene un API para python muy sencillo de usar, y como todo en python, es facil de aprender.
  
 #### Que experiencia posees sobre py spark o spark scala? Contar breves experiencias, en caso de contar experiencia con otro framework de procesamiento distribuido, dar detalles también.
  
  ● Actualmente me encuentro trabajando para el banco BBVA en donde realizamos desarrollos en notebooks con pyspark preparando data para alimentar modelos de segmentacion de clientes, mas precisamente hoy me encuentro en el area de kpis no financieros calculando saldos medios de clientes, una vez terminado nuestro notebook lo enviamos al sector en donde personas se encargaran de poner el codigo en produccion mediante jobs en una herramienta llamada scaffolder previa validacion QA.
  
  #### Qué funcionalidad podrías expandir desde el area de ingeniería de datos con una API y arquitectónicamente como lo modelarías?
  
  ● Podriamos construir una API que se encarge de disponibilizar los datos de una forma mas sencilla y rapida al area que lo desee, actualmente trabajamos creando pipelines de datos, que parte de una fuente y se canalizan en un proceso de ETL para luego depositar los mismos en un datawarehouse o aplicaciones de reporting de BI, como lo muestra el siguiente esquema:
  
  ![image](https://user-images.githubusercontent.com/87278509/134449858-cd20e6f9-33c5-48df-ab0c-9fa815cdbf2d.png)

  Pero hay una parte en la cual se pueden crear servicios de datos reutilizables o API de datos, que acceden, transforman y entregan datos analíticos, y realizan estas lecturas  pesadas de forma rápida, segura y con alto rendimiento. Estos servicios de datos pueden fusionarse en una capa de datos común que puede admitir una amplia gama de casos de uso de aplicaciones y análisis, lo voy a mostrar en el siguiente esquema:
  
  ![image](https://user-images.githubusercontent.com/87278509/134450340-997d22ce-e035-4c15-acfa-df6a1c2150ae.png)

  Esto ofrecería los siguientes beneficios principales: Los ajustes deben aplicarse en una sola capa / entorno en vez de modificar muchos procesos etls dispersos , reduce la sobrecarga y ofrece un único punto de verdad que puede ser utilizado por todo aquel que lo requiera. Tambien aplicaciones pueden conectarse ya que se utiliza formato JSON. Esto es un ejemplo sencillo, prealizar un cambio como este, hay muchos otros factores a tener en cuenta, como el volumen de datos, la velocidad de conexión, etc. 
 Esta solución puede no ser tecnicamente viable en todas las situaciones y debe analizarse y discutirse. 
  
