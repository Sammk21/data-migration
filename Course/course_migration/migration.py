import psycopg2
import json
from datetime import datetime
from slugify import slugify  # You can install python-slugify for generating slugs

# Database connection
conn = psycopg2.connect(
    host="localhost",
    database="onlyeducation",
    user="postgres",
    password="seaCalf"
)
cursor = conn.cursor()

# Load the course JSON data
with open('../course_data/courses.json', 'r', encoding='utf-8') as file:
    course_data_list = json.load(file)  # Load list of courses


# Function to check if a slug already exists in the database
def check_slug_exists(slug):
    query = "SELECT EXISTS(SELECT 1 FROM onlyedudb.coursees WHERE slug = %s);"
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

# Function to insert into the 'courses' table and return the generated course ID
def insert_course(course_data):
    query = """
    INSERT INTO onlyedudb.coursees 
    (title, slug, average_duration, average_fees, description, created_at, updated_at)
    VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id;
    """
    
    # Generate a unique slug for the course
    slug = generate_unique_slug(course_data['title'])
    
    # Data mapping with None defaults
    course = (
        course_data.get('title', None),
        slug,
        course_data.get('average_duration', None),
        course_data.get('average_fees', None),
        course_data.get('description', None),
        datetime.now(),
        datetime.now()
    )

    cursor.execute(query, course)
    course_id = cursor.fetchone()[0]
    conn.commit()
    return course_id


# Insert into the 'coursees_components' table to link sections, FAQs, and other components
def insert_course_components(course_id, course_data):
    # Insert sections (this part is unchanged)
    for section in course_data.get('sections', []):
        query = """
        INSERT INTO onlyedudb.components_course_compoents_sections (title, content)
        VALUES (%s, %s) RETURNING id;
        """
        cursor.execute(query, (section.get('title', None), section.get('content', None)))
        section_id = cursor.fetchone()[0]

        # Link with course_components
        link_query = """
        INSERT INTO onlyedudb.coursees_components (entity_id, component_id, component_type, field)
        VALUES (%s, %s, %s, %s);
        """
        cursor.execute(link_query, (course_id, section_id, 'section', 'sections'))

    # Insert FAQs (new part)
    insert_faqs(course_id, course_data.get('faqs', []))

    conn.commit()

    # Insert FAQs
def insert_faqs(course_id, faqs):
    for faq in faqs:
        # Insert the FAQ into the components_exam_components_faqs table
        query = """
        INSERT INTO onlyedudb.components_exam_components_faqs (question, answer)
        VALUES (%s, %s) RETURNING id;
        """
        cursor.execute(query, (faq.get('question', None), faq.get('answer', None)))
        faq_id = cursor.fetchone()[0]

        # Link the FAQ with the course in the coursees_components table
        link_query = """
        INSERT INTO onlyedudb.coursees_components (entity_id, component_id, component_type, field)
        VALUES (%s, %s, %s, %s);
        """
        cursor.execute(link_query, (course_id, faq_id, 'global.faq', 'faq'))
    
    conn.commit()

# Loop through the list of courses and insert the data for each one
for course_data in course_data_list:
    course_id = insert_course(course_data)
    insert_course_components(course_id, course_data)

# Close the cursor and connection
cursor.close()
conn.close()
print("Course data migration completed successfully!")
