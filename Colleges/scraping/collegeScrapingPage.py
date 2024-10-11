import scrapy
from w3lib.html import remove_tags_with_content

class IitSpider(scrapy.Spider):
    name = 'iit_spider'
    allowed_domains = ['collegedekho.com']
    start_urls = ['https://www.collegedekho.com/colleges/iitb']

    def parse(self, response):
        # Scrape the overview tab first
        overview_tab = []
        static_blocks = response.css('.collegeDetailContainer')
        for block in static_blocks:
            title = block.css('.sectionHeadingSpace h2::text').get()

            # Exclude unwanted divs and include only children of valid content
            content = block.xpath(
                './/div[contains(@class, "staticContent_staticContentBlcok__MmmkX")]'
                '/div[not(contains(@class, "staticContent_hideContent__fj6cN")) and not(contains(@class, "BannerContent_readMore__WMDLd"))]'
                '| .//div[contains(@class, "staticContent_hideContent__fj6cN") or contains(@class, "BannerContent_readMore__WMDLd")]/*'
            ).getall()

            # Clean the title, exclude null or empty fields
            title = title.strip() if title else None

            # Remove <a> tags and content inside them
            content = [remove_tags_with_content(c, which_ones=('a',)) for c in content]

            # Exclude fields where title or content is None or empty, ensure no duplicates
            content_html = ''.join(content).strip()
            if title and content_html and not any(item['title'] == title for item in overview_tab):
                overview_tab.append({
                    'title': title,
                    'content': content_html  # Content as raw HTML with links removed
                })

        # Yield the overviewTab array if it contains data
        if overview_tab:
            yield {'overviewTab': overview_tab}

        # Scrape highlights section (handled as key-value pairs)
        highlights = response.css('.collegeHighlightsCard_collegeHighlightBox__Efa_o')
        highlight_dict = {}
        for item in highlights:
            key = item.css('.collegeHighlightsCard_highlightName__NP6u9::text').get()
            value = item.css('.collegeHighlightsCard_highlightLabel__5B3__::text').get()

            # Clean the key and value
            key = key.strip() if key else None
            value = value.strip() if value else None

            if key and value:
                highlight_dict[key] = value

        # Yield the highlights dictionary if it's not empty
        if highlight_dict:
            yield {'highlights': highlight_dict}

        # Scrape courses section
        courses = []
        course_blocks = response.css('.courseCard_courseCard__dfnvS')
        for course in course_blocks:
            course_title = course.css('.courseName_courseHeading__CudEq a::text').get()
            fees = course.css('.courseCardDetail_detailBoldText__ukBXc::text').get()
            duration = course.css('.courseCardDetail_courseDetailList__eCaZU div::text').get()
            study_mode = course.css('.courseCardDetail_courseDetailList__eCaZU div:nth-child(3)::text').get()
            eligibility = course.css('.courseCardDetail_eligibilityText__H12Xm::text').get()

            offered_courses = course.css('.courseCardDetail_detailBoldText__ukBXc span span::attr(title)').getall()

            # Clean the fields and structure data as per requirements
            course_data = {
                'course_title': course_title.strip() if course_title else None,
                'fees': fees.strip() if fees else None,
                'duration': duration.strip() if duration else None,
                'study_mode': study_mode.strip() if study_mode else None,
                'eligibility': eligibility.strip() if eligibility else None,
                'offered_courses': [course.strip() for course in offered_courses] if offered_courses else []
            }

            # Append valid course data to the courses array, ensuring no duplicates
            if course_data['course_title'] and not any(c['course_title'] == course_data['course_title'] for c in courses):
                courses.append(course_data)

        # Yield courses array if it's not empty
        if courses:
            yield {'courses': courses}

        # Scrape the FAQ section
        faqs = []
        faq_blocks = response.css('.accordion_accordionInner__J27vt')
        for faq in faq_blocks:
            question = faq.css('h3::text').get()
            answer = faq.css('.accordion_content__KQYJ_ div::text').get()

            # Clean the question and answer
            question = question.strip() if question else None
            answer = answer.strip() if answer else None

            # Ensure no duplicate FAQs
            if question and answer and not any(f['question'] == question for f in faqs):
                faqs.append({'question': question, 'answer': answer})

        # Yield FAQ array if it's not empty
        if faqs:
            yield {'faqs': faqs}

        # Now extract the URLs for each tab from the sub-navigation and scrape them
        nav_tabs = response.css('.container.mobileContainerNone ul li a')
        for tab in nav_tabs:
            tab_title = tab.css('a::text').get().strip()
            tab_url = tab.css('a::attr(href)').get()

            # Skip unwanted tabs like Gallery, Reviews, News, QnA
            if tab_title not in ['Gallery', 'Reviews', 'News', 'QnA']:
                # Follow the link to each tab and scrape its content
                yield response.follow(tab_url, self.parse_tab_content, meta={'tab_title': tab_title})

    def parse_tab_content(self, response):
        tab_title = response.meta.get('tab_title')
        tab_data = {'tab': tab_title, 'content': []}

        # Extract content from the block boxes and ignore certain divs
        blocks = response.css('.block.box')
        for block in blocks:
            title = block.css('h2::text').get()

            # Extract the inner content and ignore <span class="collegeDetail_overview__Qr159">
            content = block.xpath(
                './/div[contains(@class, "collegeDetail_classRead__yd_kT")]/span[contains(@class, "collegeDetail_overview__Qr159")]/*'
                '| .//div[contains(@class, "collegeDetail_classRead__yd_kT")]/*'
            ).getall()

            # Remove <a> tags and content inside them
            content = [remove_tags_with_content(c, which_ones=('a',)) for c in content]

            # Clean the title, exclude null or empty fields
            title = title.strip() if title else None

            # Exclude fields where title or content is None or empty, and avoid duplicates
            content_html = ''.join(content).strip()
            if title and content_html and not any(item['title'] == title for item in tab_data['content']):
                tab_data['content'].append({
                    'title': title,
                    'content': content_html  # Content as raw HTML without links
                })

        # Scraping facilities if this is the campus tab
        if 'campus' in tab_title.lower():
            facilities_section = response.css('.collegeDetail_facilities__wrgyU')
            if facilities_section:
                facilities = facilities_section.css('ul li p::text').getall()
                # Clean and save as an array of strings
                facilities = [facility.strip() for facility in facilities]

                if facilities:
                    tab_data['facilities'] = facilities

        # Yield the tab data if it contains content
        if tab_data['content'] or 'facilities' in tab_data:
            yield {tab_title.replace(" ", "").lower() + "Tab": tab_data}

        # Pagination handling if there is a load more button
        next_page = response.css('.loadMore_loadMoreBlock__PH_zn span::text').get()
        if next_page:
            yield scrapy.Request(response.urljoin(next_page), callback=self.parse_tab_content, meta={'tab_title': tab_title})
