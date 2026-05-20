from app.services.content.article_image_generator import ArticleImageGenerator
import asyncio

async def test_article_images():
    generator = ArticleImageGenerator(use_ai=True)
    result = await generator.generate_images_for_article(
        title="AI有哪些变现渠道",
        content="AI变现有很多方式，包括内容创作、知识付费、数字人直播等。",
        num_images=2,
        category="科技",
        use_ai=True
    )
    print(f"生成结果: {len(result)}张配图")
    for img in result:
        print(f"第{img['index']}张: {img['file_path']}, 主题: {img['theme']}, AI生成: {img['ai_generated']}")

if __name__ == "__main__":
    asyncio.run(test_article_images())