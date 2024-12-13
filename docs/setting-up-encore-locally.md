# Setting up Encore

## Table of Contents

- [Setting up Encore](#setting-up-encore)
  - [Table of Contents](#table-of-contents)
  - [🌟 Scalable for Enterprises, Accessible for Small Projects](#-scalable-for-enterprises-accessible-for-small-projects)
  - [🛠️ Try Encore Locally with Docker](#️-try-encore-locally-with-docker)
  - [🐳 Steps to Set Up Encore Locally](#-steps-to-set-up-encore-locally)
    - [1. Clone the Repository](#1-clone-the-repository)
    - [2. Run Docker Compose](#2-run-docker-compose)
    - [3. Perform One-Time Setup](#3-perform-one-time-setup)
      - [**Elasticsearch**](#elasticsearch)
      - [**GLPI**](#glpi)
      - [**Encore**](#encore)
    - [4. Access Encore Services](#4-access-encore-services)
    - [5. Test the Setup](#5-test-the-setup)
    - [⚙️ Configuring Existing Infrastructure](#️-configuring-existing-infrastructure)
  - [🧭 Next Step - Explore](#-next-step---explore)

---

## 🌟 Scalable for Enterprises, Accessible for Small Projects

Encore is designed to meet the needs of **large enterprises and organizations** managing complex infrastructures, but it’s flexible enough to support **small-scale projects** as well. Whether you’re monitoring thousands of assets or just starting with a few, Encore provides the tools to process events efficiently and automate incident response.

To make it easy to explore and understand Encore’s capabilities, we offer a **Dockerized setup** that allows users to run the application locally. This setup is perfect for:

- Evaluating Encore’s features in a sandbox environment.
- Testing configurations before deploying to production.
- Experimenting with custom rules and integrations.

---

## 🛠️ Try Encore Locally with Docker

Our Dockerized setup packages all necessary components, including:

- **ELK (Elasticsearch, Logstash, Kibana)** for event storage and visualization.
- **PostgreSQL** as the database.
- **Redis** as the message broker.
- **GLPI** for ticket management.

---

## 🐳 Steps to Set Up Encore Locally

### 1. Clone the Repository

```bash
git clone https://github.com/Vaayujeet/encore.git
cd encore
```

### 2. Run Docker Compose

Build and start the application using Docker Compose:

```bash
docker compose -f "docker/docker-compose.yml" up -d --build
```

### 3. Perform One-Time Setup

#### **Elasticsearch**

1. Update the Elasticsearch Certificate Fingerprint in the `docker/encore.env` file.

   - To fetch the fingerprint, run the following command (ensure you’re in `/mnt/application/encore`):

     Bash:

     ```bash
     fingerprint = $(docker compose -f docker/docker-compose.yml exec encore bash -c "openssl s_client -connect es01:9200 -showcerts </dev/null 2>/dev/null | openssl x509 -noout -fingerprint -sha256 | sed 's/.*=//'")
     ```

     PowerShell:

     ```powershell
     $fingerprint = Invoke-Command { docker compose -f docker/docker-compose.yml exec encore bash -c "openssl s_client -connect es01:9200 -showcerts </dev/null 2>/dev/null | openssl x509 -noout -fingerprint -sha256 | sed 's/.*=//'" }
     ```

   - Update the `docker/encore.env` file to include the fingerprint:

     Bash:

     ```bash
     sed -i "s/ELASTIC_CERT_FINGERPRINT=[^ ]*/ELASTIC_CERT_FINGERPRINT=$fingerprint/" docker/encore.env
     ```

     PowerShell:

     ```powershell
     (Get-Content .\docker\encore.env) -replace "ELASTIC_CERT_FINGERPRINT=.*", "ELASTIC_CERT_FINGERPRINT=$fingerprint" | Set-Content .\docker\encore.env
     ```

#### **GLPI**

1. Open [http://localhost:30080](http://localhost:30080) and [Set up GLPI](https://glpi-install.readthedocs.io/en/latest/install/wizard.html) with the following configurations:

   - **SQL Server**: `mysql`
   - **MYSQL_USER**: `glpi-user`
   - **MYSQL_PASSWORD**: `glpi-pass`
   - **MYSQL_DATABASE**: `glpidb`

   Note the default user accounts / passwords created.

2. Configure API tokens:

   GLPI Admin user/password is `glpi`/`glpi`.

   - **GLPI_APP_TOKEN**:
     - Navigate to **Home -> Setup -> General -> API**.
     - Enable "REST API" and click Save.
     - Add an API client with full access and regenerate/copy the "Application token".
     - Also, update `IPv4 address range start` and `IPv4 address range end` to `0.0.0.0` or blank or any valid value.
     - Save changes.
   - **GLPI_API_TOKEN**:
     - Navigate to **Home -> Administration -> Users**.
     - Select a user (e.g., `glpi`) and configure the API token under "Remote Access Keys".

3. Update the `GLPI_APP_TOKEN` and `GLPI_API_TOKEN` in the `docker/encore.env` file.

   Bash:

   ```bash
   glpi_app_token = "app-token-from-above-step"
   glpi_api_token = "api-token-from-above-step"

   sed -i -e "s/GLPI_APP_TOKEN=[^ ]*/GLPI_APP_TOKEN=$glpi_app_token/" -e "s/GLPI_API_TOKEN=[^ ]*/GLPI_API_TOKEN=$glpi_api_token/" docker/encore.env
   ```

   PowerShell:

   ```powershell
   $glpi_app_token = "app-token-from-above-step"
   $glpi_api_token = "api-token-from-above-step"

   (Get-Content .\docker\encore.env) `
      -replace "GLPI_APP_TOKEN=.*", "GLPI_APP_TOKEN=$glpi_app_token" `
      -replace "GLPI_API_TOKEN=.*", "GLPI_API_TOKEN=$glpi_api_token" | Set-Content .\docker\encore.env
   ```

#### **Encore**

1. Execute one-time Setup and Restart the Encore container:

   ```bash
   docker compose -f docker/docker-compose.yml exec encore bash -c /mnt/application/scripts/one_time_django.sh
   docker compose -f docker/docker-compose.yml restart encore
   ```

### 4. Access Encore Services

| **Service**              | **URL**                                                      | **User**   | **Password** |
| ------------------------ | ------------------------------------------------------------ | ---------- | ------------ |
| Encore Admin Panel       | [http://localhost:8000/admin/](http://localhost:8000/admin/) | correlator | correlator   |
| Kibana (Elasticsearch)   | [http://localhost:5601](http://localhost:5601)               | elastic    | correlator   |
| GLPI (Ticket Management) | [http://localhost:30080](http://localhost:30080)             | glpi       | glpi         |

Optional services:

| **Service**                | **URL**                                        | **Login Settings**                                 | **User**   | **Password** |
| -------------------------- | ---------------------------------------------- | -------------------------------------------------- | ---------- | ------------ |
| Adminer (DB Admin)         | [http://localhost:8080](http://localhost:8080) | System: _postgreSQL_, Server: _pgdb_, DB: _encore_ | correlator | correlator   |
| Flower (Celery Monitoring) | [http://localhost:5555](http://localhost:5555) |                                                    |            |              |

### 5. Test the Setup

1. Connect to the Encore container shell:

   ```bash
   docker compose -f docker/docker-compose.yml exec encore bash
   ```

2. Run the test case to verify event correlation:

   ```bash
   python manage.py test_case tca
   ```

3. **Expected Output**:

   - A "Down" event is created.
   - An "Up" event is linked to the "Down" event.
   - Both events are resolved automatically.

4. Monitor events in **Kibana** to verify the setup.

---

### ⚙️ Configuring Existing Infrastructure

If you already have ELK, PostgreSQL, Redis, or GLPI installed, you can configure Encore to use these services. Update the Django environment variables in the [`docker/encore.env`](../docker/encore.env) file and comment out the corresponding services in the [`docker/docker-compose.yml`](../docker/docker-compose.yml) file.

Example configurations for `docker/encore.env`:

```properties
# ###### ELK Settings ######

ELASTIC_HOST=https://es01:9200

# USE_ELASTIC_AUTH=False
# ELASTIC_USER=elastic
# ELASTIC_PASSWORD=correlator

# We use these for Dockerized Setup
USE_ELASTIC_CERT=True
ELASTIC_CERT_FINGERPRINT=CopyElasticSearchCertificateFingerprint

# ###### GLPI Settings ######

GLPI_HOST=http://glpi:80
GLPI_APP_TOKEN=glpi-app-token-is-required
GLPI_API_TOKEN=glpi-user-api-token-is-required

# ###### Postgres Settings ######

PG_DB_NAME=encore
PG_DB_USER=correlator
PG_DB_PWD=correlator
PG_DB_HOST=pgdb
PG_DB_PORT=5432

# ###### Redis Settings ######

REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB_NO=0

```

---

## 🧭 Next Step - Explore

Now that you’ve set up Encore, let’s explore its features and see how it can optimize event processing and incident management for your projects!

---
