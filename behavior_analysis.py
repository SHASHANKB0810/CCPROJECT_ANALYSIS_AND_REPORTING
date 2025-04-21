import psycopg2
from psycopg2.extras import DictCursor
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle # Import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER # Import alignment constants
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib import colors
import os
import warnings
import ast

# Suppress warnings
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# --- Supabase Database Connection Details ---
# Replace with your actual connection string if different
DATABASE_URL = "postgresql://postgres:Bellad%400810@db.mvvkcjdydxqxwnzfmqhd.supabase.co:5432/postgres"

# Database connection using psycopg2 with the full DSN string
conn = None # Initialize conn to None
try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor(cursor_factory=DictCursor)
    print("Successfully connected to Supabase database using connection string.")
except Exception as e:
    print(f"Error connecting to Supabase database: {e}")
    exit()

# Prepare styles for the PDF
styles = getSampleStyleSheet()
# Add a specific style for table body text if needed (can inherit)
styles.add(ParagraphStyle(name='TableBodyText', parent=styles['BodyText'], fontSize=9, alignment=TA_LEFT))
styles.add(ParagraphStyle(name='TableHeader', parent=styles['BodyText'], fontName='Helvetica-Bold', fontSize=10, alignment=TA_CENTER, textColor=colors.whitesmoke))

report_elements = []
pdf_filename = "User_Behavior_Analysis_Report_Supabase_v2.pdf" # Changed filename
pdf_path = os.path.join(os.getcwd(), pdf_filename)
chart_dir = "charts" # Define chart_dir globally

# --- Report Generation Helper Functions ---

def add_title(title):
    report_elements.append(Paragraph(f"<b><font size=16>{title}</font></b>", styles['Title']))
    report_elements.append(Spacer(1, 12))

def add_section_title(text):
    report_elements.append(Spacer(1, 12))
    report_elements.append(Paragraph(f"<b><font size=14>{text}</font></b>", styles['Heading2']))
    report_elements.append(Spacer(1, 8))

def add_paragraph(text):
    # Replace newlines with <br/> tags for HTML-like line breaks in Paragraphs
    report_elements.append(Paragraph(text.replace('\n', '<br/>'), styles['BodyText']))
    report_elements.append(Spacer(1, 10))

def add_chart(img_path, width=6*inch, height=3.5*inch):
    if os.path.exists(img_path):
        try:
            img = Image(img_path, width=width, height=height)
            img.hAlign = 'CENTER' # Center the image
            report_elements.append(img)
            report_elements.append(Spacer(1, 20))
        except Exception as e:
            print(f"Error adding image {img_path}: {e}")
            add_paragraph(f"[Error adding chart: {os.path.basename(img_path)} - {e}]")
    else:
        print(f"Chart image file not found: {img_path}")
        add_paragraph(f"[Chart image not found: {os.path.basename(img_path)}]")


# --- *** MODIFIED add_table FUNCTION *** ---
def add_table(data, col_widths=None):
    """
    Adds a table to the report elements, wrapping cell content in Paragraphs
    for better text handling and a cleaner look.
    """
    if not data or not isinstance(data, list) or len(data) < 1 or not data[0]:
        add_paragraph("[No data available for table header]")
        return

    num_cols = len(data[0])

    # --- Wrap content in Paragraphs ---
    formatted_data = []
    # Header row: Use 'TableHeader' style
    header_row = [Paragraph(str(cell), styles['TableHeader']) for cell in data[0]]
    formatted_data.append(header_row)

    # Data rows: Use 'TableBodyText' style
    for row_index, row in enumerate(data[1:]):
        if hasattr(row, '__len__') and len(row) == num_cols:
             # Use default TableBodyText style
             formatted_data.append([Paragraph(str(item) if item is not None else '', styles['TableBodyText']) for item in row])
        else:
             print(f"Warning: Skipping row {row_index + 1} with incorrect structure or column count: {row}")
    # --- End Wrapping ---

    if len(formatted_data) <= 1:
        add_paragraph("[No data rows available for table (after processing)]")
        return

    # Calculate column widths if not provided or incorrect length
    page_width, _ = A4
    available_width = page_width - 1 * inch # Adjust for margins (e.g., 0.5 inch each side)

    if not col_widths or len(col_widths) != num_cols:
        print(f"Warning: Invalid or missing col_widths ({col_widths}). Calculating equal widths.")
        col_widths = [available_width / num_cols] * num_cols
    elif sum(col_widths) > available_width:
         print(f"Warning: Total specified column width ({sum(col_widths)/inch:.2f} inches) exceeds available page width ({available_width/inch:.2f} inches). Scaling down.")
         scale_factor = available_width / sum(col_widths)
         col_widths = [w * scale_factor for w in col_widths]

    try:
        table = Table(formatted_data, colWidths=col_widths)
        table.setStyle(TableStyle([
            # Header Style
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkslategray), # Darker header background
            ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 6),

            # Body Style
            # Use alternating row colors (zebra striping) for readability
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
            ('VALIGN', (0, 1), (-1, -1), 'TOP'), # Align text to top of cell is often better for paragraphs
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 6), # Consistent padding
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),

            # Grid
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BOX', (0, 0), (-1, -1), 1.5, colors.black), # Thicker outer box
        ]))
        report_elements.append(table)
        report_elements.append(Spacer(1, 20))
    except Exception as e:
        print(f"Error creating table with formatted data.")
        print(f"Table generation error: {e}")
        add_paragraph(f"[Error generating table - {e}]")
# --- *** END OF MODIFIED add_table FUNCTION *** ---


# ==================================================================
# Function to load data (Using _b tables as in original)
# ==================================================================
def load_behavioral_data(db_conn):
    try:
        # --- MODIFIED TABLE NAMES ---
        users = pd.read_sql("SELECT * FROM public.users_b", db_conn)
        sessions = pd.read_sql("""
            SELECT *,
                   EXTRACT(EPOCH FROM (session_end - session_start)) / 60.0 as session_duration_min
            FROM public.sessions_b
            WHERE session_end >= session_start AND session_start IS NOT NULL AND session_end IS NOT NULL
        """, db_conn) # Added NOT NULL checks
        events = pd.read_sql("""
            SELECT * FROM public.user_events_b
            WHERE event_type IN (
                'search_flight', 'view_flight', 'click_book', 'book_flight', 'abandon_booking',
                'search_hotel', 'view_hotel', 'compare_hotel', 'book_hotel',
                'search_package', 'view_package', 'wishlist_add', 'book_package',
                'search_car', 'book_car', 'search_activity', 'book_activity',
                'apply_filter', 'sort_results', 'cancel_booking', 'login',
                'view_deal', 'share_deal', 'repeat_booking', 'search_train',
                'book_train', 'search_bus'
            ) AND event_time IS NOT NULL AND user_id IS NOT NULL -- Added NOT NULL checks
        """, db_conn)
        payments = pd.read_sql("SELECT * FROM public.payments_b", db_conn)
        # --- END MODIFIED TABLE NAMES ---

        print("Data loaded successfully from _b tables.")
        return users, sessions, events, payments
    except (Exception, psycopg2.DatabaseError) as e: # Catch specific DB errors too
        print(f"Error loading data from database (check _b table names & connection): {e}")
        # Return empty dataframes on error to prevent downstream issues
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
# ==================================================================


# ==================================================================
# Main execution block
# ==================================================================
try:
    # --- Ensure Chart Directory Exists ---
    if not os.path.exists(chart_dir):
        try:
            os.makedirs(chart_dir)
            print(f"Created directory: {chart_dir}")
        except OSError as e:
            print(f"Error creating directory {chart_dir}: {e}")
            exit() # Exit if we can't create the directory for charts

    # --- Load Data ---
    users, sessions, events, payments = load_behavioral_data(conn)

    # --- Basic Data Validation ---
    if users.empty and sessions.empty and events.empty and payments.empty:
        print("Critical error: Could not load any data. Exiting.")
        if conn: conn.close() # Close connection before exiting
        exit()
    elif users.empty or sessions.empty or events.empty:
        print("Warning: Could not load one or more essential behavioral data tables. Report may be incomplete.")
        # Decide if you want to proceed or exit based on which tables are missing
        # For now, we proceed but the report sections might show "No data" messages

    # --- Data Cleaning and Preparation ---
    # Convert datetime columns only if the DataFrame is not empty and column exists
    if not users.empty and 'created_at' in users.columns:
        users['created_at'] = pd.to_datetime(users['created_at'], errors='coerce')
    if not sessions.empty:
        if 'session_start' in sessions.columns:
             sessions['session_start'] = pd.to_datetime(sessions['session_start'], errors='coerce')
        if 'session_end' in sessions.columns:
             sessions['session_end'] = pd.to_datetime(sessions['session_end'], errors='coerce')
        # Recalculate duration after conversion and handle potential NaT values
        if 'session_start' in sessions.columns and 'session_end' in sessions.columns:
            sessions = sessions.dropna(subset=['session_start', 'session_end']) # Drop rows where conversion failed
            sessions['session_duration_min'] = (sessions['session_end'] - sessions['session_start']).dt.total_seconds() / 60.0
            sessions = sessions[sessions['session_duration_min'] >= 0] # Filter invalid durations

    if not events.empty and 'event_time' in events.columns:
        events['event_time'] = pd.to_datetime(events['event_time'], errors='coerce')
        events = events.dropna(subset=['event_time', 'user_id']) # Drop rows essential for linking/time analysis

    # ---- Start Report Content ----
    add_title("User Behavioral Analysis Report (Supabase Data)")
    add_paragraph(f"Report generated on: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}") # Add generation time
    add_section_title("Travel Booking Behavior Insights")

    # Define paths for chart files
    funnel_chart = os.path.join(chart_dir, "funnel_chart.png")
    duration_chart = os.path.join(chart_dir, "duration_chart.png")
    sessions_chart = os.path.join(chart_dir, "sessions_chart.png")
    destinations_chart = os.path.join(chart_dir, "destinations_chart.png")
    hotels_chart = os.path.join(chart_dir, "hotels_chart.png")
    booking_chart = os.path.join(chart_dir, "booking_chart.png")
    time_to_book_chart = os.path.join(chart_dir, "time_to_book_chart.png")
    device_chart = os.path.join(chart_dir, "device_chart.png")

    # ---------------------------------
    # 1. USER JOURNEY ANALYSIS
    # ---------------------------------
    add_section_title("1. Travel Booking Funnel Analysis")
    if not events.empty:
        funnel_events = [
            'search_flight', 'search_hotel', 'search_package', 'search_car', 'search_activity', 'search_train', 'search_bus', # Stage 1: Search
            'view_flight', 'view_hotel', 'view_package', 'compare_hotel', 'view_deal', 'apply_filter', 'sort_results', # Stage 2: View/Consider/Refine
            'click_book', 'wishlist_add', # Stage 3: Intent
            'book_flight', 'book_hotel', 'book_package', 'book_car', 'book_activity', 'book_train', 'repeat_booking' # Stage 4: Book
        ]
        # Ensure we only consider events from the defined list
        funnel_data = events[events['event_type'].isin(funnel_events)].copy()

        if not funnel_data.empty:
            # --- Event Counts ---
            funnel_counts = funnel_data['event_type'].value_counts().reset_index()
            funnel_counts.columns = ['event_type', 'count']
            funnel_counts['event_type'] = pd.Categorical(funnel_counts['event_type'], categories=funnel_events, ordered=True)
            funnel_counts = funnel_counts.sort_values('event_type').dropna(subset=['event_type']) # Drop if category invalid

            if not funnel_counts.empty:
                plt.figure(figsize=(12, 7)) # Wider figure for more event types
                sns.barplot(x='event_type', y='count', data=funnel_counts, palette="viridis")
                plt.title("Travel Booking Funnel - Event Counts")
                plt.xlabel("Event Type (Ordered by Funnel Stage)")
                plt.ylabel("Number of Events")
                plt.xticks(rotation=60, ha='right', fontsize=9) # Rotate more, adjust size
                plt.tight_layout()
                plt.savefig(funnel_chart)
                plt.close()
                add_chart(funnel_chart, width=7*inch, height=4*inch) # Adjust chart size in PDF if needed

                # --- Conversion Rates (Simplified Grouping) ---
                funnel_counts_dict = funnel_counts.set_index('event_type')['count'].to_dict()
                search_events_count = sum(funnel_counts_dict.get(e, 0) for e in funnel_events if e.startswith('search_'))
                view_refine_count = sum(funnel_counts_dict.get(e, 0) for e in funnel_events if e.startswith('view_') or e in ['compare_hotel', 'apply_filter', 'sort_results'])
                intent_events_count = sum(funnel_counts_dict.get(e, 0) for e in funnel_events if e.startswith('click_') or e == 'wishlist_add')
                book_events_count = sum(funnel_counts_dict.get(e, 0) for e in funnel_events if e.startswith('book_'))

                # Calculate rates safely (avoid division by zero)
                search_to_view_rate = (view_refine_count / search_events_count * 100) if search_events_count > 0 else 0
                view_to_intent_rate = (intent_events_count / view_refine_count * 100) if view_refine_count > 0 else 0
                intent_to_book_rate = (book_events_count / intent_events_count * 100) if intent_events_count > 0 else 0
                overall_conversion_rate = (book_events_count / search_events_count * 100) if search_events_count > 0 else 0

                add_paragraph(f"""
                <b>Simplified Conversion Rates (Grouped Stages):</b><br/>
                Search → View/Refine: {search_to_view_rate:.1f}% ({view_refine_count:,} / {search_events_count:,})<br/>
                View/Refine → Intent (Click/Wishlist): {view_to_intent_rate:.1f}% ({intent_events_count:,} / {view_refine_count:,})<br/>
                Intent → Book: {intent_to_book_rate:.1f}% ({book_events_count:,} / {intent_events_count:,})<br/>
                Overall Search → Book: {overall_conversion_rate:.1f}% ({book_events_count:,} / {search_events_count:,})
                """)
                add_paragraph("<i>Note: Conversion rates are simplified based on event counts and may not represent unique user progression perfectly.</i>")
            else:
                add_paragraph("No relevant funnel event data found after filtering.")
        else:
            add_paragraph("No funnel event data available within selected events.")
    else:
         add_paragraph("No event data loaded. Cannot perform funnel analysis.")

    # ---------------------------------
    # 2. SESSION BEHAVIOR ANALYSIS
    # ---------------------------------
    add_section_title("2. User Session Analysis")
    if not sessions.empty and 'session_duration_min' in sessions.columns:
        # Use only valid, calculated durations
        valid_durations = sessions['session_duration_min'].dropna()
        # Filter unreasonable durations (e.g., < 1 sec or > 12 hours)
        reasonable_durations = valid_durations[(valid_durations > (1/60)) & (valid_durations < 720)]

        if not reasonable_durations.empty:
            plt.figure(figsize=(10, 6))
            sns.histplot(reasonable_durations, bins=50, kde=True) # More bins for detail
            plt.title("Distribution of Session Duration (1 sec - 12 hours)")
            plt.xlabel("Session Duration (minutes)")
            plt.ylabel("Number of Sessions")
            plt.tight_layout()
            plt.savefig(duration_chart)
            plt.close()
            add_chart(duration_chart)

            mean_duration = reasonable_durations.mean()
            median_duration = reasonable_durations.median()
            add_paragraph(f"""
            <b>Session Duration (1 sec - 12 hours):</b><br/>
            Average: {mean_duration:.1f} minutes<br/>
            Median: {median_duration:.1f} minutes<br/>
            Total sessions analyzed: {len(reasonable_durations):,}
            """)
        else:
            add_paragraph("No valid session durations found in the 1 sec - 12 hour range.")
            mean_duration = 'N/A' # Ensure variable exists for later checks
            median_duration = 'N/A'

        # Sessions per User (requires user_id)
        if 'user_id' in sessions.columns:
            sessions_per_user = sessions.groupby('user_id').size().reset_index(name='session_count')
            if not sessions_per_user.empty:
                avg_sessions = sessions_per_user['session_count'].mean()
                median_sessions = sessions_per_user['session_count'].median()

                plt.figure(figsize=(10, 6))
                # Limit bins, maybe use log scale if distribution is heavily skewed
                max_sessions_display = sessions_per_user['session_count'].quantile(0.95) # Cap at 95th percentile for plot clarity
                plot_data = sessions_per_user[sessions_per_user['session_count'] <= max_sessions_display]
                sns.histplot(plot_data['session_count'], bins=max(1, min(20, int(max_sessions_display))), kde=False)
                plt.title(f"Sessions per User Distribution (up to {max_sessions_display:.0f} sessions)")
                plt.xlabel("Number of Sessions per User")
                plt.ylabel("Number of Users")
                plt.tight_layout()
                plt.savefig(sessions_chart)
                plt.close()
                add_chart(sessions_chart)

                add_paragraph(f"""
                <b>Sessions per User:</b><br/>
                Average: {avg_sessions:.1f} sessions/user<br/>
                Median: {median_sessions:.0f} sessions/user<br/>
                Total users with sessions: {len(sessions_per_user):,}
                """)
            else:
                add_paragraph("Could not calculate sessions per user (no user_id groups found).")
        else:
             add_paragraph("Could not calculate sessions per user ('user_id' column missing).")
    else:
        add_paragraph("No session data available or 'session_duration_min' column missing.")

    # ---------------------------------
    # 3. TRAVEL PREFERENCES ANALYSIS
    # ---------------------------------
    add_section_title("3. Travel Preferences Analysis (Top 5)")
    if not events.empty and 'metadata' in events.columns:
        # Function to safely parse metadata
        def parse_metadata(meta):
            if isinstance(meta, dict):
                return meta
            elif isinstance(meta, str):
                try: return ast.literal_eval(meta) if meta.strip().startswith('{') else {}
                except: return {}
            return {}

        events['metadata_parsed'] = events['metadata'].apply(parse_metadata)

        # --- Flight Destinations ---
        flight_searches = events[events['event_type'] == 'search_flight'].copy()
        if not flight_searches.empty:
            flight_searches['destination'] = flight_searches['metadata_parsed'].apply(lambda x: x.get('destination') if isinstance(x, dict) else None)
            top_destinations = flight_searches['destination'].dropna().astype(str).str.strip().replace('', pd.NA).dropna().value_counts().head(5)

            if not top_destinations.empty:
                plt.figure(figsize=(10, 6))
                sns.barplot(y=top_destinations.index, x=top_destinations.values, palette="rocket", order=top_destinations.index) # Swapped axes
                plt.title("Top 5 Flight Destinations Searched")
                plt.xlabel("Number of Searches")
                plt.ylabel("Destination")
                plt.tight_layout()
                plt.savefig(destinations_chart)
                plt.close()
                add_chart(destinations_chart)
            else: add_paragraph("No flight destination data found in search event metadata.")
        else: add_paragraph("No 'search_flight' events found.")

        # --- Hotel Locations ---
        hotel_searches = events[events['event_type'] == 'search_hotel'].copy()
        if not hotel_searches.empty:
            hotel_searches['location'] = hotel_searches['metadata_parsed'].apply(lambda x: x.get('location') if isinstance(x, dict) else None)
            top_hotel_locations = hotel_searches['location'].dropna().astype(str).str.strip().replace('', pd.NA).dropna().value_counts().head(5)

            if not top_hotel_locations.empty:
                plt.figure(figsize=(10, 6))
                sns.barplot(y=top_hotel_locations.index, x=top_hotel_locations.values, palette="mako", order=top_hotel_locations.index) # Swapped axes
                plt.title("Top 5 Hotel Locations Searched")
                plt.xlabel("Number of Searches")
                plt.ylabel("Location")
                plt.tight_layout()
                plt.savefig(hotels_chart)
                plt.close()
                add_chart(hotels_chart)
            else: add_paragraph("No hotel location data found in search event metadata.")
        else: add_paragraph("No 'search_hotel' events found.")
    else:
        add_paragraph("No event data or 'metadata' column loaded. Cannot perform preference analysis.")

    # ---------------------------------
    # 4. BOOKING BEHAVIOR ANALYSIS
    # ---------------------------------
    add_section_title("4. Booking Behavior Insights")
    booking_status_counts = pd.Series(dtype=int) # Initialize

    if not events.empty:
        booking_event_types = [
            'book_flight', 'book_hotel', 'book_package', 'book_car', 'book_activity', 'book_train', 'repeat_booking', # Completed
            'abandon_booking', # Abandoned
            'cancel_booking' # Cancelled
        ]
        booking_events_df = events[events['event_type'].isin(booking_event_types)].copy()

        if not booking_events_df.empty:
            def categorize_booking(event_type):
                if event_type.startswith('book_') or event_type == 'repeat_booking': return 'Completed Booking'
                elif event_type == 'abandon_booking': return 'Abandoned Booking'
                elif event_type == 'cancel_booking': return 'Cancelled Booking'
                else: return 'Other'

            booking_events_df['booking_status'] = booking_events_df['event_type'].apply(categorize_booking)
            booking_status_counts = booking_events_df['booking_status'].value_counts()

            if not booking_status_counts.empty:
                plt.figure(figsize=(8, 5)) # Slightly wider pie
                status_colors = {'Completed Booking': 'mediumseagreen', 'Abandoned Booking': 'gold', 'Cancelled Booking': 'lightcoral', 'Other': 'grey'}
                plot_labels = booking_status_counts.index
                plot_colors = [status_colors.get(status, 'grey') for status in plot_labels]

                # Create labels with counts and percentages
                def make_autopct(values):
                    def my_autopct(pct):
                        total = sum(values)
                        val = int(round(pct*total/100.0))
                        return '{p:.1f}%  ({v:,})'.format(p=pct,v=val) if pct > 1 else '' # Hide tiny labels
                    return my_autopct

                plt.pie(booking_status_counts, labels=plot_labels, autopct=make_autopct(booking_status_counts),
                        startangle=90, colors=plot_colors, pctdistance=0.8, textprops={'fontsize': 9})
                plt.title("Booking Outcomes (Completion vs. Abandonment/Cancellation)")
                plt.ylabel("")
                plt.tight_layout()
                plt.savefig(booking_chart)
                plt.close()
                add_chart(booking_chart, width=5*inch, height=3*inch) # Adjust size
            else: add_paragraph("Could not determine booking statuses from filtered events.")
        else: add_paragraph("No booking, abandonment, or cancellation event data found.")

        # --- Time to Book Analysis ---
        # Requires valid session_start and booking event_time
        completed_bookings = events[events['event_type'].str.startswith('book_') | (events['event_type'] == 'repeat_booking')].copy()
        if not completed_bookings.empty and not sessions.empty and 'session_start' in sessions.columns:

            # Prepare for merge (ensure types match, drop NAs)
            completed_bookings = completed_bookings.dropna(subset=['user_id', 'event_time'])
            sessions_subset = sessions[['user_id', 'session_start']].dropna().copy()

            # Ensure user_id types are compatible before merge
            try:
                sessions_subset['user_id'] = sessions_subset['user_id'].astype(completed_bookings['user_id'].dtype)
            except Exception as e:
                print(f"Warning: Could not align user_id types for merge_asof: {e}")
                add_paragraph("Could not analyze time-to-book due to user_id type mismatch.")

            else: # Proceed if type alignment succeeded
                # Use merge_asof to find the session start *before* the booking event
                temp_merged = pd.merge_asof(
                    completed_bookings.sort_values('event_time'),
                    sessions_subset.sort_values('session_start'),
                    left_on='event_time',
                    right_on='session_start',
                    by='user_id',
                    direction='backward', # Find latest session_start <= event_time
                    tolerance=pd.Timedelta(hours=12) # Optional: only consider sessions started within 12h before booking
                ).dropna(subset=['session_start']) # Remove bookings without a matching recent session

                if not temp_merged.empty:
                    temp_merged['time_to_book_min'] = (temp_merged['event_time'] - temp_merged['session_start']).dt.total_seconds() / 60.0

                    # Filter for reasonable times (e.g., 0 mins to 4 hours)
                    reasonable_times = temp_merged[
                        (temp_merged['time_to_book_min'] >= 0) &
                        (temp_merged['time_to_book_min'] < 240)
                    ]['time_to_book_min'] # Select only the series

                    if not reasonable_times.empty:
                        plt.figure(figsize=(10, 6))
                        sns.histplot(reasonable_times, bins=40, kde=True)
                        plt.title("Time from Session Start to Booking (0-240 minutes)")
                        plt.xlabel("Minutes from Session Start")
                        plt.ylabel("Number of Bookings")
                        plt.tight_layout()
                        plt.savefig(time_to_book_chart)
                        plt.close()
                        add_chart(time_to_book_chart)
                        add_paragraph(f"Average time from session start to booking (0-240 min): {reasonable_times.mean():.1f} minutes (Median: {reasonable_times.median():.1f} min)")
                    else: add_paragraph("No 'time to book' data found within the 0-240 minute range.")
                else: add_paragraph("Could not find matching sessions for completed bookings using merge_asof.")
        else:
            add_paragraph("Insufficient data for time-to-book analysis (missing bookings, sessions, or required columns).")
    else:
        add_paragraph("No event data loaded. Cannot perform booking behavior analysis.")


    # ---------------------------------
    # 5. DEVICE AND PLATFORM ANALYSIS
    # ---------------------------------
    add_section_title("5. Device and Platform Behavior")
    if not users.empty and 'device_type' in users.columns:
        # Clean device types (e.g., lowercase, trim whitespace) before counting
        users['device_type_clean'] = users['device_type'].str.lower().str.strip().replace('', 'unknown')
        device_usage = users['device_type_clean'].value_counts().reset_index()
        device_usage.columns = ['device_type', 'count']

        if not device_usage.empty and device_usage['count'].sum() > 0:
            device_usage['percentage'] = (device_usage['count'] / device_usage['count'].sum() * 100)

            plt.figure(figsize=(8, 5))
            sns.barplot(x='device_type', y='percentage', data=device_usage, palette="Set2", order=device_usage.sort_values('percentage', ascending=False)['device_type'])
            plt.title("User Distribution by Device Type")
            plt.xlabel("Device Type")
            plt.ylabel("Percentage of Users (%)")
            plt.tight_layout()
            plt.savefig(device_chart)
            plt.close()
            add_chart(device_chart, width=5*inch, height=3*inch)

            # Optionally, add table for device counts/percentages
            device_table_data = [["Device Type", "User Count", "Percentage"]]
            for _, row in device_usage.iterrows():
                 device_table_data.append([row['device_type'], f"{row['count']:,}", f"{row['percentage']:.1f}%"])
            add_table(device_table_data, col_widths=[2*inch, 2*inch, 2*inch])

        else: add_paragraph("No valid device type data found in users table after cleaning.")
    else:
         add_paragraph("User data or 'device_type' column not available for device analysis.")

    # ---------------------------------
    # 6. RECOMMENDATIONS
    # ---------------------------------
    add_section_title("6. Behavioral Insights and Recommendations")

    reco_list = []
    # Check if booking_status_counts has data
    if not booking_status_counts.empty:
        total_outcomes = booking_status_counts.sum()
        if total_outcomes > 0:
            abandon_pct = booking_status_counts.get('Abandoned Booking', 0) / total_outcomes * 100
            if abandon_pct > 30: # Threshold for High Abandonment
                reco_list.append([
                    f"High Abandonment Rate (~{abandon_pct:.0f}%)",
                    "Investigate checkout friction: complex forms, unexpected costs (shipping, taxes), limited payment options, required login/signup. Implement abandoned cart recovery emails/notifications. Analyze events immediately preceding 'abandon_booking'."
                ])

            cancel_pct = booking_status_counts.get('Cancelled Booking', 0) / total_outcomes * 100
            if cancel_pct > 10: # Threshold for Notable Cancellations
                 reco_list.append([
                     f"Notable Cancellation Rate (~{cancel_pct:.0f}%)",
                     "Review cancellation policies for clarity and fairness. Collect cancellation reasons via survey if possible. Ensure product descriptions, pricing, and booking details are accurate and transparent to minimize expectation mismatch."
                 ])

    # Check session duration (use the calculated mean if available and numeric)
    if 'mean_duration' in locals() and isinstance(mean_duration, (int, float)):
        if mean_duration < 5: # Threshold for Short Sessions
            reco_list.append([
                f"Short Avg. Session Duration ({mean_duration:.1f} min)",
                "Potential issues: Poor landing page relevance, slow load times, confusing navigation, quick task completion (check conversion rates). Analyze entry/exit pages and user flows for short sessions. A/B test landing page content/design."
            ])
        elif mean_duration > 30: # Threshold for Long Sessions
             reco_list.append([
                 f"Long Avg. Session Duration ({mean_duration:.1f} min)",
                 "May indicate deep engagement OR user struggle. Analyze paths for long sessions: Are users comparing many options (good)? Or stuck/looping (bad)? Segment by task completion. Simplify complex flows, improve search/filtering, add clearer CTAs or help options."
             ])

    # Add fallback/general recommendations if few specific ones were triggered
    if len(reco_list) < 2:
         reco_list.extend([
             ["Funnel Drop-off Points", "Analyze conversion rates between specific funnel stages (e.g., search-to-view, view-to-intent, intent-to-book) for key products (flights vs. hotels). Identify the biggest leaks and focus optimization efforts there."],
             ["Device Experience Parity", "Compare key metrics (conversion rate, avg. session duration, bounce rate, abandonment rate) across device types (desktop, mobile, tablet). Prioritize improvements for underperforming device segments."],
             ["Personalization Opportunities", "Leverage top searched destinations/locations and viewed items data. Personalize homepage content, promotional emails, and targeted ads based on user preferences inferred from behavior."],
             # ["A/B Testing", "Systematically test changes based on insights (e.g., simplified checkout form, different CTA text, new filter options) using A/B testing to measure impact on key metrics."]
         ])

    # Ensure there's always at least one recommendation row for table structure
    if not reco_list:
        reco_list.append(["General Review", "Conduct a comprehensive review of user paths, session recordings (if available), and feedback to identify specific pain points and opportunities for improvement across the user journey."])


    # Add the recommendations table using the IMPROVED add_table function
    add_paragraph("Based on the analysis, consider the following actions:")
    add_table([["Potential Insight Area", "Suggested Action / Investigation"]] + reco_list, col_widths=[2.5*inch, 4.5*inch]) # Adjusted widths

    # ---------------------------------
    # Generate PDF
    # ---------------------------------
    try:
        doc = SimpleDocTemplate(pdf_path, pagesize=A4,
                                leftMargin=0.5*inch, rightMargin=0.5*inch,
                                topMargin=0.5*inch, bottomMargin=0.5*inch)
        doc.build(report_elements)
        print(f"PDF report generated successfully: {pdf_path}")
    except Exception as e:
        print(f"Error generating PDF: {e}")

# ==================================================================
# Error Handling and Cleanup
# ==================================================================
except Exception as e:
    print(f"An unexpected error occurred during report generation: {e}")
    import traceback
    traceback.print_exc() # Print detailed traceback for debugging

finally:
    # Define chart files list inside finally to ensure it's available
    chart_files = [
        os.path.join(chart_dir, "funnel_chart.png"),
        os.path.join(chart_dir, "duration_chart.png"),
        os.path.join(chart_dir, "sessions_chart.png"),
        os.path.join(chart_dir, "destinations_chart.png"),
        os.path.join(chart_dir, "hotels_chart.png"),
        os.path.join(chart_dir, "booking_chart.png"),
        os.path.join(chart_dir, "time_to_book_chart.png"),
        os.path.join(chart_dir, "device_chart.png")
    ]

    # Clean up: Close the database connection cleanly
    if conn:
        try:
            conn.close()
            print("Database connection closed.")
        except Exception as db_close_e:
            print(f"Error closing database connection: {db_close_e}")


    # Attempt cleanup of temp chart files
    print("Attempting to clean up chart files...")
    for chart_file in chart_files:
        if os.path.exists(chart_file):
            try:
                os.remove(chart_file)
                # print(f" - Removed: {os.path.basename(chart_file)}") # Optional: less verbose
            except Exception as e:
                print(f"Warning: Could not remove chart file {os.path.basename(chart_file)}: {e}")

    # Attempt to remove the chart directory if it's empty
    if os.path.exists(chart_dir):
        try:
            if not os.listdir(chart_dir): # Check if directory is empty
                 os.rmdir(chart_dir)
                 print(f"Removed empty chart directory: {chart_dir}")
            # else: # Optional: message if not empty
            #     print(f"Info: Chart directory '{chart_dir}' not empty, not removed.")
        except OSError as e:
            print(f"Warning: Could not remove chart directory '{chart_dir}': {e}")

    print("Script finished.")