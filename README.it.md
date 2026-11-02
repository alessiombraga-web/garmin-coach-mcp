# Garmin Coach per Claude

**Fai leggere a Claude le tue corse Garmin e fatti aiutare ad analizzarle.**

Con Garmin Coach puoi chiedere a Claude, con parole tue, cose come:

> *"Com'è andata la corsa di stamattina?"*
> *"Negli ultimi 5 km mi è salito tanto il cuore: perché?"*
> *"Confronta i miei lunghi delle ultime 8 settimane."*
> *"Quanti chilometri ho fatto questo mese? E a che ritmo?"*
> *"Mercoledì ho fatto l'allenamento come era previsto?"*

Claude legge i dati direttamente dal tuo account Garmin: passo, frequenza cardiaca, cadenza, lap, dinamiche di
corsa. Non devi più esportare file o fare screenshot.

Ci vogliono **circa 10 minuti** e **non serve essere esperti di computer**: niente comandi, niente programmi strani.

🇬🇧 [English documentation](README.md) · 🛠️ [Guida avanzata con Docker](docs/docker.it.md)

---

## Indice

- [Cosa ti serve](#cosa-ti-serve)
- [Passo 1 — Installa Claude sul computer](#passo-1--installa-claude-sul-computer)
- [Passo 2 — Crea la tua chiave Garmin](#passo-2--crea-la-tua-chiave-garmin)
- [Passo 3 — Scarica Garmin Coach](#passo-3--scarica-garmin-coach)
- [Passo 4 — Installalo in Claude](#passo-4--installalo-in-claude)
- [Passo 5 — La prima chat](#passo-5--la-prima-chat)
- [Racconta a Claude chi sei](#racconta-a-claude-chi-sei)
- [Esempi di domande](#esempi-di-domande)
- [Domande frequenti](#domande-frequenti)
- [Se qualcosa non va](#se-qualcosa-non-va)

---

## Cosa ti serve

- Un **computer Mac o Windows**. Dal telefono non funziona.
- Un **orologio Garmin** che sincronizza le corse su **Garmin Connect**, l'app di Garmin.
- Un **account Claude**, cioè le stesse credenziali con cui usi Claude sul sito o sul telefono.

---

## Passo 1 — Installa Claude sul computer

Se hai già l'app **Claude** sul computer, salta al passo 2.

1. Vai su **[claude.ai/download](https://claude.ai/download)** e scarica la versione per il tuo computer (Mac o Windows).
2. Installala come un qualsiasi programma e aprila.
3. Accedi con il tuo account Claude.

> Serve proprio l'**app per computer**: il sito claude.ai nel browser o l'app del telefono non vanno bene.

---

## Passo 2 — Crea la tua chiave Garmin

La "chiave" è un codice che dà a Garmin Coach il permesso di **leggere** le tue attività.
Non può modificare né cancellare niente sul tuo account Garmin.

1. Dal computer apri **[Garmin Connect](https://connect.garmin.com)** nel browser e accedi con il tuo account Garmin.
2. Vai nelle impostazioni, alla voce **Personal API**. Puoi usare il collegamento diretto:
   **[connect.garmin.com/app/settings/personalApiToken](https://connect.garmin.com/app/settings/personalApiToken)**
3. Leggi e accetta le condizioni.
4. Scegli la **durata** della chiave: ti consiglio **1 anno**, così non ci pensi più per un bel po'.
5. Crea la chiave e **copiala subito**, per esempio incollandola in una nota. Garmin la mostra **una volta sola**.

> 🔒 Tratta la chiave come una password: non mandarla a nessuno e non scriverla nelle chat.

---

## Passo 3 — Scarica Garmin Coach

1. Vai sulla pagina delle versioni: **[Scarica l'ultima versione](https://github.com/fabio983/garmin-coach-mcp/releases/latest)**
2. In fondo alla pagina, sotto **Assets**, clicca sul file **`garmin-coach-…mcpb`**, quello senza
   "docker-connector" nel nome.
3. Il file finisce nella cartella **Download**.

---

## Passo 4 — Installalo in Claude

1. Con Claude aperto, fai **doppio clic** sul file `garmin-coach-…mcpb` che hai scaricato.
   - Se non succede niente: in Claude apri **Impostazioni → Estensioni** e trascina il file dentro la finestra.
2. Si apre la finestra di installazione di **Garmin Coach**. Clicca su **Installa**.
3. Ti chiede le impostazioni:
   - **Garmin Personal API key**: incolla la chiave che hai copiato al passo 2;
   - **Import runs from (YYYY-MM-DD)**: è la data da cui Garmin Coach scarica le tue corse la prima volta.
     Di base è `2024-01-01`; se vuoi puoi cambiarla, scrivendola nel formato anno-mese-giorno (per esempio
     `2022-06-01`). Leggi la nota qui sotto prima di scegliere;
   - lascia tutto il resto com'è.
4. Conferma e controlla che l'estensione sia **attiva**, con l'interruttore acceso.

Fatto. La prima volta Claude può impiegare qualche secondo in più a partire, perché prepara da solo quello che gli serve.

> 📅 **Nota sulla data di partenza**
>
> - **Più la data è lontana, più tempo serve la prima volta.** Ogni corsa richiede qualche secondo: con un paio di
>   anni di corse ci vogliono alcuni minuti, con molti anni anche mezz'ora o più, sempre con Claude aperto.
>   Se vuoi partire subito, scegli una data recente: le corse più vecchie le puoi aggiungere quando vuoi.
> - **La data conta solo per la prima importazione.** Se dopo l'installazione la cambi nelle impostazioni
>   dell'estensione non succede niente, perché da lì in poi Garmin Coach scarica solo le corse nuove.
>   Per aggiungere corse più vecchie chiedi direttamente a Claude, per esempio:
>   *"Sincronizza le mie corse dal 2019"*. Le scarica in sottofondo mentre continui a usare Claude.

---

## Passo 5 — La prima chat

Apri una **nuova chat** in Claude e scrivi:

> **Sincronizza le mie corse Garmin e dimmi com'è andata l'ultima.**

Claude ti chiederà il permesso di usare Garmin Coach: rispondi di sì. Puoi anche scegliere di dargli il permesso
una volta per tutte.

La prima volta Garmin Coach scarica **tutte le tue corse dalla data scelta al passo 4** (di base il 1° gennaio 2024). Ci vuole qualche minuto, e continua
da solo finché Claude resta aperto. Puoi già fare domande mentre lavora. Per sapere a che punto è chiedi:

> **A che punto è l'archivio Garmin?**

Dopo la prima volta è tutto veloce: quando torni da una corsa e chiedi di lei, Claude la scarica in pochi secondi.

---

## Racconta a Claude chi sei

Claude ti dà consigli migliori se sa qualcosa di te. Diglielo in chat e chiedigli di ricordarlo, per esempio:

> *"La mia frequenza cardiaca massima è 188. Uso la fascia cardio da giugno. Corro con le Pegasus per gli allenamenti
> facili e con le Vaporfly in gara. Il mio obiettivo è la mezza maratona di marzo. Salvalo nelle mie note."*

Garmin Coach salva queste informazioni sul tuo computer e Claude le rilegge nelle chat successive.
Puoi cambiarle quando vuoi: *"Aggiorna le mie note: adesso la massima è 190"*.

Puoi anche aggiungere a una corsa le cose che Garmin non sa:

> *"Alla corsa di oggi aggiungi che c'erano 28 gradi e che ero molto stanco."*

---

## Esempi di domande

**Sulla singola corsa**
- *"Analizza la corsa di ieri: lap per lap, com'è andata?"*
- *"Nelle ripetute di mercoledì ho tenuto il ritmo? Quanto ho recuperato tra una e l'altra?"*
- *"Nel lungo di domenica quando è iniziata la crisi?"*

**Sull'andamento**
- *"Fammi un riepilogo delle ultime 12 settimane: chilometri, uscite, lungo più lungo."*
- *"Sto correndo troppo forte negli allenamenti facili?"*
- *"La mia cadenza è migliorata rispetto all'anno scorso?"*

**Per programmare**
- *"Guardando gli ultimi due mesi, preparami un piano per la prossima settimana."*

---

## Domande frequenti

**Garmin Coach può modificare qualcosa sul mio account Garmin?**
No. Usa l'API ufficiale di Garmin, che permette **solo di leggere**.

**Dove finiscono i miei dati?**
Sul tuo computer, nella cartella **Documenti → Garmin Coach**, o in quella che hai scelto durante l'installazione.
Lì ci sono l'archivio delle corse e le tue note. Garmin Coach non manda i tuoi dati da nessuna parte: Claude li
legge solo quando gli fai una domanda.

**Funziona anche dal telefono?**
No, solo con l'app Claude sul computer, e solo mentre è aperta.

**Devo lasciare il computer acceso?**
No. Quando riapri Claude, Garmin Coach scarica le corse nuove.

**Posso farmi mettere gli allenamenti direttamente sull'orologio?**
Con questa versione no, perché l'API ufficiale di Garmin non permette di scrivere. È possibile con la
[versione avanzata](docs/docker.it.md), che però richiede competenze tecniche.

**Funziona con tutti gli orologi Garmin?**
Funziona con qualsiasi orologio che sincronizza le corse su Garmin Connect. I dati disponibili dipendono
dall'orologio e dai sensori: le dinamiche di corsa, per esempio, ci sono solo con gli orologi e le fasce che le
misurano.

**La chiave scade?**
Sì, dopo il periodo che hai scelto. Garmin ti manda un'email circa una settimana prima. Per rinnovarla crea una
nuova chiave (passo 2), poi in Claude apri **Impostazioni → Estensioni → Garmin Coach**, incolla la nuova chiave e salva.

**Posso importare anche le corse più vecchie?**
Sì, in qualsiasi momento: chiedi a Claude *"Sincronizza le mie corse dal 2019"*. Cambiare la data nelle impostazioni
dell'estensione dopo l'installazione invece non serve: vale solo per la prima importazione.

**Come lo aggiorno quando esce una nuova versione?**
Scarica il nuovo file `.mcpb` (passo 3) e aprilo come la prima volta. Archivio e note restano dove sono.

**Come lo tolgo?**
In Claude: **Impostazioni → Estensioni → Garmin Coach → Disinstalla**. Se vuoi cancellare anche i dati, elimina la
cartella **Documenti → Garmin Coach**.

**È un prodotto Garmin o di Anthropic?**
No, è un progetto personale e gratuito, condiviso con la community.

---

## Se qualcosa non va

| Cosa succede | Cosa fare |
|---|---|
| Il doppio clic sul file non fa niente | Apri Claude → **Impostazioni → Estensioni** e trascina il file nella finestra. |
| Claude risponde senza usare i tuoi dati | Controlla che l'estensione sia **attiva** (Impostazioni → Estensioni) e apri una **nuova chat**. |
| Claude dice che la chiave non è valida o è scaduta | Crea una nuova chiave (passo 2) e incollala in **Impostazioni → Estensioni → Garmin Coach**. |
| Claude dice che non riesce a raggiungere Garmin | Controlla la connessione a internet e riprova tra qualche minuto. |
| Manca una corsa appena fatta | Controlla che l'orologio l'abbia sincronizzata sull'app Garmin Connect, poi chiedi a Claude di sincronizzare di nuovo. |

Se il problema resta, puoi segnalarlo nella pagina del progetto su GitHub, nella sezione
**[Issues](https://github.com/fabio983/garmin-coach-mcp/issues)**.

---

*Garmin Coach non è affiliato né approvato da Garmin o da Anthropic. Garmin e Garmin Connect sono marchi di Garmin
Ltd.; Claude è un marchio di Anthropic, PBC. Licenza [MIT](LICENSE).*
