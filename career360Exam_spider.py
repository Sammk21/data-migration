import scrapy

class Career360Spider(scrapy.Spider):
    name = 'career360'
    allowed_domains = ['university.careers360.com']
    start_urls = ['https://university.careers360.com/exams']

    def parse(self, response):
        # Extracting exam blocks from the page
        exams = response.css('div.examListing_card')
        for exam in exams:
            # Using asset URLs to identify the correct fields
            offline_data = exam.css('.school_infooo .offline li')
            exam_type = None
            exam_level = None
            conducting_body = None
            accepting_colleges = None
            total_applications = None

            for item in offline_data:
                img_url = item.css('img::attr(src)').get()
                
                # Identifying 'Exam Type' by asset URL
                if img_url == 'https://cnextassets.careers360.com/frontend-article/_react_article/assets/offline.svg':
                    exam_type = ''.join(item.css('::text').getall()).strip()

                # Identifying 'Exam Level' by asset URL
                elif img_url == 'https://cnextassets.careers360.com/frontend-article/_react_article/assets/exam.svg':
                    exam_level = ''.join(item.css('::text').getall()).strip()

                # Identifying 'Conducting Body' by asset URL
                elif img_url == 'https://cnextassets.careers360.com/frontend-article/_react_article/assets/festingage.svg':
                    conducting_body = ''.join(item.css('::text').getall()).strip()

                # Identifying 'Accepting Colleges' by asset URL
                elif img_url == 'https://cnextassets.careers360.com/frontend-article/_react_article/assets/acceptingcollege.svg':
                    accepting_colleges = ''.join(item.css('::text').getall()).strip()

                # Identifying 'Total Applications' by asset URL
                elif img_url == 'https://cnextassets.careers360.com/frontend-article/_react_article/assets/seats.svg':
                    total_applications = ''.join(item.css('::text').getall()).strip()

            yield {
                'exam_name': ''.join(exam.css('.school_infooo .title .school_Name a::text').getall()).strip(),
                'exam_link': exam.css('.school_infooo .title a::attr(href)').get(),  # Use get() for single URL
                'exam_type': exam_type or 'N/A',
                'exam_level': exam_level or 'N/A',
                'conducting_body': conducting_body or 'N/A',
                'accepting_colleges': accepting_colleges or 'N/A',
                'total_applications': total_applications or 'N/A',
                'application_link': exam.css('div.group a::attr(href)').getall(),  # Already correct, captures all links
            }

        # Handling pagination
        next_page = response.css('a.pagination_list_last::attr(href)').get()
        if next_page:
            yield scrapy.Request(url=response.urljoin(next_page), callback=self.parse)


