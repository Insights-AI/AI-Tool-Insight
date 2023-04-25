import asyncio
import nest_asyncio
import json
import logging
from io import StringIO
from datetime import datetime
from urllib.parse import quote
from urllib3.filepost import encode_multipart_formdata
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
from tornado.options import options, define, parse_command_line
from pyquery import PyQuery


nest_asyncio.apply()


class FeishuAPI(object):

    def __init__(
        self,
        app_token='E83SbLGvFagFJesF1vRcSKfsnzf',
        table_id='tblSjKC6GgcchXcg',
        view_id='vewmW9GTTf',
    ):
        self.app_token = app_token
        self.table_id = table_id
        self.view_id = view_id
        self.view_id = view_id

    @property
    def access_token(self):
        if not hasattr(self, '_token'):
            loop = asyncio.get_event_loop()
            access_token = loop.run_until_complete(self.get_access_token())
            setattr(self, '_token', access_token)
        return getattr(self, '_token')

    async def get_access_token(self):
        # https://open.feishu.cn/document/ukTMukTMukTM/ukDNz4SO0MjL5QzM/auth-v3/auth/app_access_token_internal
        try:
            url = 'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal'
            response = await AsyncHTTPClient().fetch(HTTPRequest(
                url,
                method='POST',
                headers={'Content-Type': 'application/json; charset=utf-8'},
                body=json.dumps({
                    "app_id": options.APP_ID,
                    "app_secret": options.APP_SECRET
                })
            ))
            return json.loads(response.body.decode())['tenant_access_token']
        except Exception as e:
            logging.exception(e)
            return None

    async def get_tags(self):
        # https://www.futurepedia.io/api/tags
        try:
            response = await AsyncHTTPClient().fetch('https://www.futurepedia.io/api/tags')
            return json.loads(response.body.decode())
        except Exception as e:
            logging.exception(e)

    async def save_tags(self, tags):
        # https://open.feishu.cn/open-apis/bitable/v1/apps/:app_token/tables/:table_id/fields/:field_id
        try:
            url = 'https://open.feishu.cn/open-apis/bitable/v1/apps/{}/tables/{}/fields'.format(
                self.app_token, self.table_id
            )
            response = await AsyncHTTPClient().fetch(HTTPRequest(
                url,
                method='POST',
                headers={
                    'Authorization': 'Bearer {}'.format(self.access_token),
                    'Content-Type': 'application/json; charset=utf-8'
                },
                body=json.dumps({
                    "field_name": 'Category1',
                    "type": 4,
                    "property": {
                        "options": [{'name': tag['categoryName']} for tag in tags]
                    }
                })
            ))
            print(response.body)
            return json.loads(response.body.decode())
        except Exception as e:
            logging.exception(e)
            logging.error(e.response)
            logging.error(e.response.body)
            return None

    async def get_tools_by_sheet(self):
        page_token = ''
        while True:
            items, has_more, page_token = await self.get_tools_by_sheet_and_page(page_token=page_token)
            for item in items:
                yield item
            if not has_more:
                break

    async def get_latest_tool(self):
        items, has_more, page_token = await self.get_tools_by_sheet_and_page(page_token='')
        return items[0] if len(items) > 0 else None

    async def get_tools_by_sheet_and_page(
        self,
        page_token='',
        page_size=100,
        sort='%5B%22Created%20DESC%22%5D'
    ):
    
        # https://egqz2y6eul.feishu.cn/base/E83SbLGvFagFJesF1vRcSKfsnzf?table=tblSjKC6GgcchXcg&view=vewmW9GTTf
        # https://open.feishu.cn/open-apis/bitable/v1/apps/:app_token/tables/:table_id/records
        try:
            url = 'https://open.feishu.cn/open-apis/bitable/v1/apps/{}/tables/{}/records?page_token={}&page_size={}&sort={}'.format(
                self.app_token, self.table_id,
                page_token, page_size,
                sort,
            )
            request = HTTPRequest(
                url,
                method='GET',
                headers={
                    'Authorization': 'Bearer {}'.format(self.access_token),
                },
            )
            print(request, request.headers, request.url)
            response = await AsyncHTTPClient().fetch(request)
            print(response.body)
            result = json.loads(response.body.decode())['data']
            # items, has_more, page_token
            return result.get('items', []) or [], result['has_more'], result.get('page_token', '')
        except Exception as e:
            logging.exception(e)
            return [], False, ''

    async def add_record(self, table_id=None, **fields):
        try:
            url = 'https://open.feishu.cn/open-apis/bitable/v1/apps/{}/tables/{}/records'.format(
                self.app_token, table_id or self.table_id,
            )
            request = HTTPRequest(
                url,
                method='POST',
                headers={
                    'Authorization': 'Bearer {}'.format(self.access_token),
                    'Content-Type': 'application/json; charset=utf-8',
                },
                body=json.dumps({'fields': fields}, ensure_ascii=True),
            )
            print(request, request.headers, request.url, request.body)
            response = await AsyncHTTPClient().fetch(request)
            print(response.body)
            # items, has_more, page_token
        except Exception as e:
            logging.exception(e)

    async def delete(self):
        # https://open.feishu.cn/open-apis/bitable/v1/apps/:app_token/tables/:table_id/records/batch_delete
        tools = await gather(self.get_tools_by_sheet())
        # print(tools)
        try:
            url = 'https://open.feishu.cn/open-apis/bitable/v1/apps/{}/tables/{}/records/batch_delete'.format(
                self.app_token, self.table_id,
            )
            request = HTTPRequest(
                url,
                method='POST',
                headers={
                    'Authorization': 'Bearer {}'.format(self.access_token),
                    'Content-Type': 'application/json; charset=utf-8',
                },
                body=json.dumps({'records': [t['record_id'] for t in tools]}),
            )
            print(request, request.headers, request.url, request.body)
            response = await AsyncHTTPClient().fetch(request)
            print(response.body)
            # items, has_more, page_token
        except Exception as e:
            logging.exception(e)

    async def translate(self, text, source_language='en', target_language='zh'):
        try:
            url = 'https://open.feishu.cn/open-apis/translation/v1/text/translate'
            request = HTTPRequest(
                url,
                method='POST',
                headers={
                    'Authorization': 'Bearer {}'.format(self.access_token),
                    'Content-Type': 'application/json; charset=utf-8',
                },
                body=json.dumps({
                    'source_language': source_language,
                    'text': text,
                    'target_language': target_language,
                }),
            )
            response = await AsyncHTTPClient().fetch(request)
            return json.loads(response.body.decode())['data']['text']
        except Exception as e:
            logging.exception(e)
            # logging.error(e.response.body)
            return text

    async def get_file_token(self, url, file_name):
        # return file_token
        try:
            response = await AsyncHTTPClient().fetch(url)
            file_content = response.body
            encoded, content_type = encode_multipart_formdata([
                ('size', len(file_content)),
                ('file', (quote(file_name), file_content)),
                ('file_name', quote(file_name)),
                ('parent_type', 'bitable_image'),
                # ('parent_node', 'fldcnujQvWiBepfNQnWGOxUi22Q'),
                ('parent_node', self.app_token),
            ])
            url = 'https://open.feishu.cn/open-apis/drive/v1/medias/upload_all'
            request = HTTPRequest(
                url,
                method='POST',
                headers={
                    'Authorization': 'Bearer {}'.format(self.access_token),
                    'Content-Type': content_type,
                },
                body=encoded,
            )
            response = await AsyncHTTPClient().fetch(request)
            print(response.body)
            return json.loads(response.body.decode())['data']['file_token']
        except Exception as e:
            logging.exception(e)
            return None


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

    price = item.get('startingPrice', '')
    return '|{} |{} |{} |{} |{} |{} |'.format(
        item['toolName'].replace('|', ' '),
        item['toolShortDescription'].replace('|', ' '),
        '[{}]({})'.format('visit website', item['websiteUrl']),
        '![]({})'.format(image) if image else '',
        '$ {}'.format(price) if price else '',
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


async def gather(ai):
    res = []
    async for i in ai:
        res.append(i)
    return res


api = FeishuAPI()


async def save_tool_item(api, item):
    try:
        ref = item['mainImage'].get('asset', {}).get('_ref', '').split('-')
        image = 'https://cdn.sanity.io/images/u0v1th4q/production/{}-{}.{}?w=640&h=334&auto=format&q=75'.format(ref[1], ref[2], ref[3])
        file_token = await api.get_file_token(image, item['toolName'] + '.png')
    except Exception as e:
        logging.error(e)
        image = ''
        file_token = None

    # print(item)
    price = item.get('startingPrice', '')
    description = await api.translate(item['toolShortDescription'])
    try:
        publishedAt = int(datetime.strptime(item.get('publishedAt')[:10], '%Y-%m-%d').timestamp())*1000
    except Exception as e:
        publishedAt = item.get('publishedAt_timestamp', 0)
        logging.error(e)

    await api.add_record(**{
        'ID': item['_id'],
        '产品 & 服务': item['toolName'],
        '简介': description,
        'Description': item['toolShortDescription'],
        '网址': {'link': item['websiteUrl'], 'text': item['websiteUrl']},
        '价格': '$ {}'.format(price) if price else '',
        '发布时间':  publishedAt,
        '分类': [c['categoryName'] for c in item['toolCategories']],
        '封面': [{'file_token': file_token}] if file_token else None,
        'Image': image,
    })


async def crawler_recent_tools(api):
    await api.delete()
    async for item in get_recent():
        await save_tool_item(api, item)


async def crawler_all_tools(api):
    tools = await gather(api.get_tools_by_sheet())
    # print(tools)
    tools_id = [t['fields']['ID'] for t in tools]
    async for item in get_all_content(get_tools_by_page):
        if item['_id'] in tools_id:
            print('latest_id', item['_id'], item['toolName'])
            continue
        print(item['toolName'])
        await save_tool_item(api, item)


async def crawler_new_tools(api):
    latest = await api.get_latest_tool()
    print(latest)
    latest_id = latest['fields']['ID'] if latest else None
    async for item in get_all_content(get_tools_by_page):
        if item['_id'] == latest_id:
            print('latest_id', latest_id, item['toolName'])
            break
        print(item['toolName'])
        await save_tool_item(api, item)


async def main():
    api = FeishuAPI(app_token='E83SbLGvFagFJesF1vRcSKfsnzf', table_id='tblSjKC6GgcchXcg')
    # await api.save_tags(await api.get_tags())
    await crawler_recent_tools(api)
    api = FeishuAPI(app_token='E83SbLGvFagFJesF1vRcSKfsnzf', table_id='tblPVxGrtlpsroVU')
    # await api.save_tags(await api.get_tags())
    # await crawler_all_tools(api)
    await crawler_new_tools(api)
    # tools = await gather(api.get_tools_by_sheet())
    # print(tools)
    # text = await api.translate('AI-Powered Cloud based Platform that \u200b\u200b Simplifies Brand Control')
    # print(text)
    # file_token = await api.get_file_token(
    #     'https://cdn.sanity.io/images/u0v1th4q/production/870ddad556846f339120b43a724183a3c6795f94-1866x811.png?w=640&h=334&auto=format&q=75',
    #     'brndaddo.png',
    # )
    # print(file_token)
    # await FeishuAPI().add_record(Name='test', Website={'link': 'https://baidu.com', 'text': 'view website'})
    # tools = await gather(FeishuAPI().get_tools_by_sheet())
    # print(tools)
    return
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
    # async for item in get_all_content(get_tools_by_page):
    async for item in api.get_tools_by_sheet():
        # print(item['_id'], item['toolName'])
        print(format_tool(item))


if __name__ == "__main__":
    define('APP_ID', default='')
    define('APP_SECRET', default='')
    parse_command_line()
    asyncio.run(main())


