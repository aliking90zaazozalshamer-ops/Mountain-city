import disnake
from disnake.ext import commands
import json, os, datetime

intents = disnake.Intents.all()
intents.message_content = True

bot = commands.Bot(command_prefix="-", intents=intents)

BANK_FILE = "bank.json"
VIOLATION_FILE = "violations.json"

# ================= DATABASE =================
def load(file):
    if os.path.exists(file):
        with open(file, "r") as f:
            try: return json.load(f)
            except: return {}
    return {}

def save(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

# ================= USER =================
def get_user(gid, uid):
    db = load(BANK_FILE)
    gid, uid = str(gid), str(uid)

    db.setdefault(gid, {})
    if uid not in db[gid]:
        db[gid][uid] = {"cash": 1000, "bank": 0}
        save(BANK_FILE, db)

    return db[gid][uid]

def update_user(gid, uid, data):
    db = load(BANK_FILE)
    db[str(gid)][str(uid)] = data
    save(BANK_FILE, db)

# ================= البنك =================
@bot.command(name="رصيدي")
async def balance(ctx):
    user = get_user(ctx.guild.id, ctx.author.id)

    embed = disnake.Embed(title="💰 حسابك البنكي", color=0x2b2d31)

    embed.add_field(name="كاش البنك", value=user["cash"], inline=False)
    embed.add_field(name="المبلغ بالبنك", value=user["bank"], inline=False)
    embed.add_field(name="المجموع الكلي", value=user["cash"] + user["bank"], inline=False)

    embed.set_thumbnail(url=ctx.author.display_avatar.url)
    embed.set_footer(text=datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))

    await ctx.send(embed=embed)

# ================= المخالفات =================
VIOLATIONS = [
    ("زره", "500"),
    ("قطع اشاره", "3000"),
    ("التفحيط", "4500"),
]

class ViolationSelect(disnake.ui.Select):
    def __init__(self, member, image):
        options = [disnake.SelectOption(label=v[0], description=v[1]) for v in VIOLATIONS]
        super().__init__(placeholder="اختر المخالفة...", options=options)
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

class ViolationView(disnake.ui.View):
    def __init__(self, member, image):
        super().__init__()
        self.add_item(ViolationSelect(member, image))

@bot.command(name="مخالفة")
async def violation(ctx, member: disnake.Member):
    image = None
    if ctx.message.attachments:
        image = ctx.message.attachments[0].url

    embed = disnake.Embed(
        title="🚓 تم رصد مخالفة جديدة",
        description="الرجاء اختيار نوع المخالفة",
        color=0x2b2d31
    )

    if image:
        embed.set_image(url=image)

    await ctx.send(embed=embed, view=ViolationView(member, image))

# ================= التقديم (بداية) =================
class ApplyStart(disnake.ui.View):
    def __init__(self):
        super().__init__()

    @disnake.ui.button(label="ابدأ التقديم", style=disnake.ButtonStyle.primary)
    async def start(self, button, inter):
        await inter.author.send("هل متأكد بدء التقديم؟ (اكتب نعم او لا)")

        def check(m):
            return m.author == inter.author and isinstance(m.channel, disnake.DMChannel)

        msg = await bot.wait_for("message", check=check)

        if msg.content.lower() == "نعم":
            await inter.author.send("ابدأ التقديم... (سيتم تطوير باقي النظام)")
        else:
            await inter.author.send("تم إلغاء التقديم")

@bot.command(name="تقديم")
async def apply(ctx):
    embed = disnake.Embed(
        title="📋 طلب هوية",
        description="اطلب هوية للعب معنا",
        color=0x2b2d31
    )

    await ctx.send(embed=embed, view=ApplyStart())

# =================
@bot.event
async def on_ready():
    print("Bot Ready")

bot.run(os.getenv("TOKEN"))
