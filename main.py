import disnake
from disnake.ext import commands
import json, os, datetime

intents = disnake.Intents.all()
intents.message_content = True

bot = commands.Bot(command_prefix="-", intents=intents)

# ================= إعدادات (عدل هنا فقط) =================
APPLY_CHANNEL_ID = 123456789012345678  # قناة التقديم

START_CASH = 1000

VIOLATIONS = [
    ("زره", "500"),
    ("قطع اشاره", "3000"),
    ("تفحيط", "4500"),
]

QUESTIONS = [
    "اسمك:",
    "عمرك:",
    "حسابك روب:",
    "اذكر قانون من السيرفر:",
    "اذكر قانون من الرول:",
    "احلف هذا الحلف:",
]

# =======================================================

BANK_FILE = "bank.json"

# ================= DATABASE =================
def load():
    if os.path.exists(BANK_FILE):
        with open(BANK_FILE, "r") as f:
            return json.load(f)
    return {}

def save(data):
    with open(BANK_FILE, "w") as f:
        json.dump(data, f, indent=4)

def get_user(gid, uid):
    db = load()
    gid, uid = str(gid), str(uid)

    if gid not in db:
        db[gid] = {}

    if uid not in db[gid]:
        db[gid][uid] = {"cash": START_CASH, "bank": 0}
        save(db)

    return db[gid][uid]

# ================= البنك =================
@bot.command(name="رصيدي")
async def balance(ctx):
    user = get_user(ctx.guild.id, ctx.author.id)

    embed = disnake.Embed(title="💰 حسابك البنكي", color=0x2b2d31)
    embed.add_field(name="كاش البنك", value=user["cash"])
    embed.add_field(name="المبلغ بالبنك", value=user["bank"])
    embed.add_field(name="المجموع الكلي", value=user["cash"] + user["bank"])

    embed.set_thumbnail(url=ctx.author.display_avatar.url)
    embed.set_footer(text=datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))

    await ctx.send(embed=embed)

# ================= المخالفات =================
class VSelect(disnake.ui.Select):
    def __init__(self, member, image):
        options = [disnake.SelectOption(label=v[0], description=v[1]) for v in VIOLATIONS]
        super().__init__(placeholder="اختر المخالفة", options=options)
        self.member = member
        self.image = image

    async def callback(self, inter):
        selected = self.values[0]
        fine = next(v[1] for v in VIOLATIONS if v[0] == selected)

        embed = disnake.Embed(title="🚨 تم تسجيل مخالفة", color=0xff0000)
        embed.add_field(name="المخالف", value=self.member.mention)
        embed.add_field(name="المخالفة", value=selected)
        embed.add_field(name="الغرامة", value=fine)

        if self.image:
            embed.set_image(url=self.image)

        await inter.message.delete()
        await inter.channel.send(embed=embed)

class VView(disnake.ui.View):
    def __init__(self, member, image):
        super().__init__()
        self.add_item(VSelect(member, image))

@bot.command(name="مخالفة")
async def violation(ctx, member: disnake.Member):
    image = ctx.message.attachments[0].url if ctx.message.attachments else None

    embed = disnake.Embed(
        title="🚓 تم رصد مخالفة جديدة",
        description="الرجاء اختيار نوع المخالفة",
        color=0x2b2d31
    )

    if image:
        embed.set_image(url=image)

    await ctx.send(embed=embed, view=VView(member, image))

# ================= التقديم =================
class StartApply(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @disnake.ui.button(label="ابدأ التقديم", style=disnake.ButtonStyle.primary)
    async def start(self, button, inter):
        try:
            await inter.author.send(embed=confirm_embed(), view=ConfirmView())
            await inter.response.send_message("📬 تم إرسال الخاص", ephemeral=True)
        except:
            await inter.response.send_message("❌ افتح الخاص", ephemeral=True)

def confirm_embed():
    return disnake.Embed(
        title="❓ تأكيد التقديم",
        description="هل متأكد بدء التقديم؟",
        color=0x2b2d31
    )

class ConfirmView(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @disnake.ui.button(label="قبول", style=disnake.ButtonStyle.green)
    async def yes(self, button, inter):
        await ask_questions(inter)

    @disnake.ui.button(label="رفض", style=disnake.ButtonStyle.red)
    async def no(self, button, inter):
        await inter.response.send_message("❌ تم الإلغاء", ephemeral=True)

async def ask_questions(inter):
    answers = []

    def check(m):
        return m.author == inter.author and isinstance(m.channel, disnake.DMChannel)

    for i, q in enumerate(QUESTIONS):
        embed = disnake.Embed(
            title=f"{i+1}/{len(QUESTIONS)} طلب هوية",
            description=q,
            color=0x2b2d31
        )
        await inter.author.send(embed=embed)

        msg = await bot.wait_for("message", check=check)
        answers.append(msg.content)

    await inter.author.send("📸 أرسل صورة حسابك الآن")
    msg = await bot.wait_for("message", check=check)

    image = msg.attachments[0].url if msg.attachments else None

    ch = bot.get_channel(APPLY_CHANNEL_ID)

    embed = disnake.Embed(title="📨 طلب تقديم", color=0x2b2d31)

    for i, q in enumerate(QUESTIONS):
        embed.add_field(name=q, value=answers[i], inline=False)

    if image:
        embed.set_image(url=image)

    await ch.send(embed=embed, view=Decision(inter.author.id))
    await inter.author.send("✅ تم إرسال طلبك")

class Decision(disnake.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=None)
        self.user_id = user_id

    @disnake.ui.button(label="قبول", style=disnake.ButtonStyle.green)
    async def accept(self, button, inter):
        member = inter.guild.get_member(self.user_id)
        await member.send("🎉 مبروك تم قبولك")
        await inter.response.send_message("تم القبول")

    @disnake.ui.button(label="رفض", style=disnake.ButtonStyle.red)
    async def reject(self, button, inter):
        member = inter.guild.get_member(self.user_id)
        await member.send("❌ تم رفضك، تقدر تعيد التقديم")
        await inter.response.send_message("تم الرفض")

@bot.command(name="تقديم")
async def apply(ctx):
    embed = disnake.Embed(
        title="📋 طلب هوية",
        description="اطلب هوية للعب معنا",
        color=0x2b2d31
    )

    await ctx.send(embed=embed, view=StartApply())

# =================
@bot.event
async def on_ready():
    print("Bot Ready")

bot.run(os.getenv("TOKEN"))
