import scrapy

class CollegesSpider(scrapy.Spider):
    name = 'colleges'
    start_urls = ['https://www.collegedekho.com/engineering/colleges-in-india/']

    def parse(self, response):
        # Extract the initial blocks with class "collegeCardBox col-md-12"
        college_blocks = response.css('div.collegeCardBox.col-md-12')

        # Also handle the blocks inside "listingCard"
        listing_card_blocks = response.css('div.collegeCardBox.listingCard.col-md-12 div.collegeCardBox.col-md-12')

        # Combine both sets of blocks into one list
        all_blocks = college_blocks + listing_card_blocks

        # Iterate through all college blocks and extract data
        for college in all_blocks:
            # Extract the title (college name)
            title = college.css('div.titleSection h3 a::text').get().strip()

            # Extract city and state
            location_info = college.css('div.collegeinfo ul.info li:nth-child(2)::text').get()
            city, state = location_info.split(', ') if location_info else (None, None)

            # Ownership extraction by checking for the flag image
            ownership_li = college.css('div.collegeinfo ul.info li')
            ownership = None
            for li in ownership_li:
                img_src = li.css('img::attr(src)').get()
                if img_src and 'flag.29bda52542d4.svg' in img_src:
                    ownership = li.css('::text').getall()[-1].strip()
                    break

            # NIRF ranking (without the # symbol)
            ranking = college.css('div.collegeinfo ul.info li b span::text').get()
            rank_publisher = college.css('div.collegeinfo ul.info li b::text').re_first(r'\s*(\w+)')
            if ranking:
                ranking = ranking.replace('#', '').strip()

            # Fees extraction
            fees = college.css('div.fessSection li img[src*="rupeeListing"] + p::text').get()
            fees = fees.strip() if fees else None

            # Accreditation extraction
            accreditation = college.css('div.fessSection li img[src*="batch"] + p::text').get()
            accreditation = accreditation.strip() if accreditation else None

            # Average Package extraction
            avg_package = college.css('div.fessSection li img[src*="symbol"] + p::text').get()
            avg_package = avg_package.strip() if avg_package else None

            # Exams extraction (main exam and tooltip exams), cleaning up and removing duplicates
            exams = []

            exam_li = college.css('div.fessSection li img[src*="exam.57dec076328a.svg"]')
            if exam_li:
                # Main exam in the <p> tag before the <span>
                main_exam = exam_li.xpath('following-sibling::p/text()[normalize-space()]').get().strip()
                exams.append(main_exam)

                # Additional exams in the tooltip
                tooltip_exams_text = exam_li.xpath('following-sibling::div[@class="tooltip"]//span[@class="hover"]/text()').get()
                if tooltip_exams_text:
                    # Split by commas, clean up whitespace, and add to exams list
                    tooltip_exams = [exam.strip() for exam in tooltip_exams_text.split(',') if exam.strip()]
                    exams.extend(tooltip_exams)

            # Remove duplicates from the exams list
            exams = list(set(exams))

            # Description extraction
            description = college.css('div.content.ReadMore::text').get()
            description = description.strip() if description else None

            # Yield the results
            yield {
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
