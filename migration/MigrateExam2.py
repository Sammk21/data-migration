import psycopg2
from psycopg2.extras import Json
import json
from slugify import slugify
from datetime import datetime

# Define the stream mappings
STREAM_MAPPINGS = {
    '../Exams/exams_data/bschool_exam_data.json': 3,
    '../Exams/exams_data/competition_exam_data.json': 16,
    '../Exams/exams_data/design_exam_data.json': 9,
    '../Exams/exams_data/engineering_exam_data.json': 1,
    '../Exams/exams_data/finance_exam_data.json': 17,
    '../Exams/exams_data/it_exam_data.json': 18,
    '../Exams/exams_data/law_exam_data.json': 10,
    '../Exams/exams_data/media_exam_data.json': 20,
    '../Exams/exams_data/medicine_exam_data.json': 2,
    '../Exams/exams_data/pharmacy_exam_data.json': 12,
    '../Exams/exams_data/school_exam_data.json': 19,
    '../Exams/exams_data/studyabroad_exam_data.json': 21,
    '../Exams/exams_data/university_exam_data.json': 22
}

# Database connection details
conn = psycopg2.connect(
    host="localhost",
    database="onlyeducation",
    user="postgres",
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
        return None
    if data_type == 'integer' and isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return None
    return value

# Function to check if a slug already exists in the database
def check_slug_exists(slug):
    query = "SELECT EXISTS(SELECT 1 FROM onlyedudb.exams WHERE slug = %s);"
    cursor.execute(query, (slug,))
    return cursor.fetchone()[0]

# Function to generate a unique slug
def generate_unique_slug(title):
    base_slug = slugify(title)
    unique_slug = base_slug
    count = 1
    
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
    
    slug = generate_unique_slug(exam['exam_name'])
    
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

    exam_id = cursor.fetchone()[0]
    conn.commit()
    return exam_id

# Function to insert exam components
def insert_exam_components(exam_id, exam):
    # Insert highlights
    for highlight in exam.get('highlights', []):
        insert_highlight_query = """
        INSERT INTO onlyedudb.components_exam_components_exam_highlights_tables (key, value)
        VALUES (%s, %s) RETURNING id;
        """
        cursor.execute(insert_highlight_query, (highlight['key'], highlight['value']))
        highlight_id = cursor.fetchone()[0]

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

        link_query = """
        INSERT INTO onlyedudb.exams_components (entity_id, component_id, component_type, field)
        VALUES (%s, %s, %s, %s);
        """
        cursor.execute(link_query, (exam_id, faq_id, 'global.faq', 'faq'))

    # Insert documents_required
    if 'documents_required' in exam:
        for document in exam['documents_required']:
            document_html = convert_array_to_html_list(document.get('documents', []))
            
            insert_document_query = """
            INSERT INTO onlyedudb.components_exam_components_doc_reqs (title, content)
            VALUES (%s, %s) RETURNING id;
            """
            cursor.execute(insert_document_query, (
                document.get('heading', None), 
                document_html
            ))
            
            document_id = cursor.fetchone()[0]

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

        link_query = """
        INSERT INTO onlyedudb.exams_components (entity_id, component_id, component_type, field)
        VALUES (%s, %s, %s, %s);
        """
        cursor.execute(link_query, (exam_id, section_id, 'section', 'sections'))

    conn.commit()

def process_json_file(filename):
    """Process a single JSON file and return its data"""
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"File not found: {filename}")
        return None
    except json.JSONDecodeError:
        print(f"Invalid JSON in file: {filename}")
        return None

# Statistics tracking
stats = {
    'total_exams': 0,
    'successful_migrations': 0,
    'failed_migrations': 0,
    'successful_files': 0,
    'failed_files': 0
}

failed_exams = []

# Main migration loop
try:
    for json_file, stream_id in STREAM_MAPPINGS.items():
        print(f"\nProcessing {json_file} for stream ID {stream_id}")
        exams_data = process_json_file(json_file)
        
        if exams_data is None:
            stats['failed_files'] += 1
            continue
            
        stats['successful_files'] += 1
        exam_count = 0
        
        for exam in exams_data:
            stats['total_exams'] += 1
            try:
                exam_id = insert_exam(exam)
                insert_exam_components(exam_id, exam)
                link_exam_to_stream(exam_id, stream_id)
                exam_count += 1
                stats['successful_migrations'] += 1
                print(f"Successfully migrated: {exam['exam_name']}")
            except Exception as e:
                stats['failed_migrations'] += 1
                failed_exams.append({
                    'file': json_file,
                    'exam_name': exam['exam_name'],
                    'error': str(e)
                })
                print(f"Failed to migrate {exam['exam_name']}: {str(e)}")
                conn.rollback()  # Rollback the failed transaction
                
        print(f"Completed {json_file}: {exam_count} exams processed")

except Exception as e:
    print(f"An error occurred during migration: {str(e)}")
    conn.rollback()

finally:
    # Print final statistics
    print("\nMigration Summary:")
    print("=" * 50)
    print(f"Total files processed: {stats['successful_files'] + stats['failed_files']}")
    print(f"Successful files: {stats['successful_files']}")
    print(f"Failed files: {stats['failed_files']}")
    print(f"Total exams processed: {stats['total_exams']}")
    print(f"Successful migrations: {stats['successful_migrations']}")
    print(f"Failed migrations: {stats['failed_migrations']}")
    
    if failed_exams:
        print("\nFailed Exams:")
        for fail in failed_exams:
            print(f"\nFile: {fail['file']}")
            print(f"Exam: {fail['exam_name']}")
            print(f"Error: {fail['error']}")
    
    cursor.close()
    conn.close()
    print("\nMigration process completed!")