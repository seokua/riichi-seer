import discord
from discord.ext import commands
import re
import aiohttp
import asyncio
import os
import json
import traceback
from pathlib import Path

class Review(commands.Cog):
    """
    雀魂牌谱分析插件，支持AI 复盘和恶手统计。
    """
    def __init__(self, bot):
        self.bot = bot
        self.pat_majsoul = re.compile(r"\w{6}-\w{8}-\w{4}-\w{4}-\w{4}-\w{12}((\w|-|_)*)")
        
        # 初始化缓存路径
        self.cache_dir = Path(os.getenv("PAIPU_CACHE_DIR", "./cache/paipu"))
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.available_models = []
        self.refresh_config()
        # 异步初始化模型列表
        asyncio.create_task(self.update_models())

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Review Cog has been loaded!')

    def refresh_config(self):
        """加载环境变量"""
        self.tensoul_url = os.getenv("TENSOUL_URL", "").strip()
        self.review_api = os.getenv("REVIEW_BASE_URL", "").strip()
        self.auth = aiohttp.BasicAuth(
            os.getenv("TENSOUL_USR", ""), 
            os.getenv("TENSOUL_PWD", "")
        )

    async def update_models(self):
        """从服务器获取可用模型列表"""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{self.review_api}/models", timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        self.available_models = data.get("models", [])
                        print(f"✅ 已同步可用模型: {[m['model_id'] for m in self.available_models]}")
            except Exception as e:
                print(f"❌ 无法获取模型列表: {e}")

    async def get_paipu_data(self, paipuid: str):
        """获取牌谱逻辑：优先缓存 -> 远程下载"""
        raw_cache_path = self.cache_dir / f"{paipuid} - raw.json"
        
        if raw_cache_path.exists():
            with open(raw_cache_path, 'r', encoding='utf-8') as f:
                return json.load(f), None

        async with aiohttp.ClientSession() as session:
            try:
                url = f"{self.tensoul_url}{paipuid}"
                async with session.get(url, auth=self.auth, timeout=30) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        with open(raw_cache_path, 'w', encoding='utf-8') as f:
                            json.dump(data, f, ensure_ascii=False, indent=4)
                        return data, None
                    return None, f"Tensoul HTTP {resp.status}"
            except Exception as e:
                return None, f"网络请求异常: {type(e).__name__}"

    @commands.hybrid_command(name="models")
    async def list_models(self, ctx):
        """显示当前 AI 后端支持的模型 ID 列表"""
        if not self.available_models:
            await self.update_models()
        
        if not self.available_models:
            return await ctx.send("❌ 无法获取模型列表，请检查后端 API。")
        
        msg = "**当前支持的模型列表：**\n"
        for m in self.available_models:
            msg += f"- `{m['model_id']}` ({m['model_type']})\n"
        await ctx.send(msg)

    @commands.hybrid_command(name="review")
    async def review(self, ctx, paipu_url: str, target_actor:str, model: str):
        """
        提交雀魂牌谱并进行 AI 复盘。
        用法: !review [URL] [Target Actor] [model_id]
        """
        match = self.pat_majsoul.search(paipu_url)
        if not match:
            return await ctx.send("❌ 无效的牌谱链接")
        
        paipuid = match.group()
        # 缓存键名加入 model 区分，防止不同模型共用同一个结果缓存
        review_cache_path = self.cache_dir / f"{paipuid} - {model} - {target_actor} - review.json"

        # 1. 检查结果缓存
        if review_cache_path.exists():
            with open(review_cache_path, 'r', encoding='utf-8') as f:
                return await self.show_result(ctx, json.load(f), paipuid, model, target_actor)

        initial_msg = await ctx.send(f"🔍 正在准备 `{model}` 分析...")

        # 2. 获取牌谱数据
        paipudata, err = await self.get_paipu_data(paipuid)
        if err:
            return await initial_msg.edit(content=f"❌ 获取牌谱失败: {err}")

        # 3. 提交任务
        async with aiohttp.ClientSession() as session:
            try:
                payload = {"player_id": target_actor, "data": paipudata}
                task_id = None
                
                # 提交重试
                for attempt in range(3):
                    try:
                        async with session.post(f"{self.review_api}/review", params={"model": model}, json=payload, timeout=60) as resp:
                            if resp.status == 200:
                                task_id = (await resp.json()).get("task_id")
                                break
                            elif resp.status == 404:
                                return await initial_msg.edit(content=f"❌ 模型 `{model}` 不存在。请使用 `!models` 查看。")
                    except (aiohttp.ServerDisconnectedError, asyncio.TimeoutError):
                        if attempt == 2: raise
                        await asyncio.sleep(2)

                if not task_id:
                    return await initial_msg.edit(content="❌ 任务提交连续失败，服务器可能已断开。")

                # 4. 轮询状态 (加入 working 处理)
                for i in range(60):
                    await asyncio.sleep(2)
                    try:
                        async with session.get(f"{self.review_api}/review", params={"task": task_id}, timeout=10) as s_resp:
                            if s_resp.status != 200: continue
                            
                            res_data = await s_resp.json()
                            status = res_data.get("status")
                            
                            if status == "done":
                                final_data = res_data.get("data", {})
                                with open(review_cache_path, 'w', encoding='utf-8') as f:
                                    json.dump(final_data, f, ensure_ascii=False, indent=4)
                                await initial_msg.delete()
                                return await self.show_result(ctx, final_data, paipuid, model, target_actor)
                            
                            elif status == "working":
                                if i % 5 == 0: # 减少编辑频率，避免 Discord API 速率限制
                                    await initial_msg.edit(content=f"⚙️ 分析进行中... 模型正在努力计算 `{paipuid}`")
                            
                            elif status == "failed":
                                return await initial_msg.edit(content=f"❌ 服务端分析失败: `{res_data.get('error', '未知原因')}`")
                    except Exception:
                        continue

                await initial_msg.edit(content="⏰ 轮询超时，服务器处理过久。")

            except aiohttp.ServerDisconnectedError:
                await initial_msg.edit(content="❌ 服务器已断开连接。这可能是临时网络问题，请稍后重试。")
            except Exception as e:
                traceback.print_exc()
                await initial_msg.edit(content=f"⚠️ 程序异常: `{type(e).__name__}`")

    
    async def parse_review_data(self, data: dict):
        """解析 Review 原始数据并计算详细指标"""
        review_data = data.get("review", {})
        total_reviewed = review_data.get("total_reviewed", 0)
        if total_reviewed == 0:
            return None

        # 指标计算
        rating_val = review_data.get("rating", 0) * 100
        matches_count = review_data.get("total_matches", 0)
        matches_total_ratio = (matches_count / total_reviewed) * 100

        bad_move_up = 0    # 极坏 (prob <= 0.05)
        bad_move_down = 0  # 较坏 (0.05 < prob <= 0.1)

        for kyoku in review_data.get("kyokus", []):
            for entry in kyoku.get("entries", []):
                # 跳过 AI 认为一致的动作
                if entry.get("is_equal"):
                    continue

                actual_action = entry.get("actual")
                for detail in entry.get("details", []):
                    if actual_action == detail.get("action"):
                        prob = detail.get("prob", 1.0)
                        if prob <= 0.05:
                            bad_move_up += 1
                        elif prob <= 0.1:
                            bad_move_down += 1
                        break 

        total_bad_moves = bad_move_up + bad_move_down
        bad_move_percent = (total_bad_moves / total_reviewed) * 100

        # 返回格式化后的字典，方便 Embed 调用
        return {
            "rating": f"{rating_val:.3f}",
            "matches_ratio": f"{matches_count}/{total_reviewed}",
            "matches_percent": f"{matches_total_ratio:.3f}%",
            "bad_move_count": total_bad_moves,
            "bad_move_detail": f"({bad_move_up} 极坏 / {bad_move_down} 较坏)",
            "bad_move_percent": f"{bad_move_percent:.3f}%",
            "review_time": data.get("review_time", "N/A")
        }

    async def show_result(self, ctx, data, paipuid, model, target_actor):
        """美化展示结果"""
        stats = await self.parse_review_data(data)
        if not stats:
            return await ctx.send("❌ 牌谱解析数据异常（total_reviewed 为 0）")

        embed = discord.Embed(title="🀄 Review 分析报告", color=discord.Color.gold())
        embed.set_author(name=f"引擎模型: {model} 目标视角: {target_actor}")
        embed.description = f"牌谱 ID: `{paipuid}`"
        
        # 第一行：核心评分
        embed.add_field(name="Rating 评分", value=f"🏆 **{stats['rating']}**", inline=True)
        embed.add_field(name="AI 一致率", value=f"🎯 {stats['matches_percent']}\n({stats['matches_ratio']})", inline=True)
        embed.add_field(name="分析耗时", value=f"⏱️ {stats['review_time']}s", inline=True)

        # 第二行：恶手统计
        embed.add_field(name="恶手总数 (BadMove)", value=f"🚫 **{stats['bad_move_count']}** 次", inline=True)
        embed.add_field(name="恶手占比", value=f"📈 {stats['bad_move_percent']}", inline=True)
        embed.add_field(name="恶手分布", value=stats['bad_move_detail'], inline=True)

        embed.set_footer(text="提示: 极坏(Prob≤5%), 较坏(5%<Prob≤10%)")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Review(bot))