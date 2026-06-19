# Ticket Reservation API
Il servizio fornito da questa app è la prenotazione di biglietti per un teatro. L'utente può prenotare, modificare la sua prenotazione o cancellarla. È sviluppato mediante Flask in linguaggio Python.
## Link di deploy
API: [progettobackendppm-production.up.railway.app](https://progettobackendppm-production.up.railway.app)

Client: [client-progettobackendppm-production.up.railway.app](https://client-progettobackendppm-production-84cd.up.railway.app)

# Setup locale dell'API
Clonare il repository e installare le dipendenze. Le dipendenze sono elencate nel file `requirements.txt`.

Assicurarsi di impostare in un file `.env` le seguenti variabili:

  - `SECRET_KEY`: chiave usata per fare l'hash dei cookie.
  - `JWT_SECRET_KEY`: chiave usata per fare l'hash dei token di autenticazione.
  - `DATABASE_URL`: url del database. È presente un piccolo database pre-popolato nel progetto: per usarlo impostare la variabile `= sqlite:///instance/database.db`.
  - `PORT`: porta sulla quale il server Flask deve mettersi in ascolto. Di default è stata impostata a `5050`.

L'app può essere avviata da terminale con `python app.py`. Adesso il server sarà in esecuzione su localhost.

# Setup locale del Client per l'avvio
Nel file `api_base_url.js`, impostare la variabile `API_BASE_URL` all'URL dell'API. Con il database del repo usare: `http://localhost:<port>`

Avviare manualmente il file `index.html`, si aprirà la home page del progetto. Da essa sarà possibile navigare nell'app, quindi accedere a tutti i servizi.

# Struttura del progetto
`/app`: cartella dell'API
 - `/auth`: contiene il Blueprint delle routes per la registrazione d nuovi utenti e per l'autenticazione, necessaria per poter accedere al servizio biglietti.
 - `/models`: contiene tutti i modelli del db dell'app. Nota: All'interno dell'app compare spesso la parola "Event", essa si riferisce o ad uno Showing o ad uno Scheduling (vedi models). È semplicemente una scelta di design.
 - `/ticket_service_spi`: contiene il Blueprint delle routes di tutti i servizi offerti, dalla stampa a schermo degli eventi disponibili, alla creazione. modifica e cancellazione delle prenotazioni
 - `/app.py`: file contenente l'inizializzazione dell'app e tutto il codice utile all'avvio.
 - `/db.py`: file contenente l'inizializzazione del db con tanto di metodo utile per la conversione del risultato di una select in JSON.

`/templates`: cartella che contiene alcuni file html con tanto di codice js per permettere l'utilizzo del sito mediante una semplice interfaccia grafica. Ci sono la home page (index.html), la pagina del login e la pagina della registrazione, oltre che:
 - `/adminDashboard.html`: pagina in cui l'admin può inserire nuovi show schedulabili e nuove schedulazioni per show esistenti nella tabella Showing.
 - `/userDashboard.html`: pagina per l'erogazione dei servizi al cliente. Il cliente può vedere tutti gli eventi futuri con tanto di posti rimanenti, creare, modificare o cancellare una prenotazione.

# Il Database

### User
Rappresenta un utente registrato, l'admin è identificato da un flag is_admin

Colonna  |   Tipo    |  Descrizione  |
---------|-----------|---------------|
id       |  Integer  | Id dell'utente (chiave primaria) |
username |  String   | Username dell'utente  |
password_hash  |  String  | Password dell'utente hashata  |
is_admin |  Bool  | Parametro per indicare se l'utente è admin o no  |

### Showing
Rappresenta uno spettacolo che è possibile schedulare
Colonna  |   Tipo    |  Descrizione  |
---------|-----------|---------------|
id       |  Integer  | Id dello spettacolo (chiave primaria) |
title |  String   | Titolo dello spettacolo  |
description  |  String  | Una breve descrizione introduttiva  |
price |  Integer  | Quanto costa il biglietto  |

### Scheduling
Rappresenta la programmazione di uno spettacolo in una certa data ad certa ora. Uno spettacolo infatti può essere riproposto più volte anche a distanza di molto tempo. Nota: il numero massimo di posti impostabili per totalSeats è 300.
Colonna  |   Tipo    |  Descrizione  |
---------|-----------|---------------|
id       |  Integer  | Id dello scheduling (chiave primaria) |
showId |  Integer   | Id dello show schedulato (chiave esterna verso Showing.id)  |
date  |  Date  | La data in cui si terrà  |
time |  Time  | L'ora di inizio  |
totalSeats | Integer | Il massimo numero di posti prenotabili |

### Reservation
Rappresenta la prenotazione che viene creata dall'utente per un preciso scheduling. Sarà chiesto anche di inserire il numero di posto desiderato (Per semplicità il numero di posto è un semplice numero e non un numero di fila tipo 2A). 
Colonna  |   Tipo    |  Descrizione  |
---------|-----------|---------------|
id       |  Integer  | Id della prenotazione (chiave primaria) |
userId |  Integer   | Id dell'utente proprietario della prenotazione (chiave esterna verso User.id)  |
schedulingId  |  Integer  | Id dello scheduling per cui si è effettuata la prenotazione (chiave esterna verso Scheduling.id)  |
seatNumber |  Integer  | Il numero del posto prenotato  |

# Documentazione dell'API
`Note per l'utilizzo:`
 - `Il database` è prepopolato, basta aprire il file database.db. È importante segnalare che al momento dell'apertura dell'app alcune schedulazioni potrebbero non essere più disponibili: è presente una funzione di controllo per cui non è possibile prenotare eventi passati.
 - Non è possibile avere più di due admin. Le credenziali dell'admin sono le seguenti: `username: admin` e `password: admin`.
 - Le credenziali di ogni utente già registrato sono omonime. Es: `username: giulio` e `password: giulio`.
 - l'API risponde sempre in formato JSON
 - l'accesso ai servizi è regolato mediante il `JWT`. Periodicamente sarà richiesto di rieseguire il login, anche se non si è fatto il logout.
 - L'unico servizio accessibile `senza autenticazione` è la visualizzazione a schermo nella home page dei futuri spettacoli programmati.

## Autenticazione

### `auth/register`
Permette di registrarsi come utente.

#### POST

**Parametri**:

  - `username`: Nome utente da registrare
  - `password`: Password dell'utente da registrare (verrà salvata dopo aver fatto l'hash)

**Risposte**:

  - `201 CREATED`: Utente creato correttamente
  - `400 BAD REQUEST`: Parametri mancanti o non validi
  - `409 CONFLICT`: Esiste già un utente con quello username

### `auth/login`
Permette di fare il login con username e password.

#### POST

**Parametri:**

  - `username`: Nome dell'utente che vuole fare il login.
  - `password`: Password dell'utente che vuole fare il login.

**Risposte**

- `400 BAD REQUEST`: Parametri mancanti o non validi.
- `401 UNAUTHORIZED`: Username o password sbagliati.
- `200 OK`: Login effettuato. L'API risponde mandando un JSON con l'access token nel campo access_token.

## Servizi

### `api/events`

#### GET
L'unico servizio erogato, anche se in maniera parziale, senza autenticazione. Stampa a schermo tutti i futuri scheduling. Se si è autenticati si possono anche vedere lo schedulingId e il numero di posti rimanenti.

**Parametri**
 - `date`: data di inizio visualizzazione eventi, impostata di default a date.today()

**Risposte**
 - `400 BAD REQUEST`: Formato data errato.
 - `404 NOT FOUND`: Nessun evento previsto.
 - `200 OK`: ritorna il json dei risultati.

#### POST
Azione eseguibile solo dall'admin. Aggiunge uno spettacolo alla lsita degli spettacoli schedulabili.

**Parametri**
 - `title`: titolo.
 - `description`: breve descizione.
 - `price`: prezzo di accesso, per ogni schedulazione dello spettacolo.

**Risposte**
 - `400 BAD REQUEST`: parametri mancanti.
 - `403 FORBIDDEN`: azione respinta perché chi ha tentato di eseguirla non era un admin.
 - `201 CREATED`: Spettacolo aggiunto.

### `api/scheduling`

#### POST
Aggiunge uno scheduling per una certa data e una certa ora di uno degli spettacoli in Showing. Viene anche impostato il numero massimo di posti.

**Parametri**
 - `showId`: l'id dello spettacolo da schedulare.
 - `date`: data svolgimento in formato %Y-%m-%d.
 - `time`: ora esatta in formato %H:%M.
 - `totalSeats`: numero massimo di prenotazioni effettuabili per tale scheduling.

**Risposte**
 - `403 FORBIDDEN`:  azione respinta perché chi ha tentato di eseguirla non era un admin.
 - `404 NOT FOUND`: Si è tentato di schedulare uno spettacolo non presente in Showing.
 - `201 CREATED`: Scheduling creato con successo.

### `api/reservation`

#### GET
Fa vedere all'utente loggato tutte le sue attuali prenotazioni, con tanto di informazioni utili.

**Parametri**
Non ce ne sono, basta che l'utente di loggi e (nell'interfaccia) prema il relativo button.

**Risposte**
 - `403 FORBIDDEN`: l'utente non è loggato.
 - `404 NOT FOUND`: Nessuna prenotazione trovata per l'utente.
 - `200 OK`: risposta ottenuta correttamente.


#### POST
Crea la prenotazione sulla base dell'id di uno scheduling esistente.
**Parametri**
 - `schedulingId`: l'id dello scehduling per cui si vuol creare la prenotazione.
 - `seatNumber`: il numero del posto che si desidera prenotare.

**Risposte**
 - `400 BAD REQUEST`: Il valore del posto da prenotare inserito è negativo o superiore al massimo numero di posti per quello scheduling.
 - `403 FORBIDDEN`: se l'utente non è loggato; Se lo scheduling che si vuol prenotare è passato o è sold-out.
 - `404 NOT FOUND`: lo scheduling che si vuol prenotare non esiste.
 - `409 CONFLICT`: il posto che si vuol prenotare è già prenotato.
 - `201 CREATED`: prenotazione creata con successo.


#### DELETE
Cancella una prenotazione sulla base dell'id di questa. La prenotazione in questione deve appartenere all'utente loggato.

**Parametri**
 - `reservation_id`: l'id della prenotazione da cancellare.
**Risposte**
 - `403 FORBIDDEN`: l'utente non è loggato.
 - `404 NOT FOUND`: l'id inserito non risulta essere tra quelli delle prenotazini appartenenti all'utente.
 - `200 OK`: la prenotazine è cancellata.


#### PATCH
Consente di modificare le proprie pronotazioni. Ci sono due canali diversi di modifica: modificare per id dello scheduling (in pratica modificare la data prenotata) oppure mantenere l'attuale scehduling modificando solo il numero del posto prenotato.  Nota per l'utilizzo: La modifica di una prenotazione tramite la modifica dello schedulingId può essere essere eseguita solo selezionando uno scheduling che prevede lo stesso spettacolo (Es: se ho prenotato per Amleto, non posso modificare selezionando una data per Cenerentola, devo selezionare un'altra data sempre per Amleto).

**Parametri**
 - `reservation_id`: id della prenotazione da modificare
 - `schedulingId`: id dello scheduling con cui si desidera eseguire il cambio. Se questo campo è nullo allora la modifica avverrà per cambio posto.
 - `seatNumber`: nuovo posto che si desidera prenotare al posto di quello attualmente prenotato. Se questo campo è nulla allora la modifica avverrà per cambio di schedulingId.

**Risposte**
 - `400 BAD REQUEST`: il numero di posto inserito non è valido; la data con cui si desidera fare a cambio è già sold-out.
 - `403 FORBIDDEN`: l'utente non è loggato; l'utente cerca di modificare una prenotazione non sua; l'utente cerca di modificare in uno scheduling appartenente al passato o che prevede uno spettacolo diverso da quello che aveva prenotato;
 - `404 NOT FOUND`: la prenotazione che si vuol modificare non è riscontrata; Lo scheduling con cui si vuol fare a cambio risulta non essere trovato;
 - `409 CONFLICT`: Il posto con cui si vuol fare a cambio è già prenotato.
 - `200 OK`: Modifica avvenuta con successo.


### `api/userInfo`

#### GET
Si ottengono le informazioni di un certo utente
**Parametri**
Nessuno, basta essere loggati

**Risposte**
 - `403 FORBIDDEN`: login non effettuato.
 - `200 OK`: risposta ottenuta.

### `api/show-admin`

#### GET
Usata nell'adminDashboard per far apparire a schermo le informazioni utili per lo scheduling di uno spettacolo.

**Parametri**
Nessuno, basta che l'utente loggato sia l'admin.

**Risposte***
 - `403 FORBIDDEN`: login non effettuato o l'utente loggato non è l'admin.
 - `404 NOT FOUND`: Non ci sono spettacoli schedulabili
 - `200 OK`: risposta ottenuta.

## Per il Testing
È possibile testare ogni funzionalità direttamente dall'interfaccia inserendo i valori richiesti. Nella tabella scheduling è presente un evento con solo un posto prenotabile, può essere sfruttato per testare i casi in cui un utente tenta di modificare la sua prenotazione in un giorno che è già sold out. Per la creazione di una prenotazione non importa perché è chiesto esplicitamente quale posto prenotare, se il posto è già occupato bisogna inserirne un altro.