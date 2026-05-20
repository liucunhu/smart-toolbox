from app.services.content.copywriting_generation import CopywritingGenerator
import asyncio

async def test_copywriting():
    generator = CopywritingGenerator()
    result = generator.generate_script('toutiao', 'AI有哪些变现渠道')
    print("生成结果:")
    print(result)

if __name__ == "__main__":
    asyncio.run(test_copywriting())