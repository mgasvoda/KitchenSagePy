import asyncio
from mcp_agent.core.fastagent import FastAgent

# Create the application
fast = FastAgent("FastAgent Example")


# Define the agent
@fast.agent(instruction="You are KitchenSage, a recipe and meal planning assistant. Your goal is to help users optimize their meal planning for nutritional health and minimal food waste.", 
            servers=["kitchen_sage", "fetch"])
async def main():
    # use the --model command line switch or agent arguments to change model
    async with fast.run() as agent:
        await agent()


if __name__ == "__main__":
    asyncio.run(main())
