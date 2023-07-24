from agent import Agent
import asyncio


async def main():
    agent = Agent()

    while True:
        prompt = input(f'> [{agent.messages.get_current_length()}/8192] ')
        reply = await agent.get_gpt_response(prompt)
        print(reply)


if __name__ == '__main__':
    asyncio.run(main())
