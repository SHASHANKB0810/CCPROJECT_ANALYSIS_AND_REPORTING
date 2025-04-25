import streamlit as st
import psycopg2
from psycopg2.extras import DictCursor
import pandas as pd
from datetime import datetime, timedelta
import os
import psycopg2.errors

# --- Configuration ---
DATABASE_URL = "postgresql://postgres:Bellad%400810@db.mvvkcjdydxqxwnzfmqhd.supabase.co:5432/postgres" # Replace with your actual Supabase URL if different

# --- Database Connection and Utility Functions ---
# (Keep the functions get_db_connection, fetch_users, execute_db_query,
#  insert_user, insert_session, insert_payment, insert_feedback,
#  insert_traffic_source, insert_q_feedback as they were in the previous version)
# --- Database Connection and Utility Functions ---
@st.cache_resource
def get_db_connection():
    """Establishes and caches a connection to the Supabase PostgreSQL database."""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        print("Successfully connected to Supabase database.")
        return conn
    except Exception as e:
        st.exception(e)
        st.error("Failed to connect to the database. Please check the DATABASE_URL and network connectivity.")
        return None

@st.cache_data(ttl=300) # Add a short TTL to allow refreshing user list
def fetch_users(_conn):
    """Fetches user IDs and emails/usernames from the users_s table."""
    if _conn is None:
        st.error("Database connection not available for fetching users.")
        return pd.DataFrame(), {}

    try:
        query = "SELECT id, email, username FROM users_s WHERE is_active = TRUE ORDER BY username;"
        df = pd.read_sql(query, _conn)
        if df.empty:
            return df, {}
        # Display format for the dropdown
        df['display_label'] = df.apply(
            lambda row: f"{row['username']} ({row['email'] if pd.notna(row['email']) else 'No Email'}) [ID: {row['id']}]", axis=1
        )
        user_options_map = pd.Series(df.id.values, index=df.display_label).to_dict()
        return df, user_options_map
    except Exception as e:
        st.error(f"Error fetching users: {e}")
        return pd.DataFrame(), {}

def execute_db_query(conn, query, params=None, fetch_results=False):
    """Executes a given SQL query with parameters and optional result fetching."""
    if conn is None:
        st.error("Database connection is not available.")
        return (False, None)

    cursor = None
    success = False
    results = None
    error_object = None

    try:
        cursor = conn.cursor(cursor_factory=DictCursor)
        cursor.execute(query, params)
        if fetch_results:
            results = cursor.fetchall()
        conn.commit()
        success = True
    except psycopg2.Error as e:
        conn.rollback()
        error_object = e
        print(f"DB Error Details: {e}")
        print(f"SQLSTATE: {e.pgcode}")
        print(f"Error Message: {e.pgerror}")
        print(f"Query attempted: {cursor.query if cursor else 'N/A'}")
        st.error(f"Database Error: {e.pgcode} - {e.pgerror}")

    except Exception as e:
        conn.rollback()
        error_object = e
        st.error(f"An unexpected error occurred: {e}")
    finally:
        if cursor:
            cursor.close()

    if success:
        return (True, results)
    else:
        return (False, error_object)

def insert_user(conn, email, username, signup_source, country, city, device_type, os_name, browser):
    query = """
        INSERT INTO users_s (email, username, created_at, signup_source, country, city, device_type, os, browser, is_active)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE)
        RETURNING id;
    """
    timestamp = datetime.now()
    params = (email, username, timestamp, signup_source, country, city, device_type, os_name, browser)
    success, result_or_error = execute_db_query(conn, query, params, fetch_results=True)

    if success:
        st.cache_data.clear()
        new_user_id = result_or_error[0]['id'] if result_or_error and len(result_or_error) > 0 else None
        print(f"Successfully inserted user into users_s: {username} ({email}) with ID: {new_user_id}")
        return True
    else:
        if hasattr(result_or_error, 'pgcode') and result_or_error.pgcode == '23505':
            st.error(f"Failed to insert user. The email '{email}' likely already exists in users_s.")
        return False

def insert_session(conn, user_id, session_start, session_end):
    query = """
        INSERT INTO sessions_s (user_id, session_start, session_end)
        VALUES (%s, %s, %s);
    """
    params = (user_id, session_start, session_end)
    success, _ = execute_db_query(conn, query, params)
    if success:
        print(f"Successfully inserted session into sessions_s for user_id: {user_id}")
    return success

def insert_payment(conn, user_id, amount, currency, plan_type):
    query = """
        INSERT INTO payments_s (user_id, amount, currency, payment_date, plan_type)
        VALUES (%s, %s, %s, %s, %s);
    """
    timestamp = datetime.now()
    params = (user_id, amount, currency, timestamp, plan_type)
    success, _ = execute_db_query(conn, query, params)
    if success:
        print(f"Successfully inserted payment into payments_s for user_id: {user_id}, amount: {amount}")
    return success

def insert_feedback(conn, user_id, product_id, rating, review_text):
    query = """
        INSERT INTO user_feedback_s (user_id, feedback_text, rating, submitted_at)
        VALUES (%s, %s, %s, %s);
    """
    full_feedback_text = f"Product ID [{product_id}]: {review_text if review_text else 'No comment.'}"
    timestamp = datetime.now()
    params = (user_id, full_feedback_text, rating, timestamp)
    success, _ = execute_db_query(conn, query, params)
    if success:
        print(f"Successfully inserted feedback into user_feedback_s for user_id: {user_id}, product_id: {product_id}")
    return success

def insert_traffic_source(conn, user_id, source, campaign, medium):
    query = """
        INSERT INTO traffic_sources_s (user_id, source, campaign, medium, tracked_at)
        VALUES (%s, %s, %s, %s, %s);
    """
    timestamp = datetime.now()
    params = (user_id, source, campaign, medium, timestamp)
    success, _ = execute_db_query(conn, query, params)
    if success:
        print(f"Successfully inserted traffic source into traffic_sources_s for user_id: {user_id}, source: {source}")
    return success

def insert_q_feedback(conn, user_id, service_type, location, rating, feedback_text):
    query = f"""
        INSERT INTO user_feedback_q (user_id, service_type, location, rating, feedback_text, submitted_at)
        VALUES (%s, %s, %s, %s, %s, %s);
    """
    timestamp = datetime.now()
    params = (user_id, service_type, location, rating, feedback_text, timestamp)
    success, result_or_error = execute_db_query(conn, query, params)

    if success:
        print(f"Successfully inserted feedback into user_feedback_q for user_id: {user_id}, service: {service_type}")
    else:
        if hasattr(result_or_error, 'pgcode') and result_or_error.pgcode == '23503':
             st.error(f"Failed to insert feedback into user_feedback_q. User ID {user_id} might not exist in the 'users_q' table (FK constraint: fk_feedback_user_q). Ensure user IDs are consistent or use users from 'users_q'.")
        pass
    return success


# --- Streamlit App Layout ---
st.set_page_config(page_title="Data Entry Portal", layout="wide")

# --- Apply Updated Custom CSS --- <<< CSS UPDATED HERE
st.markdown("""
<style>
    /* General App Background */
    .stApp { background-color: #ffffff; padding: 0; margin: 0; }

    /* Headers */
    h1, h2, h3 {
        color: #222831;
        font-family: 'Arial', sans-serif;
        font-weight: bold;
    }
    h1 {
        font-size: 36px;
        text-align: center;
        padding: 20px 0;
        background-color: #00ADB5;
        color: white;
        margin-bottom: 30px;
        border-radius: 8px;
    }
    h2 {
        font-size: 28px;
        margin-top: 30px;
        border-bottom: 2px solid #EEEEEE;
        padding-bottom: 8px;
        color: #222831;
    }
    h3 { /* This corresponds to st.subheader */
        font-size: 24px;
        margin-top: 20px;
        color: #222831;
    }

    /* Buttons */
    .stButton>button {
        background-color: #00ADB5;
        color: white;
        font-size: 16px;
        border: none;
        padding: 10px 20px;
        border-radius: 8px;
        transition: background-color 0.3s ease;
        cursor: pointer;
    }
    .stButton>button:hover {
        background-color: #007B83;
        color: #eeeeee;
    }

    /* Form Inputs - General Styling for the Box */
    .stTextInput>div>div>input,
    .stNumberInput>div>div>input,
    .stSelectbox>div>div,      /* Main container for stSelectbox */
    .stTextArea>div>textarea,
    .stDateInput>div>input,
    .stTimeInput>div>input {
        border: 1px solid #CCCCCC !important;
        border-radius: 6px !important;
        padding: 8px !important;             /* Padding around the entire widget */
        background-color: #ffffff !important;
    }

    /* Specific styling for CONTENT VISIBILITY inside widgets */

    /* Text Input, Number Input, Text Area, Date, Time Content */
    .stTextInput>div>div>input,
    .stNumberInput>div>div>input,
    .stTextArea>div>textarea,
    .stDateInput>div>input,
    .stTimeInput>div>input {
         color: #222831 !important; /* Ensure text inside is dark */
         -webkit-text-fill-color: #222831 !important; /* Force color for some browsers */
    }

    /* Selectbox - Targeting the element displaying the selected value */
    /* This might need adjustment based on Streamlit version / internal structure */
    .stSelectbox div[data-baseweb="select"] > div:first-child > div {
         color: #222831 !important;             /* <<<< FORCE DARK TEXT COLOR HERE */
         -webkit-text-fill-color: #222831 !important;
         background-color: transparent !important; /* Ensure no background color interferes */
         border: none !important;               /* Remove any potential inner border */
         padding: 0 !important;                 /* Adjust padding if needed, but usually handled by parent */
         margin: 0 !important;
         line-height: normal !important;        /* Ensure text isn't cut off vertically */
         overflow: hidden;                     /* Hide overflow */
         text-overflow: ellipsis;              /* Add ellipsis for long text */
         white-space: nowrap;                  /* Prevent wrapping */
    }

    /* Selectbox - Placeholder style */
     .stSelectbox input::placeholder {
         color: #757575 !important;
         opacity: 1 !important;
    }

     /* Selectbox - Dropdown arrow */
     .stSelectbox div[class*="indicatorContainer"] svg {
         fill: #555555 !important; /* Adjust arrow color if necessary */
    }


    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #EEEEEE;
        padding: 10px;
        border-radius: 8px 8px 0 0;
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 17px;
        font-weight: 500;
        padding: 10px 18px;
        margin-right: 0;
        background-color: #EEEEEE;
        color: #393E46;
        border-radius: 8px 8px 0 0;
        transition: background-color 0.3s ease, color 0.3s ease;
        border-bottom: 3px solid transparent;
    }
    .stTabs [data-baseweb="tab"]:hover {
         background-color: #dddddd;
         color: #222831;
    }
    .stTabs [aria-selected="true"] {
        background-color: #ffffff;
        color: #00ADB5;
        border-bottom: 3px solid #00ADB5;
        border-radius: 8px 8px 0 0;
    }

    /* Other adjustments */
    label {
        font-weight: bold;
        color: #393E46;
        margin-bottom: 5px;
        display: block;
    }
    .stForm {
        background-color: #FAFAFA;
        padding: 25px;
        border-radius: 10px;
        border: 1px solid #EEEEEE;
        box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.08);
        margin-bottom: 30px;
    }
    .stForm .stTextInput,
    .stForm .stNumberInput,
    .stForm .stSelectbox,
    .stForm .stTextArea,
    .stForm .stDateInput,
    .stForm .stTimeInput {
        width: 100%;
    }
    .stForm .row-widget.stButton {
        text-align: right;
        margin-top: 15px;
    }
</style>
""", unsafe_allow_html=True)

# --- Updated Header ---
st.markdown("""
<h1>User Data Entry Portal</h1>
""", unsafe_allow_html=True) # Removed emoji

# --- Database Connection ---
conn = get_db_connection()

# --- Fetch User Data ---
if conn:
    if st.button("🔄 Refresh User List"):
        st.cache_data.clear()
        st.rerun()

    users_df, user_options_map = fetch_users(conn)
    user_display_options = ["Select a User..."] + (list(user_options_map.keys()) if user_options_map else [])
    if users_df.empty:
        st.warning("No active users found. Some forms require an existing user.", icon="⚠️")
        can_select_user = False
    else:
        can_select_user = True
else:
    st.error("Cannot proceed without a database connection.")
    users_df = pd.DataFrame()
    user_options_map = {}
    user_display_options = ["Database connection failed"]
    can_select_user = False

# --- Data Entry Tabs ---
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "👤 New User",
    "⏱️ New Session",
    "💳 New Payment",
    "📝 Generic Feedback",
    "🌐 New Traffic Source",
    "★ Specific Feedback"
])

# --- Tab 1: New User ---
with tab1:
    st.subheader("Create New User")
    with st.form("new_user_form", clear_on_submit=True):
        st.write("Enter details for a new user. This data will be added to the `users_s` table.")
        email = st.text_input("Email*", placeholder="user@example.com")
        username = st.text_input("Username*", placeholder="username123")
        signup_source = st.text_input("Signup Source", placeholder="e.g., organic, ads, referral")
        country = st.text_input("Country", placeholder="e.g., USA, India")
        city = st.text_input("City", placeholder="e.g., New York, Mumbai")
        device_type = st.selectbox("Device Type", ["", "mobile", "desktop", "tablet"], format_func=lambda x: x if x else "Select...")
        os_name = st.text_input("Operating System", placeholder="e.g., iOS, Windows, Android")
        browser = st.text_input("Browser", placeholder="e.g., Chrome, Safari, Firefox")

        submitted = st.form_submit_button("Add User")
        if submitted:
            if not email or not username:
                st.error("Email and Username are required.")
            elif "@" not in email or "." not in email:
                st.error("Please enter a valid email address.")
            else:
                if insert_user(conn, email, username, signup_source, country, city, device_type, os_name, browser):
                    st.success(f"User '{username}' added successfully!")
                    st.rerun()

# --- Tab 2: New Session ---
with tab2:
    st.subheader("Log New Session")
    with st.form("new_session_form", clear_on_submit=True):
        st.write("Log a user session. This data will be added to the `sessions_s` table.")
        if not can_select_user:
            st.warning("Cannot log session: No users available to select.")
            st.form_submit_button("Add Session", disabled=True)
        else:
            selected_user_label_sess = st.selectbox(
                "Select User*", options=user_display_options, key="sess_user"
            )
            default_start = datetime.now() - timedelta(hours=1)
            default_end = datetime.now()

            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Session Start Date*", value=default_start.date())
                start_time = st.time_input("Session Start Time*", value=default_start.time())
            with col2:
                end_date = st.date_input("Session End Date*", value=default_end.date())
                end_time = st.time_input("Session End Time*", value=default_end.time())

            session_start = datetime.combine(start_date, start_time)
            session_end = datetime.combine(end_date, end_time)

            submitted = st.form_submit_button("Add Session")
            if submitted:
                user_id = user_options_map.get(selected_user_label_sess) if selected_user_label_sess != "Select a User..." else None
                if not user_id:
                    st.error("Please select a valid user.")
                elif session_end <= session_start:
                    st.error("Session End time must be after Session Start time.")
                else:
                    if insert_session(conn, user_id, session_start, session_end):
                        st.success(f"Session logged successfully for {selected_user_label_sess}.")

# --- Tab 3: New Payment ---
with tab3:
    st.subheader("Record New Payment")
    with st.form("new_payment_form", clear_on_submit=True):
        st.write("Record a payment. This data will be added to the `payments_s` table.")
        if not can_select_user:
            st.warning("Cannot record payment: No users available to select.")
            st.form_submit_button("Add Payment", disabled=True)
        else:
            selected_user_label_pay = st.selectbox(
                "Select User*", options=user_display_options, key="pay_user"
            )
            amount = st.number_input("Amount*", min_value=0.01, value=10.00, format="%.2f")
            currency = st.text_input("Currency*", placeholder="e.g., USD, EUR, INR", max_chars=10)
            plan_type = st.text_input("Plan Type", placeholder="e.g., pro, starter, enterprise")

            submitted = st.form_submit_button("Add Payment")
            if submitted:
                user_id = user_options_map.get(selected_user_label_pay) if selected_user_label_pay != "Select a User..." else None
                if not user_id:
                    st.error("Please select a valid user.")
                elif amount <= 0:
                    st.error("Amount must be greater than zero.")
                elif not currency:
                    st.error("Currency code is required.")
                else:
                    if insert_payment(conn, user_id, amount, currency.upper(), plan_type):
                        st.success(f"Payment of {currency.upper()} {amount:.2f} recorded for {selected_user_label_pay}.")

# --- Tab 4: Generic Feedback ---
with tab4:
    st.subheader("Submit Generic Feedback")
    with st.form("new_feedback_form", clear_on_submit=True):
        st.write("Submit general user feedback. This data will be added to the `user_feedback_s` table.")
        if not can_select_user:
            st.warning("Cannot submit feedback: No users available to select.")
            st.form_submit_button("Submit Feedback", disabled=True)
        else:
            selected_user_label_feed = st.selectbox(
                "Select User Submitting Feedback*", options=user_display_options, key="feed_user"
            )
            product_id = st.text_input("Context/Product ID*", placeholder="e.g., FLIGHT123, HOTEL456, Website UI")
            rating = st.selectbox(
                "Rating*",
                options=["", "5", "4", "3", "2", "1"],
                format_func=lambda x: f"{x} Stars" if x else "Select a rating"
            )
            review_text = st.text_area("Review", placeholder="Write your review (optional)", height=100)

            submitted = st.form_submit_button("Submit Feedback")
            if submitted:
                user_id = user_options_map.get(selected_user_label_feed) if selected_user_label_feed != "Select a User..." else None
                if not user_id:
                    st.error("Please select a valid user.")
                elif not product_id:
                    st.error("Context/Product ID is required.")
                elif not rating:
                    st.error("Rating is required.")
                else:
                    if insert_feedback(conn, user_id, product_id, int(rating), review_text):
                        st.success(f"Generic feedback submitted successfully for {selected_user_label_feed} regarding '{product_id}'.")

# --- Tab 5: New Traffic Source ---
with tab5:
    st.subheader("Log Traffic Source")
    with st.form("new_traffic_form", clear_on_submit=True):
        st.write("Log a traffic source entry. This data will be added to the `traffic_sources_s` table.")
        if not can_select_user:
            st.warning("Cannot log traffic source: No users available to select.")
            st.form_submit_button("Add Traffic Source", disabled=True)
        else:
            selected_user_label_traf = st.selectbox(
                "Select User*", options=user_display_options, key="traf_user"
            )
            source = st.text_input("Source*", placeholder="e.g., Google, Facebook, Direct")
            campaign = st.text_input("Campaign", placeholder="e.g., spring_sale (Optional)")
            medium = st.text_input("Medium", placeholder="e.g., organic, cpc, email (Optional)")

            submitted = st.form_submit_button("Add Traffic Source")
            if submitted:
                user_id = user_options_map.get(selected_user_label_traf) if selected_user_label_traf != "Select a User..." else None
                if not user_id:
                    st.error("Please select a valid user.")
                elif not source:
                    st.error("Source is required.")
                else:
                    if insert_traffic_source(conn, user_id, source, campaign, medium):
                        st.success(f"Traffic source '{source}' logged for {selected_user_label_traf}.")

# --- Tab 6: New Specific Feedback ---
with tab6:
    st.subheader("Submit Specific Feedback")
    with st.form("specific_feedback_form", clear_on_submit=True):
        st.write("Submit feedback for specific services like Flights, Hotels, etc. This data will be added to the `user_feedback_q` table.")
        st.warning("Ensure the selected User ID exists in the `users_q` table for this feedback to be validly linked. (The dropdown shows users from `users_s`).", icon="⚠️")

        if not can_select_user:
            st.warning("Cannot submit feedback: No users available to select.")
            st.form_submit_button("Submit Feedback", disabled=True)
        else:
            selected_user_label_spec = st.selectbox(
                "Select User*", options=user_display_options, key="spec_user"
            )
            feedback_type = st.selectbox(
                "Service Type*", options=["", "flights", "hotels", "trains", "bus", "package", "car_rental", "forex", "travel_insurance", "visa", "other"],
                format_func=lambda x: x.replace("_", " ").title() if x else "Select service type"
            )
            location = st.text_input("Location*", placeholder="e.g., New York, Paris, Delhi")
            rating = st.selectbox(
                "Rating*",
                options=["", "5", "4", "3", "2", "1"],
                format_func=lambda x: f"{x} Stars" if x else "Select rating"
            )
            feedback_text = st.text_area("Feedback Text*", placeholder="Write your feedback", height=100)

            submitted = st.form_submit_button("Submit Specific Feedback")
            if submitted:
                user_id = user_options_map.get(selected_user_label_spec) if selected_user_label_spec != "Select a User..." else None
                if not user_id:
                    st.error("Please select a valid user.")
                elif not feedback_type:
                    st.error("Please select a service type.")
                elif not location:
                    st.error("Location is required.")
                elif not rating:
                    st.error("Rating is required.")
                elif not feedback_text:
                    st.error("Feedback text is required.")
                else:
                    if insert_q_feedback(conn, user_id, feedback_type, location, int(rating), feedback_text):
                        st.success(f"Specific feedback (Type: {feedback_type}) submitted successfully for {selected_user_label_spec}.")

# --- Footer ---
st.markdown("---")
st.caption("Streamlit Data Entry App for Supabase Report")