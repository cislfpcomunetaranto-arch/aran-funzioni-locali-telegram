\
# Monitor ARAN – Funzioni Locali

Sistema automatico per il canale Telegram:

**Orientamenti ARAN – Funzioni Locali | CISL FP Taranto**

Il programma controlla il sito ufficiale ARAN, individua i nuovi orientamenti
applicativi del Comparto Funzioni Locali e li pubblica nel canale Telegram.

## Protezioni previste

- nessun token nel codice;
- prima esecuzione senza pubblicazione dei vecchi orientamenti;
- controllo dei duplicati tramite ID ARAN;
- stato salvato nel repository;
- esecuzioni concorrenti bloccate;
- arresto senza aggiornare lo stato quando Telegram rifiuta un messaggio;
- modalità di prova senza pubblicazione.

## Segreti GitHub richiesti

In `Impostazioni → Segreti e variabili → Actions`:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHANNEL_ID`

Il Channel ID configurato per questo progetto è:

```text
-1003875980575
```

## Caricamento iniziale

1. Aprire il repository `aran-funzioni-locali-telegram`.
2. Selezionare `Add file → Upload files`.
3. Estrarre questo ZIP sul computer.
4. Caricare **il contenuto della cartella estratta**, mantenendo le sottocartelle.
5. Confermare con `Commit changes`.

La struttura finale deve contenere direttamente:

```text
.github/workflows/monitor.yml
src/main.py
data/state.json
requirements.txt
README.md
```

Non deve esserci una cartella esterna duplicata del tipo:

```text
aran-funzioni-locali-telegram/aran-funzioni-locali-telegram/src/
```

## Prima attivazione sicura

Aprire la scheda `Actions`, selezionare:

**Controllo orientamenti ARAN**

Premere `Run workflow` e impostare:

```text
Prova senza pubblicare su Telegram: true
Registra gli orientamenti esistenti senza pubblicarli: true
```

Questa esecuzione verifica il sito e registra gli orientamenti già presenti,
senza inviare messaggi nel canale.

Controllare che l'esecuzione termini con il segno verde.

## Test reale del collegamento Telegram

Dopo l'inizializzazione, eseguire nuovamente il workflow con:

```text
Prova senza pubblicare su Telegram: false
Registra gli orientamenti esistenti senza pubblicarli: true
```

Non verrà pubblicato nulla se non esistono nuovi orientamenti successivi
all'inizializzazione. Il collegamento Telegram sarà utilizzato automaticamente
alla prima nuova pubblicazione ARAN.

## Frequenza

Il controllo automatico viene eseguito ogni 30 minuti. GitHub può avviare i
workflow programmati con alcuni minuti di ritardo.

## Modifica del testo dei messaggi

Il formato è definito in:

```text
src/telegram_client.py
```

## Diagnostica

In caso di errore:

1. aprire `Actions`;
2. selezionare l'esecuzione rossa;
3. aprire il passaggio `Esegui il monitor`;
4. leggere il messaggio finale.

Se ARAN modifica la struttura del sito, il monitor si arresta senza segnare
come pubblicati elementi che non è riuscito a leggere.
