import scrapy
from scrapy.loader import ItemLoader
from itemloaders.processors import TakeFirst, MapCompose, Join
from w3lib.html import remove_tags

class CollegeItem(scrapy.Item):
    name = scrapy.Field()
    url = scrapy.Field()
    nirf_rank = scrapy.Field()
    careers360_rating = scrapy.Field()
    ownership = scrapy.Field()
    user_rating = scrapy.Field()
    review_count = scrapy.Field()
    courses = scrapy.Field()
    fees = scrapy.Field()
    about = scrapy.Field()
    highlights = scrapy.Field(output_processor=TakeFirst())
    placement_stats = scrapy.Field(output_processor=TakeFirst())
    ranking_stats = scrapy.Field(output_processor=TakeFirst())
    admission_info = scrapy.Field(output_processor=TakeFirst())

class Careers360Spider(scrapy.Spider):
    name = 'careers360'
    start_urls = ['https://engineering.careers360.com/colleges/ranking']

    def parse(self, response):
        college_blocks = response.css('div.tupple')

        for block in college_blocks:
            loader = ItemLoader(item=CollegeItem(), selector=block)
            loader.default_output_processor = TakeFirst()

            loader.add_css('name', 'h3.college_name a::text')
            loader.add_css('url', 'h3.college_name a::attr(href)')
            loader.add_css('nirf_rank', 'div.tupple_top_block_left strong::text')
            loader.add_css('careers360_rating', 'div.content_block span strong::text')
            loader.add_css('ownership', 'div.content_block span strong.strong_ownership::text')
            loader.add_css('user_rating', 'span.star_text b::text')
            loader.add_css('review_count', 'span.review_text a::text')
            loader.add_css('courses', 'div.snippet_block ul.snippet_list li a::text', Join(', '))
            loader.add_css('fees', 'div.snippet_block ul.snippet_list li:contains("Fees")::text', Join(', '))

            # Load the basic details
            college_item = loader.load_item()

            # Follow the college URL to scrape additional details
            college_url = response.urljoin(college_item['url'])
            yield scrapy.Request(college_url, callback=self.parse_college_page, meta={'item': college_item})

        # Pagination
        next_page = response.css('a.pagination_list_last::attr(href)').get()
        if next_page:
            yield scrapy.Request(url=response.urljoin(next_page), callback=self.parse)

    def parse_college_page(self, response):
        item = response.meta['item']
        loader = ItemLoader(item=item, response=response)
        loader.default_output_processor = TakeFirst()

        # About section
        about_content = ' '.join(response.css('#about_blk .description p::text').getall()).strip()
        loader.add_value('about', about_content)

        # Highlights section
        highlights = {}
        for row in response.css('div.table-responsive tr'):
            key = row.css('td:first-child::text').get()
            value = row.css('td:last-child::text').get()

            # Only add non-empty keys and values to the highlights dictionary
            if key and value:
                highlights[key.strip()] = value.strip()
        loader.add_value('highlights', highlights)

        # Placement section
        placement_stats = {
            'description': ' '.join(response.css('#placements .description::text').getall()).strip(),
            'statistics': {}
        }
        for row in response.css('#placements .table-responsive tr'):
            key = row.css('td:first-child::text').get()
            value = row.css('td:last-child::text').get()

            # Only add non-empty keys and values to the placement_stats dictionary
            if key and value:
                placement_stats['statistics'][key.strip()] = value.strip()
        loader.add_value('placement_stats', placement_stats)

        # Ranking section
        ranking_stats = {}
        for tab in response.css('ul.nav-tabs .nav-link'):
            category = tab.css('::text').get().strip()
            tab_content = response.css(f'div#{tab.attrib["aria-controls"]}')
            overall_score = tab_content.css('.parametric_score strong::text').get()

            ranking_stats[category] = {'overall_score': overall_score}

            for row in tab_content.css('.table-responsive tr'):
                param_name = row.css('td:first-child::text').get()
                param_value = row.css('td:last-child::text').get()

                # Only add non-empty param_name and param_value to the ranking_stats
                if param_name and param_value:
                    ranking_stats[category][param_name.strip()] = param_value.strip()
        loader.add_value('ranking_stats', ranking_stats)

        # Admission section
        admission_info = {
            'description': ' '.join(response.css('#admission_blk .description::text').getall()).strip(),
            'read_more_link': response.css('#admission_blk .read_more a::attr(href)').get(),
            'view_all_process_link': response.css('#admission_blk .btnNext a::attr(href)').get(),
        }
        loader.add_value('admission_info', admission_info)

        yield loader.load_item()
