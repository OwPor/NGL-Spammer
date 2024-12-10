import asyncio
import aiohttp
from typing import List
import time
import random

cf_clearance = open('cf_clearance.txt', 'r').read().strip()

headers = {
    'accept': '*/*',
    'accept-language': 'en-US,en;q=0.9',
    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'origin': 'https://ngl.link',
    'priority': 'u=1, i',
    'Cookie': f'cf_clearance={cf_clearance}',
    'referer': 'https://ngl.link/',
    'sec-ch-ua': '"Microsoft Edge";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0',
    'x-requested-with': 'XMLHttpRequest',
}

def load_questions():
    with open('list.txt', 'r', encoding='utf-8') as file:
        return [line.strip() for line in file if line.strip()]

def load_usernames():
    with open('usernames.txt', 'r', encoding='utf-8') as file:
        return [line.strip() for line in file if line.strip()]

questions = load_questions()

async def make_request(session: aiohttp.ClientSession, url: str, username: str, attempt: int = 0) -> dict:
    try:
        data = {
            'username': username,
            'question': random.choice(questions),
            'deviceId': 'lol-any-uuid-works',
            'gameSlug': '',
            'referrer': '',
        }
        
        headers['referer'] = f'https://ngl.link/{username}'
        
        async with session.post(url, headers=headers, data=data) as response:
            if response.status == 429:
                if attempt < 3:
                    await asyncio.sleep(random.uniform(1, 3))
                    return await make_request(session, url, username, attempt + 1)
                return {"error": "Rate limited", "username": username}
            
            try:
                result = await response.json()
                result["username"] = username
                return result
            except aiohttp.ContentTypeError:
                return {"error": f"Status {response.status}", "text": await response.text(), "username": username}
                
    except Exception as e:
        return {"error": str(e), "username": username}

async def bulk_requests(urls: List[str], usernames: List[str], max_concurrent: int = 10):
    connector = aiohttp.TCPConnector(limit=max_concurrent, ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = []
        for url in urls:
            if len(usernames) == 1:
                tasks.append(make_request(session, url, usernames[0]))
            else:
                tasks.append(make_request(session, url, random.choice(usernames)))
        return await asyncio.gather(*tasks)

async def main():
    print("NGL Spammer - Choose mode:")
    print("1. Single username")
    print("2. Multiple usernames (from usernames.txt)")
    
    mode = input("Enter mode (1 or 2): ")
    
    usernames = []
    if mode == "1":
        username = input("Enter username: ")
        usernames = [username]
    elif mode == "2":
        usernames = load_usernames()
        print(f"Loaded {len(usernames)} usernames from usernames.txt")
    else:
        print("Invalid mode selected")
        return

    num_requests = int(input("Enter number of requests to send: "))
    urls = ["https://ngl.link/api/submit"] * num_requests
    
    start_time = time.time()
    results = await bulk_requests(urls, usernames)
    end_time = time.time()
    
    successful = sum(1 for r in results if "error" not in r)
    print(f"\nCompleted {successful}/{len(results)} requests in {end_time - start_time:.2f} seconds")
    print(f"Failed requests: {len(results) - successful}")
    
    username_stats = {}
    for result in results:
        username = result.get("username")
        if username not in username_stats:
            username_stats[username] = {"success": 0, "failed": 0}
        if "error" not in result:
            username_stats[username]["success"] += 1
        else:
            username_stats[username]["failed"] += 1
    
    print("\nStats per username:")
    for username, stats in username_stats.items():
        print(f"{username}: {stats['success']} successful, {stats['failed']} failed")

if __name__ == "__main__":
    asyncio.run(main())