import disnake
from disnake.ext import commands
import os

intents = disnake.Intents.all()
intents.message_content = True
bot = commands.Bot(command_prefix="-", intents=intents)

APPLY_CHANNEL_ID = 1499326967428943902

ROLE_1 = "𝐌𝐂〢🎮〕تـصـريـح لـعـب"
ROLE_2 = "𝐌𝐂〢🪪〕هـويـة مـاوتـن"

QUESTIONS = [
    "اسمك الحقيقي",
    "عمرك",
    "حسابك روب",
    "اختصار حسابك روب (مثال: N7T)",
    "اذكر قانون من قوانين الرول",
    "اذكر قانون من قوانين السيرفر",
]


class ReviewView(disnake.ui.View):
    def __init__(self, applicant_id, guild_id):
        super().__init__(timeout=None)
        self.applicant_id = applicant_id
        self.guild_id = guild_id

    @disnake.ui.button(label="قبول", style=disnake.ButtonStyle.green, emoji="✅")
    async def accept_app(self, button, inter):
        guild = bot.get_guild(self.guild_id)
        member = guild.get_member(self.applicant_id)

        if member:
            role1 = disnake.utils.get(guild.roles, name=ROLE_1)
            role2 = disnake.utils.get(guild.roles, name=ROLE_2)
            if role1:
                await member.add_roles(role1)
            if role2:
                await member.add_roles(role2)

        embed = inter.message.embeds[0]
        embed.color = 0x00ff00
        embed.set_footer(text=f"✅ تم القبول بواسطة {inter.author.display_name}")
        for child in self.children:
            child.disabled = True
        await inter.response.edit_message(embed=embed, view=self)

        try:
            user = await bot.fetch_user(self.applicant_id)
            done = disnake.Embed(
                title="✅ تم قبول طلبك",
                description="مبروك! تم قبول طلب الهوية الخاص بك وتم إعطاؤك الرتبة",
                color=0x00ff00
            )
            await user.send(embed=done)
        except:
            pass

    @disnake.ui.button(label="رفض", style=disnake.ButtonStyle.red, emoji="❌")
    async def reject_app(self, button, inter):
        embed = inter.message.embeds[0]
        embed.color = 0xff0000
        embed.set_footer(text=f"❌ تم الرفض بواسطة {inter.author.display_name}")
        for child in self.children:
            child.disabled = True
        await inter.response.edit_message(embed=embed, view=self)

        try:
            user = await bot.fetch_user(self.applicant_id)
            done = disnake.Embed(
                title="❌ تم رفض طلبك",
                description="نأسف، تم رفض طلب الهوية الخاص بك",
                color=0xff0000
            )
            await user.send(embed=done)
        except:
            pass


class ApplyView(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @disnake.ui.button(label="ابدأ التقديم", style=disnake.ButtonStyle.primary)
    async def start(self, button, inter):
        try:
            embed = disnake.Embed(
                title="📝 طلب هوية",
                description="اضغط **قبول** لبدء التقديم أو **رفض** للإلغاء",
                color=0x2b2d31
            )
            await inter.author.send(embed=embed, view=ConfirmView(inter.guild.id))
            await inter.response.send_message("📬 تم إرسال الخاص", ephemeral=True)
        except:
            await inter.response.send_message("❌ افتح الخاص", ephemeral=True)


class ConfirmView(disnake.ui.View):
    def __init__(self, guild_id):
        super().__init__(timeout=None)
        self.guild_id = guild_id

    @disnake.ui.button(label="قبول", style=disnake.ButtonStyle.green)
    async def accept(self, button, inter):
        await inter.message.delete()
        total = len(QUESTIONS) + 1
        answers = []

        def check(m):
            return m.author == inter.author and isinstance(m.channel, disnake.DMChannel)

        for i, q in enumerate(QUESTIONS):
            await inter.author.send(embed=disnake.Embed(
                title="📝 طلب هوية",
                description=f"**السؤال {i+1}/{total}**\n\n{q}",
                color=0x2b2d31
            ))
            msg = await bot.wait_for("message", check=check)
            answers.append(msg.content)
            ack = disnake.Embed(title="✅ تم استلام إجابتك", color=0x00ff00)
            ack.add_field(name=q, value=msg.content, inline=False)
            await inter.author.send(embed=ack)

        await inter.author.send(embed=disnake.Embed(
            title="📝 طلب هوية",
            description=f"**السؤال {total}/{total}**\n\nصورة حسابك",
            color=0x2b2d31
        ))

        def check_image(m):
            return m.author == inter.author and isinstance(m.channel, disnake.DMChannel) and m.attachments

        msg = await bot.wait_for("message", check=check_image)
        image = msg.attachments[0].url
        ack = disnake.Embed(title="✅ تم استلام صورة حسابك", color=0x00ff00)
        ack.set_image(url=image)
        await inter.author.send(embed=ack)

        ch = bot.get_channel(APPLY_CHANNEL_ID)
        embed = disnake.Embed(
            title="📨 طلب هوية جديد",
            description=f"من: {inter.author.mention}",
            color=0x2b2d31
        )
        for i, q in enumerate(QUESTIONS):
            embed.add_field(name=q, value=answers[i], inline=False)
        embed.set_image(url=image)

        if ch:
            await ch.send(embed=embed, view=ReviewView(inter.author.id, self.guild_id))

        await inter.author.send("✅ تم إرسال تقديمك للإدارة")

    @disnake.ui.button(label="رفض", style=disnake.ButtonStyle.red)
    async def reject(self, button, inter):
        await inter.message.delete()
        await inter.author.send("❌ تم إلغاء التقديم")


@bot.command(name="تقديم")
async def apply(ctx):
    if ctx.author.id != ctx.guild.owner_id:
        await ctx.send(embed=disnake.Embed(title="❌ خطأ", description="هذا الأمر للأونر فقط", color=0xff0000))
        return
    embed = disnake.Embed(
        title="📝 طلب هوية",
        description="اطلب هوية للعب معنا\nاضغط على الزر تحت لبدء التقديم",
        color=0x2b2d31
    )
    await ctx.send(embed=embed, view=ApplyView())


@bot.event
async def on_ready():
    print(f"Bot Ready - Logged in as {bot.user}")


bot.run(os.getenv("TOKEN"))
