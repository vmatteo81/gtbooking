# GT Booking

MVP SaaS Django per la gestione delle prenotazioni ai corsi in palestra: multi-tenant semplice (`gym_id` sulle entità), ruoli cliente / staff / admin SaaS, lista d’attesa con promozione automatica alla cancellazione.

## Requisiti

- Python 3.12+ (consigliato)
- In produzione: MySQL, Gunicorn, Nginx (vedi sotto)

## Sviluppo locale (senza Docker)

```powershell
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
copy .env.example .env
# Modifica .env se necessario (SQLite di default)
.\.venv\Scripts\python manage.py migrate
.\.venv\Scripts\python manage.py createsuperuser
.\.venv\Scripts\python manage.py runserver
```

Il superuser riceve un profilo **Admin SaaS** (`SAAS_ADMIN`, senza palestra) tramite segnale. Crea palestre, corsi e sessioni da `/admin/`. Per lo **staff palestra`, crea utenti con profilo `GYM_STAFF` e palestra associata (sempre da admin).

Area cliente: `/g/<slug-palestra>/` (calendario e prenotazioni). Staff: `/dashboard/`.

## Sviluppo locale con Docker

Solo comodo ambiente di sviluppo: SQLite in volume, codice montato dal host, porta **18765** (evita conflitti con altri progetti).

```powershell
docker compose -f docker/docker-compose.yml up --build
```

Apri `http://127.0.0.1:18765/`. Al primo avvio vengono eseguite le migrazioni. Crea un superuser **una volta** (dal container):

```powershell
docker compose -f docker/docker-compose.yml exec web python manage.py createsuperuser
```

## Variabili d’ambiente

Vedi [.env.example](.env.example). In sintesi:

- `DEBUG`, `SECRET_KEY`, `ALLOWED_HOSTS`
- `DATABASE_ENGINE`: `django.db.backends.sqlite3` oppure `django.db.backends.mysql` (valore completo del backend Django)
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` (per MySQL)
- Opzionale produzione: `STATIC_ROOT`, `MEDIA_ROOT`, `CSRF_TRUSTED_ORIGINS`, `SECURE_SSL_REDIRECT`

## Produzione (senza Docker)

Flusso tipico su Linux:

1. **MySQL**: crea database e utente con charset `utf8mb4`. Imposta le variabili `DATABASE_ENGINE=mysql` e le credenziali.
2. **Virtualenv**: installa `requirements.txt`, esegui migrazioni, imposta `STATIC_ROOT` e `MEDIA_ROOT`, poi `python manage.py collectstatic --noinput`.
3. **Gunicorn** (esempio, adatta path e utente):

   ```bash
   /path/to/venv/bin/gunicorn config.wsgi:application \
     --bind unix:/run/gtbooking/gunicorn.sock \
     --workers 3
   ```

4. **systemd** — unità di servizio esemplificativa (`/etc/systemd/system/gtbooking.service`):

   ```ini
   [Unit]
   Description=GT Booking Gunicorn
   After=network.target

   [Service]
   User=www-data
   Group=www-data
   WorkingDirectory=/srv/gtbooking
   EnvironmentFile=/srv/gtbooking/env
   RuntimeDirectory=gtbooking
   ExecStart=/srv/gtbooking/venv/bin/gunicorn config.wsgi:application \
     --bind unix:/run/gtbooking/gunicorn.sock \
     --workers 3
   Restart=on-failure

   [Install]
   WantedBy=multi-user.target
   ```

   Poi: `sudo systemctl daemon-reload && sudo systemctl enable --now gtbooking`.

5. **Nginx** — proxy verso il socket Gunicorn, `alias` per `STATIC_ROOT` e `MEDIA_ROOT`, header `Host`, `X-Forwarded-For`, `X-Forwarded-Proto`.

6. **HTTPS**: Let’s Encrypt (es. [Certbot](https://certbot.eff.org/) con plugin Nginx) con redirect HTTP → HTTPS e rinnovo automatico.

7. **Django**: `DEBUG=False`, `ALLOWED_HOSTS` e `CSRF_TRUSTED_ORIGINS` con il dominio pubblico. Se il proxy termina TLS, imposta `SECURE_PROXY_SSL_HEADER` (già previsto in settings quando `DEBUG=False`).

## Test

```powershell
.\.venv\Scripts\python manage.py test
```

## Struttura progetto

- `config/` — impostazioni Django (`config.settings`, tutto da variabili d’ambiente)
- `apps/core` — middleware palestra corrente da URL `/g/<slug>/`
- `apps/accounts` — profili e autenticazione
- `apps/gyms`, `apps/courses`, `apps/bookings`, `apps/dashboard`

## Prossimi passi (fuori MVP)

Pagamenti, email, QR check-in, report avanzati, tenancy per sottodominio, API REST.
