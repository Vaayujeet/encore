# Encore: Event Correlator

Encore is a modular and scalable event correlation platform designed for enterprises managing complex infrastructures, as well as smaller projects seeking efficient event processing. Built with **Django** and **Celery**, Encore processes and correlates large event streams in real-time, reducing noise and automating incident response.

The platform supports integration with **ELK**, **GLPI**, **PostgreSQL**, and **Redis**, but its modular design allows seamless replacement of these components. Currently at the **MVP stage**, Encore provides robust features like event tagging, correlation, and automated ticketing, making it production-ready and extensible for diverse use cases.

---

## Table of Contents

- [Encore: Event Correlator](#encore-event-correlator)
  - [Table of Contents](#table-of-contents)
  - [✨ Key Features](#-key-features)
    - [Core Features in the MVP](#core-features-in-the-mvp)
  - [🚀 Getting Started](#-getting-started)
    - [Local Setup](#local-setup)
  - [🔄 Workflow Overview](#-workflow-overview)
  - [🛠️ Technology Stack](#️-technology-stack)
  - [🏗️ Roadmap](#️-roadmap)
  - [🏆 Contributing](#-contributing)
  - [📜 License](#-license)
  - [📬 Contact Us](#-contact-us)

---

## ✨ Key Features

### Core Features in the MVP

1. **Real-Time Event Ingestion**:

   - Accepts events in **JSON format** via API and processes them in real time.

2. **Event Tagging and Processing**:

   - Tags events as **Up**, **Down**, or **Neutral** based on predefined rules.
   - Allows enrichment of event data from external sources before storage.

3. **Event Correlation**:

   - Groups related events to reduce noise.
   - Links "Down" and "Up" events to resolve incidents automatically.

4. **Automated Ticket Management**:

   - Creates, updates, and resolves tickets using **GLPI**.
   - Ready for integration with other tools like **ServiceNow** or **Jira**.

5. **Extensible Design**:
   - Replaceable storage, ticketing, database, and broker components to suit organizational requirements.

---

## 🚀 Getting Started

Encore is designed to address the needs of **large enterprises** while maintaining the flexibility to support **small-scale projects**.

### Local Setup

To try out Encore locally, use the Dockerized setup included in the repository.

**Steps to Set Up Locally**:

1. Clone the repository:

   ```bash
   git clone https://github.com/Vaayujeet/encore.git
   cd encore
   ```

2. Build and start the Dockerized setup:

   ```bash
   docker compose -f "docker/docker-compose.yml" up -d --build
   ```

3. Access services:
   - **Encore App**: `http://localhost:8000/admin/` (correlator/correlator)
   - **Kibana**: `http://localhost:5601` (elastic/correlator)
   - **GLPI**: `http://localhost:30080` (glpi/glpi) _-- One-time setup required. Check [Local Setup Guide](./docs/setting-up-encore-locally.md)._

For detailed setup instructions, including configuring Elasticsearch and GLPI, refer to the [Local Setup Guide](./docs/setting-up-encore-locally.md).

---

## 🔄 Workflow Overview

1. **Event Ingestion**:  
   Send events to Encore’s API in JSON format.

2. **Pipeline Processing**:  
   Extract and enrich key fields such as `asset_unique_id`, `event_title`, and `event_type` using pipeline rules.

3. **Event Correlation**:

   - Filter unwanted events.
   - Aggregate related events.
   - Deduplicate duplicates.
   - Apply user-defined correlation rules.

   Example: Multiple "High CPU Usage" alerts for a server are grouped into a single event, reducing noise.

4. **Ticket Creation**:  
   Automatically create, update, and resolve tickets based on correlated events.

5. **Data Analysis**:  
   Use stored events in **Elasticsearch** for visualization and long-term trend analysis.

---

## 🛠️ Technology Stack

- **Backend Framework**: Django
- **Task Queue**: Celery with Redis
- **Event Storage**: Elasticsearch (via ELK stack)
- **Database**: PostgreSQL
- **Ticket Management**: GLPI (default, pluggable with alternatives)
- **Containerization**: Docker and Docker Compose

Encore’s modular architecture ensures flexibility:

- Default tools like PostgreSQL, Redis, and Elasticsearch can be replaced with alternatives.
- Ticketing systems such as **ServiceNow** or **Jira** can be integrated.

---

## 🏗️ Roadmap

Planned improvements and features:

- Support for additional ticketing tools like **ServiceNow** and **Jira**.
- Enhanced machine learning for advanced event correlation.
- Detailed dashboards and reporting tools.
- High-availability deployment configurations.

---

## 🏆 Contributing

We welcome contributions! Here’s how you can help:

- Develop new modules for storage or ticketing integration.
- Optimize event processing pipelines.
- Expand documentation and examples.
- **Enhance Encore's features with your unique ideas.**

---

## 📜 License

Encore is licensed under the [AGPL-3.0 license](https://github.com/Vaayujeet/encore/blob/main/LICENSE).

---

## 📬 Contact Us

We’d love to hear from you! Whether you have questions, feedback, or need assistance, feel free to reach out:

- **Email**: [encore.support@vaayujeet.com](mailto:encore.support@vaayujeet.com)
- **Website**: [www.vaayujeet.com](http://www.vaayujeet.com) (coming soon)
- **GitHub Issues**: Found a bug or have a feature request? Submit an issue on our [GitHub repository](https://github.com/Vaayujeet/encore/issues).

We’re here to help and always looking for ways to improve Encore!
