import disnake
from disnake.ext import commands, tasks
import json, os, datetime

intents = disnake.Intents.all()
intents.message_content = True
bot = commands.Bot(command_prefix="-", intents=intents)

BANK_FILE = "bank.json"
SALARY_MARKER = ".last_salary"
APPLY_CHANNEL_ID = 1499326967428943902
SALARY_AMOUNT = 50000
LOAN_MAX = 5000
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

VIOLATIONS = [
    ("زره", "500"),
    ("قطع اشاره", "3000"),
    ("تفحيط", "4500"),
]

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
        db[gid][uid] = {"cash": 1000, "bank": 0, "loan": 0}
        save(db)
    if "loan" not in db[gid][uid]:
        db[gid][uid]["loan"] = 0
        save(db)
    return db[gid][uid]

def set_user(gid, uid, data):
    db = load()
    gid, uid = str(gid), str(uid)
    if gid not in db:
        db[gid] = {}
    db[gid][uid] = data
    save(db)

def err_embed(msg):
    return disnake.Embed(title="❌ خطأ", description=msg, color=0xff0000)

def ok_embed(title, color=0x00ff00):
    return disnake.Embed(title=title, color=color)

def next_saturday_11pm():
    now = datetime.datetime.now()
    days_ahead = (5 - now.weekday()) % 7
    target = now.replace(hour=23, minute=0, second=0, microsecond=0) + datetime.timedelta(days=days_ahead)
    if target <= now:
        target += datetime.timedelta(days=7)
    return target

def distribute_salaries():
    db = load()
    for gid in db:
        for uid in db[gid]:
            db[gid][uid]["cash"] += SALARY_AMOUNT
    save(db)


# ── البنك ──────────────────────────────────────────────

@bot.command(name="رصيدي")
async def balance(ctx):
    user = get_user(ctx.guild.id, ctx.author.id)
    embed = disnake.Embed(title="💰 حسابك البنكي", color=0x2b2d31)
    embed.add_field(name="كاش", value=user["cash"])
    embed.add_field(name="بنك", value=user["bank"])
    embed.add_field(name="المجموع", value=user["cash"] + user["bank"])
    embed.set_thumbnail(url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)

@bot.command(name="رصيد")
async def balance_other(ctx, member: disnake.Member):
    user = get_user(ctx.guild.id, member.id)
    embed = disnake.Embed(title=f"💰 رصيد {member.display_name}", color=0x2b2d31)
    embed.add_field(name="كاش", value=user["cash"])
    embed.add_field(name="بنك", value=user["bank"])
    embed.add_field(name="المجموع", value=user["cash"] + user["bank"])
    embed.set_thumbnail(url=member.display_avatar.url)
    await ctx.send(embed=embed)

@bot.command(name="إيداع")
async def deposit(ctx, amount: int):
    if amount <= 0:
        return await ctx.send(embed=err_embed("المبلغ لازم أكبر من صفر"))
    user = get_user(ctx.guild.id, ctx.author.id)
    if user["cash"] < amount:
        return await ctx.send(embed=err_embed(f"كاشك الحالي: {user['cash']}"))
    user["cash"] -= amount
    user["bank"] += amount
    set_user(ctx.guild.id, ctx.author.id, user)
    embed = ok_embed("✅ تم الإيداع")
    embed.add_field(name="المبلغ", value=amount)
    embed.add_field(name="كاش", value=user["cash"])
    embed.add_field(name="بنك", value=user["bank"])
    await ctx.send(embed=embed)

@bot.command(name="سحب")
async def withdraw(ctx, amount: int):
    if amount <= 0:
        return await ctx.send(embed=err_embed("المبلغ لازم أكبر من صفر"))
    user = get_user(ctx.guild.id, ctx.author.id)
    if user["bank"] < amount:
        return await ctx.send(embed=err_embed(f"رصيد البنك: {user['bank']}"))
    user["bank"] -= amount
    user["cash"] += amount
    set_user(ctx.guild.id, ctx.author.id, user)
    embed = ok_embed("✅ تم السحب")
    embed.add_field(name="المبلغ", value=amount)
    embed.add_field(name="كاش", value=user["cash"])
    embed.add_field(name="بنك", value=user["bank"])
    await ctx.send(embed=embed)

@bot.command(name="تحويل")
async def transfer(ctx, member: disnake.Member, amount: int):
    if member.id == ctx.author.id:
        return await ctx.send(embed=err_embed("ما تقدر تحول لنفسك"))
    if member.bot:
        return await ctx.send(embed=err_embed("ما تقدر تحول لبوت"))
    if amount <= 0:
        return await ctx.send(embed=err_embed("المبلغ لازم أكبر من صفر"))
    sender = get_user(ctx.guild.id, ctx.author.id)
    if sender["cash"] < amount:
        return await ctx.send(embed=err_embed(f"كاشك الحالي: {sender['cash']}"))
    receiver = get_user(ctx.guild.id, member.id)
    sender["cash"] -= amount
    receiver["cash"] += amount
    set_user(ctx.guild.id, ctx.author.id, sender)
    set_user(ctx.guild.id, member.id, receiver)
    embed = ok_embed("✅ تم التحويل")
    embed.add_field(name="المرسل", value=ctx.author.mention)
    embed.add_field(name="المستلم", value=member.mention)
    embed.add_field(name="المبلغ", value=amount)
    await ctx.send(embed=embed)

@bot.command(name="قرض")
async def loan(ctx, amount: int):
    if amount <= 0:
        return await ctx.send(embed=err_embed("المبلغ لازم أكبر من صفر"))
    if amount > LOAN_MAX:
        return await ctx.send(embed=err_embed(f"الحد الأقصى: {LOAN_MAX}"))
    user = get_user(ctx.guild.id, ctx.author.id)
    if user["loan"] > 0:
        return await ctx.send(embed=err_embed(f"عندك قرض قديم: {user['loan']} — سدده أول"))
    user["cash"] += amount
    user["loan"] += amount
    set_user(ctx.guild.id, ctx.author.id, user)
    embed = disnake.Embed(title="🏦 تمت الموافقة على القرض", color=0x00ff00)
    embed.add_field(name="المستفيد", value=ctx.author.mention)
    embed.add_field(name="مبلغ القرض", value=amount)
    embed.add_field(name="المستحق", value=user["loan"])
    await ctx.send(embed=embed)

@bot.command(name="تسديد-قرض")
async def repay_loan(ctx, amount: int):
    if amount <= 0:
        return await ctx.send(embed=err_embed("المبلغ لازم أكبر من صفر"))
    user = get_user(ctx.guild.id, ctx.author.id)
    if user["loan"] == 0:
        return await ctx.send(embed=err_embed("ما عندك قرض"))
    if user["cash"] < amount:
        return await ctx.send(embed=err_embed(f"كاشك: {user['cash']}"))
    pay = min(amount, user["loan"])
    user["cash"] -= pay
    user["loan"] -= pay
    set_user(ctx.guild.id, ctx.author.id, user)
    embed = disnake.Embed(title="✅ تم تسديد القرض", color=0x00ff00)
    embed.add_field(name="المسدَّد", value=pay)
    embed.add_field(name="المتبقي", value=user["loan"])
    embed.add_field(name="كاشك الحالي", value=user["cash"])
    await ctx.send(embed=embed)


# ── الرواتب ────────────────────────────────────────────

@bot.command(name="الرواتب")
async def salaries(ctx):
    next_time = next_saturday_11pm()
    embed = disnake.Embed(title="💵 موعد صرف الرواتب", color=0x2b2d31)
    embed.add_field(name="📅 الموعد القادم", value=next_time.strftime("%Y-%m-%d الساعة %H:%M"), inline=False)
    embed.add_field(name="🔁 الجدول", value="كل سبت 11 مساءً تلقائياً", inline=False)
    embed.add_field(name="💰 المبلغ", value=f"{SALARY_AMOUNT} كاش لكل مستخدم", inline=False)
    await ctx.send(embed=embed)

@tasks.loop(minutes=15)
async def auto_salary():
    now = datetime.datetime.now()
    if now.weekday() == 5 and now.hour == 23:
        today = now.strftime("%Y-%m-%d")
        if os.path.exists(SALARY_MARKER):
            with open(SALARY_MARKER) as f:
                if f.read().strip() == today:
                    return
        distribute_salaries()
        with open(SALARY_MARKER, "w") as f:
            f.write(today)

@auto_salary.before_loop
async def before_auto_salary():
    await bot.wait_until_ready()


# ── المخالفات ──────────────────────────────────────────

class VSelect(disnake.ui.Select):
    def __init__(self, member, image):
        options = [disnake.SelectOption(label=v[0], description=f"غرامة: {v[1]}") for v in VIOLATIONS]
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

class PayVSelect(disnake.ui.Select):
    def __init__(self, gid):
        self.gid = gid
        options = [disnake.SelectOption(label=v[0], description=f"الغرامة: {v[1]} كاش") for v in VIOLATIONS]
        super().__init__(placeholder="اختر المخالفة اللي تبي تسددها", options=options)

    async def callback(self, inter):
        selected = self.values[0]
        fine = int(next(v[1] for v in VIOLATIONS if v[0] == selected))
        user = get_user(self.gid, inter.author.id)
        if user["cash"] < fine:
            return await inter.response.edit_message(embed=err_embed(f"كاشك {user['cash']} والغرامة {fine}"), view=None)
        user["cash"] -= fine
        set_user(self.gid, inter.author.id, user)
        embed = disnake.Embed(title="✅ تم تسديد المخالفة", color=0x00ff00)
        embed.add_field(name="المخالفة", value=selected)
        embed.add_field(name="المدفوع", value=f"{fine} كاش")
        embed.add_field(name="كاشك المتبقي", value=user["cash"])
        await inter.response.edit_message(embed=embed, view=None)

class PayVView(disnake.ui.View):
    def __init__(self, gid):
        super().__init__()
        self.add_item(PayVSelect(gid))

@bot.command(name="مخالفة")
async def violation(ctx, member: disnake.Member):
    image = ctx.message.attachments[0].url if ctx.message.attachments else None
    embed = disnake.Embed(title="🚓 مخالفة جديدة", description="اختر نوع المخالفة", color=0x2b2d31)
    if image:
        embed.set_image(url=image)
    await ctx.send(embed=embed, view=VView(member, image))

@bot.command(name="تسديد")
async def pay_violation(ctx):
    embed = disnake.Embed(title="💳 تسديد مخالفة", description="اختر المخالفة من القائمة", color=0x2b2d31)
    await ctx.send(embed=embed, view=PayVView(ctx.guild.id))


# ── التقديم ────────────────────────────────────────────

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
            r1 = disnake.utils.get(guild.roles, name=ROLE_1)
            r2 = disnake.utils.get(guild.roles, name=ROLE_2)
            if r1: await member.add_roles(r1)
            if r2: await member.add_roles(r2)
        embed = inter.message.embeds[0]
        embed.color = 0x00ff00
        embed.set_footer(text=f"✅ قبله {inter.author.display_name}")
        for child in self.children:
            child.disabled = True
        await inter.response.edit_message(embed=embed, view=self)
        try:
            user = await bot.fetch_user(self.applicant_id)
            await user.send(embed=disnake.Embed(title="✅ تم قبول طلبك", description="مبروك! تم إعطاؤك الرتبة", color=0x00ff00))
        except:
            pass

    @disnake.ui.button(label="رفض", style=disnake.ButtonStyle.red, emoji="❌")
    async def reject_app(self, button, inter):
        embed = inter.message.embeds[0]
        embed.color = 0xff0000
        embed.set_footer(text=f"❌ رفضه {inter.author.display_name}")
        for child in self.children:
            child.disabled = True
        await inter.response.edit_message(embed=embed, view=self)
        try:
            user = await bot.fetch_user(self.applicant_id)
            await user.send(embed=disnake.Embed(title="❌ تم رفض طلبك", description="نأسف، تم رفض طلبك", color=0xff0000))
        except:
            pass

class ApplyView(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @disnake.ui.button(label="ابدأ التقديم", style=disnake.ButtonStyle.primary)
    async def start(self, button, inter):
        try:
            embed = disnake.Embed(title="📝 طلب هوية", description="اضغط **قبول** للبدء أو **رفض** للإلغاء", color=0x2b2d31)
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
            await inter.author.send(embed=disnake.Embed(title="📝 طلب هوية", description=f"**السؤال {i+1}/{total}**\n\n{q}", color=0x2b2d31))
            msg = await bot.wait_for("message", check=check)
            answers.append(msg.content)
            ack = disnake.Embed(title="✅ تم استلام إجابتك", color=0x00ff00)
            ack.add_field(name=q, value=msg.content, inline=False)
            await inter.author.send(embed=ack)
        await inter.author.send(embed=disnake.Embed(title="📝 طلب هوية", description=f"**السؤال {total}/{total}**\n\nصورة حسابك", color=0x2b2d31))
        def check_image(m):
            return m.author == inter.author and isinstance(m.channel, disnake.DMChannel) and m.attachments
        msg = await bot.wait_for("message", check=check_image)
        image = msg.attachments[0].url
        ack = disnake.Embed(title="✅ تم استلام صورة حسابك", color=0x00ff00)
        ack.set_image(url=image)
        await inter.author.send(embed=ack)
        ch = bot.get_channel(APPLY_CHANNEL_ID)
        embed = disnake.Embed(title="📨 طلب هوية جديد", description=f"من: {inter.author.mention}", color=0x2b2d31)
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
        return await ctx.send(embed=err_embed("هذا الأمر للأونر فقط"))
    embed = disnake.Embed(title="📝 طلب هوية", description="اطلب هوية للعب معنا\nاضغط على الزر تحت لبدء التقديم", color=0x2b2d31)
    await ctx.send(embed=embed, view=ApplyView())


# ── تشغيل البوت ────────────────────────────────────────

@bot.event
async def on_ready():
    print(f"Bot Ready - Logged in as {bot.user}")
    if not auto_salary.is_running():
        auto_salary.start()

bot.run(os.getenv("TOKEN"))
