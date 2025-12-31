import discord
import os
import asyncio
import logging
from discord.ext import commands
from dotenv import load_dotenv

# Watchdog 相关
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# 初始化环境
load_dotenv()
logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv('DISCORD_TOKEN')
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

@bot.command(name="help")
async def custom_help(ctx, cog_name: str = None):
    """
    动态帮助命令
    用法: !help (显示插件列表) 或 !help <插件名> (显示插件下的命令)
    """
    if cog_name is None:
        # --- 1. 显示插件列表 ---
        embed = discord.Embed(
            title="🤖 机器人插件列表",
            description=f"使用 `!help <插件名>` 查看具体命令详情\n当前前缀: `{bot.command_prefix}`",
            color=discord.Color.blue()
        )
        
        for name, cog in bot.cogs.items():
            # 过滤掉没有命令的插件
            if cog.get_commands():
                embed.add_field(
                    name=f"📦 {name}", 
                    value=cog.description or "无描述", 
                    inline=True
                )
        
        return await ctx.send(embed=embed)

    # --- 2. 显示特定插件下的所有命令 ---
    # 统一转换大小写方便匹配
    target_cog = None
    for name in bot.cogs:
        if name.lower() == cog_name.lower():
            target_cog = bot.get_cog(name)
            break

    if not target_cog:
        return await ctx.send(f"❌ 未找到插件: `{cog_name}`")

    embed = discord.Embed(
        title=f"📦 {target_cog.qualified_name} 插件命令",
        color=discord.Color.green()
    )
    
    for command in target_cog.get_commands():
        # 排除隐藏命令
        if command.hidden: continue
        
        # 获取命令说明（即函数下方的引号内容）
        desc = command.help or "暂无说明"
        embed.add_field(
            name=f"`!{command.name}`", 
            value=desc, 
            inline=False
        )

    await ctx.send(embed=embed)

class HotReloadHandler(FileSystemEventHandler):
    def __init__(self, bot):
        self.bot = bot

    def on_modified(self, event):
        filename = os.path.basename(event.src_path)
        
        # 1. 如果修改了 .env 文件
        if filename == ".env":
            print("⚙️ 检测到 .env 变动，正在刷新环境变量...")
            load_dotenv(override=True)
            # 环境变量变了通常需要重载所有 Cog 才能生效
            asyncio.run_coroutine_threadsafe(self.reload_all_cogs(), self.bot.loop)
            return

        # 2. 如果修改了 cogs 文件夹下的 .py 文件
        if event.src_path.endswith(".py") and "cogs" in event.src_path:
            if "__pycache__" in event.src_path: return
            
            ext_name = f"cogs.{filename[:-3]}"
            print(f"📝 检测到插件变动: {filename}，正在重载...")
            asyncio.run_coroutine_threadsafe(self.reload_cog(ext_name), self.bot.loop)

    async def reload_cog(self, name):
        try:
            await self.bot.reload_extension(name)
            print(f"✅ 插件重载成功: {name}")
        except Exception as e:
            print(f"❌ 插件重载失败: {name}\n{e}")

    async def reload_all_cogs(self):
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                await self.reload_cog(f"cogs.{filename[:-3]}")

async def load_extensions():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')

@bot.event
async def on_ready():
    print(f'🚀 登录成功: {bot.user}')
    
    # --- 关键：同步斜杠命令 ---
    try:
        # sync() 会同步全局命令。如果你只想在特定服务器测试，
        # 可以传入 guild=discord.Object(id=...) 速度会快很多
        synced = await bot.tree.sync()
        print(f"✅ 已同步 {len(synced)} 个斜杠命令")
    except Exception as e:
        print(f"❌ 同步斜杠命令失败: {e}")
        
    print('👀 文件监听器已启动...')

async def main():
    async with bot:
        await load_extensions()
        
        # 启动监听 (监听根目录以获取 .env，监听 cogs 目录获取插件)
        observer = Observer()
        handler = HotReloadHandler(bot)
        # 监听根目录，recursive=True 也会包含 cogs 文件夹
        observer.schedule(handler, path=".", recursive=True)
        observer.start()
        
        try:
            await bot.start(TOKEN)
        finally:
            observer.stop()
            observer.join()

if __name__ == '__main__':
    asyncio.run(main())