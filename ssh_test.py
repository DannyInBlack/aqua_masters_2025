import asyncio
import asyncssh

host = '192.168.1.2'
user = "danie"
password = "{+~V'X=5#k/gC5PF"

async def run():
    async with asyncssh.connect(host, username=user, password=password) as conn:
        async with conn.create_process('python -u C:/Users/danie/temp.py') as process:
            async for line in process.stdout:
                print(line.strip())

asyncio.run(run())

