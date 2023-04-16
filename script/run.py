import json
import logging
from io import StringIO
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
from tornado.ioloop import IOLoop
from pyquery import PyQuery



"""
https://www.futurepedia.io/api/tools?page=2&sort=new
"""


async def get_tools_by_page(page, sort="new"):
    try:
        url = 'https://www.futurepedia.io/api/tools?page={}&sort={}'.format(page, sort)
        response = await AsyncHTTPClient().fetch(HTTPRequest(url))
        return json.loads(response.body.decode())
    except Exception as e:
        logging.exception(e)
        return []


"""
https://www.futurepedia.io/api/getPosts?page=1&sort=New&time=Today
"""


async def get_recent(*args, **kwargs):
    try:
        url = 'https://www.futurepedia.io/recent'
        response = await AsyncHTTPClient().fetch(HTTPRequest(url))
        query = PyQuery(response.body.decode())
        script_content = query('#__NEXT_DATA__').text()
        # return json.loads(script_content)['props']['pageProps']['todayTools']
        for item in json.loads(script_content)['props']['pageProps']['todayTools']:
            yield item
    except Exception as e:
        logging.exception(e)
        # return []


def format_tool(item):
    try:
        ref = item['mainImage'].get('asset', {}).get('_ref', '').split('-')
        image = 'https://cdn.sanity.io/images/u0v1th4q/production/{}-{}.{}?w=640&h=334&auto=format&q=75'.format(ref[1], ref[2], ref[3])
    except Exception as e:
        logging.error(e)
        image = ''

    return '|{} |{} |{} |{} |{} |{} |'.format(
        item['toolName'].replace('|', ' '),
        item['toolShortDescription'].replace('|', ' '),
        '[{}]({})'.format('visit website', item['websiteUrl']),
        '![]({})'.format(image) if image else '',
        item.get('startingPrice', ''),
        # ' '.join(['`{}`'.format(p) for p in item['pricing']]),
        ' '.join(['`{}`'.format(c['categoryName']) for c in item['toolCategories']]),
    )


async def get_all_content(executor):
    page = 1
    res = []
    while page > 0:
        result = await executor(page)
        if len(result) == 0:
            logging.info("no more tools %r", page)
            page = -1
        else:
            page = page + 1

        # test
        # page = -1
        for item in result:
            res.append(item)
            yield item
    json.dump(res, open('tools.json', 'w+'))


async def main():
    print("""# AI-Tool-Insight

AI Tool Insight aims to provide you with the latest AI information and help create infinite possibilities in the future
Daily updates, welcome everyone to come and see what new and interesting AI tools are available every day  
website：https://www.aitoolinsight.com
## 🏠Discord
Join the Discord community and discuss the most cutting-edge information with experts and enthusiasts in the field of AI technology! Here, you can experience the most advanced artificial intelligence technology, communicate with like-minded people, and jointly improve your knowledge level. Whether you are a professional or a hobbyist, welcome to join our community!  
👉 https://discord.gg/xZj9Px7Xvd
## 🔥What's new today
| Name | Description | Website | Screenshot | Pricing | Category |
|---|---|---|---|---|---|""")
    async for item in get_recent():
        # print(item['_id'], item['title'])
        print(format_tool(item))

    # print('--------------')
    print("""
## 📖All AI Tools
| Name | Description | Website | Screenshot | Pricing | Category |
|---|---|---|---|---|---|""")
    async for item in get_all_content(get_tools_by_page):
        # print(item['_id'], item['toolName'])
        print(format_tool(item))


if __name__ == "__main__":
    IOLoop.current().run_sync(main)


