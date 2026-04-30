import disnake
from disnake.ext import commands
import os

intents = disnake.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# 💰 بنك
money = {}

# =======================
# 📝 التقديم (Modal)
# =======================
class ApplyModal(disnake.ui.Modal):
    def __init__(self):
        components = [
            disnake.ui.TextInput(
                label="اسمك الحقيقي",
                custom_id="name",
                style=disnake.TextInputStyle.short
            ),
            disnake.ui.TextInput(
                label="اسم روبلوكس الأساسي",
                custom_id="roblox",
                style=disnake.TextInputStyle.short
            ),
            disnake.ui.TextInput(
                label="اسمك الثاني (مثل NC_231)",
                custom_id="second",
                style=disnake.TextInputStyle.short
            ),
        ]
        super().__init__(title="📋 نموذج التقديم", components=components)

    async def callback(self, inter: disnake.ModalInteraction):
        name = inter.text_values["name"]
        roblox = inter.text_values["roblox"]
        second = inter.text_values["second"]

        await inter.response.send_message(
            f"✅ تم استلام التقديم:\n"
            f"👤 الاسم: {name}\n"
            f"🎮 روبلوكس: {roblox}\n"
            f"🆔 الثاني: {second}",
            ephemeral=True
        )

# أمر التقديم
@bot.slash_command(name="تقديم")
async def apply(inter):
    await inter.response.send_modal(modal=ApplyModal())

# =======================
# 🚨 المخالفات
# =======================
class FineSelect(disnake.ui.Select):
    def __init__(self):
        options = [
            disnake.SelectOption(label="500", description="مخالفة بسيطة"),
            disnake.SelectOption(label="900", description="مخالفة متوسطة"),
            disnake.SelectOption(label="3000", description="مخالفة قوية"),
        ]
        super().__init__(placeholder="اختر المخالفة", options=options)

    async def callback(self, inter: disnake.MessageInteraction):
        await inter.response.send_message(
            f"🚨 تم اختيار مخالفة: {self.values[0]}",
            ephemeral=True
        )

class FineView(disnake.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(FineSelect())

@bot.slash_command(name="مخالفات")
async def fines(inter):
    await inter.response.send_message(
        "اختر نوع المخالفة:",
        view=FineView(),
        ephemeral=True
    )

# =======================
# 💰 البنك
# =======================
@bot.slash_command(name="فلوسي")
async def balance(inter):
    user = inter.author.id
    bal = money.get(user, 0)
    await inter.response.send_message(f"💰 رصيدك: {bal}")

@bot.slash_command(name="اعطيني")
async def give(inter, amount: int):
    user = inter.author.id
    money[user] = money.get(user, 0) + amount
    await inter.response.send_message(f"💵 تم إعطائك {amount}")

# =======================
# 🚀 تشغيل البوت
# =======================
@bot.event
async def on_ready():
    print(f"✅ Bot is online: {bot.user}")

bot.run(os.getenv("TOKEN"))
