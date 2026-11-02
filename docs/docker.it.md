# Garmin Coach — guida avanzata (Docker)

Questa guida è per chi vuole far girare Garmin Coach **su un server sempre acceso**: VM di un homelab, NAS,
Raspberry Pi 4/5 o un PC che resta acceso, con Docker. Se vuoi solo usarlo, la strada semplice è
l'estensione di Claude Desktop: vedi la [guida passo per passo](../README.it.md).

Rispetto all'estensione, la versione Docker offre:

- **sync sempre attivo**, anche quando il computer con Claude è spento;
- **un unico archivio** raggiungibile da più computer di casa;
- **scrittura opzionale su Garmin**: allenamenti strutturati in calendario, passo corretto per la pendenza per lap,
  scarpe. Usa il modulo della community, perché l'API ufficiale è in sola lettura.

🇬🇧 [English documentation](../README.md)

---

## Indice

- [Requisiti](#requisiti)
- [Installazione](#installazione)
- [Collegare Claude Desktop](#collegare-claude-desktop)
- [Scrittura su Garmin (opzionale)](#scrittura-su-garmin-opzionale)
- [Note su di te](#note-su-di-te)
- [Configurazione](#configurazione)
- [Manutenzione](#manutenzione)
- [Risoluzione problemi](#risoluzione-problemi)
- [Sicurezza](#sicurezza)

---

## Requisiti

| Dove | Cosa |
|---|---|
| Server | Docker + Docker Compose (su Mac e Windows va bene Docker Desktop) |
| Computer con Claude | [Claude Desktop](https://claude.ai/download) |
| Garmin | Account Garmin Connect e [chiave Personal API](https://connect.garmin.com/app/settings/personalApiToken) |

Server e computer devono stare sulla stessa rete (o raggiungersi via VPN). Possono anche essere lo stesso computer.

---

## Installazione

### 1. Scarica il codice

```bash
git clone https://github.com/fabio983/garmin-coach-mcp.git
cd garmin-coach-mcp
```

### 2. Crea la chiave Garmin

Garmin Connect dal web → **Impostazioni → Personal API**
([link diretto](https://connect.garmin.com/app/settings/personalApiToken)). Accetta i termini, scegli la scadenza
(fino a 1 anno), crea la chiave e copiala subito: Garmin la mostra una volta sola.

### 3. Configura

```bash
cp .env.example .env
openssl rand -hex 32        # copia il risultato in MCP_TOKEN
nano .env                   # incolla la chiave in GARMIN_PERSONAL_API_KEY, imposta TZ, BACKFILL_FROM, HR_BANDS...
```

> **Importante:** dopo ogni modifica al `.env` usa `docker compose up -d`. Il semplice `restart` non rilegge il
> file, e il container continua con i valori vecchi: è la causa più comune dell'errore "token sbagliato".

### 4. Avvia

```bash
docker compose build
docker compose up -d
docker compose logs -f
```

Al primo avvio importa lo storico da `BACKFILL_FROM`: una riga `Details <id> (running) ok` per corsa e alla fine
`Auto sync: ok`. Dal computer con Claude verifica che risponda:

```bash
curl http://IP-SERVER:8765/healthz      # → ok   (127.0.0.1 se Docker gira sullo stesso computer)
```

---

## Collegare Claude Desktop

### Consigliato: l'estensione connettore (niente file da modificare)

1. Scarica **`garmin-coach-docker-connector-…mcpb`** dall'[ultima versione](https://github.com/fabio983/garmin-coach-mcp/releases/latest).
2. Fai doppio clic sul file. Nella finestra di installazione inserisci:
   - **Server address**: `http://127.0.0.1:8765/mcp` se Docker gira sullo stesso computer, altrimenti
     `http://IP-SERVER:8765/mcp`;
   - **MCP token**: il valore di `MCP_TOKEN` nel tuo `.env`.
3. Clicca **Installa**, apri una nuova chat e chiedi *"Com'è messo il mio archivio Garmin?"*

Non serve installare Node.js: il connettore usa quello incluso in Claude Desktop e contiene già
[mcp-remote](https://github.com/geelen/mcp-remote).

### In alternativa: configurazione manuale

Solo se preferisci non usare il connettore.

1. **Installa Node.js LTS**, se `node -v` nel terminale non mostra già una versione:
   - **Windows** (PowerShell): `winget install OpenJS.NodeJS.LTS`
   - **Mac** (Terminale), con [Homebrew](https://brew.sh): `brew install node`. Senza Homebrew, scarica
     l'installer per macOS da [nodejs.org](https://nodejs.org) e aprilo con un doppio clic.

   Poi chiudi e riapri il terminale e controlla con `node -v`.
2. Trova il percorso completo di `npx`: `where npx` su Windows, `which npx` su Mac (di solito
   `/opt/homebrew/bin/npx` oppure `/usr/local/bin/npx`). Con il percorso completo Claude non ha problemi a trovarlo.
3. In Claude Desktop: **Impostazioni → Sviluppatore → Modifica configurazione**. Aggiungi il blocco dentro
   `mcpServers` (vedi [`examples/claude_desktop_config.json`](../examples/claude_desktop_config.json)).
   Se il file contiene già altre chiavi (per esempio `preferences`), lasciale: `mcpServers` va al primo livello,
   separato da una virgola.

   ```json
   {
     "mcpServers": {
       "garmin-coach": {
         "command": "/opt/homebrew/bin/npx",
         "args": ["-y", "mcp-remote@latest", "http://IP-SERVER:8765/mcp",
                  "--allow-http", "--transport", "http-only",
                  "--header", "Authorization:${AUTH_HEADER}"],
         "env": { "AUTH_HEADER": "Bearer IL_TUO_MCP_TOKEN" }
       }
     }
   }
   ```

   Su Windows metti il percorso di `where npx` con le barre raddoppiate, per esempio
   `"C:\\Program Files\\nodejs\\npx.cmd"`.
4. **Chiudi Claude del tutto prima di salvare** (su Windows anche dall'icona in basso a destra), poi riaprilo.
   In **Impostazioni → Sviluppatore** deve comparire `garmin-coach` *in esecuzione*.

---

## Scrittura su Garmin (opzionale)

L'API ufficiale è **in sola lettura**. Per far creare e programmare a Claude gli allenamenti sul tuo Garmin, attiva il
modulo della community basato su [python-garminconnect](https://github.com/cyberjunky/python-garminconnect), che usa
l'API privata di Garmin Connect con lo stesso login dell'app per smartphone.

> **Prima di attivarlo:** non è un'interfaccia ufficiale Garmin, può smettere di funzionare quando Garmin cambia la
> sua API privata e fa il login con le tue credenziali. Usalo solo con il tuo account.

1. Nel `.env`: `ENABLE_GARMINCONNECT=true`
2. Ricrea il container: `docker compose up -d`
3. Fai il login una volta: `docker compose run --rm garmin-coach login` (email, password, codice MFA se attivo).
   Avvisi come `mobile+cffi returned 429` sono normali, purché il comando finisca con `Login OK`.
4. `docker compose restart`, poi riavvia Claude Desktop.
5. In una nuova chat chiedi *"Com'è messo il mio archivio Garmin?"*: deve risultare
   `write access (community module): enabled`.

Per disattivarlo: `ENABLE_GARMINCONNECT=false`, `docker compose up -d` e, se vuoi, cancella
`data/tokens/garmin_tokens.json`.

**Formato degli allenamenti.** Basta descrivere la seduta a parole. Claude mostra sempre un'**anteprima** e carica
solo dopo il tuo ok. Per riferimento, ecco la lista di passi che costruisce:

```json
[
  {"kind": "warmup", "time": "15:00", "hr": "120-145", "note": "facile"},
  {"repeat": 3, "steps": [
    {"kind": "interval", "distance_km": 2, "pace": "5:40-5:45"},
    {"kind": "recovery", "time": "2:00", "note": "corsa lenta"}
  ]},
  {"kind": "cooldown", "time": "10:00"}
]
```

`kind`: `warmup`, `interval`, `recovery`, `rest`, `cooldown`, `other`. Durata: `time`, `distance_km`, `distance_m`
o `lap: true`. Target: `pace` (min/km) oppure `hr` (bpm), sempre con due limiti. Con `replace_workout_id` riscrive un
allenamento mantenendo le date in calendario.

---

## Note su di te

Dille a Claude in chat (*"salva nelle mie note che la mia FC massima è 190"*) oppure scrivile in `data/athlete.md`,
partendo da [`examples/athlete.example.md`](../examples/athlete.example.md). Il file non finisce mai nel repository.

---

## Configurazione

Tutte le impostazioni stanno in `.env` (vedi [`.env.example`](../.env.example)). Dopo una modifica: `docker compose up -d`.

| Variabile | Default | Descrizione |
|---|---|---|
| `MCP_TOKEN` | – | Token richiesto dall'endpoint MCP. **Da impostare.** |
| `GARMIN_PERSONAL_API_KEY` | – | Chiave Personal API ufficiale (sola lettura). **Da impostare.** |
| `ENABLE_GARMINCONNECT` | `false` | Modulo della community (scrittura, GAP per lap, scarpe) |
| `GARMIN_EMAIL` / `GARMIN_PASSWORD` | – | Solo modulo community: re-login automatico (non con MFA) |
| `TZ` | – | Fuso orario, es. `Europe/Rome` |
| `BACKFILL_FROM` | `2024-01-01` | Inizio della prima importazione |
| `SYNC_INTERVAL_MIN` | `30` | Intervallo del sync automatico (0 = solo su richiesta) |
| `REQUEST_DELAY_S` | `1.5` | Pausa tra le chiamate a Garmin |
| `HR_BANDS` | `135,150,160,170` | Soglie inferiori delle fasce FC 2..N |
| `DETAIL_TYPE_MATCH` | `all` | Tipi di attività per cui scaricare FIT/lap/record (`all` = tutte, oppure es. `run,cycling`) |
| `ATHLETE_FILE` | `/data/athlete.md` | Note su di te |
| `MCP_PORT` | `8765` | Porta nel container |

---

## Manutenzione

| Operazione | Comando |
|---|---|
| Aggiornamento | `git pull && docker compose up -d --build`, poi riavvia Claude Desktop |
| Chiave Garmin scaduta (`auth_required`) | Nuova chiave → `.env` → `docker compose up -d` |
| Token del modulo community scaduti | `docker compose run --rm garmin-coach login && docker compose restart` |
| Importare lo storico più vecchio | `docker compose exec garmin-coach python -m app sync --since 2017-01-01` |
| Rigenerare lap/record dai FIT | `docker compose exec garmin-coach python -m app reparse` |
| Backup | Copia la cartella `data/` |
| Log | `docker compose logs -f` |

---

## Risoluzione problemi

| Sintomo | Causa / soluzione |
|---|---|
| Connettore o mcp-remote: *401 … missing or wrong MCP token* | Il token in Claude è diverso da quello che usa il server. Controlla con `docker compose exec garmin-coach printenv MCP_TOKEN`; dopo aver modificato `.env` usa `docker compose up -d`. |
| Configurazione manuale: *npx not found* / *No executable file* | Node.js mancante, o Claude non lo trova: usa il percorso completo di `npx`, oppure il connettore. |
| *"Unexpected non-whitespace character after JSON"* | Configurazione manuale: il blocco è fuori dalle `{ }` principali del file. |
| `sync_status`: `auth_required`, *Personal API rejected the key* | Chiave scaduta, revocata o copiata male. |
| `sync_status`: `network_error` | Il server non raggiunge `personal.connectapi.garmin.com`: controlla rete e firewall. |
| Avvisi `429` al `login` | Normali se finisce con `Login OK`. Se fallisce, aspetta un'ora. |
| `curl .../healthz` risponde `unauthorized` | Percorso sbagliato: solo `/healthz` è aperto senza token. |
| Una modifica al `.env` non ha effetto | Usa `docker compose up -d`, non `restart`. |

---

## Sicurezza

- Tutto resta in `./data`: database, FIT originali, token, note. `data/` e `.env` sono esclusi da `.gitignore`.
- `.env` contiene la chiave Garmin, `data/tokens/` i token: proteggili come password.
- L'endpoint MCP è HTTP semplice protetto da token: **tienilo sulla rete di casa** (o dietro VPN). Non esporre la
  porta 8765 su internet.
- `query_sql` apre il database in sola lettura. Claude scrive su Garmin solo con il modulo della community attivo e
  dopo la tua conferma.
