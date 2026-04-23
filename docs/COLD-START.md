# Sightline — Cold Start Reference

> Keep this file up to date as new services, infrastructure, and apps are added.
> Last updated: 2026-04-23

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

### 2. Next.js dev server (separate terminal — keep open)
```bash
cd ~/sightline/web
npm run dev
```
Starts web frontend on http://localhost:3000
Must stay running in its own terminal window.

### 3. Claude Code
Open VSCode in ~/sightline. Claude Code panel in sidebar.
Reads CLAUDE.md automatically on session start.

---

## Local URLs

| Service | URL |
|---|---|
| Web frontend | http://localhost:3000 |
| API Swagger docs | http://localhost:8000/docs |
| API health check | http://localhost:8000/health |
| pgAdmin | http://localhost:5050 |

---

## pgAdmin connection settings

Login with credentials from `~/.env` (PGADMIN_DEFAULT_EMAIL / PGADMIN_DEFAULT_PASSWORD)

Register server:
- Name: `sightline-local`
- Host: `postgres` (Docker network name — NOT localhost)
- Port: `5432`
- Database: `sightline`
- Username: from `.env` POSTGRES_USER
- Password: from `.env` POSTGRES_PASSWORD

---

## Azure resources

| Resource | Value |
|---|---|
| Resource group | rg-sightline (australiaeast) |
| Live API URL | https://ca-sightline-api.wittywave-8fb8cdba.australiaeast.azurecontainerapps.io |
| Container Registry | acrsightline.azurecr.io |
| PostgreSQL server | psql-sightline-dev.postgres.database.azure.com |
| DB admin user | sightline_admin |
| DB password | in terraform.tfvars (gitignored) |
| Key Vault | https://kv-sightline-dev.vault.azure.net/ |
| Terraform state | stsightlinetfstate / tfstate / dev.terraform.tfstate |

---

## Auth0

| Item | Value |
|---|---|
| Dashboard | https://manage.auth0.com |
| Tenant domain | dev-kr7ljpg5onbkey04.us.auth0.com |
| API audience | https://api.sightline.app |
| Client ID | WN9aqjcky6ILPh5fBZa0Pf5M9nRTBZca |
| Client secret | in web/.env.local — AUTH0_CLIENT_SECRET |

---

## Manual deployment to Azure

Run these steps every time you deploy a new API version. Do not skip steps.

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

### Step 3 — Build production image
```bash
cd ~/sightline
docker build -t acrsightline.azurecr.io/sightline-api:latest -f api/Dockerfile.prod ./api
```

### Step 4 — Push to ACR
```bash
docker push acrsightline.azurecr.io/sightline-api:latest
```

### Step 5 — Deploy to Container Apps
```bash
az containerapp update \
  --name ca-sightline-api \
  --resource-group rg-sightline \
  --image acrsightline.azurecr.io/sightline-api:latest
```

### Step 6 — Verify
```bash
curl https://ca-sightline-api.wittywave-8fb8cdba.australiaeast.azurecontainerapps.io/health
```
Expected: `{"status":"ok","environment":"dev","version":"0.1.0"}`

---

## Run Alembic migration against Azure database

Use when a new migration needs to be applied to the Azure PostgreSQL instance:

```bash
docker compose exec \
  -e DATABASE_URL_SYNC="postgresql://sightline_admin:YOUR_PASSWORD@psql-sightline-dev.postgres.database.azure.com:5432/sightline?sslmode=require" \
  -w /db api alembic upgrade head
```

---

## Seed species data against Azure database

```bash
docker compose exec \
  -e DATABASE_URL_SYNC="postgresql://sightline_admin:YOUR_PASSWORD@psql-sightline-dev.postgres.database.azure.com:5432/sightline?sslmode=require" \
  api python /db/seed/seed_species.py
```

---

## Git workflow — feature to production

```
1. Create feature branch off develop
   git checkout develop
   git checkout -b feature/your-feature-name

2. Work, commit, push
   git add [specific files]
   git commit -m "feat: description"
   git push -u origin feature/your-feature-name

3. Open PR → develop on GitHub
   CI runs automatically (lint + tests)
   Squash and merge

4. Pull develop locally
   git checkout develop
   git pull origin develop

5. Deploy to Azure manually (steps above)

6. Open PR develop → main on GitHub
   Review carefully — this is production promotion
   Create merge commit (not squash — preserves release marker)

7. Delete feature branch after merge
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

# Terraform — plan infrastructure changes
cd ~/sightline/infra/environments/dev
terraform plan

# Terraform — apply infrastructure changes
terraform apply
```

---

## Key file locations

| File | Purpose |
|---|---|
| ~/sightline/CLAUDE.md | Project context — read by Claude Code every session |
| ~/sightline/docs/DEVLOG.md | Session log — update at end of every session |
| ~/sightline/.env | Local environment variables (gitignored) |
| ~/sightline/web/.env.local | Web environment variables (gitignored) |
| ~/sightline/infra/environments/dev/terraform.tfvars | Terraform variables (gitignored) |
| ~/sightline/docs/adr/ | Architecture Decision Records |
| ~/sightline/docs/COLD-START.md | This file |

---

## Environment overview

| Environment | Where | API URL | Status |
|---|---|---|---|
| Local | Mac / Docker Compose | http://localhost:8000 | Always available when Docker running |
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
