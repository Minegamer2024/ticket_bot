import discord
from discord.ext import commands
import json
from typing import Literal
import emoji
intents = discord.Intents.all()
client = commands.Bot(command_prefix="!", intents=intents)
@client.event
async def on_ready():
    print(f"ready {client.user}")
    await client.tree.sync()
colors = {
    "grey":discord.ButtonStyle.grey,
    "green":discord.ButtonStyle.green,
    "red":discord.ButtonStyle.red,
    "primary":discord.ButtonStyle.primary
}
image_extension = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp')
channel_ids = []
@client.tree.command(name="add_ticket", description="لأضافة تذاكر جديدة")
@discord.app_commands.default_permissions(administrator=True)
async def add_ticket(interaction: discord.Interaction, name: str, color: Literal["grey","green","red","primary"], name_ticket_room: str, log: discord.TextChannel, role: discord.Role, emoji_ticket: str, category: discord.CategoryChannel, image: discord.Attachment = None):
    server_id = str(interaction.guild.id)
    if not emoji.is_emoji(emoji_ticket):
        await interaction.response.send_message("يرجى إدخال رمز تعبيري صالح.", ephemeral=True)
        return
    with open("button.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    if server_id not in data:
        data[server_id] = {}
    else:
        pass
    if name in data[server_id]:
        await interaction.response.send_message("اسم هذه التذكرة قد استخدمته بالفعل", ephemeral=True)
    else:
        ticket_data_server = {
            "color": color,
            "name": name_ticket_room,
            "log": log.id,
            "role": role.id,
            "emoji": str(emoji_ticket),
            "category": category.id
        }
        if image and image.filename.lower().endswith(image_extension):
            ticket_data_server["image"] = image.url
            reply_add = "تم اضافة التذكرة الى قائمة التذاكر"
        else:
            reply_add = "تم حفظ الذكرة في قائمة التذاكر بدون صورة"
        data[server_id][name] = ticket_data_server
        with open("button.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        await interaction.response.send_message(reply_add, ephemeral=True)
@client.tree.command(name="ticket_setup", description="لأضافة قائمة التذاكرة")
@discord.app_commands.default_permissions(administrator=True)
async def ticket_setup(interaction: discord.Interaction, descreption: str, channel: discord.TextChannel = None, image: discord.Attachment = None):
    await interaction.response.defer(ephemeral=True)
    if not channel:
        channel = interaction.channel
    else:
        pass
    embed = discord.Embed(title="قائمة التذاكر", description=descreption, colour= discord.Colour.dark_blue())
    embed.set_author(name=f"{interaction.guild.name} Ticket", icon_url=interaction.guild.icon)
    if image and image.filename.lower().endswith(image_extension):
        embed.set_image(url=image.url)
        reply = f"تم إرسال قائمة التذاكر في روم {channel.mention}"
    else:
        reply = f"تم إرسال قائمة التذاكر في روم {channel.mention} بدون صورة"
    if channel is None:
        channel = interaction.channel
    with open("button.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    view = discord.ui.View(timeout=None)
    server_id = str(interaction.guild.id)
    if server_id not in data or not data[server_id]:
        await interaction.followup.send("لا يوجد اي تذاكر لأضافتها", ephemeral=True)
        return
    for ticket_name, ticket_data in data[server_id].items():
        role_ticket = interaction.guild.get_role(ticket_data["role"])
        button = discord.ui.Button(label=ticket_name, style=colors[ticket_data["color"]], emoji=ticket_data["emoji"])
        view.add_item(button) 
        async def button_callback(interaction: discord.Interaction, ticket_name=ticket_name, ticket_data=ticket_data, role_ticket=role_ticket):
            if not role_ticket in interaction.guild.roles:
                await interaction.response.send_message(f"للأسف يوجد خطأ تقني لا يمكن فتح تذكرة الان يرجى الانتظار حتى يتم حل المشكلة", ephemeral=True)
                for m in interaction.guild.members:
                    if m.guild_permissions.administrator and not m.bot:
                        if not m.bot:
                            report_embed = discord.Embed(title="تحذير", description=f"لم اتمكن من فتح تذكرة {interaction.user.mention} بسبب خطأ تقني يرجى التأكد من ان البيانات التي ادخلتها في تذكرة {ticket_name} مثل الرتب مازالت موجود وان لم تكن يرجى حذفها واضفتها من جديد", colour=discord.Colour.dark_red())
                            await m.send(m.mention, embed=report_embed)
                            return
            user = interaction.user
            category_ticket_id = ticket_data["category"]
            category = interaction.guild.get_channel(category_ticket_id)
            overwrite = {
                interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
                user: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True, embed_links=True),
                role_ticket: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True, embed_links=True)
            }
            if category:
                channel_ticket = await category.create_text_channel(name=f"{ticket_data["name"]} for {user}", overwrites=overwrite)
            else:
                channel_ticket = await interaction.guild.create_text_channel(name=f"{ticket_data["name"]} for {user}", overwrites=overwrite)
            channel_ids.append(channel_ticket.id)
            embed_ticket = discord.Embed(title=ticket_name, description=f"تم فتح التذكرة من {user.mention}", colour=discord.Colour.dark_blue())
            embed_ticket.set_author(name=f"{interaction.guild.name} Ticket control", icon_url=interaction.guild.icon)
            button_view = discord.ui.View(timeout=None)
            close_button = discord.ui.Button(label="اغلاق", style=discord.ButtonStyle.red, emoji="🔒")
            delete_button = discord.ui.Button(label="حذف", style=discord.ButtonStyle.grey, emoji="🗑")
            receive_button = discord.ui.Button(label="استلام", style=discord.ButtonStyle.green, emoji="✋")
            button_view.add_item(close_button)
            button_view.add_item(receive_button)
            button_view.add_item(delete_button)
            if "image" in ticket_data:
                embed_ticket.set_image(
                    url=ticket_data["image"]
                )
            else:
                pass
            async def close_callback(interaction: discord.Interaction):
                if role_ticket in interaction.user.roles:
                    close_embed = discord.Embed(title="اغلاق تذكرة", description=f"تم اغلاق التذكرة من قبل {interaction.user.mention}", colour=discord.Colour.red())
                    overwrite = {
                        interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
                        user: discord.PermissionOverwrite(view_channel=False),
                        role_ticket: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True, embed_links=True)
                    }
                    await channel_ticket.edit(name=f"close ticket {user}", overwrites=overwrite)
                    await interaction.response.send_message(embed=close_embed)
                    close_button.disabled = True
                    await interaction.followup.edit_message(message_id=ticket_control.id, embed=embed_ticket, view=button_view)
                else:
                    await interaction.response.send_message(f"لا يمكن اغلاق التذكرة الا من قبل اصحاب رتبة {role_ticket.mention}", ephemeral=True)
            async def delete_callback(interaction: discord.Interaction):
                log_channel = interaction.guild.get_channel(ticket_data["log"])
                if role_ticket in interaction.user.roles:
                    if log_channel:
                        embed = discord.Embed(title=f"حذف تذكرة {ticket_name}", description=f"تم حذف تذكرة {user.mention} من قبل {interaction.user.mention}", colour=discord.Colour.light_grey())
                        await log_channel.send(embed=embed)
                    else:
                        pass
                    channel_ids.remove(channel_ticket.id)
                    await channel_ticket.delete()
                else:
                    await interaction.response.send_message(f"لا يمكن حذف التذكرة الا من قبل اصحاب رتبة {role_ticket.mention}", ephemeral=True)
            async def receive_callback(interaction: discord.Interaction):
                if role_ticket in interaction.user.roles:  
                    receive_embed = discord.Embed(title="استلام تذكرة", description=f"تم استلام التذكرة من قبل {interaction.user.mention}", colour=discord.Colour.green())
                    await channel_ticket.set_permissions(role_ticket, view_channel=True, send_messages=False, attach_files=False, embed_links=False)
                    await channel_ticket.set_permissions(interaction.user, view_channel=True, send_messages=True, attach_files=True, embed_links=True)
                    await interaction.response.send_message(embed=receive_embed)
                    receive_button.disabled = True
                    await interaction.followup.edit_message(message_id=ticket_control.id, embed=embed_ticket, view=button_view)
                else:
                    await interaction.response.send_message(f"لا يمكن استلام التذكرة الا من قبل اصحاب رتبة {role_ticket.mention}", ephemeral=True)
            close_button.callback = close_callback
            delete_button.callback = delete_callback
            receive_button.callback = receive_callback
            ticket_control = await channel_ticket.send(role_ticket.mention, embed=embed_ticket, view=button_view)
            await interaction.response.send_message(f"تم فتح التذكرة الخاصة بك {channel_ticket.mention}", ephemeral=True)
        button.callback = button_callback
    await interaction.followup.send(reply, ephemeral=True)
    await channel.send(embed=embed, view=view)
@client.tree.command(name="add_member", description="لأضافة عضو الى تذكرة")
async def add(interaction: discord.Interaction, member: discord.User):
    with open("button.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    server_id = str(interaction.guild.id)
    if not data[server_id] or server_id not in data:
        await interaction.response.send_message("لم يتم اضافة اي تذاكر بعد", ephemeral=True)
        return
    for roles in data[server_id].values():
        role = interaction.guild.get_role(roles["role"])
    if role in interaction.user.roles:
        if interaction.channel.id in channel_ids:
            if member:
                permission = interaction.channel.permissions_for(member)
                if permission.view_channel and permission.send_messages:
                    await interaction.response.send_message("هذا العضو موجود بالفعل في التذكرة", ephemeral=True)
                else:
                    add_embed = discord.Embed(title=f"اضافة عضو", description=f"تم اضافة {member.mention} للتذكرة من قبل {interaction.user.mention}", colour= discord.Colour.dark_blue())
                    await interaction.channel.set_permissions(member, view_channel = True, send_messages = True, attach_files = True, embed_links = True)
                    await interaction.response.send_message(embed=add_embed)
            else:
                add_embed = discord.Embed(title=f"اضافة عضو", description=f"لم اتمكن من العثور على هذا الضو", colour= discord.Colour.dark_blue())
                await interaction.response.send_message(embed=add_embed)
        else:
            await interaction.response.send_message("هذه ليست تذكرة لأضافة عضو", ephemeral=True)
    else:
        await interaction.response.send_message("است لا تملك الصلاحية لأستخدام هذا الامر", ephemeral=True)
@client.tree.command(name="delete_ticket", description="لأزالة تذاكرة")
@discord.app_commands.default_permissions(administrator=True)
async def delete_ticket(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    server_id = str(interaction.guild.id)
    with open("button.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    if not data[server_id] or server_id not in data:
        await interaction.followup.send("لا يوجد اي تذاكر لأزالتها", ephemeral=True)
    else:
        option = []
        for ticket in data[server_id]:
            option.append(discord.SelectOption(label=ticket, value=ticket))
        select_view = discord.ui.View(timeout=None)
        select = discord.ui.Select(placeholder="يرجى اختيار التذكرة", options=option)
        select_view.add_item(select)
        async def select_callback(interaction: discord.Interaction):
            del data[server_id][select.values[0]]
            with open("button.json", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            await interaction.response.edit_message(content="تم ازالة التذكرة من قائمة التذاكر", view=None)
        select.callback = select_callback
        await interaction.followup.send("يرجى اختيار التذكرة الذي تريد ازالتها", view=select_view, ephemeral=True)
@client.tree.command(name="remove_member", description="لأزالة عضو من تذكرة")
async def reomve(interaction: discord.Interaction, member: discord.User):
    with open("button.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    server_id = str(interaction.guild.id)
    if not data[server_id] or server_id not in data:
        await interaction.response.send_message("لم يتم اضافة اي تذاكر بعد", ephemeral=True)
        return
    for roles in data[server_id].values():
        role = interaction.guild.get_role(roles["role"])
    if role in interaction.user.roles:
        if interaction.channel.id in channel_ids:
            if member:
                permission = interaction.channel.permissions_for(member)
                if not permission.view_channel and not permission.send_messages:
                    await interaction.response.send_message("هذا العضو غير موجود بالفعل في التذكرة", ephemeral=True)
                else:
                    add_embed = discord.Embed(title=f"ازالة عضو", description=f"تم ازالة {member.mention} من التذكرة من قبل {interaction.user.mention}", colour= discord.Colour.dark_blue())
                    await interaction.channel.set_permissions(member, view_channel = False)
                    await interaction.response.send_message(embed=add_embed)
            else:
                add_embed = discord.Embed(title=f"ازالة عضو", description=f"لم اتمكن من العثور على هذا الضو", colour= discord.Colour.dark_blue())
                await interaction.response.send_message(embed=add_embed)
        else:
            await interaction.response.send_message("هذه ليست تذكرة لأزالة عضو", ephemeral=True)
    else:
        await interaction.response.send_message("است لا تملك الصلاحية لأستخدام هذا الامر", ephemeral=True)
client.run("add_bot_token")