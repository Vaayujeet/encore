# Encore: Event Correlator

Encore is a modular and scalable event correlation platform designed to streamline the processing and management of large volumes of system events. Built with **Django** and **Celery**, Encore enables real-time event ingestion, filtering, and correlation, helping teams reduce noise and focus on actionable incidents. Its flexible architecture supports integration with tools like **ELK** for event storage, **GLPI** for ticket management, and **PostgreSQL** and **Redis** for database and messaging.

Although Encore is still under active development, we have delivered a **Minimum Viable Product (MVP)** that is robust enough for use in production environments. The MVP includes core features such as event tagging, correlation, and incident automation, providing immediate value to operations teams. With its modular design, Encore can be customized and extended to meet diverse organizational needs, making it a versatile solution for managing system health and reducing operational overhead.

## Table of Contents

- [Encore: Event Correlator](#encore-event-correlator)
  - [Table of Contents](#table-of-contents)
  - [✨ Key Features](#-key-features)
    - [Core Features in the MVP](#core-features-in-the-mvp)
  - [🚀 Getting Started](#-getting-started)
  - [🔄 Workflow Overview](#-workflow-overview)
  - [🛠️ Technology Stack](#️-technology-stack)
  - [🏗️ Roadmap](#️-roadmap)
  - [🏆 Contributing](#-contributing)
  - [📜 License](#-license)
  - [📬 Contact Us](#-contact-us)

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

## 🚀 Getting Started

Encore is designed to address the needs of **large enterprises and organizations** managing complex infrastructures, while maintaining the flexibility to support **small-scale projects** as well.

**Interested in trying Encore?** Learn how easy it is to [set up Encore locally](./docs/setting-up-encore-locally.md) and explore its capabilities.

## 🔄 Workflow Overview

1. **Event Ingestion**:  
   Send events to Encore’s API in JSON format.

2. **Pipeline Processing**:  
   Extract and enrich key fields such as `asset_unique_id`, `event_title` and `event_type` using Pipeline Rules.

3. **Event Correlation**:  
   Filter unwanted events, Aggregate related events, Dedup duplicates, and apply user-defined correlation rules.

4. **Ticket Creation**:  
   Automatically create, update, and resolve tickets based on correlated events.

5. **Data Analysis**:  
   Use stored events in **Elasticsearch** for visualization and long-term trend analysis.

## 🛠️ Technology Stack

- **Backend Framework**: Django
- **Task Queue**: Celery with Redis
- **Event Storage**: Elasticsearch (via ELK stack)
- **Database**: PostgreSQL
- **Ticket Management**: GLPI (default, pluggable with alternatives)
- **Containerization**: Docker and Docker Compose

Like GPLI, Elasticsearch, PostgreSQL, and Redis could also be made pluggable with alternatives. However, we are not currently working on these alternatives unless there is a strong requirement.

## 🏗️ Roadmap

Planned improvements and features:

- Support for additional ticketing tools like **ServiceNow** and **Jira**.
- Enhanced machine learning for advanced event correlation.
- Detailed dashboards and reporting tools.
- High-availability deployment configurations.

## 🏆 Contributing

We welcome contributions! Here’s how you can help:

- Develop new modules for storage or ticketing integration.
- Optimize event processing pipelines.
- Expand documentation and examples.
- **Enhance Encore's features with your unique ideas.**

Fork the repository and submit a pull request to share your contributions.

## 📜 License

Encore is licensed under the [AGPL-3.0 license](https://github.com/Vaayujeet/encore?tab=readme-ov-file#AGPL-3.0-1-ov-file).

## 📬 Contact Us  

We’d love to hear from you! Whether you have questions, feedback, or need assistance, feel free to reach out:  

- **Email**: [encore.support@vaayujeet.com](mailto:encore.support@vaayujeet.com)  
- **Website**: [www.vaayujeet.com](http://www.vaayujeet.com) -- coming soon
- **GitHub Issues**: Found a bug or have a feature request? Submit an issue on our [GitHub repository](https://github.com/Vaayujeet/encore/issues).  

We’re here to help and always looking for ways to improve Encore!  
