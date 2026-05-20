"""
测试LLM智能封面图生成
验证基于大模型的内容分析和封面图生成功能
"""
import asyncio
from app.services.content.llm_cover_generator import get_llm_cover_generator


async def test_llm_cover_generation():
    """测试LLM智能封面图生成"""
    
    print("\n" + "="*80)
    print("🎨 测试LLM智能封面图生成")
    print("="*80)
    
    generator = get_llm_cover_generator()
    
    # 测试用例1: 科技类文章
    print("\n1️⃣  测试1: 科技类文章 - 人工智能发展趋势")
    print("-" * 80)
    
    title1 = "人工智能技术发展趋势分析"
    content1 = """
近年来，人工智能技术取得了长足的进步。机器学习、深度学习、自然语言处理、计算机视觉等技术正在改变我们的生活和工作方式。

人工智能的发展速度令人惊叹。从AlphaGo到GPT系列模型，AI技术在各个领域都取得了突破性进展。特别是在内容创作、智能客服、自动驾驶等领域，AI已经展现出强大的能力。

自然语言处理技术的进步尤为显著。大语言模型能够理解和生成人类语言，这在智能写作、机器翻译、对话系统等场景都有广泛应用。

计算机视觉技术也在快速发展。图像识别、目标检测、视频分析等技术正在各个行业发挥重要作用。从安防监控到医疗影像，从工业自动化到智能交通，计算机视觉的应用场景越来越广泛。

同时，AI技术的伦理和安全问题也日益受到关注。如何在推动技术发展的同时，确保AI的安全性和可控性，是我们需要共同思考的问题。

未来，人工智能将继续快速发展，在更多领域发挥重要作用。我们应该积极拥抱AI技术，同时也要注意其带来的挑战和风险。
"""
    
    result1 = generator.generate_cover_with_llm_analysis(
        title=title1,
        content=content1,
        category="科技"
    )
    
    if result1["status"] == "success":
        print(f"✅ LLM封面生成成功!")
        print(f"   📁 文件路径: {result1['file_path']}")
        print(f"   🎨 视觉风格: {result1.get('design_plan', {}).get('visual_style', 'N/A')}")
        print(f"   🌈 配色方案: {result1.get('design_plan', {}).get('color_scheme', 'N/A')}")
        print(f"   🔑 关键词: {result1.get('design_plan', {}).get('keywords', [])}")
        print(f"   📐 尺寸: {result1['dimensions']}")
        print(f"   💾 大小: {result1['size_kb']} KB")
    else:
        print(f"❌ 生成失败: {result1.get('error')}")
        return False
    
    await asyncio.sleep(2)
    
    # 测试用例2: 财经类文章
    print("\n2️⃣  测试2: 财经类文章 - 投资策略")
    print("-" * 80)
    
    title2 = "2026年股票投资十大策略"
    content2 = """
在当前复杂多变的市场环境下，投资者需要更加谨慎和理性的投资策略。本文总结了2026年最值得关注的十个投资策略。

首先，分散投资仍然是降低风险的核心原则。不要把所有鸡蛋放在一个篮子里，应该在股票、债券、基金等不同资产类别之间进行合理配置。

其次，价值投资理念依然适用。寻找被低估的优质企业，长期持有，等待价值回归。不要被短期市场波动所影响，坚持自己的投资逻辑。

第三，关注新兴行业和科技创新。人工智能、新能源、生物医药等领域蕴含着巨大的投资机会。但也要注意估值过高的风险。

第四，定期定额投资可以有效平滑市场波动。通过定投指数基金或优质个股，可以在长期获得稳定的收益。

第五，保持充足的现金流。在市场出现大幅调整时，有现金才能抓住抄底机会。不要把所有的钱都投入股市。

第六，学习基本的财务分析知识。了解公司的财务报表，判断企业的盈利能力和成长性，避免踩雷。

第七，控制情绪，理性投资。贪婪和恐惧是投资者最大的敌人。制定明确的投资计划并严格执行。

第八，关注宏观经济政策。货币政策、财政政策、产业政策等都会对股市产生重要影响。

第九，适当使用杠杆但要谨慎。杠杆可以放大收益，也会放大亏损。只有在确定性很高的情况下才考虑使用。

第十，持续学习，不断提升自己的投资能力。市场在变化，投资策略也需要与时俱进。
"""
    
    result2 = generator.generate_cover_with_llm_analysis(
        title=title2,
        content=content2,
        category="财经"
    )
    
    if result2["status"] == "success":
        print(f"✅ LLM封面生成成功!")
        print(f"   📁 文件路径: {result2['file_path']}")
        print(f"   🎨 视觉风格: {result2.get('design_plan', {}).get('visual_style', 'N/A')}")
        print(f"   🌈 配色方案: {result2.get('design_plan', {}).get('color_scheme', 'N/A')}")
        print(f"   🔑 关键词: {result2.get('design_plan', {}).get('keywords', [])}")
        print(f"   📐 尺寸: {result2['dimensions']}")
        print(f"   💾 大小: {result2['size_kb']} KB")
    else:
        print(f"❌ 生成失败: {result2.get('error')}")
        return False
    
    await asyncio.sleep(2)
    
    # 测试用例3: 娱乐类文章
    print("\n3️⃣  测试3: 娱乐类文章 - 电影推荐")
    print("-" * 80)
    
    title3 = "2026年必看的十部好莱坞大片"
    content3 = """
2026年好莱坞将迎来一波重磅电影上映潮。从科幻巨制到动作冒险，从动画佳作到悬疑惊悚，总有一部适合你。

首先是备受期待的《阿凡达3》，卡梅隆导演再次带领观众探索潘多拉星球的奥秘。这次的故事将更加深入，特效也将达到新的高度。

其次是漫威的新作《复仇者联盟5》，新一代超级英雄集结，将带来前所未有的视听盛宴。这部电影将开启漫威宇宙的新篇章。

诺兰导演的最新科幻悬疑片也将在今年上映。虽然具体剧情保密，但根据预告片来看，这又将是一部烧脑神作。

迪士尼的动画新作《魔法王国》同样值得期待。精美的画面、动人的故事，适合全家一起观看。

还有多部续集电影，包括《速度与激情11》、《碟中谍8》等，都将为观众带来熟悉的刺激体验。

除了商业大片，今年也有不少文艺佳作值得关注。多位知名导演的作品将在各大电影节亮相。

总的来说，2026年的电影市场非常丰富多彩。无论你是哪种类型的影迷，都能找到自己喜欢的作品。
"""
    
    result3 = generator.generate_cover_with_llm_analysis(
        title=title3,
        content=content3,
        category="娱乐"
    )
    
    if result3["status"] == "success":
        print(f"✅ LLM封面生成成功!")
        print(f"   📁 文件路径: {result3['file_path']}")
        print(f"   🎨 视觉风格: {result3.get('design_plan', {}).get('visual_style', 'N/A')}")
        print(f"   🌈 配色方案: {result3.get('design_plan', {}).get('color_scheme', 'N/A')}")
        print(f"   🔑 关键词: {result3.get('design_plan', {}).get('keywords', [])}")
        print(f"   📐 尺寸: {result3['dimensions']}")
        print(f"   💾 大小: {result3['size_kb']} KB")
    else:
        print(f"❌ 生成失败: {result3.get('error')}")
        return False
    
    print("\n" + "="*80)
    print("✅ LLM智能封面图生成测试完成!")
    print("="*80)
    print("\n💡 提示:")
    print("   - LLM会根据文章内容智能分析并选择合适的视觉风格和配色")
    print("   - 如果LLM分析失败，会自动降级到传统模板或PIL图形生成")
    print("   - 生成的封面图保存在 uploads/llm_covers/ 目录")
    print("="*80)
    
    return True


if __name__ == "__main__":
    asyncio.run(test_llm_cover_generation())
