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
with open('../design_exam_data.json', 'r', encoding='utf-8') as file:
    exam_data_list = json.load(file)  # Load all exam data

# Insert into the 'exams' table
def insert_exam(exam_data):
    query = """
    INSERT INTO onlyedudb.exams 
    (title, conducting_body, accepting_colleges, total_applications, about_exam, syllabus, eligibility_criteria, application_process, preparation_tips, admit_card, cut_off, counselling_process, exam_type, exam_level, created_at, updated_at, exam_pattern)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id;
    """
    
    # Convert syllabus into jsonb format
    syllabus_json = json.dumps(exam_data['syllabus'])
    
    # Handle 'N/A' or invalid integer values by setting them to zero
    total_applications = exam_data['total_applications']
    if not total_applications.isdigit():
        total_applications = 0

    # Handle missing exam_pattern by setting it to an empty string if not found
    exam_pattern = exam_data.get('exam_pattern', {}).get('html_content', '')

    # Data mapping
    exam = (
        exam_data['exam_name'],
        exam_data['conducting_body'],
        exam_data['accepting_colleges'],
        int(total_applications),  # Convert to int, or 0 if it's 'N/A'
        exam_data['about_exam']['description'],
        syllabus_json,  # syllabus as jsonb
        exam_data['eligibility_criteria']['html_content'],
        exam_data['application_process']['html_content'],
        exam_data['preparation_tips']['html_content'],
        exam_data['admit_card']['html_content'],
        exam_data['cutoffs']['html_content'],
        exam_data['counselling_process']['html_content'],
        exam_data['exam_type'],
        exam_data['exam_level'],
        datetime.now(),
        datetime.now(),
        exam_pattern  # Add exam pattern field with default empty string if missing
    )

    cursor.execute(query, exam)
    exam_id = cursor.fetchone()[0]
    conn.commit()
    return exam_id

# Insert into related components (highlights, documents, FAQs)
def insert_exam_components(exam_id, exam_data):
    # Insert highlights
    for highlight in exam_data['highlights']:
        query = """
        INSERT INTO onlyedudb.components_exam_components_exam_highlights_tables (key, value)
        VALUES (%s, %s) RETURNING id;
        """
        cursor.execute(query, (highlight['key'], highlight['value']))
        highlight_id = cursor.fetchone()[0]
        
        # Link with exam_components
        link_query = """
        INSERT INTO onlyedudb.exams_components (entity_id, component_id, component_type, field)
        VALUES (%s, %s, %s, %s);
        """
        cursor.execute(link_query, (exam_id, highlight_id, 'exam-components.exam-highlights-table', 'highlights'))

    # Insert documents required
    for document in exam_data['documents_required']:
        # Convert the list of documents into a WYSIWYG-style HTML unordered list
        documents_html = "<ul>" + "".join([f"<li>{doc}</li>" for doc in document['documents']]) + "</ul>"
        
        query = """
        INSERT INTO onlyedudb.components_exam_components_documents_requireds (title, documents)
        VALUES (%s, %s) RETURNING id;
        """
        cursor.execute(query, (
            document['heading'],  # Use heading as title
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
    for faq in exam_data['faqs']:
        query = """
        INSERT INTO onlyedudb.components_exam_components_faqs (question, asnwer)
        VALUES (%s, %s) RETURNING id;
        """
        cursor.execute(query, (faq['question'], faq['answer']))
        faq_id = cursor.fetchone()[0]

        # Link with exam_components
        link_query = """
        INSERT INTO onlyedudb.exams_components (entity_id, component_id, component_type, field)
        VALUES (%s, %s, %s, %s);
        """
        cursor.execute(link_query, (exam_id, faq_id, 'global.faq', 'faq'))

    conn.commit()

# Loop through all exams and run migration for each one
for exam_data in exam_data_list:
    exam_id = insert_exam(exam_data)
    insert_exam_components(exam_id, exam_data)

# Close the cursor and connection
cursor.close()
conn.close()
print("Data migration completed successfully!")
