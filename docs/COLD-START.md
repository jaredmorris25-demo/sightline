# Sightline — Cold Start Reference

> Keep this file up to date as new services, infrastructure, and apps are added.
> Last updated: 2026-04-27

---

## Starting from cold — run in this order

### 1. Docker Compose (local services)
```bash
cd ~/sightline
docker compose up -d
```
Starts: PostgreSQL/PostGIS (5432), pgAdmin (5050), FastAPI API (8000)

Check all three are healthy:
```bash
docker compose ps
```

If pgAdmin isn't running (sometimes stops after rebuild):
```bash
docker compose up -d pgadmin
```

### 2. Next.js dev server (separate terminal — keep open)
```bash
cd ~/sightline/web
npm run dev
```
Starts web frontend on http://localhost:3000
Must stay running in its own terminal window. Leave it open.

### 3. Claude Code
Open VSCode in ~/sightline. Claude Code panel in sidebar.
Reads CLAUDE.md automatically on session start.

### 4. SQLTools (optional — for database queries in VSCode)
SQLTools connections are saved in VSCode settings.
- `sightline-azure` — connects to Azure PostgreSQL
- `sightline-local` — connects to local Docker PostgreSQL
Run queries from `docs/queries/` or open a new session file.

---

## Local URLs

| Service | URL |
|---|---|
| Web frontend | http://localhost:3000 |
| API Swagger docs | http://localhost:8000/docs |
| API health check | http://localhost:8000/health |
| API ready check | http://localhost:8000/ready |
| pgAdmin | http://localhost:5050 |

---

## pgAdmin connection settings

Login with credentials from `~/.env` (PGADMIN_DEFAULT_EMAIL / PGADMIN_DEFAULT_PASSWORD)

Register server (if not already saved):
- Name: `sightline-local`
- Host: `postgres` (Docker network name — NOT localhost)
- Port: `5432`
- Database: `sightline`
- Username: from `.env` POSTGRES_USER
- Password: from `.env` POSTGRES_PASSWORD

---

## SQLTools connection settings (VSCode)

**Local:**
- Driver: PostgreSQL
- Host: `localhost`
- Port: `5432`
- Database: `sightline`
- Username: `sightline`
- Password: from `.env` POSTGRES_PASSWORD
- SSL: disabled

**Azure:**
- Driver: PostgreSQL
- Host: `psql-sightline-dev.postgres.database.azure.com`
- Port: `5432`
- Database: `sightline`
- Username: `sightline_admin`
- Password: from `terraform.tfvars` db_admin_password
- SSL: Require

Note: Use PostgreSQL LIMIT syntax, not SQL Server TOP syntax.

---

## Azure resources

| Resource | Value |
|---|---|
| Resource group | rg-sightline (australiaeast) |
| Live API URL | https://ca-sightline-api.wittywave-8fb8cdba.australiaeast.azurecontainerapps.io |
| Container App name | ca-sightline-api |
| Container Registry | acrsightline.azurecr.io |
| PostgreSQL server | psql-sightline-dev.postgres.database.azure.com |
| DB admin user | sightline_admin |
| DB password | in terraform.tfvars (gitignored) |
| Key Vault | https://kv-sightline-dev.vault.azure.net/ |
| Azure AI Search | https://search-sightline-dev.search.windows.net |
| Search API key | run: terraform output -raw search_primary_key |
| Media Storage Account | stsightlinemedia |
| CDN Endpoint | cdnep-sightline-media-drcgcxdph5bjceh8.z02.azurefd.net |
| Function App | func-sightline-media (Python 3.11) |
| Application Insights | appi-sightline-dev |
| Terraform state | stsightlinetfstate / tfstate / dev.terraform.tfstate |

Note: The Container App revision FQDN changes on each Terraform apply.
The stable ingress URL (without revision suffix) is always:
ca-sightline-api.wittywave-8fb8cdba.australiaeast.azurecontainerapps.io

---

## Auth0

| Item | Value |
|---|---|
| Dashboard | https://manage.auth0.com |
| Tenant domain | dev-kr7ljpg5onbkey04.us.auth0.com |
| API audience | https://api.sightline.app |
| Client ID | WN9aqjcky6ILPh5fBZa0Pf5M9nRTBZca |
| Client secret | in web/.env.local — AUTH0_CLIENT_SECRET |
| Application | Sightline Web (SPA) |
| Scopes | read:sightings, write:sightings |
| Callback URL | http://localhost:3000/api/auth/callback |

Important: Auth0 sessions created before AUTH0_AUDIENCE was configured issue
opaque tokens. If JWT validation fails, clear browser cookies and log in again.

---

## GitHub CI/CD

| Item | Value |
|---|---|
| Repo | github.com/jaredmorris25-demo/sightline |
| CI workflow | .github/workflows/api-ci.yml — triggers on PR to main/develop |
| CD workflow | .github/workflows/api-deploy.yml — triggers on merge to develop |
| CD approval | GitHub environment `dev` — requires manual approval before deploy |
| Actions tab | github.com/jaredmorris25-demo/sightline/actions |

Branch protection:
- `main` — PR required, no direct push, no deletion
- `develop` — PR required, no direct push, no deletion

GitHub secrets required for CD:
AZURE_CREDENTIALS, ACR_LOGIN_SERVER, ACR_USERNAME, ACR_PASSWORD,
CONTAINER_APP_NAME, RESOURCE_GROUP

Service principal: sp-sightline-github-actions
WARNING: Credentials need rotating before production launch.

---

## Manual deployment to Azure

Run these steps when deploying outside of the CD pipeline. Do not skip steps.

### Step 1 — Check Azure CLI is authenticated
```bash
az account show --query "{subscription:name}" --output table
```
If not authenticated: `az login`

### Step 2 — Login to ACR
```bash
az acr login --name acrsightline
```
Valid for a few hours. Re-run if push fails with auth error.

### Step 3 — Build production image (MUST use --platform linux/amd64)
```bash
cd ~/sightline
docker buildx build \
  --platform linux/amd64 \
  -t acrsightline.azurecr.io/sightline-api:latest \
  -f api/Dockerfile.prod \
  ./api \
  --push
```

WARNING: Apple Silicon (ARM64) builds will fail in Azure with platform mismatch.
Always use --platform linux/amd64. The --push flag pushes directly to ACR.

### Step 4 — Deploy to Container Apps
```bash
az containerapp update \
  --name ca-sightline-api \
  --resource-group rg-sightline \
  --image acrsightline.azurecr.io/sightline-api:latest
```

### Step 5 — Verify
```bash
curl https://ca-sightline-api.wittywave-8fb8cdba.australiaeast.azurecontainerapps.io/health
```
Expected: {"status":"ok","environment":"dev","version":"0.1.0"}

---

## Database operations

### Run Alembic migration against Azure database
```bash
docker compose exec \
  -e DATABASE_URL_SYNC="postgresql://sightline_admin:YOUR_PASSWORD@psql-sightline-dev.postgres.database.azure.com:5432/sightline?sslmode=require" \
  -w /db api alembic upgrade head
```

### Seed species data
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

### Seed synthetic sightings (10,000 records)
```bash
# Local
docker compose exec \
  -e DATABASE_URL_SYNC=postgresql://sightline:localdevonly@postgres:5432/sightline \
  api python /db/seed/seed_sightings.py

# Azure (takes ~10 mins due to network latency)
docker compose exec \
  -e DATABASE_URL_SYNC="postgresql://sightline_admin:YOUR_PASSWORD@psql-sightline-dev.postgres.database.azure.com:5432/sightline?sslmode=require" \
  api python /db/seed/seed_sightings.py
```

Seed scripts are idempotent — safe to re-run. Will skip if already seeded.

### Enable PostGIS on a fresh Azure database (run once after provisioning)
```bash
docker compose exec postgres psql \
  "postgresql://sightline_admin:YOUR_PASSWORD@psql-sightline-dev.postgres.database.azure.com:5432/sightline?sslmode=require" \
  -c "CREATE EXTENSION IF NOT EXISTS postgis;"
```

### Backfill Azure AI Search species index
```bash
docker compose exec \
  -e DATABASE_URL_SYNC=postgresql://sightline:localdevonly@postgres:5432/sightline \
  -e AZURE_SEARCH_ENDPOINT=https://search-sightline-dev.search.windows.net \
  -e AZURE_SEARCH_API_KEY=YOUR_KEY \
  api python /db/seed/backfill_search_index.py
  ```

---

## Media pipeline

Media processing pipeline — Phase 5A. See docs/adr/ for design decisions.

---

## Git workflow — feature to production

```
1. Create feature branch off develop
   git checkout develop
   git pull origin develop
   git checkout -b feature/your-feature-name

2. Work, commit, push
   git add [specific files — not git add .]
   git commit -m "type: description"
   git push -u origin feature/your-feature-name

3. Open PR to develop on GitHub
   CI runs automatically (lint + tests)
   Squash and merge
   Delete feature branch after merge

4. Pull develop locally
   git checkout develop
   git pull origin develop

5. CD pipeline triggers automatically
   Go to Actions tab — approve the deploy job when prompted
   Smoke test runs automatically after deploy

6. Open PR develop to main (production promotion)
   Review carefully
   Create merge commit (not squash — preserves release marker)
```

Merge strategy:
- feature/* to develop: squash and merge
- develop to main: create merge commit

---

## Terraform operations

```bash
cd ~/sightline/infra/environments/dev

# Check what will change
terraform plan

# Apply changes
terraform apply

# Get sensitive outputs
terraform output -raw search_primary_key

# Recovery sequence if Container App enters failed state:
# 1. terraform state rm module.api.azurerm_container_app.api
# 2. az containerapp delete --name ca-sightline-api --resource-group rg-sightline --yes
# 3. terraform apply
```

---

## Azure CLI — useful commands

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

# Check for existing search services
az resource list --resource-type Microsoft.Search/searchServices --output table
```

---

## Key file locations

| File | Purpose |
|---|---|
| ~/sightline/CLAUDE.md | Project context — read by Claude Code every session |
| ~/sightline/docs/DEVLOG.md | Session log — update at end of every session |
| ~/sightline/docs/COLD-START.md | This file |
| ~/sightline/.env | Local environment variables (gitignored) |
| ~/sightline/web/.env.local | Web environment variables (gitignored) |
| ~/sightline/infra/environments/dev/terraform.tfvars | Terraform variables (gitignored) |
| ~/sightline/docs/adr/ | Architecture Decision Records |
| ~/sightline/docs/queries/ | Saved SQL queries for VSCode SQLTools |
| ~/sightline/api/Dockerfile | Local dev Dockerfile (with --reload) |
| ~/sightline/api/Dockerfile.prod | Production Dockerfile (linux/amd64, 2 workers) |

---

## Environment overview

| Environment | Where | API URL | Status |
|---|---|---|---|
| Local | Mac / Docker Compose | http://localhost:8000 | Start with docker compose up -d |
| Azure Dev | Azure Container Apps | https://ca-sightline-api.wittywave-8fb8cdba.australiaeast.azurecontainerapps.io | Live |
| Azure Prod | Not yet created | — | Phase 5+ |

---

## Ports reference

| Port | Service |
|---|---|
| 3000 | Next.js web frontend (local) |
| 5050 | pgAdmin (local) |
| 5432 | PostgreSQL (local Docker) |
| 8000 | FastAPI API (local Docker) |

---

## Current data state

| Database | Species | Sightings | Users |
|---|---|---|---|
| Local | 255 | 10,001 | 1 (your Google account) |
| Azure | 255 | 10,001 | 1 (your Google account) |

Sightings: 1 real (Laughing Kookaburra, Brisbane, Apr 2026) +
10,000 synthetic across Australia weighted by population density.
