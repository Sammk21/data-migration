import scrapy
import json

class TestCareer360Spider(scrapy.Spider):
    name = 'test_career360'
    allowed_domains = ['engineering.careers360.com']
    
    # Replace with the link to a single exam page for testing purposes
    start_urls = ['https://engineering.careers360.com/exams/jee-advanced']

    def parse(self, response):
        # Extract the "About Exam" heading and description for this specific exam
        about_heading = response.css('div#about .common_heading h2::text').get()
        about_description = response.css('div#about .description-block').get()

        # Extracting Highlights section (table format)
        highlights = {}
        for row in response.css('div#highlights table tr'):
            key = row.css('td.bold::text').get()
            value = row.css('td div::text').get()
            if key and value:
                highlights[key.strip()] = value.strip()

        # Extract the Eligibility Criteria section in WYSIWYG (HTML) format
        eligibility_criteria_html = response.css('div#Eligibility_Criteria .description-block').get()

        # Extract the Application Process section in WYSIWYG (HTML) format
        application_process_html = response.css('div#Application_Process .description-block').get()
        
        #Extract Prep Tips
        preperation_tip_html = response.css('div#Preparation_Tips .description-block').get()
        
        #Extract Admit card
        admit_card_html = response.css('div#Admit_Card .description-block').get()
        
        cutOff_html = response.css('div#Cutoff .description-block').get()
        
        counselling_process_html = response.css('div#Counselling_Process .description-block').get()

        # Extract the Exam Pattern section
        exam_patterns = []
        exam_pattern_heading = response.css('div#Exam_Pattern .common_heading h2::text').get()
        exam_pattern_content = response.css('div#Exam_Pattern .description-block').get()

        exam_patterns.append({
            'heading': exam_pattern_heading.strip() if exam_pattern_heading else 'N/A',
            'content': exam_pattern_content.strip() if exam_pattern_content else 'N/A'
        })
        
        syllabus_data = []

        # Extracting the main exam title (Accordion Titles)
        syllabus_accordions = response.css('div.syllabus_accordian')
        for accordion in syllabus_accordions:
            main_exam_title = accordion.css('span.main-exam::text').get().strip() if accordion.css('span.main-exam::text').get() else 'N/A'

            subjects = accordion.css('div.accordion-item')  # Looping over each subject within the accordion
            subject_data = []

            for subject in subjects:
                # Extract subject name
                subject_name = subject.css('span.syllabus_subject_name::text').get().strip() if subject.css('span.syllabus_subject_name::text').get() else 'N/A'

                # Extract unit information inside each subject
                units_data = []
                units = subject.css('div.accordion-body div.border_bottom')

                for unit in units:
                    syllabus_unit = ' '.join(unit.css('p.ed_syllabus_unit::text').getall()).strip() if unit.css('p.ed_syllabus_unit::text').get() else 'N/A'
                    syllabus_heading = unit.css('a.syllabus-heading-unit::text').get().strip() if unit.css('a.syllabus-heading-unit::text').get() else 'N/A'
                    topics_html = unit.css('ul').get().strip() if unit.css('ul').get() else 'N/A'

                    # Append unit details
                    units_data.append({
                        'syllabus_unit': syllabus_unit,
                        'syllabus_heading': syllabus_heading,
                        'topics_html': topics_html  # WYSIWYG format
                    })

                # Append subject and its units to the subject data
                subject_data.append({
                    'subject_name': subject_name,
                    'units': units_data
                })

            # Append main exam title and subjects to syllabus data
            syllabus_data.append({
                'main_exam_title': main_exam_title,
                'subjects': subject_data
            })

            
        
        documents_required = []

        # Locate the documents section (by heading "Documents Required at MET 2025 Counselling")
        documents_section = response.css('div#documents_required_counselling')

        # Extract the heading for the documents section
        documents_heading = documents_section.css('h2.title-block::text').get().strip()

        # Extract each document from the unordered list
        documents_list = documents_section.css('ul li.exam_detail_documents_required::text').getall()

        # Append the extracted heading and list of documents
        documents_required.append({
            'heading': documents_heading,
            'documents': [doc.strip() for doc in documents_list]
        })
        
        faq_list = []

        # Locate each FAQ block
        faq_blocks = response.css('div.qna_question_box')

        # Loop through each block and extract the question and answer
        for block in faq_blocks:
            # Extract the question (only if available)
            question = block.css('div.qna_question_heading span:nth-of-type(2)::text').get()
            if question:
                question = question.strip()
            else:
                question = 'N/A'

            # Extract the answer (only if available)
            answer = block.css('div.faq_question div p::text').get()
            if answer:
                answer = answer.strip()
            else:
                answer = 'N/A'

            # Append the question and answer to the list
            faq_list.append({
                'question': question,
                'answer': answer
            })

        # Prepare the data for saving to JSON
        exam_data = {
            'exam_name': 'MET',
            'about_heading': about_heading.strip() if about_heading else 'N/A',
            'about_description': about_description.strip() if about_description else 'N/A',
            'highlights': highlights,
            'eligibility_criteria': eligibility_criteria_html.strip() if eligibility_criteria_html else 'N/A',
            'application_process': application_process_html.strip() if application_process_html else 'N/A',
            'exam_patterns': exam_patterns,
            'syllabus': syllabus_data,
            'preparation_tips': preperation_tip_html,
            'admit_card':admit_card_html,
            'cutOff':cutOff_html,
            'counselling_process':counselling_process_html,
            'documents_required': documents_required,
            'faqs': faq_list,
        }

        # Saving the data to a JSON file
        if exam_data:
            file_name = 'exam_data_jee.json'
            with open(file_name, 'w', encoding='utf-8') as f:
                json.dump(exam_data, f, ensure_ascii=False, indent=4)

            self.log(f'Saved exam data with Exam Patterns and other sections to {file_name}')
