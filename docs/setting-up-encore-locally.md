# Setting up Encore

## Table of Contents

- [Setting up Encore](#setting-up-encore)
  - [Table of Contents](#table-of-contents)
  - [🌟 Scalable for Enterprises, Accessible for Small Projects](#-scalable-for-enterprises-accessible-for-small-projects)
  - [🛠️ Try Encore Locally with Docker](#️-try-encore-locally-with-docker)
    - [🐳 Steps to Set Up Locally](#-steps-to-set-up-locally)
    - [⚙️ Configuring Existing Infrastructure](#️-configuring-existing-infrastructure)
  - [🧭 Next Step - Explore](#-next-step---explore)

## 🌟 Scalable for Enterprises, Accessible for Small Projects

Encore is designed to meet the needs of **large enterprises and organizations** managing complex infrastructures, but it’s flexible enough to support **small-scale projects** as well. Whether you’re monitoring thousands of assets or just starting with a few, Encore provides the tools to process events efficiently and automate incident response.

To make it easy to explore and understand Encore’s capabilities, we offer a **Dockerized setup** that allows users to run the application locally. This setup is perfect for:

- Evaluating Encore’s features in a sandbox environment.
- Testing configurations before deploying to production.
- Experimenting with custom rules and integrations.

## 🛠️ Try Encore Locally with Docker

Our Dockerized setup packages all necessary components, including:

- **ELK (Elasticsearch, Logstash, Kibana)** for event storage and visualization.
- **PostgreSQL** as the database.
- **Redis** as the message broker.
- **GLPI** for ticket management.

### 🐳 Steps to Set Up Locally

1. **Clone the Repository**:

   ```bash
   git clone https://github.com/Vaayujeet/encore.git
   cd encore
   ```

2. **Run Docker Compose**:  
   Build and start the application using Docker Compose:

   ```bash
   docker compose -f "docker\docker-compose.yml" up -d --build
   ```

3. **Perform One time Setup**

   - **ElasticSearch**

     - Update Elasticsearch Certificate Fingerprint in the [`docker\encore.env`](../docker/encore.env) file. Elasticsearch Certificate Fingerprint can be obtained by executing bellow command from Encore/ELK container shell.

     ```bash
     openssl s_client -connect es01:9200 -showcerts </dev/null 2>/dev/null | openssl x509 -noout -fingerprint -sha256 | sed 's/.*=//'
     ```

     - Command to connect Encore container shell

     ```bash
     docker compose -f docker\docker-compose.yml exec encore bash
     ```

   - **GLPI**

     - Setup GLPi for the first time
       - SQL Server = mysql
       - MYSQL_USER = glpi-user
       - MYSQL_PASSWORD = glpi-pass
       - MYSQL_DATABASE = glpidb
     - GLPI_APP_TOKEN can be set in GLPI: Home -> Setup -> General -> API (Set Enable Rest API: Yes) -> [Select or Add API Client: full access from anywhere] -> Application token. Also, update `IPv4 address range start` and `IPv4 address range end` to `0.0.0.0` or blank or any valid value.
     - GLPI_API_TOKEN can be set for a user in GLPI: Home -> Administration -> [Select User: glpi] -> Remote access keys -> API token
     - Update GLPI_APP_TOKEN and GLPI_API_TOKEN in the [`docker\encore.env`](../docker/encore.env) file.

   - **Encore**:

     - Connect to Encore container shell

     ```bash
     docker compose -f docker\docker-compose.yml exec encore bash
     ```

     - Execute below commands in the shell (you should be in the `/mnt/application/encore` directory).

     ```bash
     # Database deployment
     python manage.py migrate

     # Create a super user to manage the Encore Admin site
     export DJANGO_SUPERUSER_PASSWORD="correlator"
     python manage.py createsuperuser --username correlator --email admin@encore.com --noinput

     # Set the Django Site domain.
     python manage.py shell_plus <<EOF
     s = Site.objects.first()
     s.domain = "localhost"
     s.save()
     EOF
     ```

     - Restart the Encore container

4. **Access Encore Services**:

   - **Encore App**: <http://localhost:8000/admin/>{:target="_blank"}
   - **Kibana (for Elasticsearch visualization)**: <http://localhost:5601>
   - **GLPI (for ticket management)**: <http://localhost:30080>

5. **Optional services for administration/monitoring**

   - **Adminer**: <http://localhost:8080> (for Postgres/MySQL administration)
   - **Flower**: <http://localhost:5555> (for Celery monitoring)

6. **Test if everything is working**

   - Monitor in Kibana

   - Connect to Encore container shell once again

   ```bash
   docker compose -f docker\docker-compose.yml exec encore bash
   ```

   - Execute below commands in the shell (you should be in the `/mnt/application/encore` directory).

   ```bash
   python manage.py test_case tca
   ```

   - This should create a Down event and then later an Up event which eventually gets linked to the Down event and ultimately both events are resolved.

### ⚙️ Configuring Existing Infrastructure

If you already have ELK, PostgreSQL, Redis, or GLPI installed in your environment, you can configure Encore to use these existing services. Update the Django environment variables in the [`docker\encore.env`](../docker/encore.env) file to connect to your infrastructure. Also, comment out the unwanted services from the [`docker\docker-compose.yml`](../docker/docker-compose.yml) file.

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

## 🧭 Next Step - Explore

Now that you have setup Encore, lets explore it's features.
