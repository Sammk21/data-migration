import psycopg2
import json
from datetime import datetime

# Database connection
conn = psycopg2.connect(
    host="localhost",
    database="onlyeducation",
    user="postgres",
    password="seaCalf"
)
cursor = conn.cursor()

# Load the exam JSON data
with open('../university_exam_data.json', 'r', encoding='utf-8') as file:
    exam_data_list = json.load(file)  # Load list of exams

# Function to insert into the 'exams' table and return the generated exam ID
def insert_exam(exam_data):
    query = """
    INSERT INTO onlyedudb.exams 
    (title, conducting_body, accepting_colleges, total_applications, about_exam, syllabus, eligibility_criteria, application_process, preparation_tips, admit_card, cut_off, counselling_process, exam_type, exam_level, created_at, updated_at, exam_pattern)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id;
    """
    
    # Convert syllabus into jsonb format
    syllabus_json = json.dumps(exam_data.get('syllabus', []))  # syllabus is a list
    
    # Handle 'N/A' or invalid integer values by setting them to zero or None
    total_applications = exam_data.get('total_applications', '0')
    if not total_applications.isdigit():
        total_applications = 0

    # Get exam pattern or set to None if missing
    exam_pattern = exam_data.get('exam_pattern', {}).get('html_content', None)

    # Data mapping with None defaults
    exam = (
        exam_data.get('exam_name', None),
        exam_data.get('conducting_body', None),
        exam_data.get('accepting_colleges', None),
        int(total_applications),  # Convert to int, or 0 if it's 'N/A'
        exam_data.get('about_exam', {}).get('description', None),
        syllabus_json,  # syllabus as jsonb (handled as a list)
        exam_data.get('eligibility_criteria', {}).get('html_content', None),
        exam_data.get('application_process', {}).get('html_content', None),
        exam_data.get('preparation_tips', {}).get('html_content', None),
        exam_data.get('admit_card', {}).get('html_content', None),
        exam_data.get('cutoffs', {}).get('html_content', None),
        exam_data.get('counselling_process', {}).get('html_content', None),
        exam_data.get('exam_type', None),
        exam_data.get('exam_level', None),
        datetime.now(),
        datetime.now(),
        exam_pattern  # Add exam pattern field or None if missing
    )

    cursor.execute(query, exam)
    exam_id = cursor.fetchone()[0]
    conn.commit()
    return exam_id

# Insert into the 'exams_stream_links' table to link exams to a stream
def link_exam_to_stream(exam_id, stream_id):
    query = """
    INSERT INTO onlyedudb.exams_stream_links (exam_id, stream_id)
    VALUES (%s, %s) ON CONFLICT (exam_id, stream_id) DO NOTHING;
    """
    cursor.execute(query, (exam_id, stream_id))
    conn.commit()

# Insert into related components (highlights, documents, FAQs)
def insert_exam_components(exam_id, exam_data):
    # Insert highlights
    for highlight in exam_data.get('highlights', []):
        query = """
        INSERT INTO onlyedudb.components_exam_components_exam_highlights_tables (key, value)
        VALUES (%s, %s) RETURNING id;
        """
        cursor.execute(query, (highlight.get('key', None), highlight.get('value', None)))
        highlight_id = cursor.fetchone()[0]
        
        # Link with exam_components
        link_query = """
        INSERT INTO onlyedudb.exams_components (entity_id, component_id, component_type, field)
        VALUES (%s, %s, %s, %s);
        """
        cursor.execute(link_query, (exam_id, highlight_id, 'exam-components.exam-highlights-table', 'highlights'))

    # Insert documents required
    for document in exam_data.get('documents_required', []):
        # Convert the list of documents into a WYSIWYG-style HTML unordered list
        documents_html = "<ul>" + "".join([f"<li>{doc}</li>" for doc in document.get('documents', [])]) + "</ul>"
        
        query = """
        INSERT INTO onlyedudb.components_exam_components_documents_requireds (title, documents)
        VALUES (%s, %s) RETURNING id;
        """
        cursor.execute(query, (
            document.get('heading', None),  # Use heading or None
            documents_html  # Save as an unordered HTML list
        ))
        document_id = cursor.fetchone()[0]

        # Link with exam_components
        link_query = """
        INSERT INTO onlyedudb.exams_components (entity_id, component_id, component_type, field)
        VALUES (%s, %s, %s, %s);
        """
        cursor.execute(link_query, (exam_id, document_id, 'exam-components.documents-required', 'documents_required'))

    # Insert FAQs
    for faq in exam_data.get('faqs', []):
        query = """
        INSERT INTO onlyedudb.components_exam_components_faqs (question, answer)
        VALUES (%s, %s) RETURNING id;
        """
        cursor.execute(query, (faq.get('question', None), faq.get('answer', None)))
        faq_id = cursor.fetchone()[0]

        # Link with exam_components
        link_query = """
        INSERT INTO onlyedudb.exams_components (entity_id, component_id, component_type, field)
        VALUES (%s, %s, %s, %s);
        """
        cursor.execute(link_query, (exam_id, faq_id, 'global.faq', 'faq'))

    conn.commit()

# Stream ID for Design (you can change this for other streams later)
stream_id = 23

# Loop through the list of exams and insert the data for each one
for exam_data in exam_data_list:
    exam_id = insert_exam(exam_data)
    insert_exam_components(exam_id, exam_data)
    link_exam_to_stream(exam_id, stream_id)  # Link each exam to the Design stream

# Close the cursor and connection
cursor.close()
conn.close()
print("Data migration completed successfully!")
