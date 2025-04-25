# CCPROJECT_ANALYSIS_AND_REPORTING

## Cloud Computing Project – Phase 2

### Team Members
- **Siddharth S** – PES1UG22AM160  
- **Shashank B** – PES1UG22AM150  
- **Skandesh K K** – PES1UG22AM162  

---

##  Project Overview

This project is focused on **user feedback analytics** as part of a cloud-based solution. We built a complete pipeline for collecting, storing, analyzing, and reporting user feedback data using modern tools and technologies in the cloud computing ecosystem.

We developed a full-stack web app using **Streamlit** as the front end and **Supabase (PostgreSQL)** as the cloud-hosted backend. Users can submit feedback through interactive forms. The system retrieves and analyzes this data using **Pandas**, **Matplotlib**, and **Seaborn**, then generates dynamic **PDF reports** using **ReportLab**.

---
##  Docker Containers and Deployment

To ensure scalability and easy deployment, the entire project is containerized using **Docker**, and coordinated using **Docker Compose**. Each microservice, along with the frontend and gateway, runs in its own isolated container.

### Containers:

1. user-analytics-service
   - Runs the `useranalytics.py` script.
   - Handles data collection for user sessions, page visits, and referral tracking.

2. user-behavior-service
   - Runs the `behavior_analysis.py` script.
   - Analyzes user retention, churn, and interaction behavior inside the app.

3. feedback-analysis-service
   - Runs the `feedback_analysis_supabase.py` script.
   - Pulls feedback from Supabase, analyzes ratings and comments, and generates graphs/PDFs.

4. streamlit-web-app
   - Runs `streamlit_app.py`.
   - Provides the front-end interface for user input and viewing reports.

5. main-gateway
   - Entry point of the system.
   - Defined in `main.py`, routes requests to the appropriate microservices.

Docker Compose:
The `docker-compose.yml` file located in the `main_gateway` directory brings up all services at once. It links containers via networks, defines ports, and sets dependencies for a smooth startup.

> This setup enables the system to be deployed with a single command (`docker-compose up`) and ensures all microservices communicate reliably.
##  Tools and Technologies Used

| Tool/Technology | Purpose |
|-----------------|---------|
| Python | Core programming language |
|Docker|images|containers|
| Supabase | Cloud-hosted PostgreSQL database |
| PostgreSQL | Backend database system |
| Pandas | Data processing and analysis |
| Matplotlib | Graph and chart generation |
| Seaborn | Advanced and beautiful visualizations |
| ReportLab | Dynamic PDF report generation |
| Streamlit | Web app development and front-end interface |

---

##  Features

### Streamlit Web App Interface
Interactive UI for feedback collection and report access.
![WhatsApp Image 2025-04-21 at 20 19 12_077b9567](https://github.com/user-attachments/assets/3516978e-c6f8-4e4c-aaa0-def79429cdc1)



### Dynamic Feedback Forms
Forms adapt based on the database schema to collect detailed responses.

### Cloud-Based Data Storage
Feedback entries are securely stored in Supabase (PostgreSQL).

![WhatsApp Image 2025-04-21 at 20 19 41_6850371f](https://github.com/user-attachments/assets/f9337a6f-978d-4a32-869e-6746b3c5dbfc)


### Data Retrieval and Analysis
Processed using Pandas and visualized with Matplotlib & Seaborn.
![WhatsApp Image 2025-04-21 at 21 08 38_ea74402f](https://github.com/user-attachments/assets/b14aa45b-28cc-4883-a2a0-3e73b22bc2fc)



### Automated PDF Report Generation
Generate and download clean, professional summaries using ReportLab.
![WhatsApp Image 2025-04-21 at 20 16 57_7a1d8ff6](https://github.com/user-attachments/assets/020339aa-a67f-4fdb-9041-bf7b33ce1ea6)



### End-to-End Feedback Workflow
Submit → Store → Analyze → Visualize → Report

---

## Workflow

1. User submits feedback via the Streamlit form.
2. Data is stored in the cloud using Supabase (PostgreSQL).
3. Feedback is retrieved and processed using Pandas.
4. Visualization of trends using Seaborn and Matplotlib.
5. PDF report generated for easy sharing and offline access.
