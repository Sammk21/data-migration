import psycopg2
from psycopg2.extras import Json
import json
from slugify import slugify
from datetime import datetime

# Load the JSON data
with open('m_bschool_exam_data.json',  'r', encoding='utf-8') as file:
    exams_data = json.load(file)


# Database connection details
conn = psycopg2.connect(
    host="192.238.19.130",
    database="onlyeducation",
    user="superadmin",
    password="seaCalf"
)
cursor = conn.cursor()

# Insert into the 'exams_stream_links' table to link exams to a stream
def link_exam_to_stream(exam_id, stream_id):
    query = """
    INSERT INTO onlyedudb.exams_stream_links (exam_id, stream_id)
    VALUES (%s, %s) ON CONFLICT (exam_id, stream_id) DO NOTHING;
    """
    cursor.execute(query, (exam_id, stream_id))
    conn.commit()

# Function to convert array to HTML <ul> list
def convert_array_to_html_list(array):
    html_list = "<ul>"
    for item in array:
        html_list += f"<li>{item}</li>"
    html_list += "</ul>"
    return html_list

# Helper function to handle 'N/A' or missing data
def sanitize_data(value, data_type=None):
    if value in ['N/A', '', None]:
        return None  # Convert invalid or missing values to None (NULL in SQL)
    if data_type == 'integer' and isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return None  # If the value cannot be converted to integer, return None
    return value

# Function to check if a slug already exists in the database
def check_slug_exists(slug):
    query = "SELECT EXISTS(SELECT 1 FROM onlyedudb.exams WHERE slug = %s);"
    cursor.execute(query, (slug,))
    return cursor.fetchone()[0]  # Returns True if the slug exists, False otherwise

# Function to generate a unique slug
def generate_unique_slug(title):
    base_slug = slugify(title)
    unique_slug = base_slug
    count = 1
    
    # Check if the slug already exists and modify if necessary
    while check_slug_exists(unique_slug):
        unique_slug = f"{base_slug}-{count}"
        count += 1

    return unique_slug

# Function to insert exam and return the generated exam ID
def insert_exam(exam):
    insert_exam_query = """
    INSERT INTO onlyedudb.exams
    (title, slug, conducting_body, accepting_colleges, total_applications, exam_type, exam_level, syllabus, created_at, updated_at)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    RETURNING id
    """
    
    # Generate a unique slug for the exam
    slug = generate_unique_slug(exam['exam_name'])
    
    # Insert the main exam data
    cursor.execute(insert_exam_query, (
        exam['exam_name'], 
        slug, 
        exam['conducting_body'], 
        exam['accepting_colleges'], 
        sanitize_data(exam['total_applications'], 'integer'),
        exam['exam_type'], 
        exam['exam_level'], 
        Json(exam['syllabus']),
        datetime.now(),
        datetime.now()
    ))

    # Get the generated exam_id
    exam_id = cursor.fetchone()[0]
    conn.commit()
    return exam_id

# Function to insert exam components (highlights, FAQs, documents, etc.)
def insert_exam_components(exam_id, exam):
    # Insert highlights
    for highlight in exam.get('highlights', []):
        insert_highlight_query = """
        INSERT INTO onlyedudb.components_exam_components_exam_highlights_tables (key, value)
        VALUES (%s, %s) RETURNING id;
        """
        cursor.execute(insert_highlight_query, (highlight['key'], highlight['value']))
        highlight_id = cursor.fetchone()[0]

        # Link the highlight with the exam in the exams_components table
        link_query = """
        INSERT INTO onlyedudb.exams_components (entity_id, component_id, component_type, field)
        VALUES (%s, %s, %s, %s);
        """
        cursor.execute(link_query, (exam_id, highlight_id, 'highlight', 'highlights'))

    # Insert FAQs
    for faq in exam.get('faqs', []):
        insert_faq_query = """
        INSERT INTO onlyedudb.components_exam_components_faqs (question, answer)
        VALUES (%s, %s) RETURNING id;
        """
        cursor.execute(insert_faq_query, (faq.get('question', None), faq.get('answer', None)))
        faq_id = cursor.fetchone()[0]

        # Link the FAQ with the exam
        link_query = """
        INSERT INTO onlyedudb.exams_components (entity_id, component_id, component_type, field)
        VALUES (%s, %s, %s, %s);
        """
        cursor.execute(link_query, (exam_id, faq_id, 'global.faq', 'faq'))

    # Insert documents_required
    if 'documents_required' in exam:
        for document in exam['documents_required']:
            # Convert the documents array to an HTML list
            document_html = convert_array_to_html_list(document.get('documents', []))
            
            print(document.get('heading'))
            print(document_html)

            # Insert the document into components_exam_components_doc_reqs
            insert_document_query = """
            INSERT INTO onlyedudb.components_exam_components_doc_reqs (title, content)
            VALUES (%s, %s) RETURNING id;
            """
            cursor.execute(insert_document_query, (
                document.get('heading', None), 
                document_html
            ))
            
            # Fetch the generated document ID
            document_id = cursor.fetchone()[0]
            
            print(document_id)

            # Link the document to the exam in exams_components
            link_query = """
            INSERT INTO onlyedudb.exams_components (entity_id, component_id, component_type, field)
            VALUES (%s, %s, %s, %s);
            """
            cursor.execute(link_query, (exam_id, document_id, 'exam-components.doc-req', 'doc_req'))


    # Insert sections
    for section in exam.get('sections', []):
        insert_section_query = """
        INSERT INTO onlyedudb.components_course_compoents_sections (title, content)
        VALUES (%s, %s) RETURNING id;
        """
        cursor.execute(insert_section_query, (section.get('title', None), section.get('content', None)))
        section_id = cursor.fetchone()[0]

        # Link the section with the exam
        link_query = """
        INSERT INTO onlyedudb.exams_components (entity_id, component_id, component_type, field)
        VALUES (%s, %s, %s, %s);
        """
        cursor.execute(link_query, (exam_id, section_id, 'section', 'sections'))

    conn.commit()
    
stream_id = 3

# Main migration loop
for exam in exams_data:
    exam_id = insert_exam(exam)
    insert_exam_components(exam_id, exam)
    link_exam_to_stream(exam_id, stream_id)

# Close the connection
cursor.close()
conn.close()

print("Exam data migration completed successfully!")
