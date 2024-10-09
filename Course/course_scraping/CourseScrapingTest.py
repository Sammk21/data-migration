import scrapy

class CoursesSpider(scrapy.Spider):
    name = 'courses'
    allowed_domains = ['collegedekho.com']
    start_urls = ['https://www.collegedekho.com/courses/']

    def parse(self, response):
        # Parsing the list of courses
        courses = response.css('.course_list')

        for course in courses:
            title = course.css('h2 a::text').get().strip()
            average_duration = course.css('li:contains("Average Duration") span::text').get().strip()
            average_fees = course.css('li:contains("Average Fees") span::text').get().strip()

            # Follow the link to the course details page
            detail_url = response.urljoin(course.css('h2 a::attr(href)').get())

            yield response.follow(detail_url, self.parse_course_details, meta={
                'title': title,
                'average_duration': average_duration,
                'average_fees': average_fees,
            })

    def parse_course_details(self, response):
        # Extract the meta information passed from the previous request
        title = response.meta['title']
        average_duration = response.meta['average_duration']
        average_fees = response.meta['average_fees']

        # Fetching description
        description = response.css('.snippet_caption__5YxeJ p::text').get()

        # Preparing an array to store sections as objects with title and content
        sections = []
        blocks = response.css('.block')
        
        for block in blocks:
            section_title = block.css('h2::text').get()
            section_content = block.css('.collegeDetail_overview__Qr159').get()  # HTML content
            
            # Only add to sections if both title and content are not None
            if section_title and section_content:
                sections.append({
                    'title': section_title.strip(),
                    'content': section_content.strip()
                })

        # Handling FAQs as question-answer pairs
        faqs = []
        faq_blocks = response.css('.CommonAccordion_classNotToggled__EI8FO .CommonAccordion_collapsible__w_Hcr')
        for faq in faq_blocks:
            question = faq.css('h3::text').get()
            answer = faq.css('p::text').get()
            if question and answer:
                faqs.append({
                    'question': question.strip(),
                    'answer': answer.strip()
                })

        yield {
            'title': title,
            'average_duration': average_duration,
            'average_fees': average_fees,
            'description': description,
            'sections': sections,
            'faqs': faqs  # Saving FAQs as a separate array
        }
