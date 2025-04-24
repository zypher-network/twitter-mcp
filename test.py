import asyncio
from mcp.client.sse import sse_client
from mcp import ClientSession
import os
from dotenv import load_dotenv

async def main():
    load_dotenv()
    async with sse_client(f'http://127.0.0.1:{os.getenv("PORT")}/mcp') as streams:
        async with ClientSession(*streams) as session:
            await session.initialize()
            res = await session.list_tools()
            print(res)
            result = await session.call_tool("get_user_info", {"user_id": 1})
            print(result)



if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
       loop.run_until_complete(main())
    finally:
        loop.close()