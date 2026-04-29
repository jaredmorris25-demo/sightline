# Sightline — Cold Start Reference

> Keep this file up to date as new services, infrastructure, and apps are added.
> Last updated: 2026-04-29

---

## How to use this document

- **Part A — First-time rebuild**: Complete walkthrough from zero. Use when starting fresh on a new machine or recovering from total loss. Follow A1–A13 in order.
- **Part B — Daily startup**: Bring up an existing, already-configured system. Start here on a normal working day.
- **Part C — Operations reference**: Commands, settings, and resource details for ongoing work.

---

## Part A — First-time rebuild

### A1. Prerequisites

Install these tools before anything else.

| Tool | Minimum version | Notes |
|---|---|---|
| Docker Desktop | Latest | https://www.docker.com/products/docker-desktop |
| Node.js | 20 LTS | https://nodejs.org — required for Next.js |
| Azure CLI | Latest | `brew install azure-cli` |
| Terraform | 1.6+ | `brew install terraform` |
| Git | Latest | `brew install git` |
| VSCode | Latest | https://code.visualstudio.com — Claude Code extension optional |

Python is **not** required locally. The API and all database scripts run inside Docker.

Verify before continuing:
```bash
docker --version && node --version && az --version && terraform -version
```

---

### A2. Clone the repository

```bash
git clone https://github.com/jaredmorris25-demo/sightline.git ~/sightline
cd ~/sightline
```

---

### A3. Create local environment files

#### .env (Docker Compose + API)

```bash
cp .env.example .env
```

The defaults in `.env.example` work for local dev. Fill in the Auth0 values:
```
AUTH0_DOMAIN=dev-kr7ljpg5onbkey04.us.auth0.com
AUTH0_API_AUDIENCE=https://api.sightline.app
AUTH0_CLIENT_ID=WN9aqjcky6ILPh5fBZa0Pf5M9nRTBZca
AUTH0_CLIENT_SECRET=<Auth0 dashboard → Applications → Sightline Web → Settings>
```

#### web/.env.local (Next.js)

No example file exists — create it from scratch:
```
AUTH0_SECRET=<run: openssl rand -hex 32>
AUTH0_BASE_URL=http://localhost:3000
AUTH0_DOMAIN=dev-kr7ljpg5onbkey04.us.auth0.com
AUTH0_CLIENT_ID=WN9aqjcky6ILPh5fBZa0Pf5M9nRTBZca
AUTH0_CLIENT_SECRET=<Auth0 dashboard → Applications → Sightline Web → Settings>
AUTH0_AUDIENCE=https://api.sightline.app
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_MAPBOX_TOKEN=<https://account.mapbox.com → Access tokens>
# NEXT_PUBLIC_API_URL=https://ca-sightline-api.wittywave-8fb8cdba.australiaeast.azurecontainerapps.io
```

The Azure URL is kept as a comment for easy switching during local vs Azure testing.
Uncomment the Azure line (and comment out the localhost line) to point the frontend at the live API.

#### Install web dependencies

```bash
cd ~/sightline/web && npm install
```

---

### A4. Start local services

```bash
cd ~/sightline
docker compose up -d
```

Wait for all three services to be healthy:
```bash
docker compose ps
```

Expected: `postgres`, `pgadmin`, and `api` all showing `Up` or `(healthy)`.

---

### A5. Initialise the local database

Run in this exact order. Do not seed before migrating.

**1 — Run migrations (creates all tables):**
```bash
docker compose exec \
  -e DATABASE_URL_SYNC=postgresql://sightline:localdevonly@postgres:5432/sightline \
  -w /db api alembic upgrade head
```

**2 — Seed species (255 Australian species from ALA):**
```bash
docker compose exec \
  -e DATABASE_URL_SYNC=postgresql://sightline:localdevonly@postgres:5432/sightline \
  api python /db/seed/seed_species.py
```

**3 — Seed synthetic sightings (10,000 records — optional):**
```bash
docker compose exec \
  -e DATABASE_URL_SYNC=postgresql://sightline:localdevonly@postgres:5432/sightline \
  api python /db/seed/seed_sightings.py
```

All seed scripts are idempotent — safe to re-run.

Note: PostGIS is pre-installed in the `postgis/postgis:16-3.4` Docker image. No `CREATE EXTENSION` needed locally.

---

### A6. Verify local stack

```bash
curl http://localhost:8000/health
# Expected: {"status":"ok","environment":"local","version":"0.1.0"}

curl http://localhost:8000/v1/species/?limit=1
# Expected: JSON with one species record
```

Start the web frontend (see Part B, step 2) and open http://localhost:3000 to verify the map loads.

---

### A7. Bootstrap Azure (one-time — skip if Azure resources already exist)

**1 — Log in and capture subscription ID:**
```bash
az login
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
echo $SUBSCRIPTION_ID
```

**2 — Create resource group:**
```bash
az group create --name rg-sightline --location australiaeast
```

**3 — Create Terraform state storage:**

This must exist BEFORE `terraform init`. It cannot be managed by Terraform itself.
```bash
az storage account create \
  --name stsightlinetfstate \
  --resource-group rg-sightline \
  --location australiaeast \
  --sku Standard_LRS

az storage container create \
  --name tfstate \
  --account-name stsightlinetfstate
```

**4 — Create service principal for GitHub Actions:**
```bash
az ad sp create-for-rbac \
  --name sp-sightline-github-actions \
  --role contributor \
  --scopes /subscriptions/$SUBSCRIPTION_ID/resourceGroups/rg-sightline \
  --json-auth
```

Save the full JSON output — it becomes the `AZURE_CREDENTIALS` GitHub secret in step A11.

---

### A8. Provision Azure infrastructure

**1 — Create Terraform variables file:**
```bash
cd ~/sightline/infra/environments/dev
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` — fill in all values:
```
resource_group_name = "rg-sightline"
location            = "australiaeast"
db_admin_password   = "<strong password — save it securely>"
developer_ip        = "<your public IP — run: curl ifconfig.me>"
api_image           = "acrsightline.azurecr.io/sightline-api:latest"
auth0_domain        = "dev-kr7ljpg5onbkey04.us.auth0.com"
auth0_api_audience  = "https://api.sightline.app"
```

**2 — Initialise, plan, and apply:**
```bash
terraform init
terraform plan
terraform apply
```

First apply creates: ACR, PostgreSQL Flexible Server, Key Vault, Container Apps Environment, Container App, Azure AI Search, media storage account, CDN (Front Door), Function App.

**3 — Container App first-deploy caveat:**

The Container App enters a Failed state on first apply because no image exists in ACR yet. This is expected — continue to A9, then return here to recover.

---

### A9. Build and push the first Docker image

```bash
# Authenticate to ACR
az acr login --name acrsightline

# Build and push — MUST use --platform linux/amd64
# Apple Silicon ARM64 builds will fail in Azure with a platform mismatch error.
cd ~/sightline
docker buildx build \
  --platform linux/amd64 \
  -t acrsightline.azurecr.io/sightline-api:latest \
  -f api/Dockerfile.prod \
  ./api \
  --push
```

**If Container App is in Failed state** (expected on first deploy — recover now):
```bash
cd ~/sightline/infra/environments/dev
terraform state rm module.api.azurerm_container_app.api
az containerapp delete --name ca-sightline-api --resource-group rg-sightline --yes
terraform apply
```

---

### A10. Initialise the Azure database

Run in this exact order.

**1 — Enable PostGIS (first time only):**
```bash
docker compose exec postgres psql \
  "postgresql://sightline_admin:YOUR_PASSWORD@psql-sightline-dev.postgres.database.azure.com:5432/sightline?sslmode=require" \
  -c "CREATE EXTENSION IF NOT EXISTS postgis;"
```

**2 — Run migrations:**
```bash
docker compose exec \
  -e DATABASE_URL_SYNC="postgresql://sightline_admin:YOUR_PASSWORD@psql-sightline-dev.postgres.database.azure.com:5432/sightline?sslmode=require" \
  -w /db api alembic upgrade head
```

**3 — Seed species:**
```bash
docker compose exec \
  -e DATABASE_URL_SYNC="postgresql://sightline_admin:YOUR_PASSWORD@psql-sightline-dev.postgres.database.azure.com:5432/sightline?sslmode=require" \
  api python /db/seed/seed_species.py
```

**4 — Seed synthetic sightings (optional — ~10 mins due to network latency):**
```bash
docker compose exec \
  -e DATABASE_URL_SYNC="postgresql://sightline_admin:YOUR_PASSWORD@psql-sightline-dev.postgres.database.azure.com:5432/sightline?sslmode=require" \
  api python /db/seed/seed_sightings.py
```

---

### A11. Configure GitHub Actions secrets

Go to: **GitHub repo → Settings → Secrets and variables → Actions → New repository secret**

| Secret | Value | Where to get it |
|---|---|---|
| `AZURE_CREDENTIALS` | Full JSON object | Output of `az ad sp create-for-rbac --json-auth` from step A7 |
| `ACR_LOGIN_SERVER` | `acrsightline.azurecr.io` | `terraform output acr_login_server` |
| `ACR_USERNAME` | ACR admin username | `az acr credential show --name acrsightline --query username -o tsv` |
| `ACR_PASSWORD` | ACR admin password | `az acr credential show --name acrsightline --query "passwords[0].value" -o tsv` |
| `CONTAINER_APP_NAME` | `ca-sightline-api` | Fixed value |
| `RESOURCE_GROUP` | `rg-sightline` | Fixed value |

**Configure the deployment gate:**

Go to: **Settings → Environments → New environment**
- Name: `dev`
- Required reviewer: your GitHub username

This gates the deploy job in `api-deploy.yml` and prevents automatic deployments without approval.

---

### A12. Verify Auth0 configuration

Auth0 is an external SaaS — already provisioned. On a fresh machine, verify the settings are correct before logging in.

1. Go to https://manage.auth0.com
2. **APIs** → confirm `https://api.sightline.app` exists with scopes `read:sightings` and `write:sightings`
3. **Applications → Sightline Web → Settings** — confirm:
   - Allowed Callback URLs: `http://localhost:3000/api/auth/callback`
   - Allowed Logout URLs: `http://localhost:3000`
   - Allowed Web Origins: `http://localhost:3000`
4. Copy the **Client Secret** → add to `.env` (`AUTH0_CLIENT_SECRET`) and `web/.env.local` (`AUTH0_CLIENT_SECRET`)

If API returns 401 after login: clear browser cookies and log in again. Sessions created before `AUTH0_AUDIENCE` is configured issue opaque tokens, not JWTs.

---

### A13. End-to-end smoke test

```bash
# Local API
curl http://localhost:8000/health
# Expected: {"status":"ok","environment":"local","version":"0.1.0"}

# Local species data
curl http://localhost:8000/v1/species/?limit=1
# Expected: JSON array with one species

# Azure API
curl https://ca-sightline-api.wittywave-8fb8cdba.australiaeast.azurecontainerapps.io/health
# Expected: {"status":"ok","environment":"dev","version":"0.1.0"}
```

Manual checks:
- [ ] Open http://localhost:3000 — map loads with Mapbox tiles
- [ ] Log in with Google — no 401 errors
- [ ] Submit a sighting — species autocomplete works, form submits, sighting appears on map
- [ ] Browse /species — list loads, detail page loads
- [ ] Azure Swagger UI: https://ca-sightline-api.wittywave-8fb8cdba.australiaeast.azurecontainerapps.io/docs

---

## Part B — Daily startup

Bring up an existing, already-configured system. Run in this order.

### B1. Docker Compose

```bash
cd ~/sightline
docker compose up -d
```

Starts: PostgreSQL/PostGIS (5432), pgAdmin (5050), FastAPI API (8000)

Check all healthy:
```bash
docker compose ps
```

If pgAdmin isn't running (sometimes stops after a Docker rebuild):
```bash
docker compose up -d pgadmin
```

### B2. Next.js dev server (separate terminal — keep open)

```bash
cd ~/sightline/web
npm run dev
```

Starts web frontend on http://localhost:3000. Leave this terminal open.

### B3. Claude Code

Open VSCode in `~/sightline`. Claude Code panel in sidebar. CLAUDE.md is read automatically on session start.

### B4. SQLTools (optional)

SQLTools connections are saved in VSCode settings:
- `sightline-local` — local Docker PostgreSQL
- `sightline-azure` — Azure PostgreSQL

Run queries from `docs/queries/` or open a new session file.

---

## Part C — Operations reference

### Local URLs

| Service | URL |
|---|---|
| Web frontend | http://localhost:3000 |
| API Swagger docs | http://localhost:8000/docs |
| API health check | http://localhost:8000/health |
| API ready check | http://localhost:8000/ready |
| pgAdmin | http://localhost:5050 |

---

### Environment files reference

| File | How to create | Contains |
|---|---|---|
| `.env` | `cp .env.example .env`, add Auth0 values | PostgreSQL credentials, pgAdmin, API Auth0 config |
| `web/.env.local` | Create manually — see A3 | Auth0 secret + client, Mapbox token, API URL |
| `infra/environments/dev/terraform.tfvars` | `cp terraform.tfvars.example terraform.tfvars`, fill in | DB password, developer IP, Auth0, API image |

None of these files are committed to git — all are in `.gitignore`.

---

### pgAdmin connection settings

Login with credentials from `.env` (PGADMIN_DEFAULT_EMAIL / PGADMIN_DEFAULT_PASSWORD)

Register server (if not already saved):
- Name: `sightline-local`
- Host: `postgres` (Docker network name — NOT localhost)
- Port: `5432`
- Database: `sightline`
- Username: from `.env` POSTGRES_USER
- Password: from `.env` POSTGRES_PASSWORD

---

### SQLTools connection settings

**Local:**
- Driver: PostgreSQL / Host: `localhost` / Port: `5432`
- Database: `sightline` / Username: `sightline`
- Password: from `.env` POSTGRES_PASSWORD / SSL: disabled

**Azure:**
- Driver: PostgreSQL / Host: `psql-sightline-dev.postgres.database.azure.com` / Port: `5432`
- Database: `sightline` / Username: `sightline_admin`
- Password: from `terraform.tfvars` db_admin_password / SSL: Require

Note: Use PostgreSQL `LIMIT` syntax, not SQL Server `TOP` syntax.

---

### Azure resources

| Resource | Value |
|---|---|
| Resource group | rg-sightline (australiaeast) |
| Live API URL | https://ca-sightline-api.wittywave-8fb8cdba.australiaeast.azurecontainerapps.io |
| Container App name | ca-sightline-api |
| Container Registry | acrsightline.azurecr.io |
| PostgreSQL server | psql-sightline-dev.postgres.database.azure.com |
| DB admin user | sightline_admin |
| DB password | in `terraform.tfvars` (gitignored) |
| Key Vault | https://kv-sightline-dev.vault.azure.net/ |
| Azure AI Search | https://search-sightline-dev.search.windows.net |
| Search API key | `terraform output -raw search_primary_key` |
| Media storage account | stsightlinemedia |
| CDN endpoint | cdnep-sightline-media-drcgcxdph5bjceh8.z02.azurefd.net |
| Function App | func-sightline-media (Python 3.11) |
| Event Grid subscription | evgs-sightline-media-raw (BlobCreated on media-raw → func-sightline-media) |
| Application Insights | appi-sightline-dev |
| Terraform state | stsightlinetfstate / container: tfstate / key: dev.terraform.tfstate |

Note: The Container App revision FQDN changes on each Terraform apply. The stable ingress URL (without revision suffix) is always `ca-sightline-api.wittywave-8fb8cdba.australiaeast.azurecontainerapps.io`.

---

### Auth0

| Item | Value |
|---|---|
| Dashboard | https://manage.auth0.com |
| Tenant domain | dev-kr7ljpg5onbkey04.us.auth0.com |
| API audience | https://api.sightline.app |
| Client ID | WN9aqjcky6ILPh5fBZa0Pf5M9nRTBZca |
| Client secret | in `.env` and `web/.env.local` (never committed) |
| Application | Sightline Web (SPA) |
| Scopes | read:sightings, write:sightings |
| Callback URL | http://localhost:3000/api/auth/callback |

---

### GitHub CI/CD

| Item | Value |
|---|---|
| Repo | github.com/jaredmorris25-demo/sightline |
| CI workflow | `.github/workflows/api-ci.yml` — triggers on PR to main/develop |
| CD workflow | `.github/workflows/api-deploy.yml` — triggers on merge to develop |
| CD approval | GitHub environment `dev` — requires manual approval before deploy |
| Actions tab | github.com/jaredmorris25-demo/sightline/actions |

Branch protection:
- `main` — PR required, no direct push, no deletion
- `develop` — PR required, no direct push, no deletion

GitHub secrets required:
`AZURE_CREDENTIALS`, `ACR_LOGIN_SERVER`, `ACR_USERNAME`, `ACR_PASSWORD`, `CONTAINER_APP_NAME`, `RESOURCE_GROUP`

Service principal: `sp-sightline-github-actions` (clientId: `be0d1334-87bd-407b-9440-43aa9afa0e82`)
**WARNING: Credentials need rotating before production launch.**

---

### Manual deployment to Azure

Use when deploying outside the CD pipeline. Do not skip steps.

```bash
# Step 1 — Verify Azure CLI auth
az account show --query "{subscription:name}" --output table
# If not authenticated: az login

# Step 2 — Log in to ACR
az acr login --name acrsightline
# Valid for a few hours — re-run if push fails with auth error

# Step 3 — Build and push (MUST use --platform linux/amd64)
cd ~/sightline
docker buildx build \
  --platform linux/amd64 \
  -t acrsightline.azurecr.io/sightline-api:latest \
  -f api/Dockerfile.prod \
  ./api \
  --push

# Step 4 — Deploy to Container Apps
az containerapp update \
  --name ca-sightline-api \
  --resource-group rg-sightline \
  --image acrsightline.azurecr.io/sightline-api:latest

# Step 5 — Verify
curl https://ca-sightline-api.wittywave-8fb8cdba.australiaeast.azurecontainerapps.io/health
# Expected: {"status":"ok","environment":"dev","version":"0.1.0"}
```

---

### Database operations

#### Run Alembic migration (Azure)
```bash
docker compose exec \
  -e DATABASE_URL_SYNC="postgresql://sightline_admin:YOUR_PASSWORD@psql-sightline-dev.postgres.database.azure.com:5432/sightline?sslmode=require" \
  -w /db api alembic upgrade head
```

#### Seed species data
```bash
# Local
docker compose exec \
  -e DATABASE_URL_SYNC=postgresql://sightline:localdevonly@postgres:5432/sightline \
  api python /db/seed/seed_species.py

# Azure
docker compose exec \
  -e DATABASE_URL_SYNC="postgresql://sightline_admin:YOUR_PASSWORD@psql-sightline-dev.postgres.database.azure.com:5432/sightline?sslmode=require" \
  api python /db/seed/seed_species.py
```

#### Seed synthetic sightings (10,000 records)
```bash
# Local
docker compose exec \
  -e DATABASE_URL_SYNC=postgresql://sightline:localdevonly@postgres:5432/sightline \
  api python /db/seed/seed_sightings.py

# Azure (~10 mins due to network latency)
docker compose exec \
  -e DATABASE_URL_SYNC="postgresql://sightline_admin:YOUR_PASSWORD@psql-sightline-dev.postgres.database.azure.com:5432/sightline?sslmode=require" \
  api python /db/seed/seed_sightings.py
```

All seed scripts are idempotent — safe to re-run.

#### Enable PostGIS on a fresh Azure database (first time only)
```bash
docker compose exec postgres psql \
  "postgresql://sightline_admin:YOUR_PASSWORD@psql-sightline-dev.postgres.database.azure.com:5432/sightline?sslmode=require" \
  -c "CREATE EXTENSION IF NOT EXISTS postgis;"
```

#### Backfill Azure AI Search index
```bash
docker compose exec \
  -e DATABASE_URL_SYNC="postgresql://sightline_admin:YOUR_PASSWORD@psql-sightline-dev.postgres.database.azure.com:5432/sightline?sslmode=require" \
  -e AZURE_SEARCH_ENDPOINT=https://search-sightline-dev.search.windows.net \
  -e AZURE_SEARCH_API_KEY=YOUR_KEY \
  api python /db/seed/backfill_search_index.py
```

---

### Deploy Azure Function (manual — separate from API CD pipeline)

The Function App is not part of the GitHub Actions CD pipeline. Deploy manually
from the `functions/` directory. Remote build is required — Consumption plan does
not install packages from a plain zip upload.

```bash
cd ~/sightline/functions
zip -r /tmp/functions.zip . -x '*.pyc' -x '__pycache__/*' -x 'local.settings.json'
az functionapp deployment source config-zip \
  --name func-sightline-media \
  --resource-group rg-sightline \
  --src /tmp/functions.zip \
  --build-remote true
```

After deploy, verify the function is registered:
```bash
az functionapp function list \
  --name func-sightline-media \
  --resource-group rg-sightline \
  --output table
```

Expected: `media_processor` listed with `IsDisabled = False`.

Deployment takes ~4–5 minutes (Oryx pip install runs server-side).
If deployment fails with SCM container restart error, restart the app and retry:
```bash
az functionapp restart --name func-sightline-media --resource-group rg-sightline
# Wait ~30 seconds, then re-run the config-zip command
```

---

### Git workflow

```
1. Create feature branch off develop
   git checkout develop && git pull origin develop
   git checkout -b feature/your-feature-name

2. Work, commit, push
   git add [specific files — never: git add . or git add -A]
   git commit -m "type: description"
   git push -u origin feature/your-feature-name

3. Open PR to develop on GitHub
   CI runs automatically (lint + tests)
   Squash and merge
   Delete feature branch after merge

4. Pull develop locally
   git checkout develop && git pull origin develop

5. CD pipeline triggers automatically
   Actions tab → approve the deploy job when prompted
   Smoke test runs automatically after deploy

6. Open PR develop → main (production promotion)
   Review carefully
   Create merge commit (not squash — preserves release marker)
```

Merge strategy:
- `feature/*` → `develop`: squash and merge
- `develop` → `main`: create merge commit

---

### Terraform operations

```bash
cd ~/sightline/infra/environments/dev

# First time, or after adding new modules
terraform init

# Check what will change
terraform plan

# Apply changes
terraform apply

# Get sensitive outputs
terraform output -raw search_primary_key
terraform output -raw media_storage_connection_string

# Recovery sequence if Container App enters failed state
terraform state rm module.api.azurerm_container_app.api
az containerapp delete --name ca-sightline-api --resource-group rg-sightline --yes
terraform apply
```

---

### Azure CLI — useful commands

```bash
# Check login
az account show

# List all resources in project
az resource list --resource-group rg-sightline --output table

# View Container App logs (live)
az containerapp logs show \
  --name ca-sightline-api \
  --resource-group rg-sightline \
  --follow

# View Container App revisions
az containerapp revision list \
  --name ca-sightline-api \
  --resource-group rg-sightline \
  --output table

# Get ACR credentials (for GitHub secrets setup)
az acr credential show --name acrsightline --output table

# Check for existing search services
az resource list --resource-type Microsoft.Search/searchServices --output table
```

---

### Key file locations

| File | Purpose |
|---|---|
| `~/sightline/CLAUDE.md` | Project context — read by Claude Code every session |
| `~/sightline/docs/DEVLOG.md` | Session log — update at end of every session |
| `~/sightline/docs/COLD-START.md` | This file |
| `~/sightline/.env` | Local env variables (gitignored) |
| `~/sightline/.env.example` | Template — checked in, safe to read |
| `~/sightline/web/.env.local` | Web env variables (gitignored) |
| `~/sightline/infra/environments/dev/terraform.tfvars` | Terraform variables (gitignored) |
| `~/sightline/infra/environments/dev/terraform.tfvars.example` | TF template — checked in |
| `~/sightline/docs/adr/` | Architecture Decision Records |
| `~/sightline/docs/queries/` | Saved SQL queries for VSCode SQLTools |
| `~/sightline/api/Dockerfile` | Local dev Dockerfile (with --reload) |
| `~/sightline/api/Dockerfile.prod` | Production Dockerfile (linux/amd64, 2 workers) |

---

### Environment overview

| Environment | Where | API URL | Status |
|---|---|---|---|
| Local | Mac / Docker Compose | http://localhost:8000 | `docker compose up -d` |
| Azure Dev | Azure Container Apps | https://ca-sightline-api.wittywave-8fb8cdba.australiaeast.azurecontainerapps.io | Live |
| Azure Prod | Not yet created | — | Phase 5+ |

---

### Ports reference

| Port | Service |
|---|---|
| 3000 | Next.js web frontend (local) |
| 5050 | pgAdmin (local) |
| 5432 | PostgreSQL (local Docker) |
| 8000 | FastAPI API (local Docker) |

---

### Current data state

| Database | Species | Sightings | Users |
|---|---|---|---|
| Local | 255 | 10,001 | 1 (your Google account) |
| Azure | 255 | 10,001 | 1 (your Google account) |

Sightings: 1 real (Laughing Kookaburra, Brisbane, Apr 2026) +
10,000 synthetic across Australia weighted by population density.
