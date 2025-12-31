from discord.ext import commands

class General(commands.Cog):
    """
    通用功能插件，包含基础的系统命令。
    """
    def __init__(self, bot):
        self.bot = bot

    # 这是一个生命周期事件，当插件加载成功时触发
    @commands.Cog.listener()
    async def on_ready(self):
        print(f'General Cog has been loaded!')

    # 一个简单的测试命令
    @commands.command(name="ping")
    async def ping(self, ctx):
        """测试 Bot 的延迟"""
        await ctx.send(f"🏓 Pong! {round(self.bot.latency * 1000)}ms")

# 这是 discord.py 加载插件必须的入口函数
async def setup(bot):
    await bot.add_cog(General(bot))