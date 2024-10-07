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
    about = scrapy.Field(output_processor=TakeFirst())
    highlights = scrapy.Field(output_processor=TakeFirst())
    placement_stats = scrapy.Field(output_processor=TakeFirst())
    ranking_stats = scrapy.Field(output_processor=TakeFirst())
    admission_info = scrapy.Field(output_processor=TakeFirst())

class Careers360Spider(scrapy.Spider):
    name = 'careers360'
    start_urls = ['https://engineering.careers360.com/colleges/indian-institute-of-technology-madras']

    def parse(self, response):
        loader = ItemLoader(item=CollegeItem(), response=response)
        loader.default_output_processor = TakeFirst()

        loader.add_css('name', 'h1::text')
        loader.add_value('url', response.url)
        loader.add_css('nirf_rank', '.clg_rank_box strong::text')
        loader.add_css('careers360_rating', '.rating_btn span::text')
        loader.add_css('ownership', '.ownership::text')
        loader.add_css('user_rating', '.user_rating::text')
        loader.add_css('review_count', '.review_count::text')
        loader.add_css('courses', '.popular_courses li::text', Join(', '))
        loader.add_css('fees', '.fee_struc::text')

        # Load the basic details
        college_item = loader.load_item()

        # Use the current URL to scrape additional details
        yield scrapy.Request(response.url, callback=self.parse_college_page, meta={'item': college_item})

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