import scrapy
from w3lib.html import remove_tags_with_content
from scrapy import Request

class CombinedCollegesSpider(scrapy.Spider):
    name = 'combined_colleges_spider'
    allowed_domains = ['collegedekho.com']
    start_urls = ['https://www.collegedekho.com/engineering/colleges-in-india/']

    custom_settings = {
        'DOWNLOAD_DELAY': 0.5,
        'FEEDS': {
            'colleges.json': {
                'format': 'json',
                'overwrite': True,
            }
        }
    }

    processed_colleges = set()

    def parse(self, response):
        college_blocks = response.css('div.collegeCardBox.col-md-12')

        listing_card_blocks = response.css('div.collegeCardBox.listingCard.col-md-12 div.collegeCardBox.col-md-12')
        all_blocks = college_blocks + listing_card_blocks

        for college in all_blocks:
            
            title = college.css('div.titleSection h3 a::text').get().strip()
            
            if title in self.processed_colleges:
                continue
            
            self.processed_colleges.add(title)
            
            location_info = college.css('div.collegeinfo ul.info li:nth-child(2)::text').get()
            city, state = location_info.split(', ') if location_info else (None, None)
            
            ownership_li = college.css('div.collegeinfo ul.info li')
            ownership = None
            for li in ownership_li:
                img_src = li.css('img::attr(src)').get()
                if img_src and 'flag.29bda52542d4.svg' in img_src:
                    ownership = li.css('::text').getall()[-1].strip()
                    break

            ranking = college.css('div.collegeinfo ul.info li b span::text').get()
            rank_publisher = college.css('div.collegeinfo ul.info li b::text').re_first(r'\s*(\w+)')
            if ranking:
                ranking = ranking.replace('#', '').strip()

            fees = college.css('div.fessSection li img[src*="rupeeListing"] + p::text').get()
            fees = fees.strip() if fees else None

            accreditation = college.css('div.fessSection li img[src*="batch"] + p::text').get()
            accreditation = accreditation.strip() if accreditation else None

            avg_package = college.css('div.fessSection li img[src*="symbol"] + p::text').get()
            avg_package = avg_package.strip() if avg_package else None

            exams = []
            exam_li = college.css('div.fessSection li img[src*="exam.57dec076328a.svg"]')
            if exam_li:
                main_exam = exam_li.xpath('following-sibling::p/text()[normalize-space()]').get().strip()
                exams.append(main_exam)
                tooltip_exams_text = exam_li.xpath('following-sibling::div[@class="tooltip"]//span[@class="hover"]/text()').get()
                if tooltip_exams_text:
                    tooltip_exams = [exam.strip() for exam in tooltip_exams_text.split(',') if exam.strip()]
                    exams.extend(tooltip_exams)
            exams = list(set(exams))

            description = college.css('div.content.ReadMore::text').get()
            description = description.strip() if description else None

            # Store initial college data
            college_data = {
                'title': title,
                'city': city,
                'state': state,
                'ownership': ownership,
                'ranking': ranking,
                'rank_publisher': rank_publisher,
                'fees': fees,
                'accreditation': accreditation,
                'avg_package': avg_package,
                'exams': exams,
                'description': description
            }

            # Get college-specific link and pass college_data along with the request to parse the details page
            college_link = college.css('div.titleSection h3 a::attr(href)').get()
            if college_link:
                yield response.follow(college_link, self.parse_college_page, meta={'college_data': college_data})
            
            pagination_block = response.css('div.pagination ul li a::attr(href)').getall()    

        # Handle pagination for college list
            next_page = response.css('li.round a::attr(href)').get()
            if next_page:
                yield response.follow(next_page, self.parse)

    def parse_college_page(self, response):
        college_data = response.meta['college_data']

        # Extract overview tab content
        college_data['overviewTab'] = self.extract_overview_tab(response)
        
        # Extract highlights
        college_data['highlights'] = self.extract_highlights(response)
        
        # Extract courses
        college_data['courses'] = self.extract_courses(response)
        
        # Extract FAQs
        college_data['faqs'] = self.extract_faqs(response)

        # Extract and follow sub-navigation tabs
        nav_tabs = response.css('.container.mobileContainerNone ul li a')
        for tab in nav_tabs:
            tab_title = tab.css('::text').get().strip()
            tab_url = tab.css('::attr(href)').get()

            if tab_title not in ['Gallery', 'Reviews', 'News', 'QnA']:
                yield response.follow(
                    tab_url, 
                    self.parse_tab_content, 
                    meta={'college_data': college_data, 'tab_title': tab_title}
                )

    def extract_overview_tab(self, response):
        overview_tab = []
        static_blocks = response.css('.collegeDetailContainer')
        for block in static_blocks:
            title = block.css('.sectionHeadingSpace h2::text').get()
            content = block.xpath(
                './/div[contains(@class, "staticContent_staticContentBlcok__MmmkX")]'
                '/div[not(contains(@class, "staticContent_hideContent__fj6cN")) and not(contains(@class, "BannerContent_readMore__WMDLd"))]'
                '| .//div[contains(@class, "staticContent_hideContent__fj6cN") or contains(@class, "BannerContent_readMore__WMDLd")]/*'
            ).getall()

            title = title.strip() if title else None
            content = [remove_tags_with_content(c, which_ones=('a',)) for c in content]
            content_html = ''.join(content).strip()
            
            if title and content_html and not any(item['title'] == title for item in overview_tab):
                overview_tab.append({
                    'title': title,
                    'content': content_html
                })
        return overview_tab

    def extract_highlights(self, response):
        highlights = response.css('.collegeHighlightsCard_collegeHighlightBox__Efa_o')
        highlight_dict = {}
        for item in highlights:
            key = item.css('.collegeHighlightsCard_highlightName__NP6u9::text').get()
            value = item.css('.collegeHighlightsCard_highlightLabel__5B3__::text').get()
            if key and value:
                highlight_dict[key.strip()] = value.strip()
        return highlight_dict

    def extract_courses(self, response):
        courses = []
        course_blocks = response.css('.courseCard_courseCard__dfnvS')
        for course in course_blocks:
            course_data = {
                'course_title': self.safe_extract(course, '.courseName_courseHeading__CudEq a::text'),
                'fees': self.safe_extract(course, '.courseCardDetail_detailBoldText__ukBXc::text'),
                'duration': self.safe_extract(course, '.courseCardDetail_courseDetailList__eCaZU div::text'),
                'study_mode': self.safe_extract(course, '.courseCardDetail_courseDetailList__eCaZU div:nth-child(3)::text'),
                'eligibility': self.safe_extract(course, '.courseCardDetail_eligibilityText__H12Xm::text'),
                'offered_courses': course.css('.courseCardDetail_detailBoldText__ukBXc span span::attr(title)').getall()
            }
            course_data = {k: v for k, v in course_data.items() if v}
            if course_data.get('course_title') and not any(c['course_title'] == course_data['course_title'] for c in courses):
                courses.append(course_data)
        return courses

    def extract_faqs(self, response):
        faqs = []
        faq_blocks = response.css('.accordion_accordionInner__J27vt')
        for faq in faq_blocks:
            question = self.safe_extract(faq, 'h3::text')
            answer = self.safe_extract(faq, '.accordion_content__KQYJ_ div::text')
            if question and answer and not any(f['question'] == question for f in faqs):
                faqs.append({'question': question, 'answer': answer})
        return faqs

    def parse_tab_content(self, response):
        college_data = response.meta['college_data']
        tab_title = response.meta['tab_title']
        
        tab_key = f"{tab_title.replace(' ', '').lower()}Tab"
        tab_data = {'tab': tab_title, 'content': []}

        blocks = response.css('.block.box')
        for block in blocks:
            title = self.safe_extract(block, 'h2::text')
            content = block.xpath(
                './/div[contains(@class, "collegeDetail_classRead__yd_kT")]/span[contains(@class, "collegeDetail_overview__Qr159")]/*'
                '| .//div[contains(@class, "collegeDetail_classRead__yd_kT")]/*'
            ).getall()
            
            content = [remove_tags_with_content(c, which_ones=('a',)) for c in content]
            content_html = ''.join(content).strip()
            
            if title and content_html and not any(item['title'] == title for item in tab_data['content']):
                tab_data['content'].append({
                    'title': title,
                    'content': content_html
                })

        if 'campus' in tab_title.lower():
            facilities = self.extract_facilities(response)
            if facilities:
                tab_data['facilities'] = facilities

        college_data[tab_key] = tab_data

        # If this is the last tab, yield the complete college data
        if tab_title == "CutOffs":  # Assuming "CutOffs" is the last tab before excluded ones
            yield college_data

        # Handle pagination within tabs if present
        next_page = response.css('.loadMore_loadMoreBlock__PH_zn span::text').get()
        if next_page:
            yield response.follow(
                next_page, 
                self.parse_tab_content, 
                meta={'college_data': college_data, 'tab_title': tab_title}
            )

    def extract_facilities(self, response):
        facilities_section = response.css('.collegeDetail_facilities__wrgyU')
        if facilities_section:
            facilities = facilities_section.css('ul li p::text').getall()
            return [facility.strip() for facility in facilities if facility.strip()]
        return None

    def safe_extract(self, selector, css_selector):
        extracted = selector.css(css_selector).get()
        return extracted.strip() if extracted else None