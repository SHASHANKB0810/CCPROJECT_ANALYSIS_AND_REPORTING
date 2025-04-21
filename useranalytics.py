import psycopg2 # Replaced mysql.connector
from psycopg2.extras import DictCursor # To get dictionary-like rows
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
import os
import warnings

# Suppress UserWarnings from pandas and seaborn
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# --- Supabase Database Connection Details ---
# Use the provided DATABASE_URL
DATABASE_URL = "postgresql://postgres:Bellad%400810@db.mvvkcjdydxqxwnzfmqhd.supabase.co:5432/postgres"

# 1. Connect to Supabase (PostgreSQL) Database
conn = None # Initialize conn to None
cursor = None # Initialize cursor to None
try:
    # Establish the connection using the DATABASE_URL
    conn = psycopg2.connect(DATABASE_URL)
    # Create a cursor that returns dictionary-like rows
    cursor = conn.cursor(cursor_factory=DictCursor)
    print("Successfully connected to Supabase database.")
except Exception as e:
    print(f"Error connecting to Supabase database: {e}")
    # If connection fails, exit the script
    exit()

# 2. Prepare styles for the PDF
styles = getSampleStyleSheet()
report_elements = []
pdf_path = "User_Analytics_Report_Supabase.pdf" # Changed filename slightly

def add_title(title):
    report_elements.append(Paragraph(f"<b><font size=16>{title}</font></b>", styles['Title']))
    report_elements.append(Spacer(1, 12))

def add_section_title(text):
    report_elements.append(Spacer(1, 12))
    report_elements.append(Paragraph(f"<b><font size=14>{text}</font></b>", styles['Heading2']))
    report_elements.append(Spacer(1, 8))

def add_paragraph(text):
    report_elements.append(Paragraph(text, styles['BodyText']))
    report_elements.append(Spacer(1, 10))

def add_chart(img_path):
    # Check if the image file exists before adding
    if os.path.exists(img_path):
        report_elements.append(Image(img_path, width=6*inch, height=3.5*inch))
        report_elements.append(Spacer(1, 20))
    else:
        print(f"Warning: Chart image not found at {img_path}")
        add_paragraph(f"<i>[Chart image '{os.path.basename(img_path)}' could not be generated or found.]</i>")

# 3. Load data into DataFrames
# IMPORTANT: Ensure these table names ('users_s', 'sessions_s', etc.)
# exactly match the table names in your Supabase database.
# PostgreSQL is typically case-sensitive for identifiers unless quoted.
# If your tables are e.g., 'Users', use that name in the query.
try:
    users = pd.read_sql("SELECT * FROM users_s", conn)
    sessions = pd.read_sql("SELECT * FROM sessions_s", conn)
    events = pd.read_sql("SELECT * FROM user_events_s", conn)
    feedback = pd.read_sql("SELECT * FROM user_feedback_s", conn)
    payments = pd.read_sql("SELECT * FROM payments_s", conn)
    traffic = pd.read_sql("SELECT source FROM traffic_sources_s", conn)
    print("Successfully loaded data from Supabase tables.")
except Exception as e:
    print(f"Error loading data from Supabase: {e}")
    # Close connection if data loading fails
    if cursor:
        cursor.close()
    if conn:
        conn.close()
    exit() # Exit if data cannot be loaded

# Check if DataFrames are empty, handle potential errors downstream
if users.empty:
    print("Warning: 'users_s' table is empty or query returned no results.")
if sessions.empty:
    print("Warning: 'sessions_s' table is empty or query returned no results.")
if feedback.empty:
    print("Warning: 'user_feedback_s' table is empty or query returned no results.")
if payments.empty:
    print("Warning: 'payments_s' table is empty or query returned no results.")
if traffic.empty:
    print("Warning: 'traffic_sources_s' table is empty or query returned no results.")

# ---- Summary Stats for Front Page ----
total_users = 0
max_dau = 0
avg_rating = 0.0
total_revenue = 0.0
top_source = "N/A"
top_source_count = 0

# Calculate stats only if data is available
if not users.empty:
    users['created_at'] = pd.to_datetime(users['created_at'])
    users_daily = users.groupby(users['created_at'].dt.date).size().cumsum()
    if not users_daily.empty:
      total_users = users_daily.iloc[-1]
print(f"Total Users: {total_users}")

if not sessions.empty:
    sessions['session_start'] = pd.to_datetime(sessions['session_start'])
    sessions['day'] = sessions['session_start'].dt.date
    dau = sessions.groupby('day')['user_id'].nunique()
    if not dau.empty:
      max_dau = dau.max()
print(f"Max Daily Active Users: {max_dau}")

if not feedback.empty and 'rating' in feedback.columns:
    # Ensure rating column is numeric, coercing errors to NaN, then drop NaNs for mean calc
    feedback['rating'] = pd.to_numeric(feedback['rating'], errors='coerce')
    feedback.dropna(subset=['rating'], inplace=True)
    if not feedback.empty:
      avg_rating = feedback['rating'].mean()
      avg_rating = round(avg_rating, 2) if pd.notna(avg_rating) else 0.0
print(f"Average User Rating: {avg_rating}/5")

if not payments.empty and 'amount' in payments.columns:
    # Ensure amount column is numeric, coercing errors to NaN, then drop NaNs for sum calc
    payments['amount'] = pd.to_numeric(payments['amount'], errors='coerce')
    payments.dropna(subset=['amount'], inplace=True)
    if not payments.empty:
      total_revenue = payments['amount'].sum()
      total_revenue = round(total_revenue, 2) if pd.notna(total_revenue) else 0.0
print(f"Total Revenue: ${total_revenue}")

if not traffic.empty and 'source' in traffic.columns:
    source_counts = traffic['source'].value_counts()
    if not source_counts.empty:
        top_source = source_counts.idxmax()
        top_source_count = source_counts[top_source]
print(f"Top Traffic Source: {top_source} ({top_source_count} users)")


# ---- Start Report Content ----
add_title("User Analytics and Reporting (Supabase)") # Updated title
add_section_title("Summary Highlights")
add_paragraph(f"""
<b>Total Users:</b> {total_users}<br/>
<b>Max Daily Active Users:</b> {max_dau}<br/>
<b>Average User Rating:</b> {avg_rating} / 5<br/>
<b>Total Revenue Collected:</b> ${total_revenue:,.2f}<br/>
<b>Top Traffic Source:</b> {top_source} ({top_source_count} users)
""")

# --- Generate Charts and Add to Report (Only if data exists) ---

# 1. USER GROWTH
if not users.empty and not users_daily.empty:
    add_section_title("User Growth Metrics")
    add_paragraph("This section shows how your user base is growing over time, broken down by day.")

    plt.figure(figsize=(10, 5))
    sns.lineplot(x=users_daily.index, y=users_daily.values, marker='o', color='mediumblue')
    plt.title("Cumulative User Growth Over Time")
    plt.xlabel("Date")
    plt.ylabel("Total Users")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.grid()
    growth_chart = "growth_chart.png"
    plt.savefig(growth_chart)
    plt.close()
    add_chart(growth_chart)
else:
    add_section_title("User Growth Metrics")
    add_paragraph("No user growth data available to generate chart.")


# 2. USER ACTIVITY
if not sessions.empty and 'dau' in locals() and not dau.empty:
    add_section_title("User Activity Metrics")
    add_paragraph("Daily Active Users (DAU) is calculated based on user sessions started each day.")

    plt.figure(figsize=(10, 5))
    sns.barplot(x=list(dau.index), y=list(dau.values), palette="coolwarm")
    plt.title("Daily Active Users")
    plt.xlabel("Date")
    plt.ylabel("Unique Users")
    plt.xticks(rotation=45)
    plt.tight_layout()
    activity_chart = "activity_chart.png"
    plt.savefig(activity_chart)
    plt.close()
    add_chart(activity_chart)
else:
    add_section_title("User Activity Metrics")
    add_paragraph("No user activity data available to generate chart.")


# 3. USER FEEDBACK
add_section_title("User Feedback Summary")
add_paragraph("Here's a summary of the average rating and selected comments from users.")
add_paragraph(f"Average User Rating: {avg_rating}/5")

if not feedback.empty:
    sample_feedback = feedback[['feedback_text', 'rating']].head(5)
    if not sample_feedback.empty:
      add_paragraph("<b>Sample Feedback:</b>")
      for _, row in sample_feedback.iterrows():
          # Handle potential None/NaN in feedback text
          feedback_text = row['feedback_text'] if pd.notna(row['feedback_text']) else "No comment provided"
          add_paragraph(f"<b>Rating:</b> {row['rating']} – <i>{feedback_text}</i>")
    else:
        add_paragraph("No feedback comments found.")
else:
    add_paragraph("No user feedback data available.")


# 4. REVENUE ANALYTICS
add_section_title("Revenue Insights")
add_paragraph("Displays revenue per user and total income from all purchases.")
add_paragraph(f"Total Revenue Collected: ${total_revenue:,.2f}") # Added comma formatting

if not payments.empty:
    revenue_per_user = payments.groupby('user_id')['amount'].sum()
    if not revenue_per_user.empty:
      plt.figure(figsize=(10, 5))
      sns.histplot(revenue_per_user, bins=10, kde=True, color='green')
      plt.title("Distribution of Revenue per User")
      plt.xlabel("Revenue Amount ($)")
      plt.ylabel("User Count")
      plt.grid()
      plt.tight_layout()
      revenue_chart = "revenue_chart.png"
      plt.savefig(revenue_chart)
      plt.close()
      add_chart(revenue_chart)
    else:
        add_paragraph("No per-user revenue data to generate chart.")
else:
    add_paragraph("No revenue data available.")


# 5. TRAFFIC SOURCES
if not traffic.empty and not source_counts.empty:
    add_section_title("Traffic Sources")
    add_paragraph("Users arrive from various channels. Here's a breakdown by source.")

    plt.figure(figsize=(8, 6))
    source_counts.plot(kind='pie', autopct='%1.1f%%', startangle=140, colors=sns.color_palette('pastel'))
    plt.title("Traffic Source Distribution")
    plt.ylabel("") # Hide the default y-label from pandas plot
    plt.tight_layout()
    traffic_chart = "traffic_chart.png"
    plt.savefig(traffic_chart)
    plt.close()
    add_chart(traffic_chart)
else:
    add_section_title("Traffic Sources")
    add_paragraph("No traffic source data available to generate chart.")


# --- Finalize and Save PDF ---
try:
    doc = SimpleDocTemplate(pdf_path, pagesize=A4)
    doc.build(report_elements)
    print(f"Report saved successfully as {pdf_path}")
except Exception as e:
    print(f"Error building or saving the PDF report: {e}")
finally:
    # --- Clean up ---
    # Close the cursor and connection
    if cursor:
        cursor.close()
        print("Database cursor closed.")
    if conn:
        conn.close()
        print("Database connection closed.")

    # Optional: Clean up generated chart images
    chart_files = ["growth_chart.png", "activity_chart.png", "revenue_chart.png", "traffic_chart.png"]
    for chart_file in chart_files:
        if os.path.exists(chart_file):
            try:
                os.remove(chart_file)
                # print(f"Removed chart file: {chart_file}") # Optional: uncomment for verbose output
            except Exception as e:
                print(f"Error removing chart file {chart_file}: {e}")