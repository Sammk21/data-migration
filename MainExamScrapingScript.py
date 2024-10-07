import scrapy
import json
import uuid

class Career360Spider(scrapy.Spider):
    name = 'career360'
    allowed_domains = ['law.careers360.com']
    start_urls = ['https://law.careers360.com/exams']

    def __init__(self):
        super().__init__()
        # To store all exams in an array before writing to the file
        self.exams_data = []

    def parse(self, response):
        exams = response.css('div.examListing_card')
        for exam in exams:
            offline_data = exam.css('.school_infooo .offline li')
            exam_type, exam_level, conducting_body, accepting_colleges, total_applications = None, None, None, None, None

            for item in offline_data:
                img_url = item.css('img::attr(src)').get()
                if img_url == 'https://cnextassets.careers360.com/frontend-article/_react_article/assets/offline.svg':
                    exam_type = ''.join(item.css('::text').getall()).strip()
                elif img_url == 'https://cnextassets.careers360.com/frontend-article/_react_article/assets/exam.svg':
                    exam_level = ''.join(item.css('::text').getall()).strip()
                elif img_url == 'https://cnextassets.careers360.com/frontend-article/_react_article/assets/festingage.svg':
                    conducting_body = ''.join(item.css('::text').getall()).strip()
                elif img_url == 'https://cnextassets.careers360.com/frontend-article/_react_article/assets/acceptingcollege.svg':
                    accepting_colleges = ''.join(item.css('::text').getall()).strip()
                elif img_url == 'https://cnextassets.careers360.com/frontend-article/_react_article/assets/seats.svg':
                    total_applications = ''.join(item.css('::text').getall()).strip()

            exam_link = exam.css('.school_infooo .title a::attr(href)').get()
            yield scrapy.Request(
                url=response.urljoin(exam_link),
                callback=self.parse_exam_details,
                meta={
                    'exam_name': ''.join(exam.css('.school_infooo .title .school_Name a::text').getall()).strip(),
                    'exam_type': exam_type or 'N/A',
                    'exam_level': exam_level or 'N/A',
                    'conducting_body': conducting_body or 'N/A',
                    'accepting_colleges': accepting_colleges or 'N/A',
                    'total_applications': total_applications or 'N/A',
                    'application_link': exam.css('div.group a::attr(href)').getall(),
                }
            )

        next_page = response.css('a.pagination_list_last::attr(href)').get()
        if next_page:
            yield scrapy.Request(url=response.urljoin(next_page), callback=self.parse)

    def parse_exam_details(self, response):
        exam_id = str(uuid.uuid4())

        exam_data = {
            'exam_id': exam_id,
            'exam_name': response.meta['exam_name'],
            'exam_type': response.meta['exam_type'],
            'exam_level': response.meta['exam_level'],
            'conducting_body': response.meta['conducting_body'],
            'accepting_colleges': response.meta['accepting_colleges'],
            'total_applications': response.meta['total_applications'],
            'application_link': response.meta['application_link'],
        }

        exam_data['about_exam'] = {
            'about_id': str(uuid.uuid4()),
            'heading': response.css('div#about .common_heading h2::text').get() or 'N/A',
            'description': response.css('div#about .description-block').get() or 'N/A',
        }

        highlights = []
        for row in response.css('div#highlights table tr'):
            key = row.css('td.bold::text').get()
            value = row.css('td div::text').get()
            if key and value:
                highlights.append({
                    'highlight_id': str(uuid.uuid4()),
                    'key': key.strip(),
                    'value': value.strip()
                })
        exam_data['highlights'] = highlights

        exam_data['eligibility_criteria'] = {
            'criteria_id': str(uuid.uuid4()),
            'html_content': response.css('div#Eligibility_Criteria .description-block').get() or 'N/A'
        }

        exam_data['application_process'] = {
            'process_id': str(uuid.uuid4()),
            'html_content': response.css('div#Application_Process .description-block').get() or 'N/A'
        }

        exam_data['preparation_tips'] = {
            'prep_id': str(uuid.uuid4()),
            'html_content': response.css('div#Preparation_Tips .description-block').get() or 'N/A'
        }

        exam_data['admit_card'] = {
            'admit_id': str(uuid.uuid4()),
            'html_content': response.css('div#Admit_Card .description-block').get() or 'N/A'
        }

        exam_data['cutoffs'] = {
            'cutoff_id': str(uuid.uuid4()),
            'html_content': response.css('div#Cutoff .description-block').get() or 'N/A'
        }

        exam_data['counselling_process'] = {
            'counselling_id': str(uuid.uuid4()),
            'html_content': response.css('div#Counselling_Process .description-block').get() or 'N/A'
        }
        exam_data['Exam_Pattern'] = {
            'examPattern_id': str(uuid.uuid4()),
            'html_content': response.css('div#Exam_Pattern .description-block').get() or 'N/A'
        }

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
                    syllabus_unit = unit.css('p.ed_syllabus_unit::text').get().strip() if unit.css('p.ed_syllabus_unit::text').get() else 'N/A'
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
        exam_data['syllabus'] = syllabus_data
        
        exam_data['documents_required'] = {
            'examPattern_id': str(uuid.uuid4()),
            'html_content': response.css('div#documents_required').get() or 'N/A'
        }
        

        faq_list = []
        faq_blocks = response.css('div.qna_question_box')
        for block in faq_blocks:
            question = block.css('div.qna_question_heading span:nth-of-type(2)::text').get() or 'N/A'
            answer = block.css('div.faq_question div p::text').get() or 'N/A'
            faq_list.append({
                'faq_id': str(uuid.uuid4()),
                'question': question,
                'answer': answer
            })
        exam_data['faqs'] = faq_list

        # Append the data for this exam to the array of exams
        self.exams_data.append(exam_data)

        self.log(f'Collected data for {exam_data["exam_name"]}')

    def closed(self, reason):
        # Write the full array of exams to the JSON file when the spider closes
        with open('law_exam_data.json', 'w', encoding='utf-8') as f:
            json.dump(self.exams_data, f, ensure_ascii=False, indent=4)
        self.log('Saved all exam data to exams_data.json')
