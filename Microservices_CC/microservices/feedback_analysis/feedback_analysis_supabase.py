import psycopg2
from psycopg2.extras import DictCursor
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib import colors
import os
import warnings
from textblob import TextBlob
from wordcloud import WordCloud
from collections import Counter
import re

# Suppress warnings
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# --- Supabase Database Connection Details ---
# <<< CHANGED HERE: Updated DATABASE_URL >>>
DATABASE_URL = "postgresql://postgres:Bellad%400810@db.mvvkcjdydxqxwnzfmqhd.supabase.co:5432/postgres"

# Initialize connection and cursor variables
conn = None
cursor = None

# Database connection using psycopg2
try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor(cursor_factory=DictCursor)
    print("Successfully connected to Supabase database using connection string.") # Updated print message slightly
except Exception :
    print("Service currently unavailable. Try again later.")

    # Clean up if connection partially failed or cursor wasn't created
    if cursor:
        cursor.close()
    if conn:
        conn.close()
    exit() # Exit if connection fails

# --- Report Setup and Helper Functions (No changes needed below this line unless for robustness) ---

# Preparing styles for the PDF
styles = getSampleStyleSheet()
report_elements = []
pdf_path = "User_Feedback_Analysis_Report_NewDB.pdf" # Slightly changed output filename

# Helper functions (Consider adding error handling for file existence in add_chart)
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

def add_chart(img_path, width=6*inch, height=3.5*inch):
     # Check if file exists before adding
    if os.path.exists(img_path):
        try:
            report_elements.append(Image(img_path, width=width, height=height))
            report_elements.append(Spacer(1, 20))
        except Exception as e:
             print(f"Error adding image {img_path} to PDF: {e}")
             add_paragraph(f"<i>[Error displaying chart: {os.path.basename(img_path)}]</i>")
    else:
        print(f"Warning: Chart file not found: {img_path}")
        add_paragraph(f"<i>[Chart file not found: {os.path.basename(img_path)}]</i>")


def add_table(data, col_widths=None):
    if not data or len(data) < 1: # Check for empty data
        add_paragraph("<i>[No data available for table]</i>")
        return

    header_length = len(data[0])
    # Ensure all rows have the same number of columns as the header
    processed_data = [data[0]] # Start with the header
    for row in data[1:]:
        if isinstance(row, (list, tuple)): # Check if it's a list/tuple before checking length
            if len(row) == header_length:
                # Convert all items to string to avoid potential ReportLab errors with mixed types
                processed_data.append([str(item) if item is not None else '' for item in row])
            else:
                # Pad or truncate row if necessary
                print(f"Warning: Row length mismatch. Header={header_length}, Row={len(row)}. Padding/truncating.")
                padded_row = (list(row) + [''] * header_length)[:header_length]
                processed_data.append([str(item) if item is not None else '' for item in padded_row])
        else:
             print(f"Warning: Skipping invalid row data: {row}")


    if not processed_data or len(processed_data) <= 1: # Check if only header remains or empty
         add_paragraph("<i>[No valid data rows for table]</i>")
         return

    # Dynamic width calculation or default
    if col_widths is None:
        num_cols = len(processed_data[0])
        available_width = A4[0] - 1.5*inch # Page width minus margins
        col_widths = [available_width / num_cols] * num_cols

    try:
        table = Table(processed_data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('WORDWRAP', (0, 0), (-1, -1), 'CJK'), # Allow word wrapping
        ]))
        report_elements.append(table)
        report_elements.append(Spacer(1, 20))
    except Exception as e:
        print(f"Error creating table: {e}")
        add_paragraph(f"<i>[Error generating table: {e}]</i>")


# --- Data Loading and Processing Functions ---

# Loading the feedback data with sentiment analysis
def load_feedback_data(db_conn): # Pass connection
    # Get all feedback with user details - ASSUMES _q TABLES EXIST in the target DB
    # *** IMPORTANT: Verify 'user_feedback_q' and 'users_q' table names in the NEW database ***
    query = """
        SELECT f.*, u.country, u.city as user_city
        FROM user_feedback_q f
        JOIN users_q u ON f.user_id = u.id
    """
    try:
        feedback_df = pd.read_sql(query, db_conn)

        if feedback_df.empty:
            print("Warning: No feedback data loaded from the database.")
            return feedback_df # Return empty dataframe

        # Handle potential None/NaN before processing
        feedback_df['feedback_text'] = feedback_df['feedback_text'].fillna('')

        # Clean text data
        feedback_df['clean_text'] = feedback_df['feedback_text'].apply(lambda x: re.sub(r'[^\w\s]', '', str(x).lower()))

        # Calculate sentiment safely
        feedback_df['sentiment'] = feedback_df['feedback_text'].apply(lambda x: TextBlob(str(x)).sentiment.polarity if x else 0.0)

        # Categorize sentiment
        feedback_df['sentiment_category'] = pd.cut(feedback_df['sentiment'],
                                              bins=[-1.1, -0.5, -0.1, 0.1, 0.5, 1.1], # Adjusted bins
                                              labels=['Very Negative', 'Negative', 'Neutral', 'Positive', 'Very Positive'],
                                              right=True, include_lowest=True)
        return feedback_df

    except (Exception, pd.errors.DatabaseError, psycopg2.Error) as error:
        print(f"Error executing SQL query or reading data: {error}")
        print(f"Query attempted:\n{query}")
        # Return an empty DataFrame with expected columns for downstream safety
        return pd.DataFrame(columns=['id', 'user_id', 'service_type', 'location', 'feedback_text',
                                     'rating', 'submitted_at', 'booking_reference', 'sentiment_score',
                                     'keywords', 'country', 'user_city', 'clean_text', 'sentiment',
                                     'sentiment_category'])


# Extracting keywords from feedback
def extract_keywords(text):
    if pd.isna(text) or not isinstance(text, str):
        return []
    words = re.findall(r'\b\w{4,}\b', text.lower()) # Applied lower() here
    # Expanded stopwords slightly
    stopwords = {'the', 'and', 'was', 'were', 'this', 'that', 'with', 'for', 'they', 'have', 'has', 'had', 'but', 'not', 'are', 'you', 'your', 'very', 'just', 'from', 'service', 'experience', 'flight', 'hotel', 'room', 'staff', 'food', 'time', 'make', 'trip'}
    return [word for word in words if word not in stopwords and not word.isdigit()]


# --- Main Execution Block ---
try: # Wrap main logic in try block

    # Load data using the established connection
    feedback = load_feedback_data(conn) # Pass the connection object

    # Check if data loading was successful
    if feedback.empty:
        print("Exiting script as no data was loaded.")
        # Optional: Generate a minimal PDF indicating no data
        add_title("User Feedback Analysis Report")
        add_paragraph("<b>No feedback data found in the database.</b>")
        doc = SimpleDocTemplate(pdf_path, pagesize=A4)
        doc.build(report_elements)
        print(f"Generated empty report: {pdf_path}")

    else:
        # Apply keyword extraction only if data exists
        feedback['keywords'] = feedback['clean_text'].apply(extract_keywords)

        # Start Building PDF only if data is present
        add_title("User Feedback Analysis Report")
        add_section_title("Customer Satisfaction Insights")

        # 1. OVERALL SATISFACTION ANALYSIS
        add_section_title("1. Overall Satisfaction Metrics")
        if 'rating' in feedback.columns and not feedback['rating'].isnull().all():
            try:
                plt.figure(figsize=(10, 6))
                # Ensure ratings are treated appropriately, drop NaNs for countplot
                sns.countplot(x='rating', data=feedback.dropna(subset=['rating']), palette="viridis", order=sorted(feedback['rating'].dropna().unique().astype(int)))
                plt.title("Distribution of User Ratings")
                plt.xlabel("Rating (1-5)")
                plt.ylabel("Number of Reviews")
                plt.tight_layout()
                rating_chart = "rating_chart.png"
                plt.savefig(rating_chart)
                plt.close() # Close plot to free memory
                add_chart(rating_chart)
            except Exception as e:
                 print(f"Error generating rating distribution chart: {e}")
                 add_paragraph("<i>[Error generating rating chart]</i>")


            # Calculate satisfaction metrics safely
            valid_ratings = feedback['rating'].dropna()
            total_reviews = len(valid_ratings)
            if total_reviews > 0:
                avg_rating = valid_ratings.mean()
                positive_reviews = len(valid_ratings[valid_ratings >= 4])
                negative_reviews = len(valid_ratings[valid_ratings <= 2])
                percent_positive = round((positive_reviews / total_reviews * 100), 1)
                percent_negative = round((negative_reviews / total_reviews * 100), 1)
                avg_rating_display = f"{avg_rating:.2f}/5"
            else:
                avg_rating_display = "N/A"
                percent_positive = percent_negative = 0
                positive_reviews = negative_reviews = 0


            add_paragraph(f"""
            <b>Key Satisfaction Metrics:</b><br/>
            Average Rating: {avg_rating_display}<br/>
            Positive Reviews (4-5 stars): {percent_positive}% ({positive_reviews} reviews)<br/>
            Negative Reviews (1-2 stars): {percent_negative}% ({negative_reviews} reviews)<br/>
            Total Reviews Analyzed: {total_reviews}
            """)
        else:
             add_paragraph("<i>No valid rating data available for overall satisfaction analysis.</i>")


        # 2. SERVICE-SPECIFIC ANALYSIS
        add_section_title("2. Service-Specific Performance")
        if 'service_type' in feedback.columns and 'rating' in feedback.columns and not feedback['rating'].isnull().all():
            # Group by service_type and calculate mean/count, handling potential NaNs
            service_ratings = feedback.dropna(subset=['rating', 'service_type']).groupby('service_type')['rating'].agg(['mean', 'count']).round(2)
            service_ratings = service_ratings.reset_index().rename(columns={'mean': 'avg_rating', 'count': 'review_count'})
            service_ratings = service_ratings.sort_values(by='avg_rating', ascending=False) # Sort for clarity

            if not service_ratings.empty:
                try:
                    plt.figure(figsize=(12, 7)) # Adjust size if needed
                    sns.barplot(x='avg_rating', y='service_type', data=service_ratings, palette="rocket", orient='h') # Horizontal bar plot might be better for many services
                    plt.title("Average Rating by Service Type")
                    plt.xlabel("Average Rating (1-5)")
                    plt.ylabel("Service Type")
                    plt.xlim(0, 5.5)
                    # Add rating value labels to bars
                    for index, value in enumerate(service_ratings['avg_rating']):
                        plt.text(value + 0.05, index, f'{value:.2f}', va='center')
                    plt.tight_layout()
                    service_chart = "service_chart.png"
                    plt.savefig(service_chart)
                    plt.close()
                    add_chart(service_chart)
                except Exception as e:
                    print(f"Error generating service rating chart: {e}")
                    add_paragraph("<i>[Error generating service rating chart]</i>")

                # Add table with detailed service metrics
                service_table_data = [["Service", "Avg Rating", "Reviews", "% Positive"]]
                feedback_with_ratings = feedback.dropna(subset=['rating', 'service_type']) # Use filtered data
                for _, row in service_ratings.iterrows():
                    service_subset = feedback_with_ratings[feedback_with_ratings['service_type'] == row['service_type']]
                    positive_count = len(service_subset[service_subset['rating'] >= 4])
                    total_count = int(row['review_count'])
                    positive_pct = round((positive_count / total_count * 100), 1) if total_count > 0 else 0
                    service_table_data.append([row['service_type'], f"{row['avg_rating']:.2f}", total_count, f"{positive_pct}%"])

                add_table(service_table_data) # Let add_table calculate widths dynamically
            else:
                 add_paragraph("<i>No data available for service-specific rating analysis.</i>")
        else:
            add_paragraph("<i>'service_type' or 'rating' column missing or empty for service analysis.</i>")


        # 3. SENTIMENT ANALYSIS
        add_section_title("3. Sentiment Analysis")
        if 'sentiment_category' in feedback.columns and not feedback['sentiment_category'].isnull().all():
            try:
                plt.figure(figsize=(10, 6))
                sentiment_order = ['Very Negative', 'Negative', 'Neutral', 'Positive', 'Very Positive']
                valid_sentiment_data = feedback.dropna(subset=['sentiment_category'])
                # Plot only categories present in the data
                current_categories = valid_sentiment_data['sentiment_category'].cat.categories.tolist()
                plot_order = [cat for cat in sentiment_order if cat in current_categories]

                if plot_order: # Only plot if there are valid categories to plot
                    sns.countplot(x='sentiment_category', data=valid_sentiment_data,
                                order=plot_order,
                                palette="RdYlGn")
                    plt.title("Sentiment Distribution of Feedback")
                    plt.xlabel("Sentiment Category")
                    plt.ylabel("Number of Reviews")
                    plt.xticks(rotation=45, ha='right')
                    plt.tight_layout()
                    sentiment_chart = "sentiment_chart.png"
                    plt.savefig(sentiment_chart)
                    plt.close()
                    add_chart(sentiment_chart)
                else:
                     add_paragraph("<i>No valid sentiment categories found to plot distribution.</i>")
            except Exception as e:
                 print(f"Error generating sentiment distribution chart: {e}")
                 add_paragraph("<i>[Error generating sentiment distribution chart]</i>")
        else:
            add_paragraph("<i>No sentiment category data available for distribution plot.</i>")


        if 'rating' in feedback.columns and 'sentiment' in feedback.columns and not feedback['rating'].isnull().all() and not feedback['sentiment'].isnull().all():
            try:
                plt.figure(figsize=(10, 6))
                # Filter out NaNs before plotting
                plot_data = feedback.dropna(subset=['rating', 'sentiment'])
                sns.boxplot(x='rating', y='sentiment', data=plot_data, palette="viridis")
                plt.title("Sentiment Scores by Rating Level")
                plt.xlabel("Rating (1-5)")
                plt.ylabel("Sentiment Score (-1 to 1)")
                plt.tight_layout()
                sentiment_rating_chart = "sentiment_rating_chart.png"
                plt.savefig(sentiment_rating_chart)
                plt.close()
                add_chart(sentiment_rating_chart)
            except Exception as e:
                 print(f"Error generating sentiment vs rating chart: {e}")
                 add_paragraph("<i>[Error generating sentiment vs rating chart]</i>")
        else:
             add_paragraph("<i>Rating or sentiment score data missing for correlation plot.</i>")


        # 4. TEXT ANALYSIS
        add_section_title("4. Textual Feedback Insights")

        # Word cloud for positive reviews
        positive_feedback = feedback[(feedback['rating'] >= 4) & (feedback['clean_text'] != '')].dropna(subset=['clean_text'])
        if not positive_feedback.empty:
            positive_text = " ".join(positive_feedback['clean_text'])
            if positive_text.strip():
                try:
                    wordcloud_pos = WordCloud(width=800, height=400, background_color='white', collocations=False, max_words=100).generate(positive_text)
                    plt.figure(figsize=(12, 6))
                    plt.imshow(wordcloud_pos, interpolation='bilinear')
                    plt.axis("off")
                    plt.title("Frequent Terms in Positive Reviews (4-5 stars)")
                    plt.tight_layout()
                    wordcloud_positive_path = "wordcloud_positive.png"
                    plt.savefig(wordcloud_positive_path)
                    plt.close()
                    add_chart(wordcloud_positive_path)
                except ValueError as ve: # Handle case where text might be too short after filtering
                    print(f"Could not generate positive word cloud (ValueError): {ve}")
                    add_paragraph(f"<i>Could not generate positive word cloud: Not enough content after filtering?</i>")
                except Exception as e:
                    print(f"Error generating positive word cloud: {e}")
                    add_paragraph(f"<i>[Error generating positive word cloud]</i>")
            else:
                add_paragraph("<i>No text available for positive reviews word cloud.</i>")
        else:
             add_paragraph("<i>No positive reviews (4-5 stars) with text found for word cloud.</i>")


        # Word cloud for negative reviews
        negative_feedback = feedback[(feedback['rating'] <= 2) & (feedback['clean_text'] != '')].dropna(subset=['clean_text'])
        if not negative_feedback.empty:
            negative_text = " ".join(negative_feedback['clean_text'])
            if negative_text.strip():
                try:
                    wordcloud_neg = WordCloud(width=800, height=400, background_color='black', colormap='Reds', collocations=False, max_words=100).generate(negative_text)
                    plt.figure(figsize=(12, 6))
                    plt.imshow(wordcloud_neg, interpolation='bilinear')
                    plt.axis("off")
                    plt.title("Frequent Terms in Negative Reviews (1-2 stars)")
                    plt.tight_layout()
                    wordcloud_negative_path = "wordcloud_negative.png"
                    plt.savefig(wordcloud_negative_path)
                    plt.close()
                    add_chart(wordcloud_negative_path)
                except ValueError as ve:
                    print(f"Could not generate negative word cloud (ValueError): {ve}")
                    add_paragraph(f"<i>Could not generate negative word cloud: Not enough content after filtering?</i>")
                except Exception as e:
                    print(f"Error generating negative word cloud: {e}")
                    add_paragraph(f"<i>[Error generating negative word cloud]</i>")
            else:
                 add_paragraph("<i>No text available for negative reviews word cloud.</i>")
        else:
             add_paragraph("<i>No negative reviews (1-2 stars) with text found for word cloud.</i>")


        # Top keywords analysis
        if 'keywords' in feedback.columns:
            # Flatten list of keywords, ensuring we handle potential empty lists or NaNs
            all_keywords = [word for sublist in feedback['keywords'].dropna() if isinstance(sublist, list) for word in sublist]
            if all_keywords:
                try:
                    keyword_counts = Counter(all_keywords).most_common(15)
                    keywords_df = pd.DataFrame(keyword_counts, columns=['Keyword', 'Count'])

                    plt.figure(figsize=(12, 7))
                    sns.barplot(x='Count', y='Keyword', data=keywords_df, palette="mako", orient='h')
                    plt.title("Top 15 Keywords in Feedback (4+ letters, excluding common words)")
                    plt.xlabel("Frequency")
                    plt.ylabel("Keyword")
                    plt.tight_layout()
                    keywords_chart_path = "keywords_chart.png"
                    plt.savefig(keywords_chart_path)
                    plt.close()
                    add_chart(keywords_chart_path)
                except Exception as e:
                    print(f"Error generating keywords chart: {e}")
                    add_paragraph("<i>[Error generating keywords chart]</i>")
            else:
                 add_paragraph("<i>No keywords extracted for analysis.</i>")
        else:
            add_paragraph("<i>'keywords' column missing for keyword analysis.</i>")


        # 5. COMMON THEMES AND RECOMMENDATIONS (More Robust Example)
        add_section_title("5. Key Themes and Potential Recommendations")
        add_paragraph("This section provides high-level themes based on the analysis. Further qualitative analysis is recommended for specific actions.")

        recommendations_data = [["Analysis Area", "Observation / Potential Action"]]

        # Top/Bottom Service (if data exists)
        if 'service_ratings' in locals() and not service_ratings.empty:
             top_service = service_ratings.iloc[0] # Already sorted desc
             bottom_service = service_ratings.iloc[-1]
             recommendations_data.append(["Top Rated Service", f"{top_service['service_type']} ({top_service['avg_rating']:.2f}/5)"])
             recommendations_data.append(["Lowest Rated Service", f"{bottom_service['service_type']} ({bottom_service['avg_rating']:.2f}/5) - Investigate further"])
        else:
             recommendations_data.append(["Service Performance", "Data insufficient for comparison."])

        # Common Praise Themes (using top keywords from positive reviews)
        if 'positive_text' in locals() and positive_text.strip():
            pos_keywords = [word for sublist in positive_feedback['keywords'].dropna() if isinstance(sublist, list) for word in sublist]
            if pos_keywords:
                pos_kw_counts = Counter(pos_keywords).most_common(3)
                praise_themes = ", ".join([f"'{kw}' ({count})" for kw, count in pos_kw_counts])
                recommendations_data.append(["Common Praise Themes", f"Keywords like {praise_themes} frequently appear in positive feedback."])
            else:
                 recommendations_data.append(["Common Praise Themes", "No specific keywords dominate positive reviews."])
        else:
            recommendations_data.append(["Common Praise Themes", "No positive text to analyze."])

        # Common Complaint Themes (using top keywords from negative reviews)
        if 'negative_text' in locals() and negative_text.strip():
            neg_keywords = [word for sublist in negative_feedback['keywords'].dropna() if isinstance(sublist, list) for word in sublist]
            if neg_keywords:
                neg_kw_counts = Counter(neg_keywords).most_common(3)
                complaint_themes = ", ".join([f"'{kw}' ({count})" for kw, count in neg_kw_counts])
                recommendations_data.append(["Common Complaint Themes", f"Keywords like {complaint_themes} are common in negative feedback. Focus areas."])
            else:
                recommendations_data.append(["Common Complaint Themes", "No specific keywords dominate negative reviews."])
        else:
             recommendations_data.append(["Common Complaint Themes", "No negative text to analyze."])


        # Overall Sentiment
        if 'percent_positive' in locals():
             recommendations_data.append(["Overall Sentiment", f"{percent_positive}% positive ratings (4-5 stars)."])
        else:
             recommendations_data.append(["Overall Sentiment", "Rating data unavailable."])


        add_table(recommendations_data) # Let add_table handle widths


        # --- Generate the PDF ---
        doc = SimpleDocTemplate(pdf_path, pagesize=A4)
        doc.build(report_elements)
        print(f"PDF report generated: {pdf_path}")

# General exception handler for the main block
except Exception as e:
    print(f"An unexpected error occurred during script execution: {e}")
    import traceback
    traceback.print_exc() # Print detailed traceback for debugging

finally:
    # --- Clean up temp chart files ---
    chart_files = [
        "rating_chart.png", "service_chart.png", "sentiment_chart.png",
        "sentiment_rating_chart.png", "wordcloud_positive.png",
        "wordcloud_negative.png", "keywords_chart.png"
    ]
    print("Cleaning up chart files...")
    for chart_file in chart_files:
        try:
            if os.path.exists(chart_file):
                os.remove(chart_file)
                # print(f"Removed: {chart_file}") # Optional: confirm removal
        except Exception as e:
            print(f"Error removing {chart_file}: {e}")

    # --- Close Database Connection ---
    if cursor:
        try:
            cursor.close()
            print("Database cursor closed.")
        except Exception as e:
             print(f"Error closing cursor: {e}")
    if conn:
        try:
            conn.close()
            print("Database connection closed.")
        except Exception as e:
            print(f"Error closing connection: {e}")