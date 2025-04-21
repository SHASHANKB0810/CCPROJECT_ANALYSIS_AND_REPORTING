Cloud Computing Project – Phase – 2

Name : Siddharth S       SRN : PES1UG22AM160
Name : Shashank B       SRN : PES1UG22AM150
Name : Skandesh K       SRN : PES1UG22AM162

Github Link : https://github.com/SHASHANKB0810/CCPROJECT_ANALYSIS_AND_REPORTING

Tools Used : 
Python – Core programming language.
Supabase – Cloud database (PostgreSQL) for data storage and sharing.
PostgreSQL – Backend database.
Pandas – Data processing and analysis.
Matplotlib – Data visualization (graphs and charts).
Seaborn – Advanced and beautiful data visualizations.
ReportLab (Platypus) – Generating PDF reports.
Streamlit – Front-end web app framework.

We used the web app using Python and hosted it with Streamlit. For storing and sharing the data, we used Supabase, which provides a common online database built on PostgreSQL. The app allows users to give entries to the database. We designed the input forms to take more details based on our database structure. After users submit feedback, we pull the data from Supabase and use tools like Pandas, Matplotlib, and Seaborn to analyze and create graphs. We also used ReportLab to make PDF reports. 

•Built a web app using Python and hosted it with Streamlit.
•Used Supabase to store and share a common database (based on PostgreSQL).
•Made changes to the feedback form to collect more details according to our database design.
•Retrieved the data from Supabase for analytics.
•Used Pandas to process the data.
•Created graphs using Matplotlib and Seaborn.
•Generated PDF reports using ReportLab.
•The whole system makes it easy to collect, analyze and present report and feedback.
The system simplifies the entire workflow: collecting user feedback → storing it → analyzing the data → presenting the results visually and in downloadable reports.
Features
Web interface for submitting feedback entries.
Dynamic forms designed to collect detailed feedback based on database structure.
Retrieve and process user feedback from Supabase.
Visualize feedback trends using Matplotlib and Seaborn.
Generate downloadable PDF reports summarizing the feedback.
User-friendly and interactive web experience.


Microservice 1: User Analytics and Behavior Reporting

This microservice focuses on tracking how users interact with our platform. It collects data like session times, traffic sources (where users came from — ads, Google, etc.), what users clicked, what they searched for, and how long they stayed. Using this data, it creates detailed reports that show patterns like: which parts of the app are most popular, when users are most active, and where we are getting the most traffic from. This helps us understand user behavior, improve the user experience, and focus marketing efforts better.

In Points:

Tracks user sessions, clicks, searches, and traffic sources.

Collects data on user activity: when they login, logout, and what they browse.

Analyzes user engagement: most visited pages, average session times, peak usage hours.

Helps in marketing by showing which traffic sources are bringing the most users.

Reports help the business improve the app and marketing strategies based on real user behavior.

Microservice 2: User Behavior Analysis

This microservice looks deeper into how users behave while they use the app — not just where they click, but how they move, how often they return, and what patterns they follow. It studies things like: are users coming back every day? Are they getting stuck somewhere and leaving? Are there users who become loyal? It also calculates important metrics like retention rate (how many users keep coming back), churn rate (how many users stop using the app), and conversion rate (how many users actually complete an action, like booking a flight or hotel).
This analysis helps make smarter decisions — like where to fix problems in the app, and how to keep users happy and coming back.

In Points:

Tracks user journey inside the app (page flow, actions taken, time spent).

Analyzes user retention: how often users return after their first visit.

Finds drop-off points: where users quit without completing actions.

Calculates key metrics like Retention Rate, Churn Rate, and Conversion Rate.

Helps optimize the app to improve user satisfaction and increase bookings.

Provides detailed behavior reports for product and business teams.

Microservice 3: Feedback Analytics and Reporting

This microservice focuses on collecting and analyzing feedback from users about flights, hotels, trains, and buses. It gathers information like ratings, comments, and categories of complaints or praise. Then, it analyzes the feedback to find trends — for example, common complaints about hotel cleanliness or high ratings for flight services. It visualizes the results in graphs and also generates reports (like PDFs) to easily share insights. This helps the company identify areas that need improvement and maintain quality service.

In Points:

Collects detailed user feedback: ratings, comments, categories (flight, hotel, train, bus).

Organizes the feedback based on service type and satisfaction levels.

Performs sentiment analysis and trend analysis on user comments.

Generates visual reports (charts, graphs) using tools like Matplotlib and Seaborn.

Creates PDF reports for easy sharing with management teams.

Helps improve service quality by highlighting problem areas and strengths.
