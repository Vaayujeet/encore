# ENCORE - Event Correlator

## Setup Requirements

### ElasticSearch

- ELK Cluster must have at least one `ingest` node. This is required for the Correlator ingest pipelines to work properly.
- Better to NOT create a Monitor Tool named `Default Tool` and thus modify the `default-tool-event-pipeline` ingest pipeline.
  - The `default-tool-event-pipeline` ingest pipeline is used for events that are currently sent by tools not mapped in Correlator.

### GLPI

- Setup GLPi for the first time
  - SQL Server = mysql
  - MYSQL_USER = glpi-user
  - MYSQL_PASSWORD = glpi-pass
  - MYSQL_DATABASE = glpidb

GLPI_APP_TOKEN can be set in GLPI: Home -> Setup -> General -> API (Set Enable Rest API: Yes) -> [Select or Add API Client: full access from anywhere] -> Application token. Also, update `IPv4 address range start` and `IPv4 address range end` to `0.0.0.0` or blank or any valid value.

GLPI_API_TOKEN can be set for a user in GLPI: Home -> Administration -> [Select User: glpi] -> Remote access keys -> API token

### Postgres

### Redis
