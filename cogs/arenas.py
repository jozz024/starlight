from typing import Dict, NamedTuple, Optional

from nextcord.ext import commands
from nextcord import (
    Button,
    ButtonStyle,
    ChannelType,
    Colour,
    Embed,
    Guild,
    Interaction,
    Member,
    MessageType,
    Thread,
    ThreadMember,
    ui
)

ARENA_CHANNEL_ID: int = 905081326481330247
ARENA_LOGS_CHANNEL_ID: int = 905098720750759976
AMIIBO_ARENA_ROLE_ID: int = 905094099256889405
PVP_ARENA_ROLE_ID: int = 905100774995001354
CUSTOM_ID_PREFIX: str = "arena:"


async def get_thread_author(channel: Thread) -> Member:
    history = channel.history(oldest_first = True, limit = 1)
    history_flat = await history.flatten()
    user = history_flat[0].mentions[0]
    return user


class arenaButton(ui.Button["ArenaView"]):
    def __init__(self, arena_type: str, *, style: ButtonStyle, custom_id: str):
        super().__init__(label = f"{arena_type} arena", style = style, custom_id = f"{CUSTOM_ID_PREFIX}{custom_id}")
        self._arena_type = arena_type

    async def create_arena_thread(self, interaction: Interaction) -> None:
        channel_type = ChannelType.private_thread if interaction.guild.premium_tier >= 2 else ChannelType.public_thread
        thread = await interaction.channel.create_thread(
            name = f"{self._arena_type} arena ({interaction.user})",
            type = channel_type
        )

        await interaction.guild.get_channel(ARENA_LOGS_CHANNEL_ID).send(
            content = f"Arena thread for {self._arena_type} created by {interaction.user.mention}: {thread.mention}!"
        )
        close_button_view = ThreadCloseView()
        close_button_view._thread_author = interaction.user

        type_to_colour: Dict[str, Colour] = {
            "amiibo v amiibo": Colour.red(),
            "Player v Player": Colour.green()
        }

        em = Embed(
            title = f"{self._arena_type} arena wanted!",
            colour = type_to_colour.get(self._arena_type, Colour.blurple())
        )
        em.set_footer(text = "You and anyone with the specified role can close this thread with the button")
        if self._arena_type == 'amiibo v amiibo':
            content = f"<@&{AMIIBO_ARENA_ROLE_ID}> | {interaction.user.mention}",
        else: 
            content = f"<@&{PVP_ARENA_ROLE_ID}> | {interaction.user.mention}",
        msg = await thread.send(
            content = content,
            embed = em,
            view = ThreadCloseView()
        )
        await msg.pin(reason = "First message in arena thread with the close button.")

    async def callback(self, interaction: Interaction):
        confirm_view = ConfirmView()

        def disable_all_buttons():
            for _item in confirm_view.children:
                _item.disabled = True

        confirm_content = "Are you really sure you want to make an arena thread?"
        await interaction.response.send_message(content = confirm_content, ephemeral = True, view = confirm_view)
        await confirm_view.wait()
        if confirm_view.value is False or confirm_view.value is None:
            disable_all_buttons()
            content = "Ok, cancelled." if confirm_view.value is False else f"~~{confirm_content}~~ I guess not..."
            await interaction.edit_original_message(content = content, view = confirm_view)
        else:
            disable_all_buttons()
            await interaction.edit_original_message(content = "Created!", view = confirm_view)
            await self.create_arena_thread(interaction)


class ArenaView(ui.View):
    def __init__(self):
        super().__init__(timeout = None)
        self.add_item(arenaButton("amiibo v amiibo", style = ButtonStyle.red, custom_id = "amiibo v amiibo"))
        self.add_item(arenaButton("Player v Player", style = ButtonStyle.green, custom_id = "Player v Player"))


class ConfirmButton(ui.Button["ConfirmView"]):
    def __init__(self, label: str, style: ButtonStyle, *, custom_id: str):
        super().__init__(label = label, style = style, custom_id = f"{CUSTOM_ID_PREFIX}{custom_id}")

    async def callback(self, interaction: Interaction):
        self.view.value = True if self.custom_id == f"{CUSTOM_ID_PREFIX}confirm_button" else False
        self.view.stop()


class ConfirmView(ui.View):
    def __init__(self):
        super().__init__(timeout = 10.0)
        self.value = None
        self.add_item(ConfirmButton("Yes", ButtonStyle.green, custom_id = "confirm_button"))
        self.add_item(ConfirmButton("No", ButtonStyle.red, custom_id = "decline_button"))


class ThreadCloseView(ui.View):
    def __init__(self):
        super().__init__(timeout = None)
        self._thread_author: Optional[Member] = None

    async def _get_thread_author(self, channel: Thread) -> None:
        self._thread_author = await get_thread_author(channel)

    @ui.button(label = "Close", style = ButtonStyle.red, custom_id = f"{CUSTOM_ID_PREFIX}thread_close")
    async def thread_close_button(self, button: Button, interaction: Interaction):
        if not self._thread_author:
            await self._get_thread_author(interaction.channel)  # type: ignore

        await interaction.channel.send(
            content = "This thread has now been closed. "
                      "Please create another thread if you wish to have another arena."
        )
        button.disabled = True
        await interaction.message.edit(view = self)
        await interaction.channel.edit(locked = True, archived = True)
        await interaction.guild.get_channel(ARENA_LOGS_CHANNEL_ID).send(
            content = f"Arena thread {interaction.channel.name} (created by {self._thread_author.name}) has been closed."
        )

    async def interaction_check(self, interaction: Interaction) -> bool:
        if not self._thread_author:
            await self._get_thread_author(interaction.channel)  # type: ignore

        # because we aren't assigning the persistent view to a message_id.
        if not isinstance(interaction.channel, Thread) or interaction.channel.parent_id != ARENA_CHANNEL_ID:
            return False

        return interaction.user.id == self._thread_author.id or interaction.user.get_role(arenaER_ROLE_ID)


class ArenaCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.create_views())

    async def create_views(self):
        if getattr(self.bot, "arena_view_set", False) is False:
            self.bot.arena_view_set = True
            self.bot.add_view(ArenaView())
            self.bot.add_view(ThreadCloseView())

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel.id == ARENA_CHANNEL_ID and message.type is MessageType.thread_created:
            await message.delete(delay = 5)
        if isinstance(message.channel, Thread) and \
                message.channel.parent_id == ARENA_CHANNEL_ID and \
                message.type is MessageType.pins_add:
            await message.delete(delay = 10)

    @commands.Cog.listener()
    async def on_thread_member_remove(self, member: ThreadMember):
        thread = member.thread
        if thread.parent_id != ARENA_CHANNEL_ID:
            return

        thread_author = await get_thread_author(thread)
        if member.id != thread_author.id:
            return

        FakeContext = NamedTuple("FakeContext", [("channel", Thread), ("author", Member), ("guild", Guild)])

        # _self represents the cog. Thanks Epic#6666
        async def fake_send(_self, *args, **kwargs):
            return await thread.send(*args, **kwargs)

        FakeContext.send = fake_send
        await self.close(FakeContext(thread, thread_author, thread.guild))

    @commands.command()
    @commands.is_owner()
    async def arena_menu(self, ctx):
        await ctx.send("Click a button to create an arena thread!", view = ArenaView())

    @commands.command()
    async def close(self, ctx):
        if not isinstance(ctx.channel, Thread) or ctx.channel.parent_id != ARENA_CHANNEL_ID:
            return

        thread_author = await get_thread_author(ctx.channel)
        if thread_author.id == ctx.author.id or ctx.author.get_role(arenaER_ROLE_ID):
            await ctx.send(
                "This thread has now been closed. Please create another thread if you wish to have another arena.")
            await ctx.channel.edit(locked = True, archived = True)
            await ctx.guild.get_channel(ARENA_LOGS_CHANNEL_ID).send(
                f"Arena thread {ctx.channel.name} (created by {thread_author.name}) has been closed.")


def setup(bot):
    bot.add_cog(ArenaCog(bot))